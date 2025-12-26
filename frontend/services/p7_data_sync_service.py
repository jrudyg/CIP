"""
P7 Data Sync Service - Scroll Sync & Highlight Client Hooks
GEM P7.S1 Execution Directive - CC3 Task 2

Service layer functions to consume and route P7 events:
- Routing logic for SCROLL_SYNC to P6.C3.T1 Scroll Engine
- Routing logic for HIGHLIGHT events to Contract Viewer DOM
- CRITICAL: 100ms debounce for outgoing scroll events (P7 Timing Spec T2)

CC3 P7.S1.T2 - Data Sync Service
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import threading
import time

if TYPE_CHECKING:
    from ..components.p7_stream_validator import P7EventEnvelope, EventBuffer
    from ..integrations.workspace_mode import WorkspaceController, PanelPosition


# ============================================================================
# P7 EVENT TYPES
# ============================================================================

class P7EventType(str, Enum):
    """P7 SSE event types."""
    SCROLL_SYNC = "scroll_sync"
    HIGHLIGHT = "highlight"
    INTELLIGENCE_UPDATE = "intelligence_update"
    PANEL_STATE = "panel_state"
    KEEPALIVE = "keepalive"


# ============================================================================
# DEBOUNCE UTILITY
# ============================================================================

class Debouncer:
    """
    Debounce utility for rate-limiting outgoing events.
    CRITICAL: Implements 100ms debounce per P7 Timing Spec (T2).
    """

    def __init__(self, delay_ms: int = 100):
        self._delay_ms = delay_ms
        self._last_call_time: Optional[float] = None
        self._pending_value: Any = None
        self._timer: Optional[threading.Timer] = None
        self._callback: Optional[Callable[[Any], None]] = None
        self._lock = threading.Lock()

    def set_callback(self, callback: Callable[[Any], None]) -> None:
        """Set the callback to invoke after debounce."""
        self._callback = callback

    def call(self, value: Any) -> bool:
        """
        Debounced call. Returns True if call was scheduled, False if debounced.

        Args:
            value: Value to pass to callback after debounce

        Returns:
            True if this call will trigger callback, False if debounced
        """
        with self._lock:
            current_time = time.time() * 1000  # ms

            # Cancel pending timer
            if self._timer:
                self._timer.cancel()
                self._timer = None

            # Store pending value
            self._pending_value = value

            # Check if we can call immediately (first call or after delay)
            if self._last_call_time is None or (current_time - self._last_call_time) >= self._delay_ms:
                self._execute()
                return True
            else:
                # Schedule delayed execution
                remaining_ms = self._delay_ms - (current_time - self._last_call_time)
                self._timer = threading.Timer(remaining_ms / 1000, self._execute)
                self._timer.start()
                return False

    def _execute(self) -> None:
        """Execute the callback with pending value."""
        with self._lock:
            if self._callback and self._pending_value is not None:
                try:
                    self._callback(self._pending_value)
                except Exception:
                    pass
                finally:
                    self._last_call_time = time.time() * 1000
                    self._pending_value = None

    def cancel(self) -> None:
        """Cancel pending debounced call."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._pending_value = None

    def get_delay_ms(self) -> int:
        """Get debounce delay."""
        return self._delay_ms


# ============================================================================
# SCROLL SYNC COMMAND
# ============================================================================

@dataclass
class ScrollSyncCommand:
    """Command structure for scroll synchronization."""
    source_panel: str
    offset: float
    sync_mode: str = "clause_aligned"
    timestamp: str = ""
    debounced: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_panel": self.source_panel,
            "offset": self.offset,
            "sync_mode": self.sync_mode,
            "timestamp": self.timestamp,
            "debounced": self.debounced,
        }


# ============================================================================
# HIGHLIGHT COMMAND
# ============================================================================

@dataclass
class HighlightCommand:
    """Command structure for clause highlighting."""
    clause_id: int
    action: str  # "add", "remove", "clear", "focus"
    panel: str = "center"
    style: str = "default"
    scroll_to: bool = False
    duration_ms: Optional[int] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "action": self.action,
            "panel": self.panel,
            "style": self.style,
            "scroll_to": self.scroll_to,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


# ============================================================================
# SCROLL SYNC SERVICE
# ============================================================================

class ScrollSyncService:
    """
    Service for routing SCROLL_SYNC events to P6.C3.T1 Scroll Engine.

    Features:
    - Routes incoming SSE scroll events to workspace controller
    - Implements 100ms debounce for OUTGOING scroll events (P7 Timing Spec T2)
    - Tracks scroll state for diagnostics
    """

    # P7 Timing Spec T2: 100ms debounce for outgoing scroll events
    OUTGOING_DEBOUNCE_MS = 100

    def __init__(self):
        self._workspace_controller: Optional["WorkspaceController"] = None
        self._outgoing_debouncer = Debouncer(delay_ms=self.OUTGOING_DEBOUNCE_MS)
        self._outgoing_debouncer.set_callback(self._send_scroll_event)

        # Callbacks for outgoing events (to SSE sender)
        self._outgoing_callbacks: List[Callable[[ScrollSyncCommand], None]] = []

        # Metrics
        self._incoming_count: int = 0
        self._outgoing_count: int = 0
        self._debounced_count: int = 0
        self._last_incoming: Optional[ScrollSyncCommand] = None
        self._last_outgoing: Optional[ScrollSyncCommand] = None

        self._lock = threading.Lock()

    def attach_workspace_controller(self, controller: "WorkspaceController") -> None:
        """Attach workspace controller for scroll routing."""
        self._workspace_controller = controller

    def handle_incoming_scroll(self, event: "P7EventEnvelope") -> Optional[ScrollSyncCommand]:
        """
        Handle incoming SCROLL_SYNC SSE event.
        Routes to P6.C3.T1 Scroll Engine.

        Args:
            event: The SSE event envelope

        Returns:
            ScrollSyncCommand if processed, None if invalid
        """
        with self._lock:
            payload = event.payload

            command = ScrollSyncCommand(
                source_panel=payload.get("source_panel", "center"),
                offset=payload.get("offset", 0.0),
                sync_mode=payload.get("sync_mode", "clause_aligned"),
                timestamp=event.timestamp,
            )

            self._incoming_count += 1
            self._last_incoming = command

            # Route to workspace controller
            if self._workspace_controller:
                try:
                    # Import here to avoid circular imports
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                    from integrations.workspace_mode import PanelPosition

                    source = PanelPosition(command.source_panel)
                    self._workspace_controller.handle_scroll(source, command.offset)
                except Exception:
                    pass

            return command

    def send_scroll_event(self, source_panel: str, offset: float, sync_mode: str = "clause_aligned") -> bool:
        """
        Send outgoing scroll event (with 100ms debounce per T2).

        Args:
            source_panel: Panel initiating scroll
            offset: Scroll offset in pixels
            sync_mode: Synchronization mode

        Returns:
            True if event will be sent, False if debounced
        """
        command = ScrollSyncCommand(
            source_panel=source_panel,
            offset=offset,
            sync_mode=sync_mode,
        )

        will_send = self._outgoing_debouncer.call(command)

        with self._lock:
            if not will_send:
                self._debounced_count += 1
                command.debounced = True

        return will_send

    def _send_scroll_event(self, command: ScrollSyncCommand) -> None:
        """Internal callback for debounced scroll send."""
        with self._lock:
            self._outgoing_count += 1
            self._last_outgoing = command

        # Notify outgoing callbacks
        for cb in self._outgoing_callbacks:
            try:
                cb(command)
            except Exception:
                pass

    def on_outgoing_scroll(self, callback: Callable[[ScrollSyncCommand], None]) -> None:
        """Register callback for outgoing scroll events (to SSE sender)."""
        self._outgoing_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get scroll sync service metrics."""
        with self._lock:
            return {
                "incoming_count": self._incoming_count,
                "outgoing_count": self._outgoing_count,
                "debounced_count": self._debounced_count,
                "debounce_ms": self.OUTGOING_DEBOUNCE_MS,
                "last_incoming": self._last_incoming.to_dict() if self._last_incoming else None,
                "last_outgoing": self._last_outgoing.to_dict() if self._last_outgoing else None,
            }


# ============================================================================
# HIGHLIGHT SERVICE
# ============================================================================

class HighlightService:
    """
    Service for routing HIGHLIGHT events to Contract Viewer DOM.

    Features:
    - Routes incoming SSE highlight events to DOM elements
    - Manages active highlights state
    - Supports highlight styles (default, risk, match, diff)
    """

    def __init__(self):
        self._active_highlights: Dict[int, HighlightCommand] = {}
        self._highlight_callbacks: List[Callable[[HighlightCommand], None]] = []
        self._clear_callbacks: List[Callable[[], None]] = []

        # Metrics
        self._total_commands: int = 0
        self._add_count: int = 0
        self._remove_count: int = 0
        self._clear_count: int = 0

        self._lock = threading.Lock()

    def handle_incoming_highlight(self, event: "P7EventEnvelope") -> Optional[HighlightCommand]:
        """
        Handle incoming HIGHLIGHT SSE event.
        Routes to Contract Viewer DOM.

        Args:
            event: The SSE event envelope

        Returns:
            HighlightCommand if processed, None if invalid
        """
        with self._lock:
            payload = event.payload

            if "clause_id" not in payload:
                return None

            command = HighlightCommand(
                clause_id=payload["clause_id"],
                action=payload.get("action", "add"),
                panel=payload.get("panel", "center"),
                style=payload.get("style", "default"),
                scroll_to=payload.get("scroll_to", False),
                duration_ms=payload.get("duration_ms"),
                timestamp=event.timestamp,
            )

            self._total_commands += 1

            # Process action
            if command.action == "add" or command.action == "focus":
                self._active_highlights[command.clause_id] = command
                self._add_count += 1
            elif command.action == "remove":
                self._active_highlights.pop(command.clause_id, None)
                self._remove_count += 1
            elif command.action == "clear":
                self._active_highlights.clear()
                self._clear_count += 1
                for cb in self._clear_callbacks:
                    try:
                        cb()
                    except Exception:
                        pass

            # Notify callbacks for DOM update
            for cb in self._highlight_callbacks:
                try:
                    cb(command)
                except Exception:
                    pass

            return command

    def on_highlight(self, callback: Callable[[HighlightCommand], None]) -> None:
        """Register callback for highlight commands (DOM updates)."""
        self._highlight_callbacks.append(callback)

    def on_clear(self, callback: Callable[[], None]) -> None:
        """Register callback for clear all action."""
        self._clear_callbacks.append(callback)

    def get_active_highlights(self) -> Dict[int, HighlightCommand]:
        """Get currently active highlights."""
        with self._lock:
            return self._active_highlights.copy()

    def get_highlight_for_clause(self, clause_id: int) -> Optional[HighlightCommand]:
        """Get highlight for specific clause if active."""
        with self._lock:
            return self._active_highlights.get(clause_id)

    def clear_all(self) -> None:
        """Programmatically clear all highlights."""
        with self._lock:
            self._active_highlights.clear()
            self._clear_count += 1

        for cb in self._clear_callbacks:
            try:
                cb()
            except Exception:
                pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get highlight service metrics."""
        with self._lock:
            return {
                "total_commands": self._total_commands,
                "add_count": self._add_count,
                "remove_count": self._remove_count,
                "clear_count": self._clear_count,
                "active_highlight_count": len(self._active_highlights),
                "active_clause_ids": list(self._active_highlights.keys()),
            }


# ============================================================================
# P7 DATA SYNC SERVICE (UNIFIED)
# ============================================================================

class P7DataSyncService:
    """
    Unified service for P7 data synchronization.
    Coordinates scroll sync and highlight routing.
    """

    def __init__(self):
        self._scroll_service = ScrollSyncService()
        self._highlight_service = HighlightService()
        self._event_buffer: Optional["EventBuffer"] = None

        # Event routing
        self._event_handlers: Dict[str, Callable[["P7EventEnvelope"], Any]] = {
            P7EventType.SCROLL_SYNC.value: self._handle_scroll_sync,
            P7EventType.HIGHLIGHT.value: self._handle_highlight,
        }

    def attach_event_buffer(self, buffer: "EventBuffer") -> None:
        """Attach event buffer and wire up handlers."""
        self._event_buffer = buffer

        # Register handlers for event types
        buffer.on_event(P7EventType.SCROLL_SYNC.value, self._handle_scroll_sync)
        buffer.on_event(P7EventType.HIGHLIGHT.value, self._handle_highlight)

    def attach_workspace_controller(self, controller: "WorkspaceController") -> None:
        """Attach workspace controller for scroll routing."""
        self._scroll_service.attach_workspace_controller(controller)

    def _handle_scroll_sync(self, event: "P7EventEnvelope") -> None:
        """Route SCROLL_SYNC event."""
        self._scroll_service.handle_incoming_scroll(event)

    def _handle_highlight(self, event: "P7EventEnvelope") -> None:
        """Route HIGHLIGHT event."""
        self._highlight_service.handle_incoming_highlight(event)

    def route_event(self, event: "P7EventEnvelope") -> bool:
        """
        Route event to appropriate handler.

        Args:
            event: The SSE event to route

        Returns:
            True if event was handled
        """
        handler = self._event_handlers.get(event.event_type)
        if handler:
            handler(event)
            return True
        return False

    def get_scroll_service(self) -> ScrollSyncService:
        """Get scroll sync service."""
        return self._scroll_service

    def get_highlight_service(self) -> HighlightService:
        """Get highlight service."""
        return self._highlight_service

    def on_outgoing_scroll(self, callback: Callable[[ScrollSyncCommand], None]) -> None:
        """Register callback for outgoing scroll events."""
        self._scroll_service.on_outgoing_scroll(callback)

    def on_highlight(self, callback: Callable[[HighlightCommand], None]) -> None:
        """Register callback for highlight commands."""
        self._highlight_service.on_highlight(callback)

    def send_scroll(self, source_panel: str, offset: float) -> bool:
        """
        Send outgoing scroll event (debounced per T2).

        Returns:
            True if event will be sent, False if debounced
        """
        return self._scroll_service.send_scroll_event(source_panel, offset)

    def get_metrics(self) -> Dict[str, Any]:
        """Get unified service metrics."""
        return {
            "scroll": self._scroll_service.get_metrics(),
            "highlight": self._highlight_service.get_metrics(),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "1.0.0"
__phase__ = "Phase 7 - P7.S1"
__contract__ = "P7 Timing Spec (T2) - 100ms outgoing debounce"
