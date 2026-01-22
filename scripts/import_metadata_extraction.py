#!/usr/bin/env python3
"""
Import PDF metadata extraction results into CIP database.

This script:
1. Loads extraction results from pdf-metadata-extractor JSON output
2. Creates contract_metadata table in contracts.db if it doesn't exist
3. Imports all extraction results with execution status, signatures, and metadata
4. Provides summary statistics of the import

Usage:
    python scripts/import_metadata_extraction.py
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def create_metadata_table(cursor):
    """Create contract_metadata table if it doesn't exist."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contract_metadata (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            execution_status TEXT,
            execution_confidence INTEGER,
            has_digital_signatures BOOLEAN,
            total_signature_fields INTEGER,
            signed_signature_fields INTEGER,
            creation_date TEXT,
            modification_date TEXT,
            author TEXT,
            producer TEXT,
            page_count INTEGER,
            file_size INTEGER,
            extraction_timestamp TEXT,
            overall_confidence INTEGER,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indices for common queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_execution_status
        ON contract_metadata(execution_status)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_filename
        ON contract_metadata(filename)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_has_signatures
        ON contract_metadata(has_digital_signatures)
    ''')

    print("[OK] contract_metadata table created/verified")


def import_extraction_results(json_path, db_path):
    """Import extraction results from JSON into database."""

    # Load extraction results
    print(f"\nLoading extraction results from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['pdfs']
    metadata = data['metadata']

    print(f"[OK] Loaded {len(results)} extraction results")
    print(f"  Generated: {metadata['generated']}")
    print(f"  Total PDFs: {metadata['total_pdfs']}")
    print(f"  Executed contracts: {metadata['executed_contracts']}")

    # Connect to database
    print(f"\nConnecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    create_metadata_table(cursor)

    # Import results
    print(f"\nImporting {len(results)} records...")
    imported = 0
    updated = 0
    errors = []

    for result in results:
        doc = result['document_metadata']
        try:
            # Try to insert
            cursor.execute('''
                INSERT INTO contract_metadata
                (filename, file_path, execution_status, execution_confidence,
                 has_digital_signatures, total_signature_fields, signed_signature_fields,
                 creation_date, modification_date, author, producer,
                 page_count, file_size, extraction_timestamp, overall_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                doc['filename'],
                doc['file_path'],
                result['execution_status'],
                result['execution_confidence'],
                result['has_digital_signatures'],
                result['total_signature_fields'],
                result['signed_signature_fields'],
                doc.get('creation_date'),
                doc.get('modification_date'),
                doc.get('author'),
                doc.get('producer'),
                doc.get('page_count'),
                doc.get('file_size'),
                result['extraction_timestamp'],
                result['overall_confidence']
            ))
            imported += 1

        except sqlite3.IntegrityError:
            # File already exists, update it
            cursor.execute('''
                UPDATE contract_metadata
                SET filename = ?,
                    execution_status = ?,
                    execution_confidence = ?,
                    has_digital_signatures = ?,
                    total_signature_fields = ?,
                    signed_signature_fields = ?,
                    creation_date = ?,
                    modification_date = ?,
                    author = ?,
                    producer = ?,
                    page_count = ?,
                    file_size = ?,
                    extraction_timestamp = ?,
                    overall_confidence = ?,
                    imported_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            ''', (
                doc['filename'],
                result['execution_status'],
                result['execution_confidence'],
                result['has_digital_signatures'],
                result['total_signature_fields'],
                result['signed_signature_fields'],
                doc.get('creation_date'),
                doc.get('modification_date'),
                doc.get('author'),
                doc.get('producer'),
                doc.get('page_count'),
                doc.get('file_size'),
                result['extraction_timestamp'],
                result['overall_confidence'],
                doc['file_path']
            ))
            updated += 1

        except Exception as e:
            errors.append((doc['filename'], str(e)))

    # Commit changes
    conn.commit()

    # Print summary
    print(f"\n{'='*80}")
    print("IMPORT SUMMARY")
    print(f"{'='*80}")
    print(f"Records imported: {imported}")
    print(f"Records updated: {updated}")
    print(f"Total processed: {imported + updated}")
    print(f"Errors: {len(errors)}")

    if errors:
        print(f"\nErrors encountered:")
        for filename, error in errors[:10]:
            print(f"  - {filename}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    # Verify import with statistics
    print(f"\n{'='*80}")
    print("DATABASE STATISTICS")
    print(f"{'='*80}")

    cursor.execute('SELECT COUNT(*) FROM contract_metadata')
    total_records = cursor.fetchone()[0]
    print(f"Total records in database: {total_records}")

    cursor.execute('''
        SELECT execution_status, COUNT(*)
        FROM contract_metadata
        GROUP BY execution_status
        ORDER BY COUNT(*) DESC
    ''')
    print(f"\nExecution status distribution:")
    for status, count in cursor.fetchall():
        pct = (count / total_records) * 100
        print(f"  {status:25s}: {count:3d} ({pct:5.1f}%)")

    cursor.execute('''
        SELECT COUNT(*)
        FROM contract_metadata
        WHERE has_digital_signatures = 1
    ''')
    sig_count = cursor.fetchone()[0]
    print(f"\nContracts with digital signatures: {sig_count}/{total_records} ({sig_count/total_records*100:.1f}%)")

    cursor.execute('''
        SELECT AVG(execution_confidence)
        FROM contract_metadata
    ''')
    avg_conf = cursor.fetchone()[0]
    print(f"Average execution confidence: {avg_conf:.1f}%")

    # Close connection
    conn.close()
    print(f"\n[OK] Import complete")
    return imported + updated


def main():
    """Main entry point."""
    # Paths
    cip_root = Path(r"C:\Users\jrudy\CIP")
    json_path = cip_root / "pdf-metadata-extractor" / "outputs" / "full_portfolio" / "exports"
    db_path = cip_root / "data" / "contracts.db"

    # Find latest JSON export
    json_files = list(json_path.glob("metadata_export_*.json"))
    if not json_files:
        print(f"ERROR: No extraction results found in {json_path}")
        sys.exit(1)

    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)

    print(f"\n{'='*80}")
    print("CIP METADATA EXTRACTION IMPORT")
    print(f"{'='*80}")
    print(f"Extraction results: {latest_json.name}")
    print(f"Target database: {db_path}")

    # Verify database exists
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    # Import
    try:
        import_extraction_results(latest_json, db_path)
        print(f"\n{'='*80}")
        print("[OK] SUCCESS: Metadata import completed successfully")
        print(f"{'='*80}")

    except Exception as e:
        print(f"\nERROR: Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
