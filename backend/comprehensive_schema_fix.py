"""
Comprehensive schema fix for CIP database.
Adds ALL columns that intake_engine.py expects.
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "contracts.db"

print("=" * 70)
print("COMPREHENSIVE SCHEMA FIX")
print("=" * 70)
print(f"Database: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Track results
added_contracts = []
added_clauses = []
existing_contracts = []
existing_clauses = []
tables_created = []

# ============================================================
# CONTRACTS TABLE - Add all missing columns
# ============================================================
print("CONTRACTS TABLE - Adding missing columns...")
print("-" * 70)

contracts_columns = [
    "filepath TEXT",
    "document_hash VARCHAR(64)",
    "clause_count INTEGER DEFAULT 0",
    "party_client VARCHAR(200)",
    "party_vendor VARCHAR(200)",
    "effective_date DATE",
    "expiration_date DATE",
    "contract_value DECIMAL(15,2)",
    "currency VARCHAR(3) DEFAULT 'USD'",
    "governing_law VARCHAR(50)",
    "vendor_ticker VARCHAR(10)",
    "vendor_cik VARCHAR(20)",
    "intake_status VARCHAR(20) DEFAULT 'PENDING'",
    "intake_completed_at TIMESTAMP",
    "intake_risk_summary TEXT",
    "risk_status VARCHAR(20) DEFAULT 'BLOCKED'",
    "redline_status VARCHAR(20) DEFAULT 'BLOCKED'",
    "compare_status VARCHAR(20) DEFAULT 'BLOCKED'"
]

for col_def in contracts_columns:
    col_name = col_def.split()[0]
    sql = f"ALTER TABLE contracts ADD COLUMN {col_def};"

    try:
        cursor.execute(sql)
        conn.commit()
        print(f"[+] Added: {col_name}")
        added_contracts.append(col_name)
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"[=] Exists: {col_name}")
            existing_contracts.append(col_name)
        else:
            print(f"[X] Error: {col_name} - {e}")

# ============================================================
# CLAUSES TABLE - Add all missing columns
# ============================================================
print("\nCLAUSES TABLE - Adding missing columns...")
print("-" * 70)

clauses_columns = [
    "section_number VARCHAR(20)",
    "section_title VARCHAR(200)",
    "clause_type VARCHAR(50)",
    "verbatim_text TEXT",
    "word_count INTEGER DEFAULT 0",
    "cce_risk_score DECIMAL(3,1)",
    "cce_risk_level VARCHAR(10)",
    "cce_statutory_flag VARCHAR(20)",
    "cce_cascade_risk BOOLEAN DEFAULT 0",
    "embedding_id VARCHAR(64)",
    "chunk_hash VARCHAR(64)"
]

for col_def in clauses_columns:
    col_name = col_def.split()[0]
    sql = f"ALTER TABLE clauses ADD COLUMN {col_def};"

    try:
        cursor.execute(sql)
        conn.commit()
        print(f"[+] Added: {col_name}")
        added_clauses.append(col_name)
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"[=] Exists: {col_name}")
            existing_clauses.append(col_name)
        else:
            print(f"[X] Error: {col_name} - {e}")

# ============================================================
# ANNOTATIONS TABLE - Create if not exists
# ============================================================
print("\nANNOTATIONS TABLE - Creating if not exists...")
print("-" * 70)

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            clause_id INTEGER,
            annotation_type VARCHAR(20) NOT NULL,
            severity VARCHAR(10),
            title VARCHAR(200),
            content TEXT NOT NULL,
            source VARCHAR(50) DEFAULT 'INTAKE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (clause_id) REFERENCES clauses(id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    # Check if table was just created or already existed
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='annotations'")
    if cursor.fetchone()[0] > 0:
        # Check if it was just created by seeing if it's empty
        cursor.execute("SELECT COUNT(*) FROM annotations")
        count = cursor.fetchone()[0]
        if count == 0:
            print("[+] Created: annotations table (empty)")
            tables_created.append("annotations")
        else:
            print(f"[=] Exists: annotations table ({count} rows)")
except Exception as e:
    print(f"[X] Error creating annotations: {e}")

# ============================================================
# AUDIT_TRAIL TABLE - Create if not exists
# ============================================================
print("\nAUDIT_TRAIL TABLE - Creating if not exists...")
print("-" * 70)

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id VARCHAR(50) NOT NULL UNIQUE,
            report_type VARCHAR(30) NOT NULL,
            contract_id INTEGER,
            v1_contract_id INTEGER,
            v2_contract_id INTEGER,
            input_hash VARCHAR(64) NOT NULL,
            system_version VARCHAR(20) NOT NULL,
            risk_scorer_version VARCHAR(20) NOT NULL,
            ucc_logic_version VARCHAR(20) NOT NULL,
            prompt_name VARCHAR(50) NOT NULL,
            prompt_version VARCHAR(20) NOT NULL,
            prompt_hash VARCHAR(64) NOT NULL,
            template_name VARCHAR(50) NOT NULL,
            template_version VARCHAR(20) NOT NULL,
            template_hash VARCHAR(64) NOT NULL,
            output_hash VARCHAR(64) NOT NULL,
            output_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(50),
            last_verified_at TIMESTAMP,
            last_verified_by VARCHAR(50),
            verification_status VARCHAR(20) DEFAULT 'UNVERIFIED',
            verification_notes TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (v1_contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY (v2_contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='audit_trail'")
    if cursor.fetchone()[0] > 0:
        cursor.execute("SELECT COUNT(*) FROM audit_trail")
        count = cursor.fetchone()[0]
        print(f"[=] Exists: audit_trail table ({count} rows)")
except Exception as e:
    print(f"[X] Error creating audit_trail: {e}")

# ============================================================
# PUBLIC_COMPANIES TABLE - Create if not exists
# ============================================================
print("\nPUBLIC_COMPANIES TABLE - Creating if not exists...")
print("-" * 70)

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name VARCHAR(200) NOT NULL,
            ticker VARCHAR(10),
            cik VARCHAR(20),
            exchange VARCHAR(20),
            sector VARCHAR(100),
            aliases TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker),
            UNIQUE(cik)
        )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='public_companies'")
    if cursor.fetchone()[0] > 0:
        cursor.execute("SELECT COUNT(*) FROM public_companies")
        count = cursor.fetchone()[0]
        if count == 0:
            print("[+] Created: public_companies table (empty)")
            tables_created.append("public_companies")
        else:
            print(f"[=] Exists: public_companies table ({count} rows)")
except Exception as e:
    print(f"[X] Error creating public_companies: {e}")

# ============================================================
# VERIFY FINAL SCHEMA
# ============================================================
print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

# Count columns
cursor.execute("PRAGMA table_info(contracts)")
contracts_cols = cursor.fetchall()
print(f"Contracts table columns: {len(contracts_cols)}")

cursor.execute("PRAGMA table_info(clauses)")
clauses_cols = cursor.fetchall()
print(f"Clauses table columns: {len(clauses_cols)}")

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables present: {', '.join(tables)}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if added_contracts:
    print(f"\nContacts columns ADDED ({len(added_contracts)}):")
    for col in added_contracts:
        print(f"  - {col}")
else:
    print(f"\nContracts: All {len(existing_contracts)} columns already existed")

if added_clauses:
    print(f"\nClauses columns ADDED ({len(added_clauses)}):")
    for col in added_clauses:
        print(f"  - {col}")
else:
    print(f"\nClauses: All {len(existing_clauses)} columns already existed")

if tables_created:
    print(f"\nTables CREATED ({len(tables_created)}):")
    for table in tables_created:
        print(f"  - {table}")

# Verify critical columns
print("\n" + "=" * 70)
print("CRITICAL COLUMNS CHECK")
print("=" * 70)

critical_checks = [
    ('contracts', 'filename'),
    ('contracts', 'filepath'),
    ('contracts', 'document_hash'),
    ('contracts', 'currency'),
    ('contracts', 'intake_status'),
    ('clauses', 'section_number'),
    ('clauses', 'verbatim_text'),
    ('clauses', 'cce_risk_score'),
    ('clauses', 'cce_risk_level')
]

all_good = True
for table, col in critical_checks:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall()]
    exists = col in cols
    status = "[OK]" if exists else "[!!]"
    print(f"{status} {table}.{col}")
    if not exists:
        all_good = False

conn.close()

print("\n" + "=" * 70)
if all_good:
    print("READY FOR RETEST: YES")
else:
    print("READY FOR RETEST: NO - Missing critical columns!")
print("=" * 70)
