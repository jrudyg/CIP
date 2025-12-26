"""
Phase 6 Workspace Mode Integration Tests
CC3 P6-INTEGRATION-PREP

Tests for:
1. Three-panel layout state management
2. Scroll synchronization engine
3. Multi-clause data flow patterns
4. SSE streaming mocks
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================================
# MOCK SSE EVENTS
# ============================================================================

MOCK_SSE_EVENTS = [
    {
        "event_type": "intelligence_update",
        "data": {
            "engine": "SAE",
            "clause_pair_id": 1,
            "similarity_score": 0.95,
            "match_confidence": "HIGH",
        },
        "sequence_id": 1,
    },
    {
        "event_type": "intelligence_update",
        "data": {
            "engine": "ERCE",
            "clause_pair_id": 1,
            "risk_category": "CRITICAL",
            "confidence": 0.92,
        },
        "sequence_id": 2,
    },
    {
        "event_type": "clause_highlight",
        "data": {
            "clause_id": 5,
            "panel": "left",
            "highlight_type": "risk",
            "color": "#DC2626",
        },
        "sequence_id": 3,
    },
    {
        "event_type": "scroll_sync",
        "data": {
            "source_panel": "left",
            "target_offset": 450.0,
            "active_clause_pair": 3,
        },
        "sequence_id": 4,
    },
    {
        "event_type": "engine_status",
        "data": {
            "engine": "BIRL",
            "status": "processing",
            "progress": 0.65,
        },
        "sequence_id": 5,
    },
]


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_workspace_state():
    """Test 1: Workspace state management."""
    from integrations.workspace_mode import (
        WorkspaceState,
        WorkspaceViewMode,
        ScrollSyncMode,
    )

    results = []

    # Create default state
    state = WorkspaceState()
    results.append({
        "test": "default_state_creation",
        "passed": state.view_mode == WorkspaceViewMode.COMPARISON,
    })

    # Test panel width management
    state.set_panel_widths(40, 20, 40)
    widths = state.get_panel_widths()
    results.append({
        "test": "panel_width_normalization",
        "passed": abs(sum(widths) - 100.0) < 0.01,
    })

    # Test intelligence toggle
    original_center = state.center_panel_width
    state.toggle_intelligence_panel()
    results.append({
        "test": "intelligence_panel_toggle",
        "passed": state.center_panel_width > original_center and state.intelligence_expanded,
    })

    # Test serialization
    state_dict = state.to_dict()
    restored = WorkspaceState.from_dict(state_dict)
    results.append({
        "test": "state_serialization",
        "passed": restored.intelligence_expanded == state.intelligence_expanded,
    })

    return results


def test_scroll_sync_engine():
    """Test 2: Scroll synchronization engine."""
    from integrations.workspace_mode import (
        ScrollSyncEngine,
        AlignedClausePair,
        ClausePosition,
        PanelPosition,
        ScrollSyncMode,
    )

    results = []

    # Create aligned pairs
    pairs = [
        AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1),
        AlignedClausePair(pair_id=2, v1_clause_id=2, v2_clause_id=3),
        AlignedClausePair(pair_id=3, v1_clause_id=3, v2_clause_id=None),  # Removed
        AlignedClausePair(pair_id=4, v1_clause_id=None, v2_clause_id=4),  # Added
    ]

    engine = ScrollSyncEngine(pairs)

    # Register positions
    engine.register_clause_position(ClausePosition(
        clause_id=1, panel=PanelPosition.LEFT, scroll_offset=0, height=100, visible=True
    ))
    engine.register_clause_position(ClausePosition(
        clause_id=1, panel=PanelPosition.RIGHT, scroll_offset=0, height=120, visible=True
    ))

    results.append({
        "test": "position_registration",
        "passed": True,  # No exception means success
    })

    # Test locked sync
    offset = engine.calculate_sync_offset(
        PanelPosition.LEFT, 100.0, PanelPosition.RIGHT, ScrollSyncMode.LOCKED
    )
    results.append({
        "test": "locked_sync_mode",
        "passed": offset == 100.0,
    })

    # Test free mode
    offset = engine.calculate_sync_offset(
        PanelPosition.LEFT, 100.0, PanelPosition.RIGHT, ScrollSyncMode.FREE
    )
    results.append({
        "test": "free_sync_mode",
        "passed": offset == -1,  # No sync indicator
    })

    # Test pair detection
    results.append({
        "test": "pair_added_detection",
        "passed": pairs[3].is_added(),
    })
    results.append({
        "test": "pair_removed_detection",
        "passed": pairs[2].is_removed(),
    })

    return results


def test_multi_clause_data_flow():
    """Test 3: Multi-clause data flow patterns."""
    from integrations.workspace_mode import (
        MultiClauseDataFlow,
        ClauseDataPacket,
        PanelPosition,
    )

    results = []

    flow = MultiClauseDataFlow()

    # Create packets
    packet1 = ClauseDataPacket(
        clause_id=1,
        panel=PanelPosition.LEFT,
        number="1.1",
        title="Indemnification",
        text="Contractor shall indemnify...",
    )

    flow.register_packet(packet1)

    # Retrieve packet
    retrieved = flow.get_packet(1, PanelPosition.LEFT)
    results.append({
        "test": "packet_registration",
        "passed": retrieved is not None and retrieved.title == "Indemnification",
    })

    # Attach intelligence
    flow.attach_intelligence(1, PanelPosition.LEFT, "ERCE", {
        "risk_category": "CRITICAL",
        "confidence": 0.95,
    })

    retrieved = flow.get_packet(1, PanelPosition.LEFT)
    results.append({
        "test": "intelligence_attachment",
        "passed": retrieved.erce_data is not None and retrieved.risk_level == "CRITICAL",
    })

    # Test has_intelligence
    results.append({
        "test": "has_intelligence_check",
        "passed": retrieved.has_intelligence(),
    })

    # Test risk badge
    results.append({
        "test": "risk_badge_extraction",
        "passed": retrieved.get_risk_badge() == "CRITICAL",
    })

    # Test callback
    callback_received = []
    flow.on_update(lambda p: callback_received.append(p.clause_id))
    flow.attach_intelligence(1, PanelPosition.LEFT, "SAE", {"similarity_score": 0.9})
    results.append({
        "test": "update_callback",
        "passed": 1 in callback_received,
    })

    return results


def test_sse_streaming():
    """Test 4: SSE streaming integration."""
    from integrations.workspace_mode import (
        SSEStreamHandler,
        SSEEvent,
        SSEEventType,
    )

    results = []

    handler = SSEStreamHandler()

    # Test connection
    handler.connect("mock://localhost/sse")
    results.append({
        "test": "sse_connection",
        "passed": handler.is_connected(),
    })

    # Test event handler registration
    received_events = []
    handler.on_event(SSEEventType.INTELLIGENCE_UPDATE, lambda e: received_events.append(e))

    # Create and dispatch event
    event = SSEEvent(
        event_type=SSEEventType.INTELLIGENCE_UPDATE,
        data={"engine": "SAE", "clause_pair_id": 1},
        timestamp="2025-12-09T20:00:00Z",
        sequence_id=1,
    )
    handler.dispatch_event(event)

    results.append({
        "test": "event_dispatch",
        "passed": len(received_events) == 1 and received_events[0].data["engine"] == "SAE",
    })

    # Test SSE format serialization
    sse_format = event.to_sse_format()
    results.append({
        "test": "sse_format_serialization",
        "passed": "event: intelligence_update" in sse_format and "data:" in sse_format,
    })

    # Test SSE format parsing
    parsed = SSEEvent.from_sse_format(sse_format)
    results.append({
        "test": "sse_format_parsing",
        "passed": parsed is not None and parsed.event_type == SSEEventType.INTELLIGENCE_UPDATE,
    })

    # Test disconnect
    handler.disconnect()
    results.append({
        "test": "sse_disconnect",
        "passed": not handler.is_connected(),
    })

    return results


def test_mock_sse_events():
    """Test 5: Process mock SSE events."""
    from integrations.workspace_mode import (
        SSEStreamHandler,
        SSEEvent,
        SSEEventType,
    )

    results = []

    handler = SSEStreamHandler()
    handler.connect("mock://localhost/sse")

    processed_events = []

    # Register handlers for all event types
    for event_type in SSEEventType:
        handler.on_event(event_type, lambda e: processed_events.append(e.event_type))

    # Process mock events
    for mock in MOCK_SSE_EVENTS:
        event = SSEEvent(
            event_type=SSEEventType(mock["event_type"]),
            data=mock["data"],
            timestamp="",
            sequence_id=mock["sequence_id"],
        )
        handler.dispatch_event(event)

    results.append({
        "test": "mock_events_processed",
        "passed": len(processed_events) == len(MOCK_SSE_EVENTS),
    })

    # Verify event types
    results.append({
        "test": "intelligence_events_received",
        "passed": SSEEventType.INTELLIGENCE_UPDATE in processed_events,
    })
    results.append({
        "test": "scroll_sync_events_received",
        "passed": SSEEventType.SCROLL_SYNC in processed_events,
    })

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all workspace mode tests and return report."""
    all_results = []

    test_suites = [
        ("Workspace State Management", test_workspace_state),
        ("Scroll Synchronization Engine", test_scroll_sync_engine),
        ("Multi-Clause Data Flow", test_multi_clause_data_flow),
        ("SSE Streaming Integration", test_sse_streaming),
        ("Mock SSE Events Processing", test_mock_sse_events),
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

    # Calculate totals
    total_suites = len(all_results)
    passed_suites = sum(1 for r in all_results if r["status"] == "PASSED")

    total_tests = sum(len(r.get("tests", [])) for r in all_results)
    passed_tests = sum(
        sum(1 for t in r.get("tests", []) if t.get("passed", False))
        for r in all_results
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 6 Preparation",
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
    # Run tests
    report = run_all_tests()

    # Print summary
    print("\n" + "=" * 60)
    print("CC3 PHASE 6 WORKSPACE MODE TEST REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Phase: {report['phase']}")
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

    # Save report
    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "tests",
        "workspace_mode_test_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
