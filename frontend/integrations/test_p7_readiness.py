"""
P7 Readiness Test Suite
Phase 7 Preparation - CC3 Verification

Tests for:
1. EventBuffer stub functionality
2. SequenceValidator
3. WorkspaceSSEBridge
4. Scroll and highlight routing hooks
5. Mock SSE client

CC3 P7-PREP - Readiness Tests
"""

import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_event_buffer():
    """Test 1: EventBuffer stub functionality."""
    from integrations.event_buffer_stub import (
        EventBuffer,
        EventEnvelope,
        ConnectionState,
    )

    results = []

    buffer = EventBuffer()

    # Test initial state
    results.append({
        "test": "initial_state",
        "passed": buffer.get_connection_state() == ConnectionState.DISCONNECTED,
    })

    # Test push event
    event = EventEnvelope(
        event_id="test-1",
        event_type="test_event",
        sequence_number=1,
        timestamp=datetime.now().isoformat(),
        payload={"data": "test"},
    )
    valid = buffer.push(event)
    results.append({
        "test": "push_event",
        "passed": valid and len(buffer.get_recent(10)) == 1,
    })

    # Test event handler
    handler_called = {"value": False}
    def handler(e):
        handler_called["value"] = True
    buffer.on_event("test_event", handler)
    buffer.push(EventEnvelope(
        event_id="test-2",
        event_type="test_event",
        sequence_number=2,
        timestamp=datetime.now().isoformat(),
        payload={},
    ))
    results.append({
        "test": "event_handler",
        "passed": handler_called["value"],
    })

    # Test connection state
    buffer.set_connection_state(ConnectionState.CONNECTED)
    results.append({
        "test": "connection_state",
        "passed": buffer.get_connection_state() == ConnectionState.CONNECTED,
    })

    # Test state change callback
    callback_state = {"value": None}
    buffer.on_state_change(lambda s: callback_state.__setitem__("value", s))
    buffer.set_connection_state(ConnectionState.RECONNECTING)
    results.append({
        "test": "state_change_callback",
        "passed": callback_state["value"] == ConnectionState.RECONNECTING,
    })

    return results


def test_sequence_validator():
    """Test 2: SequenceValidator functionality."""
    from integrations.event_buffer_stub import SequenceValidator

    results = []

    validator = SequenceValidator()

    # Test valid sequence
    results.append({
        "test": "first_sequence",
        "passed": validator.validate(1),
    })

    # Test consecutive sequence
    results.append({
        "test": "consecutive_sequence",
        "passed": validator.validate(2) and validator.validate(3),
    })

    # Test gap detection
    gap_detected = {"value": False}
    validator.on_gap(lambda start, end: gap_detected.__setitem__("value", True))
    valid = validator.validate(10)  # Gap from 4-9
    results.append({
        "test": "gap_detection",
        "passed": not valid and gap_detected["value"],
    })

    # Test gaps list
    gaps = validator.get_gaps()
    results.append({
        "test": "gaps_list",
        "passed": len(gaps) == 1 and gaps[0] == (4, 9),
    })

    # Test reset
    validator.reset()
    results.append({
        "test": "reset",
        "passed": len(validator.get_gaps()) == 0,
    })

    return results


def test_mock_sse_client():
    """Test 3: MockSSEClient functionality."""
    from integrations.event_buffer_stub import (
        EventBuffer,
        MockSSEClient,
        ConnectionState,
    )

    results = []

    buffer = EventBuffer()
    client = MockSSEClient(buffer)

    # Test initial state
    results.append({
        "test": "initial_disconnected",
        "passed": not client.is_connected(),
    })

    # Test connect
    client.connect()
    results.append({
        "test": "connect",
        "passed": client.is_connected() and buffer.get_connection_state() == ConnectionState.CONNECTED,
    })

    # Test simulate event
    event = client.simulate_event("test_type", {"key": "value"})
    results.append({
        "test": "simulate_event",
        "passed": event.event_type == "test_type" and event.sequence_number == 1,
    })

    # Test simulate scroll highlight
    scroll_event = client.simulate_scroll_highlight(clause_id=5, panel="left")
    results.append({
        "test": "simulate_scroll_highlight",
        "passed": scroll_event.payload["clause_id"] == 5,
    })

    # Test disconnect
    client.disconnect()
    results.append({
        "test": "disconnect",
        "passed": not client.is_connected(),
    })

    return results


def test_workspace_sse_bridge():
    """Test 4: WorkspaceSSEBridge functionality."""
    from integrations.workspace_sse_bridge import (
        WorkspaceSSEBridge,
        WorkspaceEventType,
    )
    from integrations.workspace_mode import (
        WorkspaceController,
        AlignedClausePair,
        PanelPosition,
    )
    from integrations.event_buffer_stub import ConnectionState

    results = []

    # Setup
    controller = WorkspaceController()
    pairs = [AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1)]
    controller.initialize(pairs)

    bridge = WorkspaceSSEBridge(controller)

    # Test initial state
    indicator = bridge.get_connection_indicator()
    results.append({
        "test": "initial_disconnected",
        "passed": indicator.state == ConnectionState.DISCONNECTED,
    })

    # Test connect
    bridge.connect()
    indicator = bridge.get_connection_indicator()
    results.append({
        "test": "connect",
        "passed": indicator.state == ConnectionState.CONNECTED,
    })

    # Test simulate scroll
    scroll_routed = {"value": False}
    bridge.get_scroll_hook().on_scroll_routed(lambda e: scroll_routed.__setitem__("value", True))
    bridge.simulate_scroll("left", 100.0)
    results.append({
        "test": "scroll_routing",
        "passed": scroll_routed["value"],
    })

    # Test simulate highlight
    highlight_routed = {"value": False}
    bridge.get_highlight_hook().on_highlight_routed(lambda e: highlight_routed.__setitem__("value", True))
    bridge.simulate_highlight(clause_id=5, panel="center")
    results.append({
        "test": "highlight_routing",
        "passed": highlight_routed["value"],
    })

    # Test active highlights
    highlights = bridge.get_highlight_hook().get_active_highlights()
    results.append({
        "test": "active_highlights",
        "passed": 5 in highlights,
    })

    # Test export state
    state = bridge.export_state()
    results.append({
        "test": "export_state",
        "passed": (
            "connection_state" in state and
            "events_buffered" in state and
            "controller_state" in state
        ),
    })

    # Test disconnect
    bridge.disconnect()
    results.append({
        "test": "disconnect",
        "passed": bridge.get_connection_indicator().state == ConnectionState.DISCONNECTED,
    })

    return results


def test_scroll_routing_hook():
    """Test 5: ScrollRoutingHook functionality."""
    from integrations.workspace_sse_bridge import ScrollRoutingHook
    from integrations.workspace_mode import (
        WorkspaceController,
        AlignedClausePair,
        PanelPosition,
    )
    from integrations.event_buffer_stub import EventEnvelope
    from datetime import datetime

    results = []

    controller = WorkspaceController()
    pairs = [AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1)]
    controller.initialize(pairs)

    hook = ScrollRoutingHook(controller)

    # Test handle SSE scroll
    event = EventEnvelope(
        event_id="scroll-1",
        event_type="scroll_sync",
        sequence_number=1,
        timestamp=datetime.now().isoformat(),
        payload={"source_panel": "left", "offset": 150.0},
    )
    result = hook.handle_sse_scroll(event)
    results.append({
        "test": "handle_sse_scroll",
        "passed": result is not None and result.source_offset == 150.0,
    })

    # Test event log
    log = hook.get_event_log()
    results.append({
        "test": "event_log",
        "passed": len(log) == 1,
    })

    # Test callback
    callback_data = {"called": False}
    hook.on_scroll_routed(lambda e: callback_data.__setitem__("called", True))
    hook.handle_sse_scroll(EventEnvelope(
        event_id="scroll-2",
        event_type="scroll_sync",
        sequence_number=2,
        timestamp=datetime.now().isoformat(),
        payload={"source_panel": "right", "offset": 200.0},
    ))
    results.append({
        "test": "scroll_callback",
        "passed": callback_data["called"],
    })

    return results


def test_highlight_routing_hook():
    """Test 6: HighlightRoutingHook functionality."""
    from integrations.workspace_sse_bridge import HighlightRoutingHook
    from integrations.workspace_mode import PanelPosition
    from integrations.event_buffer_stub import EventEnvelope
    from datetime import datetime

    results = []

    hook = HighlightRoutingHook()

    # Test highlight
    event = EventEnvelope(
        event_id="highlight-1",
        event_type="highlight_clause",
        sequence_number=1,
        timestamp=datetime.now().isoformat(),
        payload={"clause_id": 10, "panel": "left", "action": "highlight"},
    )
    result = hook.handle_sse_highlight(event)
    results.append({
        "test": "handle_highlight",
        "passed": result is not None and result.clause_id == 10,
    })

    # Test active highlights
    highlights = hook.get_active_highlights()
    results.append({
        "test": "active_highlight_added",
        "passed": 10 in highlights and highlights[10] == PanelPosition.LEFT,
    })

    # Test unhighlight
    unhighlight_event = EventEnvelope(
        event_id="highlight-2",
        event_type="highlight_clause",
        sequence_number=2,
        timestamp=datetime.now().isoformat(),
        payload={"clause_id": 10, "action": "unhighlight"},
    )
    hook.handle_sse_highlight(unhighlight_event)
    results.append({
        "test": "unhighlight",
        "passed": 10 not in hook.get_active_highlights(),
    })

    # Test clear all
    hook.handle_sse_highlight(EventEnvelope(
        event_id="highlight-3",
        event_type="highlight_clause",
        sequence_number=3,
        timestamp=datetime.now().isoformat(),
        payload={"clause_id": 20, "action": "highlight"},
    ))
    hook.clear_all_highlights()
    results.append({
        "test": "clear_all",
        "passed": len(hook.get_active_highlights()) == 0,
    })

    return results


def run_all_tests():
    """Run all P7 readiness tests."""
    all_results = []

    test_suites = [
        ("EventBuffer Stub", test_event_buffer),
        ("Sequence Validator", test_sequence_validator),
        ("Mock SSE Client", test_mock_sse_client),
        ("Workspace SSE Bridge", test_workspace_sse_bridge),
        ("Scroll Routing Hook", test_scroll_routing_hook),
        ("Highlight Routing Hook", test_highlight_routing_hook),
    ]

    for suite_name, test_func in test_suites:
        try:
            results = test_func()
            all_results.append({
                "suite": suite_name,
                "status": "PASSED" if all(r.get("passed", False) for r in results) else "FAILED",
                "tests": results,
            })
        except Exception as e:
            all_results.append({
                "suite": suite_name,
                "status": "ERROR",
                "error": str(e),
            })

    total_suites = len(all_results)
    passed_suites = sum(1 for r in all_results if r["status"] == "PASSED")
    total_tests = sum(len(r.get("tests", [])) for r in all_results)
    passed_tests = sum(
        sum(1 for t in r.get("tests", []) if t.get("passed", False))
        for r in all_results
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "task": "P7-PREP",
        "agent": "CC3",
        "summary": {
            "suites_total": total_suites,
            "suites_passed": passed_suites,
            "tests_total": total_tests,
            "tests_passed": passed_tests,
            "overall_status": "PASS" if passed_suites == total_suites else "FAIL",
        },
        "results": all_results,
    }


if __name__ == "__main__":
    report = run_all_tests()

    print("\n" + "=" * 60)
    print("CC3 P7 READINESS TEST REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Task: {report['task']}")
    print(f"Agent: {report['agent']}")
    print(f"Overall Status: {report['summary']['overall_status']}")
    print(f"Suites: {report['summary']['suites_passed']}/{report['summary']['suites_total']} passed")
    print(f"Tests: {report['summary']['tests_passed']}/{report['summary']['tests_total']} passed")
    print("=" * 60)

    for result in report["results"]:
        status_icon = "PASS" if result["status"] == "PASSED" else "FAIL"
        print(f"\n[{status_icon}] {result['suite']}")
        if "tests" in result:
            for test in result["tests"]:
                test_icon = "+" if test.get("passed") else "-"
                print(f"  {test_icon} {test.get('test', 'unknown')}")
        if "error" in result:
            print(f"  ERROR: {result['error']}")

    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "tests",
        "p7_readiness_test_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")
    sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
