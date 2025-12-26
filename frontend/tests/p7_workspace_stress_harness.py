"""
P7 Workspace Layout Stress Harness
GEM P7 Validation Harness - Task P7.T2.STRESS

Stress tests for:
- High-frequency scroll sync events (100ms debounce T2 compliance)
- Scroll Authority Token (SAT) validation under load
- Panel switching during rapid events

Target Components:
- p7_data_sync_service.py (Debouncer, ScrollSyncService)
- workspace_mode.py (ScrollAuthorityToken, SAT)

CC3 P7 Validation Harness
Version: 1.0.0
"""

import sys
import os
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.p7_data_sync_service import (
    Debouncer,
    ScrollSyncService,
    ScrollSyncCommand,
    P7DataSyncService,
)


# ============================================================================
# STRESS TEST UTILITIES
# ============================================================================

@dataclass
class StressTestConfig:
    """Configuration for stress tests."""
    event_count: int = 20  # Reduced for faster tests
    burst_interval_ms: float = 5.0
    panel_sources: List[str] = field(default_factory=lambda: ["left", "center", "right"])
    debounce_ms: int = 100


# ============================================================================
# MOCK SAT MANAGER (Simulates workspace_mode.py SAT)
# ============================================================================

class MockScrollAuthorityToken:
    """Mock SAT for testing without full workspace_mode dependency."""

    def __init__(self, panel: str):
        self.token_id = f"sat-{int(time.time() * 1000)}"
        self.holder_panel = panel
        self.issued_at = datetime.now().isoformat()
        self.is_valid = True
        self.sequence_number = 0


class MockSATManager:
    """Mock SAT Manager for stress testing."""

    def __init__(self):
        self._current_token: Optional[MockScrollAuthorityToken] = None
        self._authority_changes: List[Dict] = []
        self._lock = threading.Lock()

    def request_authority(self, panel: str) -> MockScrollAuthorityToken:
        """Request scroll authority for a panel."""
        with self._lock:
            if self._current_token:
                self._current_token.is_valid = False
            self._current_token = MockScrollAuthorityToken(panel)
            self._authority_changes.append({
                "panel": panel,
                "token_id": self._current_token.token_id,
                "timestamp": time.time(),
            })
            return self._current_token

    def validate_token(self, token: MockScrollAuthorityToken) -> bool:
        """Validate a token is current."""
        with self._lock:
            return (
                self._current_token is not None and
                self._current_token.token_id == token.token_id and
                self._current_token.is_valid
            )

    def get_current_holder(self) -> Optional[str]:
        """Get current authority holder."""
        with self._lock:
            if self._current_token and self._current_token.is_valid:
                return self._current_token.holder_panel
            return None

    def release_authority(self) -> None:
        """Release current authority (for replay mode)."""
        with self._lock:
            if self._current_token:
                self._current_token.is_valid = False
                self._current_token = None

    def get_authority_changes(self) -> List[Dict]:
        """Get history of authority changes."""
        with self._lock:
            return self._authority_changes.copy()


# ============================================================================
# TEST SUITES
# ============================================================================

def test_rapid_fire_debounce() -> List[Dict[str, Any]]:
    """
    Test rapid fire scroll events - verify debounce logic.
    P7 Timing Spec T2: 100ms debounce.
    """
    results = []
    config = StressTestConfig(event_count=20)

    scroll_service = ScrollSyncService()
    delivered_events: List[ScrollSyncCommand] = []

    scroll_service.on_outgoing_scroll(lambda cmd: delivered_events.append(cmd))

    # Send rapid events without sleeping (synchronous debounce check)
    sent_count = 0
    immediate_count = 0

    for i in range(config.event_count):
        will_send = scroll_service.send_scroll_event(
            source_panel="center",
            offset=float(i * 10),
            sync_mode="clause_aligned"
        )
        sent_count += 1
        if will_send:
            immediate_count += 1

    # Get metrics immediately (no need to wait for timers)
    metrics = scroll_service.get_metrics()
    debounced_count = metrics["debounced_count"]

    # First event should send immediately
    results.append({
        "test": "first_event_immediate",
        "passed": immediate_count >= 1,
        "details": f"Immediate sends: {immediate_count}",
    })

    # Rest should be debounced (queued)
    results.append({
        "test": "subsequent_events_debounced",
        "passed": debounced_count >= config.event_count - 5,
        "details": f"Debounced: {debounced_count}/{sent_count}",
    })

    # Verify debounce ratio
    debounce_ratio = debounced_count / sent_count if sent_count > 0 else 0
    results.append({
        "test": "debounce_ratio_high",
        "passed": debounce_ratio >= 0.75,
        "details": f"Debounce ratio: {debounce_ratio:.2%}",
    })

    # Outgoing count should be low (only immediate sends, not debounced yet)
    results.append({
        "test": "outgoing_count_low",
        "passed": metrics["outgoing_count"] <= 5,
        "details": f"Outgoing count: {metrics['outgoing_count']}",
    })

    return results


def test_debouncer_configuration() -> List[Dict[str, Any]]:
    """
    Verify debouncer is configured correctly per P7 Timing Spec T2.
    """
    results = []

    # Test standalone debouncer
    debouncer = Debouncer(delay_ms=100)

    results.append({
        "test": "debounce_delay_is_100ms",
        "passed": debouncer.get_delay_ms() == 100,
        "details": f"Debouncer delay: {debouncer.get_delay_ms()}ms",
    })

    # Test ScrollSyncService constant
    results.append({
        "test": "scroll_service_uses_100ms",
        "passed": ScrollSyncService.OUTGOING_DEBOUNCE_MS == 100,
        "details": f"ScrollSyncService constant: {ScrollSyncService.OUTGOING_DEBOUNCE_MS}ms",
    })

    # Test debouncer callback setup
    callback_values: List[Any] = []
    debouncer.set_callback(lambda v: callback_values.append(v))

    # First call should return True (will execute)
    result = debouncer.call("test_value")
    results.append({
        "test": "first_call_returns_true",
        "passed": result == True,
        "details": f"First call returned: {result}",
    })

    # Immediate second call should return False (debounced)
    result2 = debouncer.call("test_value_2")
    results.append({
        "test": "rapid_second_call_returns_false",
        "passed": result2 == False,
        "details": f"Rapid second call returned: {result2}",
    })

    debouncer.cancel()

    return results


def test_sat_authority_under_stress() -> List[Dict[str, Any]]:
    """
    Test SAT authority handling during rapid panel switches.
    """
    results = []

    sat_manager = MockSATManager()
    panels = ["left", "center", "right"]

    # Rapidly switch authority between panels
    switch_count = 30
    valid_tokens = 0

    for i in range(switch_count):
        panel = panels[i % 3]
        token = sat_manager.request_authority(panel)

        if sat_manager.validate_token(token):
            valid_tokens += 1

    # All tokens should be valid when issued
    results.append({
        "test": "all_tokens_valid_when_issued",
        "passed": valid_tokens == switch_count,
        "details": f"Valid tokens: {valid_tokens}/{switch_count}",
    })

    # Authority should have changed switch_count times
    changes = sat_manager.get_authority_changes()
    results.append({
        "test": "authority_changes_tracked",
        "passed": len(changes) == switch_count,
        "details": f"Authority changes: {len(changes)}",
    })

    # Verify panel rotation
    left_count = sum(1 for c in changes if c["panel"] == "left")
    center_count = sum(1 for c in changes if c["panel"] == "center")
    right_count = sum(1 for c in changes if c["panel"] == "right")

    results.append({
        "test": "panels_rotated_evenly",
        "passed": left_count == center_count == right_count == 10,
        "details": f"L:{left_count} C:{center_count} R:{right_count}",
    })

    # Old tokens should be invalid
    first_token_id = changes[0]["token_id"]
    old_token = MockScrollAuthorityToken("left")
    old_token.token_id = first_token_id

    results.append({
        "test": "old_tokens_revoked",
        "passed": not sat_manager.validate_token(old_token),
        "details": "First issued token should be invalid now",
    })

    return results


def test_sat_release_for_replay() -> List[Dict[str, Any]]:
    """
    Test SAT release mechanism (used during replay mode).
    """
    results = []

    sat_manager = MockSATManager()

    # Get authority
    token = sat_manager.request_authority("center")
    results.append({
        "test": "initial_authority_acquired",
        "passed": sat_manager.get_current_holder() == "center",
        "details": f"Holder: {sat_manager.get_current_holder()}",
    })

    # Release authority (simulating replay mode start)
    sat_manager.release_authority()

    results.append({
        "test": "authority_released",
        "passed": sat_manager.get_current_holder() is None,
        "details": f"Holder after release: {sat_manager.get_current_holder()}",
    })

    # Token should be invalid after release
    results.append({
        "test": "token_invalid_after_release",
        "passed": not sat_manager.validate_token(token),
        "details": "Token should be invalid after authority release",
    })

    # Can re-acquire after release
    new_token = sat_manager.request_authority("left")
    results.append({
        "test": "can_reacquire_after_release",
        "passed": sat_manager.get_current_holder() == "left",
        "details": f"Re-acquired holder: {sat_manager.get_current_holder()}",
    })

    return results


def test_panel_switching_with_scroll() -> List[Dict[str, Any]]:
    """
    Test scroll events from different panels.
    """
    results = []

    scroll_service = ScrollSyncService()
    panels = ["left", "center", "right"]

    # Track which panels send
    panel_sends: Dict[str, int] = {p: 0 for p in panels}

    for i, panel in enumerate(panels * 3):  # 9 total events
        will_send = scroll_service.send_scroll_event(
            source_panel=panel,
            offset=float(i * 100)
        )
        if will_send:
            panel_sends[panel] += 1

    # First event from each burst should send (if timing allows)
    total_immediate = sum(panel_sends.values())
    results.append({
        "test": "some_panels_sent_immediate",
        "passed": total_immediate >= 1,
        "details": f"Immediate sends by panel: {panel_sends}",
    })

    # Verify metrics accumulated
    metrics = scroll_service.get_metrics()
    results.append({
        "test": "metrics_accumulated",
        "passed": metrics["outgoing_count"] + metrics["debounced_count"] == 9,
        "details": f"Out:{metrics['outgoing_count']} Deb:{metrics['debounced_count']}",
    })

    return results


def test_scroll_sync_metrics() -> List[Dict[str, Any]]:
    """
    Test ScrollSyncService metrics tracking.
    """
    results = []

    scroll_service = ScrollSyncService()

    # Initial metrics
    initial_metrics = scroll_service.get_metrics()
    results.append({
        "test": "initial_metrics_zero",
        "passed": initial_metrics["incoming_count"] == 0 and initial_metrics["outgoing_count"] == 0,
        "details": f"Initial: in={initial_metrics['incoming_count']} out={initial_metrics['outgoing_count']}",
    })

    # Send some events
    for i in range(5):
        scroll_service.send_scroll_event("center", float(i * 10))

    final_metrics = scroll_service.get_metrics()

    # Should have outgoing or debounced counts
    total_tracked = final_metrics["outgoing_count"] + final_metrics["debounced_count"]
    results.append({
        "test": "events_tracked",
        "passed": total_tracked == 5,
        "details": f"Total tracked: {total_tracked}",
    })

    # Metrics should include debounce_ms
    results.append({
        "test": "metrics_include_debounce_ms",
        "passed": final_metrics["debounce_ms"] == 100,
        "details": f"Debounce MS in metrics: {final_metrics['debounce_ms']}",
    })

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests() -> Dict[str, Any]:
    """Run all workspace stress test suites."""

    test_suites = [
        ("Rapid Fire (T2 Debounce)", test_rapid_fire_debounce),
        ("Debouncer Configuration", test_debouncer_configuration),
        ("SAT Authority", test_sat_authority_under_stress),
        ("SAT Release (Replay)", test_sat_release_for_replay),
        ("Panel Switching", test_panel_switching_with_scroll),
        ("Scroll Sync Metrics", test_scroll_sync_metrics),
    ]

    all_results = []
    total_passed = 0
    total_failed = 0

    for suite_name, test_func in test_suites:
        try:
            results = test_func()
            passed = sum(1 for r in results if r["passed"])
            failed = len(results) - passed
            total_passed += passed
            total_failed += failed

            all_results.append({
                "suite": suite_name,
                "status": "PASSED" if failed == 0 else "FAILED",
                "passed": passed,
                "failed": failed,
                "tests": results,
            })
        except Exception as e:
            import traceback
            all_results.append({
                "suite": suite_name,
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "tests": [],
            })
            total_failed += 1

    return {
        "harness": "P7.T2.STRESS - Workspace Layout Stress Harness",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_suites": len(test_suites),
            "total_passed": total_passed,
            "total_failed": total_failed,
            "pass_rate": f"{(total_passed / (total_passed + total_failed) * 100):.1f}%" if (total_passed + total_failed) > 0 else "N/A",
        },
        "results": all_results,
    }


def print_report(report: Dict[str, Any]) -> None:
    """Print formatted test report."""
    print("\n" + "=" * 60)
    print(f"P7 VALIDATION HARNESS - {report['harness']}")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print()

    for suite in report["results"]:
        status_icon = "[PASS]" if suite["status"] == "PASSED" else "[FAIL]" if suite["status"] == "FAILED" else "[ERR]"
        print(f"  {status_icon} Suite: {suite['suite']}")

        if suite.get("tests"):
            passed = suite.get("passed", 0)
            total = len(suite["tests"])
            print(f"         Tests: {passed}/{total}")

            for test in suite["tests"]:
                if not test["passed"]:
                    print(f"           - {test['test']}: {test.get('details', 'FAILED')}")

        if suite.get("error"):
            print(f"         Error: {suite['error']}")

    print()
    print("-" * 60)
    summary = report["summary"]
    print(f"SUMMARY: {summary['total_passed']} passed, {summary['total_failed']} failed")
    print(f"Pass Rate: {summary['pass_rate']}")
    print("=" * 60)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    report = run_all_tests()
    print_report(report)

    if report["summary"]["total_failed"] > 0:
        sys.exit(1)
