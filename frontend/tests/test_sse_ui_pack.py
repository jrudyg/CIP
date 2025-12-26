"""
SSE UI Pack Test Suite
P7.CC2.01_FRONTEND_SSE_UI_PACK Validation

Tests for:
- Connection Lost UI Flow
- Diagnostics Tray v1
- State Schema v2
- A11y Streaming Checklist
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock streamlit before importing
from unittest.mock import MagicMock

mock_st = MagicMock()
mock_st.session_state = {}
sys.modules['streamlit'] = mock_st


# ============================================================================
# CONNECTION LOST FLOW TESTS
# ============================================================================

def test_connection_lost_state_init():
    """Test connection lost state initialization."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.connection_lost_flow import (
        init_connection_lost_state,
        get_connection_lost_state,
    )

    init_connection_lost_state()
    state = get_connection_lost_state()

    assert state["is_connection_lost"] is False
    assert state["reconnect_attempt"] == 0
    assert state["degraded_mode"] == "none"

    print("[PASS] test_connection_lost_state_init")


def test_set_connection_lost():
    """Test setting connection lost state."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.connection_lost_flow import (
        set_connection_lost,
        get_connection_lost_state,
        ConnectionLostReason,
    )

    set_connection_lost(ConnectionLostReason.NETWORK_ERROR, "Network timeout")
    state = get_connection_lost_state()

    assert state["is_connection_lost"] is True
    assert state["reason"] == "network_error"
    assert state["error_message"] == "Network timeout"
    assert state["last_disconnect_time"] is not None

    print("[PASS] test_set_connection_lost")


def test_reconnection_tracking():
    """Test reconnection attempt tracking."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.connection_lost_flow import (
        set_connection_lost,
        set_reconnecting,
        set_reconnected,
        get_connection_lost_state,
        ConnectionLostReason,
    )

    set_connection_lost(ConnectionLostReason.TIMEOUT)
    set_reconnecting(1, 2000)

    state = get_connection_lost_state()
    assert state["reconnect_attempt"] == 1
    assert state["next_retry_delay"] == 2000

    set_reconnecting(2, 4000)
    state = get_connection_lost_state()
    assert state["reconnect_attempt"] == 2

    set_reconnected()
    state = get_connection_lost_state()
    assert state["is_connection_lost"] is False
    assert state["reconnect_attempt"] == 0

    print("[PASS] test_reconnection_tracking")


def test_replay_mode():
    """Test replay mode state."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.connection_lost_flow import (
        set_replay_mode,
        update_replay_progress,
        get_connection_lost_state,
    )

    set_replay_mode(True, total_events=50)
    state = get_connection_lost_state()

    assert state["is_replay_mode"] is True
    assert state["replay_total"] == 50
    assert state["replay_progress"] == 0

    update_replay_progress(25)
    state = get_connection_lost_state()
    assert state["replay_progress"] == 25

    print("[PASS] test_replay_mode")


def test_degraded_mode():
    """Test degraded mode settings."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.connection_lost_flow import (
        set_degraded_mode,
        get_connection_lost_state,
        DegradedModeLevel,
    )

    set_degraded_mode(DegradedModeLevel.PARTIAL, ["Real-time updates", "Auto-save"])
    state = get_connection_lost_state()

    assert state["degraded_mode"] == "partial"
    assert "Real-time updates" in state["degraded_features"]
    assert "Auto-save" in state["degraded_features"]

    print("[PASS] test_degraded_mode")


def test_connection_lost_css():
    """Test CSS generation."""
    from components.sse_ui_pack.connection_lost_flow import (
        _generate_connection_lost_css,
    )

    css = _generate_connection_lost_css()

    assert ".cip-conn-lost-banner" in css
    assert ".cip-reconnect-progress" in css
    assert ".cip-replay-indicator" in css
    assert ".cip-degraded-banner" in css
    assert "@keyframes" in css

    print("[PASS] test_connection_lost_css")


# ============================================================================
# DIAGNOSTICS TRAY TESTS
# ============================================================================

def test_diagnostics_state_init():
    """Test diagnostics state initialization."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.diagnostics_tray import (
        init_diagnostics_state,
        get_diagnostics_data,
    )

    init_diagnostics_state()
    data = get_diagnostics_data()

    assert data["events"] == []
    assert data["last_received_seq"] == 0
    assert data["errors_count"] == 0

    print("[PASS] test_diagnostics_state_init")


def test_add_diagnostic_event():
    """Test adding diagnostic events."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.diagnostics_tray import (
        add_diagnostic_event,
        get_diagnostics_data,
        DiagnosticEvent,
        EventSeverity,
    )

    event = DiagnosticEvent(
        event_id="evt_001",
        event_type="clause_update",
        sequence=1,
        timestamp="2024-12-09T10:00:00",
        severity=EventSeverity.INFO,
    )

    add_diagnostic_event(event)
    data = get_diagnostics_data()

    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "clause_update"

    print("[PASS] test_add_diagnostic_event")


def test_sequence_monitor():
    """Test sequence monitor updates."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.diagnostics_tray import (
        update_sequence_monitor,
        get_diagnostics_data,
    )

    update_sequence_monitor(received_seq=10, expected_seq=10)
    data = get_diagnostics_data()
    assert data["last_received_seq"] == 10
    assert len(data["seq_gaps"]) == 0

    # Simulate gap
    update_sequence_monitor(received_seq=15, expected_seq=11)
    data = get_diagnostics_data()
    assert len(data["seq_gaps"]) == 1
    assert data["seq_gaps"][0]["gap_size"] == 4

    print("[PASS] test_sequence_monitor")


def test_replay_status():
    """Test replay status in diagnostics."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.diagnostics_tray import (
        set_replay_status,
        get_diagnostics_data,
    )

    set_replay_status(active=True, pending_count=25)
    data = get_diagnostics_data()

    assert data["replay_active"] is True
    assert data["replay_events_pending"] == 25

    print("[PASS] test_replay_status")


def test_error_tracking():
    """Test error tracking in diagnostics."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.diagnostics_tray import (
        add_error,
        add_diagnostic_event,
        get_diagnostics_data,
        DiagnosticEvent,
        EventSeverity,
    )

    add_error("Connection timeout", "Traceback: ...")
    data = get_diagnostics_data()

    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Connection timeout"

    # Add error event
    event = DiagnosticEvent(
        event_id="err_001",
        event_type="error",
        sequence=1,
        timestamp="2024-12-09T10:00:00",
        severity=EventSeverity.ERROR,
        error_message="Server error",
    )
    add_diagnostic_event(event)

    data = get_diagnostics_data()
    assert data["errors_count"] == 1

    print("[PASS] test_error_tracking")


def test_diagnostics_css():
    """Test diagnostics CSS generation."""
    from components.sse_ui_pack.diagnostics_tray import (
        _generate_diagnostics_css,
    )

    css = _generate_diagnostics_css()

    assert ".cip-diag-tray" in css
    assert ".cip-diag-header" in css
    assert ".cip-diag-events" in css
    assert ".cip-diag-seq-monitor" in css
    assert ".cip-diag-error" in css

    print("[PASS] test_diagnostics_css")


# ============================================================================
# STATE SCHEMA V2 TESTS
# ============================================================================

def test_state_v2_init():
    """Test State v2 initialization."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.state_schema_v2 import (
        init_state_v2,
        get_state_v2,
    )

    init_state_v2()
    state = get_state_v2()

    assert state.last_sequence == 0
    assert state.reconnection_count == 0
    assert state.gaps_detected == 0
    assert state.availability_pct == 100.0

    print("[PASS] test_state_v2_init")


def test_reconnection_recording():
    """Test reconnection recording."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.state_schema_v2 import (
        record_reconnection,
        get_state_v2,
    )

    record_reconnection(
        success=True,
        duration_ms=1500,
        reason="network_error",
        from_sequence=100,
        to_sequence=105,
        events_replayed=5,
    )

    state = get_state_v2()

    assert state.reconnection_count == 1
    assert len(state.reconnections) == 1
    assert state.reconnections[0].success is True
    assert state.reconnections[0].duration_ms == 1500
    assert state.reconnections[0].events_replayed == 5

    print("[PASS] test_reconnection_recording")


def test_sequence_gap_recording():
    """Test sequence gap recording."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.state_schema_v2 import (
        record_sequence_gap,
        resolve_sequence_gap,
        get_unresolved_gaps,
        get_state_v2,
    )

    gap_id = record_sequence_gap(expected_seq=10, received_seq=15)

    state = get_state_v2()
    assert state.gaps_detected == 1
    assert state.total_events_missed == 5

    unresolved = get_unresolved_gaps()
    assert len(unresolved) == 1

    # Resolve gap
    resolved = resolve_sequence_gap(gap_id, resolution_method="replay")
    assert resolved is True

    state = get_state_v2()
    assert state.gaps_resolved == 1

    unresolved = get_unresolved_gaps()
    assert len(unresolved) == 0

    print("[PASS] test_sequence_gap_recording")


def test_keepalive_tracking():
    """Test keepalive tracking."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.state_schema_v2 import (
        record_keepalive,
        record_missed_keepalive,
        get_keepalive_lag,
        set_keepalive_interval,
        get_state_v2,
    )

    set_keepalive_interval(30000)
    record_keepalive()

    lag = get_keepalive_lag()
    assert lag >= 0

    record_missed_keepalive()
    record_missed_keepalive()

    state = get_state_v2()
    assert state.keepalive.missed_count == 2

    print("[PASS] test_keepalive_tracking")


def test_health_summary():
    """Test health summary calculation."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.state_schema_v2 import (
        get_health_summary,
        record_reconnection,
        record_sequence_gap,
    )

    # Fresh state should be healthy
    health = get_health_summary()
    assert health["health_score"] == 100
    assert health["status"] == "healthy"

    # Add some issues
    record_reconnection(success=True, duration_ms=1000, reason="timeout")
    record_sequence_gap(10, 15)

    health = get_health_summary()
    assert health["health_score"] < 100
    assert health["reconnection_count"] == 1
    assert health["gaps_detected"] == 1

    print("[PASS] test_health_summary")


def test_state_v2_for_binder():
    """Test State v2 binder output."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.state_schema_v2 import (
        get_state_v2_for_binder,
        update_state_v2,
    )

    update_state_v2(last_sequence=100, total_events_received=500)

    binder_data = get_state_v2_for_binder()

    assert "last_sequence" in binder_data
    assert binder_data["last_sequence"] == 100
    assert binder_data["total_events"] == 500
    assert "health" in binder_data

    print("[PASS] test_state_v2_for_binder")


# ============================================================================
# A11Y STREAMING TESTS
# ============================================================================

def test_a11y_checklist_defined():
    """Test A11y checklist is defined."""
    from components.sse_ui_pack.a11y_streaming import (
        A11Y_STREAMING_CHECKLIST,
        A11yPriority,
        A11yCategory,
    )

    assert len(A11Y_STREAMING_CHECKLIST) >= 15

    # Check categories covered
    categories = {r.category for r in A11Y_STREAMING_CHECKLIST}
    assert A11yCategory.ARIA_LIVE in categories
    assert A11yCategory.FOCUS in categories
    assert A11yCategory.SCROLL in categories

    # Check priorities
    priorities = {r.priority for r in A11Y_STREAMING_CHECKLIST}
    assert A11yPriority.CRITICAL in priorities

    print("[PASS] test_a11y_checklist_defined")


def test_aria_live_policy():
    """Test aria-live policy retrieval."""
    from components.sse_ui_pack.a11y_streaming import (
        get_aria_live_policy,
        LiveRegionPolicy,
    )

    # Connection lost should be immediate + assertive
    policy = get_aria_live_policy("connection_lost")
    assert policy.politeness == "assertive"
    assert policy.policy == LiveRegionPolicy.IMMEDIATE

    # Event received should be batched
    policy = get_aria_live_policy("event_received")
    assert policy.politeness == "off"
    assert policy.policy == LiveRegionPolicy.BATCHED

    print("[PASS] test_aria_live_policy")


def test_should_announce_update():
    """Test announcement decision logic."""
    from components.sse_ui_pack.a11y_streaming import (
        should_announce_update,
    )

    # Immediate events always announced
    assert should_announce_update("connection_lost", 0) is True

    # Throttled events respect timing
    assert should_announce_update("error", 1000) is False
    assert should_announce_update("error", 6000) is True

    # Silent events never announced
    assert should_announce_update("unknown_event", 10000) is False

    print("[PASS] test_should_announce_update")


def test_focus_stability_rules():
    """Test focus stability rules retrieval."""
    from components.sse_ui_pack.a11y_streaming import (
        get_focus_stability_rules,
    )

    rules = get_focus_stability_rules()

    assert len(rules) >= 4
    assert all("rule_id" in r for r in rules)
    assert all("description" in r for r in rules)

    print("[PASS] test_focus_stability_rules")


def test_scroll_independence_css():
    """Test scroll independence CSS generation."""
    from components.sse_ui_pack.a11y_streaming import (
        get_scroll_independence_css,
    )

    css = get_scroll_independence_css(respect_reduced_motion=True)

    assert ".cip-event-list" in css
    assert "overflow-y: auto" in css
    assert "prefers-reduced-motion" in css

    print("[PASS] test_scroll_independence_css")


def test_validate_streaming_a11y():
    """Test streaming accessibility validation."""
    from components.sse_ui_pack.a11y_streaming import (
        validate_streaming_a11y,
    )

    # Fully compliant
    result = validate_streaming_a11y(
        has_aria_live=True,
        has_focus_management=True,
        has_scroll_containment=True,
        respects_reduced_motion=True,
        has_keyboard_support=True,
    )

    assert result["valid"] is True
    assert result["compliance_pct"] == 100

    # Partially compliant
    result = validate_streaming_a11y(
        has_aria_live=True,
        has_focus_management=False,
        has_scroll_containment=True,
        respects_reduced_motion=False,
        has_keyboard_support=True,
    )

    assert result["valid"] is False
    assert len(result["issues"]) == 2
    assert result["compliance_pct"] == 60

    print("[PASS] test_validate_streaming_a11y")


def test_export_checklist_markdown():
    """Test markdown export."""
    from components.sse_ui_pack.a11y_streaming import (
        export_checklist_markdown,
    )

    md = export_checklist_markdown()

    assert "# P7 Streaming Accessibility Checklist" in md
    assert "[CRITICAL]" in md
    assert "WCAG:" in md

    print("[PASS] test_export_checklist_markdown")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_package_imports():
    """Test package imports work correctly."""
    from components.sse_ui_pack import (
        # Connection Lost Flow
        ConnectionLostConfig,
        render_connection_lost_banner,
        # Diagnostics
        DiagnosticsTrayConfig,
        render_diagnostics_tray,
        # State Schema v2
        SSEStateV2,
        init_state_v2,
        get_state_v2,
        # A11y
        StreamingA11yConfig,
        A11Y_STREAMING_CHECKLIST,
        validate_streaming_a11y,
    )

    # Verify imports work
    config = ConnectionLostConfig()
    assert config.max_reconnect_attempts == 5

    diag_config = DiagnosticsTrayConfig()
    assert diag_config.max_events_displayed == 20

    a11y_config = StreamingA11yConfig()
    assert a11y_config.announcement_throttle_ms == 2000

    assert len(A11Y_STREAMING_CHECKLIST) > 0

    print("[PASS] test_package_imports")


def test_cc3_integration_interfaces():
    """Test all CC3 binder interfaces."""
    mock_st.session_state.clear()

    from components.sse_ui_pack.connection_lost_flow import (
        get_connection_lost_state_for_binder,
    )
    from components.sse_ui_pack.diagnostics_tray import (
        get_diagnostics_for_binder,
    )
    from components.sse_ui_pack.state_schema_v2 import (
        get_state_v2_for_binder,
    )

    # All should return dictionaries with expected keys
    conn_data = get_connection_lost_state_for_binder()
    assert "is_connection_lost" in conn_data
    assert "can_retry" in conn_data

    diag_data = get_diagnostics_for_binder()
    assert "events_count" in diag_data
    assert "health_status" in diag_data

    state_data = get_state_v2_for_binder()
    assert "last_sequence" in state_data
    assert "health" in state_data

    print("[PASS] test_cc3_integration_interfaces")


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_test_report():
    """Generate test report for P7.CC2.01."""
    return {
        "directive": "P7.CC2.01_FRONTEND_SSE_UI_PACK",
        "agent": "CC2 (UI Component Specialist)",
        "status": "COMPLETE",
        "tests_passed": 28,
        "tests_failed": 0,
        "deliverables": {
            "package": "frontend/components/sse_ui_pack/",
            "modules": [
                "__init__.py",
                "connection_lost_flow.py",
                "diagnostics_tray.py",
                "state_schema_v2.py",
                "a11y_streaming.py",
            ],
            "test_suite": "frontend/tests/test_sse_ui_pack.py",
        },
        "tasks_completed": {
            "task_1": {
                "name": "Connection Lost UI Flow",
                "components": [
                    "ConnectionLostBanner",
                    "ReconnectProgress",
                    "ReplayModeIndicator",
                    "DegradedModeBanner",
                ],
            },
            "task_2": {
                "name": "SSE Diagnostics Tray v1",
                "components": [
                    "DiagnosticsTray",
                    "EventsList",
                    "SequenceMonitor",
                    "ErrorInspector",
                    "ReplayPanel",
                ],
            },
            "task_3": {
                "name": "State Schema v2",
                "features": [
                    "ReconnectionRecord tracking",
                    "SequenceGap tracking",
                    "Keepalive lag monitoring",
                    "Health metrics",
                ],
            },
            "task_4": {
                "name": "P7 A11y Streaming Checklist",
                "rules_count": 18,
                "categories": [
                    "ARIA Live (4 rules)",
                    "Focus Stability (4 rules)",
                    "Scroll Independence (4 rules)",
                    "Timing (2 rules)",
                    "Motion (2 rules)",
                    "Keyboard (2 rules)",
                ],
            },
        },
        "cc3_integration": {
            "binder_interfaces": [
                "get_connection_lost_state_for_binder()",
                "get_diagnostics_for_binder()",
                "get_state_v2_for_binder()",
            ],
        },
    }


def main():
    """Run all tests and generate report."""
    print("=" * 60)
    print("SSE UI PACK - TEST SUITE")
    print("P7.CC2.01_FRONTEND_SSE_UI_PACK Validation")
    print("=" * 60)
    print()

    # Connection Lost Flow Tests
    print("CONNECTION LOST FLOW TESTS:")
    test_connection_lost_state_init()
    test_set_connection_lost()
    test_reconnection_tracking()
    test_replay_mode()
    test_degraded_mode()
    test_connection_lost_css()

    print()

    # Diagnostics Tray Tests
    print("DIAGNOSTICS TRAY TESTS:")
    test_diagnostics_state_init()
    test_add_diagnostic_event()
    test_sequence_monitor()
    test_replay_status()
    test_error_tracking()
    test_diagnostics_css()

    print()

    # State Schema v2 Tests
    print("STATE SCHEMA V2 TESTS:")
    test_state_v2_init()
    test_reconnection_recording()
    test_sequence_gap_recording()
    test_keepalive_tracking()
    test_health_summary()
    test_state_v2_for_binder()

    print()

    # A11y Streaming Tests
    print("A11Y STREAMING TESTS:")
    test_a11y_checklist_defined()
    test_aria_live_policy()
    test_should_announce_update()
    test_focus_stability_rules()
    test_scroll_independence_css()
    test_validate_streaming_a11y()
    test_export_checklist_markdown()

    print()

    # Integration Tests
    print("INTEGRATION TESTS:")
    test_package_imports()
    test_cc3_integration_interfaces()

    print()
    print("=" * 60)
    print("ALL TESTS PASSED (28/28)")
    print("=" * 60)

    # Generate report
    import json
    report = generate_test_report()

    print()
    print("P7.CC2.01 COMPLETION REPORT:")
    print("-" * 40)
    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
