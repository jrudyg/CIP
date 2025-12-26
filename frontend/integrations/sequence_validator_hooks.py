"""
Sequence Validator Hooks for P7 Gap Metadata Reporting

GEM Task 8 - Gap Detection, Classification, and Reporting Logic
CC3 Implementation

This module implements detection, classification, and reporting logic
for sequence gaps in the SSE stream.
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Import schema types
import sys
sys.path.insert(0, "C:/Users/jrudy/CIP/frontend")

from diagnostics.gap_metadata_schema import (
    GapMetadata,
    GapReport,
    GapSeverity,
    GapLifecycle,
    GapProvenance,
)


# --- INTERNAL STATE (Module-level singleton) ---
_active_gaps: Dict[str, GapMetadata] = {}
_resolved_gaps: List[GapMetadata] = []


def create_gap_metadata(
    start_seq: int,
    end_seq: int,
    provenance: GapProvenance = "FLOWDOWN",
    metadata: Optional[dict] = None
) -> GapMetadata:
    """
    Creates a new GapMetadata record upon detection.

    Args:
        start_seq: The last sequence number received before the gap
        end_seq: The sequence number that triggered gap detection
        provenance: Source of the gap (default: FLOWDOWN)
        metadata: Optional additional metadata

    Returns:
        GapMetadata: The created gap record
    """
    gap_id = str(uuid.uuid4())
    gap_width = end_seq - start_seq - 1  # Actual missing events

    # Severity classification based on gap width
    if gap_width >= 10:
        severity: GapSeverity = "CRITICAL"
    elif gap_width >= 3:
        severity: GapSeverity = "WARN"
    else:
        severity: GapSeverity = "INFO"

    new_gap: GapMetadata = {
        "gap_id": gap_id,
        "detection_timestamp": datetime.utcnow().isoformat() + "Z",
        "start_sequence": start_seq,
        "end_sequence": end_seq,
        "severity": severity,
        "provenance": provenance,
        "lifecycle_state": "DETECTED",
        "metadata": metadata or {},
        "resolution_sequence": None,
    }
    _active_gaps[gap_id] = new_gap
    return new_gap


def on_gap_detected(last_seq_received: int, expected_seq: int) -> GapMetadata:
    """
    Called by SequenceValidator when a sequence gap is detected.

    This is the PRIMARY HOOK for the SequenceValidator to report gaps.

    Args:
        last_seq_received: The last valid sequence number received
        expected_seq: The sequence number that was expected (next after last)

    Returns:
        GapMetadata: The created gap record
    """
    gap = create_gap_metadata(last_seq_received, expected_seq + 1)
    # Log for diagnostics
    # print(f"[GAP DETECTED] {last_seq_received} -> {expected_seq + 1}, severity={gap['severity']}")
    return gap


def update_gap_lifecycle(gap_id: str, new_state: GapLifecycle) -> bool:
    """
    Update the lifecycle state of an existing gap.

    Args:
        gap_id: The gap identifier
        new_state: The new lifecycle state

    Returns:
        bool: True if gap was found and updated
    """
    if gap_id in _active_gaps:
        _active_gaps[gap_id]["lifecycle_state"] = new_state
        return True
    return False


def resolve_gap(gap_id: str, resolution_sequence: int) -> bool:
    """
    Mark a gap as resolved and move to resolved list.

    Args:
        gap_id: The gap identifier
        resolution_sequence: The sequence at which the gap was resolved

    Returns:
        bool: True if gap was resolved successfully
    """
    if gap_id in _active_gaps:
        gap = _active_gaps.pop(gap_id)
        gap["lifecycle_state"] = "RESOLVED"
        gap["resolution_sequence"] = resolution_sequence
        _resolved_gaps.append(gap)
        return True
    return False


def terminate_gap(gap_id: str) -> bool:
    """
    Mark a gap as terminated (unrecoverable).

    Args:
        gap_id: The gap identifier

    Returns:
        bool: True if gap was terminated successfully
    """
    if gap_id in _active_gaps:
        gap = _active_gaps.pop(gap_id)
        gap["lifecycle_state"] = "TERMINATED"
        _resolved_gaps.append(gap)
        return True
    return False


def get_current_gap_report() -> GapReport:
    """
    Returns the current state of all active and recently resolved gaps.

    This is the PRIMARY INTERFACE for the diagnostics UI.

    Returns:
        GapReport: Container with open_gaps and resolved_gaps_24h
    """
    # Filter resolved gaps to last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_resolved = [
        g for g in _resolved_gaps
        if datetime.fromisoformat(g["detection_timestamp"].rstrip("Z")) > cutoff
    ]

    return {
        "open_gaps": list(_active_gaps.values()),
        "resolved_gaps_24h": recent_resolved,
    }


def get_gap_by_id(gap_id: str) -> Optional[GapMetadata]:
    """
    Retrieve a specific gap by ID.

    Args:
        gap_id: The gap identifier

    Returns:
        GapMetadata if found, None otherwise
    """
    return _active_gaps.get(gap_id)


def get_active_gap_count() -> int:
    """Get count of currently active (unresolved) gaps."""
    return len(_active_gaps)


def get_gaps_by_severity(severity: GapSeverity) -> List[GapMetadata]:
    """Get all active gaps of a specific severity."""
    return [g for g in _active_gaps.values() if g["severity"] == severity]


def clear_all_gaps() -> None:
    """
    Clear all gap records (for testing/reset purposes).
    WARNING: This removes all gap history.
    """
    global _active_gaps, _resolved_gaps
    _active_gaps = {}
    _resolved_gaps = []


def get_gap_statistics() -> Dict:
    """
    Get aggregated statistics about gaps.

    Returns:
        Dict with gap statistics for dashboard display
    """
    report = get_current_gap_report()

    active_by_severity = {"INFO": 0, "WARN": 0, "CRITICAL": 0}
    for gap in report["open_gaps"]:
        active_by_severity[gap["severity"]] += 1

    return {
        "total_active": len(report["open_gaps"]),
        "total_resolved_24h": len(report["resolved_gaps_24h"]),
        "active_by_severity": active_by_severity,
        "oldest_active_gap": (
            min(g["detection_timestamp"] for g in report["open_gaps"])
            if report["open_gaps"] else None
        ),
    }


__version__ = "1.0.0"
__phase__ = "P7.S2"
__task__ = "Task 8 - Gap Metadata Reporting"
