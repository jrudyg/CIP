#!/usr/bin/env python3
"""
PDF Metadata Extractor - CLI Entry Point

Extracts comprehensive metadata from PDFs including digital signatures,
form fields, and execution status.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.logging_config import setup_logging
from src.processors.batch_processor import BatchProcessor
from src.reporting.excel_generator import ExcelReportGenerator
from src.reporting.json_exporter import JSONExporter

# Load environment variables
load_dotenv()

# Version
__version__ = "1.0.0"


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Extract metadata from PDF files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process PDFs in a directory
  python main.py "C:\\contracts\\active"

  # Process recursively with 8 workers
  python main.py "C:\\contracts" --recursive --workers 8

  # JSON output only
  python main.py "C:\\contracts" --format json

  # Custom output directory
  python main.py "C:\\contracts" -o "C:\\reports\\metadata"

  # Force reprocess all files (ignore cache)
  python main.py "C:\\contracts" --force
        '''
    )

    parser.add_argument(
        'input_dir',
        type=str,
        help='Directory containing PDF files'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='./outputs',
        help='Output directory (default: ./outputs)'
    )

    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: from config or 4)'
    )

    parser.add_argument(
        '--format',
        choices=['excel', 'json', 'both'],
        default=None,
        help='Report format (default: from config or both)'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process subdirectories recursively'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocess all files (ignore cache)'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable session state caching'
    )

    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Disable signature validation (faster but less info)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'PDF Metadata Extractor v{__version__}'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    # Load config from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = os.getenv('LOG_FORMAT', 'json')
    max_workers = args.workers or int(os.getenv('MAX_WORKERS', '4'))
    report_format = args.format or os.getenv('REPORT_FORMAT', 'both')
    validate_signatures = not args.no_validation and os.getenv('VALIDATE_SIGNATURES', 'true').lower() == 'true'
    enable_caching = not args.no_cache and os.getenv('ENABLE_CACHING', 'true').lower() == 'true'

    # Setup logging
    setup_logging(log_level=log_level, log_format=log_format)
    logger = logging.getLogger(__name__)

    logger.info(f"PDF Metadata Extractor v{__version__}")
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Workers: {max_workers}")
    logger.info(f"Report format: {report_format}")
    logger.info(f"Signature validation: {'enabled' if validate_signatures else 'disabled'}")
    logger.info(f"Caching: {'enabled' if enable_caching else 'disabled'}")

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize batch processor
    processor = BatchProcessor(
        max_workers=max_workers,
        validate_signatures=validate_signatures,
        enable_caching=enable_caching
    )

    # Process PDFs
    try:
        results = processor.process_directory(
            input_dir,
            recursive=args.recursive,
            force_reprocess=args.force
        )

        if not results:
            logger.warning("No results to export")
            return

        # Generate reports
        if report_format in ['excel', 'both']:
            logger.info("Generating Excel report...")
            excel_gen = ExcelReportGenerator()
            excel_path = output_dir / 'reports' / 'metadata_report.xlsx'
            excel_path.parent.mkdir(parents=True, exist_ok=True)
            excel_gen.generate(results, excel_path)

        if report_format in ['json', 'both']:
            logger.info("Generating JSON export...")
            json_exp = JSONExporter()
            json_path = output_dir / 'exports' / 'metadata_export.json'
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_exp.export(results, json_path)

        logger.info("✓ Processing complete!")

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
