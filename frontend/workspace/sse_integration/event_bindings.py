"""
SSE Event Bindings
Real SSE → Workspace Controller Binding Implementation

Binds SSE events to workspace components:
- PANEL_STATE → PanelLayoutController
- SCROLL_SYNC → SAT System
- HIGHLIGHT → HighlightOverlay
- INTELLIGENCE_UPDATE → IntelligenceRenderer

CC3 P7.CC3.01 - Event Bindings
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import logging

if TYPE_CHECKING:
    from ...integrations.workspace_mode import (
        WorkspaceController,
        WorkspaceState,
        PanelPosition,
        ScrollSyncMode,
        ScrollAuthorityManager,
    )
    from ...integrations.event_buffer_stub import EventEnvelope


# ============================================================================
# SSE EVENT TYPES
# ============================================================================

class SSEEventType(str, Enum):
    """SSE event types for workspace integration."""
    PANEL_STATE = "panel_state"
    SCROLL_SYNC = "scroll_sync"
    HIGHLIGHT = "highlight"
    INTELLIGENCE_UPDATE = "intelligence_update"
    REPLAY_START = "replay_start"
    REPLAY_END = "replay_end"
    ENGINE_STATUS = "engine_status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


# ============================================================================
# BINDING RESULT
# ============================================================================

@dataclass
class BindingResult:
    """Result of an SSE event binding operation."""
    success: bool
    event_type: SSEEventType
    target_component: str
    timestamp: str = ""
    error_message: Optional[str] = None
    data_applied: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "event_type": self.event_type.value,
            "target_component": self.target_component,
            "timestamp": self.timestamp,
            "error_message": self.error_message,
            "data_applied": self.data_applied,
        }


# ============================================================================
# ABSTRACT BINDING BASE
# ============================================================================

class SSEEventBinding(ABC):
    """
    Abstract base class for SSE event bindings.
    Each binding connects an SSE event type to a workspace component.
    """

    def __init__(self):
        self._enabled = True
        self._binding_log: List[BindingResult] = []
        self._error_callbacks: List[Callable[[BindingResult], None]] = []
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def event_type(self) -> SSEEventType:
        """The SSE event type this binding handles."""
        pass

    @property
    @abstractmethod
    def target_component(self) -> str:
        """The target UI component name."""
        pass

    @abstractmethod
    def bind(self, event: "EventEnvelope") -> BindingResult:
        """
        Bind the SSE event to the target component.

        Args:
            event: The SSE event envelope

        Returns:
            BindingResult indicating success/failure
        """
        pass

    def enable(self) -> None:
        """Enable this binding."""
        self._enabled = True

    def disable(self) -> None:
        """Disable this binding (for replay mode)."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if binding is enabled."""
        return self._enabled

    def on_error(self, callback: Callable[[BindingResult], None]) -> None:
        """Register error callback."""
        self._error_callbacks.append(callback)

    def _log_result(self, result: BindingResult) -> None:
        """Log binding result and notify error callbacks if failed."""
        self._binding_log.append(result)
        if not result.success:
            for cb in self._error_callbacks:
                cb(result)

    def get_binding_log(self, limit: int = 100) -> List[BindingResult]:
        """Get recent binding results."""
        return self._binding_log[-limit:]


# ============================================================================
# PANEL STATE BINDING
# ============================================================================

@dataclass
class PanelLayoutState:
    """Panel layout state from SSE."""
    left_width: float
    center_width: float
    right_width: float
    left_visible: bool = True
    center_visible: bool = True
    right_visible: bool = True


class PanelStateBinding(SSEEventBinding):
    """
    Binds PANEL_STATE events to PanelLayoutController.
    Updates panel widths and visibility from server state.
    """

    def __init__(self, workspace_controller: "WorkspaceController"):
        super().__init__()
        self._controller = workspace_controller
        self._last_state: Optional[PanelLayoutState] = None
        self._state_callbacks: List[Callable[[PanelLayoutState], None]] = []

    @property
    def event_type(self) -> SSEEventType:
        return SSEEventType.PANEL_STATE

    @property
    def target_component(self) -> str:
        return "PanelLayoutController"

    def bind(self, event: "EventEnvelope") -> BindingResult:
        """Bind PANEL_STATE event to workspace controller."""
        if not self._enabled:
            return BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message="Binding disabled (replay mode)",
            )

        try:
            payload = event.payload

            # Extract panel state
            panel_state = PanelLayoutState(
                left_width=payload.get("left_width", 35.0),
                center_width=payload.get("center_width", 30.0),
                right_width=payload.get("right_width", 35.0),
                left_visible=payload.get("left_visible", True),
                center_visible=payload.get("center_visible", True),
                right_visible=payload.get("right_visible", True),
            )

            # Apply to workspace controller
            state = self._controller.get_state()
            state.set_panel_widths(
                panel_state.left_width,
                panel_state.center_width,
                panel_state.right_width
            )
            state.left_panel_visible = panel_state.left_visible
            state.center_panel_visible = panel_state.center_visible
            state.right_panel_visible = panel_state.right_visible

            self._last_state = panel_state

            # Notify callbacks
            for cb in self._state_callbacks:
                cb(panel_state)

            result = BindingResult(
                success=True,
                event_type=self.event_type,
                target_component=self.target_component,
                data_applied={
                    "widths": [panel_state.left_width, panel_state.center_width, panel_state.right_width],
                    "visibility": [panel_state.left_visible, panel_state.center_visible, panel_state.right_visible],
                },
            )
            self._log_result(result)
            return result

        except Exception as e:
            result = BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message=str(e),
            )
            self._log_result(result)
            return result

    def on_state_update(self, callback: Callable[[PanelLayoutState], None]) -> None:
        """Register callback for panel state updates."""
        self._state_callbacks.append(callback)

    def get_last_state(self) -> Optional[PanelLayoutState]:
        """Get the last applied panel state."""
        return self._last_state


# ============================================================================
# SCROLL SYNC BINDING
# ============================================================================

@dataclass
class ScrollSyncCommand:
    """Scroll sync command from SSE."""
    source_panel: str
    target_panels: List[str]
    offset: float
    sync_mode: str
    authority_token_id: Optional[str] = None


class ScrollSyncBinding(SSEEventBinding):
    """
    Binds SCROLL_SYNC events to SAT (Scroll Authority Token) system.
    Handles server-initiated scroll synchronization.
    """

    def __init__(
        self,
        workspace_controller: "WorkspaceController",
        sat_manager: "ScrollAuthorityManager"
    ):
        super().__init__()
        self._controller = workspace_controller
        self._sat_manager = sat_manager
        self._server_authority = False
        self._sync_callbacks: List[Callable[[ScrollSyncCommand], None]] = []
        self._jitter_threshold_ms = 50  # Ignore rapid successive events

        self._last_sync_time: Optional[datetime] = None

    @property
    def event_type(self) -> SSEEventType:
        return SSEEventType.SCROLL_SYNC

    @property
    def target_component(self) -> str:
        return "SAT_ScrollSync"

    def bind(self, event: "EventEnvelope") -> BindingResult:
        """Bind SCROLL_SYNC event to SAT system."""
        if not self._enabled:
            return BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message="Binding disabled (replay mode)",
            )

        try:
            # Jitter protection
            now = datetime.now()
            if self._last_sync_time:
                delta_ms = (now - self._last_sync_time).total_seconds() * 1000
                if delta_ms < self._jitter_threshold_ms:
                    return BindingResult(
                        success=True,
                        event_type=self.event_type,
                        target_component=self.target_component,
                        data_applied={"skipped": "jitter_protection"},
                    )
            self._last_sync_time = now

            payload = event.payload

            # Extract scroll command
            command = ScrollSyncCommand(
                source_panel=payload.get("source_panel", "center"),
                target_panels=payload.get("target_panels", ["left", "right"]),
                offset=payload.get("offset", 0.0),
                sync_mode=payload.get("sync_mode", "locked"),
                authority_token_id=payload.get("authority_token_id"),
            )

            # Server-initiated scroll takes authority
            # Import locally to avoid circular imports
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from integrations.workspace_mode import PanelPosition
            source = PanelPosition(command.source_panel)

            # Request authority for server-initiated scroll
            self._server_authority = True
            token = self._sat_manager.request_authority(source)

            if token:
                # Apply scroll through controller
                results = self._controller.handle_scroll(source, command.offset)

                # Notify callbacks
                for cb in self._sync_callbacks:
                    cb(command)

                result = BindingResult(
                    success=True,
                    event_type=self.event_type,
                    target_component=self.target_component,
                    data_applied={
                        "source": command.source_panel,
                        "offset": command.offset,
                        "token_id": token.token_id,
                        "panels_updated": list(results.keys()),
                    },
                )
            else:
                result = BindingResult(
                    success=False,
                    event_type=self.event_type,
                    target_component=self.target_component,
                    error_message="Failed to acquire scroll authority",
                )

            self._server_authority = False
            self._log_result(result)
            return result

        except Exception as e:
            self._server_authority = False
            result = BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message=str(e),
            )
            self._log_result(result)
            return result

    def on_sync(self, callback: Callable[[ScrollSyncCommand], None]) -> None:
        """Register callback for scroll sync events."""
        self._sync_callbacks.append(callback)

    def is_server_authority(self) -> bool:
        """Check if server currently has scroll authority."""
        return self._server_authority

    def set_jitter_threshold(self, ms: int) -> None:
        """Set jitter protection threshold in milliseconds."""
        self._jitter_threshold_ms = ms


# ============================================================================
# HIGHLIGHT BINDING
# ============================================================================

@dataclass
class HighlightCommand:
    """Highlight command from SSE."""
    clause_id: int
    panel: str
    action: str  # "add", "remove", "clear_all", "focus"
    style: str = "default"  # "default", "risk", "match", "diff"
    scroll_to: bool = False
    duration_ms: Optional[int] = None  # Auto-clear after duration


class HighlightBinding(SSEEventBinding):
    """
    Binds HIGHLIGHT events to HighlightOverlay component.
    Manages clause highlighting across panels.
    """

    def __init__(self):
        super().__init__()
        self._active_highlights: Dict[int, HighlightCommand] = {}
        self._highlight_callbacks: List[Callable[[HighlightCommand], None]] = []
        self._clear_callbacks: List[Callable[[], None]] = []

    @property
    def event_type(self) -> SSEEventType:
        return SSEEventType.HIGHLIGHT

    @property
    def target_component(self) -> str:
        return "HighlightOverlay"

    def bind(self, event: "EventEnvelope") -> BindingResult:
        """Bind HIGHLIGHT event to overlay component."""
        if not self._enabled:
            return BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message="Binding disabled (replay mode)",
            )

        try:
            payload = event.payload

            command = HighlightCommand(
                clause_id=payload.get("clause_id", -1),
                panel=payload.get("panel", "center"),
                action=payload.get("action", "add"),
                style=payload.get("style", "default"),
                scroll_to=payload.get("scroll_to", False),
                duration_ms=payload.get("duration_ms"),
            )

            # Handle different actions
            if command.action == "add":
                self._active_highlights[command.clause_id] = command
            elif command.action == "remove":
                self._active_highlights.pop(command.clause_id, None)
            elif command.action == "clear_all":
                self._active_highlights.clear()
                for cb in self._clear_callbacks:
                    cb()
            elif command.action == "focus":
                # Focus implies add + scroll
                command.scroll_to = True
                self._active_highlights[command.clause_id] = command

            # Notify callbacks
            for cb in self._highlight_callbacks:
                cb(command)

            result = BindingResult(
                success=True,
                event_type=self.event_type,
                target_component=self.target_component,
                data_applied={
                    "clause_id": command.clause_id,
                    "action": command.action,
                    "active_count": len(self._active_highlights),
                },
            )
            self._log_result(result)
            return result

        except Exception as e:
            result = BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message=str(e),
            )
            self._log_result(result)
            return result

    def on_highlight(self, callback: Callable[[HighlightCommand], None]) -> None:
        """Register callback for highlight commands."""
        self._highlight_callbacks.append(callback)

    def on_clear_all(self, callback: Callable[[], None]) -> None:
        """Register callback for clear all action."""
        self._clear_callbacks.append(callback)

    def get_active_highlights(self) -> Dict[int, HighlightCommand]:
        """Get currently active highlights."""
        return self._active_highlights.copy()

    def has_orphan_highlight(self, valid_clause_ids: List[int]) -> List[int]:
        """Check for orphan highlights (clause_id not in valid list)."""
        return [cid for cid in self._active_highlights if cid not in valid_clause_ids]


# ============================================================================
# INTELLIGENCE UPDATE BINDING
# ============================================================================

@dataclass
class IntelligenceUpdate:
    """Intelligence update from SSE."""
    clause_id: int
    engine: str  # "SAE", "ERCE", "BIRL", "FAR"
    data: Dict[str, Any]
    is_partial: bool = False
    is_final: bool = True


class IntelligenceUpdateBinding(SSEEventBinding):
    """
    Binds INTELLIGENCE_UPDATE events to IntelligenceRenderer.
    Routes engine-specific updates to appropriate UI components.
    """

    def __init__(self):
        super().__init__()
        self._engine_data: Dict[str, Dict[int, IntelligenceUpdate]] = {
            "SAE": {},
            "ERCE": {},
            "BIRL": {},
            "FAR": {},
        }
        self._update_callbacks: Dict[str, List[Callable[[IntelligenceUpdate], None]]] = {
            "SAE": [],
            "ERCE": [],
            "BIRL": [],
            "FAR": [],
            "*": [],  # All engines
        }

    @property
    def event_type(self) -> SSEEventType:
        return SSEEventType.INTELLIGENCE_UPDATE

    @property
    def target_component(self) -> str:
        return "IntelligenceRenderer"

    def bind(self, event: "EventEnvelope") -> BindingResult:
        """Bind INTELLIGENCE_UPDATE event to renderer."""
        if not self._enabled:
            return BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message="Binding disabled (replay mode)",
            )

        try:
            payload = event.payload

            update = IntelligenceUpdate(
                clause_id=payload.get("clause_id", -1),
                engine=payload.get("engine", "SAE"),
                data=payload.get("data", {}),
                is_partial=payload.get("is_partial", False),
                is_final=payload.get("is_final", True),
            )

            # Validate engine
            if update.engine not in self._engine_data:
                return BindingResult(
                    success=False,
                    event_type=self.event_type,
                    target_component=self.target_component,
                    error_message=f"Unknown engine: {update.engine}",
                )

            # Store update
            if update.is_partial:
                # Merge partial updates
                existing = self._engine_data[update.engine].get(update.clause_id)
                if existing:
                    existing.data.update(update.data)
                else:
                    self._engine_data[update.engine][update.clause_id] = update
            else:
                self._engine_data[update.engine][update.clause_id] = update

            # Notify callbacks
            for cb in self._update_callbacks.get(update.engine, []):
                cb(update)
            for cb in self._update_callbacks.get("*", []):
                cb(update)

            result = BindingResult(
                success=True,
                event_type=self.event_type,
                target_component=self.target_component,
                data_applied={
                    "clause_id": update.clause_id,
                    "engine": update.engine,
                    "is_partial": update.is_partial,
                    "is_final": update.is_final,
                },
            )
            self._log_result(result)
            return result

        except Exception as e:
            result = BindingResult(
                success=False,
                event_type=self.event_type,
                target_component=self.target_component,
                error_message=str(e),
            )
            self._log_result(result)
            return result

    def on_update(self, engine: str, callback: Callable[[IntelligenceUpdate], None]) -> None:
        """
        Register callback for intelligence updates.

        Args:
            engine: Engine name or "*" for all engines
            callback: Callback function
        """
        if engine not in self._update_callbacks:
            self._update_callbacks[engine] = []
        self._update_callbacks[engine].append(callback)

    def get_engine_data(self, engine: str) -> Dict[int, IntelligenceUpdate]:
        """Get all stored data for an engine."""
        return self._engine_data.get(engine, {}).copy()

    def get_clause_data(self, clause_id: int) -> Dict[str, IntelligenceUpdate]:
        """Get all engine data for a specific clause."""
        result = {}
        for engine, data in self._engine_data.items():
            if clause_id in data:
                result[engine] = data[clause_id]
        return result

    def clear_engine_data(self, engine: Optional[str] = None) -> None:
        """Clear stored engine data."""
        if engine:
            if engine in self._engine_data:
                self._engine_data[engine].clear()
        else:
            for eng in self._engine_data:
                self._engine_data[eng].clear()


# ============================================================================
# BINDING REGISTRY
# ============================================================================

class BindingRegistry:
    """Registry for all SSE event bindings."""

    def __init__(self):
        self._bindings: Dict[SSEEventType, SSEEventBinding] = {}

    def register(self, binding: SSEEventBinding) -> None:
        """Register a binding."""
        self._bindings[binding.event_type] = binding

    def get(self, event_type: SSEEventType) -> Optional[SSEEventBinding]:
        """Get binding for event type."""
        return self._bindings.get(event_type)

    def get_all(self) -> Dict[SSEEventType, SSEEventBinding]:
        """Get all registered bindings."""
        return self._bindings.copy()

    def disable_all(self) -> None:
        """Disable all bindings (for replay mode)."""
        for binding in self._bindings.values():
            binding.disable()

    def enable_all(self) -> None:
        """Enable all bindings."""
        for binding in self._bindings.values():
            binding.enable()

    def bind_event(self, event: "EventEnvelope") -> Optional[BindingResult]:
        """
        Route event to appropriate binding.

        Args:
            event: SSE event envelope

        Returns:
            BindingResult or None if no binding found
        """
        try:
            event_type = SSEEventType(event.event_type)
        except ValueError:
            return None

        binding = self._bindings.get(event_type)
        if binding:
            return binding.bind(event)
        return None
