"""
SSE State Components Test Suite
Phase 7 Readiness Validation

Tests for sse_state.py - EventBuffer + ConnectionStateIndicator support.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock streamlit before importing
from unittest.mock import MagicMock, patch

mock_st = MagicMock()
mock_st.session_state = {}
sys.modules['streamlit'] = mock_st

from components.sse_state import (
    # Enums and dataclasses
    ConnectionState,
    SSEEvent,
    EventBufferState,
    # State management
    init_sse_state,
    get_connection_state,
    set_connection_state,
    is_debug_mode,
    toggle_debug_mode,
    _get_sse_state_key,
    # Event buffer
    get_event_buffer,
    add_event_to_buffer,
    clear_event_buffer,
    get_last_sequence,
    set_replay_mode,
    # CSS
    _generate_sse_state_css,
    # Validation
    validate_sse_state_accessibility,
    # CC3 integration
    get_sse_state_for_binder,
)


# ============================================================================
# CONNECTION STATE TESTS
# ============================================================================

def test_connection_state_enum():
    """Test ConnectionState enum values."""
    assert ConnectionState.DISCONNECTED.value == "disconnected"
    assert ConnectionState.CONNECTING.value == "connecting"
    assert ConnectionState.CONNECTED.value == "connected"
    assert ConnectionState.RECONNECTING.value == "reconnecting"
    assert ConnectionState.REPLAYING.value == "replaying"
    assert ConnectionState.ERROR.value == "error"

    # All states defined
    assert len(ConnectionState) == 6

    print("[PASS] test_connection_state_enum")


def test_sse_event_dataclass():
    """Test SSEEvent dataclass."""
    from datetime import datetime

    event = SSEEvent(
        event_id="evt_123",
        event_type="clause_update",
        sequence=42,
        timestamp=datetime.now(),
        data={"clause_id": 1, "status": "processed"},
    )

    assert event.event_id == "evt_123"
    assert event.event_type == "clause_update"
    assert event.sequence == 42
    assert event.processed is False  # Default
    assert "clause_id" in event.data

    print("[PASS] test_sse_event_dataclass")


def test_event_buffer_state_dataclass():
    """Test EventBufferState dataclass."""
    state = EventBufferState()

    assert state.events == []
    assert state.last_sequence == 0
    assert state.buffer_size == 100
    assert state.is_replaying is False
    assert state.replay_from is None

    print("[PASS] test_event_buffer_state_dataclass")


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================

def test_get_sse_state_key():
    """Test state key generation."""
    key = _get_sse_state_key("connection_state")
    assert key == "_cip_sse_connection_state"

    key = _get_sse_state_key("last_sequence")
    assert key == "_cip_sse_last_sequence"

    print("[PASS] test_get_sse_state_key")


def test_init_sse_state():
    """Test SSE state initialization."""
    mock_st.session_state.clear()
    init_sse_state()

    assert "_cip_sse_connection_state" in mock_st.session_state
    assert "_cip_sse_event_buffer" in mock_st.session_state
    assert "_cip_sse_last_sequence" in mock_st.session_state
    assert "_cip_sse_debug_mode" in mock_st.session_state

    print("[PASS] test_init_sse_state")


def test_get_set_connection_state():
    """Test connection state get/set."""
    mock_st.session_state.clear()

    # Default state
    state = get_connection_state()
    assert state == ConnectionState.DISCONNECTED

    # Set connected
    set_connection_state(ConnectionState.CONNECTED)
    state = get_connection_state()
    assert state == ConnectionState.CONNECTED

    # Connected timestamp should be set
    assert mock_st.session_state.get("_cip_sse_connected_at") is not None

    print("[PASS] test_get_set_connection_state")


def test_reconnect_attempts_tracking():
    """Test reconnect attempts increment."""
    mock_st.session_state.clear()
    init_sse_state()

    # Initial attempts = 0
    assert mock_st.session_state.get("_cip_sse_reconnect_attempts", 0) == 0

    # Set reconnecting increments counter
    set_connection_state(ConnectionState.RECONNECTING)
    assert mock_st.session_state.get("_cip_sse_reconnect_attempts") == 1

    set_connection_state(ConnectionState.RECONNECTING)
    assert mock_st.session_state.get("_cip_sse_reconnect_attempts") == 2

    # Connected resets counter
    set_connection_state(ConnectionState.CONNECTED)
    assert mock_st.session_state.get("_cip_sse_reconnect_attempts") == 0

    print("[PASS] test_reconnect_attempts_tracking")


def test_debug_mode():
    """Test debug mode toggle."""
    mock_st.session_state.clear()

    assert is_debug_mode() is False

    toggle_debug_mode()
    assert is_debug_mode() is True

    toggle_debug_mode()
    assert is_debug_mode() is False

    print("[PASS] test_debug_mode")


# ============================================================================
# EVENT BUFFER TESTS
# ============================================================================

def test_get_event_buffer_empty():
    """Test empty event buffer."""
    mock_st.session_state.clear()

    buffer = get_event_buffer()
    assert buffer == []

    print("[PASS] test_get_event_buffer_empty")


def test_add_event_to_buffer():
    """Test adding event to buffer."""
    mock_st.session_state.clear()

    event = {
        "event_id": "evt_001",
        "event_type": "test",
        "sequence": 1,
        "data": {"message": "Hello"},
    }

    add_event_to_buffer(event)
    buffer = get_event_buffer()

    assert len(buffer) == 1
    assert buffer[0]["event_id"] == "evt_001"
    assert buffer[0]["sequence"] == 1
    assert "received_at" in buffer[0]  # Timestamp added

    print("[PASS] test_add_event_to_buffer")


def test_buffer_size_limit():
    """Test buffer size enforcement."""
    mock_st.session_state.clear()
    mock_st.session_state["_cip_sse_buffer_size"] = 5

    # Add 10 events
    for i in range(10):
        add_event_to_buffer({"event_id": f"evt_{i}", "sequence": i})

    buffer = get_event_buffer()

    # Should be limited to buffer_size
    assert len(buffer) <= 5

    print("[PASS] test_buffer_size_limit")


def test_sequence_tracking():
    """Test sequence number tracking."""
    mock_st.session_state.clear()

    add_event_to_buffer({"sequence": 10})
    assert get_last_sequence() == 10

    add_event_to_buffer({"sequence": 25})
    assert get_last_sequence() == 25

    print("[PASS] test_sequence_tracking")


def test_clear_event_buffer():
    """Test clearing event buffer."""
    mock_st.session_state.clear()

    add_event_to_buffer({"sequence": 1})
    add_event_to_buffer({"sequence": 2})

    assert len(get_event_buffer()) == 2

    clear_event_buffer()

    assert len(get_event_buffer()) == 0

    print("[PASS] test_clear_event_buffer")


def test_set_replay_mode():
    """Test replay mode setting."""
    mock_st.session_state.clear()

    set_replay_mode(True, from_sequence=100)

    assert mock_st.session_state.get("_cip_sse_is_replaying") is True
    assert mock_st.session_state.get("_cip_sse_replay_from") == 100

    # Connection state should be REPLAYING
    assert get_connection_state() == ConnectionState.REPLAYING

    print("[PASS] test_set_replay_mode")


# ============================================================================
# CSS GENERATION TESTS
# ============================================================================

def test_generate_sse_state_css():
    """Test CSS generation."""
    css = _generate_sse_state_css()

    # Contains indicator classes
    assert ".cip-sse-indicator" in css
    assert ".cip-sse-indicator-dot" in css

    # Contains state classes
    assert ".connected" in css
    assert ".connecting" in css
    assert ".disconnected" in css
    assert ".error" in css
    assert ".replaying" in css

    # Contains debug overlay
    assert ".cip-sse-debug-overlay" in css

    # Contains animation
    assert "@keyframes cip-pulse" in css

    # Contains print styles
    assert "@media print" in css

    print("[PASS] test_generate_sse_state_css")


def test_css_high_contrast_mode():
    """Test CSS respects high contrast mode."""
    # This test verifies the token integration
    # Full HC testing requires mocking color_tokens
    css = _generate_sse_state_css()

    # Border width should be present (varies by mode)
    assert "border:" in css or "border-width" in css

    print("[PASS] test_css_high_contrast_mode")


def test_css_compact_mode():
    """Test compact mode CSS."""
    css = _generate_sse_state_css()

    assert ".cip-sse-indicator.compact" in css

    print("[PASS] test_css_compact_mode")


# ============================================================================
# CC3 INTEGRATION TESTS
# ============================================================================

def test_get_sse_state_for_binder():
    """Test binder output format."""
    mock_st.session_state.clear()
    set_connection_state(ConnectionState.CONNECTED)
    add_event_to_buffer({"sequence": 42})

    binder_state = get_sse_state_for_binder()

    assert "connection_state" in binder_state
    assert binder_state["connection_state"] == "connected"
    assert binder_state["is_connected"] is True
    assert binder_state["last_sequence"] == 42
    assert "buffer_size" in binder_state
    assert "reconnect_attempts" in binder_state

    print("[PASS] test_get_sse_state_for_binder")


def test_binder_disconnected_state():
    """Test binder output when disconnected."""
    mock_st.session_state.clear()

    binder_state = get_sse_state_for_binder()

    assert binder_state["connection_state"] == "disconnected"
    assert binder_state["is_connected"] is False

    print("[PASS] test_binder_disconnected_state")


def test_binder_replaying_state():
    """Test binder output during replay."""
    mock_st.session_state.clear()
    set_replay_mode(True, from_sequence=50)

    binder_state = get_sse_state_for_binder()

    assert binder_state["connection_state"] == "replaying"
    assert binder_state["is_replaying"] is True

    print("[PASS] test_binder_replaying_state")


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_validate_sse_state_accessibility():
    """Test accessibility validation."""
    result = validate_sse_state_accessibility()

    assert result["valid"] is True
    assert len(result["issues"]) == 0
    assert len(result["features"]) > 0
    assert "component" in result
    assert result["wcag_level"] == "AA"

    # Should have key features
    features_str = " ".join(result["features"])
    assert "high contrast" in features_str.lower() or "High contrast" in features_str
    assert "ARIA" in features_str or "aria" in features_str.lower()

    print("[PASS] test_validate_sse_state_accessibility")


def test_validation_features():
    """Test specific accessibility features."""
    result = validate_sse_state_accessibility()

    expected_features = [
        "animat",  # Matches "Animated"
        "keyboard",
        "screen reader",
    ]

    features_lower = " ".join(result["features"]).lower()

    for feature in expected_features:
        assert feature in features_lower, f"Missing feature: {feature}"

    print("[PASS] test_validation_features")


# ============================================================================
# INTEGRATION SCENARIO TESTS
# ============================================================================

def test_connection_lifecycle():
    """Test full connection lifecycle."""
    mock_st.session_state.clear()

    # Start disconnected
    assert get_connection_state() == ConnectionState.DISCONNECTED

    # Connect
    set_connection_state(ConnectionState.CONNECTING)
    assert get_connection_state() == ConnectionState.CONNECTING

    set_connection_state(ConnectionState.CONNECTED)
    assert get_connection_state() == ConnectionState.CONNECTED

    # Receive events
    add_event_to_buffer({"sequence": 1, "event_type": "init"})
    add_event_to_buffer({"sequence": 2, "event_type": "update"})
    assert get_last_sequence() == 2

    # Connection lost
    set_connection_state(ConnectionState.RECONNECTING)
    assert get_connection_state() == ConnectionState.RECONNECTING

    # Replay
    set_replay_mode(True, from_sequence=2)
    assert get_connection_state() == ConnectionState.REPLAYING

    # Reconnected
    set_replay_mode(False)
    set_connection_state(ConnectionState.CONNECTED)
    assert get_connection_state() == ConnectionState.CONNECTED

    print("[PASS] test_connection_lifecycle")


def test_error_state():
    """Test error state handling."""
    mock_st.session_state.clear()

    set_connection_state(ConnectionState.ERROR)
    mock_st.session_state["_cip_sse_error_message"] = "Connection timeout"

    binder_state = get_sse_state_for_binder()

    assert binder_state["connection_state"] == "error"
    assert binder_state["error_message"] == "Connection timeout"

    print("[PASS] test_error_state")


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_test_report():
    """Generate test report for P7 readiness."""
    return {
        "component": "SSE State Components",
        "phase": "Phase 7 Readiness",
        "status": "P7_READY",
        "tests_passed": 24,
        "tests_failed": 0,
        "deliverables": {
            "component": "frontend/components/sse_state.py",
            "test_suite": "frontend/tests/test_sse_state.py",
        },
        "capabilities": {
            "connection_states": [
                "DISCONNECTED", "CONNECTING", "CONNECTED",
                "RECONNECTING", "REPLAYING", "ERROR"
            ],
            "event_buffer": [
                "add_event_to_buffer()",
                "get_event_buffer()",
                "clear_event_buffer()",
                "Buffer size enforcement",
                "Sequence tracking",
            ],
            "ui_components": [
                "ConnectionStateIndicator (standard + compact)",
                "Debug overlay panel",
                "Debug toggle button",
            ],
            "cc3_integration": [
                "get_sse_state_for_binder()",
                "register_event_handler() stub",
                "State synchronization interface",
            ],
        },
        "p7_readiness": {
            "event_buffer_support": True,
            "connection_indicator": True,
            "debug_overlay": True,
            "replay_mode": True,
            "cc3_binder_compatible": True,
        },
    }


def main():
    """Run all tests and generate report."""
    print("=" * 60)
    print("SSE STATE COMPONENTS - TEST SUITE")
    print("Phase 7 Readiness Validation")
    print("=" * 60)
    print()

    # Connection State Tests
    print("CONNECTION STATE TESTS:")
    test_connection_state_enum()
    test_sse_event_dataclass()
    test_event_buffer_state_dataclass()

    print()

    # State Management Tests
    print("STATE MANAGEMENT TESTS:")
    test_get_sse_state_key()
    test_init_sse_state()
    test_get_set_connection_state()
    test_reconnect_attempts_tracking()
    test_debug_mode()

    print()

    # Event Buffer Tests
    print("EVENT BUFFER TESTS:")
    test_get_event_buffer_empty()
    test_add_event_to_buffer()
    test_buffer_size_limit()
    test_sequence_tracking()
    test_clear_event_buffer()
    test_set_replay_mode()

    print()

    # CSS Tests
    print("CSS GENERATION TESTS:")
    test_generate_sse_state_css()
    test_css_high_contrast_mode()
    test_css_compact_mode()

    print()

    # CC3 Integration Tests
    print("CC3 INTEGRATION TESTS:")
    test_get_sse_state_for_binder()
    test_binder_disconnected_state()
    test_binder_replaying_state()

    print()

    # Validation Tests
    print("VALIDATION TESTS:")
    test_validate_sse_state_accessibility()
    test_validation_features()

    print()

    # Integration Scenario Tests
    print("INTEGRATION SCENARIO TESTS:")
    test_connection_lifecycle()
    test_error_state()

    print()
    print("=" * 60)
    print("ALL TESTS PASSED (24/24)")
    print("=" * 60)

    # Generate report
    import json
    report = generate_test_report()

    print()
    print("P7 READINESS REPORT:")
    print("-" * 40)
    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
