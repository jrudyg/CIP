"""
Migration: Add CASCADE DELETE to foreign key constraints
Date: 2025-12-27
Purpose: Ensure child records are deleted when parent contracts are deleted

SQLite requires table recreation to modify FK constraints.
This script safely migrates data while adding ON DELETE CASCADE.
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "data" / "contracts.db"
BACKUP_PATH = DB_PATH.parent / f"contracts_pre_cascade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


def migrate():
    """Run the CASCADE migration."""
    print("=" * 60)
    print("CASCADE DELETE Migration")
    print("=" * 60)

    # 1. Create backup
    print(f"\n[1] Creating backup: {BACKUP_PATH.name}")
    shutil.copy(DB_PATH, BACKUP_PATH)
    print("    Backup created")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Enable FK for this session
    cursor.execute("PRAGMA foreign_keys = OFF")

    # 2. Migrate clauses table
    print("\n[2] Migrating clauses table...")
    cursor.execute("""
        CREATE TABLE clauses_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            section_number TEXT,
            title TEXT,
            text TEXT NOT NULL,
            category TEXT,
            risk_level TEXT,
            pattern_id TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO clauses_new SELECT * FROM clauses
    """)
    cursor.execute("DROP TABLE clauses")
    cursor.execute("ALTER TABLE clauses_new RENAME TO clauses")
    print("    clauses: CASCADE added")

    # 3. Migrate risk_assessments table
    print("\n[3] Migrating risk_assessments table...")
    cursor.execute("""
        CREATE TABLE risk_assessments_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            overall_risk TEXT,
            critical_items TEXT,
            dealbreakers TEXT,
            confidence_score REAL,
            analysis_json TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO risk_assessments_new SELECT * FROM risk_assessments
    """)
    cursor.execute("DROP TABLE risk_assessments")
    cursor.execute("ALTER TABLE risk_assessments_new RENAME TO risk_assessments")
    print("    risk_assessments: CASCADE added")

    # 4. Migrate analysis_snapshots table
    print("\n[4] Migrating analysis_snapshots table...")
    cursor.execute("""
        CREATE TABLE analysis_snapshots_new (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            overall_risk TEXT NOT NULL,
            categories TEXT NOT NULL,
            clauses TEXT NOT NULL,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO analysis_snapshots_new SELECT * FROM analysis_snapshots
    """)
    cursor.execute("DROP TABLE analysis_snapshots")
    cursor.execute("ALTER TABLE analysis_snapshots_new RENAME TO analysis_snapshots")
    print("    analysis_snapshots: CASCADE added")

    # 5. Recreate indexes
    print("\n[5] Recreating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clauses_contract ON clauses(contract_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_assessments_contract ON risk_assessments(contract_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_contract ON analysis_snapshots(contract_id)")
    print("    Indexes created")

    conn.commit()

    # 6. Verify
    print("\n[6] Verification...")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    if violations:
        print(f"    WARNING: {len(violations)} FK violations found")
    else:
        print("    No FK violations")

    cursor.execute("PRAGMA integrity_check")
    integrity = cursor.fetchone()[0]
    print(f"    Integrity check: {integrity}")

    # Show new schemas
    print("\n[7] New schemas (with CASCADE):")
    for table in ['clauses', 'risk_assessments', 'analysis_snapshots']:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        sql = cursor.fetchone()[0]
        has_cascade = "CASCADE" in sql.upper()
        print(f"    {table}: CASCADE={'YES' if has_cascade else 'NO'}")

    conn.close()

    print("\n" + "=" * 60)
    print("Migration complete!")
    print(f"Backup saved to: {BACKUP_PATH.name}")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
