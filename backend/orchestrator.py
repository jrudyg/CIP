"""
CIP Orchestrator
Coordinates contract analysis workflows with Claude AI integration
Implements CONTRACT_REVIEW_SYSTEM v1.2 logic with structured risk assessments
v4.1: Phase 4B - Unified AI error framework with call_claude_safe()
"""

import os
import json
import sqlite3
import ssl
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import logging
from dataclasses import dataclass, asdict

# Import configuration
try:
    from config import DEFAULT_MODEL
except ImportError:
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"  # Fallback if config not available

# Anthropic SDK
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Document processing
try:
    from docx import Document
    import PyPDF2
except ImportError:
    Document = None
    PyPDF2 = None

# Phase 4B: Import unified AIResult from models
try:
    from .models import AIResult, AI_ERROR_KEYS, AI_MAX_RETRIES, AI_RETRY_ALLOWED_CATEGORIES
except ImportError:
    from models import AIResult, AI_ERROR_KEYS, AI_MAX_RETRIES, AI_RETRY_ALLOWED_CATEGORIES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ContractContext:
    """User-provided contract context for analysis"""
    position: str  # vendor, customer, landlord, tenant, etc.
    leverage: str  # strong, moderate, weak
    narrative: str  # specific concerns and priorities
    contract_type: Optional[str] = None
    parties: Optional[str] = None


@dataclass
class RiskItem:
    """Individual risk finding (v1.4 with redline support)"""
    section_number: str
    section_title: str
    risk_level: str  # DEALBREAKER, CRITICAL, IMPORTANT, STANDARD
    category: str  # payment, liability, ip, indemnification, etc.
    finding: str
    recommendation: str
    confidence: float  # 0.0 to 1.0
    pattern_id: Optional[str] = None
    clause_text: Optional[str] = None  # v1.4: Original clause text for redlining
    redline_suggestion: Optional[str] = None  # v1.4: ~~deletions~~ and `additions`
    cascade_impacts: Optional[List[str]] = None  # v1.4: Impacted sections


@dataclass
class RiskAssessment:
    """Complete risk assessment for a contract"""
    contract_id: int
    overall_risk: str  # HIGH, MEDIUM, LOW
    critical_items: List[RiskItem]
    important_items: List[RiskItem]
    standard_items: List[RiskItem]
    dealbreakers: List[RiskItem]
    confidence_score: float
    analysis_date: str
    context: ContractContext
    # v1.6 additions
    risk_by_category: Dict = None
    clauses_reviewed: int = 0
    clauses_flagged: int = 0
    # v1.7 additions
    severity_counts: Dict = None
    low_risk_clauses: List = None


@dataclass
class ClauseAnalysis:
    """Analysis of a specific contract clause"""
    section_number: str
    title: str
    original_text: str
    risk_level: str
    category: str
    issues: List[str]
    recommendations: List[str]
    pattern_matches: List[str]


# ============================================================================
# PHASE 4B: UNIFIED AI ERROR FRAMEWORK
# ============================================================================

# Global Anthropic client (initialized by create_orchestrator or call_claude_safe)
_claude_client: Optional[Any] = None


def _get_claude_client() -> Any:
    """Get or create the global Anthropic client."""
    global _claude_client
    if _claude_client is None:
        if Anthropic is None:
            raise ImportError("anthropic package not installed")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        _claude_client = Anthropic(api_key=api_key)
    return _claude_client


def _classify_exception(exception: Exception, purpose: str) -> Tuple[str, str]:
    """
    Classify an exception into error_category and error_message_key.
    Used by call_claude_safe() for unified error handling.

    Args:
        exception: The caught exception
        purpose: Module purpose ("analyze" | "compare" | "redline" | "chat")

    Returns:
        Tuple of (error_category, error_message_key)
    """
    error_str = str(exception).lower()
    exc_type = type(exception).__name__

    # Network errors: ConnectionResetError, ConnectionError, OSError, ssl.SSLError, timeout
    if isinstance(exception, (ConnectionResetError, ConnectionError, OSError)):
        error_category = "network_error"
    elif isinstance(exception, ssl.SSLError):
        error_category = "network_error"
    elif "timeout" in error_str or "timed out" in error_str:
        error_category = "network_error"
    # Auth errors: 401, 403
    elif "401" in error_str or "403" in error_str or "unauthorized" in error_str or "forbidden" in error_str:
        error_category = "auth_error"
    # Payload errors: 400, 413, 422
    elif "400" in error_str or "413" in error_str or "422" in error_str or "payload" in error_str or "too large" in error_str:
        error_category = "payload_error"
    # Everything else is internal_error
    else:
        error_category = "internal_error"

    # Get module-specific error message key
    error_message_key = AI_ERROR_KEYS.get(purpose, AI_ERROR_KEYS["analyze"]).get(error_category, f"{purpose}.internal_failure")

    return error_category, error_message_key


def call_claude_safe(
    payload: dict,
    purpose: str,
    retry_count: int = 0,
    contract_id: Optional[int] = None,
    model: str = None
) -> AIResult:
    """
    Phase 4B: Unified Claude API wrapper for all modules.

    This function:
    - Wraps ALL Claude API calls across Analyze, Compare, Redline, Chat
    - Applies CAI exception taxonomy
    - Enforces retry policy (max 2 retries, only for network_error/internal_error)
    - Logs: contract_id, module, error_category, exception_type (never raw traces to UI)
    - Returns AIResult (never raw exceptions)

    Args:
        payload: Dict with 'system', 'messages', and optional 'max_tokens'
        purpose: Module purpose ("analyze" | "compare" | "redline" | "chat")
        retry_count: Current retry attempt (0 = first try)
        contract_id: Optional contract ID for logging
        model: Optional model override (defaults to DEFAULT_MODEL)

    Returns:
        AIResult with success=True and data, or success=False with error info
    """
    used_model = model or DEFAULT_MODEL

    try:
        client = _get_claude_client()

        # Extract payload components
        system_prompt = payload.get('system', '')
        messages = payload.get('messages', [])
        max_tokens = payload.get('max_tokens', 4096)

        # Make the API call
        message = client.messages.create(
            model=used_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )

        # Extract response text
        response_text = message.content[0].text if message.content else ""

        logger.info(
            f"call_claude_safe success: purpose={purpose}, "
            f"contract_id={contract_id}, model={used_model}, "
            f"response_length={len(response_text)}"
        )

        return AIResult.success_result(
            data={'response': response_text, 'raw_message': message},
            module=purpose
        )

    except Exception as e:
        # Classify the exception
        error_category, error_message_key = _classify_exception(e, purpose)
        exc_type = type(e).__name__

        # Log the error (structured, no raw traces to UI)
        logger.error(
            f"call_claude_safe error: purpose={purpose}, "
            f"contract_id={contract_id}, error_category={error_category}, "
            f"exception_type={exc_type}, model={used_model}, "
            f"retry_count={retry_count}"
        )

        # Check if retry is allowed
        can_retry = (
            error_category in AI_RETRY_ALLOWED_CATEGORIES and
            retry_count < AI_MAX_RETRIES
        )

        if can_retry:
            # Exponential backoff: 1s, 2s
            wait_time = (retry_count + 1) * 1.0
            logger.info(f"call_claude_safe retrying in {wait_time}s (attempt {retry_count + 1}/{AI_MAX_RETRIES})")
            time.sleep(wait_time)

            return call_claude_safe(
                payload=payload,
                purpose=purpose,
                retry_count=retry_count + 1,
                contract_id=contract_id,
                model=model
            )

        # No retry - return error result
        return AIResult.error_result(
            error_category=error_category,
            error_message_key=error_message_key,
            module=purpose,
            exception_type=exc_type,
            retry_count=retry_count
        )


# Legacy compatibility aliases (deprecated, use AIResult directly)
AnalyzeResult = AIResult
ANALYZE_ERROR_KEYS = AI_ERROR_KEYS.get("analyze", {})


class AnalyzeError(Exception):
    """Legacy exception class - use call_claude_safe() instead."""
    def __init__(self, error_category: str, error_message_key: str):
        self.error_category = error_category
        self.error_message_key = error_message_key
        super().__init__(error_message_key)


class AnalyzeNetworkError(AnalyzeError):
    """Legacy - network errors"""
    pass


class AnalyzeAuthError(AnalyzeError):
    """Legacy - auth errors"""
    pass


class AnalyzePayloadError(AnalyzeError):
    """Legacy - payload errors"""
    pass


class AnalyzeInternalError(AnalyzeError):
    """Legacy - internal errors"""
    pass


def classify_analyze_error(exception: Exception) -> AIResult:
    """
    Legacy compatibility function - use call_claude_safe() instead.
    Classify any exception into an AIResult with proper error category.
    """
    error_category, error_message_key = _classify_exception(exception, "analyze")
    return AIResult.error_result(
        error_category=error_category,
        error_message_key=error_message_key,
        module="analyze",
        exception_type=type(exception).__name__
    )


# ============================================================================
# KNOWLEDGE BASE LOADER
# ============================================================================

class KnowledgeBaseLoader:
    """Loads and manages contract review knowledge base from /knowledge/ directory"""

    def __init__(self, knowledge_dir: str, prompts_dir: str = None):
        self.knowledge_dir = Path(knowledge_dir)
        self.prompts_dir = Path(prompts_dir) if prompts_dir else Path(knowledge_dir).parent / "backend" / "prompts"
        self.knowledge_base: Dict[str, str] = {}
        self.contract_review_system = None
        self.clause_patterns = None
        self.quick_reference = None
        self.analysis_prompt = None  # v1.4: Dedicated analysis prompt

        if not self.knowledge_dir.exists():
            logger.warning(f"Knowledge directory not found: {knowledge_dir}")
            return

        self._load_knowledge_base()
        self._load_analysis_prompt()

    def _load_knowledge_base(self):
        """Load all markdown files from knowledge directory"""
        logger.info(f"Loading knowledge base from {self.knowledge_dir}")

        # Load CONTRACT_REVIEW_SYSTEM (latest version)
        review_system_files = list(self.knowledge_dir.glob("01_CONTRACT_REVIEW_SYSTEM*.md"))
        if review_system_files:
            latest = sorted(review_system_files)[-1]  # Get latest version
            with open(latest, 'r', encoding='utf-8') as f:
                self.contract_review_system = f.read()
                self.knowledge_base['contract_review_system'] = self.contract_review_system
                logger.info(f"Loaded: {latest.name}")

        # Load CLAUSE_PATTERN_LIBRARY (latest version)
        pattern_files = list(self.knowledge_dir.glob("02_CLAUSE_PATTERN_LIBRARY*.md"))
        if pattern_files:
            latest = sorted(pattern_files)[-1]  # Get latest version
            with open(latest, 'r', encoding='utf-8') as f:
                self.clause_patterns = f.read()
                self.knowledge_base['clause_patterns'] = self.clause_patterns
                logger.info(f"Loaded: {latest.name}")

        # Load QUICK_REFERENCE_CHECKLIST (latest version)
        checklist_files = list(self.knowledge_dir.glob("03_QUICK_REFERENCE*.md"))
        if checklist_files:
            latest = sorted(checklist_files)[-1]  # Get latest version
            with open(latest, 'r', encoding='utf-8') as f:
                self.quick_reference = f.read()
                self.knowledge_base['quick_reference'] = self.quick_reference
                logger.info(f"Loaded: {latest.name}")

        # Load all other markdown files
        for md_file in self.knowledge_dir.glob("*.md"):
            if not md_file.name.startswith(('01_', '02_', '03_')):
                with open(md_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base[md_file.stem] = f.read()
                    logger.info(f"Loaded: {md_file.name}")

        logger.info(f"Loaded {len(self.knowledge_base)} knowledge base documents")

    def _load_analysis_prompt(self):
        """Load dedicated analysis prompt from prompts directory (v1.4)"""
        analysis_prompt_path = self.prompts_dir / "analysis_prompt.md"

        if analysis_prompt_path.exists():
            with open(analysis_prompt_path, 'r', encoding='utf-8') as f:
                self.analysis_prompt = f.read()
                logger.info(f"Loaded analysis prompt: {analysis_prompt_path}")
        else:
            logger.warning(f"Analysis prompt not found: {analysis_prompt_path}")
            self.analysis_prompt = None

    def get_system_prompt(self, context: ContractContext, contract_category: str = "A") -> str:
        """Generate system prompt with knowledge base context"""
        # v1.4: Use dedicated analysis prompt if available
        if self.analysis_prompt:
            # Category labels for prompt clarity
            category_labels = {
                "A": "Final Binding Agreement",
                "B": "Interim/Preliminary (MOU, LOI, Term Sheet)",
                "C": "Version Comparison",
                "D": "Dual-Agreement Review"
            }
            prompt_parts = [
                self.analysis_prompt,
                "\n\n# CONTRACT CONTEXT\n",
                f"**Position:** {context.position}",
                f"**Leverage:** {context.leverage}",
                f"**Contract Category:** {contract_category} - {category_labels.get(contract_category, 'Unknown')}",
                f"**Specific Concerns:** {context.narrative}"
            ]

            # Append clause patterns if available
            if self.clause_patterns:
                prompt_parts.append("\n\n# CLAUSE PATTERN LIBRARY REFERENCE\n")
                prompt_parts.append(self.clause_patterns)

            logger.info("Using v1.4 analysis prompt with CONTRACT_REVIEW_SYSTEM v1.2 integration")
            return "\n".join(prompt_parts)

        # Fallback to legacy prompt construction
        prompt_parts = [
            "You are a senior contract attorney specializing in contract risk analysis.",
            "\n# CONTRACT REVIEW METHODOLOGY\n"
        ]

        if self.contract_review_system:
            prompt_parts.append(self.contract_review_system)

        prompt_parts.append("\n# CLAUSE PATTERN LIBRARY\n")
        if self.clause_patterns:
            prompt_parts.append(self.clause_patterns)

        prompt_parts.append("\n# CONTRACT CONTEXT\n")
        prompt_parts.append(f"Position: {context.position}")
        prompt_parts.append(f"Leverage: {context.leverage}")
        prompt_parts.append(f"Specific Concerns: {context.narrative}")

        prompt_parts.append("\n# CONFIDENCE THRESHOLDS\n")
        prompt_parts.append("- DEALBREAKER: Any uncertainty → Flag immediately")
        prompt_parts.append("- CRITICAL (95%+): Payment, liability, IP, indemnification")
        prompt_parts.append("- IMPORTANT (90%+): Warranties, termination, assignment")
        prompt_parts.append("- STANDARD (85%+): Boilerplate, notices, governing law")

        return "\n".join(prompt_parts)

    def get_analysis_instructions(self) -> str:
        """Get specific analysis instructions"""
        return """
Analyze the contract following the 10-step process:
1. Parse context (position/leverage/narrative)
2. Map contract structure (sections, headings)
3. Holistic risk assessment
4. Sequential clause processing
5. Cascade detection
6. Present findings with confidence levels
7. Identify dealbreakers immediately
8. Provide recommendations with success rates
9. Structure output as JSON risk assessment
10. Flag items requiring user review

For each risk item, provide:
- Section number and title
- Risk level (DEALBREAKER, CRITICAL, IMPORTANT, STANDARD)
- Category (payment, liability, ip, indemnification, etc.)
- Specific finding
- Recommendation with success probability
- Confidence score (0.0-1.0)
"""


# ============================================================================
# DOCUMENT EXTRACTOR (from comparison tool pattern)
# ============================================================================

class ContractDocumentExtractor:
    """Extract text and structure from contract documents"""

    @staticmethod
    def extract_from_docx(file_path: str) -> Dict:
        """Extract text from DOCX file"""
        if Document is None:
            raise ImportError("python-docx not installed")

        doc = Document(file_path)
        sections = []
        full_text = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)

                # Detect sections (simple heuristic)
                if len(text) < 200 and any(char.isdigit() for char in text[:20]):
                    sections.append({
                        'text': text,
                        'is_heading': True
                    })
                else:
                    sections.append({
                        'text': text,
                        'is_heading': False
                    })

        return {
            'full_text': '\n'.join(full_text),
            'sections': sections,
            'format': 'docx'
        }

    @staticmethod
    def extract_from_pdf(file_path: str) -> Dict:
        """Extract text from PDF file"""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 not installed")

        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            full_text = []

            for page in pdf_reader.pages:
                full_text.append(page.extract_text())

        return {
            'full_text': '\n'.join(full_text),
            'sections': [],  # PDF section detection would require more sophisticated parsing
            'format': 'pdf'
        }

    @staticmethod
    def extract_from_txt(file_path: str) -> Dict:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        return {
            'full_text': full_text,
            'sections': [],
            'format': 'txt'
        }

    @classmethod
    def extract(cls, file_path: str) -> Dict:
        """Auto-detect format and extract"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        extractors = {
            '.docx': cls.extract_from_docx,
            '.pdf': cls.extract_from_pdf,
            '.txt': cls.extract_from_txt
        }

        extractor = extractors.get(suffix)
        if not extractor:
            raise ValueError(f"Unsupported file format: {suffix}")

        return extractor(str(path))

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract full text from document (convenience method)"""
        result = cls.extract(file_path)
        return result.get('full_text', '')


# ============================================================================
# CONTRACT ANALYZER (Claude AI integration)
# ============================================================================

class ContractAnalyzer:
    """Analyzes contracts using Claude AI with knowledge base"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        knowledge_base: Optional[KnowledgeBaseLoader] = None
    ):
        if Anthropic is None:
            raise ImportError("anthropic package not installed")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.knowledge_base = knowledge_base

        logger.info(f"Contract Analyzer initialized with model: {model}")

    def analyze_contract(
        self,
        contract_text: str,
        context: ContractContext,
        max_tokens: int = 4096,
        pattern_prompt: str = None
    ) -> RiskAssessment:
        """
        Analyze contract and return structured risk assessment

        Args:
            contract_text: Full contract text
            context: Contract context (position, leverage, narrative)
            max_tokens: Maximum tokens for response
            pattern_prompt: Optional composed prompt with pattern cards (from PromptComposer)
            contract_id: Existing contract ID (skip INSERT if provided)

        Returns:
            RiskAssessment with structured findings
        """
        logger.info("Starting contract analysis")

        # Build system prompt - use pattern_prompt if provided, otherwise fall back to knowledge base
        if pattern_prompt:
            # Pattern prompt includes context header + pattern cards + instructions
            system_prompt = pattern_prompt
            logger.info("Using pattern-enhanced prompt from PromptComposer")
        else:
            system_prompt = self.knowledge_base.get_system_prompt(context) if self.knowledge_base else self._default_system_prompt()

        # Build analysis prompt
        user_prompt = self._build_analysis_prompt(contract_text, context)

        # Phase 4B: Use unified call_claude_safe() for all Claude API calls
        payload = {
            'system': system_prompt,
            'messages': [{"role": "user", "content": user_prompt}],
            'max_tokens': max_tokens
        }

        result = call_claude_safe(
            payload=payload,
            purpose="analyze",
            contract_id=getattr(context, 'contract_id', None),
            model=self.model
        )

        if not result.success:
            # Convert AIResult error to legacy AnalyzeError for backward compatibility
            error_category = result.error_category
            error_key = result.error_message_key

            if error_category == "network_error":
                raise AnalyzeNetworkError(error_category, error_key)
            elif error_category == "auth_error":
                raise AnalyzeAuthError(error_category, error_key)
            elif error_category == "payload_error":
                raise AnalyzePayloadError(error_category, error_key)
            else:
                raise AnalyzeInternalError(error_category, error_key)

        # Parse response from AIResult
        response_text = result.data.get('response', '')
        risk_assessment = self._parse_response(response_text, context)

        logger.info(f"Analysis complete - Overall risk: {risk_assessment.overall_risk}")
        return risk_assessment

    def analyze_clause(
        self,
        clause_text: str,
        section_number: str,
        context: ContractContext
    ) -> ClauseAnalysis:
        """Analyze a specific clause in detail"""
        system_prompt = "You are a contract attorney analyzing specific contract clauses for risk."

        user_prompt = f"""
Analyze this contract clause:

Section: {section_number}
Text: {clause_text}

Context:
- Position: {context.position}
- Leverage: {context.leverage}
- Concerns: {context.narrative}

Provide:
1. Risk level (DEALBREAKER, CRITICAL, IMPORTANT, STANDARD)
2. Category (payment, liability, ip, etc.)
3. Specific issues identified
4. Recommendations for improvement
5. Matching patterns from clause library

Format as JSON.
"""

        # Phase 4B: Use unified call_claude_safe()
        payload = {
            'system': system_prompt,
            'messages': [{"role": "user", "content": user_prompt}],
            'max_tokens': 2048
        }

        result = call_claude_safe(
            payload=payload,
            purpose="analyze",
            contract_id=getattr(context, 'contract_id', None),
            model=self.model
        )

        if not result.success:
            # Raise legacy error for backward compatibility
            raise AnalyzeInternalError(result.error_category, result.error_message_key)

        response = result.data.get('response', '')
        return self._parse_clause_analysis(response, section_number, clause_text)

    def _build_analysis_prompt(self, contract_text: str, context: ContractContext) -> str:
        """Build comprehensive analysis prompt (v1.4 with redline support)"""
        # v1.4: Enhanced output format with redline_suggestion and cascade_impacts
        return f"""
Analyze the following contract text and return structured findings.

## CONTRACT TEXT
{contract_text[:15000]}

## REQUIRED OUTPUT FORMAT (JSON only)

Return ONLY a valid JSON object with this exact structure:

{{
    "overall_risk": "HIGH|MEDIUM|LOW",
    "confidence_score": 0.85,
    "executive_summary": "2-3 sentence overview of key findings",
    "dealbreakers": [
        {{
            "section_number": "X.X",
            "clause_title": "Section Title",
            "clause_text": "EXACT verbatim quote from contract",
            "risk_level": "DEALBREAKER",
            "category": "liability|payment|ip|indemnification|termination|confidentiality|scope|warranty|insurance|compliance|other",
            "issue": "Specific problem identified",
            "pattern_match": "Pattern ID if matched (e.g., 2.1.4)",
            "redline_suggestion": "Original with ~~deletions~~ and `additions`",
            "cascade_impacts": ["Section Y.Y - reason"],
            "confidence": 0.98
        }}
    ],
    "critical_items": [
        {{
            "section_number": "X.X",
            "clause_title": "Section Title",
            "clause_text": "EXACT verbatim quote",
            "risk_level": "CRITICAL",
            "category": "category",
            "issue": "Specific problem",
            "pattern_match": "Pattern ID",
            "redline_suggestion": "Text with ~~deletions~~ and `additions`",
            "cascade_impacts": [],
            "confidence": 0.95
        }}
    ],
    "important_items": [],
    "standard_items": []
}}

## CRITICAL REQUIREMENTS

1. **EXACT QUOTES**: clause_text MUST be verbatim from the contract - no paraphrasing
2. **REDLINE FORMAT**:
   - Deletions: ~~strikethrough~~
   - Additions: `backtick code`
   - Example: "Vendor shall ~~not~~ be liable `up to $100,000`"
3. **CASCADE DETECTION**: Check these dependencies:
   - Payment → Acceptance, Termination
   - Liability → Insurance, Indemnification
   - Scope → Deliverables, Payment
4. **CONFIDENCE THRESHOLDS**:
   - DEALBREAKER: Flag immediately, any uncertainty
   - CRITICAL: 95%+ confidence required
   - IMPORTANT: 90%+ confidence required
   - STANDARD: 85%+ confidence required
5. **RETURN JSON ONLY**: No explanatory text before or after

Analyze comprehensively and return structured JSON only.
"""

    def _parse_response(self, response_text: str, context: ContractContext) -> RiskAssessment:
        """Parse Claude's response into RiskAssessment structure"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            logger.info(f"[PARSE] Response length: {len(response_text)}, JSON bounds: {json_start} to {json_end}")

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                logger.info(f"[PARSE] Parsed JSON keys: {list(data.keys())}")
                logger.info(f"[PARSE] Findings counts - dealbreakers: {len(data.get('dealbreakers', []))}, critical: {len(data.get('critical_items', []))}, important: {len(data.get('important_items', []))}")
            else:
                # Fallback: create structured response from text
                logger.warning(f"[PARSE] No JSON found, using fallback. Response preview: {response_text[:200]}")
                data = self._fallback_parse(response_text)

            # Convert to RiskItem objects with safe field handling
            def safe_risk_item(item: dict) -> RiskItem:
                """Safely construct RiskItem, handling missing/extra fields (v1.4)"""
                # Map v1.4 JSON fields to dataclass fields
                # clause_title -> section_title, issue -> finding
                return RiskItem(
                    section_number=item.get('section_number', 'N/A'),
                    section_title=item.get('clause_title') or item.get('section_title', 'Unknown Section'),
                    risk_level=item.get('risk_level', 'STANDARD'),
                    category=item.get('category', 'general'),
                    finding=item.get('issue') or item.get('finding', ''),
                    recommendation=item.get('redline_suggestion') or item.get('recommendation', ''),
                    confidence=float(item.get('confidence', 0.5)),
                    pattern_id=item.get('pattern_match') or item.get('pattern_id'),
                    clause_text=item.get('clause_text'),
                    redline_suggestion=item.get('redline_suggestion'),
                    cascade_impacts=item.get('cascade_impacts', [])
                )

            dealbreakers = [safe_risk_item(item) for item in data.get('dealbreakers', [])]
            critical = [safe_risk_item(item) for item in data.get('critical_items', [])]
            important = [safe_risk_item(item) for item in data.get('important_items', [])]
            standard = [safe_risk_item(item) for item in data.get('standard_items', [])]

            return RiskAssessment(
                contract_id=0,  # Will be set by orchestrator
                overall_risk=data.get('overall_risk', 'MEDIUM'),
                critical_items=critical,
                important_items=important,
                standard_items=standard,
                dealbreakers=dealbreakers,
                confidence_score=data.get('confidence_score', 0.85),
                analysis_date=datetime.now().isoformat(),
                context=context,
                # v1.6 additions
                risk_by_category=data.get('risk_by_category', {}),
                clauses_reviewed=data.get('clauses_reviewed', 0),
                clauses_flagged=data.get('clauses_flagged', 0),
                # v1.7 additions
                severity_counts=data.get('severity_counts', {}),
                low_risk_clauses=data.get('low_risk_clauses', [])
            )

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            # Return minimal assessment
            return RiskAssessment(
                contract_id=0,
                overall_risk="UNKNOWN",
                critical_items=[],
                important_items=[],
                standard_items=[],
                dealbreakers=[],
                confidence_score=0.0,
                analysis_date=datetime.now().isoformat(),
                context=context
            )

    def _fallback_parse(self, text: str) -> Dict:
        """Fallback parsing when JSON extraction fails"""
        return {
            'overall_risk': 'MEDIUM',
            'confidence_score': 0.5,
            'dealbreakers': [],
            'critical_items': [],
            'important_items': [],
            'standard_items': []
        }

    def _parse_clause_analysis(self, response: str, section_number: str, original_text: str) -> ClauseAnalysis:
        """Parse clause-specific analysis"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            data = json.loads(response[json_start:json_end])

            return ClauseAnalysis(
                section_number=section_number,
                title=data.get('title', ''),
                original_text=original_text,
                risk_level=data.get('risk_level', 'STANDARD'),
                category=data.get('category', 'general'),
                issues=data.get('issues', []),
                recommendations=data.get('recommendations', []),
                pattern_matches=data.get('pattern_matches', [])
            )
        except Exception as e:
            logger.error(f"Error parsing clause analysis: {e}")
            return ClauseAnalysis(
                section_number=section_number,
                title="",
                original_text=original_text,
                risk_level="UNKNOWN",
                category="general",
                issues=[],
                recommendations=[],
                pattern_matches=[]
            )

    def _default_system_prompt(self) -> str:
        """Default system prompt if no knowledge base"""
        return """You are a senior contract attorney specializing in contract risk analysis.
Analyze contracts for risks, focusing on payment terms, liability, indemnification, IP rights,
termination, and other critical business terms. Provide structured, actionable recommendations."""


# ============================================================================
# CONTRACT ORCHESTRATOR (Main coordinator)
# ============================================================================

class ContractOrchestrator:
    """Main orchestrator for contract analysis workflows"""

    def __init__(
        self,
        db_path: Optional[str] = None,
        knowledge_dir: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        # Database connection
        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "contracts.db")
        self._db_connections: Dict[int, sqlite3.Connection] = {}  # Thread-local connections

        # Knowledge base
        knowledge_path = knowledge_dir or str(Path(__file__).parent.parent / "knowledge")
        self.knowledge_base = KnowledgeBaseLoader(knowledge_path)

        # Contract analyzer
        self.analyzer = ContractAnalyzer(
            api_key=api_key,
            knowledge_base=self.knowledge_base
        )

        # Document extractor
        self.extractor = ContractDocumentExtractor()

        # Registered tools
        self.tools: Dict[str, callable] = {}
        self.agents: Dict[str, object] = {}

        logger.info("Contract Orchestrator initialized")

    def _get_db_conn(self):
        """Get thread-local database connection"""
        import threading
        thread_id = threading.current_thread().ident

        if thread_id not in self._db_connections:
            try:
                self._db_connections[thread_id] = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False
                )
                self._db_connections[thread_id].row_factory = sqlite3.Row
                self._db_connections[thread_id].execute("PRAGMA foreign_keys = ON")
                logger.debug(f"Created DB connection for thread {thread_id}")
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                return None

        return self._db_connections[thread_id]

    def register_agent(self, name: str, agent):
        """Register an agent with the orchestrator"""
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")

    def register_tool(self, name: str, tool):
        """Register a tool with the orchestrator"""
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def analyze_contract_file(
        self,
        file_path: str,
        context: ContractContext,
        save_to_db: bool = True,
        pattern_prompt: str = None,
        contract_id: int = None
    ) -> RiskAssessment:
        """
        Complete contract analysis workflow

        Args:
            file_path: Path to contract file
            context: Contract context (position, leverage, narrative)
            save_to_db: Save results to database
            pattern_prompt: Optional composed prompt with pattern cards (from PromptComposer)
            contract_id: Existing contract ID (skip INSERT if provided)

        Returns:
            RiskAssessment with complete analysis
        """
        logger.info(f"Analyzing contract: {file_path}")

        # Extract document
        extracted = self.extractor.extract(file_path)
        contract_text = extracted['full_text']

        # Analyze with Claude - pass pattern_prompt if provided
        risk_assessment = self.analyzer.analyze_contract(
            contract_text,
            context,
            pattern_prompt=pattern_prompt
        )

        # Save to database if requested
        if save_to_db:
            conn = self._get_db_conn()
            if conn:
                if contract_id:
                    # Use existing contract - don't create duplicate
                    risk_assessment.contract_id = contract_id
                else:
                    # New contract - insert
                    contract_id = self._save_contract(file_path, context)
                    risk_assessment.contract_id = contract_id
                self._save_risk_assessment(risk_assessment)

                # Also save to analysis_snapshots for historical tracking
                all_clauses = (
                    [asdict(item) for item in risk_assessment.dealbreakers] +
                    [asdict(item) for item in risk_assessment.critical_items] +
                    [asdict(item) for item in risk_assessment.important_items] +
                    [asdict(item) for item in risk_assessment.standard_items] +
                    (risk_assessment.low_risk_clauses or [])
                )
                categories = risk_assessment.risk_by_category or {}
                save_analysis_snapshot(
                    db_path=self.db_path,
                    contract_id=risk_assessment.contract_id,
                    overall_risk=risk_assessment.overall_risk,
                    categories=list(categories.values()) if isinstance(categories, dict) else categories,
                    clauses=all_clauses
                )

        return risk_assessment

    def _save_contract(self, file_path: str, context: ContractContext) -> int:
        """Save contract metadata to database"""
        conn = self._get_db_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contracts (
                filename, filepath, contract_type, position, leverage, narrative, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            Path(file_path).name,
            file_path,
            context.contract_type,
            context.position,
            context.leverage,
            context.narrative,
            json.dumps(asdict(context))
        ))

        conn.commit()
        return cursor.lastrowid

    def _save_risk_assessment(self, assessment: RiskAssessment):
        """Save risk assessment to database"""
        conn = self._get_db_conn()
        cursor = conn.cursor()

        # Save overall assessment
        cursor.execute("""
            INSERT INTO risk_assessments (
                contract_id, overall_risk, critical_items, dealbreakers,
                confidence_score, analysis_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            assessment.contract_id,
            assessment.overall_risk,
            json.dumps([asdict(item) for item in assessment.critical_items]),
            json.dumps([asdict(item) for item in assessment.dealbreakers]),
            assessment.confidence_score,
            json.dumps(asdict(assessment), default=str)
        ))

        # Update workflow_stage to 1 (Analyzed)
        cursor.execute("UPDATE contracts SET workflow_stage = 1 WHERE id = ?", (assessment.contract_id,))
        cursor.execute("UPDATE contracts SET status = 'review' WHERE id = ? AND status = 'intake'", (assessment.contract_id,))

        # Save individual clauses
        all_items = (
            assessment.dealbreakers +
            assessment.critical_items +
            assessment.important_items +
            assessment.standard_items
        )

        for item in all_items:
            cursor.execute("""
                INSERT INTO clauses (
                    contract_id, section_number, title, text, category, risk_level, pattern_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment.contract_id,
                item.section_number,
                item.section_title,
                item.finding,
                item.category,
                item.risk_level,
                item.pattern_id
            ))

        conn.commit()
        logger.info(f"Saved risk assessment for contract {assessment.contract_id}")

    def get_contract(self, contract_id: int) -> Optional[Dict]:
        """Retrieve contract from database"""
        conn = self._get_db_conn()
        if not conn:
            return None

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def get_risk_assessment(self, contract_id: int) -> Optional[Dict]:
        """Retrieve risk assessment from database"""
        conn = self._get_db_conn()
        if not conn:
            return None

        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM risk_assessments
            WHERE contract_id = ?
            ORDER BY assessment_date DESC
            LIMIT 1
        """, (contract_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def execute_workflow(self, workflow_name: str, params: Dict):
        """Execute a named workflow"""
        workflows = {
            'analyze': self._workflow_analyze,
            'compare': self._workflow_compare,
            'risk_report': self._workflow_risk_report
        }

        workflow = workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        return workflow(params)

    def _workflow_analyze(self, params: Dict):
        """Analysis workflow"""
        file_path = params.get('file_path')
        context = ContractContext(**params.get('context', {}))

        return self.analyze_contract_file(file_path, context)

    def _workflow_compare(self, params: Dict):
        """Comparison workflow (placeholder for comparison tool integration)"""
        # Integration point for comparison tool
        comparison_tool = self.tools.get('comparison')
        if comparison_tool:
            return comparison_tool.compare(**params)

        raise NotImplementedError("Comparison workflow requires comparison tool registration")

    def _workflow_risk_report(self, params: Dict):
        """Risk report generation workflow"""
        contract_id = params.get('contract_id')
        assessment = self.get_risk_assessment(contract_id)

        if not assessment:
            raise ValueError(f"No assessment found for contract {contract_id}")

        # Format for reporting
        return {
            'contract_id': contract_id,
            'overall_risk': assessment['overall_risk'],
            'confidence': assessment['confidence_score'],
            'critical_count': len(json.loads(assessment['critical_items'])),
            'dealbreaker_count': len(json.loads(assessment['dealbreakers'])),
            'report_date': datetime.now().isoformat()
        }

    def extract_metadata(self, file_path: str, filename: str) -> Dict:
        """
        Extract contract metadata using Claude AI

        Args:
            file_path: Path to contract file
            filename: Original filename

        Returns:
            Dict with extracted metadata: {
                'type': str,
                'parties': list,
                'perspective': str,
                'dates': dict,
                'amounts': dict,
                'jurisdiction': str,
                'confidence': float
            }
        """
        try:
            logger.info(f"Extracting metadata from: {filename}")

            # Extract document text
            doc_text = self.extractor.extract_text(file_path)

            if not doc_text or len(doc_text) < 100:
                logger.warning("Insufficient document content for metadata extraction")
                return {
                    'type': 'Unknown',
                    'parties': [],
                    'perspective': 'Unknown',
                    'dates': {},
                    'amounts': {},
                    'jurisdiction': '',
                    'confidence': 0.0
                }

            # Prepare Claude prompt for metadata extraction
            extraction_prompt = f"""You are a contract analysis expert. Extract key metadata from this contract document.

DOCUMENT FILENAME: {filename}

DOCUMENT TEXT (first 3000 chars):
{doc_text[:3000]}

Extract and return ONLY a valid JSON object with these fields:
{{
    "type": "contract type (MSA, NDA, SOW, Purchase Order, Service Agreement, Employment Agreement, Lease, etc.)",
    "parties": ["Company A", "Company B", ...],
    "perspective": "Buyer|Seller|Vendor|Customer|Landlord|Tenant|Employer|Employee|Service Provider|Client",
    "dates": {{
        "effective_date": "YYYY-MM-DD or null",
        "expiration_date": "YYYY-MM-DD or null",
        "signature_date": "YYYY-MM-DD or null"
    }},
    "amounts": {{
        "total_value": "amount with currency or null",
        "payment_terms": "brief description or null"
    }},
    "jurisdiction": "governing law jurisdiction or empty string",
    "confidence": 0.85
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

            # Phase 4B: Use unified call_claude_safe()
            payload = {
                'system': '',
                'messages': [{"role": "user", "content": extraction_prompt}],
                'max_tokens': 2000
            }

            result = call_claude_safe(
                payload=payload,
                purpose="analyze",
                model=self.analyzer.model
            )

            if not result.success:
                logger.error(f"Metadata extraction API failed: {result.error_category}")
                return {
                    'type': 'Unknown',
                    'parties': [],
                    'perspective': 'Unknown',
                    'dates': {},
                    'amounts': {},
                    'jurisdiction': '',
                    'confidence': 0.0
                }

            # Parse response
            response_text = result.data.get('response', '').strip()

            # Extract JSON from response (handle cases where Claude adds explanation)
            if '{' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text

            metadata = json.loads(json_text)

            logger.info(f"Metadata extracted successfully: type={metadata.get('type')}, parties={len(metadata.get('parties', []))}")

            return metadata

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            return {
                'type': 'Unknown',
                'parties': [],
                'perspective': 'Unknown',
                'dates': {},
                'amounts': {},
                'jurisdiction': '',
                'confidence': 0.0
            }
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}", exc_info=True)
            return {
                'type': 'Unknown',
                'parties': [],
                'perspective': 'Unknown',
                'dates': {},
                'amounts': {},
                'jurisdiction': '',
                'confidence': 0.0
            }

    def detect_version(self, filename: str, content_hash: str) -> Tuple[Optional[int], int]:
        """
        Detect if uploaded contract is a new version of existing contract

        Args:
            filename: Original filename
            content_hash: MD5 hash of file content

        Returns:
            Tuple of (parent_id or None, suggested_version_number)
        """
        try:
            logger.info(f"Checking for existing versions of: {filename}")

            conn = self._get_db_conn()
            if not conn:
                logger.error("Database connection failed")
                return None, 1

            cursor = conn.cursor()

            # Check for exact content hash match (duplicate)
            cursor.execute("""
                SELECT id, filename FROM contracts
                WHERE content_hash = ?
            """, (content_hash,))

            duplicate = cursor.fetchone()
            if duplicate:
                logger.warning(f"Duplicate content detected: matches contract ID {duplicate[0]}")
                return duplicate[0], 1  # Return existing as parent, but version 1 (duplicate)

            # Check for similar filename (version detection)
            # Extract base filename without version indicators and extension
            import re

            # Remove version patterns: v1, v2, V1, V2, _v1, -v1, (v1), etc.
            base_filename = re.sub(r'[_\-\s\(]?v?\d+[_\-\s\)]?', '', filename, flags=re.IGNORECASE)
            base_filename = re.sub(r'\.[^.]+$', '', base_filename)  # Remove extension
            base_filename = base_filename.strip('_- ')

            # Search for contracts with similar base name
            cursor.execute("""
                SELECT id, filename, version_number, is_latest_version
                FROM contracts
                ORDER BY upload_date DESC
            """)

            contracts = cursor.fetchall()

            from difflib import SequenceMatcher

            best_match = None
            best_similarity = 0.0

            for contract in contracts:
                contract_id = contract[0]
                contract_filename = contract[1]

                # Extract base of existing filename
                contract_base = re.sub(r'[_\-\s\(]?v?\d+[_\-\s\)]?', '', contract_filename, flags=re.IGNORECASE)
                contract_base = re.sub(r'\.[^.]+$', '', contract_base)
                contract_base = contract_base.strip('_- ')

                # Calculate similarity
                similarity = SequenceMatcher(None, base_filename.lower(), contract_base.lower()).ratio()

                if similarity > best_similarity and similarity >= 0.80:  # 80% threshold
                    best_similarity = similarity
                    best_match = contract

            if best_match:
                parent_id = best_match[0]
                current_version = best_match[2] or 1
                suggested_version = current_version + 1

                logger.info(f"Version detected: {filename} appears to be version {suggested_version} of contract ID {parent_id}")
                logger.info(f"Similarity: {best_similarity:.2%}")

                return parent_id, suggested_version

            logger.info(f"No similar contracts found. This is a new contract (version 1)")
            return None, 1

        except Exception as e:
            logger.error(f"Version detection failed: {e}", exc_info=True)
            return None, 1

    def suggest_context(self, file_path: str, metadata: Dict) -> Dict:
        """
        Suggest business context (position, leverage, narrative) using Claude AI

        Args:
            file_path: Path to contract file
            metadata: Extracted metadata dict

        Returns:
            Dict with suggested context: {
                'position': str,
                'leverage': str,
                'narrative': str,
                'confidence': float
            }
        """
        try:
            logger.info("Generating business context suggestions...")

            # Extract document text
            doc_text = self.extractor.extract_text(file_path)

            if not doc_text or len(doc_text) < 100:
                logger.warning("Insufficient content for context analysis")
                return {
                    'position': 'Unknown',
                    'leverage': 'Balanced',
                    'narrative': 'Unable to analyze contract context due to insufficient content.',
                    'confidence': 0.0
                }

            # Prepare context analysis prompt
            context_prompt = f"""You are a business contract advisor. Analyze this contract and suggest the business context.

CONTRACT TYPE: {metadata.get('type', 'Unknown')}
PARTIES: {', '.join(metadata.get('parties', []))}
PERSPECTIVE: {metadata.get('perspective', 'Unknown')}

CONTRACT TEXT (first 4000 chars):
{doc_text[:4000]}

Based on the contract structure, terms, parties, and financial arrangements, determine:

1. POSITION: Which party is this contract analysis for? Consider:
   - Who drafted the contract? (usually has stronger position)
   - Who has payment obligations?
   - Who provides goods/services vs receives them?
   - Is this party the "Vendor", "Customer", "Buyer", "Seller", "Service Provider", "Client", "Landlord", "Tenant", etc.?

2. LEVERAGE: What is the business leverage position?
   - Strong: Favorable terms, strong protections, limited liability, flexible termination
   - Balanced: Fair allocation of risk, mutual obligations, standard market terms
   - Weak: Unfavorable terms, heavy obligations, limited rights, strict penalties

3. NARRATIVE: Brief 2-3 sentence business context summary explaining the relationship, key obligations, and strategic considerations.

Return ONLY a valid JSON object:
{{
    "position": "Vendor|Customer|Buyer|Seller|Service Provider|Client|Landlord|Tenant|etc.",
    "leverage": "Strong|Balanced|Weak",
    "narrative": "2-3 sentence summary of business context and key considerations",
    "confidence": 0.75
}}

IMPORTANT: Return ONLY the JSON object."""

            # Phase 4B: Use unified call_claude_safe()
            payload = {
                'system': '',
                'messages': [{"role": "user", "content": context_prompt}],
                'max_tokens': 1500
            }

            result = call_claude_safe(
                payload=payload,
                purpose="analyze",
                model=self.analyzer.model
            )

            if not result.success:
                logger.error(f"Context suggestion API failed: {result.error_category}")
                return {
                    'position': 'Unknown',
                    'leverage': 'Balanced',
                    'narrative': 'Unable to generate context suggestion due to analysis error.',
                    'confidence': 0.0
                }

            # Parse response
            response_text = result.data.get('response', '').strip()

            # Extract JSON
            if '{' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text

            context = json.loads(json_text)

            # Validate position and leverage values
            valid_positions = ['Vendor', 'Customer', 'Buyer', 'Seller', 'Service Provider', 'Client',
                             'Landlord', 'Tenant', 'Employer', 'Employee', 'Contractor', 'Principal']

            if context.get('position') not in valid_positions:
                # Try to map to closest valid position
                position_lower = context.get('position', '').lower()
                if 'vendor' in position_lower or 'seller' in position_lower or 'provider' in position_lower:
                    context['position'] = 'Vendor'
                elif 'customer' in position_lower or 'buyer' in position_lower or 'client' in position_lower:
                    context['position'] = 'Customer'
                else:
                    context['position'] = 'Unknown'

            valid_leverage = ['Strong', 'Balanced', 'Weak']
            if context.get('leverage') not in valid_leverage:
                context['leverage'] = 'Balanced'

            logger.info(f"Context suggested: position={context.get('position')}, leverage={context.get('leverage')}")

            return context

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse context JSON: {e}")
            return {
                'position': 'Unknown',
                'leverage': 'Balanced',
                'narrative': 'Unable to generate context suggestion due to parsing error.',
                'confidence': 0.0
            }
        except Exception as e:
            logger.error(f"Context suggestion failed: {e}", exc_info=True)
            return {
                'position': 'Unknown',
                'leverage': 'Balanced',
                'narrative': 'Unable to generate context suggestion due to analysis error.',
                'confidence': 0.0
            }

    def close(self):
        """Clean up resources"""
        for thread_id, conn in self._db_connections.items():
            if conn:
                conn.close()
                logger.debug(f"Closed DB connection for thread {thread_id}")
        self._db_connections.clear()
        logger.info("All database connections closed")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_orchestrator(
    db_path: Optional[str] = None,
    knowledge_dir: Optional[str] = None,
    api_key: Optional[str] = None
) -> ContractOrchestrator:
    """Factory function to create configured orchestrator"""
    return ContractOrchestrator(
        db_path=db_path,
        knowledge_dir=knowledge_dir,
        api_key=api_key
    )


def quick_analyze(
    file_path: str,
    position: str,
    leverage: str,
    narrative: str
) -> RiskAssessment:
    """Quick analysis without database persistence"""
    orchestrator = create_orchestrator()
    context = ContractContext(
        position=position,
        leverage=leverage,
        narrative=narrative
    )

    return orchestrator.analyze_contract_file(
        file_path,
        context,
        save_to_db=False
    )


# ============================================================================
# RISK CHANGE DETECTION
# ============================================================================

def detect_risk_change(previous_risk: str | None, new_risk: str) -> bool:
    """
    Detect if the risk level has changed between analyses.

    Args:
        previous_risk: Previous risk level (or None if no prior analysis)
        new_risk: New risk level from current analysis

    Returns:
        True if risk changed, False otherwise
    """
    return previous_risk is not None and previous_risk != new_risk


# ============================================================================
# v2: ANALYSIS SNAPSHOT HELPERS
# ============================================================================

def save_analysis_snapshot(
    db_path: str,
    contract_id: int,
    overall_risk: str,
    categories: list,
    clauses: list
) -> Optional[int]:
    """
    Save an analysis snapshot to the database.

    Args:
        db_path: Path to SQLite database
        contract_id: Contract ID
        overall_risk: Overall risk level (low/medium/high/critical)
        categories: List of category risk summaries
        clauses: List of clause findings

    Returns:
        snapshot_id if successful, None otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO analysis_snapshots (
                contract_id, created_at, overall_risk, categories, clauses
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            contract_id,
            datetime.now().isoformat(),
            overall_risk,
            json.dumps(categories),
            json.dumps(clauses)
        ))

        snapshot_id = cursor.lastrowid

        # Update last_analyzed_at for staleness detection (B12 fix)
        cursor.execute("""
            UPDATE contracts SET last_analyzed_at = ? WHERE id = ?
        """, (datetime.now().isoformat(), contract_id))

        conn.commit()
        conn.close()

        logger.info(f"Saved analysis snapshot {snapshot_id} for contract {contract_id}")
        return snapshot_id

    except Exception as e:
        logger.error(f"Failed to save analysis snapshot: {e}")
        return None


def load_analysis_history(db_path: str, contract_id: int, limit: int = 10) -> List[Dict]:
    """
    Load analysis history for a contract.

    Args:
        db_path: Path to SQLite database
        contract_id: Contract ID
        limit: Maximum number of snapshots to return

    Returns:
        List of analysis snapshot summaries
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT snapshot_id, contract_id, created_at, overall_risk, categories, clauses
            FROM analysis_snapshots
            WHERE contract_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (contract_id, limit))

        rows = cursor.fetchall()
        conn.close()

        snapshots = []
        for row in rows:
            snapshots.append({
                'snapshot_id': row['snapshot_id'],
                'contract_id': row['contract_id'],
                'created_at': row['created_at'],
                'overall_risk': row['overall_risk'],
                'categories': json.loads(row['categories']) if row['categories'] else [],
                'clauses': json.loads(row['clauses']) if row['clauses'] else []
            })

        return snapshots

    except Exception as e:
        logger.error(f"Failed to load analysis history: {e}")
        return []


def load_analysis_snapshot(db_path: str, snapshot_id: int) -> Optional[Dict]:
    """
    Load a specific analysis snapshot.

    Args:
        db_path: Path to SQLite database
        snapshot_id: Snapshot ID

    Returns:
        Analysis snapshot dict or None
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT snapshot_id, contract_id, created_at, overall_risk, categories, clauses
            FROM analysis_snapshots
            WHERE snapshot_id = ?
        """, (snapshot_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'snapshot_id': row['snapshot_id'],
                'contract_id': row['contract_id'],
                'created_at': row['created_at'],
                'overall_risk': row['overall_risk'],
                'categories': json.loads(row['categories']) if row['categories'] else [],
                'clauses': json.loads(row['clauses']) if row['clauses'] else []
            }
        return None

    except Exception as e:
        logger.error(f"Failed to load analysis snapshot: {e}")
        return None


# ============================================================================
# v2: COMPARISON SNAPSHOT HELPERS
# ============================================================================

def save_comparison_snapshot(
    db_path: str,
    v1_contract_id: int,
    v2_contract_id: int,
    v1_snapshot_id: Optional[int],
    v2_snapshot_id: Optional[int],
    similarity_score: float,
    changed_clauses: list,
    risk_delta: list
) -> Optional[int]:
    """
    Save a comparison snapshot to the database.

    Args:
        db_path: Path to SQLite database
        v1_contract_id: V1 contract ID
        v2_contract_id: V2 contract ID
        v1_snapshot_id: V1 analysis snapshot ID (optional)
        v2_snapshot_id: V2 analysis snapshot ID (optional)
        similarity_score: Similarity percentage (0-100)
        changed_clauses: List of changed clause details
        risk_delta: List of risk changes by category

    Returns:
        comparison_id if successful, None otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO comparison_snapshots (
                v1_contract_id, v2_contract_id, v1_snapshot_id, v2_snapshot_id,
                similarity_score, changed_clauses, risk_delta, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v1_contract_id,
            v2_contract_id,
            v1_snapshot_id,
            v2_snapshot_id,
            similarity_score,
            json.dumps(changed_clauses),
            json.dumps(risk_delta),
            datetime.now().isoformat()
        ))

        comparison_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Saved comparison snapshot {comparison_id}: V1={v1_contract_id} vs V2={v2_contract_id}")
        return comparison_id

    except Exception as e:
        logger.error(f"Failed to save comparison snapshot: {e}")
        return None


def load_comparison_snapshot(db_path: str, comparison_id: int) -> Optional[Dict]:
    """
    Load a specific comparison snapshot.

    Args:
        db_path: Path to SQLite database
        comparison_id: Comparison ID

    Returns:
        Comparison snapshot dict or None
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT comparison_id, v1_contract_id, v2_contract_id,
                   v1_snapshot_id, v2_snapshot_id, similarity_score,
                   changed_clauses, risk_delta, created_at
            FROM comparison_snapshots
            WHERE comparison_id = ?
        """, (comparison_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'comparison_id': row['comparison_id'],
                'v1_contract_id': row['v1_contract_id'],
                'v2_contract_id': row['v2_contract_id'],
                'v1_snapshot_id': row['v1_snapshot_id'],
                'v2_snapshot_id': row['v2_snapshot_id'],
                'similarity_score': row['similarity_score'],
                'changed_clauses': json.loads(row['changed_clauses']) if row['changed_clauses'] else [],
                'risk_delta': json.loads(row['risk_delta']) if row['risk_delta'] else [],
                'created_at': row['created_at']
            }
        return None

    except Exception as e:
        logger.error(f"Failed to load comparison snapshot: {e}")
        return None


def load_comparison_history(
    db_path: str,
    contract_id: int,
    limit: int = 10
) -> List[Dict]:
    """
    Load comparison history involving a contract.

    Args:
        db_path: Path to SQLite database
        contract_id: Contract ID (matches either v1 or v2)
        limit: Maximum number of comparisons to return

    Returns:
        List of comparison snapshot summaries
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT comparison_id, v1_contract_id, v2_contract_id,
                   similarity_score, created_at
            FROM comparison_snapshots
            WHERE v1_contract_id = ? OR v2_contract_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (contract_id, contract_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Failed to load comparison history: {e}")
        return []


def align_clauses_simple(v1_clauses: list, v2_clauses: list) -> list:
    """
    Simple clause alignment by number and title similarity.

    Args:
        v1_clauses: List of V1 clause dicts with 'number' and 'title' keys
        v2_clauses: List of V2 clause dicts with 'number' and 'title' keys

    Returns:
        List of aligned pairs: [{'v1': clause, 'v2': clause, 'match_type': str, 'similarity': float}]
    """
    from difflib import SequenceMatcher

    aligned = []
    v2_matched = set()

    for v1 in v1_clauses:
        best_match = None
        best_score = 0.0
        best_idx = -1

        for idx, v2 in enumerate(v2_clauses):
            if idx in v2_matched:
                continue

            # Score based on number match + title similarity
            number_match = 1.0 if v1.get('number') == v2.get('number') else 0.0

            title_similarity = SequenceMatcher(
                None,
                (v1.get('title') or '').lower(),
                (v2.get('title') or '').lower()
            ).ratio()

            # Combined score: 40% number, 60% title
            score = (number_match * 0.4) + (title_similarity * 0.6)

            if score > best_score:
                best_score = score
                best_match = v2
                best_idx = idx

        # Determine match type
        if best_score >= 0.85:
            match_type = "High Match"
        elif best_score >= 0.60:
            match_type = "Likely Match"
        elif best_score >= 0.40:
            match_type = "Best Guess"
        else:
            match_type = "No Match"
            best_match = None

        if best_match and best_idx >= 0:
            v2_matched.add(best_idx)

        aligned.append({
            'v1': v1,
            'v2': best_match,
            'match_type': match_type,
            'similarity': best_score
        })

    # Add unmatched V2 clauses
    for idx, v2 in enumerate(v2_clauses):
        if idx not in v2_matched:
            aligned.append({
                'v1': None,
                'v2': v2,
                'match_type': "Added",
                'similarity': 0.0
            })

    return aligned


# ============================================================================
# REDLINE v4: ENGINE CLIENT AND BATCH PROCESSING
# ============================================================================

REDLINE_BATCH_SIZE = 8
CLAUDE_TIMEOUT_SECONDS = 60

# v4: Dual confidence thresholds
CONFIDENCE_THRESHOLD_STANDARD = 0.85
CONFIDENCE_THRESHOLD_CRITICAL = 0.93

# v4: Critical categories requiring higher confidence
CRITICAL_CATEGORIES = ["liability", "indemnity", "ip", "intellectual_property", "limitation_of_liability"]

# v4: Risk priority order
RISK_PRIORITY_ORDER = ["CRITICAL", "HIGH", "MODERATE", "ADMINISTRATIVE"]

# v4: Dealbreaker patterns
DEALBREAKER_PATTERNS = [
    "unlimited liability",
    "unlimited indemnity",
    "waive all claims",
    "no limitation",
    "sole discretion",
    "unconditional",
    "irrevocable",
    "perpetual license",
    "assigns all rights",
    "work for hire",
]

# v4: Claude 3.5 Sonnet model
REDLINE_MODEL = "claude-3-5-sonnet-20241022"


def check_dealbreakers_before_redline(clauses: list, contract_position: str) -> list:
    """
    v4: Pre-check clauses for dealbreaker patterns before redline batching.
    Returns list of flagged clauses with dealbreaker_flag = True.
    Does NOT block redline generation - returns warnings only.

    Args:
        clauses: List of clause dicts with 'text', 'title', 'risk_category'
        contract_position: 'upstream' | 'downstream' | 'teaming' | 'other'

    Returns:
        List of clause dicts with 'dealbreaker_flag' and 'dealbreaker_reason' added
    """
    flagged_clauses = []

    for clause in clauses:
        text = (clause.get('text', '') + ' ' + clause.get('title', '')).lower()
        dealbreaker_found = False
        dealbreaker_reason = None

        for pattern in DEALBREAKER_PATTERNS:
            if pattern.lower() in text:
                dealbreaker_found = True
                dealbreaker_reason = f"Dealbreaker pattern detected: '{pattern}'"
                break

        # Position-specific dealbreaker checks
        if contract_position == 'downstream' and 'flow down' not in text:
            category = clause.get('risk_category', '').lower()
            if category in ['liability', 'indemnity']:
                # Potential flowdown gap
                if not dealbreaker_found:
                    dealbreaker_reason = "Potential flowdown gap: liability/indemnity clause without flowdown"

        clause_copy = clause.copy()
        clause_copy['dealbreaker_flag'] = dealbreaker_found
        clause_copy['dealbreaker_reason'] = dealbreaker_reason
        flagged_clauses.append(clause_copy)

    return flagged_clauses


def prioritize_clauses_by_risk(clauses: list) -> list:
    """
    v4: Reorder clauses by risk priority: CRITICAL → HIGH → MODERATE → ADMINISTRATIVE.
    Maintains original clause_id for reference.

    Args:
        clauses: List of clause dicts

    Returns:
        List of clauses reordered by risk priority
    """
    def get_priority_rank(clause):
        category = clause.get('risk_category', '').lower()
        severity = clause.get('severity', '').lower()

        # Map to priority level
        if category in CRITICAL_CATEGORIES or severity in ['critical', 'dealbreaker']:
            return (0, "CRITICAL")
        elif severity == 'high' or category in ['termination', 'damages', 'warranty']:
            return (1, "HIGH")
        elif severity == 'medium' or category in ['scope', 'payment', 'schedule']:
            return (2, "MODERATE")
        else:
            return (3, "ADMINISTRATIVE")

    # Add priority info to each clause
    prioritized = []
    for clause in clauses:
        clause_copy = clause.copy()
        rank, priority = get_priority_rank(clause)
        clause_copy['_priority_rank'] = rank
        clause_copy['risk_priority'] = priority
        prioritized.append(clause_copy)

    # Sort by priority rank (CRITICAL first)
    prioritized.sort(key=lambda c: c['_priority_rank'])

    return prioritized


def compute_flowdown_impact(clause: dict, contract_position: str, upstream_terms: list = None) -> str:
    """
    v4: Compute flowdown impact for a clause based on contract position.

    Args:
        clause: Clause dict
        contract_position: 'upstream' | 'downstream' | 'teaming' | 'other'
        upstream_terms: Optional list of upstream contract terms for comparison

    Returns:
        Flowdown impact description or None
    """
    category = clause.get('risk_category', '').lower()
    text = clause.get('text', '').lower()

    if contract_position == 'downstream':
        # Check if downstream obligations align with potential upstream
        if category in ['liability', 'indemnity', 'ip']:
            if 'flow down' in text or 'flowdown' in text:
                return "Flowdown clause present - verify alignment with upstream"
            else:
                return "WARNING: No flowdown language - potential gap with upstream obligations"
    elif contract_position == 'upstream':
        if category in ['liability', 'indemnity', 'ip']:
            return "Upstream position - ensure downstream contracts include appropriate flowdown"
    elif contract_position == 'teaming':
        if category in ['liability', 'indemnity', 'ip', 'scope']:
            return "Teaming arrangement - verify mutual obligations and risk sharing"

    return None


def annotate_epc_fields_on_redline(clause: dict, contract_context: dict = None) -> dict:
    """
    v4: Annotate EPC-specific fields on a redline clause.

    Args:
        clause: RedlineClause-like dict
        contract_context: Optional context with position, leverage, etc.

    Returns:
        Dict with success_probability and leverage_context added
    """
    category = clause.get('risk_category', '').lower()
    confidence = clause.get('confidence', 0.0)

    # Estimate success probability based on category and confidence
    base_probability = confidence * 0.8  # Start with confidence as base

    # Adjust based on category
    if category in CRITICAL_CATEGORIES:
        base_probability *= 0.7  # Critical items harder to negotiate
    elif category in ['scope', 'schedule']:
        base_probability *= 1.1  # More room for scope/schedule negotiation

    success_probability = min(1.0, max(0.0, base_probability))

    # Determine leverage context (EPC: quality / schedule / margin)
    leverage_context = None
    if category in ['warranty', 'quality', 'acceptance']:
        leverage_context = "quality"
    elif category in ['schedule', 'delivery', 'milestone']:
        leverage_context = "schedule"
    elif category in ['payment', 'price', 'damages', 'liability']:
        leverage_context = "margin"

    clause['success_probability'] = success_probability
    clause['leverage_context'] = leverage_context

    return clause


def get_confidence_threshold(clause: dict) -> float:
    """
    v4: Get appropriate confidence threshold based on clause category.
    CRITICAL categories require 0.93, STANDARD categories require 0.85.
    """
    category = clause.get('risk_category', '').lower()
    if category in CRITICAL_CATEGORIES:
        return CONFIDENCE_THRESHOLD_CRITICAL
    return CONFIDENCE_THRESHOLD_STANDARD


def build_redline_batches(clauses: list, batch_size: int = REDLINE_BATCH_SIZE) -> list:
    """
    Build batches of clauses for processing.
    v4: Clauses should already be priority-ordered via prioritize_clauses_by_risk().
    Returns list of batches as contiguous slices.
    """
    batches = []
    for i in range(0, len(clauses), batch_size):
        batches.append(clauses[i:i + batch_size])
    return batches


def call_claude_redline_api(batch: list, contract_context: Optional[Dict] = None) -> list:
    """
    v4.1 Phase 4B: Sends one batch of clauses to Claude 3.5 Sonnet Redline Engine.
    Uses unified call_claude_safe() for error handling and retry logic.

    Request JSON contains:
      - contract_context (optional): position, leverage, etc.
      - clauses: list of {clause_id, section_number, title, risk_category, text, risk_priority}
    Response JSON contains list of:
      - clause_id
      - suggested_text
      - rationale (EPC-focused: quality/schedule/margin impact)
      - confidence (0-1 float)
      - pattern_ref (optional)
      - epc_impact (quality/schedule/margin)

    Returns list of redline results, or raises exception on unrecoverable errors.
    """
    # v4: Build context string
    position = contract_context.get('position', 'other') if contract_context else 'other'
    leverage = contract_context.get('leverage', 'neutral') if contract_context else 'neutral'

    # Build the redline prompt with v4 enhancements
    clauses_text = "\n\n".join([
        f"CLAUSE {c.get('clause_id', i)}:\n"
        f"Section: {c.get('section_number', 'N/A')}\n"
        f"Title: {c.get('title', 'Untitled')}\n"
        f"Category: {c.get('risk_category', 'general')}\n"
        f"Priority: {c.get('risk_priority', 'MODERATE')}\n"
        f"Dealbreaker: {c.get('dealbreaker_flag', False)}\n"
        f"Text: {c.get('text', '')[:2000]}"
        for i, c in enumerate(batch)
    ])

    # v4: GEM-defined SYSTEM PROMPT for Redline Engine
    system_prompt = f"""You are an expert EPC (Engineering, Procurement, Construction) contract redlining specialist. Your role is to generate precise, risk-reducing contract redlines that protect quality, schedule, and margin.

CONTRACT CONTEXT:
- Position: {position} (upstream = prime contractor, downstream = subcontractor, teaming = partner)
- Leverage: {leverage}

For each clause provided, generate a suggested redline revision that:
1. Reduces commercial and legal risk
2. Maintains business intent and relationship
3. Aligns with EPC industry standards
4. Considers flowdown implications based on contract position

For each clause, return a JSON object with:
- clause_id: the original clause ID (integer)
- suggested_text: the revised clause text with improvements
- rationale: brief explanation (1-2 sentences) focusing on EPC impact (quality, schedule, or margin)
- confidence: your confidence in this suggestion (0.0 to 1.0)
- pattern_ref: reference to any standard clause pattern used (or null)
- epc_impact: primary impact area ("quality" | "schedule" | "margin" | null)

CRITICAL CATEGORIES (Liability, Indemnity, IP) require higher confidence. If uncertain, return lower confidence.

Return ONLY a valid JSON array of these objects, one per input clause, in the same order as provided."""

    # v4: GEM-defined USER PROMPT for Batch Redline Request
    user_prompt = f"""Analyze and suggest redlines for the following {len(batch)} contract clauses.

CONTRACT POSITION: {position}
LEVERAGE CONTEXT: {leverage}

CLAUSES:
{clauses_text}

Return a JSON array with one object per clause containing: clause_id, suggested_text, rationale, confidence, pattern_ref, epc_impact

Focus rationales on EPC business impact:
- Quality impact: affects deliverable standards, acceptance criteria, warranty obligations
- Schedule impact: affects timeline, milestones, delays, liquidated damages
- Margin impact: affects payment terms, liability caps, indemnity exposure, cost risk"""

    # Phase 4B: Use unified call_claude_safe() for all Claude API calls
    payload = {
        'system': system_prompt,
        'messages': [{"role": "user", "content": user_prompt}],
        'max_tokens': 4096
    }

    # Extract contract_id from context for logging
    contract_id = contract_context.get('contract_id') if contract_context else None

    result = call_claude_safe(
        payload=payload,
        purpose="redline",
        contract_id=contract_id,
        model=REDLINE_MODEL
    )

    if not result.success:
        # Log and raise error with structured info
        logger.error(
            f"Redline API failed: error_category={result.error_category}, "
            f"error_key={result.error_message_key}, contract_id={contract_id}"
        )
        raise ValueError(f"Redline API error: {result.error_message_key}")

    # Parse JSON from response
    response_text = result.data.get('response', '')
    json_start = response_text.find('[')
    json_end = response_text.rfind(']') + 1

    if json_start >= 0 and json_end > json_start:
        results = json.loads(response_text[json_start:json_end])
        return results
    else:
        raise ValueError("No valid JSON array found in response")


def generate_redlines_for_clauses(clauses: list, contract_context: Optional[Dict] = None) -> list:
    """
    v4: Processes all clauses via Claude 3.5 Sonnet in batches with Phase 4 enhancements.

    Strategy:
      1. Check dealbreakers before processing (non-blocking alerts)
      2. Prioritize clauses by risk: CRITICAL → HIGH → MODERATE → ADMINISTRATIVE
      3. Build batches via build_redline_batches(..., REDLINE_BATCH_SIZE)
      4. For each batch:
          a) Try once at full batch size
          b) On failure, split that batch into halves and retry each half once
      5. Apply dual confidence thresholds:
          - CRITICAL categories (liability, indemnity, IP): 0.93
          - STANDARD categories: 0.85
      6. Annotate EPC fields (success_probability, leverage_context)
      7. Compute flowdown impact based on contract position

    For any clause where:
      - API failed repeatedly, OR
      - returned confidence < threshold for that category
    -> create RedlineClause with:
        suggested_text = ""
        rationale = "Needs CM/Legal Review"
        confidence = 0.0
        status = "needs_cm_legal_review"

    For successful high-confidence clauses:
        status = "suggested"

    Returns ordered list of RedlineClause aligned to input clause_id order,
    sorted by risk priority (CRITICAL first).
    """
    from .models import RedlineClause

    # Extract contract position for flowdown analysis
    contract_position = contract_context.get('position', 'other') if contract_context else 'other'

    # v4 Step 1: Check dealbreakers (non-blocking)
    clauses_with_dealbreakers = check_dealbreakers_before_redline(clauses, contract_position)
    dealbreaker_count = sum(1 for c in clauses_with_dealbreakers if c.get('dealbreaker_flag'))
    if dealbreaker_count > 0:
        logger.warning(f"Dealbreaker patterns detected in {dealbreaker_count} clause(s) - continuing with redline generation")

    # v4 Step 2: Prioritize by risk (CRITICAL → HIGH → MODERATE → ADMINISTRATIVE)
    prioritized_clauses = prioritize_clauses_by_risk(clauses_with_dealbreakers)

    results_map = {}  # clause_id -> RedlineClause

    # v4 Step 3: Build batches (already priority-ordered)
    batches = build_redline_batches(prioritized_clauses, REDLINE_BATCH_SIZE)

    def create_redline_clause(input_clause: dict, result: dict = None, needs_review: bool = False) -> RedlineClause:
        """
        Helper to create RedlineClause with all v4 fields populated.
        """
        clause_id = input_clause.get('clause_id')
        category = input_clause.get('risk_category', 'general')

        # v4: Get appropriate confidence threshold for this category
        threshold = get_confidence_threshold(input_clause)
        confidence = result.get('confidence', 0.0) if result else 0.0

        # Determine if this passes the threshold
        passes_threshold = confidence >= threshold and not needs_review

        if passes_threshold and result:
            # Successful redline
            base_clause = {
                'clause_id': clause_id,
                'section_number': input_clause.get('section_number', 'N/A'),
                'title': input_clause.get('title', 'Untitled'),
                'risk_category': category,
                'current_text': input_clause.get('text', ''),
                'suggested_text': result.get('suggested_text', ''),
                'rationale': result.get('rationale', ''),
                'pattern_ref': result.get('pattern_ref'),
                'confidence': confidence,
                'status': 'suggested',
                'user_notes': None,
                'dealbreaker_flag': input_clause.get('dealbreaker_flag', False),
                'risk_priority': input_clause.get('risk_priority', 'MODERATE'),
            }

            # v4 Step 6: Annotate EPC fields
            base_clause = annotate_epc_fields_on_redline(base_clause, contract_context)

            # v4 Step 7: Compute flowdown impact
            flowdown = compute_flowdown_impact(input_clause, contract_position)
            base_clause['flowdown_impact'] = flowdown

            return RedlineClause(
                clause_id=base_clause['clause_id'],
                section_number=base_clause['section_number'],
                title=base_clause['title'],
                risk_category=base_clause['risk_category'],
                current_text=base_clause['current_text'],
                suggested_text=base_clause['suggested_text'],
                rationale=base_clause['rationale'],
                pattern_ref=base_clause['pattern_ref'],
                confidence=base_clause['confidence'],
                status=base_clause['status'],
                user_notes=base_clause['user_notes'],
                success_probability=base_clause.get('success_probability'),
                leverage_context=base_clause.get('leverage_context'),
                flowdown_impact=base_clause.get('flowdown_impact'),
                dealbreaker_flag=base_clause['dealbreaker_flag'],
                risk_priority=base_clause['risk_priority']
            )
        else:
            # Needs CM/Legal review - either low confidence or API failure
            review_reason = "Needs CM/Legal Review"
            if input_clause.get('dealbreaker_flag'):
                review_reason = f"Dealbreaker detected: {input_clause.get('dealbreaker_reason', 'Review required')}"
            elif result and confidence < threshold:
                review_reason = f"Low confidence ({confidence:.0%}) - threshold {threshold:.0%} for {category}"

            # Compute flowdown impact even for review items
            flowdown = compute_flowdown_impact(input_clause, contract_position)

            return RedlineClause(
                clause_id=clause_id,
                section_number=input_clause.get('section_number', 'N/A'),
                title=input_clause.get('title', 'Untitled'),
                risk_category=category,
                current_text=input_clause.get('text', ''),
                suggested_text="",
                rationale=review_reason,
                pattern_ref=None,
                confidence=0.0,
                status="needs_cm_legal_review",
                user_notes=None,
                success_probability=None,
                leverage_context=None,
                flowdown_impact=flowdown,
                dealbreaker_flag=input_clause.get('dealbreaker_flag', False),
                risk_priority=input_clause.get('risk_priority', 'MODERATE')
            )

    # v4 Step 4: Process batches
    for batch in batches:
        try:
            # Try full batch
            api_results = call_claude_redline_api(batch, contract_context)

            # Process results
            for result in api_results:
                clause_id = result.get('clause_id')

                # Find matching input clause
                input_clause = next((c for c in batch if c.get('clause_id') == clause_id), None)
                if not input_clause:
                    continue

                results_map[clause_id] = create_redline_clause(input_clause, result)

        except Exception as e:
            logger.warning(f"Batch failed, attempting split retry: {e}")

            # Split batch and retry
            mid = len(batch) // 2
            sub_batches = [batch[:mid], batch[mid:]] if mid > 0 else [batch]

            for sub_batch in sub_batches:
                if not sub_batch:
                    continue

                try:
                    api_results = call_claude_redline_api(sub_batch, contract_context)

                    for result in api_results:
                        clause_id = result.get('clause_id')

                        input_clause = next((c for c in sub_batch if c.get('clause_id') == clause_id), None)
                        if not input_clause:
                            continue

                        results_map[clause_id] = create_redline_clause(input_clause, result)

                except Exception as sub_e:
                    logger.error(f"Sub-batch also failed: {sub_e}")

                    # Mark all clauses in sub-batch as needs review
                    for clause in sub_batch:
                        clause_id = clause.get('clause_id')
                        results_map[clause_id] = create_redline_clause(clause, needs_review=True)

    # Ensure all input clauses have a result (handle any missed)
    for clause in prioritized_clauses:
        clause_id = clause.get('clause_id')
        if clause_id not in results_map:
            results_map[clause_id] = create_redline_clause(clause, needs_review=True)

    # Return in priority order (CRITICAL first, as prioritized)
    return [results_map[c.get('clause_id')] for c in prioritized_clauses]


# ============================================================================
# REDLINE v3: SNAPSHOT HELPERS
# ============================================================================

def save_redline_snapshot(db_path: str, snapshot) -> int:
    """
    v4: Inserts RedlineSnapshot into redline_snapshots table.
    Serializes clauses to JSON including v4 fields.
    Returns new redline_id.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # v4: Serialize clauses to JSON with all v4 fields
        clauses_json = json.dumps([
            {
                'clause_id': c.clause_id,
                'section_number': c.section_number,
                'title': c.title,
                'risk_category': c.risk_category,
                'current_text': c.current_text,
                'suggested_text': c.suggested_text,
                'rationale': c.rationale,
                'pattern_ref': c.pattern_ref,
                'confidence': c.confidence,
                'status': c.status,
                'user_notes': c.user_notes,
                # v4 fields
                'success_probability': getattr(c, 'success_probability', None),
                'leverage_context': getattr(c, 'leverage_context', None),
                'flowdown_impact': getattr(c, 'flowdown_impact', None),
                'dealbreaker_flag': getattr(c, 'dealbreaker_flag', False),
                'risk_priority': getattr(c, 'risk_priority', None)
            }
            for c in snapshot.clauses
        ])

        # v4: Include status, contract_position, and dealbreakers_detected
        cursor.execute("""
            INSERT INTO redline_snapshots (
                contract_id, base_version_contract_id, source_mode,
                created_at, overall_risk_before, overall_risk_after, clauses_json,
                status, contract_position, dealbreakers_detected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.contract_id,
            snapshot.base_version_contract_id,
            snapshot.source_mode,
            snapshot.created_at,
            snapshot.overall_risk_before,
            snapshot.overall_risk_after,
            clauses_json,
            getattr(snapshot, 'status', 'draft'),
            getattr(snapshot, 'contract_position', None),
            getattr(snapshot, 'dealbreakers_detected', 0)
        ))

        redline_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Saved redline snapshot {redline_id} for contract {snapshot.contract_id}")
        return redline_id

    except Exception as e:
        logger.error(f"Failed to save redline snapshot: {e}")
        raise


def load_redline_snapshot(db_path: str, redline_id: int):
    """
    v4: Loads RedlineSnapshot and deserializes clauses_json into RedlineClause list.
    Includes all v4 fields.
    """
    from .models import RedlineSnapshot, RedlineClause

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT redline_id, contract_id, base_version_contract_id, source_mode,
                   created_at, overall_risk_before, overall_risk_after, clauses_json,
                   status, contract_position, dealbreakers_detected
            FROM redline_snapshots
            WHERE redline_id = ?
        """, (redline_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # v4: Deserialize clauses with v4 fields
        clauses_data = json.loads(row['clauses_json']) if row['clauses_json'] else []
        clauses = [
            RedlineClause(
                clause_id=c['clause_id'],
                section_number=c['section_number'],
                title=c['title'],
                risk_category=c['risk_category'],
                current_text=c['current_text'],
                suggested_text=c['suggested_text'],
                rationale=c['rationale'],
                pattern_ref=c.get('pattern_ref'),
                confidence=c['confidence'],
                status=c['status'],
                user_notes=c.get('user_notes'),
                # v4 fields
                success_probability=c.get('success_probability'),
                leverage_context=c.get('leverage_context'),
                flowdown_impact=c.get('flowdown_impact'),
                dealbreaker_flag=c.get('dealbreaker_flag', False),
                risk_priority=c.get('risk_priority')
            )
            for c in clauses_data
        ]

        return RedlineSnapshot(
            redline_id=row['redline_id'],
            contract_id=row['contract_id'],
            base_version_contract_id=row['base_version_contract_id'],
            source_mode=row['source_mode'],
            created_at=row['created_at'],
            overall_risk_before=row['overall_risk_before'],
            overall_risk_after=row['overall_risk_after'],
            clauses=clauses,
            # v4 fields
            status=row['status'] if 'status' in row.keys() else 'draft',
            contract_position=row['contract_position'] if 'contract_position' in row.keys() else None,
            dealbreakers_detected=row['dealbreakers_detected'] if 'dealbreakers_detected' in row.keys() else 0
        )

    except Exception as e:
        logger.error(f"Failed to load redline snapshot: {e}")
        return None


def load_redline_history(db_path: str, contract_id: int, limit: int = 10) -> list:
    """
    v4: Loads recent redline_snapshots for given contract, most recent first.
    Returns list of RedlineSnapshot objects (with full clause data and v4 fields).
    """
    from .models import RedlineSnapshot, RedlineClause

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT redline_id, contract_id, base_version_contract_id, source_mode,
                   created_at, overall_risk_before, overall_risk_after, clauses_json,
                   status, contract_position, dealbreakers_detected
            FROM redline_snapshots
            WHERE contract_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (contract_id, limit))

        rows = cursor.fetchall()
        conn.close()

        snapshots = []
        for row in rows:
            clauses_data = json.loads(row['clauses_json']) if row['clauses_json'] else []
            clauses = [
                RedlineClause(
                    clause_id=c['clause_id'],
                    section_number=c['section_number'],
                    title=c['title'],
                    risk_category=c['risk_category'],
                    current_text=c['current_text'],
                    suggested_text=c['suggested_text'],
                    rationale=c['rationale'],
                    pattern_ref=c.get('pattern_ref'),
                    confidence=c['confidence'],
                    status=c['status'],
                    user_notes=c.get('user_notes'),
                    # v4 fields
                    success_probability=c.get('success_probability'),
                    leverage_context=c.get('leverage_context'),
                    flowdown_impact=c.get('flowdown_impact'),
                    dealbreaker_flag=c.get('dealbreaker_flag', False),
                    risk_priority=c.get('risk_priority')
                )
                for c in clauses_data
            ]

            snapshots.append(RedlineSnapshot(
                redline_id=row['redline_id'],
                contract_id=row['contract_id'],
                base_version_contract_id=row['base_version_contract_id'],
                source_mode=row['source_mode'],
                created_at=row['created_at'],
                overall_risk_before=row['overall_risk_before'],
                overall_risk_after=row['overall_risk_after'],
                clauses=clauses,
                # v4 fields
                status=row['status'] if 'status' in row.keys() else 'draft',
                contract_position=row['contract_position'] if 'contract_position' in row.keys() else None,
                dealbreakers_detected=row['dealbreakers_detected'] if 'dealbreakers_detected' in row.keys() else 0
            ))

        return snapshots

    except Exception as e:
        logger.error(f"Failed to load redline history: {e}")
        return []


def create_pending_draft_from_redline(db_path: str, base_contract_id: int, redline_id: int) -> int:
    """
    Creates a new contract row based on base_contract_id:
      - status = 'pending_draft'
      - display_id = next unused visible integer (do NOT reuse deleted displayIds)
      - copies core metadata from base version
    Updates contract_relationships.versions for this contract family to append new version.
    Returns new contract_id for pending draft.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get base contract data
        cursor.execute("SELECT * FROM contracts WHERE id = ?", (base_contract_id,))
        base_contract = cursor.fetchone()

        if not base_contract:
            raise ValueError(f"Base contract {base_contract_id} not found")

        # Get next display_id (max + 1, never reuse)
        cursor.execute("SELECT MAX(display_id) FROM contracts")
        max_display_id = cursor.fetchone()[0] or 0
        new_display_id = max_display_id + 1

        # Create new contract with pending_draft status
        cursor.execute("""
            INSERT INTO contracts (
                filename, filepath, title, contract_type, status,
                position, leverage, narrative, display_id,
                upload_date, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"redline_draft_{base_contract['filename']}",
            base_contract['filepath'],
            f"[Draft] {base_contract['title'] or base_contract['filename']}",
            base_contract['contract_type'],
            'pending_draft',
            base_contract['position'],
            base_contract['leverage'],
            base_contract['narrative'],
            new_display_id,
            datetime.now().isoformat(),
            json.dumps({
                'source_redline_id': redline_id,
                'base_version_id': base_contract_id
            })
        ))

        new_contract_id = cursor.lastrowid

        # Update contract_relationships to append new version
        cursor.execute("""
            SELECT versions FROM contract_relationships
            WHERE contract_id = ?
        """, (base_contract_id,))

        rel_row = cursor.fetchone()
        if rel_row:
            versions = json.loads(rel_row['versions']) if rel_row['versions'] else []
            if new_contract_id not in versions:
                versions.append(new_contract_id)
            cursor.execute("""
                UPDATE contract_relationships SET versions = ?
                WHERE contract_id = ?
            """, (json.dumps(versions), base_contract_id))
        else:
            # Create new relationship entry
            cursor.execute("""
                INSERT INTO contract_relationships (contract_id, parent_id, children, versions)
                VALUES (?, ?, '[]', ?)
            """, (base_contract_id, None, json.dumps([new_contract_id])))

        conn.commit()
        conn.close()

        logger.info(f"Created pending draft {new_contract_id} (display_id={new_display_id}) from redline {redline_id}")
        return new_contract_id

    except Exception as e:
        logger.error(f"Failed to create pending draft: {e}")
        raise


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("CIP Contract Orchestrator")
    print("=" * 60)

    # Create orchestrator
    orchestrator = create_orchestrator()

    print(f"Knowledge base documents: {len(orchestrator.knowledge_base.knowledge_base)}")
    print(f"Database: {orchestrator.db_path}")
    print("\nOrchestrator ready for contract analysis")
    print("=" * 60)
