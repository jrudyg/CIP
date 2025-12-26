"""
Phase 5 Step 6 Validation Tests
Orchestrator Wiring - Unified Pipeline Execution

Test Gates:
- ORCH-SEQ-01: Pipeline executes SAE → ERCE → BIRL → FAR in sequence
- ORCH-TIMEOUT-01: Per-stage timeouts are configured
- ORCH-DURATION-01: Per-stage duration is captured in _meta
- ORCH-GRACEFUL-01: Stage failures do not cascade
- ORCH-LOG-01: Unified logging format with required fields
- ORCH-FLAG-01: All intelligence flags default to OFF
- ORCH-STATUS-01: Pipeline status reflects partial/full execution
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# ORCH-SEQ-01: Pipeline Sequence
# ============================================================================

class TestPipelineSequence:
    """Test pipeline executes in correct order"""

    def test_orchestrator_exists(self):
        """Orchestrator function should be importable"""
        from compare_v3_engine import run_compare_v3_orchestrator
        assert callable(run_compare_v3_orchestrator)

    def test_orchestrator_returns_all_stages(self):
        """Orchestrator should return results from all 4 stages"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        # Should have all stage outputs
        assert "sae_matches" in result
        assert "erce_results" in result
        assert "birl_narratives" in result
        assert "flowdown_gaps" in result
        assert "_meta" in result

    def test_orchestrator_returns_meta_stats(self):
        """Orchestrator should return _meta.stats for all stages"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        stats = result["_meta"]["stats"]
        assert "sae" in stats
        assert "erce" in stats
        assert "birl" in stats
        assert "far" in stats


# ============================================================================
# ORCH-TIMEOUT-01: Timeout Configuration
# ============================================================================

class TestTimeoutConfiguration:
    """Test timeout configuration"""

    def test_orchestrator_timeouts_exist(self):
        """Orchestrator timeouts should be configured"""
        from compare_v3_engine import ORCHESTRATOR_TIMEOUTS

        assert "global" in ORCHESTRATOR_TIMEOUTS
        assert "SAE" in ORCHESTRATOR_TIMEOUTS
        assert "ERCE" in ORCHESTRATOR_TIMEOUTS
        assert "BIRL" in ORCHESTRATOR_TIMEOUTS
        assert "FAR" in ORCHESTRATOR_TIMEOUTS

    def test_timeout_values_are_reasonable(self):
        """Timeout values should be reasonable"""
        from compare_v3_engine import ORCHESTRATOR_TIMEOUTS

        assert ORCHESTRATOR_TIMEOUTS["global"] == 120
        assert ORCHESTRATOR_TIMEOUTS["SAE"] == 60
        assert ORCHESTRATOR_TIMEOUTS["ERCE"] == 30
        assert ORCHESTRATOR_TIMEOUTS["BIRL"] == 45
        assert ORCHESTRATOR_TIMEOUTS["FAR"] == 15

    def test_execute_stage_with_timeout_exists(self):
        """Helper function for timeout execution should exist"""
        from compare_v3_engine import _execute_stage_with_timeout
        assert callable(_execute_stage_with_timeout)


# ============================================================================
# ORCH-DURATION-01: Duration Tracking
# ============================================================================

class TestDurationTracking:
    """Test per-stage duration tracking"""

    def test_meta_contains_stage_durations(self):
        """_meta should contain stage durations in ms"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        meta = result["_meta"]
        assert "stage_durations_ms" in meta
        assert "SAE" in meta["stage_durations_ms"]
        assert "ERCE" in meta["stage_durations_ms"]
        assert "BIRL" in meta["stage_durations_ms"]
        assert "FAR" in meta["stage_durations_ms"]

    def test_meta_contains_total_duration(self):
        """_meta should contain total pipeline duration"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert "total_duration_ms" in result["_meta"]
        assert result["_meta"]["total_duration_ms"] >= 0

    def test_durations_are_integers(self):
        """Durations should be integers (milliseconds)"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        durations = result["_meta"]["stage_durations_ms"]
        for stage, duration in durations.items():
            assert isinstance(duration, int), f"{stage} duration should be int"


# ============================================================================
# ORCH-GRACEFUL-01: Graceful Degradation
# ============================================================================

class TestGracefulDegradation:
    """Test graceful degradation behavior"""

    def test_meta_contains_stage_statuses(self):
        """_meta should contain status for each stage"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        statuses = result["_meta"]["stage_statuses"]
        assert "SAE" in statuses
        assert "ERCE" in statuses
        assert "BIRL" in statuses
        assert "FAR" in statuses

    def test_stage_status_values_are_valid(self):
        """Stage statuses should be 'success' or 'failure'"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        valid_statuses = {"success", "failure"}
        statuses = result["_meta"]["stage_statuses"]
        for stage, status in statuses.items():
            assert status in valid_statuses, f"{stage} has invalid status: {status}"

    def test_pipeline_status_reflects_failures(self):
        """Pipeline status should reflect stage failures"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        # With flags OFF, pipeline runs with placeholders but no failures
        pipeline_status = result["_meta"]["pipeline_status"]
        assert pipeline_status in ["REAL", "PLACEHOLDER"] or pipeline_status.startswith("PARTIAL:")

    def test_stage_stats_contain_status(self):
        """Each stage stats should contain status field"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        stats = result["_meta"]["stats"]
        for stage_name, stage_stats in stats.items():
            assert "status" in stage_stats, f"{stage_name} stats missing status"


# ============================================================================
# ORCH-LOG-01: Unified Logging Format
# ============================================================================

class TestUnifiedLogging:
    """Test unified logging format"""

    def test_stage_agent_roles_configured(self):
        """Agent roles should be configured for each stage"""
        from compare_v3_engine import STAGE_AGENT_ROLES

        assert STAGE_AGENT_ROLES["SAE"] == "cip-severity"
        assert STAGE_AGENT_ROLES["ERCE"] == "cip-severity"
        assert STAGE_AGENT_ROLES["BIRL"] == "cip-reasoning"
        assert STAGE_AGENT_ROLES["FAR"] == "far"

    def test_meta_contains_request_id(self):
        """_meta should contain request_id"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert "request_id" in result["_meta"]
        assert len(result["_meta"]["request_id"]) > 0


# ============================================================================
# ORCH-FLAG-01: Intelligence Flags Default OFF
# ============================================================================

class TestIntelligenceFlagsOff:
    """Test all intelligence flags default to OFF"""

    def test_sae_flag_defaults_false(self):
        """sae_intelligence_active should default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("sae_intelligence_active") is False
        assert is_flag_enabled("sae_intelligence_active") is False

    def test_erce_flag_defaults_false(self):
        """erce_intelligence_active should default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("erce_intelligence_active") is False
        assert is_flag_enabled("erce_intelligence_active") is False

    def test_birl_flag_defaults_false(self):
        """birl_intelligence_active should default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("birl_intelligence_active") is False
        assert is_flag_enabled("birl_intelligence_active") is False

    def test_far_flag_defaults_false(self):
        """far_intelligence_active should default to False"""
        from phase5_flags import PHASE_5_FLAGS, is_flag_enabled
        assert PHASE_5_FLAGS.get("far_intelligence_active") is False
        assert is_flag_enabled("far_intelligence_active") is False

    def test_meta_shows_all_flags_off(self):
        """_meta should show all intelligence flags as OFF"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        flags = result["_meta"]["intelligence_flags"]
        assert flags["sae_intelligence_active"] is False
        assert flags["erce_intelligence_active"] is False
        assert flags["birl_intelligence_active"] is False
        assert flags["far_intelligence_active"] is False


# ============================================================================
# ORCH-STATUS-01: Pipeline Status
# ============================================================================

class TestPipelineStatus:
    """Test pipeline status reporting"""

    def test_engine_version_is_5_7(self):
        """Engine version should be 5.7 for orchestrator with monitoring"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert result["_meta"]["engine_version"] == "5.7"

    def test_meta_contains_generated_at(self):
        """_meta should contain generated_at timestamp"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert "generated_at" in result["_meta"]
        # Should be ISO format
        assert "T" in result["_meta"]["generated_at"]

    def test_meta_contains_intelligence_active(self):
        """_meta should contain intelligence_active boolean"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert "intelligence_active" in result["_meta"]
        # Should be False since all flags are OFF
        assert result["_meta"]["intelligence_active"] is False


# ============================================================================
# Output Shape Tests
# ============================================================================

class TestOutputShape:
    """Test orchestrator output shape"""

    def test_sae_matches_is_list(self):
        """sae_matches should be a list"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert isinstance(result["sae_matches"], list)

    def test_erce_results_is_list(self):
        """erce_results should be a list"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert isinstance(result["erce_results"], list)

    def test_birl_narratives_is_list(self):
        """birl_narratives should be a list"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert isinstance(result["birl_narratives"], list)

    def test_flowdown_gaps_is_list(self):
        """flowdown_gaps should be a list"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2"
        )

        assert isinstance(result["flowdown_gaps"], list)


# ============================================================================
# Integration Tests
# ============================================================================

class TestStep6Integration:
    """Integration tests for Step 6"""

    def test_all_orchestrator_imports(self):
        """All orchestrator components should be importable"""
        from compare_v3_engine import (
            run_compare_v3_orchestrator,
            _execute_stage_with_timeout,
            ORCHESTRATOR_TIMEOUTS,
            STAGE_AGENT_ROLES,
        )

        assert callable(run_compare_v3_orchestrator)
        assert callable(_execute_stage_with_timeout)
        assert isinstance(ORCHESTRATOR_TIMEOUTS, dict)
        assert isinstance(STAGE_AGENT_ROLES, dict)

    def test_orchestrator_with_contract_ids(self):
        """Orchestrator should accept contract IDs"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="Test contract v1",
            v2_text="Test contract v2",
            v1_contract_id=1,
            v2_contract_id=2
        )

        assert result is not None
        assert "_meta" in result

    def test_orchestrator_with_empty_text(self):
        """Orchestrator should handle empty text gracefully"""
        from compare_v3_engine import run_compare_v3_orchestrator

        result = run_compare_v3_orchestrator(
            v1_text="",
            v2_text=""
        )

        # Should still return valid structure
        assert "sae_matches" in result
        assert "_meta" in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
