"""
Phase 5 Step 1 Validation Tests
Cache Infrastructure Foundation

Test Gates:
- CACHE-SCHEMA-01: clause_embeddings matches spec
- CACHE-SCHEMA-02: comparison_snapshots matches spec
- CACHE-FLAGS-01: embedding_cache_active and comparison_snapshot_active exist and are False
- CACHE-UX-01: No frontend file diffs affecting layout/behavior
"""

import os
import sys
import sqlite3
import tempfile
import json
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# CACHE-FLAGS-01: Feature Flags Exist and Default to False
# ============================================================================

class TestPhase5Flags:
    """Test Phase 5 feature flag configuration"""

    def test_phase5_flags_module_exists(self):
        """Verify phase5_flags module can be imported"""
        from phase5_flags import PHASE_5_FLAGS
        assert PHASE_5_FLAGS is not None

    def test_embedding_cache_active_default_false(self):
        """CACHE-FLAGS-01: embedding_cache_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("embedding_cache_active") is False
        assert is_flag_enabled("embedding_cache_active") is False

    def test_comparison_snapshot_active_default_false(self):
        """CACHE-FLAGS-01: comparison_snapshot_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("comparison_snapshot_active") is False
        assert is_flag_enabled("comparison_snapshot_active") is False

    def test_pattern_cache_active_default_false(self):
        """CACHE-FLAGS-01: pattern_cache_active must default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("pattern_cache_active") is False
        assert is_flag_enabled("pattern_cache_active") is False

    def test_intelligence_flags_default_false(self):
        """All intelligence flags must default to False"""
        from phase5_flags import PHASE_5_FLAGS
        assert PHASE_5_FLAGS.get("sae_intelligence_active") is False
        assert PHASE_5_FLAGS.get("erce_intelligence_active") is False
        assert PHASE_5_FLAGS.get("birl_intelligence_active") is False
        assert PHASE_5_FLAGS.get("far_intelligence_active") is False

    def test_compare_v3_ui_active_default_true(self):
        """compare_v3_ui_active must default to True (existing UI stays)"""
        from phase5_flags import PHASE_5_FLAGS
        assert PHASE_5_FLAGS.get("compare_v3_ui_active") is True

    def test_config_values_exist(self):
        """Verify configuration values are set"""
        from phase5_flags import PHASE_5_CONFIG, get_config
        assert PHASE_5_CONFIG.get("birl_max_narratives") == 5
        assert PHASE_5_CONFIG.get("global_hard_timeout_seconds") == 120
        assert get_config("embedding_cache_max_entries") == 10000
        assert get_config("comparison_snapshot_max_entries") == 1000


# ============================================================================
# CACHE-SCHEMA-01: clause_embeddings Table Schema
# ============================================================================

class TestEmbeddingCacheSchema:
    """Test embedding cache schema matches spec"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_embedding_cache_creates_table(self, temp_db):
        """CACHE-SCHEMA-01: clause_embeddings table must be created"""
        from embedding_cache import EmbeddingCache
        cache = EmbeddingCache(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='clause_embeddings'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'clause_embeddings'

    def test_embedding_table_has_required_columns(self, temp_db):
        """CACHE-SCHEMA-01: clause_embeddings must have required columns"""
        from embedding_cache import EmbeddingCache
        cache = EmbeddingCache(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clause_embeddings)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        # Required columns per spec
        assert 'id' in columns
        assert 'clause_text_hash' in columns
        assert 'embedding_vector' in columns
        assert 'model_version' in columns
        assert 'vector_dimensions' in columns
        assert 'created_at' in columns
        assert 'last_accessed_at' in columns
        assert 'access_count' in columns

    def test_embedding_table_has_hash_index(self, temp_db):
        """CACHE-SCHEMA-01: clause_embeddings must have index on clause_text_hash"""
        from embedding_cache import EmbeddingCache
        cache = EmbeddingCache(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='clause_embeddings'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert 'idx_clause_text_hash' in indexes

    def test_embedding_cache_respects_flag(self, temp_db):
        """Cache operations must respect embedding_cache_active flag"""
        from embedding_cache import EmbeddingCache
        cache = EmbeddingCache(db_path=temp_db)

        # Flag is False by default, so get should return None
        result = cache.get("test clause text")
        assert result is None

        # Put should return False when flag is disabled
        success = cache.put("test clause", b"vector", "test-model", 768)
        assert success is False


# ============================================================================
# CACHE-SCHEMA-02: comparison_snapshots Table Schema
# ============================================================================

class TestComparisonSnapshotSchema:
    """Test comparison snapshot cache schema matches spec"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_snapshot_cache_creates_table(self, temp_db):
        """CACHE-SCHEMA-02: comparison_snapshots table must be created"""
        from comparison_snapshot_cache import ComparisonSnapshotCache
        cache = ComparisonSnapshotCache(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='comparison_snapshots'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'comparison_snapshots'

    def test_snapshot_table_has_required_columns(self, temp_db):
        """CACHE-SCHEMA-02: comparison_snapshots must have required columns"""
        from comparison_snapshot_cache import ComparisonSnapshotCache
        cache = ComparisonSnapshotCache(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(comparison_snapshots)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        # Required columns per spec
        assert 'id' in columns
        assert 'v1_hash' in columns
        assert 'v2_hash' in columns
        assert 'comparison_hash' in columns
        assert 'sae_results' in columns
        assert 'erce_results' in columns
        assert 'birl_results' in columns
        assert 'far_results' in columns
        assert 'pipeline_meta' in columns
        assert 'created_at' in columns
        assert 'last_accessed_at' in columns
        assert 'access_count' in columns

    def test_snapshot_table_has_indexes(self, temp_db):
        """CACHE-SCHEMA-02: comparison_snapshots must have required indexes"""
        from comparison_snapshot_cache import ComparisonSnapshotCache
        cache = ComparisonSnapshotCache(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='comparison_snapshots'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert 'idx_comparison_hash' in indexes
        assert 'idx_v1_hash' in indexes
        assert 'idx_v2_hash' in indexes

    def test_snapshot_cache_respects_flag(self, temp_db):
        """Cache operations must respect comparison_snapshot_active flag"""
        from comparison_snapshot_cache import ComparisonSnapshotCache
        cache = ComparisonSnapshotCache(db_path=temp_db)

        # Flag is False by default, so get should return None
        result = cache.get("v1 text", "v2 text")
        assert result is None

        # Put should return False when flag is disabled
        success = cache.put(
            "v1 text", "v2 text",
            sae_results={}, erce_results={},
            birl_results={}, far_results={},
            pipeline_meta={}
        )
        assert success is False


# ============================================================================
# Pattern Cache Tests
# ============================================================================

class TestPatternCacheSchema:
    """Test pattern cache structure"""

    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache path for testing (file created by cache)"""
        # Use mktemp to get a path without creating the file
        # The PatternCache will create the file itself
        cache_path = tempfile.mktemp(suffix='.json')
        yield cache_path
        if os.path.exists(cache_path):
            os.unlink(cache_path)

    def test_pattern_cache_creates_file(self, temp_cache):
        """Pattern cache must create JSON file"""
        from pattern_cache import PatternCache
        cache = PatternCache(cache_path=temp_cache)

        assert os.path.exists(temp_cache)

    def test_pattern_cache_has_default_patterns(self, temp_cache):
        """Pattern cache must include default patterns"""
        from pattern_cache import PatternCache
        cache = PatternCache(cache_path=temp_cache)

        patterns = cache.get_all_patterns()
        assert len(patterns) > 0

    def test_pattern_cache_structure(self, temp_cache):
        """Pattern cache JSON must have required structure"""
        from pattern_cache import PatternCache
        cache = PatternCache(cache_path=temp_cache)

        with open(temp_cache, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'schema_version' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'patterns' in data
        assert isinstance(data['patterns'], list)

    def test_pattern_structure(self, temp_cache):
        """Each pattern must have required fields"""
        from pattern_cache import PatternCache
        cache = PatternCache(cache_path=temp_cache)

        patterns = cache.get_all_patterns()
        for p in patterns:
            assert hasattr(p, 'pattern_id')
            assert hasattr(p, 'pattern_name')
            assert hasattr(p, 'risk_category')
            assert hasattr(p, 'pattern_type')
            assert hasattr(p, 'pattern_value')
            assert hasattr(p, 'priority')
            assert hasattr(p, 'enabled')

    def test_pattern_cache_respects_flag(self, temp_cache):
        """Pattern matching must respect pattern_cache_active flag"""
        from pattern_cache import PatternCache
        cache = PatternCache(cache_path=temp_cache)

        # Flag is False by default, so match_text should return empty
        result = cache.match_text("unlimited indemnification")
        assert result == []


# ============================================================================
# Metrics Tests
# ============================================================================

class TestCacheMetrics:
    """Test cache metrics collection"""

    def test_metrics_collector_exists(self):
        """Metrics collector must be importable"""
        from cache_metrics import get_metrics_collector
        collector = get_metrics_collector()
        assert collector is not None

    def test_collect_all_returns_structure(self):
        """collect_all must return proper structure"""
        from cache_metrics import collect_cache_metrics
        metrics = collect_cache_metrics()

        assert 'collected_at' in metrics
        assert 'aggregated' in metrics
        assert 'caches' in metrics
        assert 'phase5_flags' in metrics

    def test_aggregated_metrics_structure(self):
        """Aggregated metrics must have required fields"""
        from cache_metrics import collect_cache_metrics
        metrics = collect_cache_metrics()
        agg = metrics['aggregated']

        assert 'total_hits' in agg
        assert 'total_misses' in agg
        assert 'total_writes' in agg
        assert 'total_evictions' in agg
        assert 'total_errors' in agg
        assert 'overall_hit_rate' in agg

    def test_health_summary_structure(self):
        """Health summary must have required fields"""
        from cache_metrics import get_cache_health
        health = get_cache_health()

        assert 'status' in health
        assert 'issues' in health
        assert 'metrics_summary' in health
        assert 'checked_at' in health


# ============================================================================
# Integration Test
# ============================================================================

class TestStep1Integration:
    """Integration tests for Step 1 cache infrastructure"""

    def test_all_caches_initialize_without_error(self):
        """All cache systems must initialize without errors"""
        from embedding_cache import get_embedding_cache
        from comparison_snapshot_cache import get_snapshot_cache
        from pattern_cache import get_pattern_cache

        embedding_cache = get_embedding_cache()
        snapshot_cache = get_snapshot_cache()
        pattern_cache = get_pattern_cache()

        # All should return valid stats
        assert embedding_cache.get_stats() is not None
        assert snapshot_cache.get_stats() is not None
        assert pattern_cache.get_stats() is not None

    def test_metrics_collection_works(self):
        """Metrics collection must work across all caches"""
        from cache_metrics import collect_cache_metrics

        metrics = collect_cache_metrics()

        # Should have data from all three caches
        assert 'aggregated' in metrics
        assert metrics['aggregated']['total_errors'] == 0  # No errors on fresh init


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
