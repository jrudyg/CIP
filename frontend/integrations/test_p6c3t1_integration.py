"""
P6.C3.T1 Integration Test Suite
Workspace Layout + Scroll Synchronization Integration

Tests for:
1. Scroll Authority Token (SAT) system
2. TopNav workspace mode binding
3. A11y scroll behavior
4. Diagnostic instrumentation hooks
5. Enhanced scroll sync engine
6. Workspace controller integration

CC3 P6.C3.T1 - Integration Test Suite
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_scroll_authority_token():
    """Test 1: Scroll Authority Token (SAT) system."""
    from integrations.workspace_mode import (
        ScrollAuthorityToken,
        ScrollAuthorityManager,
        PanelPosition,
    )

    results = []

    # Test token issuance
    token = ScrollAuthorityToken.issue(PanelPosition.LEFT)
    results.append({
        "test": "token_issuance",
        "passed": token.is_valid and token.holder_panel == PanelPosition.LEFT,
    })

    # Test token revocation
    token.revoke()
    results.append({
        "test": "token_revocation",
        "passed": not token.is_valid,
    })

    # Test manager authority request
    manager = ScrollAuthorityManager()
    token1 = manager.request_authority(PanelPosition.LEFT)
    results.append({
        "test": "manager_request_authority",
        "passed": token1 is not None and manager.get_current_holder() == PanelPosition.LEFT,
    })

    # Test authority transfer
    token2 = manager.request_authority(PanelPosition.RIGHT)
    results.append({
        "test": "authority_transfer",
        "passed": (
            manager.get_current_holder() == PanelPosition.RIGHT and
            not token1.is_valid and
            token2.is_valid
        ),
    })

    # Test token validation
    valid = manager.validate_token(token2)
    invalid = manager.validate_token(token1)
    results.append({
        "test": "token_validation",
        "passed": valid and not invalid,
    })

    # Test authority release
    manager.release_authority()
    results.append({
        "test": "authority_release",
        "passed": manager.get_current_holder() is None,
    })

    # Test callbacks
    callback_fired = {"lock": False, "release": False}
    manager.on_lock(lambda p: callback_fired.__setitem__("lock", True))
    manager.on_release(lambda p: callback_fired.__setitem__("release", True))
    manager.request_authority(PanelPosition.CENTER)
    manager.release_authority()
    results.append({
        "test": "callbacks",
        "passed": callback_fired["lock"] and callback_fired["release"],
    })

    # Test token history
    history = manager.get_token_history()
    results.append({
        "test": "token_history",
        "passed": len(history) >= 2,
    })

    return results


def test_topnav_workspace_binding():
    """Test 2: TopNav workspace mode binding."""
    from integrations.workspace_mode import (
        TopNavWorkspaceBinding,
        TopNavTab,
        WorkspaceViewMode,
        ScrollSyncMode,
        WorkspaceState,
    )

    results = []

    binding = TopNavWorkspaceBinding()

    # Test default tab
    results.append({
        "test": "default_tab",
        "passed": binding.get_current_tab() == TopNavTab.COMPARE,
    })

    # Test view mode mapping
    view_mode = binding.get_view_mode_for_tab(TopNavTab.INTELLIGENCE)
    results.append({
        "test": "view_mode_mapping",
        "passed": view_mode == WorkspaceViewMode.INTELLIGENCE,
    })

    # Test scroll mode mapping
    scroll_mode = binding.get_scroll_mode_for_tab(TopNavTab.COMPARE)
    results.append({
        "test": "scroll_mode_mapping",
        "passed": scroll_mode == ScrollSyncMode.CLAUSE_ALIGNED,
    })

    # Test preset retrieval
    preset = binding.get_preset_for_mode(WorkspaceViewMode.INTELLIGENCE)
    results.append({
        "test": "preset_retrieval",
        "passed": preset.center == 50.0 and preset.left == 25.0,
    })

    # Test set_active_tab
    view_mode, preset, scroll_mode = binding.set_active_tab(TopNavTab.REVIEW)
    results.append({
        "test": "set_active_tab",
        "passed": (
            view_mode == WorkspaceViewMode.REVIEW and
            scroll_mode == ScrollSyncMode.CLAUSE_ALIGNED and
            binding.get_current_tab() == TopNavTab.REVIEW
        ),
    })

    # Test tab change callback
    callback_data = {"called": False, "tab": None}
    def on_change(tab, mode):
        callback_data["called"] = True
        callback_data["tab"] = tab
    binding.on_tab_change(on_change)
    binding.set_active_tab(TopNavTab.RISK_ANALYSIS)
    results.append({
        "test": "tab_change_callback",
        "passed": callback_data["called"] and callback_data["tab"] == TopNavTab.RISK_ANALYSIS,
    })

    # Test apply_to_workspace_state
    state = WorkspaceState()
    binding.apply_to_workspace_state(TopNavTab.INTELLIGENCE, state)
    results.append({
        "test": "apply_to_workspace_state",
        "passed": (
            state.view_mode == WorkspaceViewMode.INTELLIGENCE and
            state.scroll_sync_mode == ScrollSyncMode.LOCKED and
            state.center_panel_width == 50.0
        ),
    })

    return results


def test_a11y_scroll_preferences():
    """Test 3: A11y scroll preferences."""
    from integrations.workspace_mode import A11yScrollPreferences

    results = []

    # Test default preferences
    prefs = A11yScrollPreferences()
    results.append({
        "test": "default_preferences",
        "passed": (
            not prefs.reduce_motion and
            prefs.smooth_scroll_duration_ms == 300 and
            prefs.keyboard_scroll_step == 100.0
        ),
    })

    # Test scroll behavior with motion
    results.append({
        "test": "scroll_behavior_smooth",
        "passed": prefs.get_scroll_behavior() == "smooth",
    })

    # Test scroll behavior with reduced motion
    prefs_reduced = A11yScrollPreferences(reduce_motion=True)
    results.append({
        "test": "scroll_behavior_auto",
        "passed": prefs_reduced.get_scroll_behavior() == "auto",
    })

    # Test transition duration with motion
    results.append({
        "test": "transition_duration_normal",
        "passed": prefs.get_transition_duration() == 300,
    })

    # Test transition duration with reduced motion
    results.append({
        "test": "transition_duration_reduced",
        "passed": prefs_reduced.get_transition_duration() == 0,
    })

    # Test serialization
    data = prefs.to_dict()
    results.append({
        "test": "to_dict",
        "passed": (
            "reduce_motion" in data and
            "smooth_scroll_duration_ms" in data and
            data["keyboard_scroll_step"] == 100.0
        ),
    })

    return results


def test_enhanced_scroll_engine():
    """Test 4: Enhanced scroll sync engine with SAT integration."""
    from integrations.workspace_mode import (
        EnhancedScrollSyncEngine,
        ScrollAuthorityManager,
        A11yScrollPreferences,
        AlignedClausePair,
        PanelPosition,
        ScrollSyncMode,
    )

    results = []

    # Create test data
    pairs = [
        AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1),
        AlignedClausePair(pair_id=2, v1_clause_id=2, v2_clause_id=2),
    ]

    # Test engine initialization
    sat_manager = ScrollAuthorityManager()
    a11y_prefs = A11yScrollPreferences()
    engine = EnhancedScrollSyncEngine(pairs, sat_manager, a11y_prefs)
    results.append({
        "test": "engine_initialization",
        "passed": engine.get_sat_manager() is sat_manager,
    })

    # Test handle_scroll with SAT
    scroll_results = engine.handle_scroll(
        PanelPosition.LEFT, 100.0, ScrollSyncMode.LOCKED
    )
    results.append({
        "test": "handle_scroll_sat",
        "passed": (
            PanelPosition.LEFT in scroll_results and
            sat_manager.get_current_holder() == PanelPosition.LEFT
        ),
    })

    # Test scroll callback registration
    callback_data = {"called": False}
    def on_scroll(panel, offset, mode):
        callback_data["called"] = True
    engine.on_scroll(on_scroll)
    engine.handle_scroll(PanelPosition.RIGHT, 200.0, ScrollSyncMode.LOCKED)
    results.append({
        "test": "scroll_callback",
        "passed": callback_data["called"],
    })

    # Test A11y scroll params
    params = engine.get_a11y_scroll_params()
    results.append({
        "test": "a11y_scroll_params",
        "passed": (
            params["behavior"] == "smooth" and
            params["duration"] == 300 and
            params["step"] == 100.0
        ),
    })

    # Test with reduced motion
    engine_reduced = EnhancedScrollSyncEngine(
        pairs,
        ScrollAuthorityManager(),
        A11yScrollPreferences(reduce_motion=True)
    )
    params_reduced = engine_reduced.get_a11y_scroll_params()
    results.append({
        "test": "a11y_reduced_motion",
        "passed": params_reduced["behavior"] == "auto" and params_reduced["duration"] == 0,
    })

    return results


def test_workspace_controller():
    """Test 5: Workspace controller integration."""
    from integrations.workspace_mode import (
        WorkspaceController,
        TopNavTab,
        WorkspaceViewMode,
        ScrollSyncMode,
        PanelPosition,
        AlignedClausePair,
        A11yScrollPreferences,
    )

    results = []

    # Test controller initialization
    controller = WorkspaceController()
    state = controller.get_state()
    results.append({
        "test": "controller_initialization",
        "passed": state.view_mode == WorkspaceViewMode.COMPARISON,
    })

    # Test initialize with pairs
    pairs = [AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1)]
    controller.initialize(pairs)
    results.append({
        "test": "initialize_with_pairs",
        "passed": controller._scroll_engine is not None,
    })

    # Test set_tab
    new_state = controller.set_tab(TopNavTab.INTELLIGENCE)
    results.append({
        "test": "set_tab",
        "passed": (
            new_state.view_mode == WorkspaceViewMode.INTELLIGENCE and
            new_state.scroll_sync_mode == ScrollSyncMode.LOCKED
        ),
    })

    # Test handle_scroll
    scroll_results = controller.handle_scroll(PanelPosition.LEFT, 150.0)
    results.append({
        "test": "handle_scroll",
        "passed": (
            PanelPosition.LEFT in scroll_results and
            controller.get_state().scroll_state.left_offset == 150.0
        ),
    })

    # Test set_scroll_mode
    controller.set_scroll_mode(ScrollSyncMode.FREE)
    results.append({
        "test": "set_scroll_mode",
        "passed": controller.get_state().scroll_sync_mode == ScrollSyncMode.FREE,
    })

    # Test set_a11y_preferences
    prefs = A11yScrollPreferences(reduce_motion=True)
    controller.set_a11y_preferences(prefs)
    results.append({
        "test": "set_a11y_preferences",
        "passed": controller._a11y_prefs.reduce_motion,
    })

    # Test state change callback
    callback_data = {"called": False}
    def on_change(state):
        callback_data["called"] = True
    controller.on_state_change(on_change)
    controller.set_scroll_mode(ScrollSyncMode.LOCKED)
    results.append({
        "test": "state_change_callback",
        "passed": callback_data["called"],
    })

    # Test export_state
    exported = controller.export_state()
    results.append({
        "test": "export_state",
        "passed": (
            "workspace_state" in exported and
            "current_tab" in exported and
            "a11y_prefs" in exported
        ),
    })

    return results


def test_diagnostic_integration():
    """Test 6: Diagnostic instrumentation hooks."""
    from integrations.workspace_mode import (
        WorkspaceController,
        EnhancedScrollSyncEngine,
        AlignedClausePair,
        PanelPosition,
        ScrollSyncMode,
    )
    from integrations.layout_diagnostics import LayoutDiagnosticPanel

    results = []

    # Test attach diagnostics to engine
    pairs = [AlignedClausePair(pair_id=1, v1_clause_id=1, v2_clause_id=1)]
    engine = EnhancedScrollSyncEngine(pairs)
    diag_panel = LayoutDiagnosticPanel()
    engine.attach_diagnostics(diag_panel)
    results.append({
        "test": "attach_diagnostics_engine",
        "passed": engine._diagnostic_panel is diag_panel,
    })

    # Test scroll logging to diagnostics
    engine.handle_scroll(PanelPosition.LEFT, 100.0, ScrollSyncMode.LOCKED)
    logs = diag_panel.get_logs(source="scroll_sync")
    results.append({
        "test": "scroll_diagnostic_logging",
        "passed": len(logs) >= 1,
    })

    # Test attach diagnostics to controller
    controller = WorkspaceController()
    controller.initialize(pairs)
    controller.attach_diagnostics(diag_panel)
    results.append({
        "test": "attach_diagnostics_controller",
        "passed": controller._diagnostic_panel is diag_panel,
    })

    # Test get_diagnostic_report
    report = controller.get_diagnostic_report()
    results.append({
        "test": "get_diagnostic_report",
        "passed": report is not None and "log_summary" in report,
    })

    # Test scroll events recorded
    controller.handle_scroll(PanelPosition.RIGHT, 200.0)
    events = diag_panel.scroll_monitor.get_events()
    results.append({
        "test": "scroll_events_recorded",
        "passed": len(events) >= 1,
    })

    return results


def test_module_metadata():
    """Test 7: Module metadata and version."""
    import integrations.workspace_mode as wm

    results = []

    # Test version
    results.append({
        "test": "version_6_1_0",
        "passed": wm.__version__ == "6.1.0",
    })

    # Test phase
    results.append({
        "test": "phase_p6c3t1",
        "passed": "P6.C3.T1" in wm.__phase__,
    })

    # Test features
    expected_features = [
        "scroll_authority_token",
        "topnav_workspace_binding",
        "a11y_scroll_behavior",
        "diagnostic_instrumentation",
        "enhanced_scroll_engine",
        "workspace_controller",
    ]
    results.append({
        "test": "features_complete",
        "passed": all(f in wm.__features__ for f in expected_features),
    })

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all P6.C3.T1 integration tests."""
    all_results = []

    test_suites = [
        ("Scroll Authority Token (SAT)", test_scroll_authority_token),
        ("TopNav Workspace Binding", test_topnav_workspace_binding),
        ("A11y Scroll Preferences", test_a11y_scroll_preferences),
        ("Enhanced Scroll Engine", test_enhanced_scroll_engine),
        ("Workspace Controller", test_workspace_controller),
        ("Diagnostic Integration", test_diagnostic_integration),
        ("Module Metadata", test_module_metadata),
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
        "task": "P6.C3.T1",
        "module": "workspace_mode",
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
    print("CC3 P6.C3.T1 INTEGRATION TEST REPORT")
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
    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "tests",
        "p6c3t1_integration_test_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
