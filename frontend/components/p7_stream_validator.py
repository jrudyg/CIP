"""
P7 Stream Validator - Sequence Validator & Event Buffer Implementation
GEM P7.S1 Execution Directive - CC3 Task 1

Core logic for:
- Sequence Validator with gap detection
- Event Buffer with out-of-order event storage
- Introspection hooks per P7 EventBuffer Observability Contract (T6)

CC3 P7.S1.T1 - Stream Validator
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Deque
from collections import deque
from enum import Enum
from datetime import datetime
import threading
import time


# ============================================================================
# STREAM STATE ENUMS
# ============================================================================

class StreamState(str, Enum):
    """P7 Connection States per GEM contract."""
    ACTIVE = "active"           # Healthy streaming
    STALE = "stale"             # No events received within threshold
    RECONNECTING = "reconnecting"  # Attempting to reconnect
    TERMINATED = "terminated"   # Connection closed


class GapStatus(str, Enum):
    """Status of sequence gap handling."""
    NONE = "none"               # No gap detected
    DETECTED = "detected"       # Gap detected, awaiting replay
    REPLAYING = "replaying"     # Replay in progress
    RESOLVED = "resolved"       # Gap filled


# ============================================================================
# EVENT ENVELOPE (P7 CONTRACT)
# ============================================================================

@dataclass
class P7EventEnvelope:
    """
    P7 Event Envelope per streaming contract.
    All SSE events must conform to this structure.
    """
    event_id: str
    event_type: str
    seq: int                    # Sequence number for ordering
    timestamp: str
    payload: Dict[str, Any]
    session_id: Optional[str] = None

    # Processing metadata
    received_at: str = ""
    processed: bool = False

    def __post_init__(self):
        if not self.received_at:
            self.received_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "seq": self.seq,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "session_id": self.session_id,
            "received_at": self.received_at,
            "processed": self.processed,
        }


# ============================================================================
# SEQUENCE GAP
# ============================================================================

@dataclass
class SequenceGap:
    """Represents a detected sequence gap."""
    start_seq: int              # First missing sequence
    end_seq: int                # Last missing sequence (inclusive)
    detected_at: str = ""
    status: GapStatus = GapStatus.DETECTED
    replay_requested_at: Optional[str] = None
    resolved_at: Optional[str] = None

    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()

    @property
    def gap_size(self) -> int:
        """Number of missing events."""
        return self.end_seq - self.start_seq + 1

    def mark_replaying(self) -> None:
        """Mark gap as being replayed."""
        self.status = GapStatus.REPLAYING
        self.replay_requested_at = datetime.now().isoformat()

    def mark_resolved(self) -> None:
        """Mark gap as resolved."""
        self.status = GapStatus.RESOLVED
        self.resolved_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_seq": self.start_seq,
            "end_seq": self.end_seq,
            "gap_size": self.gap_size,
            "detected_at": self.detected_at,
            "status": self.status.value,
            "replay_requested_at": self.replay_requested_at,
            "resolved_at": self.resolved_at,
        }


# ============================================================================
# SEQUENCE VALIDATOR
# ============================================================================

class SequenceValidator:
    """
    Validates event sequence numbers and detects gaps.

    Gap Detection Logic (per GEM spec):
    - Gap detected when: event.seq > last_processed_seq + 1
    - Tracks all gaps for replay requests
    - Supports gap resolution tracking
    """

    def __init__(self):
        self._last_processed_seq: int = -1
        self._highest_seen_seq: int = -1
        self._gaps: List[SequenceGap] = []
        self._gap_callbacks: List[Callable[[SequenceGap], None]] = []
        self._lock = threading.Lock()

        # Metrics
        self._total_validated: int = 0
        self._total_gaps_detected: int = 0
        self._total_gaps_resolved: int = 0

    def validate(self, seq: int) -> Tuple[bool, Optional[SequenceGap]]:
        """
        Validate incoming sequence number.

        Args:
            seq: The sequence number to validate

        Returns:
            Tuple of (is_valid, gap_if_detected)
            - is_valid: True if sequence is in order
            - gap_if_detected: SequenceGap if gap detected, None otherwise
        """
        with self._lock:
            self._total_validated += 1
            self._highest_seen_seq = max(self._highest_seen_seq, seq)

            # First event
            if self._last_processed_seq == -1:
                self._last_processed_seq = seq
                return (True, None)

            expected = self._last_processed_seq + 1

            # In order
            if seq == expected:
                self._last_processed_seq = seq
                return (True, None)

            # Gap detected: event.seq > last_processed_seq + 1
            if seq > expected:
                gap = SequenceGap(
                    start_seq=expected,
                    end_seq=seq - 1,
                )
                self._gaps.append(gap)
                self._total_gaps_detected += 1
                self._last_processed_seq = seq

                # Notify callbacks
                for cb in self._gap_callbacks:
                    try:
                        cb(gap)
                    except Exception:
                        pass

                return (False, gap)

            # Out of order (seq < expected) - might be filling a gap
            # Check if it fills a known gap
            for gap in self._gaps:
                if gap.status != GapStatus.RESOLVED:
                    if gap.start_seq <= seq <= gap.end_seq:
                        # This event fills part of a gap
                        # For simplicity, mark resolved if we get any gap event
                        # A full implementation would track all missing seqs
                        return (True, None)

            # Duplicate or old event
            return (True, None)

    def resolve_gap(self, gap: SequenceGap) -> None:
        """Mark a gap as resolved."""
        with self._lock:
            gap.mark_resolved()
            self._total_gaps_resolved += 1

    def on_gap_detected(self, callback: Callable[[SequenceGap], None]) -> None:
        """Register callback for gap detection."""
        self._gap_callbacks.append(callback)

    def get_active_gaps(self) -> List[SequenceGap]:
        """Get unresolved gaps."""
        with self._lock:
            return [g for g in self._gaps if g.status != GapStatus.RESOLVED]

    def get_all_gaps(self) -> List[SequenceGap]:
        """Get all gaps (including resolved)."""
        with self._lock:
            return self._gaps.copy()

    @property
    def last_processed_seq(self) -> int:
        """Get last processed sequence number."""
        return self._last_processed_seq

    @property
    def highest_seen_seq(self) -> int:
        """Get highest seen sequence number."""
        return self._highest_seen_seq

    def reset(self) -> None:
        """Reset validator state."""
        with self._lock:
            self._last_processed_seq = -1
            self._highest_seen_seq = -1
            self._gaps.clear()

    # ========================================================================
    # INTROSPECTION HOOKS (P7 EventBuffer Observability Contract T6)
    # ========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get validator metrics for observability."""
        with self._lock:
            active_gaps = [g for g in self._gaps if g.status != GapStatus.RESOLVED]
            return {
                "last_processed_seq": self._last_processed_seq,
                "highest_seen_seq": self._highest_seen_seq,
                "total_validated": self._total_validated,
                "total_gaps_detected": self._total_gaps_detected,
                "total_gaps_resolved": self._total_gaps_resolved,
                "active_gap_count": len(active_gaps),
                "pending_gap_events": sum(g.gap_size for g in active_gaps),
            }


# ============================================================================
# EVENT BUFFER
# ============================================================================

class EventBuffer:
    """
    Event buffer for P7 streaming events.

    Features:
    - Stores events in arrival order
    - Supports out-of-order event storage for gap filling
    - Bounded size with configurable max
    - Introspection hooks per T6 contract
    """

    def __init__(
        self,
        max_size: int = 1000,
        stale_threshold_ms: int = 5000,
    ):
        self._buffer: Deque[P7EventEnvelope] = deque(maxlen=max_size)
        self._out_of_order: Dict[int, P7EventEnvelope] = {}  # seq -> event
        self._max_size = max_size
        self._stale_threshold_ms = stale_threshold_ms

        self._sequence_validator = SequenceValidator()
        self._state = StreamState.TERMINATED
        self._last_event_time: Optional[datetime] = None

        # Callbacks
        self._event_callbacks: Dict[str, List[Callable[[P7EventEnvelope], None]]] = {}
        self._state_callbacks: List[Callable[[StreamState], None]] = []

        # Metrics
        self._total_received: int = 0
        self._total_processed: int = 0
        self._total_dropped: int = 0

        self._lock = threading.Lock()

    def push(self, event: P7EventEnvelope) -> Tuple[bool, Optional[SequenceGap]]:
        """
        Push event to buffer.

        Args:
            event: The event envelope to buffer

        Returns:
            Tuple of (accepted, gap_if_detected)
        """
        with self._lock:
            self._total_received += 1
            self._last_event_time = datetime.now()

            # Update state if needed
            if self._state != StreamState.ACTIVE:
                self._set_state(StreamState.ACTIVE)

            # Validate sequence
            is_valid, gap = self._sequence_validator.validate(event.seq)

            # Add to buffer
            self._buffer.append(event)

            # Track if out of order
            if not is_valid and gap:
                self._out_of_order[event.seq] = event

            # Dispatch to handlers
            self._dispatch_event(event)

            self._total_processed += 1
            event.processed = True

            return (True, gap)

    def _dispatch_event(self, event: P7EventEnvelope) -> None:
        """Dispatch event to registered handlers."""
        # Type-specific handlers
        handlers = self._event_callbacks.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass

        # Wildcard handlers
        for handler in self._event_callbacks.get("*", []):
            try:
                handler(event)
            except Exception:
                pass

    def on_event(self, event_type: str, handler: Callable[[P7EventEnvelope], None]) -> None:
        """
        Register handler for event type.
        Use "*" for all events.
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(handler)

    def on_state_change(self, callback: Callable[[StreamState], None]) -> None:
        """Register callback for state changes."""
        self._state_callbacks.append(callback)

    def _set_state(self, state: StreamState) -> None:
        """Update stream state and notify callbacks."""
        if self._state != state:
            self._state = state
            for cb in self._state_callbacks:
                try:
                    cb(state)
                except Exception:
                    pass

    def check_staleness(self) -> bool:
        """
        Check if stream is stale based on last event time.

        Returns:
            True if stale (no events within threshold)
        """
        if self._last_event_time is None:
            return True

        delta_ms = (datetime.now() - self._last_event_time).total_seconds() * 1000
        is_stale = delta_ms > self._stale_threshold_ms

        if is_stale and self._state == StreamState.ACTIVE:
            self._set_state(StreamState.STALE)

        return is_stale

    def get_recent(self, count: int = 10) -> List[P7EventEnvelope]:
        """Get most recent events."""
        with self._lock:
            return list(self._buffer)[-count:]

    def get_by_type(self, event_type: str) -> List[P7EventEnvelope]:
        """Get events of specific type."""
        with self._lock:
            return [e for e in self._buffer if e.event_type == event_type]

    def get_by_seq_range(self, start: int, end: int) -> List[P7EventEnvelope]:
        """Get events within sequence range."""
        with self._lock:
            return [e for e in self._buffer if start <= e.seq <= end]

    def clear(self) -> None:
        """Clear buffer."""
        with self._lock:
            self._buffer.clear()
            self._out_of_order.clear()
            self._sequence_validator.reset()

    @property
    def state(self) -> StreamState:
        """Get current stream state."""
        return self._state

    @property
    def size(self) -> int:
        """Get current buffer size."""
        return len(self._buffer)

    def get_sequence_validator(self) -> SequenceValidator:
        """Get the sequence validator instance."""
        return self._sequence_validator

    # ========================================================================
    # INTROSPECTION HOOKS (P7 EventBuffer Observability Contract T6)
    # ========================================================================

    def get_buffer_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics for observability.
        Implements T6 introspection hooks.
        """
        with self._lock:
            return {
                "buffer_size": len(self._buffer),
                "max_size": self._max_size,
                "buffer_utilization": len(self._buffer) / self._max_size if self._max_size > 0 else 0,
                "out_of_order_count": len(self._out_of_order),
                "total_received": self._total_received,
                "total_processed": self._total_processed,
                "total_dropped": self._total_dropped,
                "stream_state": self._state.value,
                "last_event_time": self._last_event_time.isoformat() if self._last_event_time else None,
                "stale_threshold_ms": self._stale_threshold_ms,
            }

    def get_full_metrics(self) -> Dict[str, Any]:
        """
        Get complete metrics combining buffer and validator stats.
        Primary introspection endpoint per T6.
        """
        buffer_stats = self.get_buffer_stats()
        validator_metrics = self._sequence_validator.get_metrics()

        return {
            "buffer": buffer_stats,
            "validator": validator_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    def get_gap_report(self) -> Dict[str, Any]:
        """Get detailed gap report for diagnostics."""
        gaps = self._sequence_validator.get_all_gaps()
        active_gaps = [g for g in gaps if g.status != GapStatus.RESOLVED]

        return {
            "total_gaps": len(gaps),
            "active_gaps": len(active_gaps),
            "resolved_gaps": len(gaps) - len(active_gaps),
            "total_missing_events": sum(g.gap_size for g in active_gaps),
            "gaps": [g.to_dict() for g in gaps[-20:]],  # Last 20 gaps
        }


# ============================================================================
# STREAM HEALTH MONITOR
# ============================================================================

class StreamHealthMonitor:
    """
    Monitors stream health and provides keepalive tracking.
    Implements metrics required by P7 Visual Diagnostics Panel Spec (T3).
    """

    def __init__(self, buffer: EventBuffer, keepalive_interval_ms: int = 30000):
        self._buffer = buffer
        self._keepalive_interval_ms = keepalive_interval_ms
        self._last_keepalive: Optional[datetime] = None
        self._keepalive_count: int = 0
        self._missed_keepalives: int = 0

    def record_keepalive(self) -> None:
        """Record receipt of keepalive event."""
        self._last_keepalive = datetime.now()
        self._keepalive_count += 1

    def check_keepalive(self) -> bool:
        """
        Check if keepalive is overdue.

        Returns:
            True if keepalive is overdue
        """
        if self._last_keepalive is None:
            return False

        delta_ms = (datetime.now() - self._last_keepalive).total_seconds() * 1000
        is_overdue = delta_ms > self._keepalive_interval_ms * 1.5  # 50% grace

        if is_overdue:
            self._missed_keepalives += 1

        return is_overdue

    def get_keepalive_delta_ms(self) -> Optional[float]:
        """
        Get time since last keepalive in milliseconds.
        Required by T3 Visual Diagnostics spec.
        """
        if self._last_keepalive is None:
            return None
        return (datetime.now() - self._last_keepalive).total_seconds() * 1000

    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get health metrics for T3 Visual Diagnostics Panel.
        """
        buffer_metrics = self._buffer.get_full_metrics()

        return {
            "stream_state": self._buffer.state.value,
            "last_sequence_id": buffer_metrics["validator"]["last_processed_seq"],
            "keepalive_delta_ms": self.get_keepalive_delta_ms(),
            "keepalive_count": self._keepalive_count,
            "missed_keepalives": self._missed_keepalives,
            "buffer_size": buffer_metrics["buffer"]["buffer_size"],
            "active_gaps": buffer_metrics["validator"]["active_gap_count"],
            "total_events_processed": buffer_metrics["buffer"]["total_processed"],
            "is_healthy": (
                self._buffer.state == StreamState.ACTIVE and
                buffer_metrics["validator"]["active_gap_count"] == 0
            ),
        }


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "1.0.0"
__phase__ = "Phase 7 - P7.S1"
__contract__ = "P7 EventBuffer Observability Contract (T6)"
