"""
Unit Tests for UCC Statutory Matcher Module
Tests UCC rule loading, matching logic, and risk score integration.

Created: 2026-01-18
Version: 1.0
"""

import unittest
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from ucc_statutory_matcher import (
    load_ucc_rules,
    match_ucc_violations,
    classify_ucc_severity,
    detect_ucc_violation,
    UCCRule,
    UCCMatch
)
from cce_plus_integration import calculate_risk_score


class TestUCCRuleLoading(unittest.TestCase):
    """Test UCC rule loading from JSON."""

    def test_load_ucc_rules(self):
        """Verify rules loaded from UCC_Statutory_Logic_v2.json."""
        rules = load_ucc_rules()

        # Should have rules loaded
        self.assertGreater(len(rules), 0, "No UCC rules loaded")

        # Verify structure of first rule
        first_rule = rules[0]
        self.assertIsInstance(first_rule, UCCRule)
        self.assertTrue(hasattr(first_rule, 'rule_id'))
        self.assertTrue(hasattr(first_rule, 'trigger_concepts'))
        self.assertTrue(hasattr(first_rule, 'risk_multiplier'))

    def test_rule_structure(self):
        """Validate UCCRule dataclass structure."""
        rules = load_ucc_rules()

        for rule in rules:
            # Required fields
            self.assertIsNotNone(rule.rule_id)
            self.assertIsNotNone(rule.title)
            self.assertIsNotNone(rule.citation)
            self.assertIsNotNone(rule.category)
            self.assertIsInstance(rule.trigger_concepts, list)
            self.assertIsInstance(rule.risk_multiplier, float)
            self.assertIn(rule.severity, ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])

            # Risk multiplier should be in reasonable range
            self.assertGreaterEqual(rule.risk_multiplier, 1.0)
            self.assertLessEqual(rule.risk_multiplier, 10.0)


class TestTriggerConceptMatching(unittest.TestCase):
    """Test trigger concept matching logic."""

    def setUp(self):
        """Load UCC rules for testing."""
        self.rules = load_ucc_rules()

    def test_match_consequential_damages(self):
        """Test matching UCC-2-719 consequential damages exclusion."""
        clause_text = """
        Seller's sole remedy is repair or replacement. Buyer expressly waives
        all claims for consequential damages, including lost profits.
        """

        match = match_ucc_violations(clause_text, None, self.rules)

        self.assertIsNotNone(match, "Should match UCC-2-719")
        self.assertIsInstance(match, UCCMatch)
        self.assertIn("UCC-2-719", match.rule_id)
        self.assertGreater(len(match.matched_concepts), 0)
        self.assertEqual(match.risk_multiplier, 10.0)

    def test_match_prepayment_lock(self):
        """Test matching UCC-2-719 prepayment scenario."""
        clause_text = """
        Full prepayment of $100,000 is required before work commences.
        Payment is non-refundable under any circumstances.
        """

        match = match_ucc_violations(clause_text, None, self.rules)

        self.assertIsNotNone(match, "Should match UCC-2-719 or similar")
        self.assertGreater(match.risk_multiplier, 5.0)

    def test_match_gross_negligence_waiver(self):
        """Test matching UCC-2-302 unconscionable clause."""
        clause_text = """
        Vendor shall not be liable for any damages whatsoever, including
        those arising from gross negligence or willful misconduct.
        """

        match = match_ucc_violations(clause_text, None, self.rules)

        self.assertIsNotNone(match, "Should match UCC-2-302")
        self.assertEqual(match.risk_multiplier, 10.0)
        self.assertEqual(match.severity, "CRITICAL")

    def test_no_match_standard_clause(self):
        """Test that standard clauses don't trigger false positives."""
        clause_text = """
        The Parties agree to negotiate in good faith. This Agreement shall
        be governed by Delaware law. Both parties shall cooperate reasonably.
        """

        match = match_ucc_violations(clause_text, None, self.rules)

        # Should not match (or match low severity only)
        if match:
            self.assertLess(match.risk_multiplier, 5.0, "Standard clause should not trigger high-severity match")

    def test_match_as_is_disclaimer(self):
        """Test matching UCC-2-314 AS IS warranty disclaimer."""
        clause_text = """
        Equipment is sold AS IS, WITH ALL FAULTS. Seller disclaims all
        warranties of merchantability and fitness for a particular purpose.
        """

        match = match_ucc_violations(clause_text, None, self.rules)

        self.assertIsNotNone(match, "Should match UCC-2-314 or UCC-2-316")
        self.assertGreaterEqual(match.risk_multiplier, 8.0)


class TestRiskScoreIntegration(unittest.TestCase):
    """Test risk score calculation with statutory weight."""

    def test_risk_score_no_violation(self):
        """Test base score calculation without statutory violation."""
        score = calculate_risk_score(
            severity=7,
            complexity=5,
            impact=8,
            statutory_multiplier=None  # No violation
        )

        # Base formula: (7 * 0.3) + (5 * 0.3) + (8 * 0.4) = 6.8
        self.assertEqual(score, 6.8)

    def test_risk_score_with_critical_violation(self):
        """Test score escalation with critical UCC violation (multiplier 10.0)."""
        base_severity = 7
        base_complexity = 5
        base_impact = 8

        # Base score
        base_score = calculate_risk_score(base_severity, base_complexity, base_impact)
        self.assertEqual(base_score, 6.8)

        # With statutory multiplier 10.0
        score_with_ucc = calculate_risk_score(
            base_severity,
            base_complexity,
            base_impact,
            statutory_multiplier=10.0,
            statutory_weight=0.4
        )

        # Expected: (6.8 * 0.6) + (10.0 * 0.4) = 4.08 + 4.0 = 8.08
        self.assertEqual(score_with_ucc, 8.1)  # Rounded to 1 decimal
        self.assertGreater(score_with_ucc, base_score, "Score should escalate with statutory violation")

    def test_risk_score_escalation_medium_to_high(self):
        """Test score escalation from MEDIUM to HIGH risk."""
        # Base MEDIUM risk clause
        base_score = calculate_risk_score(
            severity=3,
            complexity=2,
            impact=4
        )

        # Base: (3 * 0.3) + (2 * 0.3) + (4 * 0.4) = 3.1 (LOW)
        self.assertEqual(base_score, 3.1)

        # With UCC multiplier 8.5
        score_with_ucc = calculate_risk_score(
            severity=3,
            complexity=2,
            impact=4,
            statutory_multiplier=8.5,
            statutory_weight=0.4
        )

        # Expected: (3.1 * 0.6) + (8.5 * 0.4) = 1.86 + 3.4 = 5.26
        self.assertAlmostEqual(score_with_ucc, 5.3, delta=0.1)  # Rounded to 1 decimal
        self.assertGreaterEqual(score_with_ucc, 5.0, "Should escalate to MEDIUM risk (≥5.0)")

    def test_statutory_weight_custom(self):
        """Test custom statutory weight (e.g., 30% instead of 40%)."""
        score_40pct = calculate_risk_score(
            severity=5,
            complexity=5,
            impact=5,
            statutory_multiplier=10.0,
            statutory_weight=0.4
        )

        score_30pct = calculate_risk_score(
            severity=5,
            complexity=5,
            impact=5,
            statutory_multiplier=10.0,
            statutory_weight=0.3
        )

        # 40% weight should produce higher score than 30% weight
        self.assertGreater(score_40pct, score_30pct)


class TestSeverityClassification(unittest.TestCase):
    """Test UCC severity classification."""

    def test_classify_critical(self):
        """Test CRITICAL severity classification."""
        severity = classify_ucc_severity(10.0)
        self.assertEqual(severity, "CRITICAL")

        severity = classify_ucc_severity(9.5)
        self.assertEqual(severity, "CRITICAL")

    def test_classify_high(self):
        """Test HIGH severity classification."""
        severity = classify_ucc_severity(9.0)
        self.assertEqual(severity, "HIGH")

        severity = classify_ucc_severity(8.0)
        self.assertEqual(severity, "HIGH")

    def test_classify_medium(self):
        """Test MEDIUM severity classification."""
        severity = classify_ucc_severity(7.0)
        self.assertEqual(severity, "MEDIUM")

        severity = classify_ucc_severity(5.0)
        self.assertEqual(severity, "MEDIUM")

    def test_classify_low(self):
        """Test LOW severity classification."""
        severity = classify_ucc_severity(4.0)
        self.assertEqual(severity, "LOW")


class TestDetectUCCViolation(unittest.TestCase):
    """Test high-level detect_ucc_violation() function."""

    def test_detect_violation_returns_dict(self):
        """Test that detect_ucc_violation returns dict with expected keys."""
        clause_text = "Sole remedy is repair. No liability for consequential damages."

        result = detect_ucc_violation(clause_text)

        if result:  # If violation detected
            self.assertIsInstance(result, dict)
            self.assertIn("statutory_flag", result)
            self.assertIn("citation", result)
            self.assertIn("severity", result)
            self.assertIn("risk_multiplier", result)
            self.assertIn("matched_concepts", result)
            self.assertIn("category", result)

    def test_detect_violation_none_for_safe_clause(self):
        """Test that safe clauses return None."""
        clause_text = "The parties shall cooperate in good faith."

        result = detect_ucc_violation(clause_text)

        # Should return None or low-severity match only
        if result:
            self.assertLess(result["risk_multiplier"], 5.0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_clause_text(self):
        """Test handling of empty clause text."""
        rules = load_ucc_rules()
        match = match_ucc_violations("", None, rules)
        self.assertIsNone(match, "Empty text should return None")

    def test_none_clause_text(self):
        """Test handling of None clause text."""
        rules = load_ucc_rules()
        match = match_ucc_violations(None, None, rules)
        self.assertIsNone(match, "None text should return None")

    def test_empty_rules_list(self):
        """Test matching with empty rules list."""
        match = match_ucc_violations("Some clause text", None, [])
        self.assertIsNone(match, "Empty rules should return None")

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        clause_upper = "SOLE REMEDY IS REPAIR. EXCLUSIVE REMEDY."
        clause_lower = "sole remedy is repair. exclusive remedy."
        clause_mixed = "Sole Remedy is Repair. Exclusive Remedy."

        rules = load_ucc_rules()

        match_upper = match_ucc_violations(clause_upper, None, rules)
        match_lower = match_ucc_violations(clause_lower, None, rules)
        match_mixed = match_ucc_violations(clause_mixed, None, rules)

        # All should match the same rule
        if match_upper:
            self.assertIsNotNone(match_lower)
            self.assertIsNotNone(match_mixed)
            self.assertEqual(match_upper.rule_id, match_lower.rule_id)
            self.assertEqual(match_upper.rule_id, match_mixed.rule_id)


def run_tests():
    """Run all tests with verbose output."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
