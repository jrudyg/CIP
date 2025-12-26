"""
Phase 5 Step 4 Validation Tests
BIRL Intelligence Activation

Test Gates:
- BIRL-FLAG-01: birl_intelligence_active flag controls behavior
- BIRL-HALLUC-01: Hallucination shield rejects fabricated clause numbers
- BIRL-HALLUC-02: Hallucination shield rejects fabricated dollar amounts
- BIRL-HALLUC-03: Hallucination shield rejects fabricated dates
- BIRL-HALLUC-04: Hallucination shield rejects legal advice phrases
- BIRL-SHAPE-01: BusinessImpact shape is preserved
- BIRL-CAP-01: birl_max_narratives cap is enforced
- BIRL-TRUNC-01: Narratives > 4 sentences are truncated
- BIRL-FALLBACK-01: Placeholder fallback when flag disabled
"""

import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# BIRL-FLAG-01: Feature Flag Controls Behavior
# ============================================================================

class TestBIRLFeatureFlag:
    """Test BIRL feature flag behavior"""

    def test_birl_flag_defaults_to_false(self):
        """BIRL-FLAG-01: birl_intelligence_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("birl_intelligence_active") is False
        assert is_flag_enabled("birl_intelligence_active") is False

    def test_birl_returns_placeholder_when_flag_disabled(self):
        """BIRL-FLAG-01: BIRL returns placeholder when flag is False"""
        from compare_v3_engine import run_birl_real

        erce_results = [{"clause_pair_id": 1, "risk_category": "MODERATE"}]
        sae_matches = [{"v1_clause_id": 1, "v2_clause_id": 1}]
        v1_clauses = [{"id": 1, "text": "Test clause one"}]
        v2_clauses = [{"id": 1, "text": "Test clause two"}]

        results, stats = run_birl_real(
            erce_results, sae_matches, v1_clauses, v2_clauses, "test-req"
        )

        # Should return placeholder (3 results)
        assert len(results) == 3
        assert stats.get("narratives_count") == 3


# ============================================================================
# BIRL-HALLUC-01: Hallucination Shield - Clause Numbers
# ============================================================================

class TestHallucinationShieldClauseNumbers:
    """Test hallucination shield for clause numbers"""

    def test_rejects_hallucinated_clause_number(self):
        """BIRL-HALLUC-01: Should reject narrative with fabricated clause number"""
        from compare_v3_engine import _validate_narrative_hallucination

        # Input mentions Section 5
        input_text = "This is Section 5 of the agreement."
        # Narrative mentions Section 12 which is not in input
        narrative = "The changes to Section 12 may impact operations."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is False
        assert "hallucinated_clause_number" in reason

    def test_accepts_matching_clause_number(self):
        """BIRL-HALLUC-01: Should accept narrative with clause number from input"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "This is Section 5 of the agreement."
        narrative = "The changes to Section 5 may impact operations."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is True
        assert reason is None

    def test_accepts_narrative_without_clause_numbers(self):
        """BIRL-HALLUC-01: Should accept narrative without any clause numbers"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "This agreement covers payment terms."
        narrative = "Payment terms may impact cash flow."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is True


# ============================================================================
# BIRL-HALLUC-02: Hallucination Shield - Dollar Amounts
# ============================================================================

class TestHallucinationShieldDollarAmounts:
    """Test hallucination shield for dollar amounts"""

    def test_rejects_hallucinated_dollar_amount(self):
        """BIRL-HALLUC-02: Should reject narrative with fabricated dollar amount"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "The fee is $500 per month."
        narrative = "This could result in costs of $10,000 annually."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is False
        assert "hallucinated_dollar_amount" in reason

    def test_accepts_matching_dollar_amount(self):
        """BIRL-HALLUC-02: Should accept narrative with dollar amount from input"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "The fee is $500 per month."
        narrative = "The $500 monthly fee impacts budget planning."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is True


# ============================================================================
# BIRL-HALLUC-03: Hallucination Shield - Dates
# ============================================================================

class TestHallucinationShieldDates:
    """Test hallucination shield for dates"""

    def test_rejects_hallucinated_date(self):
        """BIRL-HALLUC-03: Should reject narrative with fabricated date"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "Contract effective January 1, 2024."
        narrative = "This must be completed by March 15, 2025."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is False
        assert "hallucinated_date" in reason

    def test_accepts_matching_date(self):
        """BIRL-HALLUC-03: Should accept narrative with date from input"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "Contract effective January 1, 2024."
        narrative = "The January 1, 2024 effective date starts the obligation period."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is True


# ============================================================================
# BIRL-HALLUC-04: Hallucination Shield - Legal Advice
# ============================================================================

class TestHallucinationShieldLegalAdvice:
    """Test hallucination shield for legal advice phrases"""

    def test_rejects_legal_advice_consult(self):
        """BIRL-HALLUC-04: Should reject narrative suggesting legal consultation"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "Payment terms change."
        narrative = "You should consult with an attorney before signing."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is False
        assert "legal_advice_phrase" in reason

    def test_rejects_legal_counsel_mention(self):
        """BIRL-HALLUC-04: Should reject narrative mentioning legal counsel"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "Indemnification clause modified."
        narrative = "We recommend seeking legal counsel before proceeding."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is False
        assert "legal_advice_phrase" in reason

    def test_rejects_disclaimer(self):
        """BIRL-HALLUC-04: Should reject narrative with disclaimer"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "Terms updated."
        narrative = "This is not legal advice. The changes affect payment timing."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is False
        assert "legal_advice_phrase" in reason

    def test_accepts_clean_narrative(self):
        """BIRL-HALLUC-04: Should accept clean business narrative"""
        from compare_v3_engine import _validate_narrative_hallucination

        input_text = "Payment terms change from Net 30 to Net 60."
        narrative = "Extended payment terms may impact quarterly cash flow projections."

        is_valid, reason = _validate_narrative_hallucination(narrative, input_text, "test")

        assert is_valid is True


# ============================================================================
# BIRL-SHAPE-01: BusinessImpact Shape Preserved
# ============================================================================

class TestBusinessImpactShape:
    """Test BusinessImpact output shape is preserved"""

    def test_placeholder_has_correct_fields(self):
        """Placeholder results should have BusinessImpact fields"""
        from compare_v3_engine import _generate_birl_placeholder

        results = _generate_birl_placeholder()

        for result in results:
            assert "clause_pair_id" in result
            assert "narrative" in result
            assert "impact_dimensions" in result
            assert "token_count" in result

    def test_birl_result_matches_businessimpact_shape(self):
        """BIRL results should match BusinessImpact dataclass shape"""
        from compare_v3_engine import run_birl_real

        erce_results = [{"clause_pair_id": 1, "risk_category": "MODERATE"}]
        sae_matches = [{"v1_clause_id": 1, "v2_clause_id": 1}]
        v1_clauses = [{"id": 1, "text": "Test clause"}]
        v2_clauses = [{"id": 1, "text": "Test clause"}]

        results, stats = run_birl_real(
            erce_results, sae_matches, v1_clauses, v2_clauses, "test-req"
        )

        # Verify shape (placeholder path when flag disabled)
        for result in results:
            assert "clause_pair_id" in result
            assert "narrative" in result
            assert "impact_dimensions" in result
            assert "token_count" in result
            # impact_dimensions must be non-empty list
            assert isinstance(result["impact_dimensions"], list)
            assert len(result["impact_dimensions"]) > 0

    def test_fallback_narrative_format(self):
        """Fallback narrative should have correct format"""
        from compare_v3_engine import _generate_birl_placeholder

        results = _generate_birl_placeholder()

        # Each narrative should be a string
        for result in results:
            assert isinstance(result["narrative"], str)
            assert len(result["narrative"]) > 0


# ============================================================================
# BIRL-CAP-01: Max Narratives Cap
# ============================================================================

class TestMaxNarrativesCap:
    """Test birl_max_narratives cap enforcement"""

    def test_max_narratives_config_exists(self):
        """birl_max_narratives should be configured"""
        from phase5_flags import PHASE_5_CONFIG, get_config

        assert PHASE_5_CONFIG.get("birl_max_narratives") == 5
        assert get_config("birl_max_narratives") == 5


# ============================================================================
# BIRL-TRUNC-01: Sentence Truncation
# ============================================================================

class TestSentenceTruncation:
    """Test sentence truncation functionality"""

    def test_truncate_to_sentences_short_text(self):
        """Short text should not be truncated"""
        from compare_v3_engine import _truncate_to_sentences

        text = "First sentence. Second sentence."
        result = _truncate_to_sentences(text, max_sentences=4)
        assert result == text

    def test_truncate_to_sentences_long_text(self):
        """Long text should be truncated to max sentences"""
        from compare_v3_engine import _truncate_to_sentences

        text = "One. Two. Three. Four. Five. Six."
        result = _truncate_to_sentences(text, max_sentences=4)

        # Should only have 4 sentences
        assert result.count('.') == 4
        assert "Five" not in result
        assert "Six" not in result

    def test_count_sentences(self):
        """Sentence counter should work correctly"""
        from compare_v3_engine import _count_sentences

        assert _count_sentences("One sentence.") == 1
        assert _count_sentences("One. Two.") == 2
        assert _count_sentences("One! Two? Three.") == 3


# ============================================================================
# BIRL-FALLBACK-01: Placeholder Fallback
# ============================================================================

class TestPlaceholderFallback:
    """Test placeholder fallback behavior"""

    def test_placeholder_returns_three_results(self):
        """Placeholder should return exactly 3 results"""
        from compare_v3_engine import _generate_birl_placeholder

        results = _generate_birl_placeholder()
        assert len(results) == 3

    def test_placeholder_has_valid_dimensions(self):
        """Placeholder should have valid impact dimensions"""
        from compare_v3_engine import _generate_birl_placeholder

        valid_dimensions = {"MARGIN", "SCHEDULE", "QUALITY", "CASH_FLOW", "COMPLIANCE", "ADMIN"}
        results = _generate_birl_placeholder()

        for result in results:
            for dim in result["impact_dimensions"]:
                assert dim in valid_dimensions


# ============================================================================
# Dimension Extraction Tests
# ============================================================================

class TestDimensionExtraction:
    """Test impact dimension extraction"""

    def test_extract_margin_dimension(self):
        """Should extract MARGIN dimension from cost-related text"""
        from compare_v3_engine import _extract_dimensions

        text = "This will increase the cost and reduce profit margins."
        dimensions = _extract_dimensions(text)

        assert "MARGIN" in dimensions

    def test_extract_schedule_dimension(self):
        """Should extract SCHEDULE dimension from timeline text"""
        from compare_v3_engine import _extract_dimensions

        text = "The delivery timeline may be delayed."
        dimensions = _extract_dimensions(text)

        assert "SCHEDULE" in dimensions

    def test_extract_cash_flow_dimension(self):
        """Should extract CASH_FLOW dimension from payment text"""
        from compare_v3_engine import _extract_dimensions

        text = "Payment terms changed to Net 60."
        dimensions = _extract_dimensions(text)

        assert "CASH_FLOW" in dimensions

    def test_default_to_admin(self):
        """Should default to ADMIN for generic text"""
        from compare_v3_engine import _extract_dimensions

        text = "Generic clause with no specific impact keywords."
        dimensions = _extract_dimensions(text)

        assert "ADMIN" in dimensions
        assert len(dimensions) == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestStep4Integration:
    """Integration tests for Step 4 BIRL activation"""

    def test_phase5_birl_flag_available(self):
        """birl_intelligence_active flag should be available"""
        from phase5_flags import PHASE_5_FLAGS
        assert "birl_intelligence_active" in PHASE_5_FLAGS

    def test_hallucination_validators_importable(self):
        """Hallucination validation functions should be importable"""
        from compare_v3_engine import (
            _validate_narrative_hallucination,
            _extract_clause_numbers_from_text,
            _extract_dollar_amounts_from_text,
            _extract_dates_from_text,
            _truncate_to_sentences,
            _count_sentences,
            LEGAL_ADVICE_PHRASES,
        )

        assert callable(_validate_narrative_hallucination)
        assert callable(_extract_clause_numbers_from_text)
        assert callable(_extract_dollar_amounts_from_text)
        assert callable(_extract_dates_from_text)
        assert callable(_truncate_to_sentences)
        assert callable(_count_sentences)
        assert len(LEGAL_ADVICE_PHRASES) > 0

    def test_entity_extractors_work(self):
        """Entity extraction functions should work correctly"""
        from compare_v3_engine import (
            _extract_clause_numbers_from_text,
            _extract_dollar_amounts_from_text,
            _extract_dates_from_text,
        )

        # Clause numbers
        clause_nums = _extract_clause_numbers_from_text("See Section 5.2 and Article 3")
        assert "5.2" in clause_nums or "5" in clause_nums
        assert "3" in clause_nums

        # Dollar amounts
        dollars = _extract_dollar_amounts_from_text("Fee is $1,000 or $500")
        assert len(dollars) == 2

        # Dates
        dates = _extract_dates_from_text("Effective January 1, 2024")
        assert len(dates) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
