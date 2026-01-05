"""
Verify that intake_engine.py INSERT statements satisfy all NOT NULL constraints.
"""

import sqlite3
from pathlib import Path
import re

db_path = Path(__file__).parent.parent / "data" / "contracts.db"
engine_path = Path(__file__).parent / "intake_engine.py"

print("=" * 70)
print("NOT NULL CONSTRAINT VERIFICATION")
print("=" * 70)
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ============================================================
# Check CONTRACTS table
# ============================================================
print("CONTRACTS TABLE - NOT NULL columns:")
print("-" * 70)

cursor.execute("PRAGMA table_info(contracts);")
contracts_cols = cursor.fetchall()
contracts_not_null = [col for col in contracts_cols if col[3] == 1]  # notnull flag

print(f"Total columns: {len(contracts_cols)}")
print(f"NOT NULL columns: {len(contracts_not_null)}")
print()

for col in contracts_not_null:
    col_name = col[1]
    col_type = col[2]
    print(f"  - {col_name:30s} {col_type}")

# Read INSERT statement from intake_engine.py
with open(engine_path, 'r', encoding='utf-8') as f:
    engine_content = f.read()

# Find contracts INSERT
contracts_insert_match = re.search(
    r'INSERT INTO contracts \((.*?)\) VALUES',
    engine_content,
    re.DOTALL
)

if contracts_insert_match:
    contracts_insert_cols = contracts_insert_match.group(1)
    # Extract column names
    contracts_insert_cols_list = [
        col.strip() for col in re.findall(r'\b\w+\b', contracts_insert_cols)
        if col.strip() and col.strip().upper() not in ('INSERT', 'INTO', 'CONTRACTS')
    ]

    print()
    print("Columns in INSERT statement:")
    for col in contracts_insert_cols_list:
        print(f"  - {col}")

    print()
    print("NOT NULL constraint check:")
    all_satisfied = True
    for col in contracts_not_null:
        col_name = col[1]
        if col_name == 'id':  # Auto-increment, skip
            print(f"  [OK] {col_name:30s} (auto-increment)")
        elif col_name in contracts_insert_cols_list:
            print(f"  [OK] {col_name:30s} (populated)")
        else:
            print(f"  [!!] {col_name:30s} (MISSING FROM INSERT!)")
            all_satisfied = False

    if all_satisfied:
        print("\n[OK] All NOT NULL constraints satisfied for contracts")
    else:
        print("\n[!!] Some NOT NULL constraints NOT satisfied!")

# ============================================================
# Check CLAUSES table
# ============================================================
print()
print("=" * 70)
print("CLAUSES TABLE - NOT NULL columns:")
print("-" * 70)

cursor.execute("PRAGMA table_info(clauses);")
clauses_cols = cursor.fetchall()
clauses_not_null = [col for col in clauses_cols if col[3] == 1]  # notnull flag

print(f"Total columns: {len(clauses_cols)}")
print(f"NOT NULL columns: {len(clauses_not_null)}")
print()

for col in clauses_not_null:
    col_name = col[1]
    col_type = col[2]
    print(f"  - {col_name:30s} {col_type}")

# Find clauses INSERT
clauses_insert_match = re.search(
    r'INSERT INTO clauses \((.*?)\) VALUES',
    engine_content,
    re.DOTALL
)

if clauses_insert_match:
    clauses_insert_cols = clauses_insert_match.group(1)
    # Extract column names
    clauses_insert_cols_list = [
        col.strip() for col in re.findall(r'\b\w+\b', clauses_insert_cols)
        if col.strip() and col.strip().upper() not in ('INSERT', 'INTO', 'CLAUSES')
    ]

    print()
    print("Columns in INSERT statement:")
    for col in clauses_insert_cols_list:
        print(f"  - {col}")

    print()
    print("NOT NULL constraint check:")
    all_satisfied = True
    for col in clauses_not_null:
        col_name = col[1]
        if col_name == 'id':  # Auto-increment, skip
            print(f"  [OK] {col_name:30s} (auto-increment)")
        elif col_name in clauses_insert_cols_list:
            print(f"  [OK] {col_name:30s} (populated)")
        else:
            print(f"  [!!] {col_name:30s} (MISSING FROM INSERT!)")
            all_satisfied = False

    if all_satisfied:
        print("\n[OK] All NOT NULL constraints satisfied for clauses")
    else:
        print("\n[!!] Some NOT NULL constraints NOT satisfied!")

conn.close()

print()
print("=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
