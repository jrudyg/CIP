"""
SSE Event Envelope for P7 Streaming Backend.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

Defines:
- EventType enum for all SSE event categories
- EventEnvelope dataclass for structured event data
- Serialization methods including .to_sse_frame()

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

# Diagnostic logging hook
logger = logging.getLogger("sse.envelope")


class EventType(Enum):
    """
    SSE Event Type enumeration.

    Categories:
    - Connection lifecycle events
    - Data events
    - Control events
    - Error events
    """

    # Connection lifecycle
    HANDSHAKE_START = "handshake_start"
    HANDSHAKE_COMPLETE = "handshake_complete"
    KEEPALIVE = "keepalive"
    CONNECTION_CLOSE = "connection_close"

    # Replay events
    REPLAY_START = "replay_start"
    REPLAY_END = "replay_end"
    REPLAY_EVENT = "replay_event"

    # Data events
    DATA = "data"
    UPDATE = "update"
    INSERT = "insert"
    DELETE = "delete"

    # Intelligence pipeline events
    ENGINE_START = "engine_start"
    ENGINE_COMPLETE = "engine_complete"
    ENGINE_ERROR = "engine_error"
    STAGE_ACTIVATION = "stage_activation"
    FLAG_CHANGE = "flag_change"

    # Control events
    PAUSE = "pause"
    RESUME = "resume"
    BACKPRESSURE = "backpressure"

    # Error events
    ERROR = "error"
    WARNING = "warning"

    def is_lifecycle(self) -> bool:
        """Check if event is a lifecycle event."""
        return self in {
            EventType.HANDSHAKE_START,
            EventType.HANDSHAKE_COMPLETE,
            EventType.KEEPALIVE,
            EventType.CONNECTION_CLOSE
        }

    def is_replay(self) -> bool:
        """Check if event is a replay event."""
        return self in {
            EventType.REPLAY_START,
            EventType.REPLAY_END,
            EventType.REPLAY_EVENT
        }

    def is_data(self) -> bool:
        """Check if event is a data event."""
        return self in {
            EventType.DATA,
            EventType.UPDATE,
            EventType.INSERT,
            EventType.DELETE
        }

    def is_error(self) -> bool:
        """Check if event is an error event."""
        return self in {
            EventType.ERROR,
            EventType.WARNING,
            EventType.ENGINE_ERROR
        }


@dataclass
class EventEnvelope:
    """
    Structured envelope for SSE events.

    Provides consistent structure for all SSE events with:
    - Unique event ID
    - Sequence number for ordering
    - Typed event classification
    - Timestamp for ordering and debugging
    - Payload for event data
    - Metadata for context
    """

    event_id: str
    sequence: int
    event_type: EventType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    retry_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert envelope to dictionary.

        Returns:
            Dictionary representation of the envelope
        """
        result = {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata
        }

        if self.session_id:
            result["session_id"] = self.session_id

        return result

    def to_json(self) -> str:
        """
        Serialize envelope to JSON string.

        Returns:
            JSON string representation
        """
        try:
            return json.dumps(self.to_dict(), separators=(",", ":"))
        except (TypeError, ValueError) as e:
            logger.error(f"Envelope serialization failed: {e}")
            # Fallback to safe serialization
            return json.dumps({
                "event_id": self.event_id,
                "sequence": self.sequence,
                "event_type": self.event_type.value,
                "timestamp": self.timestamp,
                "error": "serialization_failed"
            })

    def to_sse_frame(self) -> str:
        """
        Format envelope as SSE frame.

        SSE Frame Format:
            id: <event_id>
            event: <event_type>
            retry: <retry_ms>  (optional)
            data: <json_payload>

            (blank line to end frame)

        Returns:
            Properly formatted SSE frame string
        """
        lines = []

        # Event ID for client-side tracking
        lines.append(f"id: {self.event_id}")

        # Event type for client-side routing
        lines.append(f"event: {self.event_type.value}")

        # Retry interval (optional)
        if self.retry_ms is not None:
            lines.append(f"retry: {self.retry_ms}")

        # Data payload (JSON)
        data_json = self.to_json()
        lines.append(f"data: {data_json}")

        # SSE requires blank line to terminate frame
        lines.append("")
        lines.append("")

        frame = "\n".join(lines)

        # Diagnostic logging
        logger.debug(
            f"SSE frame created: id={self.event_id}, "
            f"type={self.event_type.value}, "
            f"seq={self.sequence}"
        )

        return frame

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        """
        Create EventEnvelope from dictionary.

        Args:
            data: Dictionary containing envelope fields

        Returns:
            EventEnvelope instance
        """
        return cls(
            event_id=data["event_id"],
            sequence=data["sequence"],
            event_type=EventType(data["event_type"]),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            session_id=data.get("session_id"),
            retry_ms=data.get("retry_ms")
        )

    @classmethod
    def create_handshake_complete(
        cls,
        event_id: str,
        sequence: int,
        session_id: str,
        server_version: str,
        capabilities: Dict[str, Any]
    ) -> "EventEnvelope":
        """
        Factory method for HANDSHAKE_COMPLETE event.

        Args:
            event_id: Unique event identifier
            sequence: Sequence number
            session_id: Session identifier
            server_version: Server version string
            capabilities: Server capabilities dictionary

        Returns:
            EventEnvelope for handshake completion
        """
        return cls(
            event_id=event_id,
            sequence=sequence,
            event_type=EventType.HANDSHAKE_COMPLETE,
            session_id=session_id,
            payload={
                "server_version": server_version,
                "capabilities": capabilities
            },
            metadata={
                "handshake": True
            }
        )

    @classmethod
    def create_keepalive(
        cls,
        event_id: str,
        sequence: int,
        session_id: Optional[str] = None
    ) -> "EventEnvelope":
        """
        Factory method for KEEPALIVE event.

        Args:
            event_id: Unique event identifier
            sequence: Sequence number
            session_id: Optional session identifier

        Returns:
            EventEnvelope for keepalive
        """
        return cls(
            event_id=event_id,
            sequence=sequence,
            event_type=EventType.KEEPALIVE,
            session_id=session_id,
            payload={
                "ping": True
            }
        )

    @classmethod
    def create_error(
        cls,
        event_id: str,
        sequence: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> "EventEnvelope":
        """
        Factory method for ERROR event.

        Args:
            event_id: Unique event identifier
            sequence: Sequence number
            error_code: Machine-readable error code
            message: Human-readable error message
            details: Optional error details
            session_id: Optional session identifier

        Returns:
            EventEnvelope for error
        """
        return cls(
            event_id=event_id,
            sequence=sequence,
            event_type=EventType.ERROR,
            session_id=session_id,
            payload={
                "error_code": error_code,
                "message": message,
                "details": details or {}
            }
        )

    @classmethod
    def create_replay_start(
        cls,
        event_id: str,
        sequence: int,
        from_sequence: int,
        event_count: int,
        session_id: Optional[str] = None
    ) -> "EventEnvelope":
        """
        Factory method for REPLAY_START event.

        Args:
            event_id: Unique event identifier
            sequence: Sequence number
            from_sequence: Starting sequence for replay
            event_count: Number of events to replay
            session_id: Optional session identifier

        Returns:
            EventEnvelope for replay start
        """
        return cls(
            event_id=event_id,
            sequence=sequence,
            event_type=EventType.REPLAY_START,
            session_id=session_id,
            payload={
                "from_sequence": from_sequence,
                "event_count": event_count
            },
            metadata={
                "replay": True
            }
        )

    @classmethod
    def create_replay_end(
        cls,
        event_id: str,
        sequence: int,
        events_replayed: int,
        session_id: Optional[str] = None
    ) -> "EventEnvelope":
        """
        Factory method for REPLAY_END event.

        Args:
            event_id: Unique event identifier
            sequence: Sequence number
            events_replayed: Number of events replayed
            session_id: Optional session identifier

        Returns:
            EventEnvelope for replay end
        """
        return cls(
            event_id=event_id,
            sequence=sequence,
            event_type=EventType.REPLAY_END,
            session_id=session_id,
            payload={
                "events_replayed": events_replayed
            },
            metadata={
                "replay": True
            }
        )
