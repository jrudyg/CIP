"""
Layout Diagnostics Test Module
Phase 6 - Non-Blocking Utility Tests

Tests for:
1. Panel dimension logger
2. Scroll synchronization event monitor
3. Panel position validator
4. Aggregate diagnostic panel

This test module is INDEPENDENT and verifies read-only behavior.

CC3 P6-LAYOUT-DIAGNOSTICS
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

def test_panel_dimension_logger():
    """Test 1: Panel dimension logger functionality."""
    from integrations.layout_diagnostics import (
        PanelDimensionLogger,
        PanelDimensions,
        PanelId,
    )

    results = []

    logger = PanelDimensionLogger(max_history=50)

    # Test single capture
    dims = logger.capture(
        panel_id=PanelId.LEFT.value,
        width_percent=35.0,
        width_pixels=350,
        height_pixels=800,
        visible=True
    )
    results.append({
        "test": "single_capture",
        "passed": dims.panel_id == "left" and dims.width_percent == 35.0,
    })

    # Test capture_all
    all_dims = logger.capture_all(
        left=(35.0, 350, 800, True),
        center=(30.0, 300, 800, True),
        right=(35.0, 350, 800, True),
    )
    results.append({
        "test": "capture_all",
        "passed": len(all_dims) == 3,
    })

    # Test get_latest
    latest = logger.get_latest(PanelId.CENTER.value)
    results.append({
        "test": "get_latest",
        "passed": latest is not None and latest.width_percent == 30.0,
    })

    # Test history filtering
    left_history = logger.get_history(PanelId.LEFT.value)
    results.append({
        "test": "history_filtering",
        "passed": len(left_history) == 2,  # Initial + capture_all
    })

    # Test snapshot count
    results.append({
        "test": "snapshot_count",
        "passed": logger.get_snapshot_count() == 4,  # 1 + 3
    })

    # Test export
    exported = logger.export_history()
    results.append({
        "test": "export_history",
        "passed": len(exported) == 4 and "panel_id" in exported[0],
    })

    # Test clear
    logger.clear()
    results.append({
        "test": "clear_history",
        "passed": len(logger.get_history()) == 0,
    })

    return results


def test_scroll_sync_monitor():
    """Test 2: Scroll synchronization event monitor."""
    from integrations.layout_diagnostics import (
        ScrollSyncMonitor,
        ScrollEvent,
    )

    results = []

    monitor = ScrollSyncMonitor(max_events=100)

    # Test initial state
    results.append({
        "test": "initial_state",
        "passed": not monitor.is_monitoring(),
    })

    # Test recording when not monitoring
    event = monitor.record_event(
        source_panel="left",
        source_offset=100.0,
        sync_mode="locked",
    )
    results.append({
        "test": "no_record_when_not_monitoring",
        "passed": event is None,
    })

    # Start monitoring
    monitor.start_monitoring()
    results.append({
        "test": "start_monitoring",
        "passed": monitor.is_monitoring(),
    })

    # Record events
    event1 = monitor.record_event(
        source_panel="left",
        source_offset=100.0,
        sync_mode="locked",
        target_panel="right",
        calculated_offset=100.0,
    )
    event2 = monitor.record_event(
        source_panel="center",
        source_offset=200.0,
        sync_mode="clause",
    )
    event3 = monitor.record_event(
        source_panel="left",
        source_offset=300.0,
        sync_mode="locked",
    )

    results.append({
        "test": "record_events",
        "passed": event1 is not None and event1.event_id == 1,
    })

    # Test event count
    results.append({
        "test": "event_count",
        "passed": monitor.get_event_count() == 3,
    })

    # Test filtering by source panel
    left_events = monitor.get_events(source_panel="left")
    results.append({
        "test": "filter_by_source",
        "passed": len(left_events) == 2,
    })

    # Test filtering by sync mode
    locked_events = monitor.get_events(sync_mode="locked")
    results.append({
        "test": "filter_by_sync_mode",
        "passed": len(locked_events) == 2,
    })

    # Test sync mode stats
    stats = monitor.get_sync_mode_stats()
    results.append({
        "test": "sync_mode_stats",
        "passed": stats.get("locked") == 2 and stats.get("clause") == 1,
    })

    # Stop monitoring
    monitor.stop_monitoring()
    results.append({
        "test": "stop_monitoring",
        "passed": not monitor.is_monitoring(),
    })

    # Test export
    exported = monitor.export_events()
    results.append({
        "test": "export_events",
        "passed": len(exported) == 3 and "event_id" in exported[0],
    })

    return results


def test_panel_position_validator():
    """Test 3: Panel position validator."""
    from integrations.layout_diagnostics import (
        PanelPositionValidator,
        PanelDimensions,
        PanelId,
    )

    results = []

    validator = PanelPositionValidator()

    # Test valid dimensions
    valid_dims = PanelDimensions(
        panel_id=PanelId.LEFT.value,
        width_percent=35.0,
        width_pixels=350,
        visible=True,
    )
    result = validator.validate_dimensions(valid_dims)
    results.append({
        "test": "valid_dimensions",
        "passed": result.valid and len(result.checks_passed) >= 2,
    })

    # Test too narrow
    narrow_dims = PanelDimensions(
        panel_id=PanelId.CENTER.value,
        width_percent=5.0,  # Below minimum
        visible=True,
    )
    result = validator.validate_dimensions(narrow_dims)
    results.append({
        "test": "too_narrow_fails",
        "passed": not result.valid and len(result.checks_failed) > 0,
    })

    # Test too wide
    wide_dims = PanelDimensions(
        panel_id=PanelId.RIGHT.value,
        width_percent=90.0,  # Above maximum
        visible=True,
    )
    result = validator.validate_dimensions(wide_dims)
    results.append({
        "test": "too_wide_fails",
        "passed": not result.valid and len(result.checks_failed) > 0,
    })

    # Test hidden panel warning
    hidden_dims = PanelDimensions(
        panel_id=PanelId.LEFT.value,
        width_percent=20.0,
        visible=False,  # Hidden but has width
    )
    result = validator.validate_dimensions(hidden_dims)
    results.append({
        "test": "hidden_panel_warning",
        "passed": len(result.warnings) > 0,
    })

    # Test full layout validation
    left = PanelDimensions(panel_id="left", width_percent=35.0, visible=True)
    center = PanelDimensions(panel_id="center", width_percent=30.0, visible=True)
    right = PanelDimensions(panel_id="right", width_percent=35.0, visible=True)

    layout_result = validator.validate_layout(left, center, right)
    results.append({
        "test": "valid_layout",
        "passed": layout_result["valid"] and layout_result["total_width_valid"],
    })

    # Test invalid total width
    left_bad = PanelDimensions(panel_id="left", width_percent=40.0, visible=True)
    center_bad = PanelDimensions(panel_id="center", width_percent=40.0, visible=True)
    right_bad = PanelDimensions(panel_id="right", width_percent=40.0, visible=True)

    layout_result = validator.validate_layout(left_bad, center_bad, right_bad)
    results.append({
        "test": "invalid_total_width",
        "passed": not layout_result["total_width_valid"],
    })

    # Test scroll offset validation
    valid_offset = validator.validate_scroll_offset(500.0)
    results.append({
        "test": "valid_scroll_offset",
        "passed": valid_offset.valid,
    })

    negative_offset = validator.validate_scroll_offset(-100.0)
    results.append({
        "test": "negative_offset_fails",
        "passed": not negative_offset.valid,
    })

    return results


def test_diagnostic_panel():
    """Test 4: Aggregate diagnostic panel."""
    from integrations.layout_diagnostics import (
        LayoutDiagnosticPanel,
        DiagnosticLevel,
        PanelId,
    )

    results = []

    panel = LayoutDiagnosticPanel()

    # Test logging
    panel.info("test", "Info message")
    panel.warn("test", "Warning message")
    panel.error("test", "Error message", {"code": 500})
    panel.debug("test", "Debug message")

    results.append({
        "test": "logging",
        "passed": len(panel.get_logs()) == 4,
    })

    # Test log filtering by level
    errors = panel.get_logs(level=DiagnosticLevel.ERROR)
    results.append({
        "test": "filter_by_level",
        "passed": len(errors) == 1 and errors[0].data.get("code") == 500,
    })

    # Test dimension capture through panel
    panel.dimension_logger.capture(PanelId.LEFT.value, 35.0)
    panel.dimension_logger.capture(PanelId.CENTER.value, 30.0)
    panel.dimension_logger.capture(PanelId.RIGHT.value, 35.0)

    results.append({
        "test": "dimension_capture",
        "passed": panel.dimension_logger.get_snapshot_count() == 3,
    })

    # Test scroll monitoring through panel
    panel.scroll_monitor.start_monitoring()
    panel.scroll_monitor.record_event("left", 100.0, "locked")
    panel.scroll_monitor.record_event("right", 200.0, "clause")

    results.append({
        "test": "scroll_monitoring",
        "passed": panel.scroll_monitor.get_event_count() == 2,
    })

    # Test report generation
    report = panel.generate_report()
    results.append({
        "test": "report_generation",
        "passed": (
            "dimensions" in report and
            "scroll_events" in report and
            "log_summary" in report
        ),
    })

    # Verify report contents
    results.append({
        "test": "report_dimensions",
        "passed": report["dimensions"]["snapshot_count"] == 3,
    })

    results.append({
        "test": "report_scroll_events",
        "passed": report["scroll_events"]["total_count"] == 2,
    })

    results.append({
        "test": "report_log_summary",
        "passed": report["log_summary"]["total_entries"] == 4,
    })

    # Test clear all
    panel.clear_all()
    results.append({
        "test": "clear_all",
        "passed": (
            len(panel.get_logs()) == 0 and
            len(panel.dimension_logger.get_history()) == 0
        ),
    })

    return results


def test_readonly_behavior():
    """Test 5: Verify read-only behavior (no workspace_mode modifications)."""
    import integrations.layout_diagnostics as diag

    results = []

    # Verify module declares itself as readonly
    results.append({
        "test": "readonly_flag",
        "passed": getattr(diag, "__readonly__", False) is True,
    })

    # Verify no imports from workspace_mode
    import inspect
    source = inspect.getsource(diag)
    results.append({
        "test": "no_workspace_mode_import",
        "passed": "from .workspace_mode" not in source and "import workspace_mode" not in source,
    })

    # Verify diagnostics can run independently
    panel = diag.LayoutDiagnosticPanel()
    panel.dimension_logger.capture("left", 33.3)
    panel.scroll_monitor.start_monitoring()
    panel.scroll_monitor.record_event("left", 0.0, "free")
    report = panel.generate_report()

    results.append({
        "test": "independent_execution",
        "passed": report is not None and report["dimensions"]["snapshot_count"] == 1,
    })

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all layout diagnostics tests."""
    all_results = []

    test_suites = [
        ("Panel Dimension Logger", test_panel_dimension_logger),
        ("Scroll Sync Monitor", test_scroll_sync_monitor),
        ("Panel Position Validator", test_panel_position_validator),
        ("Diagnostic Panel (Aggregate)", test_diagnostic_panel),
        ("Read-Only Behavior", test_readonly_behavior),
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
        "module": "layout_diagnostics",
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
    print("CC3 LAYOUT DIAGNOSTICS TEST REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
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

    # Save report
    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "tests",
        "layout_diagnostics_test_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
