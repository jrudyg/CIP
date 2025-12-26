"""Legal Document Loader - Load and parse legal documents (PDF, DOCX, TXT)"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LegalDocumentLoader:
    """Load and parse legal documents with metadata extraction"""

    # Legal document type patterns
    DOCUMENT_TYPES = {
        'statute': r'(?i)(statute|code|act|law)\s+(?:of\s+)?(\d{4}|[IVXLCDM]+)',
        'contract': r'(?i)(agreement|contract)\s+(between|by and between)',
        'regulation': r'(?i)(regulation|rule|cfr|c\.f\.r\.)\s+(\d+)',
        'case_law': r'(?i)(v\.|vs\.|versus)\s+[A-Z]',
        'opinion': r'(?i)(opinion|decision|ruling)\s+(of|by)',
        'brief': r'(?i)(brief|memorandum)\s+(in support|in opposition)',
    }

    def __init__(self, directory: str):
        self.directory = Path(directory)

    def load_all(self) -> List[Dict]:
        """Load all supported legal documents from directory"""
        documents = []

        for file_path in self.directory.rglob('*'):
            if file_path.is_file():
                doc = self.load_document(file_path)
                if doc:
                    documents.append(doc)

        logger.info(f"Loaded {len(documents)} legal documents")
        return documents

    def load_document(self, file_path: Path) -> Optional[Dict]:
        """Load a single legal document with metadata extraction"""
        suffix = file_path.suffix.lower()

        try:
            if suffix == '.txt':
                doc = self._load_txt(file_path)
            elif suffix == '.pdf':
                doc = self._load_pdf(file_path)
            elif suffix == '.docx':
                doc = self._load_docx(file_path)
            else:
                logger.warning(f"Unsupported file type: {suffix}")
                return None

            if doc:
                # Extract legal metadata
                doc['metadata'] = self._enrich_metadata(doc)

            return doc

        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def _load_txt(self, file_path: Path) -> Dict:
        """Load text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return {
            'content': content,
            'metadata': {
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'txt'
            }
        }

    def _load_pdf(self, file_path: Path) -> Optional[Dict]:
        """Load PDF file"""
        try:
            import pypdf
        except ImportError:
            logger.error("pypdf not installed. Run: pip install pypdf")
            return None

        content = []
        with open(file_path, 'rb') as f:
            pdf = pypdf.PdfReader(f)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content.append(text)

        full_content = '\n\n'.join(content)

        return {
            'content': full_content,
            'metadata': {
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'pdf',
                'pages': len(content)
            }
        }

    def _load_docx(self, file_path: Path) -> Optional[Dict]:
        """Load DOCX file"""
        try:
            import docx
        except ImportError:
            logger.error("python-docx not installed. Run: pip install python-docx")
            return None

        doc = docx.Document(file_path)
        content = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]

        return {
            'content': '\n\n'.join(content),
            'metadata': {
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'docx'
            }
        }

    def _enrich_metadata(self, document: Dict) -> Dict:
        """Extract legal-specific metadata from document content"""
        metadata = document['metadata'].copy()
        content = document['content']

        # Detect document type
        doc_type = self._detect_document_type(content)
        metadata['document_type'] = doc_type

        # Extract citations
        citations = self._extract_citations(content)
        metadata['citations'] = citations
        metadata['citation_count'] = len(citations)

        # Extract parties (for contracts and cases)
        parties = self._extract_parties(content)
        if parties:
            metadata['parties'] = parties

        # Extract dates
        dates = self._extract_dates(content)
        if dates:
            metadata['dates'] = dates

        # Extract jurisdiction indicators
        jurisdiction = self._extract_jurisdiction(content)
        if jurisdiction:
            metadata['jurisdiction'] = jurisdiction

        return metadata

    def _detect_document_type(self, content: str) -> str:
        """Detect the type of legal document"""
        # Check first 2000 characters for type indicators
        sample = content[:2000]

        for doc_type, pattern in self.DOCUMENT_TYPES.items():
            if re.search(pattern, sample):
                return doc_type

        return 'unknown'

    def _extract_citations(self, content: str) -> List[str]:
        """Extract legal citations from content"""
        citations = []

        # US Code citations (e.g., 42 U.S.C. § 1983)
        usc_pattern = r'\d+\s+U\.S\.C\.\s+§\s+\d+(?:\([a-z0-9]+\))?'
        citations.extend(re.findall(usc_pattern, content))

        # Case citations (e.g., Smith v. Jones, 123 F.3d 456)
        case_pattern = r'[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+,\s+\d+\s+[A-Z]\.\s*(?:\d+d\s+)?\d+'
        citations.extend(re.findall(case_pattern, content))

        # CFR citations (e.g., 29 C.F.R. § 1910.1200)
        cfr_pattern = r'\d+\s+C\.F\.R\.\s+§\s+[\d\.]+'
        citations.extend(re.findall(cfr_pattern, content))

        # Public Law citations (e.g., Pub. L. No. 117-58)
        pl_pattern = r'Pub\.\s+L\.\s+No\.\s+\d+-\d+'
        citations.extend(re.findall(pl_pattern, content))

        return list(set(citations))  # Remove duplicates

    def _extract_parties(self, content: str) -> Optional[List[str]]:
        """Extract party names from contracts or cases"""
        # Contract parties pattern
        contract_pattern = r'(?i)(?:between|by and between)\s+([A-Z][A-Za-z\s,\.]+)\s+(?:and|&)\s+([A-Z][A-Za-z\s,\.]+)'
        match = re.search(contract_pattern, content[:1000])
        if match:
            return [match.group(1).strip(), match.group(2).strip()]

        # Case parties pattern
        case_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        match = re.search(case_pattern, content[:1000])
        if match:
            return [match.group(1).strip(), match.group(2).strip()]

        return None

    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from legal documents"""
        dates = []

        # Month Day, Year format (e.g., January 1, 2024)
        pattern1 = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
        dates.extend(re.findall(pattern1, content[:2000]))

        # MM/DD/YYYY format
        pattern2 = r'\d{1,2}/\d{1,2}/\d{4}'
        dates.extend(re.findall(pattern2, content[:2000]))

        return list(set(dates))

    def _extract_jurisdiction(self, content: str) -> Optional[str]:
        """Extract jurisdiction from legal document"""
        # US State patterns
        states = [
            'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
            'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
            'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
            'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
            'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
            'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
            'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
            'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
            'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
            'West Virginia', 'Wisconsin', 'Wyoming'
        ]

        sample = content[:2000]
        for state in states:
            if re.search(rf'\b{state}\b', sample):
                return state

        # Federal jurisdiction
        if re.search(r'\b(?:federal|Federal|U\.S\.|United States)\b', sample):
            return 'Federal'

        return None
