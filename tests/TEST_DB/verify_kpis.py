"""
Verify Test Database KPI Alignment
Checks that the database has proper data for all dashboard KPIs.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def verify_kpis(db_path):
    """Verify database meets KPI requirements."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    ninety_days_str = (today + timedelta(days=90)).strftime("%Y-%m-%d")
    ninety_ago_str = (today - timedelta(days=90)).strftime("%Y-%m-%d")

    print("="*70)
    print("KPI VERIFICATION REPORT")
    print("="*70)
    print(f"Database: {db_path}")
    print(f"Date: {today_str}")

    issues = []

    # =========================================================================
    # 1. PORTFOLIO METRICS
    # =========================================================================
    print("\n" + "-"*70)
    print("1. PORTFOLIO METRICS (Active Contracts)")
    print("-"*70)

    # Total portfolio
    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE status NOT IN ('archived', 'expired', 'terminated')
    """)
    portfolio_total = cursor.fetchone()[0]
    print(f"  Total Active Portfolio: {portfolio_total}")

    if portfolio_total < 50:
        issues.append(f"Low portfolio count: {portfolio_total} (expected 50+)")

    # By role
    cursor.execute("""
        SELECT contract_role, COUNT(*) FROM contracts
        WHERE status NOT IN ('archived', 'expired', 'terminated')
        GROUP BY contract_role
    """)
    print("  By Role:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # Portfolio value
    cursor.execute("""
        SELECT SUM(contract_value) FROM contracts
        WHERE status NOT IN ('archived', 'expired', 'terminated')
        AND contract_value IS NOT NULL
    """)
    portfolio_value = cursor.fetchone()[0] or 0
    print(f"  Portfolio Value: ${portfolio_value:,.2f}")

    # =========================================================================
    # 2. PIPELINE METRICS
    # =========================================================================
    print("\n" + "-"*70)
    print("2. PIPELINE METRICS (In Progress)")
    print("-"*70)

    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE status IN ('intake', 'uploaded', 'analyzing', 'review', 'in_progress', 'pending_review')
    """)
    pipeline_total = cursor.fetchone()[0]
    print(f"  Total Pipeline: {pipeline_total}")

    if pipeline_total < 15:
        issues.append(f"Low pipeline count: {pipeline_total} (expected 15+)")

    # Pipeline breakdown
    cursor.execute("""
        SELECT status, COUNT(*) FROM contracts
        WHERE status IN ('intake', 'uploaded', 'analyzing', 'review', 'in_progress', 'pending_review')
        GROUP BY status
    """)
    print("  Pipeline Breakdown:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # =========================================================================
    # 3. TIMELINE METRICS (90-Day Window)
    # =========================================================================
    print("\n" + "-"*70)
    print("3. TIMELINE METRICS (Next 90 Days)")
    print("-"*70)

    # Expiring contracts
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE (expiration_date BETWEEN '{today_str}' AND '{ninety_days_str}'
               OR end_date BETWEEN '{today_str}' AND '{ninety_days_str}')
        AND status NOT IN ('archived', 'expired', 'terminated')
    """)
    expiring = cursor.fetchone()[0]
    print(f"  Expiring in 90 days: {expiring}")

    if expiring < 5:
        issues.append(f"Low expiring count: {expiring} (expected 5+)")

    # Renewal contracts
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE renewal_date BETWEEN '{today_str}' AND '{ninety_days_str}'
        AND status NOT IN ('archived', 'expired', 'terminated')
    """)
    renewal = cursor.fetchone()[0]
    print(f"  Renewal in 90 days: {renewal}")

    # Pending review
    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE status IN ('intake', 'uploaded', 'pending_review')
    """)
    pending = cursor.fetchone()[0]
    print(f"  Pending review: {pending}")

    if pending < 5:
        issues.append(f"Low pending review count: {pending} (expected 5+)")

    # =========================================================================
    # 4. ACTIVITY METRICS (Past 90 Days)
    # =========================================================================
    print("\n" + "-"*70)
    print("4. ACTIVITY METRICS (Past 90 Days)")
    print("-"*70)

    # Analyzed contracts
    cursor.execute(f"""
        SELECT COUNT(*) FROM risk_assessments
        WHERE assessment_date >= '{ninety_ago_str}'
    """)
    analyzed = cursor.fetchone()[0]
    print(f"  Contracts analyzed: {analyzed}")

    if analyzed < 30:
        issues.append(f"Low recent analysis count: {analyzed} (expected 30+)")

    # Negotiating activity
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE status = 'negotiating'
        AND updated_at >= '{ninety_ago_str}'
    """)
    negotiating = cursor.fetchone()[0]
    print(f"  Contracts negotiating: {negotiating}")

    # Audit activity
    cursor.execute(f"""
        SELECT COUNT(*) FROM audit_log
        WHERE timestamp >= '{ninety_ago_str}'
    """)
    audit_activity = cursor.fetchone()[0]
    print(f"  Audit log entries: {audit_activity}")

    # =========================================================================
    # 5. RISK DISTRIBUTION
    # =========================================================================
    print("\n" + "-"*70)
    print("5. RISK DISTRIBUTION")
    print("-"*70)

    cursor.execute("""
        SELECT risk_level, COUNT(*) as cnt FROM contracts
        GROUP BY risk_level
        ORDER BY cnt DESC
    """)
    risk_data = cursor.fetchall()
    total = sum(r[1] for r in risk_data)

    print("  Distribution:")
    risk_found = set()
    for row in risk_data:
        pct = (row[1] / total * 100) if total > 0 else 0
        print(f"    {row[0]}: {row[1]} ({pct:.1f}%)")
        risk_found.add(row[0])

    expected_risks = {"LOW", "MEDIUM", "HIGH", "CRITICAL", "DEALBREAKER"}
    missing_risks = expected_risks - risk_found
    if missing_risks:
        issues.append(f"Missing risk levels: {missing_risks}")

    # High risk count
    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE risk_level IN ('HIGH', 'CRITICAL', 'DEALBREAKER')
    """)
    high_risk = cursor.fetchone()[0]
    print(f"  High risk items: {high_risk}")

    # =========================================================================
    # 6. STATUS DISTRIBUTION
    # =========================================================================
    print("\n" + "-"*70)
    print("6. STATUS DISTRIBUTION")
    print("-"*70)

    cursor.execute("""
        SELECT status, COUNT(*) FROM contracts
        GROUP BY status
        ORDER BY COUNT(*) DESC
    """)
    print("  All statuses:")
    status_found = set()
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")
        status_found.add(row[0])

    expected_statuses = {"active", "expired", "negotiating", "intake", "review",
                         "uploaded", "analyzing", "in_progress", "terminated", "archived"}
    missing_statuses = expected_statuses - status_found
    if missing_statuses:
        issues.append(f"Missing statuses: {missing_statuses}")

    # =========================================================================
    # 7. HIGH-VALUE CONTRACTS
    # =========================================================================
    print("\n" + "-"*70)
    print("7. HIGH-VALUE CONTRACTS (>$100K)")
    print("-"*70)

    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE contract_value > 100000
    """)
    high_value = cursor.fetchone()[0]
    print(f"  High-value contracts: {high_value}")

    if high_value < 20:
        issues.append(f"Low high-value count: {high_value} (expected 20+)")

    # High-value expiring
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE contract_value > 100000
        AND expiration_date BETWEEN '{today_str}' AND '{ninety_days_str}'
        AND status NOT IN ('archived', 'expired', 'terminated')
    """)
    high_value_expiring = cursor.fetchone()[0]
    print(f"  High-value expiring in 90 days: {high_value_expiring}")

    if high_value_expiring < 3:
        issues.append(f"Low high-value expiring: {high_value_expiring} (expected 3+)")

    # =========================================================================
    # 8. CONTRACT TYPES
    # =========================================================================
    print("\n" + "-"*70)
    print("8. CONTRACT TYPES")
    print("-"*70)

    cursor.execute("""
        SELECT contract_type, COUNT(*) FROM contracts
        GROUP BY contract_type
        ORDER BY COUNT(*) DESC
    """)
    print("  Distribution:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # =========================================================================
    # 9. VALUE TREND (Last 12 Months)
    # =========================================================================
    print("\n" + "-"*70)
    print("9. VALUE TREND (Last 12 Months)")
    print("-"*70)

    cursor.execute("""
        SELECT strftime('%Y-%m', upload_date) as month,
               COUNT(*) as contracts,
               SUM(contract_value) as value
        FROM contracts
        WHERE upload_date IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    trend_data = cursor.fetchall()
    print("  Monthly uploads:")
    months_with_data = 0
    for row in trend_data:
        value = row[2] or 0
        print(f"    {row[0]}: {row[1]} contracts (${value:,.0f})")
        months_with_data += 1

    if months_with_data < 6:
        issues.append(f"Limited upload history: {months_with_data} months (expected 6+)")

    # =========================================================================
    # 10. EXPIRATION CALENDAR
    # =========================================================================
    print("\n" + "-"*70)
    print("10. EXPIRATION CALENDAR (Next 90 Days)")
    print("-"*70)

    cursor.execute(f"""
        SELECT expiration_date, COUNT(*) FROM contracts
        WHERE expiration_date BETWEEN '{today_str}' AND '{ninety_days_str}'
        GROUP BY expiration_date
        ORDER BY expiration_date
        LIMIT 15
    """)
    exp_data = cursor.fetchall()
    if exp_data:
        print("  Upcoming expirations:")
        for row in exp_data:
            print(f"    {row[0]}: {row[1]} contracts")
    else:
        issues.append("No contracts expiring in next 90 days calendar")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    if issues:
        print(f"\n  ISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"    - {issue}")
        print("\n  Status: NEEDS ATTENTION")
    else:
        print("\n  All KPI requirements verified!")
        print("  Status: PASSED")

    conn.close()
    return len(issues) == 0


def main():
    db_paths = [
        Path("C:/Users/jrudy/CIP/tests/TEST_DB/test_contracts.db"),
        Path("C:/Users/jrudy/CIP/data/contracts.db"),
    ]

    for db_path in db_paths:
        if db_path.exists():
            print(f"\n{'#'*70}")
            print(f"# Verifying: {db_path.name}")
            print(f"{'#'*70}")
            verify_kpis(str(db_path))


if __name__ == "__main__":
    main()
