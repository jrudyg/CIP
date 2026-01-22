"""
Digital signature extraction with 3-tier fallback chain.

TIER 1: pyhanko - Full validation + certificate info (best)
TIER 2: pikepdf - Signature field detection (good)
TIER 3: pypdf + text search - Keyword detection (basic)
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

from ..core.base_extractor import BaseExtractor
from ..core.extraction_result import DigitalSignature

logger = logging.getLogger(__name__)


class DigitalSignatureExtractor(BaseExtractor):
    """Extracts digital signatures with 3-tier fallback"""

    # E-signature provider keywords
    PROVIDER_KEYWORDS = {
        'DocuSign': ['DocuSign', 'Certificate of Completion', 'DocuSign Envelope ID', 'Envelope ID'],
        'Adobe Sign': ['Adobe Sign', 'EchoSign', 'Adobe eSign'],
        'HelloSign': ['HelloSign', 'Dropbox Sign'],
        'PandaDoc': ['PandaDoc'],
        'SignNow': ['SignNow'],
        'eSignLive': ['eSignLive']
    }

    def __init__(self, validate_signatures: bool = True):
        """
        Initialize signature extractor.

        Args:
            validate_signatures: Whether to validate signatures (requires pyhanko)
        """
        super().__init__("DigitalSignature")
        self.validate_signatures = validate_signatures

    def extract(self, pdf_path: Path) -> List[DigitalSignature]:
        """
        Extract digital signatures with 3-tier fallback.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of DigitalSignature objects
        """
        self.log_extraction_start(pdf_path)

        # TIER 1: Try pyhanko (best - full validation + certificate info)
        if self.validate_signatures:
            signatures = self._extract_with_pyhanko(pdf_path)
            if signatures:
                logger.info(f"✓ pyhanko succeeded: {len(signatures)} signatures with validation")
                return signatures

        # TIER 2: Try pikepdf (good - signature field detection)
        signatures = self._extract_with_pikepdf(pdf_path)
        if signatures:
            logger.info(f"✓ pikepdf succeeded: {len(signatures)} signature fields detected")
            return signatures

        # TIER 3: Try pypdf + text search (basic - keyword detection)
        signatures = self._extract_with_text_search(pdf_path)
        if signatures:
            logger.info(f"✓ pypdf text search found provider: {signatures[0].signature_type}")
            return signatures

        # TIER 4: Complete failure
        logger.debug(f"✗ All signature extraction methods failed for {pdf_path.name}")
        return []

    def _extract_with_pyhanko(self, pdf_path: Path) -> List[DigitalSignature]:
        """
        TIER 1: Extract and validate signatures using pyhanko.

        Returns:
            List of validated signatures or empty list
        """
        try:
            logger.debug(f"Attempting pyhanko extraction for {pdf_path.name}")

            # Import pyhanko (optional dependency)
            from pyhanko.sign.validation import validate_pdf_signature
            from pyhanko.pdf_utils.reader import PdfFileReader

            signatures = []

            # Open PDF with pyhanko
            with open(pdf_path, 'rb') as f:
                reader = PdfFileReader(f)

                # Get signature fields
                if not hasattr(reader, 'embedded_signatures') or not reader.embedded_signatures:
                    logger.debug("No embedded signatures found by pyhanko")
                    return []

                # Validate each signature
                for sig_field in reader.embedded_signatures:
                    try:
                        # Validate signature
                        validation_result = validate_pdf_signature(sig_field)

                        # Extract signature info
                        sig_obj = sig_field.sig_object

                        signature = DigitalSignature(
                            signature_name=sig_field.field_name,
                            signer_name=validation_result.signer_info.subject_dn if hasattr(validation_result, 'signer_info') else None,
                            signing_time=self._extract_signing_time(sig_obj),
                            signature_type=self._get_signature_type(sig_obj),
                            certificate_issuer=validation_result.signer_info.issuer_dn if hasattr(validation_result, 'signer_info') else None,
                            certificate_subject=validation_result.signer_info.subject_dn if hasattr(validation_result, 'signer_info') else None,
                            is_valid=validation_result.bottom_line if hasattr(validation_result, 'bottom_line') else None,
                            signature_covers_document=validation_result.coverage if hasattr(validation_result, 'coverage') else False,
                            confidence=90 if validation_result.bottom_line else 60,
                            notes="Validated via pyhanko"
                        )

                        signatures.append(signature)

                    except Exception as e:
                        logger.warning(f"Failed to validate signature field: {e}")
                        continue

            return signatures

        except ImportError:
            logger.debug("pyhanko not installed, skipping TIER 1")
            return []
        except Exception as e:
            logger.warning(f"pyhanko failed for {pdf_path.name}: {e}")
            return []

    def _extract_with_pikepdf(self, pdf_path: Path) -> List[DigitalSignature]:
        """
        TIER 2: Extract signature fields using pikepdf.

        Returns:
            List of signature fields or empty list
        """
        try:
            logger.debug(f"Falling back to pikepdf for {pdf_path.name}")

            # Import pikepdf (required dependency)
            import pikepdf

            signatures = []

            # Open PDF with pikepdf
            with pikepdf.open(pdf_path) as pdf:
                # Check for AcroForm
                if '/AcroForm' not in pdf.Root:
                    logger.debug("No AcroForm found")
                    return []

                acro_form = pdf.Root.AcroForm

                # Check for fields
                if '/Fields' not in acro_form:
                    logger.debug("No fields in AcroForm")
                    return []

                # Iterate through fields
                for field in acro_form.Fields:
                    try:
                        # Check if signature field
                        if '/FT' in field and str(field.FT) == '/Sig':
                            field_name = str(field.T) if '/T' in field else "Unknown"

                            # Check if signed (has /V value)
                            is_signed = '/V' in field and field.V is not None

                            if is_signed:
                                signature = DigitalSignature(
                                    signature_name=field_name,
                                    signature_type=self._get_pikepdf_signature_type(field),
                                    is_valid=None,  # Cannot validate with pikepdf
                                    confidence=70,
                                    notes="Detected via pikepdf (validation not performed)"
                                )
                                signatures.append(signature)

                    except Exception as e:
                        logger.warning(f"Error processing field: {e}")
                        continue

            return signatures

        except ImportError:
            logger.warning("pikepdf not installed, skipping TIER 2")
            return []
        except Exception as e:
            logger.warning(f"pikepdf failed for {pdf_path.name}: {e}")
            return []

    def _extract_with_text_search(self, pdf_path: Path) -> List[DigitalSignature]:
        """
        TIER 3: Detect e-signatures via text search.

        Returns:
            List with single signature if provider detected, else empty
        """
        try:
            logger.debug(f"Falling back to pypdf text search for {pdf_path.name}")

            # Extract full PDF text
            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text()

            # Search for provider keywords
            provider = self._detect_provider(text)

            if provider != 'Unknown':
                signature = DigitalSignature(
                    signature_name="Detected from text",
                    signer_name=None,
                    signing_time=None,
                    signature_type=provider,
                    is_valid=None,
                    confidence=40,
                    notes=f"Detected via text search (no signature fields found)"
                )
                return [signature]

        except Exception as e:
            logger.warning(f"pypdf text search failed for {pdf_path.name}: {e}")

        return []

    def _detect_provider(self, text: str) -> str:
        """Detect e-signature provider from text"""
        text_lower = text.lower()

        for provider, keywords in self.PROVIDER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return provider

        return 'Unknown'

    def _get_signature_type(self, sig_obj) -> str:
        """Extract signature type from signature object"""
        try:
            if hasattr(sig_obj, 'SubFilter'):
                return str(sig_obj.SubFilter)
            return "unknown"
        except:
            return "unknown"

    def _get_pikepdf_signature_type(self, field) -> str:
        """Extract signature type from pikepdf field"""
        try:
            if '/V' in field and '/SubFilter' in field.V:
                return str(field.V.SubFilter)
            return "unknown"
        except:
            return "unknown"

    def _extract_signing_time(self, sig_obj) -> Optional[datetime]:
        """Extract signing time from signature object"""
        try:
            if hasattr(sig_obj, 'M'):
                # Parse PDF date format
                date_str = str(sig_obj.M)
                if date_str.startswith('D:'):
                    date_str = date_str[2:]
                if len(date_str) >= 14:
                    return datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
        except:
            pass
        return None
