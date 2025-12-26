"""
CIP Database Index Optimization Script

Creates performance indexes on contracts.db for frequently queried columns.
Safe to run multiple times - skips existing indexes.

Usage:
    python scripts/optimize_db_indexes.py

Created: 2025-12-17
"""

import sqlite3
import time
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "contracts.db"

# Index definitions: (name, table, columns)
INDEXES = [
    # contracts table - single column indexes
    ("idx_contracts_archived", "contracts", "archived"),
    ("idx_contracts_upload_date", "contracts", "upload_date"),
    ("idx_contracts_created_at", "contracts", "created_at"),
    ("idx_contracts_expiration", "contracts", "expiration_date"),
    ("idx_contracts_effective", "contracts", "effective_date"),

    # contracts table - composite indexes for common query patterns
    ("idx_contracts_archived_status", "contracts", "archived, status"),
    ("idx_contracts_archived_upload", "contracts", "archived, upload_date DESC"),

    # risk_assessments table
    ("idx_risk_assessments_date", "risk_assessments", "assessment_date"),
    ("idx_risk_assessments_risk", "risk_assessments", "overall_risk"),

    # clauses table
    ("idx_clauses_category", "clauses", "category"),
    ("idx_clauses_section", "clauses", "section_number"),
]


def optimize_indexes(db_path: Path = DB_PATH, verbose: bool = True) -> dict:
    """
    Create missing indexes on the database.

    Returns:
        dict with 'created', 'skipped', 'errors' counts
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get existing indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing = {r[0] for r in cursor.fetchall()}

    results = {"created": 0, "skipped": 0, "errors": 0}

    if verbose:
        print(f"Optimizing: {db_path}")
        print(f"Existing indexes: {len(existing)}")
        print()

    for idx_name, table, columns in INDEXES:
        if idx_name in existing:
            if verbose:
                print(f"  SKIP: {idx_name} (exists)")
            results["skipped"] += 1
        else:
            sql = f"CREATE INDEX {idx_name} ON {table}({columns})"
            try:
                start = time.time()
                cursor.execute(sql)
                elapsed = (time.time() - start) * 1000
                if verbose:
                    print(f"  CREATE: {idx_name} ({elapsed:.1f}ms)")
                results["created"] += 1
            except Exception as e:
                if verbose:
                    print(f"  ERROR: {idx_name} - {e}")
                results["errors"] += 1

    conn.commit()
    conn.close()

    if verbose:
        print()
        print(f"Created: {results['created']}")
        print(f"Skipped: {results['skipped']}")
        if results["errors"]:
            print(f"Errors: {results['errors']}")

    return results


def verify_indexes(db_path: Path = DB_PATH) -> None:
    """Print all indexes in the database."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, tbl_name
        FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY tbl_name, name
    """)

    print("Current indexes:")
    current_table = None
    for name, table in cursor.fetchall():
        if table != current_table:
            print(f"\n  {table}:")
            current_table = table
        print(f"    - {name}")

    conn.close()


if __name__ == "__main__":
    import sys

    if "--verify" in sys.argv:
        verify_indexes()
    else:
        optimize_indexes()
