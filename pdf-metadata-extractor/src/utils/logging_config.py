"""
Structured logging configuration for PDF metadata extractor.

Supports:
- JSON structured logging
- File rotation
- Console and file output
- Performance tracking
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def __init__(self, include_fields: Optional[list] = None):
        super().__init__()
        self.include_fields = include_fields or [
            'timestamp', 'level', 'logger_name', 'message',
            'filename', 'function_name', 'line_number'
        ]

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {}

        if 'timestamp' in self.include_fields:
            log_data['timestamp'] = datetime.fromtimestamp(record.created).isoformat()

        if 'level' in self.include_fields:
            log_data['level'] = record.levelname

        if 'logger_name' in self.include_fields:
            log_data['logger_name'] = record.name

        if 'message' in self.include_fields:
            log_data['message'] = record.getMessage()

        if 'filename' in self.include_fields:
            log_data['filename'] = record.filename

        if 'function_name' in self.include_fields:
            log_data['function_name'] = record.funcName

        if 'line_number' in self.include_fields:
            log_data['line_number'] = record.lineno

        if 'process_id' in self.include_fields:
            log_data['process_id'] = record.process

        if 'thread_id' in self.include_fields:
            log_data['thread_id'] = record.thread

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add custom fields
        if hasattr(record, 'custom_fields'):
            log_data.update(record.custom_fields)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter"""

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging(
    log_level: str = 'INFO',
    log_format: str = 'json',
    log_dir: str = 'logs',
    config_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ('json' or 'text')
        log_dir: Directory for log files
        config_file: Optional YAML config file path

    Returns:
        Configured root logger
    """
    # Load config from YAML if provided
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        log_level = config['logging']['level']
        log_format = config['logging']['format']
        log_dir = config['logging']['output']['file']['path'].split('/')[0]

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if log_format == 'json':
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(TextFormatter())

    root_logger.addHandler(console_handler)

    # File handler with rotation
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path / f'pdf_extractor_{timestamp}.log'

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # File gets all logs

    if log_format == 'json':
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(TextFormatter())

    root_logger.addHandler(file_handler)

    # Log initialization
    root_logger.info(f"Logging initialized: level={log_level}, format={log_format}, file={log_file}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def log_performance(logger: logging.Logger, operation: str, duration: float, threshold: float = 5.0):
    """
    Log performance metrics for slow operations.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        threshold: Threshold for slow operations (default: 5.0s)
    """
    if duration > threshold:
        logger.warning(
            f"Slow operation detected: {operation} took {duration:.2f}s",
            extra={'custom_fields': {
                'operation': operation,
                'duration_seconds': duration,
                'threshold_seconds': threshold,
                'performance_issue': True
            }}
        )
    else:
        logger.debug(
            f"Operation completed: {operation} in {duration:.2f}s",
            extra={'custom_fields': {
                'operation': operation,
                'duration_seconds': duration
            }}
        )
