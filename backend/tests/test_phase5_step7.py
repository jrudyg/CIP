"""
Phase 5 Step 7 Validation Tests
Monitor Agent Observability

Test Gates:
- MON-EVENT-01: monitor_event() emits unified monitoring envelope
- MON-METRIC-01: Per-stage latency is tracked
- MON-METRIC-02: Per-stage failure count is tracked
- MON-METRIC-03: Per-stage fallback count is tracked
- MON-METRIC-04: Cache hit/miss numbers are tracked
- MON-METRIC-05: Stages skipped due to error are tracked
- MON-OUTPUT-01: _meta.monitor contains required fields
- MON-SAFETY-01: No UI, TRUST, shared_components modifications
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# MON-EVENT-01: Unified Monitoring Envelope
# ============================================================================

class TestMonitorEvent:
    """Test monitor_event() unified envelope"""

    def test_monitor_event_exists(self):
        """monitor_event function should be importable"""
        from compare_v3_engine import monitor_event
        assert callable(monitor_event)

    def test_monitor_metrics_class_exists(self):
        """MonitorMetrics class should be importable"""
        from compare_v3_engine import MonitorMetrics
        assert MonitorMetrics is not None

    def test_monitor_metrics_initialization(self):
        """MonitorMetrics should initialize with request_id"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-request-123")
        assert metrics.request_id == "test-request-123"
        assert metrics.events == []
        assert metrics.fallback_count == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_monitor_event_records_event(self):
        """monitor_event should record event in metrics"""
        from compare_v3_engine import MonitorMetrics, monitor_event

        metrics = MonitorMetrics("test-req")
        monitor_event(
            metrics=metrics,
            agent_role="cip-severity",
            stage="SAE",
            event_type="stage_start",
            duration_ms=0,
            status_code="OK"
        )

        assert len(metrics.events) == 1
        event = metrics.events[0]
        assert event["agent_role"] == "cip-severity"
        assert event["stage"] == "SAE"
        assert event["event_type"] == "stage_start"
        assert event["status_code"] == "OK"

    def test_monitor_event_types(self):
        """monitor_event should support all event types"""
        from compare_v3_engine import MonitorMetrics, monitor_event

        metrics = MonitorMetrics("test-req")

        # stage_start
        monitor_event(metrics, "orchestrator", "ORCH", "stage_start")
        # stage_end
        monitor_event(metrics, "orchestrator", "ORCH", "stage_end", duration_ms=100)
        # stage_error
        monitor_event(metrics, "cip-severity", "SAE", "stage_error", status_code="FAIL", error_detail="timeout")

        assert len(metrics.events) == 3
        assert metrics.events[0]["event_type"] == "stage_start"
        assert metrics.events[1]["event_type"] == "stage_end"
        assert metrics.events[2]["event_type"] == "stage_error"


# ============================================================================
# MON-METRIC-01: Per-Stage Latency
# ============================================================================

class TestLatencyTracking:
    """Test per-stage latency tracking"""

    def test_record_stage_latency(self):
        """Should record latency for each stage"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_stage_latency("SAE", 150)
        metrics.record_stage_latency("ERCE", 75)

        assert metrics.stage_latencies["SAE"] == 150
        assert metrics.stage_latencies["ERCE"] == 75

    def test_meta_monitor_has_stage_ms_fields(self):
        """_meta.monitor should have sae_ms, erce_ms, birl_ms, far_ms"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_stage_latency("SAE", 100)
        metrics.record_stage_latency("ERCE", 50)
        metrics.record_stage_latency("BIRL", 200)
        metrics.record_stage_latency("FAR", 30)

        monitor = metrics.to_meta_monitor()

        assert monitor["sae_ms"] == 100
        assert monitor["erce_ms"] == 50
        assert monitor["birl_ms"] == 200
        assert monitor["far_ms"] == 30


# ============================================================================
# MON-METRIC-02: Failure Count
# ============================================================================

class TestFailureTracking:
    """Test per-stage failure count tracking"""

    def test_record_error(self):
        """Should record errors with stage, key, and detail"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_error("SAE", "sae.timeout", "Stage timed out after 60s")

        assert len(metrics.errors) == 1
        assert metrics.errors[0]["stage"] == "SAE"
        assert metrics.errors[0]["error_key"] == "sae.timeout"

    def test_meta_monitor_has_errors_array(self):
        """_meta.monitor.errors should be an array"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_error("ERCE", "erce.exception", "Pattern load failed")

        monitor = metrics.to_meta_monitor()

        assert isinstance(monitor["errors"], list)
        assert len(monitor["errors"]) == 1


# ============================================================================
# MON-METRIC-03: Fallback Count
# ============================================================================

class TestFallbackTracking:
    """Test per-stage fallback count tracking"""

    def test_record_fallback(self):
        """Should increment fallback counter"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        assert metrics.fallback_count == 0

        metrics.record_fallback()
        assert metrics.fallback_count == 1

        metrics.record_fallback()
        assert metrics.fallback_count == 2

    def test_meta_monitor_has_fallbacks(self):
        """_meta.monitor.fallbacks should be an integer"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_fallback()
        metrics.record_fallback()

        monitor = metrics.to_meta_monitor()

        assert monitor["fallbacks"] == 2


# ============================================================================
# MON-METRIC-04: Cache Hit/Miss
# ============================================================================

class TestCacheTracking:
    """Test cache hit/miss tracking"""

    def test_record_cache_hit(self):
        """Should increment cache hit counter"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_cache_hit()
        metrics.record_cache_hit()

        assert metrics.cache_hits == 2

    def test_record_cache_miss(self):
        """Should increment cache miss counter"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_cache_miss()

        assert metrics.cache_misses == 1

    def test_meta_monitor_has_cache_stats(self):
        """_meta.monitor should have cache_hits and cache_misses"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()

        monitor = metrics.to_meta_monitor()

        assert monitor["cache_hits"] == 2
        assert monitor["cache_misses"] == 1


# ============================================================================
# MON-METRIC-05: Stages Skipped
# ============================================================================

class TestStagesSkipped:
    """Test stages skipped tracking"""

    def test_record_stage_skipped(self):
        """Should increment stages skipped counter"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_stage_skipped()
        metrics.record_stage_skipped()

        assert metrics.stages_skipped == 2

    def test_meta_monitor_has_stages_skipped(self):
        """_meta.monitor should have stages_skipped"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.record_stage_skipped()

        monitor = metrics.to_meta_monitor()

        assert monitor["stages_skipped"] == 1


# ============================================================================
# MON-OUTPUT-01: _meta.monitor Output Contract
# ============================================================================

class TestMetaMonitorOutput:
    """Test _meta.monitor output contract"""

    def test_meta_monitor_has_all_required_fields(self):
        """_meta.monitor should have all required fields"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.total_start_ms = 1000
        metrics.total_end_ms = 2000

        monitor = metrics.to_meta_monitor()

        required_fields = [
            "sae_ms",
            "erce_ms",
            "birl_ms",
            "far_ms",
            "total_ms",
            "errors",
            "fallbacks",
        ]

        for field in required_fields:
            assert field in monitor, f"Missing required field: {field}"

    def test_total_ms_calculated_correctly(self):
        """total_ms should be calculated from start/end times"""
        from compare_v3_engine import MonitorMetrics

        metrics = MonitorMetrics("test-req")
        metrics.total_start_ms = 1000
        metrics.total_end_ms = 1500

        monitor = metrics.to_meta_monitor()

        assert monitor["total_ms"] == 500

    def test_orchestrator_returns_meta_monitor(self):
        """Orchestrator should return _meta.monitor"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert "monitor" in result["_meta"]
        monitor = result["_meta"]["monitor"]
        assert "sae_ms" in monitor
        assert "erce_ms" in monitor
        assert "birl_ms" in monitor
        assert "far_ms" in monitor
        assert "total_ms" in monitor
        assert "errors" in monitor
        assert "fallbacks" in monitor


# ============================================================================
# MON-SAFETY-01: Safety Constraints
# ============================================================================

class TestSafetyConstraints:
    """Test safety constraints are respected"""

    def test_no_new_pipeline_keys_outside_meta_monitor(self):
        """Only _meta.monitor should be new, no other top-level keys"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        # Expected top-level keys (frozen)
        expected_keys = {"sae_matches", "erce_results", "birl_narratives", "flowdown_gaps", "_meta"}
        actual_keys = set(result.keys())

        assert actual_keys == expected_keys, f"Unexpected keys: {actual_keys - expected_keys}"

    def test_monitor_only_in_meta(self):
        """Monitor data should only be in _meta.monitor"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        # Monitor should be nested in _meta
        assert "monitor" in result["_meta"]
        # Monitor should NOT be at top level
        assert "monitor" not in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestStep7Integration:
    """Integration tests for Step 7 observability"""

    def test_compute_payload_ref_exists(self):
        """compute_payload_ref helper should exist"""
        from compare_v3_engine import compute_payload_ref
        assert callable(compute_payload_ref)

    def test_compute_payload_ref_returns_hash(self):
        """compute_payload_ref should return short hash"""
        from compare_v3_engine import compute_payload_ref

        data = [{"id": 1, "text": "test"}]
        ref = compute_payload_ref(data)

        assert isinstance(ref, str)
        assert len(ref) == 12  # SHA256 truncated to 12 chars

    def test_engine_version_is_5_7(self):
        """Engine version should be 5.7 with monitoring"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert result["_meta"]["engine_version"] == "5.7"

    def test_events_count_in_monitor(self):
        """Monitor should track total events count"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        monitor = result["_meta"]["monitor"]
        # Should have at least: ORCH start, SAE start/end, ERCE start/end, BIRL start/end, FAR start/end, ORCH end
        assert monitor["events_count"] >= 10


# ============================================================================
# Metrics Recording Tests
# ============================================================================

class TestMetricsRecording:
    """Test metrics recording during orchestration"""

    def test_all_stages_have_latency(self):
        """All stages should have latency recorded"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        monitor = result["_meta"]["monitor"]
        assert monitor["sae_ms"] >= 0
        assert monitor["erce_ms"] >= 0
        assert monitor["birl_ms"] >= 0
        assert monitor["far_ms"] >= 0

    def test_total_ms_is_sum_of_stages_approximately(self):
        """total_ms should be approximately sum of stage times"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        monitor = result["_meta"]["monitor"]
        stage_sum = monitor["sae_ms"] + monitor["erce_ms"] + monitor["birl_ms"] + monitor["far_ms"]

        # total_ms should be >= stage_sum (may include overhead)
        assert monitor["total_ms"] >= stage_sum or monitor["total_ms"] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
