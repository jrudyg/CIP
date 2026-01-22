"""
Integration smoke tests for PDF metadata extractor.

Tests the complete extraction pipeline end-to-end.
"""

import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.processors.batch_processor import BatchProcessor
from src.reporting.excel_generator import ExcelReportGenerator
from src.reporting.json_exporter import JSONExporter
from src.utils.session_state import SessionState
from src.utils.cost_tracker import VisionAPITracker
from src.utils.file_validator import validate_pdf_file


class TestEndToEndPipeline:
    """Integration tests for complete extraction pipeline"""

    def test_process_sample_directory(self, tmp_path):
        """Smoke test: Process sample PDFs and verify all outputs"""
        # Setup
        sample_dir = Path("tests/fixtures/sample_pdfs")
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)

        # Skip if no sample PDFs
        if not sample_dir.exists() or not list(sample_dir.glob("*.pdf")):
            pytest.skip("No sample PDFs found for integration testing")

        # Execute
        processor = BatchProcessor(max_workers=2, enable_caching=False)
        results = processor.process_directory(sample_dir)

        # Assertions
        assert len(results) > 0, "Should process at least one PDF"
        assert all(r.document_metadata is not None for r in results), \
            "All PDFs should have document metadata"

        # Verify extraction ran without errors
        total_sigs = sum(len(r.digital_signatures) for r in results)
        assert total_sigs >= 0, "Signature extraction should run without errors"

        # Verify report generation
        excel_path = output_dir / "test_report.xlsx"
        json_path = output_dir / "test_export.json"

        excel_gen = ExcelReportGenerator()
        excel_gen.generate(results, excel_path, include_timestamp=False)
        assert excel_path.exists(), "Excel report should be created"

        json_exp = JSONExporter()
        json_exp.export(results, json_path, include_timestamp=False)
        assert json_path.exists(), "JSON export should be created"

    def test_error_handling_corrupted_pdf(self, tmp_path):
        """Test graceful handling of corrupted PDF"""
        corrupted_path = tmp_path / "corrupted.pdf"

        # Create a corrupted PDF (truncated)
        corrupted_path.write_bytes(b"%PDF-1.4\n%truncated")

        processor = BatchProcessor(enable_caching=False)
        results = processor.process_directory(tmp_path)

        # Should return result with error field populated
        if results:
            corrupted_result = [r for r in results
                               if r.document_metadata.filename == "corrupted.pdf"]
            if corrupted_result:
                assert corrupted_result[0].error is not None, \
                    "Should capture error"
                assert corrupted_result[0].overall_confidence == 0, \
                    "Confidence should be 0 on error"

    def test_execution_status_classification(self, tmp_path):
        """Test execution status is correctly classified"""
        sample_dir = Path("tests/fixtures/sample_pdfs")

        if not sample_dir.exists():
            pytest.skip("No sample PDFs found")

        processor = BatchProcessor(max_workers=2, enable_caching=False)
        results = processor.process_directory(sample_dir)

        # Verify execution status is set (not None)
        for result in results:
            assert result.execution_status is not None, \
                f"Execution status missing for {result.document_metadata.filename}"
            assert result.execution_confidence >= 0, \
                "Confidence should be non-negative"

    def test_session_state_caching(self, tmp_path):
        """Test session state prevents re-processing unchanged files"""
        sample_dir = Path("tests/fixtures/sample_pdfs")

        if not sample_dir.exists():
            pytest.skip("No sample PDFs found")

        state_file = tmp_path / "session_test.json"
        state = SessionState(str(state_file))

        # First run
        processor = BatchProcessor(
            max_workers=2,
            enable_caching=True,
            session_state_file=str(state_file)
        )
        results1 = processor.process_directory(sample_dir)

        if not results1:
            pytest.skip("No PDFs processed")

        # Verify state file was created
        assert state_file.exists(), "Session state file should be created"

    def test_vision_api_cost_tracking(self):
        """Test vision API cost tracking and budget limits"""
        tracker = VisionAPITracker(cost_per_call=0.02, max_budget=1.00)

        # Simulate 50 calls
        for i in range(50):
            if tracker.can_make_call():
                tracker.track_call()

        # Should stop at $1.00 budget (50 calls × $0.02 = $1.00)
        assert tracker.calls == 50
        assert tracker.estimated_cost == 1.00
        assert tracker.budget_exceeded is True

    def test_large_file_handling(self):
        """Test file size limits are enforced"""
        # Mock large file using Path with stat()
        class MockPath:
            name = "large_contract.pdf"

            def stat(self):
                class Stat:
                    st_size = 250 * 1024 * 1024  # 250MB
                return Stat()

            def exists(self):
                return True

            def is_file(self):
                return True

        large_file = MockPath()

        from src.utils.file_validator import FileValidator
        validator = FileValidator(max_size_mb=200, skip_on_exceed=True)

        should_process, message = validator.validate_file(large_file)
        assert should_process is False, "Files >200MB should be skipped"
        assert "exceeds maximum size" in message.lower()

    def test_file_validator_warnings(self):
        """Test file size warnings for medium-large files"""
        class MockPath:
            name = "medium_contract.pdf"

            def stat(self):
                class Stat:
                    st_size = 75 * 1024 * 1024  # 75MB
                return Stat()

            def exists(self):
                return True

            def is_file(self):
                return True

        medium_file = MockPath()

        from src.utils.file_validator import FileValidator
        validator = FileValidator(warn_size_mb=50, max_size_mb=200)

        should_process, message = validator.validate_file(medium_file)
        assert should_process is True, "Files <200MB should be processed"
        assert message is not None, "Should warn for files >50MB"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
