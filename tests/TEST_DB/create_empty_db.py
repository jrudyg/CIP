"""
Create Empty CIP Database
Creates a clean database with all tables but 0 contracts.
"""

import sqlite3
from pathlib import Path

# =============================================================================
# DATABASE SCHEMA - All tables from CIP
# =============================================================================

SCHEMA = """
-- Main contracts table
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT,
    title TEXT,
    counterparty TEXT,
    contract_type TEXT,
    contract_role TEXT,
    status TEXT DEFAULT 'intake',
    effective_date TEXT,
    expiration_date TEXT,
    end_date TEXT,
    renewal_date TEXT,
    contract_value REAL,
    parent_id INTEGER,
    relationship_type TEXT,
    version_number INTEGER DEFAULT 1,
    is_latest_version INTEGER DEFAULT 1,
    last_amended_date TEXT,
    risk_level TEXT,
    metadata_verified INTEGER DEFAULT 0,
    parsed_metadata TEXT,
    position TEXT,
    leverage TEXT,
    narrative TEXT,
    parties TEXT,
    metadata_json TEXT,
    upload_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    archived INTEGER DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_contracts_type ON contracts(contract_type);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_counterparty ON contracts(counterparty);
CREATE INDEX IF NOT EXISTS idx_contracts_risk ON contracts(risk_level);
CREATE INDEX IF NOT EXISTS idx_contracts_parent ON contracts(parent_id);

-- Clauses table
CREATE TABLE IF NOT EXISTS clauses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    section_number TEXT,
    title TEXT,
    text TEXT NOT NULL,
    category TEXT,
    risk_level TEXT,
    pattern_id TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_clauses_contract ON clauses(contract_id);
CREATE INDEX IF NOT EXISTS idx_clauses_risk ON clauses(risk_level);

-- Risk assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_risk TEXT,
    critical_items TEXT,
    dealbreakers TEXT,
    confidence_score REAL,
    analysis_json TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_contract ON risk_assessments(contract_id);

-- Negotiations table
CREATE TABLE IF NOT EXISTS negotiations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    strategy TEXT,
    leverage TEXT,
    position TEXT,
    key_points TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_negotiations_contract ON negotiations(contract_id);

-- Analysis snapshots table
CREATE TABLE IF NOT EXISTS analysis_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    overall_risk TEXT NOT NULL,
    categories TEXT NOT NULL,
    clauses TEXT NOT NULL,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_contract_id ON analysis_snapshots(contract_id);

-- Comparison snapshots table
CREATE TABLE IF NOT EXISTS comparison_snapshots (
    comparison_id INTEGER PRIMARY KEY AUTOINCREMENT,
    v1_contract_id INTEGER NOT NULL,
    v2_contract_id INTEGER NOT NULL,
    v1_snapshot_id INTEGER,
    v2_snapshot_id INTEGER,
    similarity_score REAL NOT NULL,
    changed_clauses TEXT NOT NULL,
    risk_delta TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (v1_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (v2_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (v1_snapshot_id) REFERENCES analysis_snapshots(snapshot_id),
    FOREIGN KEY (v2_snapshot_id) REFERENCES analysis_snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_comparison_snapshots_contracts ON comparison_snapshots(v1_contract_id, v2_contract_id);

-- Contract relationships table
CREATE TABLE IF NOT EXISTS contract_relationships (
    contract_id INTEGER PRIMARY KEY,
    parent_id INTEGER,
    children TEXT NOT NULL DEFAULT '[]',
    versions TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (parent_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_contract_relationships_parent ON contract_relationships(parent_id);

-- Redline snapshots table
CREATE TABLE IF NOT EXISTS redline_snapshots (
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
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (base_version_contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_redline_snapshots_contract_id ON redline_snapshots(contract_id);

-- Redlines table
CREATE TABLE IF NOT EXISTS redlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    section_number TEXT,
    original_text TEXT,
    revised_text TEXT,
    rationale TEXT,
    success_probability REAL,
    pattern_id TEXT,
    status TEXT DEFAULT 'proposed',
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_redlines_contract ON redlines(contract_id);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    contract_id INTEGER,
    user TEXT,
    details TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- Comparisons table
CREATE TABLE IF NOT EXISTS comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    v1_contract_id INTEGER NOT NULL,
    v2_contract_id INTEGER NOT NULL,
    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    substantive_changes INTEGER,
    administrative_changes INTEGER,
    executive_summary TEXT,
    report_path TEXT,
    metadata_json TEXT,
    FOREIGN KEY (v1_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (v2_contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_comparisons_dates ON comparisons(comparison_date);

-- Risk reports table
CREATE TABLE IF NOT EXISTS risk_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_type TEXT,
    findings TEXT,
    recommendations TEXT,
    report_path TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_risk_reports_contract ON risk_reports(contract_id);

-- Related documents table
CREATE TABLE IF NOT EXISTS related_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    document_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT,
    description TEXT,
    upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_contract ON related_documents(contract_id);

-- Contract versions table
CREATE TABLE IF NOT EXISTS contract_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    change_summary TEXT,
    changed_by TEXT,
    change_date TEXT DEFAULT CURRENT_TIMESTAMP,
    previous_version_id INTEGER,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (previous_version_id) REFERENCES contract_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_versions_contract ON contract_versions(contract_id);
"""


def create_empty_database(db_path):
    """Create an empty database with all tables."""

    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print(f"Removed existing: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create all tables
    cursor.executescript(SCHEMA)

    conn.commit()

    # Verify tables created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Created: {db_path}")
    print(f"Tables: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")

    conn.close()
    return db_path


def main():
    # Create empty test database
    test_db = Path("C:/Users/jrudy/CIP/tests/TEST_DB/test_contracts.db")
    create_empty_database(test_db)

    # Copy to active locations
    import shutil

    active_paths = [
        Path("C:/Users/jrudy/CIP/data/contracts.db"),
        Path("C:/Users/jrudy/CIP/backend/contracts.db"),
    ]

    print("\nCopying to active locations...")
    for dest in active_paths:
        shutil.copy(test_db, dest)
        print(f"  Copied to: {dest}")

    print("\nDone! All databases are now empty with 0 contracts.")


if __name__ == "__main__":
    main()
