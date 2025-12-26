"""
P7 Streaming Contract - Joint Frontend/Backend Agreement.

Phase: P7
Version: 1.0.0 (Stable)
Author: CC1 (Backend Mechanic), validated by CAI + GEM

This contract defines the shared interfaces, event types, and timing
specifications that both frontend (CC2/CC3) and backend (CC1) must adhere to
for the P7 Streaming Architecture.

STATUS: STABLE - Production ready
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# =============================================================================
# P7 CONNECTION STATES
# Shared between frontend ConnectionIndicator and backend SSEHandler
# =============================================================================


class P7ConnectionState(Enum):
    """
    P7 Connection States per GEM Degraded-Mode UX Playbook (T1).

    These states are shared between:
    - Backend: SSEHandler lifecycle
    - Frontend: ConnectionIndicator UI component
    """

    ACTIVE = "active"
    """Connection is healthy, events flowing normally."""

    STALE = "stale"
    """No events received within keepalive threshold. UI shows warning."""

    RECONNECTING = "reconnecting"
    """Connection lost, attempting to reconnect. Replay may be needed."""

    TERMINATED = "terminated"
    """Connection permanently closed. Manual action required."""


# =============================================================================
# P7 EVENT TYPES
# Shared event type definitions for FE/BE consistency
# =============================================================================


class P7EventType(Enum):
    """
    P7 Streaming Event Types.

    Shared between backend envelope.py and frontend stream_validator.py.
    """

    # Lifecycle events
    HANDSHAKE_COMPLETE = "handshake_complete"
    KEEPALIVE = "keepalive"
    CONNECTION_CLOSE = "connection_close"

    # Replay events
    REPLAY_START = "replay_start"
    REPLAY_END = "replay_end"
    REPLAY_EVENT = "replay_event"

    # Data sync events (P7 specific)
    SCROLL_SYNC = "scroll_sync"
    HIGHLIGHT = "highlight"
    SELECTION_CHANGE = "selection_change"

    # Intelligence pipeline events
    ENGINE_UPDATE = "engine_update"
    STAGE_CHANGE = "stage_change"

    # Error events
    ERROR = "error"
    WARNING = "warning"


# =============================================================================
# P7 TIMING SPECIFICATION (T2)
# Shared timing constants
# =============================================================================


@dataclass(frozen=True)
class P7TimingSpec:
    """
    P7 Timing Specification per GEM T2 contract.

    All timing values in milliseconds unless otherwise noted.
    """

    # Keepalive interval (server-side)
    KEEPALIVE_INTERVAL_MS: int = 30000  # 30 seconds

    # Stale threshold (client-side)
    STALE_THRESHOLD_MS: int = 45000  # 45 seconds (1.5x keepalive)

    # Reconnection timing
    RECONNECT_INITIAL_DELAY_MS: int = 1000  # 1 second
    RECONNECT_MAX_DELAY_MS: int = 30000  # 30 seconds
    RECONNECT_BACKOFF_MULTIPLIER: float = 1.5

    # Debounce timing
    SCROLL_DEBOUNCE_MS: int = 100  # Client-side scroll event debounce
    HIGHLIGHT_DEBOUNCE_MS: int = 50  # Highlight event debounce

    # Replay timing
    REPLAY_BATCH_SIZE: int = 50  # Events per replay batch
    REPLAY_BATCH_DELAY_MS: int = 10  # Delay between batches


# Singleton instance
P7_TIMING = P7TimingSpec()


# =============================================================================
# P7 EVENT ENVELOPE SCHEMA
# Shared envelope structure
# =============================================================================


@dataclass
class P7EventEnvelopeSchema:
    """
    Schema for P7 event envelopes.

    This defines the required fields that both FE and BE must support.
    """

    event_id: str
    """Unique event identifier (UUID format recommended)."""

    sequence: int
    """Monotonically increasing sequence number for ordering and gap detection."""

    event_type: str
    """Event type from P7EventType enum."""

    timestamp: str
    """ISO 8601 timestamp of event creation."""

    payload: Dict[str, Any]
    """Event-specific data payload."""

    session_id: Optional[str] = None
    """Session identifier for connection correlation."""

    metadata: Optional[Dict[str, Any]] = None
    """Optional metadata for diagnostics."""


# =============================================================================
# P7 GAP DETECTION CONTRACT
# Sequence validation rules for CC3 stream_validator.py
# =============================================================================


@dataclass
class P7GapDetectionRules:
    """
    Rules for sequence gap detection per GEM EventBuffer Observability (T6).

    CC3 must implement these rules in p7_stream_validator.py.
    """

    # Gap detection trigger
    GAP_THRESHOLD: int = 1
    """Gap detected when: event.seq > last_processed_seq + GAP_THRESHOLD"""

    # Buffer limits
    MAX_BUFFER_SIZE: int = 1000
    """Maximum events to buffer while awaiting replay."""

    MAX_GAP_SIZE: int = 100
    """Maximum gap size before requesting full resync."""

    # Replay request timing
    REPLAY_REQUEST_DELAY_MS: int = 500
    """Delay before requesting replay (allows natural reordering)."""


P7_GAP_RULES = P7GapDetectionRules()


# =============================================================================
# P7 SCROLL SYNC CONTRACT
# Scroll synchronization event structure
# =============================================================================


@dataclass
class P7ScrollSyncEvent:
    """
    Scroll sync event structure per GEM P7 contract.

    Used by:
    - Backend: Broadcast scroll position changes
    - Frontend: Route to P6.C3.T1 Scroll Engine
    """

    scroll_position: float
    """Scroll position as percentage (0.0 - 1.0)."""

    viewport_start: int
    """First visible line/element index."""

    viewport_end: int
    """Last visible line/element index."""

    source_client_id: str
    """Client that originated the scroll (for echo suppression)."""

    document_id: Optional[str] = None
    """Document being scrolled (for multi-doc scenarios)."""


# =============================================================================
# P7 HIGHLIGHT CONTRACT
# Highlight event structure
# =============================================================================


@dataclass
class P7HighlightEvent:
    """
    Highlight event structure per GEM P7 contract.

    Used by:
    - Backend: Broadcast highlight changes
    - Frontend: Route to Contract Viewer DOM
    """

    highlight_id: str
    """Unique identifier for this highlight."""

    start_offset: int
    """Character offset where highlight starts."""

    end_offset: int
    """Character offset where highlight ends."""

    highlight_type: str
    """Type of highlight (selection, search, annotation)."""

    color_token: Optional[str] = None
    """High-contrast color token from P6.C2.T1."""

    metadata: Optional[Dict[str, Any]] = None
    """Additional highlight metadata."""


# =============================================================================
# P7 OBSERVABILITY HOOKS
# Required introspection points per GEM T6
# =============================================================================


class P7ObservabilityHooks:
    """
    Required observability hooks per GEM EventBuffer Observability (T6).

    Both CC1 (backend) and CC3 (frontend) must expose these metrics.
    """

    REQUIRED_METRICS: List[str] = [
        "last_sequence_id",
        "buffer_size",
        "gap_count",
        "events_processed",
        "events_dropped",
        "replay_count",
        "keepalive_delta_ms",
        "connection_state",
        "last_event_timestamp",
    ]

    REQUIRED_EVENTS: List[str] = [
        "on_gap_detected",
        "on_replay_start",
        "on_replay_complete",
        "on_state_change",
        "on_buffer_overflow",
    ]


# =============================================================================
# CONTRACT VERSION
# =============================================================================

P7_CONTRACT_VERSION = "1.0.0"
P7_CONTRACT_STATUS = "STABLE"

# Version History:
# 1.0.0 (2025-12-10) - Initial stable release
#   - P7ConnectionState: 4 states (ACTIVE, STALE, RECONNECTING, TERMINATED)
#   - P7EventType: 13 event types
#   - P7TimingSpec: Keepalive 30s, Stale 45s, Reconnect backoff
#   - P7GapDetectionRules: Threshold 1, Buffer 1000, Max gap 100
#   - Full FE/BE implementation validated by CAI
#   - State mapping confirmed by GEM
#
# 7.0.0-placeholder (2025-12-XX) - Initial draft (superseded)

__all__ = [
    "P7ConnectionState",
    "P7EventType",
    "P7TimingSpec",
    "P7_TIMING",
    "P7EventEnvelopeSchema",
    "P7GapDetectionRules",
    "P7_GAP_RULES",
    "P7ScrollSyncEvent",
    "P7HighlightEvent",
    "P7ObservabilityHooks",
    "P7_CONTRACT_VERSION",
    "P7_CONTRACT_STATUS",
]
