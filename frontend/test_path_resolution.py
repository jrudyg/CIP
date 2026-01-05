"""Test path resolution for intake page database path"""
from pathlib import Path

# Simulate the path resolution from 3_Intelligent_Intake.py
simulated_file = Path(r"C:\Users\jrudy\CIP\frontend\pages\3_Intelligent_Intake.py")

print("Path Resolution Test")
print("=" * 60)
print(f"__file__ (simulated): {simulated_file}")
print()

# Line 16 logic
backend_path = simulated_file.parent.parent.parent / "backend"
print(f"backend_path = Path(__file__).parent.parent.parent / 'backend'")
print(f"  Step 1 - .parent:               {simulated_file.parent}")
print(f"  Step 2 - .parent.parent:        {simulated_file.parent.parent}")
print(f"  Step 3 - .parent.parent.parent: {simulated_file.parent.parent.parent}")
print(f"  Final backend_path:             {backend_path}")
print()

# Line 72 logic
db_path = str(backend_path.parent / "data" / "contracts.db")
print(f"db_path = str(backend_path.parent / 'data' / 'contracts.db')")
print(f"  Step 1 - backend_path.parent:   {backend_path.parent}")
print(f"  Final db_path:                  {db_path}")
print()

# Check if database exists
import os
db_exists = os.path.exists(db_path)
print(f"Database exists: {db_exists}")

if db_exists:
    # Check column count
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(contracts);")
    cols = cursor.fetchall()
    conn.close()

    print(f"Contracts table columns: {len(cols)}")

    # Check for currency column
    currency_col = [col for col in cols if col[1] == 'currency']
    if currency_col:
        print(f"Currency column: EXISTS at position {currency_col[0][0] + 1}")
    else:
        print(f"Currency column: NOT FOUND")
else:
    print("ERROR: Database not found at expected path!")
