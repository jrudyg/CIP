"""
CIP Database Maintenance Script
Optimizes database performance and integrity
"""

import sqlite3
from pathlib import Path
import time

DB_PATH = Path(__file__).parent.parent / "data" / "contracts.db"

def add_missing_indexes():
    """Add performance indexes to database"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    indexes = [
        # Contracts table
        "CREATE INDEX IF NOT EXISTS idx_contracts_upload_date ON contracts(upload_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_contracts_effective_date ON contracts(effective_date)",
        "CREATE INDEX IF NOT EXISTS idx_contracts_hash ON contracts(content_hash)",
        "CREATE INDEX IF NOT EXISTS idx_contracts_parent ON contracts(parent_id)",

        # Risk assessments table (active table - not the orphaned 'assessments' table)
        "CREATE INDEX IF NOT EXISTS idx_risk_assessments_contract_id ON risk_assessments(contract_id)",
        "CREATE INDEX IF NOT EXISTS idx_risk_assessments_date ON risk_assessments(assessment_date DESC)",

        # Negotiations table removed in schema v2.0
    ]

    print("Adding missing indexes...")
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            idx_name = idx_sql.split("idx_")[1].split(" ON")[0]
            print(f"  [OK] idx_{idx_name}")
        except Exception as e:
            print(f"  [SKIP] {idx_sql[:50]}... ({str(e)})")

    conn.commit()
    conn.close()
    print("Indexes updated!\n")

def analyze_database():
    """Analyze database for query optimization"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("Analyzing database...")
    cursor.execute("ANALYZE")
    conn.commit()
    conn.close()
    print("[OK] Database analyzed\n")

def vacuum_database():
    """Reclaim unused space"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Get size before
    cursor = conn.cursor()
    cursor.execute("PRAGMA page_count")
    page_count_before = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    size_before = page_count_before * page_size

    print("Vacuuming database...")
    print(f"  Size before: {size_before / 1024:.1f} KB")

    conn.execute("VACUUM")

    # Get size after
    cursor.execute("PRAGMA page_count")
    page_count_after = cursor.fetchone()[0]
    size_after = page_count_after * page_size

    print(f"  Size after: {size_after / 1024:.1f} KB")
    print(f"  Reclaimed: {(size_before - size_after) / 1024:.1f} KB\n")

    conn.close()

def check_integrity():
    """Check database integrity"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("Checking database integrity...")
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]

    if result == "ok":
        print("  [OK] Database integrity verified\n")
    else:
        print(f"  [ERROR] Integrity check failed: {result}\n")

    conn.close()

def get_statistics():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("Database Statistics:")

    tables = [
        'contracts', 'clauses', 'risk_assessments',
        'analysis_snapshots', 'comparison_snapshots',
        'redline_snapshots', 'contract_relationships', 'audit_log'
    ]

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:20} {count:6} records")
        except:
            print(f"  {table:20} (table not found)")

    print()
    conn.close()

def remove_orphaned_records():
    """Remove records with no parent contract"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("Checking for orphaned records...")

    # Check if legacy tables exist (they may have been dropped by schema cleanup migration)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    orphaned_metadata = 0
    orphaned_assessments = 0
    orphaned_context = 0

    # Check metadata (if table exists)
    if 'metadata' in existing_tables:
        cursor.execute("""
            SELECT COUNT(*) FROM metadata
            WHERE contract_id NOT IN (SELECT id FROM contracts)
        """)
        orphaned_metadata = cursor.fetchone()[0]

        if orphaned_metadata > 0:
            print(f"  Found {orphaned_metadata} orphaned metadata records")
            cursor.execute("""
                DELETE FROM metadata
                WHERE contract_id NOT IN (SELECT id FROM contracts)
            """)
            print("  [OK] Cleaned up metadata")

    # Check assessments (if table exists)
    if 'assessments' in existing_tables:
        cursor.execute("""
            SELECT COUNT(*) FROM assessments
            WHERE contract_id NOT IN (SELECT id FROM contracts)
        """)
        orphaned_assessments = cursor.fetchone()[0]

        if orphaned_assessments > 0:
            print(f"  Found {orphaned_assessments} orphaned assessment records")
            cursor.execute("""
                DELETE FROM assessments
                WHERE contract_id NOT IN (SELECT id FROM contracts)
            """)
            print("  [OK] Cleaned up assessments")

    # Check context (if table exists)
    if 'context' in existing_tables:
        cursor.execute("""
            SELECT COUNT(*) FROM context
            WHERE contract_id NOT IN (SELECT id FROM contracts)
        """)
        orphaned_context = cursor.fetchone()[0]

        if orphaned_context > 0:
            print(f"  Found {orphaned_context} orphaned context records")
            cursor.execute("""
                DELETE FROM context
                WHERE contract_id NOT IN (SELECT id FROM contracts)
            """)
            print("  [OK] Cleaned up context")

    if orphaned_metadata == 0 and orphaned_assessments == 0 and orphaned_context == 0:
        print("  [OK] No orphaned records found")

    conn.commit()
    conn.close()
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("CIP Database Maintenance")
    print("=" * 60)
    print()

    start_time = time.time()

    # 1. Check integrity first
    check_integrity()

    # 2. Get current statistics
    get_statistics()

    # 3. Clean orphaned records
    remove_orphaned_records()

    # 4. Add missing indexes
    add_missing_indexes()

    # 5. Analyze for optimization
    analyze_database()

    # 6. Vacuum to reclaim space
    vacuum_database()

    # 7. Final statistics
    print("Final Statistics:")
    get_statistics()

    elapsed = time.time() - start_time
    print(f"Maintenance completed in {elapsed:.2f}s")
    print("=" * 60)
