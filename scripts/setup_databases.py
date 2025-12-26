"""
Database setup script for CIP
Creates contracts.db and reports.db with full schemas
Matches code expectations in api.py and orchestrator.py
"""

import sqlite3
from pathlib import Path

def create_contracts_db():
    """Create contracts.db with schema matching code expectations"""
    db_path = Path(__file__).parent / "contracts.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create contracts table - unified schema matching all code paths
    cursor.execute("""
    CREATE TABLE contracts (
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
    )
    """)

    # Create clauses table
    cursor.execute("""
    CREATE TABLE clauses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        section_number TEXT,
        title TEXT,
        text TEXT NOT NULL,
        category TEXT,
        risk_level TEXT,
        pattern_id TEXT,
        FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """)

    # Create risk_assessments table
    cursor.execute("""
    CREATE TABLE risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        overall_risk TEXT,
        critical_items TEXT,
        dealbreakers TEXT,
        confidence_score REAL,
        analysis_json TEXT,
        FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """)

    # Create negotiations table
    cursor.execute("""
    CREATE TABLE negotiations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        strategy TEXT,
        leverage TEXT,
        position TEXT,
        key_points TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_contracts_type ON contracts(contract_type)")
    cursor.execute("CREATE INDEX idx_contracts_status ON contracts(status)")
    cursor.execute("CREATE INDEX idx_contracts_counterparty ON contracts(counterparty)")
    cursor.execute("CREATE INDEX idx_contracts_risk ON contracts(risk_level)")
    cursor.execute("CREATE INDEX idx_clauses_contract ON clauses(contract_id)")
    cursor.execute("CREATE INDEX idx_clauses_risk ON clauses(risk_level)")
    cursor.execute("CREATE INDEX idx_risk_assessments_contract ON risk_assessments(contract_id)")

    conn.commit()
    conn.close()
    return db_path


def create_reports_db():
    """Create reports.db with schema"""
    db_path = Path(__file__).parent / "reports.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create comparisons table
    cursor.execute("""
    CREATE TABLE comparisons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        v1_contract_id INTEGER NOT NULL,
        v2_contract_id INTEGER NOT NULL,
        comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        substantive_changes INTEGER,
        administrative_changes INTEGER,
        executive_summary TEXT,
        report_path TEXT,
        metadata_json TEXT
    )
    """)

    # Create risk_reports table
    cursor.execute("""
    CREATE TABLE risk_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        report_type TEXT,
        findings TEXT,
        recommendations TEXT,
        report_path TEXT
    )
    """)

    # Create redlines table
    cursor.execute("""
    CREATE TABLE redlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        section_number TEXT,
        original_text TEXT,
        revised_text TEXT,
        rationale TEXT,
        success_probability REAL,
        pattern_id TEXT,
        status TEXT DEFAULT 'proposed'
    )
    """)

    # Create audit_log table
    cursor.execute("""
    CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        action TEXT NOT NULL,
        contract_id INTEGER,
        user TEXT,
        details TEXT
    )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_comparisons_dates ON comparisons(comparison_date)")
    cursor.execute("CREATE INDEX idx_risk_reports_contract ON risk_reports(contract_id)")
    cursor.execute("CREATE INDEX idx_redlines_contract ON redlines(contract_id)")
    cursor.execute("CREATE INDEX idx_audit_timestamp ON audit_log(timestamp)")

    conn.commit()
    conn.close()
    return db_path


def verify_databases():
    """Verify both databases were created correctly"""
    contracts_path = Path(__file__).parent / "contracts.db"
    reports_path = Path(__file__).parent / "reports.db"

    print("\n=== CONTRACTS.DB ===")
    conn = sqlite3.connect(contracts_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")

    cursor.execute("PRAGMA table_info(contracts)")
    cols = cursor.fetchall()
    print(f"Contracts columns ({len(cols)}):")
    for col in cols:
        print(f"  - {col[1]} ({col[2]})")
    conn.close()

    print("\n=== REPORTS.DB ===")
    conn = sqlite3.connect(reports_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    conn.close()


if __name__ == "__main__":
    print("="*50)
    print("CIP DATABASE SETUP")
    print("="*50)

    contracts_db = create_contracts_db()
    print(f"[OK] Created: {contracts_db}")

    reports_db = create_reports_db()
    print(f"[OK] Created: {reports_db}")

    verify_databases()
    print("\n[OK] Database setup complete!")
