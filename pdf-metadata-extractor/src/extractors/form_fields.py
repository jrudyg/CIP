"""
Form field extraction from PDF AcroForms.

Extracts all form fields including text fields, checkboxes, and signature fields.
"""

from pathlib import Path
from typing import List, Dict, Optional
import logging

from ..core.base_extractor import BaseExtractor
from ..core.extraction_result import FormField

logger = logging.getLogger(__name__)


class FormFieldExtractor(BaseExtractor):
    """Extracts form fields from PDF AcroForms"""

    # Field type mappings
    FIELD_TYPES = {
        '/Tx': 'Text',
        '/Btn': 'Button',
        '/Ch': 'Choice',
        '/Sig': 'Signature'
    }

    def __init__(self):
        super().__init__("FormField")

    def extract(self, pdf_path: Path) -> List[FormField]:
        """
        Extract form fields from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of FormField objects
        """
        self.log_extraction_start(pdf_path)

        try:
            # Import pikepdf
            import pikepdf

            form_fields = []

            # Open PDF
            with pikepdf.open(pdf_path) as pdf:
                # Check for AcroForm
                if '/AcroForm' not in pdf.Root:
                    logger.debug(f"No AcroForm found in {pdf_path.name}")
                    return []

                acro_form = pdf.Root.AcroForm

                # Check for fields
                if '/Fields' not in acro_form:
                    logger.debug(f"No fields in AcroForm for {pdf_path.name}")
                    return []

                # Iterate through fields
                for field in acro_form.Fields:
                    try:
                        field_data = self._extract_field_data(field, pdf)
                        if field_data:
                            form_fields.append(field_data)

                    except Exception as e:
                        logger.warning(f"Error processing field: {e}")
                        continue

            logger.info(f"Extracted {len(form_fields)} form fields from {pdf_path.name}")
            return form_fields

        except ImportError:
            logger.error("pikepdf not installed, cannot extract form fields")
            return []
        except Exception as e:
            self.log_extraction_error(pdf_path, e)
            return []

    def _extract_field_data(self, field, pdf) -> Optional[FormField]:
        """
        Extract data from a single form field.

        Args:
            field: pikepdf field object
            pdf: pikepdf PDF object

        Returns:
            FormField object or None
        """
        try:
            # Field name
            field_name = str(field.T) if '/T' in field else "Unknown"

            # Field type
            field_type_code = str(field.FT) if '/FT' in field else None
            field_type = self.FIELD_TYPES.get(field_type_code, 'Unknown')

            # Field value
            field_value = None
            if '/V' in field:
                val = field.V
                if val is not None:
                    field_value = str(val)

            # Flags
            flags = int(field.Ff) if '/Ff' in field else 0
            is_required = bool(flags & (1 << 1))  # Bit 2
            is_read_only = bool(flags & 1)         # Bit 1

            # Page number and coordinates
            page_number = 0
            coordinates = None

            # Try to find page and coordinates
            if '/Rect' in field:
                try:
                    rect = field.Rect
                    coordinates = {
                        'x1': float(rect[0]),
                        'y1': float(rect[1]),
                        'x2': float(rect[2]),
                        'y2': float(rect[3])
                    }

                    # Find page number (simplified)
                    if '/P' in field:
                        page_obj = field.P
                        for i, page in enumerate(pdf.pages):
                            if page.objgen == page_obj.objgen:
                                page_number = i + 1
                                break

                except Exception as e:
                    logger.debug(f"Could not extract coordinates: {e}")

            return FormField(
                field_name=field_name,
                field_type=field_type,
                field_value=field_value,
                is_required=is_required,
                is_read_only=is_read_only,
                page_number=page_number,
                coordinates=coordinates,
                confidence=100  # Form fields are structural data
            )

        except Exception as e:
            logger.warning(f"Error extracting field data: {e}")
            return None
