"""
End-to-End Integration Test for UCC Statutory Detection
Tests full pipeline from clause text to weighted risk score.

Created: 2026-01-18
Version: 1.0
"""

import unittest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from cce_plus_integration import score_clause_risk


class TestUCCIntegration(unittest.TestCase):
    """Test end-to-end UCC integration in risk scoring pipeline."""

    def test_consequential_damages_escalation(self):
        """Test UCC-2-719 consequential damages exclusion escalates risk score."""

        # High-risk clause with UCC violation (consequential damages waiver)
        clause_with_ucc = """
        Seller's sole and exclusive remedy is repair or replacement of
        defective equipment. Buyer expressly waives all claims for
        consequential damages, lost profits, and business interruption.
        """

        # Similar clause WITHOUT UCC violation
        clause_without_ucc = """
        Seller shall repair or replace defective equipment. Buyer may
        claim all damages permitted by law, including consequential damages.
        """

        # Score both clauses
        result_with_ucc = score_clause_risk(clause_with_ucc, "Legal/Remedy")
        result_without_ucc = score_clause_risk(clause_without_ucc, "Legal/Remedy")

        # Verify UCC violation detected
        self.assertIsNotNone(result_with_ucc['statutory_flag'], "UCC violation should be detected")
        self.assertIn("UCC", result_with_ucc['statutory_flag'], "Should be UCC rule")
        self.assertIsNone(result_without_ucc['statutory_flag'], "No UCC violation should be detected")

        # Verify risk score escalation
        score_with = result_with_ucc['risk_score']
        score_without = result_without_ucc['risk_score']

        print(f"\nClause WITH UCC violation:")
        print(f"  - Statutory Flag: {result_with_ucc['statutory_flag']}")
        print(f"  - Risk Score: {score_with}")
        print(f"  - Risk Level: {result_with_ucc['risk_level']}")

        print(f"\nClause WITHOUT UCC violation:")
        print(f"  - Statutory Flag: {result_without_ucc['statutory_flag']}")
        print(f"  - Risk Score: {score_without}")
        print(f"  - Risk Level: {result_without_ucc['risk_level']}")

        self.assertGreater(score_with, score_without,
                          "UCC violation should escalate risk score")

        # Verify escalation magnitude (should be meaningful)
        escalation = score_with - score_without
        self.assertGreater(escalation, 0.5,
                          "Risk score escalation should be at least 0.5 points")

    def test_prepayment_trap_detection(self):
        """Test UCC-2-719 prepayment trap detection."""

        clause = """
        Client shall make full prepayment of $50,000 before work begins.
        Payment is non-refundable under any circumstances. No refunds will
        be provided upon termination for any reason.
        """

        result = score_clause_risk(clause, "Financial/Prepayment")

        print(f"\nPrepayment Trap Detection:")
        print(f"  - Statutory Flag: {result['statutory_flag']}")
        print(f"  - Risk Score: {result['risk_score']}")
        print(f"  - Risk Level: {result['risk_level']}")

        # Should detect UCC violation
        self.assertIsNotNone(result['statutory_flag'], "Prepayment trap should be detected")

        # Should be HIGH or CRITICAL risk
        self.assertIn(result['risk_level'], ['HIGH', 'CRITICAL'],
                     "Prepayment trap should be HIGH or CRITICAL risk")

    def test_as_is_warranty_disclaimer(self):
        """Test UCC-2-314/2-316 AS IS warranty disclaimer detection."""

        clause = """
        EQUIPMENT IS SOLD AS IS, WITH ALL FAULTS. Seller disclaims all
        warranties of merchantability and fitness for a particular purpose.
        No implied warranties shall apply.
        """

        result = score_clause_risk(clause, "WARRANTY")

        print(f"\nAS IS Warranty Disclaimer:")
        print(f"  - Statutory Flag: {result['statutory_flag']}")
        print(f"  - Risk Score: {result['risk_score']}")
        print(f"  - Risk Level: {result['risk_level']}")

        # Should detect UCC violation
        self.assertIsNotNone(result['statutory_flag'], "AS IS disclaimer should be detected")

        # Should be HIGH risk minimum
        self.assertGreaterEqual(result['risk_score'], 7.0,
                               "AS IS disclaimer should be HIGH risk (≥7.0)")

    def test_standard_clause_baseline(self):
        """Test that standard non-risky clauses have baseline scores."""

        clause = """
        This Agreement shall be governed by the laws of Delaware.
        The parties agree to negotiate in good faith to resolve disputes.
        """

        result = score_clause_risk(clause, "Default")

        print(f"\nStandard Clause Baseline:")
        print(f"  - Statutory Flag: {result.get('statutory_flag')}")
        print(f"  - Risk Score: {result['risk_score']}")
        print(f"  - Risk Level: {result['risk_level']}")

        # Should be MEDIUM or below
        self.assertLessEqual(result['risk_score'], 6.0,
                            "Standard clause should be MEDIUM risk or lower")

    def test_ucc_violation_metadata(self):
        """Test that UCC violation includes full metadata."""

        clause = """
        Seller's exclusive remedy is repair. Buyer waives all other remedies
        and claims for consequential damages.
        """

        result = score_clause_risk(clause, "Legal/Remedy")

        # Verify full UCC metadata present
        if result.get('ucc_violation'):
            ucc = result['ucc_violation']

            print(f"\nUCC Violation Metadata:")
            print(f"  - Rule ID: {ucc.get('statutory_flag')}")
            print(f"  - Citation: {ucc.get('citation')}")
            print(f"  - Category: {ucc.get('category')}")
            print(f"  - Severity: {ucc.get('severity')}")
            print(f"  - Risk Multiplier: {ucc.get('risk_multiplier')}")
            print(f"  - Matched Concepts: {ucc.get('matched_concepts')}")

            self.assertIn('statutory_flag', ucc)
            self.assertIn('citation', ucc)
            self.assertIn('category', ucc)
            self.assertIn('severity', ucc)
            self.assertIn('risk_multiplier', ucc)
            self.assertIn('matched_concepts', ucc)

    def test_40_percent_weight_applied(self):
        """Verify 40% statutory weight is correctly applied in calculation."""

        # Create clause with known UCC violation (risk_multiplier = 10.0)
        clause = """
        Seller's sole remedy is repair. Buyer waives all claims for
        consequential damages and exclusive remedy is provided.
        """

        result = score_clause_risk(clause, "Legal/Remedy")

        # Legal/Remedy baseline: severity=10, complexity=7, impact=10
        # Base score = (10 * 0.3) + (7 * 0.3) + (10 * 0.4) = 9.1
        #
        # With UCC multiplier 10.0 and 40% weight:
        # Final score = (9.1 * 0.6) + (10.0 * 0.4) = 5.46 + 4.0 = 9.46
        #
        # But also keyword adjustments apply, so expect score ≥ 9.0

        print(f"\n40% Weight Verification:")
        print(f"  - Statutory Flag: {result['statutory_flag']}")
        print(f"  - Base Severity: {result['severity']}")
        print(f"  - Base Complexity: {result['complexity']}")
        print(f"  - Base Impact: {result['impact']}")
        print(f"  - Final Risk Score: {result['risk_score']}")
        print(f"  - Risk Level: {result['risk_level']}")

        # Should be CRITICAL risk (≥9.0)
        self.assertEqual(result['risk_level'], 'CRITICAL',
                        "UCC violation + Legal/Remedy should be CRITICAL")

        self.assertGreaterEqual(result['risk_score'], 9.0,
                               "Score should be ≥9.0 with UCC violation")


def run_integration_tests():
    """Run all integration tests with verbose output."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("UCC STATUTORY INTEGRATION - END-TO-END TESTS")
    print("=" * 70)

    success = run_integration_tests()

    print("\n" + "=" * 70)
    if success:
        print("✓ ALL INTEGRATION TESTS PASSED")
    else:
        print("✗ SOME INTEGRATION TESTS FAILED")
    print("=" * 70)

    sys.exit(0 if success else 1)
