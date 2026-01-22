"""
Batch processor for parallel PDF metadata extraction.

Orchestrates all extractors with ThreadPoolExecutor for efficient processing.
Includes session state caching, file validation, and execution status determination.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.extraction_result import PDFMetadataResult, ExecutionStatus
from ..extractors.document_metadata import DocumentMetadataExtractor
from ..extractors.digital_signatures import DigitalSignatureExtractor
from ..extractors.form_fields import FormFieldExtractor
from ..utils.session_state import SessionState
from ..utils.file_validator import FileValidator

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processes multiple PDFs in parallel"""

    def __init__(
        self,
        max_workers: int = 4,
        timeout_seconds: int = 60,
        validate_signatures: bool = True,
        enable_caching: bool = True,
        session_state_file: str = "session_state.json"
    ):
        """
        Initialize batch processor.

        Args:
            max_workers: Number of parallel workers (default: 4)
            timeout_seconds: Timeout per PDF (default: 60)
            validate_signatures: Enable signature validation (default: True)
            enable_caching: Enable session state caching (default: True)
            session_state_file: Session state file path (default: "session_state.json")
        """
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.validate_signatures = validate_signatures
        self.enable_caching = enable_caching

        # Initialize extractors
        self.metadata_extractor = DocumentMetadataExtractor()
        self.signature_extractor = DigitalSignatureExtractor(validate_signatures)
        self.form_field_extractor = FormFieldExtractor()

        # Initialize utilities
        self.file_validator = FileValidator()
        self.session_state = SessionState(session_state_file) if enable_caching else None

        logger.info(f"Batch processor initialized: {max_workers} workers, "
                   f"caching={'enabled' if enable_caching else 'disabled'}")

    def process_directory(
        self,
        directory: Path,
        recursive: bool = False,
        force_reprocess: bool = False
    ) -> List[PDFMetadataResult]:
        """
        Process all PDFs in a directory.

        Args:
            directory: Directory containing PDFs
            recursive: Process subdirectories recursively
            force_reprocess: Ignore cache and reprocess all files

        Returns:
            List of PDFMetadataResult objects
        """
        # Collect PDF files
        if recursive:
            pdf_files = list(directory.rglob("*.pdf"))
        else:
            pdf_files = list(directory.glob("*.pdf"))

        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        if not pdf_files:
            logger.warning("No PDF files found")
            return []

        # Process files
        results = self.process_files(pdf_files, force_reprocess)

        # Save session state
        if self.session_state:
            self.session_state.save_state()

        # Log statistics
        self.file_validator.log_statistics()

        return results

    def process_files(
        self,
        pdf_files: List[Path],
        force_reprocess: bool = False
    ) -> List[PDFMetadataResult]:
        """
        Process list of PDF files in parallel.

        Args:
            pdf_files: List of PDF file paths
            force_reprocess: Ignore cache and reprocess all

        Returns:
            List of PDFMetadataResult objects
        """
        results = []
        processed_count = 0
        skipped_count = 0
        error_count = 0

        start_time = time.time()

        # Process with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_file, force_reprocess): pdf_file
                for pdf_file in pdf_files
            }

            # Collect results
            for future in as_completed(future_to_pdf):
                pdf_file = future_to_pdf[future]

                try:
                    result = future.result(timeout=self.timeout_seconds)

                    if result:
                        results.append(result)
                        processed_count += 1

                        # Progress update every 10 PDFs
                        if processed_count % 10 == 0:
                            elapsed = time.time() - start_time
                            rate = processed_count / elapsed if elapsed > 0 else 0
                            logger.info(f"Progress: {processed_count}/{len(pdf_files)} PDFs "
                                       f"({rate:.1f} PDFs/sec)")
                    else:
                        skipped_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing {pdf_file.name}: {e}")

        # Final statistics
        elapsed = time.time() - start_time
        logger.info(f"Batch processing complete:")
        logger.info(f"  Total files: {len(pdf_files)}")
        logger.info(f"  Processed: {processed_count}")
        logger.info(f"  Skipped: {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Time: {elapsed:.1f}s ({processed_count/elapsed:.1f} PDFs/sec)")

        return results

    def process_single_pdf(
        self,
        pdf_path: Path,
        force_reprocess: bool = False
    ) -> Optional[PDFMetadataResult]:
        """
        Process a single PDF file.

        Args:
            pdf_path: Path to PDF file
            force_reprocess: Ignore cache

        Returns:
            PDFMetadataResult or None if skipped
        """
        start_time = time.time()

        # Validate file
        should_process, message = self.file_validator.validate_file(pdf_path)
        if not should_process:
            logger.info(f"Skipping {pdf_path.name}: {message}")
            return None

        # Check session state cache
        if self.session_state and not force_reprocess:
            if not self.session_state.should_process_pdf(pdf_path):
                # Return cached result (could be reconstructed, but for now skip)
                return None

        # Extract metadata
        doc_metadata = self.metadata_extractor.extract(pdf_path)

        # Extract signatures
        signatures = self.signature_extractor.extract(pdf_path)

        # Extract form fields
        form_fields = self.form_field_extractor.extract(pdf_path)

        # Determine execution status
        execution_status, execution_confidence = self._determine_execution_status(
            pdf_path, signatures, form_fields
        )

        # Count signature fields
        signature_fields = [f for f in form_fields if f.field_type == 'Signature']
        signed_fields = [f for f in signature_fields if f.field_value is not None]

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            doc_metadata, signatures, execution_confidence
        )

        # Create result
        result = PDFMetadataResult(
            document_metadata=doc_metadata,
            digital_signatures=signatures,
            form_fields=form_fields,
            has_digital_signatures=len(signatures) > 0,
            has_valid_signatures=any(s.is_valid for s in signatures if s.is_valid is not None),
            has_form_fields=len(form_fields) > 0,
            execution_status=execution_status,
            execution_confidence=execution_confidence,
            total_signature_fields=len(signature_fields),
            signed_signature_fields=len(signed_fields),
            extraction_timestamp=datetime.now(),
            processing_time_seconds=time.time() - start_time,
            overall_confidence=overall_confidence,
            error=doc_metadata.error
        )

        # Update session state
        if self.session_state:
            self.session_state.update_file_state(
                pdf_path,
                {
                    'execution_status': execution_status.value,
                    'has_digital_signatures': result.has_digital_signatures,
                    'execution_confidence': execution_confidence
                },
                result.processing_time_seconds
            )

        logger.debug(f"Processed {pdf_path.name}: {execution_status.value} "
                    f"(confidence: {execution_confidence}%)")

        return result

    def _determine_execution_status(
        self,
        pdf_path: Path,
        signatures: list,
        form_fields: list
    ) -> tuple:
        """
        Determine execution status with confidence score.

        Returns:
            Tuple of (ExecutionStatus, confidence)
        """
        # Check for valid signatures
        valid_sigs = [s for s in signatures if s.is_valid is True]
        if valid_sigs:
            return ExecutionStatus.FULLY_EXECUTED, 95

        # Check for signatures (not validated)
        if signatures:
            return ExecutionStatus.PARTIALLY_EXECUTED, 70

        # Check filename indicators
        filename_lower = pdf_path.name.lower()

        if any(indicator in filename_lower for indicator in [
            'fully executed', 'executed', 'counter-signed', 'countersigned'
        ]):
            return ExecutionStatus.FULLY_EXECUTED, 85

        if any(indicator in filename_lower for indicator in ['signed', '_signed']):
            return ExecutionStatus.FULLY_EXECUTED, 80

        if any(indicator in filename_lower for indicator in [
            'unsigned', 'draft', 'template'
        ]):
            return ExecutionStatus.UNSIGNED, 90

        # Check signature fields
        signature_fields = [f for f in form_fields if f.field_type == 'Signature']
        if signature_fields:
            signed_fields = [f for f in signature_fields if f.field_value is not None]
            if len(signed_fields) == len(signature_fields) and len(signed_fields) > 0:
                return ExecutionStatus.FULLY_EXECUTED, 75
            elif len(signed_fields) > 0:
                return ExecutionStatus.PARTIALLY_EXECUTED, 70
            else:
                return ExecutionStatus.UNSIGNED, 80

        # Default: unknown
        return ExecutionStatus.UNKNOWN, 40

    def _calculate_overall_confidence(
        self,
        doc_metadata,
        signatures: list,
        execution_confidence: int
    ) -> int:
        """Calculate overall confidence score"""
        confidences = [doc_metadata.confidence, execution_confidence]

        if signatures:
            confidences.extend([s.confidence for s in signatures])

        return int(sum(confidences) / len(confidences)) if confidences else 0
