"""
Document metadata extraction from PDF /Info dictionary.

Uses pypdf to extract basic PDF metadata like author, dates, producer, etc.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

try:
    from pypdf import PdfReader
except ImportError:
    # Try alternate import
    from PyPDF2 import PdfReader

from ..core.base_extractor import BaseExtractor
from ..core.extraction_result import DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentMetadataExtractor(BaseExtractor):
    """Extracts document metadata from PDF /Info dictionary"""

    def __init__(self):
        super().__init__("DocumentMetadata")

    def extract(self, pdf_path: Path) -> DocumentMetadata:
        """
        Extract document metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            DocumentMetadata object
        """
        self.log_extraction_start(pdf_path)

        try:
            # Open PDF with pypdf
            reader = PdfReader(str(pdf_path))

            # Extract metadata
            metadata = reader.metadata if reader.metadata else {}

            # Get file stats
            file_size = pdf_path.stat().st_size
            page_count = len(reader.pages)
            is_encrypted = reader.is_encrypted

            # Parse dates (PDF format: D:YYYYMMDDHHmmSS)
            creation_date = self._parse_pdf_date(metadata.get('/CreationDate'))
            modification_date = self._parse_pdf_date(metadata.get('/ModDate'))

            # Extract standard fields
            author = self._clean_string(metadata.get('/Author'))
            title = self._clean_string(metadata.get('/Title'))
            subject = self._clean_string(metadata.get('/Subject'))
            keywords = self._clean_string(metadata.get('/Keywords'))
            creator = self._clean_string(metadata.get('/Creator'))
            producer = self._clean_string(metadata.get('/Producer'))

            # Get PDF version
            pdf_version = f"1.{reader.pdf_header[5:]}" if hasattr(reader, 'pdf_header') else None

            # Calculate confidence
            data_points = sum([
                author is not None,
                title is not None,
                creation_date is not None,
                modification_date is not None,
                creator is not None,
                producer is not None
            ])

            confidence = self.calculate_confidence(
                base_confidence=70,
                data_points_found=data_points,
                expected_data_points=6,
                has_errors=False
            )

            notes = f"{data_points}/6 metadata fields populated"

            result = DocumentMetadata(
                filename=pdf_path.name,
                file_path=str(pdf_path),
                creation_date=creation_date,
                modification_date=modification_date,
                author=author,
                title=title,
                subject=subject,
                keywords=keywords,
                creator=creator,
                producer=producer,
                pdf_version=pdf_version,
                page_count=page_count,
                file_size_bytes=file_size,
                is_encrypted=is_encrypted,
                confidence=confidence,
                notes=notes,
                error=None
            )

            self.log_extraction_complete(pdf_path, confidence)
            return result

        except Exception as e:
            self.log_extraction_error(pdf_path, e)

            # Return minimal metadata on error
            return DocumentMetadata(
                filename=pdf_path.name,
                file_path=str(pdf_path),
                file_size_bytes=pdf_path.stat().st_size if pdf_path.exists() else 0,
                page_count=0,
                is_encrypted=False,
                confidence=0,
                notes="Extraction failed",
                error=str(e)
            )

    def _parse_pdf_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS) to datetime.

        Args:
            date_str: PDF date string

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        try:
            # Remove 'D:' prefix if present
            if date_str.startswith('D:'):
                date_str = date_str[2:]

            # Remove timezone info (after + or -)
            if '+' in date_str:
                date_str = date_str.split('+')[0]
            elif '-' in date_str and len(date_str) > 14:
                date_str = date_str.split('-')[0]

            # Parse: YYYYMMDDHHmmSS
            if len(date_str) >= 14:
                return datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], '%Y%m%d')

        except Exception as e:
            logger.debug(f"Failed to parse PDF date '{date_str}': {e}")

        return None

    def _clean_string(self, value: Optional[str]) -> Optional[str]:
        """
        Clean and normalize string value.

        Args:
            value: String value

        Returns:
            Cleaned string or None
        """
        if not value:
            return None

        # Convert to string if not already
        if not isinstance(value, str):
            value = str(value)

        # Strip whitespace
        value = value.strip()

        # Return None for empty strings
        return value if value else None
