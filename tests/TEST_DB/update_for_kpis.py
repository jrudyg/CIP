"""
Update Test Database for KPI Requirements
Modifies existing 100 contracts to have realistic distributions for:
- Lifecycle stages (pipeline, active, expiring, expired)
- Risk levels (proper distribution)
- Date ranges (12-month history, 90-day expirations)
- Contract values (including high-value contracts)
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
import json

# =============================================================================
# KPI-ALIGNED CONFIGURATION
# =============================================================================

# Status distribution based on KPIs
# Portfolio: active contracts (not archived/expired/terminated)
# Pipeline: intake, uploaded, analyzing, review, in_progress
# Timeline: expiring within 90 days
STATUS_DISTRIBUTION = {
    # Pipeline statuses (30% of contracts)
    "intake": 5,
    "uploaded": 4,
    "analyzing": 3,
    "review": 5,
    "in_progress": 4,
    "pending_review": 4,

    # Negotiation (10%)
    "negotiating": 10,

    # Active portfolio (35%)
    "active": 35,

    # Expired/terminated (15%)
    "expired": 10,
    "terminated": 5,

    # Archived (5%)
    "archived": 5,
}

# Risk distribution based on KPIs
# Critical (10%), High (20%), Medium (40%), Low (30%)
RISK_DISTRIBUTION = {
    "LOW": 25,
    "MEDIUM": 35,
    "HIGH": 20,
    "CRITICAL": 12,
    "DEALBREAKER": 8,
}

# Contract role distribution
ROLE_DISTRIBUTION = {
    "VENDOR": 35,
    "CUSTOMER": 40,
    "PARTNER": 10,
    "RESELLER": 10,
    "CONSULTANT": 5,
}

def get_date_in_range(start_days_ago, end_days_ago):
    """Generate a date between start_days_ago and end_days_ago from today."""
    today = datetime.now()
    start = today - timedelta(days=start_days_ago)
    end = today - timedelta(days=end_days_ago)
    delta = (end - start).days
    if delta <= 0:
        delta = 1
    random_days = random.randint(0, delta)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

def get_future_date(min_days, max_days):
    """Generate a future date between min_days and max_days from today."""
    today = datetime.now()
    random_days = random.randint(min_days, max_days)
    return (today + timedelta(days=random_days)).strftime("%Y-%m-%d")

def get_past_date(min_days, max_days):
    """Generate a past date between min_days and max_days ago."""
    today = datetime.now()
    random_days = random.randint(min_days, max_days)
    return (today - timedelta(days=random_days)).strftime("%Y-%m-%d")

def distribute_values(distribution, count):
    """Distribute count items according to percentage distribution."""
    result = []
    for value, pct in distribution.items():
        num = int(count * pct / 100)
        result.extend([value] * num)

    # Fill remaining with random choices
    while len(result) < count:
        result.append(random.choice(list(distribution.keys())))

    # Shuffle to randomize order
    random.shuffle(result)
    return result[:count]

def generate_contract_value(contract_type, is_high_value=False):
    """Generate realistic contract values."""
    if is_high_value:
        return round(random.uniform(150000, 5000000), 2)

    ranges = {
        "NDA": (0, 0),
        "MNDA": (0, 0),
        "MSA": (100000, 2000000),
        "SOW": (25000, 500000),
        "SLA": (10000, 200000),
        "MOU": (0, 0),
        "LOI": (50000, 1000000),
        "AMENDMENT": (10000, 300000),
        "ADDENDUM": (5000, 150000),
        "ORDER": (5000, 250000),
        "LICENSE": (10000, 500000),
        "LEASE": (24000, 300000),
        "EMPLOYMENT": (60000, 250000),
        "OTHER": (10000, 200000),
    }
    min_val, max_val = ranges.get(contract_type, (10000, 100000))
    if max_val == 0:
        return None
    return round(random.uniform(min_val, max_val), 2)

def update_database(db_path):
    """Update the test database with KPI-aligned data."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*70)
    print("UPDATING TEST DATABASE FOR KPI REQUIREMENTS")
    print("="*70)

    # Get all contract IDs
    cursor.execute("SELECT id, contract_type FROM contracts ORDER BY id")
    contracts = cursor.fetchall()
    contract_count = len(contracts)

    print(f"\nTotal contracts to update: {contract_count}")

    # ==========================================================================
    # 1. UPDATE STATUS DISTRIBUTION
    # ==========================================================================
    print("\n[1] Updating status distribution...")

    statuses = distribute_values(STATUS_DISTRIBUTION, contract_count)

    for i, (contract_id, contract_type) in enumerate(contracts):
        status = statuses[i]
        cursor.execute("UPDATE contracts SET status = ? WHERE id = ?", (status, contract_id))

    # Show distribution
    cursor.execute("SELECT status, COUNT(*) FROM contracts GROUP BY status ORDER BY COUNT(*) DESC")
    print("  New status distribution:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # ==========================================================================
    # 2. UPDATE RISK DISTRIBUTION
    # ==========================================================================
    print("\n[2] Updating risk level distribution...")

    risks = distribute_values(RISK_DISTRIBUTION, contract_count)

    for i, (contract_id, contract_type) in enumerate(contracts):
        risk = risks[i]
        cursor.execute("UPDATE contracts SET risk_level = ? WHERE id = ?", (risk, contract_id))

        # Also update risk_assessments
        cursor.execute("""
            UPDATE risk_assessments SET overall_risk = ? WHERE contract_id = ?
        """, (risk, contract_id))

    # Show distribution
    cursor.execute("SELECT risk_level, COUNT(*) FROM contracts GROUP BY risk_level ORDER BY COUNT(*) DESC")
    print("  New risk distribution:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # ==========================================================================
    # 3. UPDATE CONTRACT ROLES
    # ==========================================================================
    print("\n[3] Updating contract role distribution...")

    roles = distribute_values(ROLE_DISTRIBUTION, contract_count)

    for i, (contract_id, contract_type) in enumerate(contracts):
        role = roles[i]
        cursor.execute("UPDATE contracts SET contract_role = ? WHERE id = ?", (role, contract_id))

    # ==========================================================================
    # 4. UPDATE DATES FOR REALISTIC TIMELINE
    # ==========================================================================
    print("\n[4] Updating dates for realistic timeline...")

    cursor.execute("SELECT id, status, contract_type FROM contracts")
    all_contracts = cursor.fetchall()

    expiring_soon_count = 0
    expired_count = 0
    active_future_count = 0

    for contract_id, status, contract_type in all_contracts:
        # Upload date: spread over last 12 months
        upload_date = get_date_in_range(365, 1)

        # Effective date: around upload date
        effective_offset = random.randint(0, 30)
        effective_date = (datetime.strptime(upload_date, "%Y-%m-%d") +
                         timedelta(days=effective_offset)).strftime("%Y-%m-%d")

        # Expiration date based on status
        if status == "expired":
            # Expired: expiration date in the past (1-180 days ago)
            expiration_date = get_past_date(1, 180)
            expired_count += 1
        elif status == "terminated":
            # Terminated: expiration date in the past
            expiration_date = get_past_date(1, 90)
        elif status == "active":
            # Active: Some expiring soon (within 90 days), some later
            if random.random() < 0.3:  # 30% of active contracts expiring soon
                expiration_date = get_future_date(1, 90)
                expiring_soon_count += 1
            else:
                expiration_date = get_future_date(91, 730)
                active_future_count += 1
        elif status in ["negotiating", "in_progress", "review"]:
            # In progress: expiration date in future
            expiration_date = get_future_date(30, 365)
        elif status in ["intake", "uploaded", "analyzing", "pending_review"]:
            # Pipeline: expiration date typically future or null
            if random.random() < 0.7:
                expiration_date = get_future_date(60, 730)
            else:
                expiration_date = None
        elif status == "archived":
            # Archived: expiration in past
            expiration_date = get_past_date(30, 365)
        else:
            expiration_date = get_future_date(30, 365)

        # Renewal date: 30-60 days before expiration for some contracts
        renewal_date = None
        if expiration_date and random.random() < 0.4:
            exp_dt = datetime.strptime(expiration_date, "%Y-%m-%d")
            renewal_offset = random.randint(30, 60)
            renewal_dt = exp_dt - timedelta(days=renewal_offset)
            renewal_date = renewal_dt.strftime("%Y-%m-%d")

        # Updated_at: Recent for active/negotiating, older for archived/expired
        if status in ["active", "negotiating", "in_progress", "review", "analyzing"]:
            updated_at = get_date_in_range(30, 0)  # Last 30 days
        else:
            updated_at = get_date_in_range(180, 30)  # 30-180 days ago

        cursor.execute("""
            UPDATE contracts SET
                upload_date = ?,
                effective_date = ?,
                expiration_date = ?,
                updated_at = ?
            WHERE id = ?
        """, (upload_date, effective_date, expiration_date, updated_at, contract_id))

        # Store renewal_date in metadata_json
        if renewal_date:
            cursor.execute("SELECT metadata_json FROM contracts WHERE id = ?", (contract_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    metadata = json.loads(row[0])
                except:
                    metadata = {}
            else:
                metadata = {}
            metadata["renewal_date"] = renewal_date
            cursor.execute("UPDATE contracts SET metadata_json = ? WHERE id = ?",
                          (json.dumps(metadata), contract_id))

    print(f"  Contracts expiring within 90 days: {expiring_soon_count}")
    print(f"  Contracts already expired: {expired_count}")
    print(f"  Active contracts with future expiration: {active_future_count}")

    # ==========================================================================
    # 5. UPDATE CONTRACT VALUES (include high-value contracts)
    # ==========================================================================
    print("\n[5] Updating contract values...")

    cursor.execute("SELECT id, contract_type, expiration_date FROM contracts")
    all_contracts = cursor.fetchall()

    high_value_count = 0
    high_value_expiring = 0
    total_value = 0

    today = datetime.now()
    ninety_days = today + timedelta(days=90)

    for i, (contract_id, contract_type, exp_date) in enumerate(all_contracts):
        # Make ~20% high-value contracts
        is_high_value = i < 20

        value = generate_contract_value(contract_type, is_high_value)

        if value:
            total_value += value
            if value > 100000:
                high_value_count += 1
                # Check if expiring soon
                if exp_date:
                    exp_dt = datetime.strptime(exp_date, "%Y-%m-%d")
                    if today <= exp_dt <= ninety_days:
                        high_value_expiring += 1

        cursor.execute("UPDATE contracts SET contract_value = ? WHERE id = ?",
                      (value, contract_id))

    print(f"  Total portfolio value: ${total_value:,.2f}")
    print(f"  High-value contracts (>$100K): {high_value_count}")
    print(f"  High-value expiring in 90 days: {high_value_expiring}")

    # ==========================================================================
    # 6. UPDATE RISK ASSESSMENTS WITH RECENT DATES
    # ==========================================================================
    print("\n[6] Updating risk assessment dates...")

    cursor.execute("SELECT id FROM risk_assessments")
    assessments = cursor.fetchall()

    recent_count = 0
    for assessment_id, in assessments:
        # 60% assessed in last 90 days (for activity metrics)
        if random.random() < 0.6:
            assessed_date = get_date_in_range(90, 0)
            recent_count += 1
        else:
            assessed_date = get_date_in_range(365, 90)

        cursor.execute("""
            UPDATE risk_assessments SET assessment_date = ? WHERE id = ?
        """, (assessed_date, assessment_id))

    print(f"  Assessments in last 90 days: {recent_count}")

    # ==========================================================================
    # 7. UPDATE ANALYSIS SNAPSHOTS
    # ==========================================================================
    print("\n[7] Updating analysis snapshot dates...")

    cursor.execute("""
        SELECT s.snapshot_id, c.status, c.updated_at
        FROM analysis_snapshots s
        JOIN contracts c ON s.contract_id = c.id
    """)
    snapshots = cursor.fetchall()

    for snapshot_id, status, updated_at in snapshots:
        # Analysis date should be around contract updated_at
        if updated_at:
            try:
                base_date = datetime.strptime(updated_at[:10], "%Y-%m-%d")
                offset = random.randint(-5, 5)
                analysis_date = (base_date + timedelta(days=offset)).isoformat()
            except:
                analysis_date = datetime.now().isoformat()
        else:
            analysis_date = get_date_in_range(180, 0)

        cursor.execute("""
            UPDATE analysis_snapshots SET created_at = ? WHERE snapshot_id = ?
        """, (analysis_date, snapshot_id))

    # ==========================================================================
    # 8. UPDATE AUDIT LOG WITH REALISTIC ACTIVITY
    # ==========================================================================
    print("\n[8] Updating audit log timestamps...")

    cursor.execute("SELECT id, contract_id FROM audit_log")
    audit_entries = cursor.fetchall()

    recent_audit = 0
    for audit_id, contract_id in audit_entries:
        # Get contract's upload date as baseline
        cursor.execute("SELECT upload_date FROM contracts WHERE id = ?", (contract_id,))
        row = cursor.fetchone()
        if row and row[0]:
            try:
                upload_dt = datetime.strptime(row[0], "%Y-%m-%d")
                # Audit entries from upload to now
                days_since = (datetime.now() - upload_dt).days
                if days_since > 0:
                    offset = random.randint(0, days_since)
                    audit_date = (upload_dt + timedelta(days=offset)).isoformat()
                else:
                    audit_date = datetime.now().isoformat()
            except:
                audit_date = datetime.now().isoformat()
        else:
            audit_date = get_date_in_range(180, 0)

        # Check if recent
        try:
            audit_dt = datetime.fromisoformat(audit_date[:10])
            if (datetime.now() - audit_dt).days <= 90:
                recent_audit += 1
        except:
            pass

        cursor.execute("UPDATE audit_log SET timestamp = ? WHERE id = ?",
                      (audit_date, audit_id))

    print(f"  Audit entries in last 90 days: {recent_audit}")

    # ==========================================================================
    # 9. ADD END_DATE COLUMN IF MISSING (for Home.py compatibility)
    # ==========================================================================
    print("\n[9] Ensuring end_date column exists...")

    try:
        cursor.execute("ALTER TABLE contracts ADD COLUMN end_date TEXT")
        print("  Added end_date column")
    except sqlite3.OperationalError:
        print("  end_date column already exists")

    # Copy expiration_date to end_date
    cursor.execute("UPDATE contracts SET end_date = expiration_date")
    print("  Synced end_date with expiration_date")

    # ==========================================================================
    # 10. ADD RENEWAL_DATE COLUMN IF MISSING
    # ==========================================================================
    print("\n[10] Ensuring renewal_date column exists...")

    try:
        cursor.execute("ALTER TABLE contracts ADD COLUMN renewal_date TEXT")
        print("  Added renewal_date column")
    except sqlite3.OperationalError:
        print("  renewal_date column already exists")

    # Populate renewal_date from metadata_json
    cursor.execute("SELECT id, metadata_json FROM contracts WHERE metadata_json IS NOT NULL")
    for contract_id, metadata_json in cursor.fetchall():
        try:
            metadata = json.loads(metadata_json)
            if "renewal_date" in metadata:
                cursor.execute("UPDATE contracts SET renewal_date = ? WHERE id = ?",
                              (metadata["renewal_date"], contract_id))
        except:
            pass

    # Count contracts with renewal dates
    cursor.execute("SELECT COUNT(*) FROM contracts WHERE renewal_date IS NOT NULL")
    renewal_count = cursor.fetchone()[0]
    print(f"  Contracts with renewal dates: {renewal_count}")

    # ==========================================================================
    # 11. ADD ARCHIVED COLUMN IF MISSING
    # ==========================================================================
    print("\n[11] Ensuring archived column exists...")

    try:
        cursor.execute("ALTER TABLE contracts ADD COLUMN archived INTEGER DEFAULT 0")
        print("  Added archived column")
    except sqlite3.OperationalError:
        print("  archived column already exists")

    # Set archived = 1 for archived status
    cursor.execute("UPDATE contracts SET archived = 1 WHERE status = 'archived'")
    cursor.execute("UPDATE contracts SET archived = 0 WHERE status != 'archived'")

    # ==========================================================================
    # COMMIT AND SUMMARY
    # ==========================================================================
    conn.commit()

    print("\n" + "="*70)
    print("UPDATE SUMMARY")
    print("="*70)

    # Portfolio metrics
    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE status NOT IN ('archived', 'expired', 'terminated')
    """)
    portfolio_count = cursor.fetchone()[0]

    # Pipeline metrics
    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE status IN ('intake', 'uploaded', 'analyzing', 'review', 'in_progress', 'pending_review')
    """)
    pipeline_count = cursor.fetchone()[0]

    # Expiring in 90 days
    today_str = datetime.now().strftime("%Y-%m-%d")
    ninety_str = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE expiration_date BETWEEN '{today_str}' AND '{ninety_str}'
        AND status NOT IN ('archived', 'expired', 'terminated')
    """)
    expiring_count = cursor.fetchone()[0]

    # High risk
    cursor.execute("""
        SELECT COUNT(*) FROM contracts
        WHERE risk_level IN ('CRITICAL', 'HIGH', 'DEALBREAKER')
    """)
    high_risk_count = cursor.fetchone()[0]

    # Total value
    cursor.execute("SELECT SUM(contract_value) FROM contracts WHERE contract_value IS NOT NULL")
    total_value = cursor.fetchone()[0] or 0

    print(f"\n  PORTFOLIO STATS:")
    print(f"    Active portfolio: {portfolio_count} contracts")
    print(f"    Pipeline (in progress): {pipeline_count} contracts")
    print(f"    Expiring in 90 days: {expiring_count} contracts")
    print(f"    High risk items: {high_risk_count} contracts")
    print(f"    Total portfolio value: ${total_value:,.2f}")

    # Status breakdown
    print(f"\n  STATUS DISTRIBUTION:")
    cursor.execute("SELECT status, COUNT(*) FROM contracts GROUP BY status ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # Risk breakdown
    print(f"\n  RISK DISTRIBUTION:")
    cursor.execute("SELECT risk_level, COUNT(*) FROM contracts GROUP BY risk_level ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    conn.close()
    print("\n" + "="*70)
    print("Database update complete!")
    print("="*70)


def main():
    db_path = Path("C:/Users/jrudy/CIP/tests/TEST_DB/test_contracts.db")

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return

    # Also update the active databases
    active_paths = [
        Path("C:/Users/jrudy/CIP/data/contracts.db"),
        Path("C:/Users/jrudy/CIP/backend/contracts.db"),
    ]

    # Update test DB first
    print(f"\nUpdating: {db_path}")
    update_database(str(db_path))

    # Copy to active locations
    print("\n\nCopying updated database to active locations...")
    import shutil
    for active_path in active_paths:
        if active_path.parent.exists():
            shutil.copy(db_path, active_path)
            print(f"  Copied to: {active_path}")


if __name__ == "__main__":
    main()
