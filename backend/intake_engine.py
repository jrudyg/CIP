"""
INTAKE ENGINE
=============
Comprehensive contract intake with risk scoring, RAG, and metadata extraction.

Location: C:\\Users\\jrudy\\CIP\\backend\\intake_engine.py

Design Principles:
- Single module (no scattered files)
- Pipeline pattern (each step is a pure function)
- Transaction-safe (all or nothing)
- Fail fast (validate before heavy processing)
- One pass (extract everything in single traversal)
- Batch operations (minimize API calls)

Usage:
    from intake_engine import process_intake
    
    result = process_intake(
        file_path='contract.docx',
        db_path='contracts.db'
    )
"""

import os
import re
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from config import ANTHROPIC_API_KEY
import anthropic

# =============================================================================
# CONFIGURATION
# =============================================================================

# CCE-Plus paths
CCE_PLUS_ROOT = Path(r"C:\Users\jrudy\CCE\cce-plus")

# Supported file types
SUPPORTED_EXTENSIONS = {'.docx', '.pdf', '.txt'}

# AI Extraction configuration
CLAUDE_MODEL = "claude-sonnet-4-20250514"
EXTRACTION_TIMEOUT = 30

# Size limits
MAX_FILE_SIZE_MB = 25
MAX_CLAUSES = 500

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Clause:
    """Extracted clause with all metadata."""
    section_number: str
    section_title: str
    clause_type: str
    verbatim_text: str
    word_count: int
    # CCE-Plus scoring (populated during processing)
    cce_risk_score: float = 0.0
    cce_risk_level: str = 'LOW'
    cce_statutory_flag: Optional[str] = None
    cce_cascade_risk: bool = False
    # RAG reference (populated during embedding)
    embedding_id: Optional[str] = None
    chunk_hash: Optional[str] = None


@dataclass
class ContractMetadata:
    """Extracted contract metadata."""
    party_client: Optional[str] = None
    party_vendor: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    contract_value: Optional[float] = None
    currency: str = 'USD'
    governing_law: Optional[str] = None
    vendor_ticker: Optional[str] = None
    vendor_cik: Optional[str] = None
    # NEW FIELDS
    contract_type: Optional[str] = None
    purpose: Optional[str] = None
    relationship: Optional[str] = None
    counterparty_type: Optional[str] = None
    extraction_method: str = 'REGEX'
    extraction_confidence: Dict[str, float] = field(default_factory=dict)


@dataclass
class IntakeResult:
    """Complete intake processing result."""
    success: bool
    contract_id: Optional[int] = None
    document_hash: Optional[str] = None
    clause_count: int = 0
    metadata: Optional[ContractMetadata] = None
    risk_summary: Dict = field(default_factory=dict)
    annotations: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: int = 0


# =============================================================================
# STEP 1: VALIDATION
# =============================================================================

def validate_document(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validate document before processing.
    Fail fast - check everything before heavy lifting.
    """
    errors = []
    path = Path(file_path)
    
    # Check exists
    if not path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    # Check extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        errors.append(f"Unsupported file type: {path.suffix}. Supported: {SUPPORTED_EXTENSIONS}")
        return False, errors
    
    # Check size
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        errors.append(f"File too large: {size_mb:.1f}MB. Max: {MAX_FILE_SIZE_MB}MB")
        return False, errors
    
    # Check readable
    try:
        with open(path, 'rb') as f:
            f.read(1024)  # Read first 1KB to verify access
    except Exception as e:
        errors.append(f"Cannot read file: {e}")
        return False, errors
    
    return True, errors


def compute_document_hash(file_path: str) -> str:
    """Compute SHA-256 hash of document."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_duplicate(db_path: str, document_hash: str) -> Optional[int]:
    """Check if document already ingested. Returns contract_id if duplicate."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM contracts WHERE document_hash = ?",
        (document_hash,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


# =============================================================================
# STEP 2: PARSING
# =============================================================================

def parse_docx(file_path: str) -> str:
    """Extract text from .docx file."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n\n'.join(paragraphs)
    except ImportError:
        raise ImportError("python-docx required. Install: pip install python-docx")


def parse_pdf(file_path: str) -> str:
    """Extract text from .pdf file."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = []
        for page in doc:
            text.append(page.get_text())
        doc.close()
        return '\n\n'.join(text)
    except ImportError:
        raise ImportError("PyMuPDF required. Install: pip install pymupdf")


def parse_txt(file_path: str) -> str:
    """Extract text from .txt file."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def parse_document(file_path: str) -> str:
    """Parse document based on extension."""
    ext = Path(file_path).suffix.lower()
    
    parsers = {
        '.docx': parse_docx,
        '.pdf': parse_pdf,
        '.txt': parse_txt
    }
    
    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"No parser for extension: {ext}")
    
    return parser(file_path)


# =============================================================================
# STEP 3: CHUNKING (CCE-Plus patterns)
# =============================================================================

# Section detection patterns (from CCE-Plus clause-chunker.js)
SECTION_PATTERN = re.compile(r'^(?:SECTION|ARTICLE)\s+(\d+)[\.:]\s*(.+)$', re.IGNORECASE | re.MULTILINE)
CLAUSE_PATTERN = re.compile(r'^§\s*(\d+(?:\.\d+)?)\s+(.+)$', re.MULTILINE)
NUMBERED_PATTERN = re.compile(r'^(\d+(?:\.\d+)?)\s+([A-Z][^\n]{3,60})\s*$', re.MULTILINE)

# Clause type detection keywords
CLAUSE_TYPE_KEYWORDS = {
    'Legal/Liability': ['liability', 'indemnif', 'negligence', 'damages', 'warranty'],
    'Legal/Remedy': ['remedy', 'sole remedy', 'exclusive remedy', 'waive'],
    'Financial/Prepayment': ['prepay', 'advance payment', 'deposit', 'upfront'],
    'Financial/Payment': ['payment', 'invoice', 'fee', 'price', 'compensation'],
    'IP/Ownership': ['intellectual property', 'ownership', 'patent', 'copyright', 'trademark'],
    'Termination': ['terminat', 'cancel', 'expire', 'renewal'],
    'Indemnification': ['indemnif', 'hold harmless', 'defend'],
    'Confidentiality': ['confidential', 'non-disclosure', 'proprietary', 'secret'],
}


def detect_clause_type(text: str) -> str:
    """Detect clause type based on keywords."""
    text_lower = text.lower()
    
    for clause_type, keywords in CLAUSE_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return clause_type
    
    return 'General'


def chunk_document(full_text: str) -> List[Clause]:
    """
    Chunk document into clauses using CCE-Plus patterns.
    Preserves section structure and verbatim text.
    """
    clauses = []
    
    # Try section-based chunking first
    sections = SECTION_PATTERN.split(full_text)
    
    if len(sections) > 1:
        # Document has clear sections
        # sections[0] is text before first section
        # sections[1::3] are section numbers
        # sections[2::3] are section titles  
        # sections[3::3] are section contents (but this indexing is complex)
        
        # Simpler: find all section starts and extract
        matches = list(SECTION_PATTERN.finditer(full_text))
        
        for i, match in enumerate(matches):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            
            # Get content until next section or end
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            content = full_text[start:end].strip()
            
            if content:
                clause = Clause(
                    section_number=section_num,
                    section_title=section_title,
                    clause_type=detect_clause_type(content),
                    verbatim_text=content,
                    word_count=len(content.split())
                )
                clause.chunk_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                clauses.append(clause)
    
    # Try clause markers (§)
    if not clauses:
        matches = list(CLAUSE_PATTERN.finditer(full_text))
        
        for i, match in enumerate(matches):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            content = full_text[start:end].strip()
            
            if content:
                clause = Clause(
                    section_number=f"§{section_num}",
                    section_title=section_title,
                    clause_type=detect_clause_type(content),
                    verbatim_text=content,
                    word_count=len(content.split())
                )
                clause.chunk_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                clauses.append(clause)
    
    # Try numbered paragraphs
    if not clauses:
        matches = list(NUMBERED_PATTERN.finditer(full_text))
        
        for i, match in enumerate(matches):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            content = full_text[start:end].strip()
            
            if content:
                clause = Clause(
                    section_number=section_num,
                    section_title=section_title,
                    clause_type=detect_clause_type(content),
                    verbatim_text=content,
                    word_count=len(content.split())
                )
                clause.chunk_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                clauses.append(clause)
    
    # Fallback: paragraph-based chunking
    if not clauses:
        paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip() and len(p.strip()) > 50]
        
        for i, para in enumerate(paragraphs[:MAX_CLAUSES]):
            clause = Clause(
                section_number=str(i + 1),
                section_title=f"Paragraph {i + 1}",
                clause_type=detect_clause_type(para),
                verbatim_text=para,
                word_count=len(para.split())
            )
            clause.chunk_hash = hashlib.sha256(para.encode()).hexdigest()[:16]
            clauses.append(clause)
    
    return clauses[:MAX_CLAUSES]


# =============================================================================
# STEP 4: RISK SCORING (CCE-Plus integration)
# =============================================================================

def score_clauses_batch(clauses: List[Clause]) -> List[Clause]:
    """
    Score all clauses using CCE-Plus risk scorer.
    Batch operation for efficiency.
    """
    try:
        # Import CCE-Plus integration
        import sys
        if str(CCE_PLUS_ROOT) not in sys.path:
            sys.path.insert(0, str(CCE_PLUS_ROOT))
        
        # Try to import from CIP backend first (if integration module exists)
        try:
            from cce_plus_integration import score_clause_risk, detect_cascades
        except ImportError:
            # Fallback: inline scoring (simplified CCE-Plus logic)
            score_clause_risk = _fallback_score_clause
            detect_cascades = _fallback_detect_cascades
        
        # Score each clause
        for clause in clauses:
            risk_data = score_clause_risk(
                clause.verbatim_text,
                clause.clause_type,
                clause.section_number
            )
            clause.cce_risk_score = risk_data['risk_score']
            clause.cce_risk_level = risk_data['risk_level']
            clause.cce_statutory_flag = risk_data.get('statutory_flag')
        
        # Detect cascades
        clause_dicts = [
            {
                'section_number': c.section_number,
                'clause_type': c.clause_type,
                'v2_content': c.verbatim_text,
                'cce_risk_score': c.cce_risk_score
            }
            for c in clauses
        ]
        
        cascades = detect_cascades(clause_dicts)
        
        # Mark cascade-affected clauses
        cascade_sections = set()
        for cascade in cascades:
            cascade_sections.update(cascade.get('affected_sections', []))
        
        for clause in clauses:
            if clause.section_number in cascade_sections:
                clause.cce_cascade_risk = True
        
    except Exception as e:
        # Log error but don't fail - use fallback scores
        print(f"Warning: CCE-Plus scoring failed, using fallback: {e}")
        for clause in clauses:
            fallback = _fallback_score_clause(clause.verbatim_text, clause.clause_type)
            clause.cce_risk_score = fallback['risk_score']
            clause.cce_risk_level = fallback['risk_level']
    
    return clauses


def _fallback_score_clause(text: str, clause_type: str, section: str = None) -> Dict:
    """Fallback scoring when CCE-Plus unavailable."""
    # Simple keyword-based scoring
    text_lower = text.lower()
    
    risk_keywords = {
        'critical': ['gross negligence', 'willful misconduct', 'sole remedy', 'non-refundable'],
        'high': ['indemnif', 'liability', 'waive', 'prepayment'],
        'medium': ['terminat', 'confidential', 'payment'],
    }
    
    score = 3.0  # Default LOW
    
    for level, keywords in risk_keywords.items():
        if any(kw in text_lower for kw in keywords):
            if level == 'critical':
                score = 9.0
                break
            elif level == 'high':
                score = max(score, 7.0)
            elif level == 'medium':
                score = max(score, 5.0)
    
    level = 'CRITICAL' if score >= 9 else 'HIGH' if score >= 7 else 'MEDIUM' if score >= 5 else 'LOW'
    
    return {'risk_score': score, 'risk_level': level, 'statutory_flag': None}


def _fallback_detect_cascades(clauses: List[Dict]) -> List[Dict]:
    """Fallback cascade detection."""
    return []  # No cascades detected in fallback mode


# =============================================================================
# STEP 5: RAG EMBEDDING
# =============================================================================

def embed_clauses_batch(clauses: List[Clause], collection_name: str = 'cip_contracts') -> List[Clause]:
    """
    Generate embeddings for all clauses and store in ChromaDB.
    Batch operation for efficiency.
    """
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Connect to ChromaDB
        chroma_client = chromadb.HttpClient(host='localhost', port=8000)
        collection = chroma_client.get_or_create_collection(name=collection_name)
        
        # Prepare batch data
        ids = []
        documents = []
        metadatas = []
        
        for clause in clauses:
            doc_id = f"{clause.chunk_hash}_{clause.section_number}"
            ids.append(doc_id)
            documents.append(clause.verbatim_text)
            metadatas.append({
                'section_number': clause.section_number,
                'section_title': clause.section_title,
                'clause_type': clause.clause_type,
                'risk_level': clause.cce_risk_level,
                'risk_score': clause.cce_risk_score
            })
            clause.embedding_id = doc_id
        
        # Batch upsert
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
    except Exception as e:
        # ChromaDB not available - continue without embeddings
        print(f"Warning: ChromaDB embedding failed: {e}")
    
    return clauses


# =============================================================================
# STEP 6: METADATA EXTRACTION
# =============================================================================

def extract_metadata(full_text: str, clauses: List[Clause]) -> ContractMetadata:
    """
    Extract contract metadata using AI with regex fallback.

    This is the main entry point - replaces the original regex-only version.
    """
    return extract_metadata_ai(full_text, clauses)


def extract_metadata_ai(full_text: str, clauses: List[Clause]) -> ContractMetadata:
    """
    Extract contract metadata using Claude AI with regex fallback.

    Primary: Claude API structured extraction
    Fallback: Regex patterns if API unavailable

    Returns ContractMetadata with extraction_method and extraction_confidence populated.
    """
    metadata = ContractMetadata()

    # Try AI extraction first
    try:
        metadata = _extract_with_claude(full_text)
        metadata.extraction_method = 'AI'
    except Exception as e:
        print(f"AI extraction failed, using regex fallback: {e}")
        metadata = _extract_with_regex(full_text)
        metadata.extraction_method = 'REGEX'

    return metadata


def _extract_with_claude(full_text: str) -> ContractMetadata:
    """
    Extract metadata using Claude API with structured prompt.
    """
    # Truncate text if too long (use first 15000 chars for extraction)
    text_sample = full_text[:15000] if len(full_text) > 15000 else full_text

    extraction_prompt = f"""Analyze this contract text and extract the following metadata.
Respond ONLY with valid JSON, no other text.

CONTRACT TEXT:
{text_sample}

EXTRACT (respond in this exact JSON format):
{{
    "party_client": "Name of the client/customer/buyer or null if not found",
    "party_vendor": "Name of the vendor/supplier/seller or null if not found",
    "effective_date": "Date in YYYY-MM-DD format or null if not found",
    "expiration_date": "Date in YYYY-MM-DD format or null if not found",
    "contract_value": 0.00 or null if not found (numeric only, no currency symbols),
    "currency": "USD" or appropriate currency code,
    "governing_law": "State or jurisdiction name or null if not found",
    "contract_type": "One of: MSA, SOW, NDA, MNDA, IPA, EULA, Amendment, Purchase Order, Services Agreement, License Agreement, Other",
    "purpose": "One of: Equipment, Services, Professional Services, Engineering, Installation, Staffing, Transportation, Maintenance, Software, Consulting, Integration, Other",
    "relationship": "One of: Standalone, Parent, Child, Amendment, Renewal, Other",
    "confidence": {{
        "party_client": 0.0-1.0,
        "party_vendor": 0.0-1.0,
        "effective_date": 0.0-1.0,
        "expiration_date": 0.0-1.0,
        "contract_value": 0.0-1.0,
        "governing_law": 0.0-1.0,
        "contract_type": 0.0-1.0,
        "purpose": 0.0-1.0
    }}
}}

RULES:
- Extract actual entity names, not placeholders like [COMPANY_A]
- If a party is labeled "Client" or "Customer", that's party_client
- If a party is labeled "Vendor", "Supplier", "Contractor", that's party_vendor
- For dates, convert to YYYY-MM-DD format
- For contract_value, extract the primary/total value, not individual line items
- Confidence should reflect how certain you are (1.0 = explicitly stated, 0.5 = inferred, 0.0 = not found)
"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": extraction_prompt}
        ]
    )

    # Parse response
    response_text = message.content[0].text.strip()

    # Clean JSON (remove markdown code blocks if present)
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip()

    data = json.loads(response_text)

    # Build metadata object
    metadata = ContractMetadata()
    metadata.party_client = data.get('party_client')
    metadata.party_vendor = data.get('party_vendor')
    metadata.effective_date = data.get('effective_date')
    metadata.expiration_date = data.get('expiration_date')
    metadata.contract_value = data.get('contract_value')
    metadata.currency = data.get('currency', 'USD')
    metadata.governing_law = data.get('governing_law')
    metadata.contract_type = data.get('contract_type')
    metadata.purpose = data.get('purpose')
    metadata.relationship = data.get('relationship')
    metadata.extraction_confidence = data.get('confidence', {})

    return metadata


def _extract_with_regex(full_text: str) -> ContractMetadata:
    """
    Fallback regex-based extraction (original logic).
    """
    metadata = ContractMetadata()

    # Party extraction patterns
    party_patterns = [
        r'between\s+([A-Z][A-Za-z\s,\.]+(?:Inc|LLC|Corp|Ltd|Company|LP|LLP))',
        r'(?:"Client"|"Customer"|"Buyer")\s+(?:means|refers to)?\s*([A-Z][A-Za-z\s,\.]+)',
        r'(?:"Vendor"|"Supplier"|"Seller"|"Contractor")\s+(?:means|refers to)?\s*([A-Z][A-Za-z\s,\.]+)',
    ]

    for pattern in party_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            party = match.group(1).strip()
            # Remove trailing punctuation
            party = re.sub(r'[,\.\s]+$', '', party)

            if any(kw in pattern.lower() for kw in ['client', 'customer', 'buyer']):
                if not metadata.party_client:
                    metadata.party_client = party
                    metadata.extraction_confidence['party_client'] = 0.6
            else:
                if not metadata.party_vendor:
                    metadata.party_vendor = party
                    metadata.extraction_confidence['party_vendor'] = 0.6

    # Date extraction
    date_patterns = [
        (r'effective\s+(?:date|as of)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'effective'),
        (r'(?:dated|entered into)(?:\s+as of)?[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'effective'),
        (r'expires?\s+(?:on)?[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'expiration'),
        (r'expiration\s+date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'expiration'),
        (r'term\s+(?:shall\s+)?(?:end|expire)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'expiration'),
    ]

    for pattern, date_type in date_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            if date_type == 'effective' and not metadata.effective_date:
                metadata.effective_date = match.group(1)
                metadata.extraction_confidence['effective_date'] = 0.7
            elif date_type == 'expiration' and not metadata.expiration_date:
                metadata.expiration_date = match.group(1)
                metadata.extraction_confidence['expiration_date'] = 0.7

    # Value extraction
    value_pattern = r'\$\s?([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars)?'
    values = re.findall(value_pattern, full_text)
    if values:
        numeric_values = [float(v.replace(',', '')) for v in values]
        if numeric_values:
            metadata.contract_value = max(numeric_values)
            metadata.extraction_confidence['contract_value'] = 0.5

    # Governing law
    law_patterns = [
        r'governed by.*?(?:laws? of|law of)\s+(?:the\s+)?(?:State of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'jurisdiction.*?(?:State of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]

    for pattern in law_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            metadata.governing_law = match.group(1)
            metadata.extraction_confidence['governing_law'] = 0.7
            break

    # Contract type detection (keyword-based)
    type_keywords = {
        'MSA': ['master service', 'master agreement', 'msa'],
        'SOW': ['statement of work', 'sow', 'work order'],
        'NDA': ['non-disclosure', 'nda', 'confidentiality agreement'],
        'MNDA': ['mutual non-disclosure', 'mnda', 'mutual nda'],
        'Amendment': ['amendment', 'addendum', 'modification'],
        'Purchase Order': ['purchase order', 'po'],
        'Services Agreement': ['services agreement', 'professional services'],
        'License Agreement': ['license agreement', 'software license', 'eula'],
    }

    text_lower = full_text.lower()
    for contract_type, keywords in type_keywords.items():
        if any(kw in text_lower for kw in keywords):
            metadata.contract_type = contract_type
            metadata.extraction_confidence['contract_type'] = 0.6
            break

    # Purpose detection
    purpose_keywords = {
        'Equipment': ['equipment', 'hardware', 'machinery'],
        'Software': ['software', 'saas', 'application'],
        'Services': ['services', 'support'],
        'Professional Services': ['professional services', 'consulting', 'advisory'],
        'Engineering': ['engineering', 'design'],
        'Installation': ['installation', 'implementation'],
        'Maintenance': ['maintenance', 'support services'],
        'Integration': ['integration', 'system integration'],
    }

    for purpose, keywords in purpose_keywords.items():
        if any(kw in text_lower for kw in keywords):
            metadata.purpose = purpose
            metadata.extraction_confidence['purpose'] = 0.5
            break

    metadata.relationship = 'Standalone'  # Default
    metadata.extraction_confidence['relationship'] = 0.3

    return metadata


# =============================================================================
# STEP 7: PUBLIC COMPANY LOOKUP
# =============================================================================

def lookup_public_company(db_path: str, vendor_name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Look up vendor in public companies table.
    Returns (ticker, cik) or (None, None).
    """
    if not vendor_name:
        return None, None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    vendor_lower = vendor_name.lower()
    
    # Try exact match first
    cursor.execute(
        "SELECT ticker, cik FROM public_companies WHERE LOWER(company_name) = ?",
        (vendor_lower,)
    )
    result = cursor.fetchone()
    
    if not result:
        # Try partial match
        cursor.execute(
            "SELECT ticker, cik, aliases FROM public_companies"
        )
        for row in cursor.fetchall():
            ticker, cik, aliases_json = row
            
            # Check aliases
            if aliases_json:
                aliases = json.loads(aliases_json)
                if any(alias.lower() in vendor_lower or vendor_lower in alias.lower() for alias in aliases):
                    result = (ticker, cik)
                    break
    
    conn.close()
    return result if result else (None, None)


# =============================================================================
# STEP 8: STORAGE
# =============================================================================

def store_intake(
    db_path: str,
    file_path: str,
    document_hash: str,
    clauses: List[Clause],
    metadata: ContractMetadata,
    annotations: List[Dict],
    original_filename: str = None
) -> int:
    """
    Store all intake data in single transaction.
    Returns contract_id.

    Args:
        original_filename: Original filename (if file_path is a temp file)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Calculate risk summary
        risk_summary = {
            'total_clauses': len(clauses),
            'critical': sum(1 for c in clauses if c.cce_risk_level == 'CRITICAL'),
            'high': sum(1 for c in clauses if c.cce_risk_level == 'HIGH'),
            'medium': sum(1 for c in clauses if c.cce_risk_level == 'MEDIUM'),
            'low': sum(1 for c in clauses if c.cce_risk_level == 'LOW'),
            'avg_score': round(sum(c.cce_risk_score for c in clauses) / len(clauses), 1) if clauses else 0,
            'max_score': max((c.cce_risk_score for c in clauses), default=0),
            'statutory_flags': sum(1 for c in clauses if c.cce_statutory_flag),
            'cascade_risks': sum(1 for c in clauses if c.cce_cascade_risk)
        }
        
        # Insert or update contract
        # Use original filename if provided (for temp files), otherwise extract from path
        if original_filename:
            title = Path(original_filename).stem
            filename = Path(original_filename).name
        else:
            title = Path(file_path).stem
            filename = Path(file_path).name

        cursor.execute("""
            INSERT INTO contracts (
                title, filename, filepath, document_hash, clause_count,
                party_client, party_vendor, counterparty, our_entity, effective_date, expiration_date,
                contract_value, currency, governing_law,
                vendor_ticker, vendor_cik,
                contract_type, contract_purpose, party_relationship, counterparty_type,
                intake_status, intake_completed_at, intake_risk_summary,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, filename, file_path, document_hash, len(clauses),
            metadata.party_client, metadata.party_vendor, metadata.party_vendor, metadata.party_client,
            metadata.effective_date, metadata.expiration_date,
            metadata.contract_value, metadata.currency, metadata.governing_law,
            metadata.vendor_ticker, metadata.vendor_cik,
            metadata.contract_type, metadata.purpose, metadata.relationship, metadata.counterparty_type,
            'COMPLETE', datetime.now().isoformat(), json.dumps(risk_summary),
            datetime.now().isoformat()
        ))
        
        contract_id = cursor.lastrowid
        
        # Insert clauses
        for clause in clauses:
            cursor.execute("""
                INSERT INTO clauses (
                    contract_id, text, section_number, section_title, clause_type,
                    verbatim_text, word_count,
                    cce_risk_score, cce_risk_level, cce_statutory_flag, cce_cascade_risk,
                    embedding_id, chunk_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id, clause.verbatim_text, clause.section_number, clause.section_title, clause.clause_type,
                clause.verbatim_text, clause.word_count,
                clause.cce_risk_score, clause.cce_risk_level, clause.cce_statutory_flag,
                1 if clause.cce_cascade_risk else 0,
                clause.embedding_id, clause.chunk_hash
            ))
        
        # Insert annotations
        for annotation in annotations:
            cursor.execute("""
                INSERT INTO annotations (
                    contract_id, clause_id, annotation_type, severity,
                    title, content, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id, annotation.get('clause_id'),
                annotation['type'], annotation.get('severity', 'INFO'),
                annotation.get('title', ''), annotation['content'],
                annotation.get('source', 'INTAKE')
            ))
        
        conn.commit()
        return contract_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# =============================================================================
# STEP 9: REPORT GENERATION
# =============================================================================

def generate_intake_report(
    contract_id: int,
    file_path: str,
    clauses: List[Clause],
    metadata: ContractMetadata,
    annotations: List[Dict]
) -> str:
    """Generate markdown intake report."""
    
    # Calculate stats
    total = len(clauses)
    critical = sum(1 for c in clauses if c.cce_risk_level == 'CRITICAL')
    high = sum(1 for c in clauses if c.cce_risk_level == 'HIGH')
    medium = sum(1 for c in clauses if c.cce_risk_level == 'MEDIUM')
    low = sum(1 for c in clauses if c.cce_risk_level == 'LOW')
    avg_score = round(sum(c.cce_risk_score for c in clauses) / total, 1) if total else 0
    statutory = [c for c in clauses if c.cce_statutory_flag]
    cascades = [c for c in clauses if c.cce_cascade_risk]
    
    # Determine overall risk
    if critical > 0 or len(cascades) > 0:
        overall_risk = '🔴 CRITICAL'
    elif high > 0:
        overall_risk = '🟠 HIGH'
    elif medium > 0:
        overall_risk = '🟡 MEDIUM'
    else:
        overall_risk = '🟢 LOW'
    
    report = f"""# INTAKE REPORT

**Contract:** {Path(file_path).name}  
**Contract ID:** {contract_id}  
**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Overall Risk:** {overall_risk}

---

## PARTIES

| Role | Name | Public Company |
|------|------|----------------|
| Client | {metadata.party_client or 'Not identified'} | — |
| Vendor | {metadata.party_vendor or 'Not identified'} | {metadata.vendor_ticker or 'Private/Unknown'} |

## KEY TERMS

| Term | Value |
|------|-------|
| Effective Date | {metadata.effective_date or 'Not identified'} |
| Expiration Date | {metadata.expiration_date or 'Not identified'} |
| Contract Value | {'${:,.2f}'.format(metadata.contract_value) if metadata.contract_value else 'Not identified'} |
| Governing Law | {metadata.governing_law or 'Not identified'} |

---

## RISK SUMMARY

| Level | Count | Percentage |
|-------|-------|------------|
| 🔴 CRITICAL | {critical} | {critical/total*100:.0f}% |
| 🟠 HIGH | {high} | {high/total*100:.0f}% |
| 🟡 MEDIUM | {medium} | {medium/total*100:.0f}% |
| 🟢 LOW | {low} | {low/total*100:.0f}% |

**Average Risk Score:** {avg_score}/10.0  
**Total Clauses:** {total}

---

## STATUTORY FLAGS ({len(statutory)})

"""
    
    if statutory:
        report += "| Section | Title | Flag | Score |\n|---------|-------|------|-------|\n"
        for c in statutory:
            report += f"| {c.section_number} | {c.section_title[:30]} | {c.cce_statutory_flag} | {c.cce_risk_score} |\n"
    else:
        report += "*No statutory conflicts detected.*\n"
    
    report += f"""

---

## CASCADE RISKS ({len(cascades)})

"""
    
    if cascades:
        report += "| Section | Title | Risk Score |\n|---------|-------|------------|\n"
        for c in cascades:
            report += f"| {c.section_number} | {c.section_title[:30]} | {c.cce_risk_score} |\n"
        report += "\n⚠️ **These clauses interact to create combined risk exceeding individual scores.**\n"
    else:
        report += "*No cascade risks detected.*\n"
    
    report += f"""

---

## TOP RISK CLAUSES

"""
    
    # Top 5 by risk score
    top_clauses = sorted(clauses, key=lambda c: c.cce_risk_score, reverse=True)[:5]
    
    for c in top_clauses:
        badge = '🔴' if c.cce_risk_level == 'CRITICAL' else '🟠' if c.cce_risk_level == 'HIGH' else '🟡' if c.cce_risk_level == 'MEDIUM' else '🟢'
        report += f"""### {badge} {c.section_number}: {c.section_title}

**Risk Score:** {c.cce_risk_score}/10.0 ({c.cce_risk_level})  
**Type:** {c.clause_type}  
{f"**Statutory Flag:** {c.cce_statutory_flag}" if c.cce_statutory_flag else ""}

> {c.verbatim_text[:300]}{'...' if len(c.verbatim_text) > 300 else ''}

---

"""
    
    report += f"""
## INTAKE STATUS

- [x] Document parsed
- [x] {total} clauses extracted
- [x] All clauses risk-scored
- [x] {'Embeddings generated' if any(c.embedding_id for c in clauses) else 'Embeddings skipped (ChromaDB unavailable)'}
- [x] Metadata extracted
- [x] Vendor lookup {'completed' if metadata.vendor_ticker else 'no match'}
- [x] Annotations generated

**Ready for:** Compare, Negotiate, Analysis

---

*Generated by CCE-Plus Intake Engine v1.0*
"""
    
    return report


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def process_intake(
    file_path: str,
    db_path: str = 'contracts.db',
    embed: bool = True,
    verbose: bool = False,
    original_filename: str = None
) -> IntakeResult:
    """
    Process complete contract intake.

    Args:
        file_path: Path to contract document
        db_path: Path to SQLite database
        embed: Whether to generate ChromaDB embeddings
        verbose: Print progress messages
        original_filename: Original filename (if file_path is a temp file)
    
    Returns:
        IntakeResult with all processing outcomes
    """
    start_time = datetime.now()
    result = IntakeResult(success=False)
    
    try:
        # STEP 1: Validate
        if verbose: print("1/9 Validating document...")
        valid, errors = validate_document(file_path)
        if not valid:
            result.errors = errors
            return result
        
        # Check duplicate
        document_hash = compute_document_hash(file_path)
        result.document_hash = document_hash
        
        existing_id = check_duplicate(db_path, document_hash)
        if existing_id:
            result.errors = [f"Document already ingested as contract ID {existing_id}"]
            result.contract_id = existing_id
            return result
        
        # STEP 2: Parse
        if verbose: print("2/9 Parsing document...")
        full_text = parse_document(file_path)
        
        if not full_text or len(full_text) < 100:
            result.errors = ["Document appears empty or too short"]
            return result
        
        # STEP 3: Chunk
        if verbose: print("3/9 Extracting clauses...")
        clauses = chunk_document(full_text)
        result.clause_count = len(clauses)
        
        if not clauses:
            result.errors = ["No clauses could be extracted"]
            return result
        
        # STEP 4: Score
        if verbose: print("4/9 Scoring clauses...")
        clauses = score_clauses_batch(clauses)
        
        # STEP 5: Embed
        if embed:
            if verbose: print("5/9 Generating embeddings...")
            clauses = embed_clauses_batch(clauses)
        else:
            if verbose: print("5/9 Skipping embeddings...")
        
        # STEP 6: Extract metadata
        if verbose: print("6/9 Extracting metadata...")
        metadata = extract_metadata(full_text, clauses)
        result.metadata = metadata
        
        # STEP 7: Vendor lookup
        if verbose: print("7/9 Looking up vendor...")
        ticker, cik = lookup_public_company(db_path, metadata.party_vendor)
        metadata.vendor_ticker = ticker
        metadata.vendor_cik = cik
        
        # Generate annotations
        annotations = []
        
        # Risk annotations
        for clause in clauses:
            if clause.cce_risk_level in ('CRITICAL', 'HIGH'):
                annotations.append({
                    'type': 'RISK',
                    'severity': clause.cce_risk_level,
                    'title': f'{clause.cce_risk_level} Risk: {clause.section_number}',
                    'content': f'{clause.section_title} scored {clause.cce_risk_score}/10.0',
                    'source': 'INTAKE'
                })
            
            if clause.cce_statutory_flag:
                annotations.append({
                    'type': 'STATUTORY',
                    'severity': 'CRITICAL',
                    'title': f'Statutory Flag: {clause.cce_statutory_flag}',
                    'content': f'{clause.section_number} may violate {clause.cce_statutory_flag}',
                    'source': 'INTAKE'
                })
            
            if clause.cce_cascade_risk:
                annotations.append({
                    'type': 'CASCADE',
                    'severity': 'HIGH',
                    'title': f'Cascade Risk: {clause.section_number}',
                    'content': f'{clause.section_title} contributes to cross-clause risk',
                    'source': 'INTAKE'
                })
        
        result.annotations = annotations
        
        # STEP 8: Store
        if verbose: print("8/9 Storing data...")
        contract_id = store_intake(
            db_path, file_path, document_hash,
            clauses, metadata, annotations,
            original_filename
        )
        result.contract_id = contract_id
        
        # Calculate risk summary
        result.risk_summary = {
            'total_clauses': len(clauses),
            'critical': sum(1 for c in clauses if c.cce_risk_level == 'CRITICAL'),
            'high': sum(1 for c in clauses if c.cce_risk_level == 'HIGH'),
            'medium': sum(1 for c in clauses if c.cce_risk_level == 'MEDIUM'),
            'low': sum(1 for c in clauses if c.cce_risk_level == 'LOW'),
            'avg_score': round(sum(c.cce_risk_score for c in clauses) / len(clauses), 1),
            'statutory_flags': sum(1 for c in clauses if c.cce_statutory_flag),
            'cascade_risks': sum(1 for c in clauses if c.cce_cascade_risk)
        }
        
        # STEP 9: Report
        if verbose: print("9/9 Generating report...")
        report = generate_intake_report(
            contract_id, file_path, clauses, metadata, annotations
        )
        
        # Save report
        report_path = Path(file_path).with_suffix('.intake_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        result.success = True
        
    except Exception as e:
        result.errors.append(str(e))
    
    finally:
        result.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return result


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python intake_engine.py <contract_file> [db_path]")
        print("Example: python intake_engine.py contract.docx contracts.db")
        sys.exit(1)
    
    file_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else 'contracts.db'
    
    print("=" * 60)
    print("CCE-Plus INTAKE ENGINE")
    print("=" * 60)
    print(f"File: {file_path}")
    print(f"Database: {db_path}")
    print("-" * 60)
    
    result = process_intake(file_path, db_path, verbose=True)
    
    print("-" * 60)
    
    if result.success:
        print(f"✅ INTAKE COMPLETE")
        print(f"   Contract ID: {result.contract_id}")
        print(f"   Clauses: {result.clause_count}")
        print(f"   Avg Risk: {result.risk_summary.get('avg_score', 0)}/10.0")
        print(f"   Critical: {result.risk_summary.get('critical', 0)}")
        print(f"   Statutory Flags: {result.risk_summary.get('statutory_flags', 0)}")
        print(f"   Processing Time: {result.processing_time_ms}ms")
    else:
        print(f"❌ INTAKE FAILED")
        for error in result.errors:
            print(f"   Error: {error}")
    
    print("=" * 60)
