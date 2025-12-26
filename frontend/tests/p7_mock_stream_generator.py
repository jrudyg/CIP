"""
P7 Mock SSE Sequence Generator
GEM P7 Validation Harness - Task P7.T1.MOCK

Generates mock SSE event sequences for testing:
- Sequence gaps and gap detection
- Out-of-order event arrival
- Stress sequences with configurable gap probability

Target Components:
- p7_stream_validator.py (SequenceValidator, EventBuffer)

CC3 P7 Validation Harness
Version: 1.0.0
"""

import sys
import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.p7_stream_validator import (
    P7EventEnvelope,
    SequenceValidator,
    EventBuffer,
    SequenceGap,
    GapStatus,
)


# ============================================================================
# MOCK EVENT GENERATOR
# ============================================================================

class MockSSESequenceGenerator:
    """
    Generates mock SSE event sequences for testing P7 stream validation.

    Capabilities:
    - Sequential event generation
    - Gap injection at specified positions
    - Out-of-order event simulation
    - Stress sequences with random gaps
    """

    def __init__(self, event_type: str = "test_event", session_id: str = "test-session"):
        self._event_type = event_type
        self._session_id = session_id
        self._event_counter = 0

    def _create_event(self, seq: int, payload: Optional[Dict] = None) -> P7EventEnvelope:
        """Create a single mock event."""
        self._event_counter += 1
        return P7EventEnvelope(
            event_id=f"evt-{self._event_counter:04d}",
            event_type=self._event_type,
            seq=seq,
            timestamp=datetime.now().isoformat(),
            payload=payload or {"seq": seq},
            session_id=self._session_id,
        )

    def generate_sequential(self, count: int, start_seq: int = 1) -> List[P7EventEnvelope]:
        """
        Generate a clean sequential event stream.

        Args:
            count: Number of events to generate
            start_seq: Starting sequence number

        Returns:
            List of events with sequential sequence numbers
        """
        return [self._create_event(seq) for seq in range(start_seq, start_seq + count)]

    def generate_with_gap(
        self,
        total_count: int,
        gap_start: int,
        gap_end: int,
        start_seq: int = 1
    ) -> Tuple[List[P7EventEnvelope], Dict[str, Any]]:
        """
        Generate events with a specific gap.

        Args:
            total_count: Total events (excluding gap)
            gap_start: First missing sequence number
            gap_end: Last missing sequence number
            start_seq: Starting sequence number

        Returns:
            Tuple of (events list, gap metadata)
        """
        events = []
        for seq in range(start_seq, start_seq + total_count + (gap_end - gap_start + 1)):
            if gap_start <= seq <= gap_end:
                continue  # Skip this sequence (create gap)
            events.append(self._create_event(seq))

        gap_meta = {
            "gap_start": gap_start,
            "gap_end": gap_end,
            "gap_size": gap_end - gap_start + 1,
            "events_generated": len(events),
        }

        return events, gap_meta

    def generate_out_of_order(
        self,
        sequence: List[int],
        shuffle_indices: Optional[List[Tuple[int, int]]] = None
    ) -> List[P7EventEnvelope]:
        """
        Generate events that arrive out of order.

        Args:
            sequence: Base sequence numbers
            shuffle_indices: Pairs of indices to swap (or None for random)

        Returns:
            Events in specified out-of-order arrangement
        """
        seq_list = list(sequence)

        if shuffle_indices:
            for i, j in shuffle_indices:
                if i < len(seq_list) and j < len(seq_list):
                    seq_list[i], seq_list[j] = seq_list[j], seq_list[i]
        else:
            # Random shuffle some pairs
            for _ in range(len(seq_list) // 4):
                i, j = random.sample(range(len(seq_list)), 2)
                seq_list[i], seq_list[j] = seq_list[j], seq_list[i]

        return [self._create_event(seq) for seq in seq_list]

    def generate_stress_sequence(
        self,
        count: int,
        gap_probability: float = 0.1,
        max_gap_size: int = 5
    ) -> Tuple[List[P7EventEnvelope], List[Dict[str, Any]]]:
        """
        Generate a stress sequence with random gaps.

        Args:
            count: Total sequence range
            gap_probability: Probability of a gap starting at any position
            max_gap_size: Maximum size of each gap

        Returns:
            Tuple of (events list, list of gap metadata)
        """
        events = []
        gaps = []
        seq = 1

        while seq <= count:
            if random.random() < gap_probability and seq < count - max_gap_size:
                # Create a gap
                gap_size = random.randint(1, max_gap_size)
                gaps.append({
                    "gap_start": seq,
                    "gap_end": seq + gap_size - 1,
                    "gap_size": gap_size,
                })
                seq += gap_size
            else:
                events.append(self._create_event(seq))
                seq += 1

        return events, gaps

    def generate_multiple_gaps(
        self,
        gap_specs: List[Tuple[int, int]]
    ) -> Tuple[List[P7EventEnvelope], List[Dict[str, Any]]]:
        """
        Generate events with multiple specific gaps.

        Args:
            gap_specs: List of (gap_start, gap_end) tuples

        Returns:
            Tuple of (events list, list of gap metadata)
        """
        # Find range
        all_positions = set()
        for start, end in gap_specs:
            for seq in range(start, end + 1):
                all_positions.add(seq)

        max_seq = max(end for _, end in gap_specs) + 5

        events = []
        gaps = []

        for seq in range(1, max_seq + 1):
            if seq not in all_positions:
                events.append(self._create_event(seq))

        for start, end in gap_specs:
            gaps.append({
                "gap_start": start,
                "gap_end": end,
                "gap_size": end - start + 1,
            })

        return events, gaps


# ============================================================================
# TEST SUITES
# ============================================================================

def test_sequential_flow() -> List[Dict[str, Any]]:
    """Test sequential event flow with no gaps."""
    results = []

    generator = MockSSESequenceGenerator()
    validator = SequenceValidator()
    buffer = EventBuffer(max_size=100)

    # Generate 5 sequential events
    events = generator.generate_sequential(5)

    # Process each event
    gaps_detected = []
    validator.on_gap_detected(lambda gap: gaps_detected.append(gap))

    for event in events:
        valid, gap = validator.validate(event.seq)
        buffer.push(event)
        results.append({
            "test": f"seq_{event.seq}_valid",
            "passed": valid == True,
            "details": f"Sequence {event.seq} validation",
        })

    # Verify no gaps
    results.append({
        "test": "no_gaps_detected",
        "passed": len(gaps_detected) == 0,
        "details": f"Expected 0 gaps, got {len(gaps_detected)}",
    })

    # Verify buffer state
    stats = buffer.get_buffer_stats()
    results.append({
        "test": "buffer_count_correct",
        "passed": stats["buffer_size"] == 5,
        "details": f"Expected 5 events in buffer, got {stats['buffer_size']}",
    })

    results.append({
        "test": "stream_state_active",
        "passed": stats["stream_state"] == "active",
        "details": f"Expected 'active' state, got {stats['stream_state']}",
    })

    results.append({
        "test": "total_processed_correct",
        "passed": stats["total_processed"] == 5,
        "details": f"Expected 5 processed, got {stats['total_processed']}",
    })

    return results


def test_gap_detection() -> List[Dict[str, Any]]:
    """Test gap detection when events are missing."""
    results = []

    generator = MockSSESequenceGenerator()
    validator = SequenceValidator()

    # Generate events 1,2,5,6 (gap at 3-4)
    events, gap_meta = generator.generate_with_gap(
        total_count=4,
        gap_start=3,
        gap_end=4
    )

    gaps_detected = []
    validator.on_gap_detected(lambda gap: gaps_detected.append(gap))

    # Process events
    for event in events:
        valid, gap = validator.validate(event.seq)

    # Verify gap was detected
    results.append({
        "test": "gap_detected",
        "passed": len(gaps_detected) == 1,
        "details": f"Expected 1 gap, detected {len(gaps_detected)}",
    })

    if gaps_detected:
        gap = gaps_detected[0]
        results.append({
            "test": "gap_start_correct",
            "passed": gap.start_seq == 3,
            "details": f"Expected gap start=3, got {gap.start_seq}",
        })

        results.append({
            "test": "gap_end_correct",
            "passed": gap.end_seq == 4,
            "details": f"Expected gap end=4, got {gap.end_seq}",
        })

        results.append({
            "test": "gap_size_correct",
            "passed": gap.gap_size == 2,
            "details": f"Expected gap size=2, got {gap.gap_size}",
        })

    return results


def test_out_of_order() -> List[Dict[str, Any]]:
    """Test out-of-order event handling."""
    results = []

    generator = MockSSESequenceGenerator()
    validator = SequenceValidator()

    # Generate events 1,3,2,4 (event 2 arrives late)
    events = generator.generate_out_of_order(
        sequence=[1, 2, 3, 4],
        shuffle_indices=[(1, 2)]  # Swap positions of 2 and 3
    )

    # Should be: 1, 3, 2, 4
    results.append({
        "test": "out_of_order_sequence",
        "passed": [e.seq for e in events] == [1, 3, 2, 4],
        "details": f"Expected [1,3,2,4], got {[e.seq for e in events]}",
    })

    gaps_detected = []
    validator.on_gap_detected(lambda gap: gaps_detected.append(gap))

    validation_results = []
    for event in events:
        valid, gap = validator.validate(event.seq)
        validation_results.append((event.seq, valid, gap))

    # Event 3 should trigger a gap (2 missing)
    results.append({
        "test": "gap_on_out_of_order",
        "passed": len(gaps_detected) >= 1,
        "details": f"Expected gap when seq 3 arrives before 2",
    })

    # Verify gaps were tracked (gap should be resolved when 2 arrives)
    metrics = validator.get_metrics()
    results.append({
        "test": "validator_processed_all",
        "passed": metrics["total_validated"] == 4,
        "details": f"Total validated: {metrics['total_validated']}",
    })

    return results


def test_large_gap() -> List[Dict[str, Any]]:
    """Test detection of large gaps."""
    results = []

    generator = MockSSESequenceGenerator()
    validator = SequenceValidator()

    # Generate events 1,2,50 (gap 3-49)
    events, gap_meta = generator.generate_with_gap(
        total_count=3,
        gap_start=3,
        gap_end=49
    )

    gaps_detected = []
    validator.on_gap_detected(lambda gap: gaps_detected.append(gap))

    for event in events:
        validator.validate(event.seq)

    results.append({
        "test": "large_gap_detected",
        "passed": len(gaps_detected) == 1,
        "details": f"Expected 1 large gap, detected {len(gaps_detected)}",
    })

    if gaps_detected:
        gap = gaps_detected[0]
        results.append({
            "test": "large_gap_size",
            "passed": gap.gap_size == 47,
            "details": f"Expected gap size=47, got {gap.gap_size}",
        })

    return results


def test_multiple_gaps() -> List[Dict[str, Any]]:
    """Test detection of multiple gaps."""
    results = []

    generator = MockSSESequenceGenerator()
    validator = SequenceValidator()

    # Generate events with gaps at 3-4, 8-9, 13-14
    gap_specs = [(3, 4), (8, 9), (13, 14)]
    events, gap_metas = generator.generate_multiple_gaps(gap_specs)

    gaps_detected = []
    validator.on_gap_detected(lambda gap: gaps_detected.append(gap))

    for event in events:
        validator.validate(event.seq)

    results.append({
        "test": "multiple_gaps_detected",
        "passed": len(gaps_detected) == 3,
        "details": f"Expected 3 gaps, detected {len(gaps_detected)}",
    })

    # Verify each gap
    expected_starts = [3, 8, 13]
    detected_starts = sorted([g.start_seq for g in gaps_detected])

    results.append({
        "test": "gap_positions_correct",
        "passed": detected_starts == expected_starts,
        "details": f"Expected starts {expected_starts}, got {detected_starts}",
    })

    # Verify metrics
    metrics = validator.get_metrics()
    results.append({
        "test": "total_gap_events_correct",
        "passed": metrics["pending_gap_events"] >= 6,
        "details": f"Expected at least 6 pending events, got {metrics['pending_gap_events']}",
    })

    return results


def test_t6_observability() -> List[Dict[str, Any]]:
    """Test T6 observability hooks."""
    results = []

    generator = MockSSESequenceGenerator()
    buffer = EventBuffer(max_size=100)

    # Generate and push some events
    events = generator.generate_sequential(10)
    for event in events:
        buffer.push(event)

    # Test full metrics
    metrics = buffer.get_full_metrics()

    results.append({
        "test": "metrics_has_buffer",
        "passed": "buffer" in metrics,
        "details": "T6 metrics should include buffer stats",
    })

    results.append({
        "test": "metrics_has_validator",
        "passed": "validator" in metrics,
        "details": "T6 metrics should include validator stats",
    })

    results.append({
        "test": "metrics_has_timestamp",
        "passed": "timestamp" in metrics,
        "details": "T6 metrics should include timestamp",
    })

    # Verify buffer metrics content
    buffer_metrics = metrics["buffer"]
    expected_keys = ["buffer_size", "total_processed", "stream_state"]
    for key in expected_keys:
        results.append({
            "test": f"buffer_metric_{key}",
            "passed": key in buffer_metrics,
            "details": f"Buffer metrics should include {key}",
        })

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests() -> Dict[str, Any]:
    """Run all mock stream generator test suites."""

    test_suites = [
        ("Sequential Flow", test_sequential_flow),
        ("Gap Detection", test_gap_detection),
        ("Out-of-Order", test_out_of_order),
        ("Large Gap", test_large_gap),
        ("Multiple Gaps", test_multiple_gaps),
        ("T6 Observability", test_t6_observability),
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
            all_results.append({
                "suite": suite_name,
                "status": "ERROR",
                "error": str(e),
                "tests": [],
            })
            total_failed += 1

    return {
        "harness": "P7.T1.MOCK - Mock SSE Sequence Generator",
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

            # Show failed tests
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

    # Exit with error code if tests failed
    if report["summary"]["total_failed"] > 0:
        sys.exit(1)
