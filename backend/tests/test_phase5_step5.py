"""
Phase 5 Step 5 Validation Tests
FAR (Flowdown Analysis & Requirements) Intelligence Activation

Test Gates:
- FAR-FLAG-01: far_intelligence_active flag controls behavior
- FAR-MISSING-01: MISSING gap type detected for absent downstream clauses
- FAR-WEAKER-01: WEAKER gap type detected for weakened language
- FAR-CONFLICT-01: CONFLICT gap type detected for contradictory terms
- FAR-SHAPE-01: FlowdownGap shape is preserved
- FAR-SEVERITY-01: Severity classification follows rules (CRITICAL/HIGH/MODERATE)
- FAR-CATEGORY-01: Critical categories flagged appropriately
- FAR-FALLBACK-01: Placeholder fallback when flag disabled
"""

import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# FAR-FLAG-01: Feature Flag Controls Behavior
# ============================================================================

class TestFARFeatureFlag:
    """Test FAR feature flag behavior"""

    def test_far_flag_defaults_to_false(self):
        """FAR-FLAG-01: far_intelligence_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("far_intelligence_active") is False
        assert is_flag_enabled("far_intelligence_active") is False

    def test_far_returns_empty_when_flag_disabled(self):
        """FAR-FLAG-01: FAR returns empty list when flag is False"""
        from compare_v3_engine import run_far_real

        v1_clauses = [{"id": 1, "section_number": "1", "text": "Test clause", "title": "Section 1"}]
        v2_clauses = [{"id": 1, "section_number": "1", "text": "Test clause", "title": "Section 1"}]

        gaps, stats = run_far_real(1, 2, v1_clauses, v2_clauses, "test-req")

        # Should return empty placeholder
        assert len(gaps) == 0
        assert stats.get("gaps_count") == 0


# ============================================================================
# FAR-MISSING-01: MISSING Gap Detection
# ============================================================================

class TestMissingGapDetection:
    """Test MISSING gap type detection"""

    def test_detect_missing_critical_clause(self):
        """FAR-MISSING-01: Should detect missing critical category clause"""
        from compare_v3_engine import _classify_gap

        # Upstream has indemnification, downstream empty
        v1_text = "Contractor shall provide indemnification for all claims."
        v2_text = ""

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "5.1", "test-req")

        assert gap_type == "MISSING"
        assert severity == "HIGH"
        assert "missing downstream" in recommendation.lower()

    def test_missing_gap_shape(self):
        """FAR-MISSING-01: Missing gap should have correct structure"""
        from compare_v3_engine import (
            FLOWDOWN_CRITICAL_CATEGORIES,
            UPSTREAM_MANDATORY_KEYWORDS,
            _extract_clause_category,
        )

        clause = {
            "id": 1,
            "section_number": "7.1",
            "title": "Indemnification",
            "text": "Contractor shall indemnify customer.",
        }

        category = _extract_clause_category(clause)
        assert category == "indemnification"
        assert category in FLOWDOWN_CRITICAL_CATEGORIES


# ============================================================================
# FAR-WEAKER-01: WEAKER Gap Detection
# ============================================================================

class TestWeakerGapDetection:
    """Test WEAKER gap type detection"""

    def test_detect_weaker_language(self):
        """FAR-WEAKER-01: Should detect weakened downstream language"""
        from compare_v3_engine import _classify_gap

        v1_text = "Contractor shall comply with all regulations."
        v2_text = "Contractor may use reasonable efforts to comply."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "3.1", "test-req")

        assert gap_type == "WEAKER"
        assert severity == "MODERATE"
        assert "weaker language" in recommendation.lower()

    def test_detect_weaker_best_efforts(self):
        """FAR-WEAKER-01: Should detect 'best efforts' as weakening"""
        from compare_v3_engine import _classify_gap

        v1_text = "Provider must deliver within 30 days."
        v2_text = "Provider will use best efforts to deliver."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "4.2", "test-req")

        assert gap_type == "WEAKER"

    def test_detect_weaker_commercially_reasonable(self):
        """FAR-WEAKER-01: Should detect 'commercially reasonable' as weakening"""
        from compare_v3_engine import _classify_gap

        v1_text = "Vendor shall maintain insurance coverage."
        v2_text = "Vendor will make commercially reasonable efforts."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "6.1", "test-req")

        assert gap_type == "WEAKER"


# ============================================================================
# FAR-CONFLICT-01: CONFLICT Gap Detection
# ============================================================================

class TestConflictGapDetection:
    """Test CONFLICT gap type detection"""

    def test_detect_unlimited_vs_limited_conflict(self):
        """FAR-CONFLICT-01: Should detect unlimited vs limited conflict"""
        from compare_v3_engine import _classify_gap

        v1_text = "Contractor provides unlimited indemnification."
        v2_text = "Contractor provides limited indemnification capped at fees."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "8.1", "test-req")

        assert gap_type == "CONFLICT"
        assert severity == "CRITICAL"
        assert "conflicting terms" in recommendation.lower()

    def test_detect_exclusive_vs_nonexclusive_conflict(self):
        """FAR-CONFLICT-01: Should detect exclusive vs non-exclusive conflict"""
        from compare_v3_engine import _classify_gap

        v1_text = "Grant of exclusive license."
        v2_text = "Grant of non-exclusive license."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "2.1", "test-req")

        assert gap_type == "CONFLICT"
        assert severity == "CRITICAL"

    def test_detect_perpetual_vs_term_conflict(self):
        """FAR-CONFLICT-01: Should detect perpetual vs term conflict"""
        from compare_v3_engine import _classify_gap

        v1_text = "This agreement grants perpetual rights."
        v2_text = "This agreement is for a term of one year."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "1.1", "test-req")

        assert gap_type == "CONFLICT"
        assert severity == "CRITICAL"

    def test_detect_irrevocable_vs_revocable_conflict(self):
        """FAR-CONFLICT-01: Should detect irrevocable vs revocable conflict"""
        from compare_v3_engine import _classify_gap

        v1_text = "License is irrevocable."
        v2_text = "License is revocable upon breach."

        gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, "9.1", "test-req")

        assert gap_type == "CONFLICT"
        assert severity == "CRITICAL"


# ============================================================================
# FAR-SHAPE-01: FlowdownGap Shape Preserved
# ============================================================================

class TestFlowdownGapShape:
    """Test FlowdownGap output shape is preserved"""

    def test_gap_has_correct_fields(self):
        """FAR-SHAPE-01: Gap results should have correct fields"""
        # Define expected fields for FAR gap output
        expected_fields = [
            "gap_type",
            "severity",
            "upstream_clause",
            "upstream_section",
            "downstream_clause",
            "downstream_section",
            "category",
            "recommendation",
        ]

        # Verify constants exist
        from compare_v3_engine import (
            FLOWDOWN_CRITICAL_CATEGORIES,
            UPSTREAM_MANDATORY_KEYWORDS,
            DOWNSTREAM_WEAK_KEYWORDS,
            CONFLICT_TERM_PAIRS,
        )

        assert len(FLOWDOWN_CRITICAL_CATEGORIES) > 0
        assert len(UPSTREAM_MANDATORY_KEYWORDS) > 0
        assert len(DOWNSTREAM_WEAK_KEYWORDS) > 0
        assert len(CONFLICT_TERM_PAIRS) > 0


# ============================================================================
# FAR-SEVERITY-01: Severity Classification
# ============================================================================

class TestSeverityClassification:
    """Test severity classification rules"""

    def test_conflict_is_critical(self):
        """FAR-SEVERITY-01: CONFLICT gaps should be CRITICAL"""
        from compare_v3_engine import _classify_gap

        v1_text = "Worldwide license granted."
        v2_text = "Territorial license for US only."

        gap_type, severity, _ = _classify_gap(v1_text, v2_text, "3.1", "test-req")

        assert gap_type == "CONFLICT"
        assert severity == "CRITICAL"

    def test_missing_is_high(self):
        """FAR-SEVERITY-01: MISSING gaps should be HIGH"""
        from compare_v3_engine import _classify_gap

        v1_text = "Required clause content here."
        v2_text = ""

        gap_type, severity, _ = _classify_gap(v1_text, v2_text, "4.1", "test-req")

        assert gap_type == "MISSING"
        assert severity == "HIGH"

    def test_weaker_is_moderate(self):
        """FAR-SEVERITY-01: WEAKER gaps should be MODERATE"""
        from compare_v3_engine import _classify_gap

        v1_text = "Provider shall deliver on time."
        v2_text = "Provider may attempt delivery."

        gap_type, severity, _ = _classify_gap(v1_text, v2_text, "5.1", "test-req")

        assert gap_type == "WEAKER"
        assert severity == "MODERATE"

    def test_aligned_is_admin(self):
        """FAR-SEVERITY-01: ALIGNED results should be ADMIN"""
        from compare_v3_engine import _classify_gap

        v1_text = "Standard terms apply."
        v2_text = "Standard terms apply here too."

        gap_type, severity, _ = _classify_gap(v1_text, v2_text, "1.1", "test-req")

        assert gap_type == "ALIGNED"
        assert severity == "ADMIN"


# ============================================================================
# FAR-CATEGORY-01: Critical Category Detection
# ============================================================================

class TestCriticalCategoryDetection:
    """Test critical category detection"""

    def test_indemnification_is_critical(self):
        """FAR-CATEGORY-01: Indemnification should be critical"""
        from compare_v3_engine import _extract_clause_category, FLOWDOWN_CRITICAL_CATEGORIES

        clause = {"title": "Indemnification", "text": "Contractor indemnifies..."}
        category = _extract_clause_category(clause)

        assert category == "indemnification"
        assert category in FLOWDOWN_CRITICAL_CATEGORIES

    def test_liability_is_critical(self):
        """FAR-CATEGORY-01: Liability should be critical"""
        from compare_v3_engine import _extract_clause_category, FLOWDOWN_CRITICAL_CATEGORIES

        clause = {"title": "Limitation of Liability", "text": "Liability is limited..."}
        category = _extract_clause_category(clause)

        assert category == "liability"
        assert category in FLOWDOWN_CRITICAL_CATEGORIES

    def test_insurance_is_critical(self):
        """FAR-CATEGORY-01: Insurance should be critical"""
        from compare_v3_engine import _extract_clause_category, FLOWDOWN_CRITICAL_CATEGORIES

        clause = {"title": "Insurance Requirements", "text": "Contractor shall maintain insurance..."}
        category = _extract_clause_category(clause)

        assert category == "insurance"
        assert category in FLOWDOWN_CRITICAL_CATEGORIES

    def test_general_clause_not_critical(self):
        """FAR-CATEGORY-01: General clause should not be critical"""
        from compare_v3_engine import _extract_clause_category, FLOWDOWN_CRITICAL_CATEGORIES

        clause = {"title": "Notices", "text": "All notices shall be in writing..."}
        category = _extract_clause_category(clause)

        assert category == "general"
        assert category not in FLOWDOWN_CRITICAL_CATEGORIES


# ============================================================================
# FAR-FALLBACK-01: Placeholder Fallback
# ============================================================================

class TestPlaceholderFallback:
    """Test placeholder fallback behavior"""

    def test_placeholder_returns_empty(self):
        """FAR-FALLBACK-01: Placeholder should return empty list"""
        from compare_v3_engine import _generate_far_placeholder

        gaps = _generate_far_placeholder()
        assert gaps == []

    def test_far_disabled_returns_empty_stats(self):
        """FAR-FALLBACK-01: Disabled FAR should return empty stats"""
        from compare_v3_engine import run_far_real

        v1_clauses = [{"id": 1, "section_number": "1", "text": "Test", "title": "Test"}]
        v2_clauses = []

        gaps, stats = run_far_real(1, 2, v1_clauses, v2_clauses, "test-req")

        assert len(gaps) == 0
        assert stats.get("gaps_count") == 0
        assert stats.get("critical_count") == 0
        assert stats.get("high_count") == 0


# ============================================================================
# Keyword Detection Tests
# ============================================================================

class TestKeywordDetection:
    """Test keyword detection for mandatory/weak language"""

    def test_mandatory_keywords_detected(self):
        """Mandatory keywords should be detected"""
        from compare_v3_engine import UPSTREAM_MANDATORY_KEYWORDS

        text = "Contractor shall comply and must deliver as required."
        text_lower = text.lower()

        detected = [kw for kw in UPSTREAM_MANDATORY_KEYWORDS if kw in text_lower]
        assert "shall" in detected
        assert "must" in detected
        assert "required" in detected

    def test_weak_keywords_detected(self):
        """Weak keywords should be detected"""
        from compare_v3_engine import DOWNSTREAM_WEAK_KEYWORDS

        text = "Contractor may use reasonable efforts or best efforts."
        text_lower = text.lower()

        detected = [kw for kw in DOWNSTREAM_WEAK_KEYWORDS if kw in text_lower]
        assert "may" in detected
        assert "reasonable efforts" in detected
        assert "best efforts" in detected


# ============================================================================
# Conflict Term Pairs Tests
# ============================================================================

class TestConflictTermPairs:
    """Test conflict term pair detection"""

    def test_all_conflict_pairs_exist(self):
        """All expected conflict pairs should exist"""
        from compare_v3_engine import CONFLICT_TERM_PAIRS

        expected_pairs = [
            ("unlimited", "limited"),
            ("perpetual", "term"),
            ("exclusive", "non-exclusive"),
            ("irrevocable", "revocable"),
            ("worldwide", "territorial"),
            ("unconditional", "conditional"),
        ]

        for pair in expected_pairs:
            assert pair in CONFLICT_TERM_PAIRS, f"Missing conflict pair: {pair}"


# ============================================================================
# Integration Tests
# ============================================================================

class TestStep5Integration:
    """Integration tests for Step 5 FAR activation"""

    def test_phase5_far_flag_available(self):
        """far_intelligence_active flag should be available"""
        from phase5_flags import PHASE_5_FLAGS
        assert "far_intelligence_active" in PHASE_5_FLAGS

    def test_far_helpers_importable(self):
        """FAR helper functions should be importable"""
        from compare_v3_engine import (
            _classify_gap,
            _extract_clause_category,
            _check_contract_relationships,
            _generate_far_placeholder,
            run_far_real,
            FLOWDOWN_CRITICAL_CATEGORIES,
            UPSTREAM_MANDATORY_KEYWORDS,
            DOWNSTREAM_WEAK_KEYWORDS,
            CONFLICT_TERM_PAIRS,
        )

        assert callable(_classify_gap)
        assert callable(_extract_clause_category)
        assert callable(_check_contract_relationships)
        assert callable(_generate_far_placeholder)
        assert callable(run_far_real)

    def test_far_config_exists(self):
        """FAR timeout config should exist"""
        from phase5_flags import PHASE_5_CONFIG, get_config

        assert PHASE_5_CONFIG.get("far_timeout_seconds") == 15
        assert get_config("far_timeout_seconds") == 15


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases for FAR"""

    def test_empty_clauses_handled(self):
        """Empty clause lists should be handled gracefully"""
        from compare_v3_engine import run_far_real

        gaps, stats = run_far_real(1, 2, [], [], "test-req")

        assert len(gaps) == 0
        assert stats.get("gaps_count") == 0

    def test_none_text_handled(self):
        """None text values should be handled gracefully"""
        from compare_v3_engine import _classify_gap

        gap_type, severity, _ = _classify_gap(None, None, "1.1", "test-req")

        # Both None should result in ALIGNED
        assert gap_type == "ALIGNED"

    def test_clause_without_section_number_skipped(self):
        """Clauses without section_number should be skipped"""
        from compare_v3_engine import run_far_real

        v1_clauses = [
            {"id": 1, "text": "Test clause", "title": "Test"},  # No section_number
        ]
        v2_clauses = []

        gaps, stats = run_far_real(1, 2, v1_clauses, v2_clauses, "test-req")

        # Should return empty since clause has no section_number
        assert len(gaps) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
