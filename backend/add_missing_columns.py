"""
Add missing intake schema columns to contracts table.
Runs all ALTER TABLE commands, ignoring errors for columns that already exist.
"""

import sqlite3
from pathlib import Path

# Database path
db_path = Path(__file__).parent.parent / "data" / "contracts.db"

# Columns to add
columns_to_add = [
    "currency VARCHAR(3) DEFAULT 'USD'",
    "contract_value DECIMAL(15,2)",
    "party_client VARCHAR(200)",
    "party_vendor VARCHAR(200)",
    "effective_date DATE",
    "expiration_date DATE",
    "governing_law VARCHAR(50)",
    "vendor_ticker VARCHAR(10)",
    "vendor_cik VARCHAR(20)",
    "document_hash VARCHAR(64)",
    "intake_risk_summary TEXT",
    "intake_completed_at TIMESTAMP"
]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding missing intake schema columns...")
print(f"Database: {db_path}")
print("-" * 60)

added_count = 0
exists_count = 0

for col_def in columns_to_add:
    col_name = col_def.split()[0]
    sql = f"ALTER TABLE contracts ADD COLUMN {col_def};"

    try:
        cursor.execute(sql)
        conn.commit()
        print(f"[+] Added: {col_name}")
        added_count += 1
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"[=] Exists: {col_name}")
            exists_count += 1
        else:
            print(f"[X] Error: {col_name} - {e}")

conn.close()

print("-" * 60)
print(f"Summary: {added_count} added, {exists_count} already exist")
print("\nVerifying currency column...")

# Verify currency column
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(contracts);")
columns = cursor.fetchall()
conn.close()

currency_exists = any(col[1] == 'currency' for col in columns)
if currency_exists:
    print("[OK] Currency column verified in schema")
else:
    print("[!!] Currency column NOT FOUND")

print(f"\nTotal columns in contracts table: {len(columns)}")
