"""
Event Buffer Stub for P7 SSE Integration
Phase 7 Preparation - Mock Implementation

This module provides stub interfaces for SSE event handling.
NO BACKEND CALLS - mock-only implementation for P7 readiness.

CC3 P7-PREP - EventBuffer Stub
Version: 0.1.0-stub
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from datetime import datetime
import json


# ============================================================================
# CONNECTION STATE
# ============================================================================

class ConnectionState(str, Enum):
    """SSE connection states for UI indicator."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    REPLAYING = "replaying"
    ERROR = "error"


# ============================================================================
# EVENT ENVELOPE
# ============================================================================

@dataclass
class EventEnvelope:
    """
    Standard event envelope for SSE messages.
    Matches CAI backend contract (placeholder).
    """
    event_id: str
    event_type: str
    sequence_number: int
    timestamp: str
    payload: Dict[str, Any]
    session_id: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "session_id": self.session_id,
        })

    @classmethod
    def from_json(cls, data: str) -> "EventEnvelope":
        obj = json.loads(data)
        return cls(**obj)


# ============================================================================
# SEQUENCE VALIDATOR (STUB)
# ============================================================================

class SequenceValidator:
    """
    Validates event sequence numbers to detect gaps.
    Stub implementation for P7 readiness.
    """

    def __init__(self):
        self._last_sequence: int = -1
        self._gaps: List[tuple] = []
        self._on_gap_callbacks: List[Callable[[int, int], None]] = []

    def validate(self, sequence: int) -> bool:
        """
        Validate incoming sequence number.

        Returns:
            True if sequence is valid (no gap), False if gap detected
        """
        if self._last_sequence == -1:
            self._last_sequence = sequence
            return True

        expected = self._last_sequence + 1
        if sequence == expected:
            self._last_sequence = sequence
            return True
        elif sequence > expected:
            # Gap detected
            self._gaps.append((expected, sequence - 1))
            for cb in self._on_gap_callbacks:
                cb(expected, sequence - 1)
            # P7.S2 Task 8: Call gap metadata reporting hook
            try:
                from .sequence_validator_hooks import on_gap_detected
                on_gap_detected(self._last_sequence, sequence)
            except ImportError:
                pass  # Hook not available (graceful degradation)
            self._last_sequence = sequence
            return False
        else:
            # Duplicate or out-of-order (ignored in stub)
            return True

    def get_gaps(self) -> List[tuple]:
        """Get list of detected sequence gaps."""
        return self._gaps.copy()

    def on_gap(self, callback: Callable[[int, int], None]) -> None:
        """Register callback for gap detection."""
        self._on_gap_callbacks.append(callback)

    def reset(self) -> None:
        """Reset validator state."""
        self._last_sequence = -1
        self._gaps = []


# ============================================================================
# EVENT BUFFER (STUB)
# ============================================================================

class EventBuffer:
    """
    Buffers SSE events for processing.
    Stub implementation - no actual SSE connection.
    """

    def __init__(self, max_size: int = 1000):
        self._buffer: List[EventEnvelope] = []
        self._max_size = max_size
        self._sequence_validator = SequenceValidator()
        self._event_handlers: Dict[str, List[Callable[[EventEnvelope], None]]] = {}
        self._connection_state = ConnectionState.DISCONNECTED
        self._state_callbacks: List[Callable[[ConnectionState], None]] = []

    def push(self, event: EventEnvelope) -> bool:
        """
        Push event to buffer.

        Returns:
            True if sequence valid, False if gap detected
        """
        valid = self._sequence_validator.validate(event.sequence_number)

        self._buffer.append(event)
        if len(self._buffer) > self._max_size:
            self._buffer = self._buffer[-self._max_size:]

        # Dispatch to handlers
        handlers = self._event_handlers.get(event.event_type, [])
        handlers.extend(self._event_handlers.get("*", []))
        for handler in handlers:
            handler(event)

        return valid

    def on_event(self, event_type: str, handler: Callable[[EventEnvelope], None]) -> None:
        """
        Register handler for event type.
        Use "*" for all events.
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def get_recent(self, count: int = 10) -> List[EventEnvelope]:
        """Get most recent events from buffer."""
        return self._buffer[-count:]

    def get_by_type(self, event_type: str) -> List[EventEnvelope]:
        """Get events of specific type."""
        return [e for e in self._buffer if e.event_type == event_type]

    def set_connection_state(self, state: ConnectionState) -> None:
        """Update connection state and notify callbacks."""
        self._connection_state = state
        for cb in self._state_callbacks:
            cb(state)

    def get_connection_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._connection_state

    def on_state_change(self, callback: Callable[[ConnectionState], None]) -> None:
        """Register callback for connection state changes."""
        self._state_callbacks.append(callback)

    def get_sequence_validator(self) -> SequenceValidator:
        """Get the sequence validator instance."""
        return self._sequence_validator

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer = []
        self._sequence_validator.reset()


# ============================================================================
# CONNECTION STATE INDICATOR (STUB)
# ============================================================================

@dataclass
class ConnectionStateIndicator:
    """
    UI state for connection indicator component.
    Stub for P7 visual debug overlay.
    """
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_event_time: Optional[str] = None
    events_received: int = 0
    gaps_detected: int = 0
    reconnect_attempts: int = 0

    def update_from_buffer(self, buffer: EventBuffer) -> None:
        """Update indicator state from buffer."""
        self.state = buffer.get_connection_state()
        recent = buffer.get_recent(1)
        if recent:
            self.last_event_time = recent[0].timestamp
        self.gaps_detected = len(buffer.get_sequence_validator().get_gaps())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "last_event_time": self.last_event_time,
            "events_received": self.events_received,
            "gaps_detected": self.gaps_detected,
            "reconnect_attempts": self.reconnect_attempts,
        }


# ============================================================================
# MOCK SSE CLIENT (STUB)
# ============================================================================

class MockSSEClient:
    """
    Mock SSE client for testing without backend.
    Generates synthetic events for development.
    """

    def __init__(self, buffer: EventBuffer):
        self._buffer = buffer
        self._sequence = 0
        self._running = False

    def connect(self) -> None:
        """Simulate connection."""
        self._buffer.set_connection_state(ConnectionState.CONNECTING)
        self._buffer.set_connection_state(ConnectionState.CONNECTED)
        self._running = True

    def disconnect(self) -> None:
        """Simulate disconnection."""
        self._running = False
        self._buffer.set_connection_state(ConnectionState.DISCONNECTED)

    def simulate_event(self, event_type: str, payload: Dict[str, Any]) -> EventEnvelope:
        """Generate and push a synthetic event."""
        self._sequence += 1
        event = EventEnvelope(
            event_id=f"mock-{self._sequence}",
            event_type=event_type,
            sequence_number=self._sequence,
            timestamp=datetime.now().isoformat(),
            payload=payload,
        )
        self._buffer.push(event)
        return event

    def simulate_scroll_highlight(self, clause_id: int, panel: str) -> EventEnvelope:
        """Simulate a scroll highlight event."""
        return self.simulate_event("scroll_highlight", {
            "clause_id": clause_id,
            "panel": panel,
            "action": "highlight",
        })

    def simulate_intelligence_update(self, clause_id: int, engine: str, data: Dict) -> EventEnvelope:
        """Simulate an intelligence update event."""
        return self.simulate_event("intelligence_update", {
            "clause_id": clause_id,
            "engine": engine,
            "data": data,
        })

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._running


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "0.1.0-stub"
__phase__ = "Phase 7 Preparation"
__status__ = "STUB - No backend implementation"


# ============================================================================
# REAL SSE CLIENT (P7.S2 - DIAGNOSTICS ONLY)
# ============================================================================

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

import threading


class RealSSEClient:
    """
    Real SSE client for connecting to backend stream endpoint.
    P7.S2 Activation - DIAGNOSTICS CONTEXT ONLY
    """

    def __init__(self, endpoint: str, buffer: EventBuffer, session_id: str = "diag"):
        self._endpoint = endpoint.format(session_id=session_id)
        self._buffer = buffer
        self._session_id = session_id
        self._running = False
        self._thread = None
        self._response = None
        self._events_received = 0
        self._connection_errors = 0
        self._last_error = None

    def connect(self) -> bool:
        if not REQUESTS_AVAILABLE:
            self._last_error = "requests library not available"
            self._buffer.set_connection_state(ConnectionState.ERROR)
            return False
        if self._running:
            return True
        self._buffer.set_connection_state(ConnectionState.CONNECTING)
        self._running = True
        self._thread = threading.Thread(target=self._stream_reader, daemon=True)
        self._thread.start()
        return True

    def disconnect(self) -> None:
        self._running = False
        if self._response:
            try:
                self._response.close()
            except Exception:
                pass
        self._buffer.set_connection_state(ConnectionState.DISCONNECTED)

    def _stream_reader(self) -> None:
        try:
            self._response = requests.get(
                self._endpoint, stream=True,
                headers={"Accept": "text/event-stream"},
                timeout=(5, None),
            )
            if self._response.status_code == 200:
                self._buffer.set_connection_state(ConnectionState.CONNECTED)
                self._parse_stream()
            else:
                self._last_error = f"HTTP {self._response.status_code}"
                self._connection_errors += 1
                self._buffer.set_connection_state(ConnectionState.ERROR)
        except Exception as e:
            self._last_error = str(e)
            self._connection_errors += 1
            self._buffer.set_connection_state(ConnectionState.ERROR)
        finally:
            self._running = False

    def _parse_stream(self) -> None:
        event_data, event_type, event_id = "", "message", ""
        for line in self._response.iter_lines(decode_unicode=True):
            if not self._running:
                break
            if line is None:
                continue
            if line == "":
                if event_data:
                    self._dispatch_event(event_type, event_data, event_id)
                    event_data, event_type, event_id = "", "message", ""
                continue
            if line.startswith("data:"):
                data = line[5:].strip()
                event_data = data if not event_data else event_data + chr(10) + data
            elif line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("id:"):
                event_id = line[3:].strip()

    def _dispatch_event(self, event_type: str, data: str, event_id: str) -> None:
        try:
            payload = json.loads(data) if data else {}
            seq = payload.get("seq", payload.get("sequence_number", self._events_received + 1))
            envelope = EventEnvelope(
                event_id=event_id or f"sse-{self._events_received + 1}",
                event_type=event_type, sequence_number=seq,
                timestamp=payload.get("timestamp", datetime.now().isoformat()),
                payload=payload, session_id=self._session_id,
            )
            self._buffer.push(envelope)
            self._events_received += 1
        except json.JSONDecodeError:
            envelope = EventEnvelope(
                event_id=event_id or f"sse-{self._events_received + 1}",
                event_type=event_type, sequence_number=self._events_received + 1,
                timestamp=datetime.now().isoformat(),
                payload={"raw": data}, session_id=self._session_id,
            )
            self._buffer.push(envelope)
            self._events_received += 1

    def is_connected(self) -> bool:
        return self._running and self._buffer.get_connection_state() == ConnectionState.CONNECTED

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "endpoint": self._endpoint, "session_id": self._session_id,
            "is_connected": self.is_connected(), "events_received": self._events_received,
            "connection_errors": self._connection_errors, "last_error": self._last_error,
            "connection_state": self._buffer.get_connection_state().value,
        }


# Backend base URL for SSE endpoints (configure based on environment)
SSE_BASE_URL = "http://localhost:5000"

USE_REAL_SSE = True


class DiagnosticsSSEContext:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._buffer = EventBuffer()
        self._validator = SequenceValidator()
        self._client = None
        self._initialized = True
        self._buffer.on_event("*", self._on_event)

    def _on_event(self, event: EventEnvelope) -> None:
        self._validator.validate(event.sequence_number)

    def connect(self, session_id: str = "diagnostics", base_url: str = None) -> bool:
        if USE_REAL_SSE:
            url = base_url or SSE_BASE_URL
            self._client = RealSSEClient(
                endpoint=f"{url}/api/v1/stream/{{session_id}}",
                buffer=self._buffer, session_id=session_id,
            )
        else:
            self._client = MockSSEClient(self._buffer)
        if isinstance(self._client, RealSSEClient):
            return self._client.connect()
        else:
            self._client.connect()
            return True

    def disconnect(self) -> None:
        if self._client:
            self._client.disconnect()

    def get_diagnostics_metrics(self) -> Dict[str, Any]:
        gaps = self._validator.get_gaps()
        return {
            "last_sequence_id": self._validator._last_sequence,
            "buffer_size": len(self._buffer._buffer),
            "gap_count": len(gaps),
            "connection_state": self._buffer.get_connection_state().value,
            "use_real_sse": USE_REAL_SSE,
            "client_type": "real" if isinstance(self._client, RealSSEClient) else "mock",
            "events_in_buffer": len(self._buffer._buffer),
            "gaps": [{"start": g[0], "end": g[1]} for g in gaps],
        }

    def get_buffer(self) -> EventBuffer:
        return self._buffer

    def get_validator(self) -> SequenceValidator:
        return self._validator

    def get_client(self):
        return self._client

    def simulate_event(self, event_type: str, payload: Dict[str, Any]):
        if isinstance(self._client, MockSSEClient):
            return self._client.simulate_event(event_type, payload)
        return None


def get_diagnostics_context() -> DiagnosticsSSEContext:
    return DiagnosticsSSEContext()
