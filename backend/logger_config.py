"""
CIP Logging Configuration
Comprehensive logging setup with rotation and multiple handlers
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log files
APP_LOG = LOG_DIR / "cip.log"
ERROR_LOG = LOG_DIR / "error.log"
API_LOG = LOG_DIR / "api.log"

# Log format
DETAILED_FORMAT = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SIMPLE_FORMAT = logging.Formatter(
    fmt='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_logging(name: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    Setup logging with file rotation and multiple handlers

    Args:
        name: Logger name (use __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or 'cip')
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SIMPLE_FORMAT)
    logger.addHandler(console_handler)

    # Main application log (rotating, 10MB max, keep 5 backups)
    app_handler = logging.handlers.RotatingFileHandler(
        APP_LOG,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(app_handler)

    # Error log (ERROR and above only)
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(error_handler)

    return logger

def setup_api_logging() -> logging.Logger:
    """
    Setup dedicated API request/response logging

    Returns:
        API logger instance
    """
    api_logger = logging.getLogger('cip.api')
    api_logger.setLevel(logging.DEBUG)
    api_logger.handlers.clear()

    # API log (rotating, 10MB max, keep 10 backups)
    api_handler = logging.handlers.RotatingFileHandler(
        API_LOG,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    api_handler.setLevel(logging.DEBUG)
    api_handler.setFormatter(DETAILED_FORMAT)
    api_logger.addHandler(api_handler)

    return api_logger

def log_api_request(logger: logging.Logger, method: str, endpoint: str,
                   ip: Optional[str] = None, user_agent: Optional[str] = None):
    """Log incoming API request"""
    logger.info(f"API Request: {method} {endpoint} from {ip or 'unknown'}")
    if user_agent:
        logger.debug(f"User-Agent: {user_agent}")

def log_api_response(logger: logging.Logger, endpoint: str, status: int,
                    duration_ms: Optional[float] = None):
    """Log API response"""
    duration_str = f" ({duration_ms:.2f}ms)" if duration_ms else ""
    logger.info(f"API Response: {endpoint} - Status {status}{duration_str}")

def log_user_action(logger: logging.Logger, action: str, contract_id: Optional[int] = None,
                   details: Optional[dict] = None):
    """Log user actions"""
    msg = f"User Action: {action}"
    if contract_id:
        msg += f" (Contract ID: {contract_id})"
    if details:
        msg += f" - {details}"
    logger.info(msg)

def log_error_with_context(logger: logging.Logger, error: Exception,
                          context: Optional[dict] = None):
    """Log error with full stack trace and context"""
    logger.error(f"Error: {type(error).__name__}: {str(error)}")
    if context:
        logger.error(f"Context: {context}")
    logger.exception("Full traceback:")

# Create default logger on module import
default_logger = setup_logging('cip', 'INFO')
api_logger = setup_api_logging()

__all__ = [
    'setup_logging',
    'setup_api_logging',
    'log_api_request',
    'log_api_response',
    'log_user_action',
    'log_error_with_context',
    'default_logger',
    'api_logger'
]
