"""
UCC Integration Demonstration
Shows UCC statutory detection in action with real examples.

Created: 2026-01-18
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from cce_plus_integration import score_clause_risk


def print_result(title, result):
    """Pretty print risk scoring result."""
    print(f"\n{title}")
    print("=" * 70)
    print(f"Risk Score: {result['risk_score']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Severity: {result['severity']}, Complexity: {result['complexity']}, Impact: {result['impact']}")

    if result.get('statutory_flag'):
        print(f"\nUCC STATUTORY VIOLATION DETECTED:")
        print(f"  Rule: {result['statutory_flag']}")
        print(f"  Citation: {result['statutory_cite']}")

        if result.get('ucc_violation'):
            ucc = result['ucc_violation']
            print(f"  Category: {ucc.get('category')}")
            print(f"  Severity: {ucc.get('severity')}")
            print(f"  Risk Multiplier: {ucc.get('risk_multiplier')}")
            print(f"  Matched Concepts: {', '.join(ucc.get('matched_concepts', [])[:5])}")
    else:
        print(f"\nNo UCC violation detected")


def demo():
    """Run demonstration of UCC integration."""

    print("\n" + "=" * 70)
    print("UCC STATUTORY INTEGRATION DEMONSTRATION")
    print("Showing 40% weight for statutory violations")
    print("=" * 70)

    # Example 1: Consequential Damages Exclusion (UCC-2-719)
    clause1 = """
    Seller's sole and exclusive remedy is repair or replacement.
    Buyer waives all claims for consequential damages, including
    lost profits, business interruption, and any other indirect damages.
    """

    result1 = score_clause_risk(clause1, "Legal/Remedy")
    print_result("EXAMPLE 1: Consequential Damages Exclusion (UCC-2-719)", result1)

    # Example 2: Prepayment Trap (UCC-2-719)
    clause2 = """
    Client shall make full prepayment of $75,000 upon execution.
    All payments are non-refundable. No refunds will be issued
    upon termination for any reason whatsoever.
    """

    result2 = score_clause_risk(clause2, "Financial/Prepayment")
    print_result("EXAMPLE 2: Prepayment Trap (UCC-2-719)", result2)

    # Example 3: AS IS Warranty Disclaimer (UCC-2-314)
    clause3 = """
    EQUIPMENT IS SOLD AS IS, WITH ALL FAULTS. Seller disclaims
    all warranties of merchantability and fitness for particular purpose.
    """

    result3 = score_clause_risk(clause3, "WARRANTY")
    print_result("EXAMPLE 3: AS IS Warranty Disclaimer (UCC-2-314)", result3)

    # Example 4: Standard Clause (No Violation)
    clause4 = """
    This Agreement shall be governed by Delaware law. The parties
    shall cooperate in good faith to resolve any disputes.
    """

    result4 = score_clause_risk(clause4, "Default")
    print_result("EXAMPLE 4: Standard Clause (No Violation)", result4)

    # Example 5: Liability Cap Squeeze (SI-002)
    clause5 = """
    Vendor's aggregate liability under this Agreement is limited to
    the lesser of fees paid or $50,000. This cap applies to all claims.
    """

    result5 = score_clause_risk(clause5, "Legal/Liability")
    print_result("EXAMPLE 5: Liability Cap (SI-002)", result5)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Example 1 (UCC-2-719): {result1['risk_level']} risk (score {result1['risk_score']})")
    print(f"Example 2 (UCC-2-719): {result2['risk_level']} risk (score {result2['risk_score']})")
    print(f"Example 3 (UCC-2-314): {result3['risk_level']} risk (score {result3['risk_score']})")
    print(f"Example 4 (No UCC):    {result4['risk_level']} risk (score {result4['risk_score']})")
    print(f"Example 5 (SI-002):    {result5['risk_level']} risk (score {result5['risk_score']})")

    print("\nNOTE: Risk scores escalate when UCC violations detected due to 40% statutory weight.")
    print("=" * 70)


if __name__ == '__main__':
    demo()
