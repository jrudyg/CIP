"""
P7.CC3.01 SSE Integration Test Suite
Tests for workspace SSE bindings, flow dispatcher, replay mode, and failure matrix

CC3 P7.CC3.01 - Integration Tests
Version: 1.0.0
"""

import json
import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_event_bindings():
    """Test 1: SSE Event Bindings."""
    from workspace.sse_integration.event_bindings import (
        PanelStateBinding,
        ScrollSyncBinding,
        HighlightBinding,
        IntelligenceUpdateBinding,
        BindingRegistry,
        SSEEventType,
        BindingResult,
    )
    from integrations.workspace_mode import (
        WorkspaceController,
        AlignedClausePair,
        ScrollAuthorityManager,
    )
    from integrations.event_buffer_stub import EventEnvelope

    results = []

    # Setup
    controller = WorkspaceController()
    pairs = [AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1)]
    controller.initialize(pairs)
    sat_manager = ScrollAuthorityManager()

    # Test PanelStateBinding
    panel_binding = PanelStateBinding(controller)
    event = EventEnvelope(
        event_id="ps-1",
        event_type="panel_state",
        sequence_number=1,
        timestamp=datetime.now().isoformat(),
        payload={"left_width": 40.0, "center_width": 30.0, "right_width": 30.0},
    )
    result = panel_binding.bind(event)
    results.append({
        "test": "panel_state_binding",
        "passed": result.success and controller.get_state().left_panel_width == 40.0,
    })

    # Test ScrollSyncBinding
    scroll_binding = ScrollSyncBinding(controller, sat_manager)
    event = EventEnvelope(
        event_id="ss-1",
        event_type="scroll_sync",
        sequence_number=2,
        timestamp=datetime.now().isoformat(),
        payload={"source_panel": "left", "offset": 200.0, "sync_mode": "locked"},
    )
    result = scroll_binding.bind(event)
    results.append({
        "test": "scroll_sync_binding",
        "passed": result.success,
    })

    # Test HighlightBinding
    highlight_binding = HighlightBinding()
    event = EventEnvelope(
        event_id="hl-1",
        event_type="highlight",
        sequence_number=3,
        timestamp=datetime.now().isoformat(),
        payload={"clause_id": 10, "panel": "center", "action": "add"},
    )
    result = highlight_binding.bind(event)
    results.append({
        "test": "highlight_binding",
        "passed": result.success and 10 in highlight_binding.get_active_highlights(),
    })

    # Test IntelligenceUpdateBinding
    intel_binding = IntelligenceUpdateBinding()
    event = EventEnvelope(
        event_id="iu-1",
        event_type="intelligence_update",
        sequence_number=4,
        timestamp=datetime.now().isoformat(),
        payload={"clause_id": 5, "engine": "SAE", "data": {"score": 0.95}},
    )
    result = intel_binding.bind(event)
    results.append({
        "test": "intelligence_update_binding",
        "passed": result.success and 5 in intel_binding.get_engine_data("SAE"),
    })

    # Test BindingRegistry
    registry = BindingRegistry()
    registry.register(panel_binding)
    registry.register(scroll_binding)
    registry.register(highlight_binding)
    registry.register(intel_binding)
    results.append({
        "test": "binding_registry",
        "passed": len(registry.get_all()) == 4,
    })

    # Test disable/enable
    registry.disable_all()
    disabled_result = panel_binding.bind(event)
    results.append({
        "test": "binding_disable",
        "passed": not disabled_result.success,
    })

    registry.enable_all()
    results.append({
        "test": "binding_enable",
        "passed": panel_binding.is_enabled(),
    })

    return results


def test_flow_dispatcher():
    """Test 2: SSE Flow Dispatcher."""
    from workspace.sse_integration.flow_dispatcher import (
        WorkspaceSSEDispatcher,
        WorkspaceSSEFlowMap,
        SSEFlowStage,
        FlowTrace,
    )
    from workspace.sse_integration.event_bindings import (
        BindingRegistry,
        PanelStateBinding,
    )
    from integrations.workspace_mode import WorkspaceController, AlignedClausePair
    from integrations.event_buffer_stub import EventBuffer, EventEnvelope

    results = []

    # Setup
    controller = WorkspaceController()
    pairs = [AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1)]
    controller.initialize(pairs)

    buffer = EventBuffer()
    registry = BindingRegistry()
    registry.register(PanelStateBinding(controller))

    dispatcher = WorkspaceSSEDispatcher(buffer, registry)

    # Test dispatch
    event = EventEnvelope(
        event_id="test-1",
        event_type="panel_state",
        sequence_number=1,
        timestamp=datetime.now().isoformat(),
        payload={"left_width": 35.0, "center_width": 30.0, "right_width": 35.0},
    )
    trace = dispatcher.dispatch(event)
    results.append({
        "test": "dispatch_success",
        "passed": trace.success and len(trace.stages) >= 4,
    })

    # Test flow stages
    stage_names = [s["stage"] for s in trace.stages]
    results.append({
        "test": "flow_stages_complete",
        "passed": (
            "ingress" in stage_names and
            "buffer" in stage_names and
            "validate" in stage_names and
            "complete" in stage_names
        ),
    })

    # Test replay mode
    dispatcher.set_replay_mode(True)
    results.append({
        "test": "replay_mode_set",
        "passed": dispatcher.is_replay_mode(),
    })

    trace2 = dispatcher.dispatch(EventEnvelope(
        event_id="test-2",
        event_type="panel_state",
        sequence_number=2,
        timestamp=datetime.now().isoformat(),
        payload={},
    ))
    skipped = any(s.get("data", {}).get("skipped") == "replay_mode" for s in trace2.stages)
    results.append({
        "test": "replay_mode_skip",
        "passed": skipped,
    })

    dispatcher.set_replay_mode(False)

    # Test flow stats
    stats = dispatcher.get_flow_stats()
    results.append({
        "test": "flow_stats",
        "passed": stats["total_events"] >= 2,
    })

    # Test flow map
    flow_map = WorkspaceSSEFlowMap.get_all_flows()
    results.append({
        "test": "flow_map_complete",
        "passed": len(flow_map) >= 8,  # All event types mapped
    })

    return results


def test_replay_mode():
    """Test 3: Replay Mode Controller."""
    from workspace.sse_integration.replay_mode import (
        ReplayModeController,
        ReplayState,
        ReplayProgress,
        ReplayIndicatorData,
        ReplayEventHandler,
    )
    from integrations.workspace_mode import ScrollAuthorityManager

    results = []

    sat_manager = ScrollAuthorityManager()
    controller = ReplayModeController(sat_manager)

    # Test initial state
    results.append({
        "test": "initial_idle",
        "passed": controller.get_state() == ReplayState.IDLE,
    })

    # Test start replay
    state_changes = []
    controller.on_state_change(lambda s: state_changes.append(s))

    controller.start_replay(start_sequence=1, end_sequence=100, estimated_total=100)
    results.append({
        "test": "replay_started",
        "passed": controller.is_replaying() and controller.get_state() == ReplayState.REPLAYING,
    })

    # Test progress tracking
    for i in range(10):
        controller.record_replay_event(i + 1)
    progress = controller.get_progress()
    results.append({
        "test": "replay_progress",
        "passed": progress.events_replayed == 10 and progress.get_progress_percent() == 10.0,
    })

    # Test end replay
    controller.end_replay()
    results.append({
        "test": "replay_ended",
        "passed": controller.get_state() == ReplayState.IDLE and not controller.is_replaying(),
    })

    # Test state callbacks
    results.append({
        "test": "state_callbacks",
        "passed": len(state_changes) >= 3,  # STARTING, REPLAYING, ENDING, IDLE
    })

    # Test indicator data - create fresh progress for indicator test
    fresh_progress = ReplayProgress(
        state=ReplayState.REPLAYING,
        events_replayed=10,
        estimated_total=100,
    )
    indicator = ReplayIndicatorData.from_progress(True, fresh_progress)
    results.append({
        "test": "indicator_data",
        "passed": indicator.events_replayed == 10 and len(indicator.message) > 0,
    })

    # Test abort
    controller.start_replay(1, 50)
    controller.abort_replay("Test error")
    results.append({
        "test": "replay_abort",
        "passed": controller.get_state() == ReplayState.ERROR,
    })

    # Test event handler
    sat_manager2 = ScrollAuthorityManager()
    controller2 = ReplayModeController(sat_manager2)
    handler = ReplayEventHandler(controller2)

    handler.handle_replay_start({"start_sequence": 1, "end_sequence": 50})
    results.append({
        "test": "event_handler_start",
        "passed": controller2.is_replaying(),
    })

    handler.handle_replay_end({"status": "complete"})
    results.append({
        "test": "event_handler_end",
        "passed": not controller2.is_replaying(),
    })

    return results


def test_failure_matrix():
    """Test 4: Workspace Failure Matrix."""
    from workspace.sse_integration.failure_matrix import (
        WorkspaceFailureMatrix,
        FailureMode,
        FailureSeverity,
        RecoveryStrategy,
        FailureInstance,
    )

    results = []

    matrix = WorkspaceFailureMatrix()

    # Test definitions
    defn = matrix.get_definition(FailureMode.SEQUENCE_GAP)
    results.append({
        "test": "definition_exists",
        "passed": defn is not None and defn.severity == FailureSeverity.HIGH,
    })

    # Test all definitions present
    results.append({
        "test": "all_definitions",
        "passed": len(matrix.DEFINITIONS) >= 8,
    })

    # Test report failure
    instance = matrix.report_failure(
        FailureMode.SEQUENCE_GAP,
        {"start": 5, "end": 10}
    )
    results.append({
        "test": "report_failure",
        "passed": instance.mode == FailureMode.SEQUENCE_GAP and instance.context["start"] == 5,
    })

    # Test active failures
    active = matrix.get_active_failures()
    results.append({
        "test": "active_failures",
        "passed": len(active) == 1,
    })

    # Test recovery
    success = matrix.attempt_recovery(instance)
    results.append({
        "test": "attempt_recovery",
        "passed": success,
    })

    # Test failure resolved
    results.append({
        "test": "failure_resolved",
        "passed": instance.is_resolved(),
    })

    # Test callbacks
    callback_data = {"failure": None, "recovery": None}
    matrix.on_failure(lambda f: callback_data.__setitem__("failure", f))
    matrix.on_recovery(lambda f: callback_data.__setitem__("recovery", f))

    instance2 = matrix.report_failure(FailureMode.HIGHLIGHT_ORPHAN)
    results.append({
        "test": "failure_callback",
        "passed": callback_data["failure"] is not None,
    })

    # Test stats
    stats = matrix.get_failure_stats()
    results.append({
        "test": "failure_stats",
        "passed": stats["total_failures"] >= 2,
    })

    # Test export matrix
    exported = matrix.export_matrix()
    results.append({
        "test": "export_matrix",
        "passed": len(exported) >= 8 and "recovery_strategy" in exported[0],
    })

    return results


def test_integration_flow():
    """Test 5: Full Integration Flow."""
    from workspace.sse_integration.event_bindings import (
        PanelStateBinding,
        ScrollSyncBinding,
        HighlightBinding,
        IntelligenceUpdateBinding,
        BindingRegistry,
    )
    from workspace.sse_integration.flow_dispatcher import WorkspaceSSEDispatcher
    from workspace.sse_integration.replay_mode import ReplayModeController
    from workspace.sse_integration.failure_matrix import WorkspaceFailureMatrix, FailureMode
    from integrations.workspace_mode import (
        WorkspaceController,
        AlignedClausePair,
        ScrollAuthorityManager,
    )
    from integrations.event_buffer_stub import EventBuffer, EventEnvelope

    results = []

    # Full setup
    controller = WorkspaceController()
    pairs = [AlignedClausePair(pair_id=i, v1_clause_id=i, v2_clause_id=i) for i in range(1, 6)]
    controller.initialize(pairs)

    sat_manager = controller._sat_manager
    buffer = EventBuffer()

    registry = BindingRegistry()
    registry.register(PanelStateBinding(controller))
    registry.register(ScrollSyncBinding(controller, sat_manager))
    registry.register(HighlightBinding())
    registry.register(IntelligenceUpdateBinding())

    dispatcher = WorkspaceSSEDispatcher(buffer, registry)
    replay_controller = ReplayModeController(sat_manager, dispatcher, registry)
    failure_matrix = WorkspaceFailureMatrix()

    # Test full event flow
    events = [
        EventEnvelope("e1", "panel_state", 1, datetime.now().isoformat(),
                      {"left_width": 35, "center_width": 30, "right_width": 35}),
        EventEnvelope("e2", "scroll_sync", 2, datetime.now().isoformat(),
                      {"source_panel": "left", "offset": 100}),
        EventEnvelope("e3", "highlight", 3, datetime.now().isoformat(),
                      {"clause_id": 1, "action": "add"}),
        EventEnvelope("e4", "intelligence_update", 4, datetime.now().isoformat(),
                      {"clause_id": 1, "engine": "SAE", "data": {"score": 0.9}}),
    ]

    traces = [dispatcher.dispatch(e) for e in events]
    results.append({
        "test": "full_event_flow",
        "passed": all(t.success for t in traces),
    })

    # Test sequence gap detection
    gap_event = EventEnvelope("e10", "panel_state", 10, datetime.now().isoformat(), {})
    dispatcher.dispatch(gap_event)
    gaps = buffer.get_sequence_validator().get_gaps()
    results.append({
        "test": "gap_detection",
        "passed": len(gaps) > 0,
    })

    # Report gap failure
    if gaps:
        failure_matrix.report_failure(FailureMode.SEQUENCE_GAP, {"gaps": gaps})
    results.append({
        "test": "gap_failure_reported",
        "passed": len(failure_matrix.get_active_failures()) > 0,
    })

    # Test replay integration
    replay_controller.start_replay(5, 9)
    results.append({
        "test": "replay_disables_bindings",
        "passed": not registry.get(list(registry.get_all().keys())[0]).is_enabled(),
    })

    replay_controller.end_replay()
    results.append({
        "test": "replay_enables_bindings",
        "passed": registry.get(list(registry.get_all().keys())[0]).is_enabled(),
    })

    # Test stats
    flow_stats = dispatcher.get_flow_stats()
    results.append({
        "test": "flow_stats_accurate",
        "passed": flow_stats["total_events"] >= 5,
    })

    return results


def run_all_tests():
    """Run all P7.CC3.01 integration tests."""
    all_results = []

    test_suites = [
        ("Event Bindings", test_event_bindings),
        ("Flow Dispatcher", test_flow_dispatcher),
        ("Replay Mode", test_replay_mode),
        ("Failure Matrix", test_failure_matrix),
        ("Integration Flow", test_integration_flow),
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
            import traceback
            all_results.append({
                "suite": suite_name,
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc(),
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
        "task": "P7.CC3.01",
        "module": "sse_integration",
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
    print("CC3 P7.CC3.01 BINDING INTEGRATION TEST REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Task: {report['task']}")
    print(f"Module: {report['module']}")
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

    # Save report
    report_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tests")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "p7_cc3_01_test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")
    sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
