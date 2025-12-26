"""
CIP Configuration
Application configuration and settings with environment variable support
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (in CIP root, parent of backend)
# Use override=True to ensure .env values take precedence over system environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)


# ============================================================================
# BASE PATHS
# ============================================================================

# CIP Root Directory
CIP_ROOT = Path(r"C:\Users\jrudy\CIP")

# Core directories
KNOWLEDGE_PATH = CIP_ROOT / "knowledge"
DATA_PATH = CIP_ROOT / "data"
TOOLS_PATH = CIP_ROOT / "tools"
BACKEND_PATH = CIP_ROOT / "backend"
FRONTEND_PATH = CIP_ROOT / "frontend"
AGENTS_PATH = CIP_ROOT / "agents"
TESTS_PATH = CIP_ROOT / "tests"
DOCS_PATH = CIP_ROOT / "docs"


# ============================================================================
# DATABASE PATHS
# ============================================================================

CONTRACTS_DB = DATA_PATH / "contracts.db"
REPORTS_DB = DATA_PATH / "reports.db"


# ============================================================================
# TOOL PATHS
# ============================================================================

COMPARISON_TOOL_PATH = TOOLS_PATH / "comparison"
LAW_LIBRARY_PATH = TOOLS_PATH / "law_library"
RISK_ENGINE_PATH = TOOLS_PATH / "risk_engine"
REDLINE_GEN_PATH = TOOLS_PATH / "redline_gen"
NEGOTIATION_PATH = TOOLS_PATH / "negotiation"
CLAUSE_RAG_PATH = TOOLS_PATH / "clause_rag"


# ============================================================================
# VECTOR STORE PATHS
# ============================================================================

VECTOR_STORES_PATH = DATA_PATH / "vector_stores"
CONTRACTS_VECTOR_STORE = VECTOR_STORES_PATH / "contracts"
CLAUSES_VECTOR_STORE = VECTOR_STORES_PATH / "clauses"
PATTERNS_VECTOR_STORE = VECTOR_STORES_PATH / "patterns"


# ============================================================================
# API CONFIGURATION
# ============================================================================

# Anthropic API Key (from environment)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Alternative: Load from different environment variable names
if not ANTHROPIC_API_KEY:
    ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY")

# Claude Model Configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"  # Latest Sonnet 4
FALLBACK_MODEL = "claude-3-5-sonnet-20241022"  # Stable fallback

# Model parameters
MAX_TOKENS = 4096
TEMPERATURE = 0.7
TOP_P = 1.0

# Extended analysis settings
MAX_TOKENS_EXTENDED = 8192  # For detailed analysis
MAX_TOKENS_QUICK = 2048     # For quick assessments


# ============================================================================
# CONFIDENCE THRESHOLDS (from CONTRACT_REVIEW_SYSTEM v1.2)
# ============================================================================

# Confidence levels for risk assessment
DEALBREAKER_CONFIDENCE = 1.00   # Any uncertainty → Ask user immediately
CRITICAL_CONFIDENCE = 0.98      # Payment, liability, IP, indemnification
HIGH_CONFIDENCE = 0.95          # Warranties, termination, assignment
IMPORTANT_CONFIDENCE = 0.90     # Important business terms
STANDARD_CONFIDENCE = 0.85      # Boilerplate, notices, governing law
MINIMUM_CONFIDENCE = 0.70       # Below this → Flag for review


# ============================================================================
# RISK CLASSIFICATION
# ============================================================================

# Risk levels
RISK_LEVELS = {
    "DEALBREAKER": 4,
    "CRITICAL": 3,
    "HIGH": 2,
    "MEDIUM": 1,
    "LOW": 0
}

# Risk categories
RISK_CATEGORIES = [
    "payment",
    "liability",
    "indemnification",
    "intellectual_property",
    "ip",
    "termination",
    "warranties",
    "assignment",
    "confidentiality",
    "compliance",
    "regulatory",
    "insurance",
    "dispute_resolution",
    "governing_law",
    "notices",
    "general"
]

# Critical categories requiring high confidence
CRITICAL_CATEGORIES = [
    "payment",
    "liability",
    "indemnification",
    "intellectual_property",
    "ip"
]


# ============================================================================
# ANALYSIS CONFIGURATION
# ============================================================================

# Contract analysis settings
ENABLE_PATTERN_MATCHING = True
ENABLE_CLAUSE_EXTRACTION = True
ENABLE_RISK_SCORING = True
ENABLE_RECOMMENDATIONS = True

# Clause extraction settings
MIN_CLAUSE_LENGTH = 20          # Minimum characters for a clause
MAX_CLAUSE_LENGTH = 5000        # Maximum characters for a clause
SECTION_DETECTION_THRESHOLD = 0.85  # Confidence for section detection


# ============================================================================
# COMPARISON SETTINGS
# ============================================================================

# Version comparison thresholds
SIMILARITY_THRESHOLD = 0.85     # Sections below this are considered changed
SUBSTANTIVE_CHANGE_THRESHOLD = 0.70  # Below this is substantive change
ADMINISTRATIVE_CHANGE_THRESHOLD = 0.95  # Above this is administrative

# Change classification
CHANGE_TYPES = [
    "addition",
    "deletion",
    "modification",
    "none"
]


# ============================================================================
# NEGOTIATION SETTINGS
# ============================================================================

# Success probability thresholds
HIGH_SUCCESS_PROBABILITY = 0.75
MEDIUM_SUCCESS_PROBABILITY = 0.50
LOW_SUCCESS_PROBABILITY = 0.25

# Negotiation positions
POSITIONS = [
    "vendor",
    "customer",
    "landlord",
    "tenant",
    "employer",
    "employee",
    "buyer",
    "seller",
    "other"
]

# Leverage levels
LEVERAGE_LEVELS = [
    "strong",
    "moderate",
    "balanced",
    "weak",
    "unknown"
]


# ============================================================================
# WORKFLOW SETTINGS
# ============================================================================

# Available workflows
WORKFLOWS = {
    "analyze": "Complete contract analysis with risk assessment",
    "compare": "Version comparison and change detection",
    "negotiate": "Negotiation strategy and redline generation",
    "risk_report": "Comprehensive risk reporting",
    "quick_scan": "Quick risk scan without detailed analysis"
}

# Workflow timeouts (seconds)
ANALYSIS_TIMEOUT = 300
COMPARISON_TIMEOUT = 180
NEGOTIATION_TIMEOUT = 240
REPORT_TIMEOUT = 120


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = CIP_ROOT / "logs" / "cip.log"

# Create logs directory if it doesn't exist
LOG_DIR = CIP_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


# ============================================================================
# FRONTEND SETTINGS
# ============================================================================

# Streamlit configuration
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "127.0.0.1"

# API configuration
API_HOST = os.getenv("CIP_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("CIP_API_PORT", "5000"))
DEBUG_MODE = os.getenv("CIP_DEBUG", "True").lower() == "true"


# ============================================================================
# FILE UPLOAD SETTINGS
# ============================================================================

# Supported file formats
SUPPORTED_FORMATS = [".pdf", ".docx", ".txt", ".doc"]

# Upload limits
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# File storage
UPLOAD_DIRECTORY = DATA_PATH / "uploads"
UPLOAD_DIRECTORY.mkdir(exist_ok=True)


# ============================================================================
# REPORT GENERATION SETTINGS
# ============================================================================

# Report formats
REPORT_FORMATS = ["PDF", "DOCX", "HTML", "Markdown", "JSON"]

# Report output directory
REPORTS_OUTPUT_PATH = DATA_PATH / "reports"
REPORTS_OUTPUT_PATH.mkdir(exist_ok=True)

# Report templates
REPORT_TEMPLATES_PATH = CIP_ROOT / "templates" / "reports"


# ============================================================================
# CACHE SETTINGS
# ============================================================================

# Enable caching
ENABLE_CACHE = True
CACHE_TTL = 3600  # Time to live in seconds (1 hour)
CACHE_DIR = DATA_PATH / "cache"
CACHE_DIR.mkdir(exist_ok=True)


# ============================================================================
# VECTOR STORE SETTINGS (for RAG)
# ============================================================================

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Vector store settings
VECTOR_STORE_TYPE = "chromadb"  # chromadb, faiss, or pinecone
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300
TOP_K_RETRIEVAL = 5

# ChromaDB settings
CHROMA_PERSIST_DIRECTORY = VECTOR_STORES_PATH / "chroma"
CHROMA_COLLECTION_NAME = "cip_contracts"


# ============================================================================
# KNOWLEDGE BASE SETTINGS
# ============================================================================

# Knowledge base files (in priority order)
KB_FILES = {
    "contract_review_system": "01_CONTRACT_REVIEW_SYSTEM*.md",
    "clause_patterns": "02_CLAUSE_PATTERN_LIBRARY*.md",
    "quick_reference": "03_QUICK_REFERENCE*.md"
}

# Auto-reload knowledge base on file changes
AUTO_RELOAD_KB = True
KB_RELOAD_INTERVAL = 300  # Seconds


# ============================================================================
# PROMPT COMPOSER SETTINGS
# ============================================================================

# Pattern deck path (CCE memory repository) - v3.0 with v1.3 confirmations
PATTERN_DECK_PATH = Path(r"C:\Users\jrudy\CCE\memory\patterns\deck_v3_phase3.json")

# Pattern selection limits
MAX_PATTERNS_PER_PROMPT = 15
PATTERN_TOKEN_CEILING = 1500
PATTERN_COMPACT_AVG_TOKENS = 70

# Contract stages (v1.3)
CONTRACT_STAGES = ['MNDA', 'NDA', 'COMMERCIAL', 'EXECUTED']

# Pattern statuses (v1.3)
PATTERN_STATUSES = ['CONFIRMED', 'RESEARCH_NEEDED', 'DEALBREAKER', 'LEGAL_REVIEW']

# Escalation types (v1.3)
ESCALATION_TYPES = ['CEO', 'LEGAL', 'INSURANCE']

# Contract type to deck category mapping (ARCHITECTURE.md authoritative)
CONTRACT_CATEGORY_MAP = {
    "MSA": "A",
    "MASTER SERVICE AGREEMENT": "A",
    "SOW": "D",
    "STATEMENT OF WORK": "D",
    "SOW_PHASED": "E",
    "NDA": "C",
    "NON-DISCLOSURE": "C",
    "CONFIDENTIALITY": "C",
    "MOU": "B",
    "MEMORANDUM OF UNDERSTANDING": "B",
    "LOI": "B",
    "LETTER OF INTENT": "B",
    "CHANNEL": "F",
    "CHANNEL PARTNER": "F",
    "RESELLER": "F",
    "DISTRIBUTION": "F",
    "BROKER": "G",
    "FACILITATOR": "G",
    "PROJECT": "E",
    "DESIGN-BUILD": "E"
}

# Prompt composer configuration dict (for passing to PromptComposer)
def get_prompt_composer_config() -> dict:
    """Get configuration dict for PromptComposer initialization."""
    return {
        'PATTERN_DECK_PATH': str(PATTERN_DECK_PATH),
        'MAX_PATTERNS_PER_PROMPT': MAX_PATTERNS_PER_PROMPT,
        'PATTERN_TOKEN_CEILING': PATTERN_TOKEN_CEILING,
        'PATTERN_COMPACT_AVG_TOKENS': PATTERN_COMPACT_AVG_TOKENS,
        'CONTRACT_CATEGORY_MAP': CONTRACT_CATEGORY_MAP,
        'CONTRACT_STAGES': CONTRACT_STAGES,
        'PATTERN_STATUSES': PATTERN_STATUSES,
        'ESCALATION_TYPES': ESCALATION_TYPES,
        'DB_PATH': str(CONTRACTS_DB)
    }


# ============================================================================
# SECURITY SETTINGS
# ============================================================================

# Data encryption
ENABLE_ENCRYPTION = False  # Set to True in production
ENCRYPTION_KEY = os.getenv("CIP_ENCRYPTION_KEY")

# Session management
SESSION_TIMEOUT = 3600  # 1 hour
MAX_SESSIONS = 100

# API rate limiting
ENABLE_RATE_LIMITING = True
RATE_LIMIT_PER_MINUTE = 60


# ============================================================================
# DEVELOPMENT / DEBUG SETTINGS
# ============================================================================

# Development mode
DEV_MODE = os.getenv("DEV_MODE", "True").lower() == "true"

# Debug flags
DEBUG_KNOWLEDGE_BASE = False
DEBUG_DATABASE = False
DEBUG_CLAUDE_API = False
DEBUG_WORKFLOWS = False

# Mock mode (for testing without API)
MOCK_CLAUDE_API = os.getenv("MOCK_CLAUDE_API", "False").lower() == "true"


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_config() -> bool:
    """Validate configuration settings"""
    errors = []

    # Check API key
    if not ANTHROPIC_API_KEY and not MOCK_CLAUDE_API:
        errors.append("ANTHROPIC_API_KEY not set in environment")

    # Check required directories
    required_dirs = [
        CIP_ROOT,
        KNOWLEDGE_PATH,
        DATA_PATH,
        TOOLS_PATH
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            errors.append(f"Required directory not found: {dir_path}")

    # Check database files
    if not CONTRACTS_DB.exists():
        errors.append(f"Contracts database not found: {CONTRACTS_DB}")

    if not REPORTS_DB.exists():
        errors.append(f"Reports database not found: {REPORTS_DB}")

    # Print errors
    if errors:
        print("Configuration Validation Errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def get_config_summary() -> dict:
    """Get configuration summary"""
    return {
        "cip_root": str(CIP_ROOT),
        "knowledge_path": str(KNOWLEDGE_PATH),
        "data_path": str(DATA_PATH),
        "contracts_db": str(CONTRACTS_DB),
        "reports_db": str(REPORTS_DB),
        "model": DEFAULT_MODEL,
        "api_key_set": bool(ANTHROPIC_API_KEY),
        "dev_mode": DEV_MODE,
        "mock_mode": MOCK_CLAUDE_API
    }


def print_config():
    """Print configuration for debugging"""
    print("=" * 60)
    print("CIP CONFIGURATION")
    print("=" * 60)

    summary = get_config_summary()
    for key, value in summary.items():
        print(f"{key:20} : {value}")

    print("=" * 60)
    print(f"Confidence Thresholds:")
    print(f"  DEALBREAKER : {DEALBREAKER_CONFIDENCE}")
    print(f"  CRITICAL    : {CRITICAL_CONFIDENCE}")
    print(f"  HIGH        : {HIGH_CONFIDENCE}")
    print(f"  IMPORTANT   : {IMPORTANT_CONFIDENCE}")
    print(f"  STANDARD    : {STANDARD_CONFIDENCE}")
    print("=" * 60)


# ============================================================================
# INITIALIZATION
# ============================================================================

# Create required directories on import
for directory in [DATA_PATH, UPLOAD_DIRECTORY, REPORTS_OUTPUT_PATH,
                  VECTOR_STORES_PATH, LOG_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True, parents=True)


# ============================================================================
# EXPORT ALL SETTINGS
# ============================================================================

__all__ = [
    # Paths
    "CIP_ROOT",
    "KNOWLEDGE_PATH",
    "DATA_PATH",
    "TOOLS_PATH",
    "CONTRACTS_DB",
    "REPORTS_DB",

    # API Settings
    "ANTHROPIC_API_KEY",
    "DEFAULT_MODEL",
    "MAX_TOKENS",
    "TEMPERATURE",

    # Confidence Thresholds
    "DEALBREAKER_CONFIDENCE",
    "CRITICAL_CONFIDENCE",
    "HIGH_CONFIDENCE",
    "IMPORTANT_CONFIDENCE",
    "STANDARD_CONFIDENCE",

    # Risk Settings
    "RISK_LEVELS",
    "RISK_CATEGORIES",

    # Prompt Composer Settings
    "PATTERN_DECK_PATH",
    "MAX_PATTERNS_PER_PROMPT",
    "PATTERN_TOKEN_CEILING",
    "CONTRACT_CATEGORY_MAP",
    "get_prompt_composer_config",

    # Functions
    "validate_config",
    "get_config_summary",
    "print_config"
]


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    print_config()
    print("\nValidating configuration...")

    is_valid = validate_config()

    if is_valid:
        print("\n[OK] Configuration is valid")
    else:
        print("\n[FAIL] Configuration has errors")
