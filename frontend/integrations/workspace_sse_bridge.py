"""
Workspace SSE Bridge
Phase 7 Preparation - Links WorkspaceController to EventBuffer

This module bridges the P6 workspace components with P7 SSE infrastructure.
Provides scroll + highlight routing hooks without actual backend calls.

CC3 P7-PREP - Workspace SSE Bridge
Version: 0.1.0-stub
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

from .event_buffer_stub import (
    EventBuffer,
    EventEnvelope,
    ConnectionState,
    MockSSEClient,
    RealSSEClient,
    ConnectionStateIndicator,
    USE_REAL_SSE,
    SSE_BASE_URL,
)
from .workspace_mode import (
    WorkspaceController,
    PanelPosition,
    ScrollSyncMode,
    TopNavTab,
)

if TYPE_CHECKING:
    from .layout_diagnostics import LayoutDiagnosticPanel


# ============================================================================
# FEATURE FLAG FOR LIVE P7 STREAM
# ============================================================================

FLAG_ENABLE_LIVE_P7_STREAM = "enable_live_p7_stream"

def is_feature_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled. Uses USE_REAL_SSE as the source."""
    if flag_name == FLAG_ENABLE_LIVE_P7_STREAM:
        return USE_REAL_SSE
    return False


def get_workspace_client(session_id: str, buffer: EventBuffer):
    """
    Selects the appropriate SSE client based on the feature flag.

    Args:
        session_id: The session identifier for the stream
        buffer: The EventBuffer to receive events

    Returns:
        RealSSEClient if live streaming is enabled, MockSSEClient otherwise
    """
    if is_feature_enabled(FLAG_ENABLE_LIVE_P7_STREAM):
        # Use the validated Real SSE Client
        endpoint_template = SSE_BASE_URL + "/api/v1/stream/{session_id}"
        return RealSSEClient(
            endpoint=endpoint_template,
            buffer=buffer,
            session_id=session_id,
        )
    else:
        # Fallback to the production-safe Mock Client
        return MockSSEClient(buffer)



# ============================================================================
# SSE EVENT TYPES FOR WORKSPACE
# ============================================================================

class WorkspaceEventType:
    """Event type constants for workspace SSE events."""
    SCROLL_SYNC = "scroll_sync"
    HIGHLIGHT_CLAUSE = "highlight_clause"
    INTELLIGENCE_UPDATE = "intelligence_update"
    PANEL_RESIZE = "panel_resize"
    MODE_CHANGE = "mode_change"
    ENGINE_STATUS = "engine_status"


# ============================================================================
# SCROLL ROUTING HOOK
# ============================================================================

@dataclass
class ScrollRoutingEvent:
    """Scroll event for routing between panels."""
    source_panel: PanelPosition
    target_panels: List[PanelPosition]
    source_offset: float
    calculated_offsets: Dict[str, float]
    sync_mode: ScrollSyncMode
    timestamp: str


class ScrollRoutingHook:
    """
    Routes scroll events from SSE to WorkspaceController.
    Provides hook interface for P7 SSE integration.
    """

    def __init__(self, controller: WorkspaceController):
        self._controller = controller
        self._event_log: List[ScrollRoutingEvent] = []
        self._callbacks: List[Callable[[ScrollRoutingEvent], None]] = []

    def handle_sse_scroll(self, event: EventEnvelope) -> Optional[ScrollRoutingEvent]:
        """
        Handle incoming SSE scroll event.

        Args:
            event: SSE event envelope with scroll data

        Returns:
            ScrollRoutingEvent if processed, None if invalid
        """
        payload = event.payload
        if not payload.get("source_panel"):
            return None

        source_panel = PanelPosition(payload["source_panel"])
        offset = payload.get("offset", 0.0)

        # Route through controller
        results = self._controller.handle_scroll(source_panel, offset)

        # Build routing event
        routing_event = ScrollRoutingEvent(
            source_panel=source_panel,
            target_panels=[p for p in results.keys() if p != source_panel],
            source_offset=offset,
            calculated_offsets={p.value: o for p, o in results.items()},
            sync_mode=self._controller.get_state().scroll_sync_mode,
            timestamp=event.timestamp,
        )

        self._event_log.append(routing_event)

        # Notify callbacks
        for cb in self._callbacks:
            cb(routing_event)

        return routing_event

    def on_scroll_routed(self, callback: Callable[[ScrollRoutingEvent], None]) -> None:
        """Register callback for routed scroll events."""
        self._callbacks.append(callback)

    def get_event_log(self, limit: int = 100) -> List[ScrollRoutingEvent]:
        """Get recent scroll routing events."""
        return self._event_log[-limit:]


# ============================================================================
# HIGHLIGHT ROUTING HOOK
# ============================================================================

@dataclass
class HighlightRoutingEvent:
    """Highlight event for clause highlighting."""
    clause_id: int
    panel: PanelPosition
    action: str  # "highlight", "unhighlight", "focus"
    scroll_to: bool
    timestamp: str


class HighlightRoutingHook:
    """
    Routes highlight events from SSE to UI components.
    Provides hook interface for P7 SSE integration.
    """

    def __init__(self):
        self._active_highlights: Dict[int, PanelPosition] = {}
        self._event_log: List[HighlightRoutingEvent] = []
        self._callbacks: List[Callable[[HighlightRoutingEvent], None]] = []

    def handle_sse_highlight(self, event: EventEnvelope) -> Optional[HighlightRoutingEvent]:
        """
        Handle incoming SSE highlight event.

        Args:
            event: SSE event envelope with highlight data

        Returns:
            HighlightRoutingEvent if processed, None if invalid
        """
        payload = event.payload
        if "clause_id" not in payload:
            return None

        clause_id = payload["clause_id"]
        panel = PanelPosition(payload.get("panel", "center"))
        action = payload.get("action", "highlight")
        scroll_to = payload.get("scroll_to", True)

        # Update active highlights
        if action == "highlight":
            self._active_highlights[clause_id] = panel
        elif action == "unhighlight" and clause_id in self._active_highlights:
            del self._active_highlights[clause_id]

        # Build routing event
        routing_event = HighlightRoutingEvent(
            clause_id=clause_id,
            panel=panel,
            action=action,
            scroll_to=scroll_to,
            timestamp=event.timestamp,
        )

        self._event_log.append(routing_event)

        # Notify callbacks
        for cb in self._callbacks:
            cb(routing_event)

        return routing_event

    def on_highlight_routed(self, callback: Callable[[HighlightRoutingEvent], None]) -> None:
        """Register callback for routed highlight events."""
        self._callbacks.append(callback)

    def get_active_highlights(self) -> Dict[int, PanelPosition]:
        """Get currently active clause highlights."""
        return self._active_highlights.copy()

    def clear_all_highlights(self) -> None:
        """Clear all active highlights."""
        self._active_highlights.clear()


# ============================================================================
# WORKSPACE SSE BRIDGE
# ============================================================================

class WorkspaceSSEBridge:
    """
    Main bridge connecting WorkspaceController to SSE EventBuffer.
    Coordinates scroll and highlight routing with mock support.
    """

    def __init__(self, controller: WorkspaceController, session_id: str = "workspace"):
        self._controller = controller
        self._session_id = session_id
        self._event_buffer = EventBuffer()
        # Use feature flag to select client type
        self._client = get_workspace_client(session_id, self._event_buffer)
        # Keep reference for backward compatibility
        self._mock_client = self._client if isinstance(self._client, MockSSEClient) else None

        # Routing hooks
        self._scroll_hook = ScrollRoutingHook(controller)
        self._highlight_hook = HighlightRoutingHook()

        # Connection indicator
        self._indicator = ConnectionStateIndicator()

        # Diagnostic panel (optional)
        self._diagnostic_panel: Optional["LayoutDiagnosticPanel"] = None

        # Wire up event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Set up SSE event handlers."""
        self._event_buffer.on_event(
            WorkspaceEventType.SCROLL_SYNC,
            self._handle_scroll_event
        )
        self._event_buffer.on_event(
            WorkspaceEventType.HIGHLIGHT_CLAUSE,
            self._handle_highlight_event
        )
        self._event_buffer.on_event(
            WorkspaceEventType.MODE_CHANGE,
            self._handle_mode_change
        )

        # Update indicator on state changes
        self._event_buffer.on_state_change(self._on_connection_state_change)

    def _handle_scroll_event(self, event: EventEnvelope) -> None:
        """Handle scroll sync event."""
        result = self._scroll_hook.handle_sse_scroll(event)
        if result and self._diagnostic_panel:
            self._diagnostic_panel.info("sse_bridge", "Scroll routed", {
                "source": result.source_panel.value,
                "offset": result.source_offset,
            })

    def _handle_highlight_event(self, event: EventEnvelope) -> None:
        """Handle highlight event."""
        result = self._highlight_hook.handle_sse_highlight(event)
        if result and self._diagnostic_panel:
            self._diagnostic_panel.info("sse_bridge", "Highlight routed", {
                "clause_id": result.clause_id,
                "action": result.action,
            })

    def _handle_mode_change(self, event: EventEnvelope) -> None:
        """Handle mode change event."""
        payload = event.payload
        if "tab" in payload:
            tab = TopNavTab(payload["tab"])
            self._controller.set_tab(tab)
            if self._diagnostic_panel:
                self._diagnostic_panel.info("sse_bridge", "Mode changed", {
                    "tab": tab.value,
                })

    def _on_connection_state_change(self, state: ConnectionState) -> None:
        """Handle connection state change."""
        self._indicator.state = state
        if self._diagnostic_panel:
            self._diagnostic_panel.info("sse_bridge", f"Connection state: {state.value}")

    def attach_diagnostics(self, panel: "LayoutDiagnosticPanel") -> None:
        """Attach diagnostic panel for instrumentation."""
        self._diagnostic_panel = panel
        panel.info("sse_bridge", "WorkspaceSSEBridge attached to diagnostics")

    def connect(self) -> None:
        """Connect to SSE (uses RealSSEClient if feature flag enabled)."""
        self._client.connect()

    def disconnect(self) -> None:
        """Disconnect from SSE."""
        self._client.disconnect()

    def get_event_buffer(self) -> EventBuffer:
        """Get the event buffer."""
        return self._event_buffer

    def get_scroll_hook(self) -> ScrollRoutingHook:
        """Get the scroll routing hook."""
        return self._scroll_hook

    def get_highlight_hook(self) -> HighlightRoutingHook:
        """Get the highlight routing hook."""
        return self._highlight_hook

    def get_connection_indicator(self) -> ConnectionStateIndicator:
        """Get connection state indicator for UI."""
        self._indicator.update_from_buffer(self._event_buffer)
        return self._indicator

    def get_mock_client(self) -> MockSSEClient:
        """Get mock client for testing (returns None if using real client)."""
        return self._mock_client

    def get_client(self):
        """Get the active SSE client (real or mock based on feature flag)."""
        return self._client

    def is_using_real_sse(self) -> bool:
        """Check if the bridge is using the real SSE client."""
        return is_feature_enabled(FLAG_ENABLE_LIVE_P7_STREAM)

    def simulate_scroll(self, source_panel: str, offset: float) -> None:
        """Simulate a scroll event (for testing)."""
        self._mock_client.simulate_event(WorkspaceEventType.SCROLL_SYNC, {
            "source_panel": source_panel,
            "offset": offset,
        })

    def simulate_highlight(self, clause_id: int, panel: str = "center", action: str = "highlight") -> None:
        """Simulate a highlight event (for testing)."""
        self._mock_client.simulate_event(WorkspaceEventType.HIGHLIGHT_CLAUSE, {
            "clause_id": clause_id,
            "panel": panel,
            "action": action,
        })

    def export_state(self) -> Dict[str, Any]:
        """Export bridge state for debugging."""
        return {
            "connection_state": self._indicator.state.value,
            "events_buffered": len(self._event_buffer.get_recent(1000)),
            "active_highlights": {
                str(k): v.value for k, v in self._highlight_hook.get_active_highlights().items()
            },
            "scroll_events_routed": len(self._scroll_hook.get_event_log()),
            "controller_state": self._controller.export_state(),
            "using_real_sse": self.is_using_real_sse(),
            "session_id": self._session_id,
        }


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "0.2.0"
__phase__ = "Phase 7.S2"
__status__ = "Feature-flagged Real/Mock SSE client selection"
