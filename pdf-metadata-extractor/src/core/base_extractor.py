"""
Abstract base class for all PDF extractors.

Provides common interface and confidence scoring methodology.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for PDF metadata extractors"""

    def __init__(self, name: str):
        """
        Initialize extractor.

        Args:
            name: Extractor name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def extract(self, pdf_path: Path) -> Any:
        """
        Extract metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted metadata (type varies by extractor)
        """
        pass

    def calculate_confidence(
        self,
        base_confidence: int,
        data_points_found: int,
        expected_data_points: int = 5,
        has_errors: bool = False
    ) -> int:
        """
        Calculate confidence score using standard methodology.

        Args:
            base_confidence: Base confidence level (0-100)
            data_points_found: Number of data points successfully extracted
            expected_data_points: Expected number of data points
            has_errors: Whether extraction encountered errors

        Returns:
            Confidence score (0-100)
        """
        confidence = base_confidence

        # Adjust based on data completeness
        completeness_ratio = data_points_found / expected_data_points if expected_data_points > 0 else 0

        if completeness_ratio >= 0.6:  # ≥60% complete
            confidence += 15
        elif completeness_ratio < 0.4:  # <40% complete
            confidence -= 20

        # Penalty for errors
        if has_errors:
            confidence -= 10

        # Clamp to 0-100
        return max(0, min(100, confidence))

    def log_extraction_start(self, pdf_path: Path):
        """Log extraction start"""
        self.logger.debug(f"Starting {self.name} extraction: {pdf_path.name}")

    def log_extraction_complete(self, pdf_path: Path, confidence: int):
        """Log extraction completion"""
        self.logger.debug(f"Completed {self.name} extraction: {pdf_path.name} (confidence: {confidence}%)")

    def log_extraction_error(self, pdf_path: Path, error: Exception):
        """Log extraction error"""
        self.logger.error(f"Error in {self.name} extraction for {pdf_path.name}: {error}")

    def safe_extract(self, pdf_path: Path) -> Optional[Any]:
        """
        Safe extraction wrapper with error handling.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted data or None on error
        """
        try:
            self.log_extraction_start(pdf_path)
            result = self.extract(pdf_path)
            return result
        except Exception as e:
            self.log_extraction_error(pdf_path, e)
            return None
