"""
CIP Test Database Verification Script
Validates database integrity, relationships, and data quality.
"""

import sqlite3
from pathlib import Path
import json


def verify_database(db_path):
    """Run comprehensive verification on the test database."""

    print("="*70)
    print("CIP TEST DATABASE VERIFICATION")
    print("="*70)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    errors = []
    warnings = []

    # =========================================================================
    # 1. TABLE EXISTENCE CHECK
    # =========================================================================
    print("\n[1] Checking table existence...")

    expected_tables = [
        "contracts", "clauses", "risk_assessments", "negotiations",
        "analysis_snapshots", "comparison_snapshots", "contract_relationships",
        "redline_snapshots", "redlines", "audit_log", "comparisons",
        "risk_reports", "related_documents", "contract_versions"
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    actual_tables = [row[0] for row in cursor.fetchall()]

    for table in expected_tables:
        if table in actual_tables:
            print(f"  [OK] {table}")
        else:
            errors.append(f"Missing table: {table}")
            print(f"  [FAIL] {table} - MISSING")

    # =========================================================================
    # 2. DATA COUNT VERIFICATION
    # =========================================================================
    print("\n[2] Verifying data counts...")

    min_counts = {
        "contracts": 100,
        "clauses": 500,
        "risk_assessments": 100,
        "analysis_snapshots": 100,
        "audit_log": 300,
    }

    for table, min_count in min_counts.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count >= min_count:
            print(f"  [OK] {table}: {count} rows (min: {min_count})")
        else:
            warnings.append(f"{table} has only {count} rows (expected >= {min_count})")
            print(f"  [WARN] {table}: {count} rows (expected >= {min_count})")

    # =========================================================================
    # 3. CONTRACT TYPE DISTRIBUTION
    # =========================================================================
    print("\n[3] Checking contract type distribution...")

    expected_types = ["NDA", "MNDA", "MSA", "SOW", "SLA", "MOU", "LOI",
                      "AMENDMENT", "ADDENDUM", "ORDER", "LICENSE", "LEASE",
                      "EMPLOYMENT", "OTHER"]

    cursor.execute("SELECT DISTINCT contract_type FROM contracts")
    actual_types = [row[0] for row in cursor.fetchall()]

    missing_types = set(expected_types) - set(actual_types)
    if missing_types:
        warnings.append(f"Missing contract types: {missing_types}")
        print(f"  [WARN] Missing types: {missing_types}")
    else:
        print(f"  [OK] All {len(expected_types)} contract types present")

    cursor.execute("""
        SELECT contract_type, COUNT(*)
        FROM contracts
        GROUP BY contract_type
        ORDER BY COUNT(*) DESC
    """)
    print("  Distribution:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}: {row[1]}")

    # =========================================================================
    # 4. PARTY RELATIONSHIP DISTRIBUTION
    # =========================================================================
    print("\n[4] Checking party relationship distribution...")

    expected_roles = ["CUSTOMER", "VENDOR", "PARTNER", "RESELLER", "CONSULTANT"]

    cursor.execute("SELECT DISTINCT contract_role FROM contracts")
    actual_roles = [row[0] for row in cursor.fetchall()]

    missing_roles = set(expected_roles) - set(actual_roles)
    if missing_roles:
        warnings.append(f"Missing party relationships: {missing_roles}")
        print(f"  [WARN] Missing roles: {missing_roles}")
    else:
        print(f"  [OK] All {len(expected_roles)} party relationships present")

    # =========================================================================
    # 5. STATUS DISTRIBUTION
    # =========================================================================
    print("\n[5] Checking CLM status distribution...")

    expected_statuses = ["NEW CONTRACT", "REVIEWING", "NEGOTIATING", "APPROVING",
                         "EXECUTING", "IN_EFFECT", "AMENDING", "RENEWAL", "EXPIRED"]

    cursor.execute("SELECT DISTINCT status FROM contracts")
    actual_statuses = [row[0] for row in cursor.fetchall()]

    missing_statuses = set(expected_statuses) - set(actual_statuses)
    if missing_statuses:
        warnings.append(f"Missing statuses: {missing_statuses}")
        print(f"  [WARN] Missing statuses: {missing_statuses}")
    else:
        print(f"  [OK] All {len(expected_statuses)} CLM stages present")

    # =========================================================================
    # 6. RISK LEVEL DISTRIBUTION
    # =========================================================================
    print("\n[6] Checking risk level distribution...")

    expected_risks = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "DEALBREAKER"]

    cursor.execute("SELECT DISTINCT risk_level FROM contracts")
    actual_risks = [row[0] for row in cursor.fetchall()]

    missing_risks = set(expected_risks) - set(actual_risks)
    if missing_risks:
        warnings.append(f"Missing risk levels: {missing_risks}")
        print(f"  [WARN] Missing risk levels: {missing_risks}")
    else:
        print(f"  [OK] All {len(expected_risks)} risk levels present")

    cursor.execute("""
        SELECT risk_level, COUNT(*)
        FROM contracts
        GROUP BY risk_level
        ORDER BY COUNT(*) DESC
    """)
    print("  Distribution:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}: {row[1]}")

    # =========================================================================
    # 7. FOREIGN KEY RELATIONSHIPS
    # =========================================================================
    print("\n[7] Verifying foreign key relationships...")

    # Check clauses -> contracts
    cursor.execute("""
        SELECT COUNT(*) FROM clauses c
        LEFT JOIN contracts ct ON c.contract_id = ct.id
        WHERE ct.id IS NULL
    """)
    orphan_clauses = cursor.fetchone()[0]
    if orphan_clauses > 0:
        errors.append(f"Found {orphan_clauses} orphan clauses")
        print(f"  [FAIL] {orphan_clauses} clauses without valid contract")
    else:
        print("  [OK] All clauses linked to valid contracts")

    # Check risk_assessments -> contracts
    cursor.execute("""
        SELECT COUNT(*) FROM risk_assessments r
        LEFT JOIN contracts ct ON r.contract_id = ct.id
        WHERE ct.id IS NULL
    """)
    orphan_assessments = cursor.fetchone()[0]
    if orphan_assessments > 0:
        errors.append(f"Found {orphan_assessments} orphan risk assessments")
        print(f"  [FAIL] {orphan_assessments} assessments without valid contract")
    else:
        print("  [OK] All risk assessments linked to valid contracts")

    # Check parent_id references
    cursor.execute("""
        SELECT COUNT(*) FROM contracts c
        WHERE c.parent_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM contracts p WHERE p.id = c.parent_id)
    """)
    invalid_parents = cursor.fetchone()[0]
    if invalid_parents > 0:
        errors.append(f"Found {invalid_parents} contracts with invalid parent_id")
        print(f"  [FAIL] {invalid_parents} contracts with invalid parent reference")
    else:
        print("  [OK] All parent references are valid")

    # =========================================================================
    # 8. VERSION TRACKING
    # =========================================================================
    print("\n[8] Checking version tracking...")

    cursor.execute("SELECT COUNT(*) FROM contracts WHERE version_number > 1")
    versioned = cursor.fetchone()[0]
    print(f"  Contracts with version > 1: {versioned}")

    cursor.execute("SELECT COUNT(*) FROM contract_versions")
    version_records = cursor.fetchone()[0]
    print(f"  Version history records: {version_records}")

    if version_records == 0:
        warnings.append("No version history records found")
    else:
        print("  [OK] Version tracking present")

    # =========================================================================
    # 9. RELATED DOCUMENTS
    # =========================================================================
    print("\n[9] Checking related documents...")

    cursor.execute("SELECT COUNT(DISTINCT contract_id) FROM related_documents")
    contracts_with_docs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM related_documents")
    total_docs = cursor.fetchone()[0]

    print(f"  Contracts with documents: {contracts_with_docs}")
    print(f"  Total related documents: {total_docs}")

    if contracts_with_docs > 0:
        print("  [OK] Related documents present")
    else:
        warnings.append("No related documents found")

    # =========================================================================
    # 10. PARENT-CHILD RELATIONSHIPS
    # =========================================================================
    print("\n[10] Checking parent-child relationships...")

    cursor.execute("SELECT COUNT(*) FROM contracts WHERE parent_id IS NOT NULL")
    children = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT parent_id) FROM contracts WHERE parent_id IS NOT NULL")
    parents = cursor.fetchone()[0]

    print(f"  Parent contracts: {parents}")
    print(f"  Child contracts: {children}")

    # Check SOWs with MSA parents
    cursor.execute("""
        SELECT COUNT(*) FROM contracts c
        JOIN contracts p ON c.parent_id = p.id
        WHERE c.contract_type = 'SOW' AND p.contract_type = 'MSA'
    """)
    sow_msa = cursor.fetchone()[0]
    print(f"  SOWs linked to MSAs: {sow_msa}")

    if children > 0:
        print("  [OK] Parent-child relationships present")
    else:
        warnings.append("No parent-child relationships found")

    # =========================================================================
    # 11. JSON FIELD VALIDATION
    # =========================================================================
    print("\n[11] Validating JSON fields...")

    # Check parties JSON
    cursor.execute("SELECT id, parties FROM contracts WHERE parties IS NOT NULL LIMIT 5")
    json_valid = True
    for row in cursor.fetchall():
        try:
            data = json.loads(row[1])
            if not isinstance(data, dict):
                json_valid = False
        except json.JSONDecodeError:
            json_valid = False
            errors.append(f"Invalid JSON in contracts.parties for id {row[0]}")

    if json_valid:
        print("  [OK] parties JSON fields valid")
    else:
        print("  [FAIL] Invalid JSON in parties fields")

    # Check metadata_json
    cursor.execute("SELECT id, metadata_json FROM contracts WHERE metadata_json IS NOT NULL LIMIT 5")
    json_valid = True
    for row in cursor.fetchall():
        try:
            data = json.loads(row[1])
            if not isinstance(data, dict):
                json_valid = False
        except json.JSONDecodeError:
            json_valid = False
            errors.append(f"Invalid JSON in contracts.metadata_json for id {row[0]}")

    if json_valid:
        print("  [OK] metadata_json fields valid")
    else:
        print("  [FAIL] Invalid JSON in metadata_json fields")

    # =========================================================================
    # 12. INDEX VERIFICATION
    # =========================================================================
    print("\n[12] Checking indexes...")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    indexes = [row[0] for row in cursor.fetchall()]

    expected_indexes = [
        "idx_contracts_type", "idx_contracts_status", "idx_contracts_counterparty",
        "idx_contracts_risk", "idx_contracts_parent", "idx_clauses_contract",
        "idx_clauses_risk", "idx_risk_assessments_contract"
    ]

    missing_indexes = []
    for idx in expected_indexes:
        if idx not in indexes:
            missing_indexes.append(idx)

    if missing_indexes:
        warnings.append(f"Missing indexes: {missing_indexes}")
        print(f"  [WARN] Missing indexes: {missing_indexes}")
    else:
        print(f"  [OK] All {len(expected_indexes)} core indexes present")
    print(f"  Total indexes: {len(indexes)}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  - {warn}")

    if not errors and not warnings:
        print("\nAll checks passed successfully!")
    elif not errors:
        print(f"\nVerification complete with {len(warnings)} warnings")
    else:
        print(f"\nVerification FAILED with {len(errors)} errors and {len(warnings)} warnings")

    conn.close()

    return len(errors) == 0


def main():
    db_path = Path("C:/Users/jrudy/CIP/tests/TEST_DB/test_contracts.db")

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return False

    return verify_database(str(db_path))


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
