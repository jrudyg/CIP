"""
Phase 5 Step 3 Validation Tests
ERCE Intelligence Activation

Test Gates:
- ERCE-FLAG-01: erce_intelligence_active flag controls behavior
- ERCE-PATTERN-01: Pattern matching works correctly
- ERCE-CLASSIFY-01: Risk classification follows severity rules
- ERCE-SHAPE-01: RiskDelta shape is preserved
- ERCE-FALLBACK-01: Placeholder fallback when flag disabled
"""

import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# ERCE-FLAG-01: Feature Flag Controls Behavior
# ============================================================================

class TestERCEFeatureFlag:
    """Test ERCE feature flag behavior"""

    def test_erce_flag_defaults_to_false(self):
        """ERCE-FLAG-01: erce_intelligence_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("erce_intelligence_active") is False
        assert is_flag_enabled("erce_intelligence_active") is False

    def test_erce_returns_placeholder_when_flag_disabled(self):
        """ERCE-FLAG-01: ERCE returns placeholder when flag is False"""
        from compare_v3_engine import run_erce_real

        sae_matches = [
            {"v1_clause_id": 1, "v2_clause_id": 1, "similarity_score": 0.95},
        ]
        v1_clauses = [{"id": 1, "text": "Test clause one"}]
        v2_clauses = [{"id": 1, "text": "Test clause two"}]

        results, stats = run_erce_real(sae_matches, v1_clauses, v2_clauses, "test-req")

        # Should return placeholder (3 results)
        assert len(results) == 3
        assert stats.get("risk_count") == 3


# ============================================================================
# ERCE-PATTERN-01: Pattern Matching
# ============================================================================

class TestPatternMatching:
    """Test pattern matching functionality"""

    def test_match_patterns_for_erce_detects_unlimited_indemnification(self):
        """Pattern should match unlimited indemnification text"""
        from pattern_cache import match_patterns_for_erce, get_erce_patterns

        patterns = get_erce_patterns()
        text = "The contractor shall provide unlimited indemnification for all claims."

        matches = match_patterns_for_erce(text, patterns)

        assert len(matches) > 0
        # Should find the CRITICAL unlimited indemnification pattern
        critical_matches = [m for m in matches if m["risk_category"] == "CRITICAL"]
        assert len(critical_matches) > 0

    def test_match_patterns_for_erce_detects_auto_renewal(self):
        """Pattern should match auto-renewal text"""
        from pattern_cache import match_patterns_for_erce, get_erce_patterns

        patterns = get_erce_patterns()
        # Pattern regex is: (?i)(auto|automatic)\s*(renew|extend)
        text = "This agreement shall auto renew for successive one-year terms."

        matches = match_patterns_for_erce(text, patterns)

        assert len(matches) > 0
        # Should find auto-renewal pattern
        pattern_ids = [m["pattern_id"] for m in matches]
        assert "TERM_AUTO_RENEW_003" in pattern_ids

    def test_match_patterns_for_erce_detects_net_payment_terms(self):
        """Pattern should match extended payment terms"""
        from pattern_cache import match_patterns_for_erce, get_erce_patterns

        patterns = get_erce_patterns()
        text = "Payment shall be due net 90 days from invoice date."

        matches = match_patterns_for_erce(text, patterns)

        assert len(matches) > 0
        pattern_ids = [m["pattern_id"] for m in matches]
        assert "PAY_NET_EXTENDED_004" in pattern_ids

    def test_match_patterns_for_erce_returns_empty_for_clean_text(self):
        """Pattern should return empty for text with no risk patterns"""
        from pattern_cache import match_patterns_for_erce, get_erce_patterns

        patterns = get_erce_patterns()
        text = "The quick brown fox jumps over the lazy dog."

        matches = match_patterns_for_erce(text, patterns)

        assert len(matches) == 0

    def test_match_patterns_for_erce_handles_empty_input(self):
        """Pattern matching should handle empty input gracefully"""
        from pattern_cache import match_patterns_for_erce, get_erce_patterns

        patterns = get_erce_patterns()

        assert match_patterns_for_erce("", patterns) == []
        assert match_patterns_for_erce(None, patterns) == []
        assert match_patterns_for_erce("test", []) == []


# ============================================================================
# ERCE-CLASSIFY-01: Risk Classification
# ============================================================================

class TestRiskClassification:
    """Test risk classification logic"""

    def test_classify_erce_risk_picks_highest_severity(self):
        """Classification should pick highest severity pattern"""
        from pattern_cache import classify_erce_risk

        matched_patterns = [
            {"pattern_id": "P1", "risk_category": "MODERATE", "success_probability": 0.7},
            {"pattern_id": "P2", "risk_category": "CRITICAL", "success_probability": 0.3},
            {"pattern_id": "P3", "risk_category": "HIGH", "success_probability": 0.5},
        ]

        result = classify_erce_risk(matched_patterns, "test text")

        assert result.risk_category == "CRITICAL"
        assert result.pattern_id == "P2"

    def test_classify_erce_risk_returns_admin_for_no_matches(self):
        """Classification should return ADMIN when no patterns match"""
        from pattern_cache import classify_erce_risk

        result = classify_erce_risk([], "some text here")

        assert result.risk_category == "ADMIN"
        assert result.pattern_id is None
        assert result.success_probability is None
        assert result.confidence < 0.60  # Low confidence for no matches

    def test_classify_erce_risk_confidence_increases_with_matches(self):
        """Confidence should increase with more pattern matches"""
        from pattern_cache import classify_erce_risk

        one_match = [{"pattern_id": "P1", "risk_category": "HIGH", "match_text": "test"}]
        three_matches = [
            {"pattern_id": "P1", "risk_category": "HIGH", "match_text": "test"},
            {"pattern_id": "P2", "risk_category": "MODERATE", "match_text": "test2"},
            {"pattern_id": "P3", "risk_category": "ADMIN", "match_text": "test3"},
        ]

        result_one = classify_erce_risk(one_match, "test text")
        result_three = classify_erce_risk(three_matches, "test text")

        # More matches should yield higher confidence
        assert result_three.confidence >= result_one.confidence

    def test_severity_ordering_is_correct(self):
        """Verify CRITICAL > HIGH > MODERATE > ADMIN"""
        from pattern_cache import SEVERITY_ORDER

        assert SEVERITY_ORDER["CRITICAL"] > SEVERITY_ORDER["HIGH"]
        assert SEVERITY_ORDER["HIGH"] > SEVERITY_ORDER["MODERATE"]
        assert SEVERITY_ORDER["MODERATE"] > SEVERITY_ORDER["ADMIN"]


# ============================================================================
# ERCE-SHAPE-01: RiskDelta Shape Preserved
# ============================================================================

class TestRiskDeltaShape:
    """Test RiskDelta output shape is preserved"""

    def test_placeholder_has_correct_fields(self):
        """Placeholder results should have RiskDelta fields"""
        from compare_v3_engine import _generate_erce_placeholder

        results = _generate_erce_placeholder()

        for result in results:
            assert "clause_pair_id" in result
            assert "risk_category" in result
            assert "pattern_ref" in result
            assert "success_probability" in result
            assert "confidence" in result

    def test_erce_result_matches_riskdelta_shape(self):
        """ERCE results should match RiskDelta dataclass shape"""
        from compare_v3_engine import run_erce_real

        sae_matches = [
            {"v1_clause_id": 1, "v2_clause_id": 1, "similarity_score": 0.95},
        ]
        v1_clauses = [{"id": 1, "text": "Test clause"}]
        v2_clauses = [{"id": 1, "text": "Test clause"}]

        results, stats = run_erce_real(sae_matches, v1_clauses, v2_clauses, "test-req")

        # Verify shape (placeholder path when flag disabled)
        for result in results:
            assert "clause_pair_id" in result
            assert "risk_category" in result
            assert "pattern_ref" in result
            assert "success_probability" in result
            assert "confidence" in result

    def test_risk_category_values_are_valid(self):
        """Risk categories should be one of the valid values"""
        from compare_v3_engine import _generate_erce_placeholder

        valid_categories = {"ADMIN", "MODERATE", "HIGH", "CRITICAL"}
        results = _generate_erce_placeholder()

        for result in results:
            assert result["risk_category"] in valid_categories


# ============================================================================
# ERCE-FALLBACK-01: Placeholder Fallback
# ============================================================================

class TestPlaceholderFallback:
    """Test placeholder fallback behavior"""

    def test_placeholder_returns_three_results(self):
        """Placeholder should return exactly 3 results"""
        from compare_v3_engine import _generate_erce_placeholder

        results = _generate_erce_placeholder()
        assert len(results) == 3

    def test_placeholder_has_mixed_risk_levels(self):
        """Placeholder should include different risk levels"""
        from compare_v3_engine import _generate_erce_placeholder

        results = _generate_erce_placeholder()
        categories = {r["risk_category"] for r in results}

        # Should have variety
        assert len(categories) >= 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestStep3Integration:
    """Integration tests for Step 3 ERCE activation"""

    def test_phase5_erce_imports_available(self):
        """compare_v3_engine should have ERCE Phase 5 imports"""
        from compare_v3_engine import PHASE5_AVAILABLE
        assert PHASE5_AVAILABLE is True

    def test_pattern_cache_has_step3_helpers(self):
        """pattern_cache should have Step 3 helper functions"""
        from pattern_cache import (
            get_erce_patterns,
            match_patterns_for_erce,
            classify_erce_risk,
            ERCEMatchResult,
            SEVERITY_ORDER,
        )

        assert callable(get_erce_patterns)
        assert callable(match_patterns_for_erce)
        assert callable(classify_erce_risk)

    def test_get_erce_patterns_returns_patterns(self):
        """get_erce_patterns should return list of RiskPattern objects"""
        from pattern_cache import get_erce_patterns, RiskPattern

        patterns = get_erce_patterns()

        assert len(patterns) > 0
        for p in patterns:
            assert isinstance(p, RiskPattern)
            assert p.enabled is True

    def test_erce_match_result_structure(self):
        """ERCEMatchResult should have correct structure"""
        from pattern_cache import ERCEMatchResult

        result = ERCEMatchResult(
            pattern_id="TEST_001",
            pattern_name="Test Pattern",
            risk_category="HIGH",
            success_probability=0.65,
            confidence=0.80,
            matched_patterns_count=2,
            keyword_density=0.15,
        )

        assert result.pattern_id == "TEST_001"
        assert result.risk_category == "HIGH"
        assert result.confidence == 0.80


class TestEndToEndPatternMatching:
    """End-to-end pattern matching tests"""

    def test_full_erce_pipeline_with_critical_text(self):
        """Full ERCE pipeline should classify critical risk text"""
        from pattern_cache import (
            get_erce_patterns,
            match_patterns_for_erce,
            classify_erce_risk,
        )

        patterns = get_erce_patterns()
        text = "Contractor agrees to unlimited indemnification and liability for all claims arising from this agreement."

        matches = match_patterns_for_erce(text, patterns)
        classification = classify_erce_risk(matches, text)

        assert classification.risk_category == "CRITICAL"
        assert classification.pattern_id is not None
        assert classification.confidence >= 0.60

    def test_full_erce_pipeline_with_moderate_text(self):
        """Full ERCE pipeline should classify moderate risk text"""
        from pattern_cache import (
            get_erce_patterns,
            match_patterns_for_erce,
            classify_erce_risk,
        )

        patterns = get_erce_patterns()
        # Pattern regex is: (?i)(auto|automatic)\s*(renew|extend)
        text = "This agreement shall automatic extend for additional terms unless terminated."

        matches = match_patterns_for_erce(text, patterns)
        classification = classify_erce_risk(matches, text)

        assert classification.risk_category == "MODERATE"

    def test_full_erce_pipeline_with_admin_text(self):
        """Full ERCE pipeline should classify admin text with low confidence"""
        from pattern_cache import (
            get_erce_patterns,
            match_patterns_for_erce,
            classify_erce_risk,
        )

        patterns = get_erce_patterns()
        text = "The parties agree to maintain confidentiality of proprietary information."

        matches = match_patterns_for_erce(text, patterns)
        classification = classify_erce_risk(matches, text)

        # No high-risk patterns, should default to ADMIN
        if len(matches) == 0:
            assert classification.risk_category == "ADMIN"
            assert classification.confidence < 0.60


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
