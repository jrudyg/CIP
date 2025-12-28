"""
Migration: Add CASCADE DELETE to remaining foreign key constraints
Date: 2025-12-28
Purpose: Complete CASCADE coverage for all child tables (B5-B7 blockers)

Tables migrated:
- comparison_snapshots (4 FKs: v1_contract_id, v2_contract_id, v1_snapshot_id, v2_snapshot_id)
- redline_snapshots (2 FKs: contract_id, base_version_contract_id)
- audit_log (1 FK: contract_id)
- contract_relationships (2 FKs: contract_id, parent_id)

SQLite requires table recreation to modify FK constraints.
This script safely migrates data while adding ON DELETE CASCADE.
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "data" / "contracts.db"
BACKUP_PATH = DB_PATH.parent / f"contracts_pre_cascade_ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


def migrate():
    """Run the extended CASCADE migration."""
    print("=" * 60)
    print("CASCADE DELETE Extended Migration (B5-B7)")
    print("=" * 60)

    # 1. Create backup
    print(f"\n[1] Creating backup: {BACKUP_PATH.name}")
    shutil.copy(DB_PATH, BACKUP_PATH)
    print("    Backup created")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Disable FK for migration (required for table drops)
    cursor.execute("PRAGMA foreign_keys = OFF")

    # 2. Migrate comparison_snapshots table
    print("\n[2] Migrating comparison_snapshots table...")
    cursor.execute("""
        CREATE TABLE comparison_snapshots_new (
            comparison_id INTEGER PRIMARY KEY AUTOINCREMENT,
            v1_contract_id INTEGER NOT NULL,
            v2_contract_id INTEGER NOT NULL,
            v1_snapshot_id INTEGER,
            v2_snapshot_id INTEGER,
            similarity_score REAL NOT NULL,
            changed_clauses TEXT NOT NULL,
            risk_delta TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            comparison_hash TEXT,
            result_json TEXT,
            FOREIGN KEY (v1_contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (v2_contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (v1_snapshot_id) REFERENCES analysis_snapshots(snapshot_id) ON DELETE CASCADE,
            FOREIGN KEY (v2_snapshot_id) REFERENCES analysis_snapshots(snapshot_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO comparison_snapshots_new
        SELECT comparison_id, v1_contract_id, v2_contract_id, v1_snapshot_id, v2_snapshot_id,
               similarity_score, changed_clauses, risk_delta, created_at, comparison_hash, result_json
        FROM comparison_snapshots
    """)
    cursor.execute("DROP TABLE comparison_snapshots")
    cursor.execute("ALTER TABLE comparison_snapshots_new RENAME TO comparison_snapshots")
    print("    comparison_snapshots: CASCADE added (4 FKs)")

    # 3. Migrate redline_snapshots table
    print("\n[3] Migrating redline_snapshots table...")
    cursor.execute("""
        CREATE TABLE redline_snapshots_new (
            redline_id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            base_version_contract_id INTEGER NOT NULL,
            source_mode TEXT NOT NULL,
            created_at TEXT NOT NULL,
            overall_risk_before TEXT NOT NULL,
            overall_risk_after TEXT,
            clauses_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            contract_position TEXT,
            dealbreakers_detected INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (base_version_contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO redline_snapshots_new
        SELECT redline_id, contract_id, base_version_contract_id, source_mode, created_at,
               overall_risk_before, overall_risk_after, clauses_json, status, contract_position,
               dealbreakers_detected
        FROM redline_snapshots
    """)
    cursor.execute("DROP TABLE redline_snapshots")
    cursor.execute("ALTER TABLE redline_snapshots_new RENAME TO redline_snapshots")
    print("    redline_snapshots: CASCADE added (2 FKs)")

    # 4. Migrate audit_log table
    print("\n[4] Migrating audit_log table...")
    cursor.execute("""
        CREATE TABLE audit_log_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            contract_id INTEGER,
            user TEXT,
            details TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO audit_log_new
        SELECT id, timestamp, action, contract_id, user, details
        FROM audit_log
    """)
    cursor.execute("DROP TABLE audit_log")
    cursor.execute("ALTER TABLE audit_log_new RENAME TO audit_log")
    print("    audit_log: CASCADE added (1 FK)")

    # 5. Migrate contract_relationships table
    print("\n[5] Migrating contract_relationships table...")
    cursor.execute("""
        CREATE TABLE contract_relationships_new (
            contract_id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            children TEXT NOT NULL DEFAULT '[]',
            versions TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        INSERT INTO contract_relationships_new
        SELECT contract_id, parent_id, children, versions
        FROM contract_relationships
    """)
    cursor.execute("DROP TABLE contract_relationships")
    cursor.execute("ALTER TABLE contract_relationships_new RENAME TO contract_relationships")
    print("    contract_relationships: CASCADE added (2 FKs)")

    # 6. Recreate indexes
    print("\n[6] Recreating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparison_snapshots_contracts ON comparison_snapshots(v1_contract_id, v2_contract_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparison_hash ON comparison_snapshots(comparison_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_redline_snapshots_contract_id ON redline_snapshots(contract_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contract_relationships_parent ON contract_relationships(parent_id)")
    print("    5 indexes recreated")

    conn.commit()

    # 7. Verify
    print("\n[7] Verification...")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    if violations:
        print(f"    WARNING: {len(violations)} FK violations found")
        for v in violations[:5]:
            print(f"      {v}")
    else:
        print("    No FK violations")

    cursor.execute("PRAGMA integrity_check")
    integrity = cursor.fetchone()[0]
    print(f"    Integrity check: {integrity}")

    # 8. Show all CASCADE status
    print("\n[8] Final CASCADE status (all tables):")
    tables = ['clauses', 'risk_assessments', 'analysis_snapshots',
              'comparison_snapshots', 'redline_snapshots', 'audit_log', 'contract_relationships']
    for table in tables:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        sql = cursor.fetchone()[0]
        has_cascade = "CASCADE" in sql.upper()
        print(f"    {table}: CASCADE={'YES' if has_cascade else 'NO'}")

    conn.close()

    print("\n" + "=" * 60)
    print("Extended CASCADE migration complete!")
    print(f"Backup saved to: {BACKUP_PATH.name}")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
