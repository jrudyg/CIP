"""
CIP Monitoring Configuration

Centralized configuration for monitoring tools.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# =============================================================================
# PATHS
# =============================================================================

CIP_ROOT = Path(r"C:\Users\jrudy\CIP")
BACKEND_PATH = CIP_ROOT / "backend"
FRONTEND_PATH = CIP_ROOT / "frontend"
LOGS_PATH = CIP_ROOT / "logs"
DATA_PATH = CIP_ROOT / "data"

# Log files
LOG_FILES = {
    "cip": LOGS_PATH / "cip.log",
    "error": LOGS_PATH / "error.log",
    "api": LOGS_PATH / "api.log",
}

# Databases
CONTRACTS_DB = DATA_PATH / "contracts.db"
REPORTS_DB = DATA_PATH / "reports.db"

# =============================================================================
# API CONFIGURATION
# =============================================================================

API_HOST = "127.0.0.1"
API_PORT = 5000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 8501
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"

# =============================================================================
# PROCESS CONFIGURATION
# =============================================================================

@dataclass
class ProcessConfig:
    """Configuration for a managed process."""
    name: str
    command: List[str]
    cwd: Path
    port: int
    health_endpoint: Optional[str] = None
    restart_on_crash: bool = True
    max_restart_attempts: int = 3
    restart_delay_seconds: int = 5


BACKEND_CONFIG = ProcessConfig(
    name="backend",
    command=["python", "api.py"],
    cwd=BACKEND_PATH,
    port=API_PORT,
    health_endpoint=HEALTH_ENDPOINT,
    restart_on_crash=True,
    max_restart_attempts=3,
    restart_delay_seconds=5,
)

FRONTEND_CONFIG = ProcessConfig(
    name="frontend",
    command=["streamlit", "run", "app.py", "--server.port", str(FRONTEND_PORT)],
    cwd=FRONTEND_PATH,
    port=FRONTEND_PORT,
    health_endpoint=None,
    restart_on_crash=True,
    max_restart_attempts=3,
    restart_delay_seconds=5,
)

PROCESS_CONFIGS = {
    "backend": BACKEND_CONFIG,
    "frontend": FRONTEND_CONFIG,
}

# =============================================================================
# LOG PARSING CONFIGURATION
# =============================================================================

# Log format: '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
LOG_PATTERN = (
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?) - '  # timestamp
    r'(\S+) - '                                               # logger name
    r'(DEBUG|INFO|WARNING|ERROR|CRITICAL) - '                 # level
    r'(?:\[(\S+):(\d+)\] - )?'                                # optional file:line
    r'(.+)'                                                   # message
)

# =============================================================================
# TERMINAL UI CONFIGURATION
# =============================================================================

# ANSI color codes
COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "DIM": "\033[2m",

    # Log levels
    "DEBUG": "\033[90m",      # Gray
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[1;31m", # Bold Red

    # Status
    "OK": "\033[32m",         # Green
    "WARN": "\033[33m",       # Yellow
    "FAIL": "\033[31m",       # Red

    # UI elements
    "HEADER": "\033[1;36m",   # Bold Cyan
    "LABEL": "\033[36m",      # Cyan
    "VALUE": "\033[37m",      # White
}

# =============================================================================
# MONITORING DEFAULTS
# =============================================================================

DEFAULT_LOG_LINES = 50
DEFAULT_REFRESH_INTERVAL = 5  # seconds
DEFAULT_LOG_LEVEL = "INFO"
MAX_LOG_LINES = 1000

# Health check
HEALTH_CHECK_TIMEOUT = 5  # seconds
HEALTH_CHECK_INTERVAL = 5  # seconds

# Process manager
GRACEFUL_SHUTDOWN_TIMEOUT = 10  # seconds
