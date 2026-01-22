"""
JSON export for programmatic access to extraction results.

Exports all extraction data in a structured JSON format.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from ..core.extraction_result import PDFMetadataResult, ExecutionStatus

logger = logging.getLogger(__name__)


class JSONExporter:
    """Exports extraction results to JSON format"""

    def __init__(self):
        """Initialize JSON exporter"""
        pass

    def export(
        self,
        results: List[PDFMetadataResult],
        output_path: Path,
        include_timestamp: bool = True,
        pretty_print: bool = True
    ):
        """
        Export results to JSON file.

        Args:
            results: List of extraction results
            output_path: Output file path
            include_timestamp: Include timestamp in filename
            pretty_print: Pretty-print JSON (indent=2)
        """
        logger.info(f"Exporting {len(results)} results to JSON...")

        # Add timestamp to filename if requested
        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stem = output_path.stem
            output_path = output_path.parent / f"{stem}_{timestamp}{output_path.suffix}"

        # Build JSON structure
        export_data = {
            'metadata': self._build_metadata(results),
            'pdfs': [self._result_to_dict(result) for result in results]
        }

        # Write to file
        with open(output_path, 'w') as f:
            if pretty_print:
                json.dump(export_data, f, indent=2, default=str)
            else:
                json.dump(export_data, f, default=str)

        logger.info(f"JSON export saved: {output_path}")

    def _build_metadata(self, results: List[PDFMetadataResult]) -> dict:
        """Build metadata section"""
        total_pdfs = len(results)
        total_signatures = sum(len(r.digital_signatures) for r in results)
        executed_contracts = sum(
            1 for r in results
            if r.execution_status == ExecutionStatus.FULLY_EXECUTED
        )
        avg_confidence = (
            sum(r.overall_confidence for r in results) / total_pdfs
            if total_pdfs > 0 else 0
        )

        return {
            'generated': datetime.now().isoformat(),
            'total_pdfs': total_pdfs,
            'total_signatures': total_signatures,
            'executed_contracts': executed_contracts,
            'average_confidence': round(avg_confidence, 2)
        }

    def _result_to_dict(self, result: PDFMetadataResult) -> dict:
        """Convert PDFMetadataResult to dictionary"""
        return result.to_dict()
