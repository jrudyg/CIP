"""
File validation utilities for PDF processing.

Handles file size limits to prevent memory crashes and infinite hangs.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates PDF files before processing"""

    def __init__(
        self,
        warn_size_mb: int = 50,
        max_size_mb: int = 200,
        skip_on_exceed: bool = True
    ):
        """
        Initialize file validator.

        Args:
            warn_size_mb: Warn if file exceeds this size (default: 50MB)
            max_size_mb: Skip files larger than this (default: 200MB)
            skip_on_exceed: Skip large files vs. error (default: True)
        """
        self.warn_size_mb = warn_size_mb
        self.max_size_mb = max_size_mb
        self.skip_on_exceed = skip_on_exceed

        self.warn_size_bytes = warn_size_mb * 1024 * 1024
        self.max_size_bytes = max_size_mb * 1024 * 1024

        self.files_checked = 0
        self.files_warned = 0
        self.files_skipped = 0
        self.total_size_bytes = 0

    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate file for processing.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (should_process, message)
            - should_process: True if file should be processed
            - message: Optional warning/error message
        """
        self.files_checked += 1

        try:
            # Check file exists
            if not file_path.exists():
                return False, f"File not found: {file_path.name}"

            # Check file is readable
            if not file_path.is_file():
                return False, f"Not a file: {file_path.name}"

            # Check file size
            file_size = file_path.stat().st_size
            self.total_size_bytes += file_size
            file_size_mb = file_size / (1024 * 1024)

            # Check if exceeds maximum
            if file_size > self.max_size_bytes:
                self.files_skipped += 1
                message = (f"⚠️  File exceeds maximum size: {file_path.name} "
                          f"({file_size_mb:.1f}MB > {self.max_size_mb}MB)")

                if self.skip_on_exceed:
                    logger.warning(message + " - SKIPPING")
                    return False, message
                else:
                    logger.error(message)
                    return False, message

            # Warn if exceeds warning threshold
            if file_size > self.warn_size_bytes:
                self.files_warned += 1
                message = (f"⚠️  Large file detected: {file_path.name} "
                          f"({file_size_mb:.1f}MB > {self.warn_size_mb}MB) "
                          f"- processing may be slow")
                logger.warning(message)
                return True, message

            # File is valid
            return True, None

        except Exception as e:
            logger.error(f"Error validating file {file_path.name}: {e}")
            return False, str(e)

    def get_statistics(self) -> dict:
        """Get validation statistics"""
        return {
            'files_checked': self.files_checked,
            'files_warned': self.files_warned,
            'files_skipped': self.files_skipped,
            'total_size_mb': self.total_size_bytes / (1024 * 1024),
            'avg_size_mb': (self.total_size_bytes / (1024 * 1024) / self.files_checked
                           if self.files_checked > 0 else 0)
        }

    def log_statistics(self):
        """Log validation statistics"""
        stats = self.get_statistics()
        logger.info(f"File validation statistics:")
        logger.info(f"  Files checked: {stats['files_checked']}")
        logger.info(f"  Files warned: {stats['files_warned']}")
        logger.info(f"  Files skipped: {stats['files_skipped']}")
        logger.info(f"  Total size: {stats['total_size_mb']:.1f}MB")
        logger.info(f"  Average size: {stats['avg_size_mb']:.1f}MB")


def validate_pdf_file(
    file_path: Path,
    warn_size_mb: int = 50,
    max_size_mb: int = 200,
    skip_on_exceed: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a single PDF file.

    Args:
        file_path: Path to PDF file
        warn_size_mb: Warn if file exceeds this size
        max_size_mb: Skip files larger than this
        skip_on_exceed: Skip large files vs. error

    Returns:
        Tuple of (should_process, message)
    """
    validator = FileValidator(warn_size_mb, max_size_mb, skip_on_exceed)
    return validator.validate_file(file_path)
