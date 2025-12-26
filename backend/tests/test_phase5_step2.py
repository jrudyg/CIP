"""
Phase 5 Step 2 Validation Tests
SAE Intelligence Activation

Test Gates:
- SAE-FLAG-01: sae_intelligence_active flag controls behavior
- SAE-TRUNC-01: Semantic truncation works correctly
- SAE-COSINE-01: Cosine similarity computation is correct
- SAE-CACHE-01: Cache integration works when flag enabled
- SAE-FALLBACK-01: Placeholder fallback when flag disabled
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# SAE-FLAG-01: Feature Flag Controls Behavior
# ============================================================================

class TestSAEFeatureFlag:
    """Test SAE feature flag behavior"""

    def test_sae_flag_defaults_to_false(self):
        """SAE-FLAG-01: sae_intelligence_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("sae_intelligence_active") is False
        assert is_flag_enabled("sae_intelligence_active") is False

    def test_sae_returns_placeholder_when_flag_disabled(self):
        """SAE-FLAG-01: SAE returns placeholder when flag is False"""
        from compare_v3_engine import run_sae_real

        v1_clauses = [{"id": 1, "text": "Test clause one"}]
        v2_clauses = [{"id": 1, "text": "Test clause two"}]

        matches, stats = run_sae_real(v1_clauses, v2_clauses, 1, 2, "test-req")

        # Should return placeholder (3 matches)
        assert len(matches) == 3
        assert stats.get("matched_count") == 3

    def test_embedding_cache_respects_sae_flag(self):
        """SAE-FLAG-01: Embedding cache respects sae_intelligence_active"""
        from embedding_cache import get_sae_embedding

        result = get_sae_embedding(
            clause_text="Test clause",
            openai_client=None,
            model="text-embedding-3-large"
        )

        # Flag is False, should return error
        assert result.vector is None
        assert "flag is False" in result.error


# ============================================================================
# SAE-TRUNC-01: Semantic Truncation
# ============================================================================

class TestSemanticTruncation:
    """Test semantic-safe truncation"""

    def test_short_text_not_truncated(self):
        """Short text should not be truncated"""
        from embedding_cache import truncate_for_embedding

        text = "This is a short clause."
        result = truncate_for_embedding(text, max_tokens=512)
        assert result == text.strip()

    def test_long_text_truncated_at_sentence_boundary(self):
        """Long text should be truncated at sentence boundary when possible"""
        from embedding_cache import truncate_for_embedding

        # Create text that exceeds 512 tokens (~2048 chars)
        text = "This is sentence one. " * 100  # ~2200 chars
        result = truncate_for_embedding(text, max_tokens=512)

        # Should be truncated
        assert len(result) < len(text)
        # Should end at a sentence boundary (period)
        assert result.endswith('.')

    def test_truncation_preserves_minimum_content(self):
        """Truncation should preserve at least 50% of max content"""
        from embedding_cache import truncate_for_embedding

        text = "A" * 3000  # No sentence boundaries
        result = truncate_for_embedding(text, max_tokens=512)

        max_chars = 512 * 4  # ~2048
        min_expected = max_chars * 0.5  # At least 50%

        assert len(result) >= min_expected

    def test_empty_text_returns_empty(self):
        """Empty text should return empty string"""
        from embedding_cache import truncate_for_embedding

        assert truncate_for_embedding("") == ""
        assert truncate_for_embedding(None, max_tokens=512) == ""


# ============================================================================
# SAE-COSINE-01: Cosine Similarity
# ============================================================================

class TestCosineSimilarity:
    """Test cosine similarity computation"""

    def test_identical_vectors_return_one(self):
        """Identical vectors should have similarity of 1.0"""
        from embedding_cache import compute_cosine_similarity

        vec = [1.0, 0.5, 0.3, 0.8]
        assert compute_cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self):
        """Orthogonal vectors should have similarity of 0.0"""
        from embedding_cache import compute_cosine_similarity

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert compute_cosine_similarity(vec1, vec2) == pytest.approx(0.0)

    def test_opposite_vectors_return_negative_one(self):
        """Opposite vectors should have similarity of -1.0"""
        from embedding_cache import compute_cosine_similarity

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        assert compute_cosine_similarity(vec1, vec2) == pytest.approx(-1.0)

    def test_empty_vectors_return_zero(self):
        """Empty vectors should return 0.0"""
        from embedding_cache import compute_cosine_similarity

        assert compute_cosine_similarity([], []) == 0.0
        assert compute_cosine_similarity([1.0], []) == 0.0
        assert compute_cosine_similarity([], [1.0]) == 0.0

    def test_mismatched_dimensions_return_zero(self):
        """Vectors with different dimensions should return 0.0"""
        from embedding_cache import compute_cosine_similarity

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0]
        assert compute_cosine_similarity(vec1, vec2) == 0.0

    def test_zero_vector_returns_zero(self):
        """Zero vector should return 0.0"""
        from embedding_cache import compute_cosine_similarity

        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert compute_cosine_similarity(vec1, vec2) == 0.0


# ============================================================================
# SAE-CACHE-01: Cache Integration
# ============================================================================

class TestCacheIntegration:
    """Test embedding cache integration"""

    def test_vectors_to_bytes_conversion(self):
        """Vector to bytes conversion should be reversible"""
        from embedding_cache import vectors_to_bytes, bytes_to_vector

        original = [0.1, 0.2, 0.3, 0.4, 0.5]
        as_bytes = vectors_to_bytes(original)
        recovered = bytes_to_vector(as_bytes)

        assert recovered == original

    def test_bytes_to_vector_handles_invalid_data(self):
        """bytes_to_vector should handle invalid data gracefully"""
        from embedding_cache import bytes_to_vector

        assert bytes_to_vector(b"invalid json") is None
        assert bytes_to_vector(b"\xff\xfe") is None  # Invalid UTF-8

    def test_sae_embedding_result_structure(self):
        """SAEEmbeddingResult should have correct structure"""
        from embedding_cache import SAEEmbeddingResult

        result = SAEEmbeddingResult(
            clause_hash="abc123",
            vector=[0.1, 0.2, 0.3],
            model_version="text-embedding-3-large",
            dimensions=3,
            cached=True
        )

        assert result.clause_hash == "abc123"
        assert result.vector == [0.1, 0.2, 0.3]
        assert result.model_version == "text-embedding-3-large"
        assert result.dimensions == 3
        assert result.cached is True
        assert result.error is None


# ============================================================================
# SAE-FALLBACK-01: Placeholder Fallback
# ============================================================================

class TestPlaceholderFallback:
    """Test placeholder fallback behavior"""

    def test_placeholder_returns_three_matches(self):
        """Placeholder should return exactly 3 matches"""
        from compare_v3_engine import _generate_sae_placeholder

        matches = _generate_sae_placeholder()
        assert len(matches) == 3

    def test_placeholder_has_correct_structure(self):
        """Placeholder matches should have correct structure"""
        from compare_v3_engine import _generate_sae_placeholder

        matches = _generate_sae_placeholder()
        for match in matches:
            assert "v1_clause_id" in match
            assert "v2_clause_id" in match
            assert "similarity_score" in match
            assert "threshold_used" in match
            assert "match_confidence" in match

    def test_placeholder_confidence_levels(self):
        """Placeholder should include HIGH, MEDIUM, LOW confidence"""
        from compare_v3_engine import _generate_sae_placeholder

        matches = _generate_sae_placeholder()
        confidences = {m["match_confidence"] for m in matches}

        assert "HIGH" in confidences
        assert "MEDIUM" in confidences
        assert "LOW" in confidences


# ============================================================================
# Integration Tests
# ============================================================================

class TestStep2Integration:
    """Integration tests for Step 2 SAE activation"""

    def test_phase5_available_in_engine(self):
        """compare_v3_engine should have PHASE5_AVAILABLE = True"""
        from compare_v3_engine import PHASE5_AVAILABLE
        assert PHASE5_AVAILABLE is True

    def test_compare_v3_engine_imports_phase5(self):
        """compare_v3_engine should import Phase 5 modules"""
        from compare_v3_engine import is_flag_enabled, get_config
        assert callable(is_flag_enabled)
        assert callable(get_config)

    def test_embedding_cache_has_step2_helpers(self):
        """embedding_cache should have Step 2 helper functions"""
        from embedding_cache import (
            truncate_for_embedding,
            vectors_to_bytes,
            bytes_to_vector,
            compute_cosine_similarity,
            get_sae_embedding,
            SAEEmbeddingResult,
        )

        # All should be callable/importable
        assert callable(truncate_for_embedding)
        assert callable(vectors_to_bytes)
        assert callable(bytes_to_vector)
        assert callable(compute_cosine_similarity)
        assert callable(get_sae_embedding)

    def test_sae_thresholds_configured(self):
        """SAE thresholds should be properly configured"""
        from compare_v3_engine import (
            SAE_HIGH_THRESHOLD,
            SAE_MEDIUM_THRESHOLD,
            SAE_LOW_THRESHOLD,
            EMBEDDING_MODEL,
            MAX_EMBEDDING_TOKENS,
        )

        assert SAE_HIGH_THRESHOLD == 0.90
        assert SAE_MEDIUM_THRESHOLD == 0.75
        assert SAE_LOW_THRESHOLD == 0.60
        assert EMBEDDING_MODEL == "text-embedding-3-large"
        assert MAX_EMBEDDING_TOKENS == 512


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
