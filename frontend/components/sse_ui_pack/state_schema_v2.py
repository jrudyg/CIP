"""
SSE State Schema v2
P7.CC2.01 - Task 3

Extended state management with:
- Reconnection timestamps
- Sequence gap counters
- Keepalive-lag tracking placeholder

CIP Protocol: CC2 implementation for P7 state tracking.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ReconnectionRecord:
    """Record of a reconnection event."""
    attempt_number: int
    started_at: str
    completed_at: Optional[str] = None
    success: bool = False
    duration_ms: Optional[int] = None
    reason: str = "unknown"
    from_sequence: Optional[int] = None
    to_sequence: Optional[int] = None
    events_replayed: int = 0


@dataclass
class SequenceGap:
    """Record of a sequence gap."""
    gap_id: str
    detected_at: str
    expected_seq: int
    received_seq: int
    gap_size: int
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution_method: Optional[str] = None  # "replay", "skip", "manual"


@dataclass
class KeepaliveStatus:
    """Keepalive monitoring status."""
    last_keepalive_at: Optional[str] = None
    expected_interval_ms: int = 30000  # 30 seconds default
    current_lag_ms: int = 0
    missed_count: int = 0
    max_lag_observed_ms: int = 0
    is_healthy: bool = True


@dataclass
class SSEStateV2:
    """
    Extended SSE State Schema v2.

    Adds:
    - Reconnection history with timestamps
    - Sequence gap tracking
    - Keepalive lag monitoring
    """
    # Connection state
    connection_id: Optional[str] = None
    connected_at: Optional[str] = None
    disconnected_at: Optional[str] = None

    # Sequence tracking
    last_sequence: int = 0
    highest_sequence_seen: int = 0
    total_events_received: int = 0

    # Reconnection tracking
    reconnection_count: int = 0
    reconnections: List[ReconnectionRecord] = field(default_factory=list)
    last_reconnection_at: Optional[str] = None
    total_reconnection_time_ms: int = 0

    # Sequence gaps
    gaps_detected: int = 0
    gaps_resolved: int = 0
    gaps: List[SequenceGap] = field(default_factory=list)
    total_events_missed: int = 0

    # Keepalive tracking
    keepalive: KeepaliveStatus = field(default_factory=KeepaliveStatus)

    # Health metrics
    uptime_ms: int = 0
    downtime_ms: int = 0
    availability_pct: float = 100.0


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_v2_key(suffix: str) -> str:
    """Get session state key for v2 state."""
    return f"_cip_sse_v2_{suffix}"


def init_state_v2() -> None:
    """Initialize SSE State v2."""
    defaults = {
        # Connection
        "connection_id": None,
        "connected_at": None,
        "disconnected_at": None,

        # Sequences
        "last_sequence": 0,
        "highest_sequence_seen": 0,
        "total_events_received": 0,

        # Reconnections
        "reconnection_count": 0,
        "reconnections": [],
        "last_reconnection_at": None,
        "total_reconnection_time_ms": 0,
        "current_reconnection": None,

        # Gaps
        "gaps_detected": 0,
        "gaps_resolved": 0,
        "gaps": [],
        "total_events_missed": 0,

        # Keepalive
        "last_keepalive_at": None,
        "keepalive_interval_ms": 30000,
        "keepalive_lag_ms": 0,
        "keepalive_missed_count": 0,
        "keepalive_max_lag_ms": 0,

        # Health
        "session_started_at": datetime.now().isoformat(),
        "uptime_ms": 0,
        "downtime_ms": 0,
    }

    for key, default in defaults.items():
        full_key = _get_v2_key(key)
        if full_key not in st.session_state:
            st.session_state[full_key] = default


def get_state_v2() -> SSEStateV2:
    """Get current SSE State v2."""
    init_state_v2()

    # Build reconnections list
    reconnections_raw = st.session_state.get(_get_v2_key("reconnections"), [])
    reconnections = [
        ReconnectionRecord(**r) if isinstance(r, dict) else r
        for r in reconnections_raw
    ]

    # Build gaps list
    gaps_raw = st.session_state.get(_get_v2_key("gaps"), [])
    gaps = [
        SequenceGap(**g) if isinstance(g, dict) else g
        for g in gaps_raw
    ]

    # Build keepalive status
    keepalive = KeepaliveStatus(
        last_keepalive_at=st.session_state.get(_get_v2_key("last_keepalive_at")),
        expected_interval_ms=st.session_state.get(_get_v2_key("keepalive_interval_ms"), 30000),
        current_lag_ms=st.session_state.get(_get_v2_key("keepalive_lag_ms"), 0),
        missed_count=st.session_state.get(_get_v2_key("keepalive_missed_count"), 0),
        max_lag_observed_ms=st.session_state.get(_get_v2_key("keepalive_max_lag_ms"), 0),
        is_healthy=st.session_state.get(_get_v2_key("keepalive_lag_ms"), 0) < 60000,
    )

    # Calculate availability
    uptime = st.session_state.get(_get_v2_key("uptime_ms"), 0)
    downtime = st.session_state.get(_get_v2_key("downtime_ms"), 0)
    total_time = uptime + downtime
    availability = (uptime / total_time * 100) if total_time > 0 else 100.0

    return SSEStateV2(
        connection_id=st.session_state.get(_get_v2_key("connection_id")),
        connected_at=st.session_state.get(_get_v2_key("connected_at")),
        disconnected_at=st.session_state.get(_get_v2_key("disconnected_at")),
        last_sequence=st.session_state.get(_get_v2_key("last_sequence"), 0),
        highest_sequence_seen=st.session_state.get(_get_v2_key("highest_sequence_seen"), 0),
        total_events_received=st.session_state.get(_get_v2_key("total_events_received"), 0),
        reconnection_count=st.session_state.get(_get_v2_key("reconnection_count"), 0),
        reconnections=reconnections,
        last_reconnection_at=st.session_state.get(_get_v2_key("last_reconnection_at")),
        total_reconnection_time_ms=st.session_state.get(_get_v2_key("total_reconnection_time_ms"), 0),
        gaps_detected=st.session_state.get(_get_v2_key("gaps_detected"), 0),
        gaps_resolved=st.session_state.get(_get_v2_key("gaps_resolved"), 0),
        gaps=gaps,
        total_events_missed=st.session_state.get(_get_v2_key("total_events_missed"), 0),
        keepalive=keepalive,
        uptime_ms=uptime,
        downtime_ms=downtime,
        availability_pct=availability,
    )


def update_state_v2(**kwargs) -> None:
    """Update SSE State v2 fields."""
    init_state_v2()
    for key, value in kwargs.items():
        full_key = _get_v2_key(key)
        if full_key in st.session_state or key in [
            "connection_id", "connected_at", "disconnected_at",
            "last_sequence", "highest_sequence_seen", "total_events_received",
        ]:
            st.session_state[_get_v2_key(key)] = value


# ============================================================================
# RECONNECTION TRACKING
# ============================================================================

def start_reconnection(reason: str = "unknown", from_sequence: Optional[int] = None) -> int:
    """
    Start tracking a reconnection attempt.

    Args:
        reason: Reason for reconnection
        from_sequence: Last known sequence before disconnect

    Returns:
        Attempt number
    """
    init_state_v2()

    count = st.session_state.get(_get_v2_key("reconnection_count"), 0) + 1
    st.session_state[_get_v2_key("reconnection_count")] = count

    record = {
        "attempt_number": count,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "success": False,
        "duration_ms": None,
        "reason": reason,
        "from_sequence": from_sequence,
        "to_sequence": None,
        "events_replayed": 0,
    }

    st.session_state[_get_v2_key("current_reconnection")] = record
    st.session_state[_get_v2_key("disconnected_at")] = datetime.now().isoformat()

    return count


def complete_reconnection(
    success: bool,
    to_sequence: Optional[int] = None,
    events_replayed: int = 0,
) -> None:
    """
    Complete a reconnection attempt.

    Args:
        success: Whether reconnection succeeded
        to_sequence: Current sequence after reconnection
        events_replayed: Number of events replayed
    """
    init_state_v2()

    current = st.session_state.get(_get_v2_key("current_reconnection"))
    if not current:
        return

    now = datetime.now()
    current["completed_at"] = now.isoformat()
    current["success"] = success
    current["to_sequence"] = to_sequence
    current["events_replayed"] = events_replayed

    # Calculate duration
    started = datetime.fromisoformat(current["started_at"])
    duration_ms = int((now - started).total_seconds() * 1000)
    current["duration_ms"] = duration_ms

    # Add to history
    reconnections = st.session_state.get(_get_v2_key("reconnections"), [])
    reconnections.append(current)
    st.session_state[_get_v2_key("reconnections")] = reconnections[-50:]  # Keep last 50

    # Update totals
    st.session_state[_get_v2_key("total_reconnection_time_ms")] = \
        st.session_state.get(_get_v2_key("total_reconnection_time_ms"), 0) + duration_ms
    st.session_state[_get_v2_key("last_reconnection_at")] = now.isoformat()

    # Update downtime
    st.session_state[_get_v2_key("downtime_ms")] = \
        st.session_state.get(_get_v2_key("downtime_ms"), 0) + duration_ms

    # Clear current
    st.session_state[_get_v2_key("current_reconnection")] = None

    if success:
        st.session_state[_get_v2_key("connected_at")] = now.isoformat()
        st.session_state[_get_v2_key("disconnected_at")] = None


def record_reconnection(
    success: bool,
    duration_ms: int,
    reason: str = "unknown",
    from_sequence: Optional[int] = None,
    to_sequence: Optional[int] = None,
    events_replayed: int = 0,
) -> None:
    """
    Record a complete reconnection event (shorthand).

    Args:
        success: Whether reconnection succeeded
        duration_ms: Duration in milliseconds
        reason: Reason for reconnection
        from_sequence: Sequence before disconnect
        to_sequence: Sequence after reconnect
        events_replayed: Events replayed during reconnection
    """
    init_state_v2()

    count = st.session_state.get(_get_v2_key("reconnection_count"), 0) + 1
    st.session_state[_get_v2_key("reconnection_count")] = count

    now = datetime.now()
    record = {
        "attempt_number": count,
        "started_at": (now - __import__("datetime").timedelta(milliseconds=duration_ms)).isoformat(),
        "completed_at": now.isoformat(),
        "success": success,
        "duration_ms": duration_ms,
        "reason": reason,
        "from_sequence": from_sequence,
        "to_sequence": to_sequence,
        "events_replayed": events_replayed,
    }

    reconnections = st.session_state.get(_get_v2_key("reconnections"), [])
    reconnections.append(record)
    st.session_state[_get_v2_key("reconnections")] = reconnections[-50:]

    st.session_state[_get_v2_key("total_reconnection_time_ms")] = \
        st.session_state.get(_get_v2_key("total_reconnection_time_ms"), 0) + duration_ms
    st.session_state[_get_v2_key("last_reconnection_at")] = now.isoformat()


# ============================================================================
# SEQUENCE GAP TRACKING
# ============================================================================

def record_sequence_gap(
    expected_seq: int,
    received_seq: int,
) -> str:
    """
    Record a sequence gap.

    Args:
        expected_seq: Expected sequence number
        received_seq: Actually received sequence number

    Returns:
        Gap ID for resolution tracking
    """
    init_state_v2()

    gap_id = f"gap_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    gap_size = received_seq - expected_seq

    gap = {
        "gap_id": gap_id,
        "detected_at": datetime.now().isoformat(),
        "expected_seq": expected_seq,
        "received_seq": received_seq,
        "gap_size": gap_size,
        "resolved": False,
        "resolved_at": None,
        "resolution_method": None,
    }

    gaps = st.session_state.get(_get_v2_key("gaps"), [])
    gaps.append(gap)
    st.session_state[_get_v2_key("gaps")] = gaps[-100:]  # Keep last 100

    st.session_state[_get_v2_key("gaps_detected")] = \
        st.session_state.get(_get_v2_key("gaps_detected"), 0) + 1
    st.session_state[_get_v2_key("total_events_missed")] = \
        st.session_state.get(_get_v2_key("total_events_missed"), 0) + gap_size

    return gap_id


def resolve_sequence_gap(
    gap_id: str,
    resolution_method: str = "replay",
) -> bool:
    """
    Mark a sequence gap as resolved.

    Args:
        gap_id: Gap ID to resolve
        resolution_method: How gap was resolved

    Returns:
        True if gap was found and resolved
    """
    init_state_v2()

    gaps = st.session_state.get(_get_v2_key("gaps"), [])

    for gap in gaps:
        if gap.get("gap_id") == gap_id and not gap.get("resolved"):
            gap["resolved"] = True
            gap["resolved_at"] = datetime.now().isoformat()
            gap["resolution_method"] = resolution_method

            st.session_state[_get_v2_key("gaps")] = gaps
            st.session_state[_get_v2_key("gaps_resolved")] = \
                st.session_state.get(_get_v2_key("gaps_resolved"), 0) + 1

            return True

    return False


def get_unresolved_gaps() -> List[Dict[str, Any]]:
    """Get list of unresolved sequence gaps."""
    init_state_v2()
    gaps = st.session_state.get(_get_v2_key("gaps"), [])
    return [g for g in gaps if not g.get("resolved")]


# ============================================================================
# KEEPALIVE TRACKING
# ============================================================================

def record_keepalive() -> None:
    """Record receipt of a keepalive signal."""
    init_state_v2()

    now = datetime.now()
    last = st.session_state.get(_get_v2_key("last_keepalive_at"))

    if last:
        last_dt = datetime.fromisoformat(last)
        interval = st.session_state.get(_get_v2_key("keepalive_interval_ms"), 30000)
        actual_ms = int((now - last_dt).total_seconds() * 1000)
        lag_ms = max(0, actual_ms - interval)

        st.session_state[_get_v2_key("keepalive_lag_ms")] = lag_ms

        if lag_ms > st.session_state.get(_get_v2_key("keepalive_max_lag_ms"), 0):
            st.session_state[_get_v2_key("keepalive_max_lag_ms")] = lag_ms

        # Reset missed count on successful keepalive
        st.session_state[_get_v2_key("keepalive_missed_count")] = 0

    st.session_state[_get_v2_key("last_keepalive_at")] = now.isoformat()


def record_missed_keepalive() -> None:
    """Record a missed keepalive."""
    init_state_v2()
    st.session_state[_get_v2_key("keepalive_missed_count")] = \
        st.session_state.get(_get_v2_key("keepalive_missed_count"), 0) + 1


def get_keepalive_lag() -> int:
    """
    Get current keepalive lag in milliseconds.

    Returns:
        Lag in milliseconds (0 if healthy)
    """
    init_state_v2()

    last = st.session_state.get(_get_v2_key("last_keepalive_at"))
    if not last:
        return 0

    now = datetime.now()
    last_dt = datetime.fromisoformat(last)
    interval = st.session_state.get(_get_v2_key("keepalive_interval_ms"), 30000)
    elapsed_ms = int((now - last_dt).total_seconds() * 1000)

    return max(0, elapsed_ms - interval)


def set_keepalive_interval(interval_ms: int) -> None:
    """Set expected keepalive interval."""
    init_state_v2()
    st.session_state[_get_v2_key("keepalive_interval_ms")] = interval_ms


# ============================================================================
# HEALTH METRICS
# ============================================================================

def record_uptime(duration_ms: int) -> None:
    """Record uptime duration."""
    init_state_v2()
    st.session_state[_get_v2_key("uptime_ms")] = \
        st.session_state.get(_get_v2_key("uptime_ms"), 0) + duration_ms


def get_health_summary() -> Dict[str, Any]:
    """
    Get health summary for monitoring.

    Returns:
        Dictionary with health metrics
    """
    state = get_state_v2()

    # Calculate health score (0-100)
    health_score = 100

    # Deduct for gaps
    if state.gaps_detected > 0:
        unresolved = state.gaps_detected - state.gaps_resolved
        health_score -= min(30, unresolved * 5)

    # Deduct for reconnections
    if state.reconnection_count > 0:
        health_score -= min(20, state.reconnection_count * 2)

    # Deduct for keepalive issues
    if state.keepalive.missed_count > 0:
        health_score -= min(20, state.keepalive.missed_count * 5)

    # Deduct for low availability
    if state.availability_pct < 99:
        health_score -= int((99 - state.availability_pct) * 2)

    health_score = max(0, health_score)

    return {
        "health_score": health_score,
        "availability_pct": state.availability_pct,
        "total_events": state.total_events_received,
        "reconnection_count": state.reconnection_count,
        "gaps_detected": state.gaps_detected,
        "gaps_unresolved": state.gaps_detected - state.gaps_resolved,
        "keepalive_lag_ms": state.keepalive.current_lag_ms,
        "keepalive_healthy": state.keepalive.is_healthy,
        "status": "healthy" if health_score >= 80 else (
            "degraded" if health_score >= 50 else "unhealthy"
        ),
    }


# ============================================================================
# CC3 INTEGRATION
# ============================================================================

def get_state_v2_for_binder() -> Dict[str, Any]:
    """
    Get State v2 for CC3 binder.

    Returns:
        Dictionary with state v2 data
    """
    state = get_state_v2()
    health = get_health_summary()

    return {
        "connection_id": state.connection_id,
        "connected": state.connected_at is not None and state.disconnected_at is None,
        "last_sequence": state.last_sequence,
        "total_events": state.total_events_received,
        "reconnection_count": state.reconnection_count,
        "last_reconnection_at": state.last_reconnection_at,
        "gaps_detected": state.gaps_detected,
        "gaps_resolved": state.gaps_resolved,
        "events_missed": state.total_events_missed,
        "keepalive_lag_ms": state.keepalive.current_lag_ms,
        "keepalive_healthy": state.keepalive.is_healthy,
        "availability_pct": state.availability_pct,
        "health": health,
    }
