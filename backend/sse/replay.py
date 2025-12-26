"""
SSE Replay Controller for P7 Streaming Backend.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

Defines:
- EventBuffer for storing recent events
- ReplayController for client reconnection replay
- REPLAY_START and REPLAY_END event generators

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import AsyncGenerator, Deque, Dict, Iterator, List, Optional

from .envelope import EventEnvelope, EventType

# Diagnostic logging hook
logger = logging.getLogger("sse.replay")


@dataclass
class BufferConfig:
    """Configuration for EventBuffer."""

    max_events: int = 1000
    max_age_seconds: int = 300  # 5 minutes
    enable_persistence: bool = False
    persistence_path: Optional[str] = None


@dataclass
class ReplayRequest:
    """Request for event replay."""

    session_id: str
    from_sequence: int
    to_sequence: Optional[int] = None
    max_events: Optional[int] = None
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReplayResult:
    """Result of replay operation."""

    success: bool
    events_replayed: int
    from_sequence: int
    to_sequence: int
    gaps: List[tuple]  # List of (start, end) sequence gaps
    duration_ms: float
    truncated: bool = False


class EventBuffer:
    """
    Circular buffer for storing recent SSE events.

    Features:
    - Thread-safe operations
    - Automatic eviction based on size and age
    - Sequence-based retrieval
    - Gap detection for missing sequences

    Used by ReplayController to serve reconnecting clients.
    """

    def __init__(self, config: Optional[BufferConfig] = None) -> None:
        """
        Initialize event buffer.

        Args:
            config: Buffer configuration
        """
        self._config = config or BufferConfig()
        self._buffer: Deque[EventEnvelope] = deque(maxlen=self._config.max_events)
        self._sequence_index: Dict[int, int] = {}  # sequence -> buffer position
        self._lock = threading.RLock()
        self._min_sequence: int = 0
        self._max_sequence: int = 0

        logger.info(
            f"EventBuffer initialized: max_events={self._config.max_events}, "
            f"max_age={self._config.max_age_seconds}s"
        )

    def append(self, event: EventEnvelope) -> None:
        """
        Append event to buffer.

        Args:
            event: Event envelope to append
        """
        with self._lock:
            # Check for age-based eviction before append
            self._evict_old_events()

            # Append to buffer
            self._buffer.append(event)

            # Update sequence tracking
            if self._min_sequence == 0 or event.sequence < self._min_sequence:
                self._min_sequence = event.sequence
            if event.sequence > self._max_sequence:
                self._max_sequence = event.sequence

            # Update index (position may shift due to deque rotation)
            self._rebuild_index()

        logger.debug(f"Event buffered: seq={event.sequence}, type={event.event_type.value}")

    def get_events_from_sequence(
        self,
        from_sequence: int,
        max_events: Optional[int] = None
    ) -> List[EventEnvelope]:
        """
        Get events starting from a sequence number.

        Args:
            from_sequence: Starting sequence number (inclusive)
            max_events: Maximum events to return

        Returns:
            List of events from the specified sequence
        """
        with self._lock:
            events = [
                e for e in self._buffer
                if e.sequence >= from_sequence
            ]

            # Sort by sequence
            events.sort(key=lambda e: e.sequence)

            # Apply limit
            if max_events is not None and len(events) > max_events:
                events = events[:max_events]

        logger.debug(
            f"Retrieved {len(events)} events from sequence {from_sequence}"
        )
        return events

    def get_events_in_range(
        self,
        from_sequence: int,
        to_sequence: int
    ) -> List[EventEnvelope]:
        """
        Get events in a sequence range.

        Args:
            from_sequence: Start sequence (inclusive)
            to_sequence: End sequence (inclusive)

        Returns:
            List of events in range
        """
        with self._lock:
            events = [
                e for e in self._buffer
                if from_sequence <= e.sequence <= to_sequence
            ]

            events.sort(key=lambda e: e.sequence)

        return events

    def detect_gaps(
        self,
        from_sequence: int,
        to_sequence: int
    ) -> List[tuple]:
        """
        Detect sequence gaps in a range.

        Args:
            from_sequence: Start of range
            to_sequence: End of range

        Returns:
            List of (gap_start, gap_end) tuples
        """
        with self._lock:
            present_sequences = {
                e.sequence for e in self._buffer
                if from_sequence <= e.sequence <= to_sequence
            }

        gaps = []
        gap_start = None

        for seq in range(from_sequence, to_sequence + 1):
            if seq not in present_sequences:
                if gap_start is None:
                    gap_start = seq
            else:
                if gap_start is not None:
                    gaps.append((gap_start, seq - 1))
                    gap_start = None

        # Handle trailing gap
        if gap_start is not None:
            gaps.append((gap_start, to_sequence))

        return gaps

    def get_sequence_range(self) -> tuple:
        """
        Get the current sequence range in buffer.

        Returns:
            Tuple of (min_sequence, max_sequence)
        """
        with self._lock:
            return (self._min_sequence, self._max_sequence)

    def size(self) -> int:
        """
        Get current buffer size.

        Returns:
            Number of events in buffer
        """
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        """Clear all events from buffer."""
        with self._lock:
            self._buffer.clear()
            self._sequence_index.clear()
            self._min_sequence = 0
            self._max_sequence = 0

        logger.info("EventBuffer cleared")

    def _evict_old_events(self) -> None:
        """Evict events older than max_age_seconds."""
        if self._config.max_age_seconds <= 0:
            return

        cutoff = datetime.now() - timedelta(seconds=self._config.max_age_seconds)
        cutoff_iso = cutoff.isoformat()

        # Remove old events from front of deque
        while self._buffer and self._buffer[0].timestamp < cutoff_iso:
            evicted = self._buffer.popleft()
            logger.debug(f"Evicted old event: seq={evicted.sequence}")

        # Update min sequence
        if self._buffer:
            self._min_sequence = min(e.sequence for e in self._buffer)
        else:
            self._min_sequence = 0
            self._max_sequence = 0

    def _rebuild_index(self) -> None:
        """Rebuild the sequence index."""
        self._sequence_index = {
            e.sequence: i for i, e in enumerate(self._buffer)
        }


class ReplayController:
    """
    Controller for SSE event replay on client reconnection.

    Features:
    - REPLAY_START and REPLAY_END event generation
    - Gap detection and reporting
    - Configurable replay limits
    - Async generator for streaming replay
    """

    def __init__(
        self,
        event_buffer: EventBuffer,
        max_replay_events: int = 500,
        replay_batch_size: int = 50
    ) -> None:
        """
        Initialize replay controller.

        Args:
            event_buffer: EventBuffer to replay from
            max_replay_events: Maximum events to replay
            replay_batch_size: Events per batch for streaming
        """
        self._buffer = event_buffer
        self._max_replay_events = max_replay_events
        self._replay_batch_size = replay_batch_size
        self._active_replays: Dict[str, ReplayRequest] = {}
        self._lock = threading.Lock()

        logger.info(
            f"ReplayController initialized: "
            f"max_events={max_replay_events}, batch_size={replay_batch_size}"
        )

    def create_replay_start_event(
        self,
        event_id: str,
        sequence: int,
        from_sequence: int,
        event_count: int,
        session_id: Optional[str] = None
    ) -> EventEnvelope:
        """
        Create REPLAY_START event envelope.

        Args:
            event_id: Unique event identifier
            sequence: Current sequence number
            from_sequence: Starting replay sequence
            event_count: Number of events to replay
            session_id: Optional session identifier

        Returns:
            REPLAY_START event envelope
        """
        return EventEnvelope.create_replay_start(
            event_id=event_id,
            sequence=sequence,
            from_sequence=from_sequence,
            event_count=event_count,
            session_id=session_id
        )

    def create_replay_end_event(
        self,
        event_id: str,
        sequence: int,
        events_replayed: int,
        session_id: Optional[str] = None
    ) -> EventEnvelope:
        """
        Create REPLAY_END event envelope.

        Args:
            event_id: Unique event identifier
            sequence: Current sequence number
            events_replayed: Number of events replayed
            session_id: Optional session identifier

        Returns:
            REPLAY_END event envelope
        """
        return EventEnvelope.create_replay_end(
            event_id=event_id,
            sequence=sequence,
            events_replayed=events_replayed,
            session_id=session_id
        )

    def replay_events(
        self,
        request: ReplayRequest
    ) -> Iterator[EventEnvelope]:
        """
        Synchronous generator for replaying events.

        Args:
            request: Replay request parameters

        Yields:
            Event envelopes in sequence order
        """
        start_time = datetime.now()

        # Register active replay
        with self._lock:
            self._active_replays[request.session_id] = request

        try:
            # Determine replay range
            to_sequence = request.to_sequence
            if to_sequence is None:
                _, max_seq = self._buffer.get_sequence_range()
                to_sequence = max_seq

            # Get events to replay
            events = self._buffer.get_events_from_sequence(
                from_sequence=request.from_sequence,
                max_events=request.max_events or self._max_replay_events
            )

            # Filter to requested range
            events = [e for e in events if e.sequence <= to_sequence]

            logger.info(
                f"Replaying {len(events)} events for session {request.session_id} "
                f"from seq {request.from_sequence}"
            )

            # Yield events
            for event in events:
                # Wrap in REPLAY_EVENT type for client distinction
                replay_event = EventEnvelope(
                    event_id=f"replay_{event.event_id}",
                    sequence=event.sequence,
                    event_type=EventType.REPLAY_EVENT,
                    timestamp=event.timestamp,
                    payload={
                        "original_type": event.event_type.value,
                        "original_payload": event.payload
                    },
                    metadata={
                        "replay": True,
                        "original_metadata": event.metadata
                    },
                    session_id=request.session_id
                )
                yield replay_event

        finally:
            # Cleanup active replay
            with self._lock:
                self._active_replays.pop(request.session_id, None)

            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Replay complete for session {request.session_id}: "
                f"{len(events)} events in {duration:.2f}ms"
            )

    async def replay_events_async(
        self,
        request: ReplayRequest
    ) -> AsyncGenerator[EventEnvelope, None]:
        """
        Async generator for replaying events.

        Args:
            request: Replay request parameters

        Yields:
            Event envelopes in sequence order
        """
        # Use sync implementation wrapped for async
        for event in self.replay_events(request):
            yield event

    def get_replay_result(
        self,
        request: ReplayRequest,
        events_replayed: int,
        duration_ms: float
    ) -> ReplayResult:
        """
        Generate replay result summary.

        Args:
            request: Original replay request
            events_replayed: Number of events replayed
            duration_ms: Duration in milliseconds

        Returns:
            ReplayResult with summary information
        """
        to_sequence = request.to_sequence
        if to_sequence is None:
            _, max_seq = self._buffer.get_sequence_range()
            to_sequence = max_seq

        gaps = self._buffer.detect_gaps(request.from_sequence, to_sequence)
        truncated = (
            request.max_events is not None and
            events_replayed >= request.max_events
        )

        return ReplayResult(
            success=True,
            events_replayed=events_replayed,
            from_sequence=request.from_sequence,
            to_sequence=to_sequence,
            gaps=gaps,
            duration_ms=duration_ms,
            truncated=truncated
        )

    def get_active_replays(self) -> Dict[str, ReplayRequest]:
        """
        Get currently active replay operations.

        Returns:
            Dict mapping session_id to ReplayRequest
        """
        with self._lock:
            return dict(self._active_replays)

    def cancel_replay(self, session_id: str) -> bool:
        """
        Cancel an active replay.

        Args:
            session_id: Session to cancel replay for

        Returns:
            True if replay was cancelled, False if not found
        """
        with self._lock:
            if session_id in self._active_replays:
                del self._active_replays[session_id]
                logger.info(f"Replay cancelled for session {session_id}")
                return True
            return False


# Factory function
def create_replay_controller(
    buffer_config: Optional[BufferConfig] = None,
    max_replay_events: int = 500
) -> tuple:
    """
    Factory function to create EventBuffer and ReplayController.

    Args:
        buffer_config: Configuration for EventBuffer
        max_replay_events: Maximum events to replay

    Returns:
        Tuple of (EventBuffer, ReplayController)
    """
    buffer = EventBuffer(buffer_config)
    controller = ReplayController(buffer, max_replay_events=max_replay_events)

    return buffer, controller
