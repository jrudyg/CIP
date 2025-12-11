"""
Session State Models for P7 Streaming Backend.

Phase: P7.S2
Author: CC1 (Backend Mechanic)
Directive: S2.T1_SESSION_STATE_MODELS

Defines:
- SessionStatus enum for lifecycle states
- SessionMetadata for connection metadata
- SessionConfig for session configuration
- SessionState as the primary state container

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Diagnostic logging hook
logger = logging.getLogger("session_state.models")


class SessionStatus(Enum):
    """
    Session lifecycle status.

    Maps to P7ConnectionState from the shared contract for FE/BE alignment.
    """

    PENDING = "pending"
    """Session created but not yet connected."""

    ACTIVE = "active"
    """Session is connected and streaming events."""

    STALE = "stale"
    """Session has not received keepalive within threshold."""

    RECONNECTING = "reconnecting"
    """Client is attempting to reconnect."""

    PAUSED = "paused"
    """Session is temporarily paused (backpressure)."""

    CLOSED = "closed"
    """Session has been gracefully closed."""

    TERMINATED = "terminated"
    """Session was forcefully terminated."""

    ERROR = "error"
    """Session is in error state."""


@dataclass
class SessionConfig:
    """
    Configuration for a session.

    Defines operational parameters for the session lifecycle.
    """

    keepalive_interval_ms: int = 30000
    """Keepalive interval in milliseconds (default: 30s)."""

    stale_threshold_ms: int = 45000
    """Stale detection threshold in milliseconds (default: 45s)."""

    max_replay_events: int = 1000
    """Maximum events to buffer for replay."""

    max_reconnect_attempts: int = 5
    """Maximum reconnection attempts before termination."""

    backpressure_threshold: int = 100
    """Queue size threshold for backpressure."""

    client_version: Optional[str] = None
    """Client version for compatibility checking."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "keepalive_interval_ms": self.keepalive_interval_ms,
            "stale_threshold_ms": self.stale_threshold_ms,
            "max_replay_events": self.max_replay_events,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "backpressure_threshold": self.backpressure_threshold,
            "client_version": self.client_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionConfig":
        """Create from dictionary representation."""
        return cls(
            keepalive_interval_ms=data.get("keepalive_interval_ms", 30000),
            stale_threshold_ms=data.get("stale_threshold_ms", 45000),
            max_replay_events=data.get("max_replay_events", 1000),
            max_reconnect_attempts=data.get("max_reconnect_attempts", 5),
            backpressure_threshold=data.get("backpressure_threshold", 100),
            client_version=data.get("client_version"),
        )


@dataclass
class SessionMetadata:
    """
    Metadata for a session.

    Contains diagnostic and tracking information.
    """

    client_ip: Optional[str] = None
    """Client IP address."""

    user_agent: Optional[str] = None
    """Client user agent string."""

    user_id: Optional[str] = None
    """Authenticated user identifier."""

    contract_id: Optional[str] = None
    """Associated contract identifier (CIP context)."""

    workspace_id: Optional[str] = None
    """Associated workspace identifier."""

    tags: Dict[str, str] = field(default_factory=dict)
    """Custom tags for categorization."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "user_id": self.user_id,
            "contract_id": self.contract_id,
            "workspace_id": self.workspace_id,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMetadata":
        """Create from dictionary representation."""
        return cls(
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            user_id=data.get("user_id"),
            contract_id=data.get("contract_id"),
            workspace_id=data.get("workspace_id"),
            tags=data.get("tags", {}),
        )


@dataclass
class SessionState:
    """
    Primary session state container.

    Represents the complete state of an SSE session, including:
    - Identity and lifecycle status
    - Sequence tracking for replay
    - Connection metrics
    - Configuration and metadata
    """

    session_id: str
    """Unique session identifier."""

    status: SessionStatus = SessionStatus.PENDING
    """Current session status."""

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    """Session creation timestamp (ISO 8601)."""

    connected_at: Optional[str] = None
    """Connection establishment timestamp."""

    last_event_at: Optional[str] = None
    """Last event timestamp."""

    last_keepalive_at: Optional[str] = None
    """Last keepalive timestamp."""

    closed_at: Optional[str] = None
    """Session closure timestamp."""

    # Sequence tracking
    last_sequence: int = 0
    """Last sequence number sent."""

    last_acked_sequence: int = 0
    """Last sequence acknowledged by client."""

    replay_from_sequence: Optional[int] = None
    """Sequence to replay from on reconnection."""

    # Metrics
    events_sent: int = 0
    """Total events sent."""

    events_dropped: int = 0
    """Events dropped due to backpressure."""

    bytes_sent: int = 0
    """Total bytes sent."""

    keepalives_sent: int = 0
    """Keepalive events sent."""

    replays_performed: int = 0
    """Number of replay operations."""

    reconnect_count: int = 0
    """Number of reconnections."""

    # State transitions
    state_history: List[str] = field(default_factory=list)
    """History of state transitions."""

    # Configuration and metadata
    config: SessionConfig = field(default_factory=SessionConfig)
    """Session configuration."""

    metadata: SessionMetadata = field(default_factory=SessionMetadata)
    """Session metadata."""

    # Error tracking
    last_error: Optional[str] = None
    """Last error message."""

    error_count: int = 0
    """Total error count."""

    def transition_to(self, new_status: SessionStatus) -> None:
        """
        Transition to a new status.

        Args:
            new_status: Target status
        """
        old_status = self.status
        self.status = new_status

        transition = f"{old_status.value}->{new_status.value}@{datetime.now().isoformat()}"
        self.state_history.append(transition)

        logger.debug(f"Session {self.session_id}: {transition}")

        # Update timestamps based on status
        if new_status == SessionStatus.ACTIVE:
            self.connected_at = datetime.now().isoformat()
        elif new_status in {SessionStatus.CLOSED, SessionStatus.TERMINATED}:
            self.closed_at = datetime.now().isoformat()

    def record_event(self, sequence: int, bytes_size: int = 0) -> None:
        """
        Record an event being sent.

        Args:
            sequence: Event sequence number
            bytes_size: Size of event in bytes
        """
        self.last_sequence = sequence
        self.last_event_at = datetime.now().isoformat()
        self.events_sent += 1
        self.bytes_sent += bytes_size

    def record_keepalive(self) -> None:
        """Record a keepalive event."""
        self.last_keepalive_at = datetime.now().isoformat()
        self.keepalives_sent += 1

    def record_replay(self) -> None:
        """Record a replay operation."""
        self.replays_performed += 1

    def record_reconnect(self, from_sequence: int) -> None:
        """
        Record a reconnection.

        Args:
            from_sequence: Sequence to replay from
        """
        self.reconnect_count += 1
        self.replay_from_sequence = from_sequence
        self.transition_to(SessionStatus.RECONNECTING)

    def record_error(self, error_message: str) -> None:
        """
        Record an error.

        Args:
            error_message: Error description
        """
        self.last_error = error_message
        self.error_count += 1
        logger.warning(f"Session {self.session_id} error: {error_message}")

    def is_active(self) -> bool:
        """Check if session is in an active state."""
        return self.status in {
            SessionStatus.ACTIVE,
            SessionStatus.RECONNECTING,
            SessionStatus.PAUSED,
        }

    def is_terminal(self) -> bool:
        """Check if session is in a terminal state."""
        return self.status in {
            SessionStatus.CLOSED,
            SessionStatus.TERMINATED,
            SessionStatus.ERROR,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "connected_at": self.connected_at,
            "last_event_at": self.last_event_at,
            "last_keepalive_at": self.last_keepalive_at,
            "closed_at": self.closed_at,
            "last_sequence": self.last_sequence,
            "last_acked_sequence": self.last_acked_sequence,
            "replay_from_sequence": self.replay_from_sequence,
            "events_sent": self.events_sent,
            "events_dropped": self.events_dropped,
            "bytes_sent": self.bytes_sent,
            "keepalives_sent": self.keepalives_sent,
            "replays_performed": self.replays_performed,
            "reconnect_count": self.reconnect_count,
            "state_history": self.state_history,
            "config": self.config.to_dict(),
            "metadata": self.metadata.to_dict(),
            "last_error": self.last_error,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Create from dictionary representation."""
        state = cls(
            session_id=data["session_id"],
            status=SessionStatus(data.get("status", "pending")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            connected_at=data.get("connected_at"),
            last_event_at=data.get("last_event_at"),
            last_keepalive_at=data.get("last_keepalive_at"),
            closed_at=data.get("closed_at"),
            last_sequence=data.get("last_sequence", 0),
            last_acked_sequence=data.get("last_acked_sequence", 0),
            replay_from_sequence=data.get("replay_from_sequence"),
            events_sent=data.get("events_sent", 0),
            events_dropped=data.get("events_dropped", 0),
            bytes_sent=data.get("bytes_sent", 0),
            keepalives_sent=data.get("keepalives_sent", 0),
            replays_performed=data.get("replays_performed", 0),
            reconnect_count=data.get("reconnect_count", 0),
            state_history=data.get("state_history", []),
            last_error=data.get("last_error"),
            error_count=data.get("error_count", 0),
        )

        if "config" in data:
            state.config = SessionConfig.from_dict(data["config"])
        if "metadata" in data:
            state.metadata = SessionMetadata.from_dict(data["metadata"])

        return state

    def get_observability_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for P7 observability hooks.

        Returns metrics required by P7ObservabilityHooks.REQUIRED_METRICS.
        """
        return {
            "last_sequence_id": self.last_sequence,
            "buffer_size": 0,  # Populated by handler
            "gap_count": 0,  # Populated by validator
            "events_processed": self.events_sent,
            "events_dropped": self.events_dropped,
            "replay_count": self.replays_performed,
            "keepalive_delta_ms": 0,  # Calculated by client
            "connection_state": self.status.value,
            "last_event_timestamp": self.last_event_at,
        }
