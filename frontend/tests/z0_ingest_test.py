"""
Z0 Knowledge Layer - Ingest and Profile Test
Validates ingestion, idempotence, and profile queries.
"""

import sys
from pathlib import Path

# Ensure frontend/ is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

Z0_DB_PATH = ROOT / "z0" / "z0_knowledge.db"


def _reset_db():
    """For test purposes, delete the DB if it exists to start fresh."""
    if Z0_DB_PATH.exists():
        Z0_DB_PATH.unlink()


def build_sample_z8_result():
    """
    Construct a minimal but representative z8_result dict for testing Z0 ingestion.
    Uses the exact structure produced by z8_cross_document_zone().
    """
    return {
        "summary": {
            "round_count": 3,
            "baseline_posture": "High Risk",
            "final_posture": "Balanced",
            "trajectory": "Improving",
        },
        "clause_trends": [
            {
                "clause_id": "C1",
                "stability": "Moderately volatile",
                "net_verdict": "Better",
                "impact_start": "high",
                "impact_end": "medium",
                "shift_start": "favors_counterparty",
                "shift_end": "balanced",
                "transitions": 2,
            },
            {
                "clause_id": "C2",
                "stability": "Stable",
                "net_verdict": "No net change",
                "impact_start": "medium",
                "impact_end": "medium",
                "shift_start": "balanced",
                "shift_end": "balanced",
                "transitions": 0,
            },
            {
                "clause_id": "C3",
                "stability": "Highly volatile",
                "net_verdict": "Worse",
                "impact_start": "low",
                "impact_end": "high",
                "shift_start": "favors_customer",
                "shift_end": "favors_counterparty",
                "transitions": 3,
            },
        ],
        "behavior_insights": {
            "concessions_count": 1,
            "counterparty_leaning_changes": 1,
        },
        "invariants": {
            "clause_id_stable": True,
            "round_count": 3,
            "missing_clauses": [],
            "trend_consistency_ok": True,
        },
    }


def build_second_z8_result():
    """Build a second Z8 result for a different deal with same counterparty."""
    return {
        "summary": {
            "round_count": 2,
            "baseline_posture": "Moderate",
            "final_posture": "Favorable",
            "trajectory": "Improving",
        },
        "clause_trends": [
            {
                "clause_id": "C1",
                "stability": "Stable",
                "net_verdict": "Better",
                "impact_start": "medium",
                "impact_end": "low",
                "shift_start": "balanced",
                "shift_end": "favors_customer",
                "transitions": 1,
            },
            {
                "clause_id": "C3",
                "stability": "Moderately volatile",
                "net_verdict": "Worse",
                "impact_start": "medium",
                "impact_end": "high",
                "shift_start": "balanced",
                "shift_end": "favors_counterparty",
                "transitions": 2,
            },
        ],
        "behavior_insights": {
            "concessions_count": 1,
            "counterparty_leaning_changes": 1,
        },
        "invariants": {
            "clause_id_stable": True,
            "round_count": 2,
            "missing_clauses": [],
            "trend_consistency_ok": True,
        },
    }


def main():
    _reset_db()

    # Import store module
    from z0 import store

    z8_result = build_sample_z8_result()

    # Test 1: Ingest first deal
    print("Test 1: Ingesting first deal...")
    store.ingest_z8_result(
        deal_id="DEAL-1",
        counterparty_id="CP-ACME",
        timestamp="2025-12-01T10:00:00Z",
        z8_result=z8_result,
    )
    print("  PASS: First deal ingested")

    # Test 2: Idempotence - ingest same deal again
    print("Test 2: Testing idempotence (re-ingest same deal)...")
    store.ingest_z8_result(
        deal_id="DEAL-1",
        counterparty_id="CP-ACME",
        timestamp="2025-12-01T10:00:00Z",
        z8_result=z8_result,
    )

    portfolio = store.get_portfolio_summary()
    assert portfolio["total_deals"] == 1, f"Expected 1 deal after idempotent re-ingest, got {portfolio['total_deals']}"
    print("  PASS: Idempotence verified (still 1 deal)")

    # Test 3: Ingest second deal for same counterparty
    print("Test 3: Ingesting second deal...")
    z8_result_2 = build_second_z8_result()
    store.ingest_z8_result(
        deal_id="DEAL-2",
        counterparty_id="CP-ACME",
        timestamp="2025-12-02T14:00:00Z",
        z8_result=z8_result_2,
    )

    portfolio = store.get_portfolio_summary()
    assert portfolio["total_deals"] == 2, f"Expected 2 deals, got {portfolio['total_deals']}"
    print("  PASS: Second deal ingested (total: 2)")

    # Test 4: Counterparty profile
    print("Test 4: Testing counterparty profile...")
    cp_profile = store.get_counterparty_profile("CP-ACME")
    assert cp_profile["deal_count"] == 2, f"Expected 2 deals for CP-ACME, got {cp_profile['deal_count']}"
    assert cp_profile["avg_concessions_per_deal"] == 1.0, f"Expected avg_concessions=1.0, got {cp_profile['avg_concessions_per_deal']}"
    print(f"  PASS: Counterparty profile: {cp_profile['deal_count']} deals, avg_concessions={cp_profile['avg_concessions_per_deal']}")

    # Test 5: Clause profile
    print("Test 5: Testing clause profile...")
    clause_profile_c1 = store.get_clause_profile("C1")
    assert clause_profile_c1["occurrences"] == 2, f"Expected 2 occurrences for C1, got {clause_profile_c1['occurrences']}"
    print(f"  PASS: Clause C1 profile: {clause_profile_c1['occurrences']} occurrences")

    clause_profile_c3 = store.get_clause_profile("C3")
    assert clause_profile_c3["occurrences"] == 2, f"Expected 2 occurrences for C3, got {clause_profile_c3['occurrences']}"
    assert clause_profile_c3["net_verdict_distribution"].get("Worse", 0) == 2, "Expected C3 to have 2 'Worse' verdicts"
    print(f"  PASS: Clause C3 profile: {clause_profile_c3['occurrences']} occurrences, {clause_profile_c3['net_verdict_distribution'].get('Worse', 0)} 'Worse'")

    # Test 6: Top risky clauses
    print("Test 6: Testing top risky clauses...")
    top_risky = store.get_top_risky_clauses(limit=5)
    assert len(top_risky) >= 1, "Expected at least 1 risky clause"
    assert top_risky[0]["clause_id"] == "C3", f"Expected C3 to be top risky, got {top_risky[0]['clause_id']}"
    print(f"  PASS: Top risky clause: {top_risky[0]['clause_id']} with {top_risky[0]['worse_count']} 'Worse' verdicts")

    # Test 7: Portfolio summary distributions
    print("Test 7: Testing portfolio summary...")
    portfolio = store.get_portfolio_summary()
    assert "Improving" in portfolio["trajectory_distribution"], "Expected 'Improving' in trajectory distribution"
    print(f"  PASS: Portfolio: {portfolio['total_deals']} deals, trajectory distribution: {portfolio['trajectory_distribution']}")

    # Test 8: Validation rejection
    print("Test 8: Testing validation rejection...")
    bad_z8 = {
        "summary": {"round_count": 0, "baseline_posture": None, "final_posture": None, "trajectory": None},
        "clause_trends": [],
        "behavior_insights": {},
        "invariants": {"trend_consistency_ok": False},
    }
    try:
        store.ingest_z8_result(
            deal_id="DEAL-BAD",
            counterparty_id="CP-BAD",
            timestamp="2025-12-03T00:00:00Z",
            z8_result=bad_z8,
        )
        print("  FAIL: Should have rejected invalid Z8 result")
        sys.exit(1)
    except ValueError as e:
        print(f"  PASS: Correctly rejected invalid Z8: {e}")

    print("\n" + "=" * 50)
    print("Z0 ingest/profile test passed.")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: Z0 test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
