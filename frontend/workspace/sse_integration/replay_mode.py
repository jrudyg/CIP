"""
Replay Mode Controller
Handles SSE replay mode workspace behavior

During replay:
- Disable SAT (Scroll Authority Token)
- Freeze scroll sync
- Show replay indicator (via CC2)
- Re-enable once REPLAY_END arrives

CC3 P7.CC3.01 - Replay Mode
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from ...integrations.workspace_mode import ScrollAuthorityManager, WorkspaceController
    from .event_bindings import BindingRegistry
    from .flow_dispatcher import WorkspaceSSEDispatcher


# ============================================================================
# REPLAY STATE
# ============================================================================

class ReplayState(str, Enum):
    """Replay mode states."""
    IDLE = "idle"                    # Normal operation
    REPLAY_STARTING = "starting"     # Replay initiated, disabling systems
    REPLAYING = "replaying"          # Actively receiving replay events
    REPLAY_ENDING = "ending"         # Replay complete, re-enabling systems
    ERROR = "error"                  # Replay error occurred


# ============================================================================
# REPLAY PROGRESS
# ============================================================================

@dataclass
class ReplayProgress:
    """Progress information during replay."""
    state: ReplayState = ReplayState.IDLE
    start_sequence: int = 0
    end_sequence: int = 0
    current_sequence: int = 0
    events_replayed: int = 0
    estimated_total: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def get_progress_percent(self) -> float:
        """Get replay progress as percentage."""
        if self.estimated_total <= 0:
            return 0.0
        return min(100.0, (self.events_replayed / self.estimated_total) * 100)

    def is_active(self) -> bool:
        """Check if replay is active."""
        return self.state in [ReplayState.REPLAY_STARTING, ReplayState.REPLAYING]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "start_sequence": self.start_sequence,
            "end_sequence": self.end_sequence,
            "current_sequence": self.current_sequence,
            "events_replayed": self.events_replayed,
            "estimated_total": self.estimated_total,
            "progress_percent": self.get_progress_percent(),
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


# ============================================================================
# REPLAY MODE CONTROLLER
# ============================================================================

class ReplayModeController:
    """
    Controls workspace behavior during SSE replay.

    Responsibilities:
    1. Disable SAT during replay
    2. Freeze scroll sync
    3. Coordinate with CC2 for replay indicator
    4. Re-enable systems on REPLAY_END
    """

    def __init__(
        self,
        sat_manager: "ScrollAuthorityManager",
        dispatcher: Optional["WorkspaceSSEDispatcher"] = None,
        binding_registry: Optional["BindingRegistry"] = None,
    ):
        self._sat_manager = sat_manager
        self._dispatcher = dispatcher
        self._binding_registry = binding_registry

        self._progress = ReplayProgress()
        self._pre_replay_state: Dict[str, Any] = {}

        # Callbacks for UI updates
        self._state_callbacks: List[Callable[[ReplayState], None]] = []
        self._progress_callbacks: List[Callable[[ReplayProgress], None]] = []
        self._indicator_callbacks: List[Callable[[bool, ReplayProgress], None]] = []  # For CC2

    def start_replay(
        self,
        start_sequence: int,
        end_sequence: int,
        estimated_total: Optional[int] = None
    ) -> None:
        """
        Start replay mode.

        Args:
            start_sequence: First sequence number being replayed
            end_sequence: Last sequence number to replay
            estimated_total: Estimated total events (for progress)
        """
        self._progress.state = ReplayState.REPLAY_STARTING
        self._progress.start_sequence = start_sequence
        self._progress.end_sequence = end_sequence
        self._progress.current_sequence = start_sequence
        self._progress.events_replayed = 0
        self._progress.estimated_total = estimated_total or (end_sequence - start_sequence + 1)
        self._progress.start_time = datetime.now().isoformat()
        self._progress.end_time = None

        # Save pre-replay state
        self._save_pre_replay_state()

        # Disable systems
        self._disable_for_replay()

        # Notify callbacks
        self._notify_state_change(ReplayState.REPLAY_STARTING)
        self._progress.state = ReplayState.REPLAYING
        self._notify_state_change(ReplayState.REPLAYING)
        self._notify_indicator(True)

    def record_replay_event(self, sequence: int) -> None:
        """Record a replayed event for progress tracking."""
        if not self._progress.is_active():
            return

        self._progress.current_sequence = sequence
        self._progress.events_replayed += 1
        self._notify_progress()

    def end_replay(self) -> None:
        """
        End replay mode and restore normal operation.
        """
        self._progress.state = ReplayState.REPLAY_ENDING
        self._notify_state_change(ReplayState.REPLAY_ENDING)

        # Re-enable systems
        self._enable_after_replay()

        # Restore pre-replay state if needed
        self._restore_pre_replay_state()

        # Finalize progress
        self._progress.end_time = datetime.now().isoformat()
        self._progress.state = ReplayState.IDLE
        self._notify_state_change(ReplayState.IDLE)
        self._notify_indicator(False)

    def abort_replay(self, error_message: str) -> None:
        """
        Abort replay due to error.

        Args:
            error_message: Description of the error
        """
        self._progress.state = ReplayState.ERROR
        self._progress.end_time = datetime.now().isoformat()

        # Re-enable systems despite error
        self._enable_after_replay()

        self._notify_state_change(ReplayState.ERROR)
        self._notify_indicator(False)

    def _save_pre_replay_state(self) -> None:
        """Save state before replay for potential restoration."""
        self._pre_replay_state = {
            "sat_holder": self._sat_manager.get_current_holder(),
            "timestamp": datetime.now().isoformat(),
        }

    def _restore_pre_replay_state(self) -> None:
        """Restore state after replay if needed."""
        # SAT authority is released during replay, so we don't restore holder
        # Other components may need restoration based on requirements
        self._pre_replay_state.clear()

    def _disable_for_replay(self) -> None:
        """Disable systems for replay mode."""
        # Release SAT authority
        self._sat_manager.release_authority()

        # Put dispatcher in replay mode (skips binding dispatch)
        if self._dispatcher:
            self._dispatcher.set_replay_mode(True)

        # Disable individual bindings
        if self._binding_registry:
            self._binding_registry.disable_all()

    def _enable_after_replay(self) -> None:
        """Re-enable systems after replay."""
        # Dispatcher exits replay mode
        if self._dispatcher:
            self._dispatcher.set_replay_mode(False)

        # Enable bindings
        if self._binding_registry:
            self._binding_registry.enable_all()

        # SAT is ready for new authority requests

    def _notify_state_change(self, state: ReplayState) -> None:
        """Notify state change callbacks."""
        for cb in self._state_callbacks:
            cb(state)

    def _notify_progress(self) -> None:
        """Notify progress callbacks."""
        for cb in self._progress_callbacks:
            cb(self._progress)

    def _notify_indicator(self, show: bool) -> None:
        """Notify indicator callbacks (for CC2 UI)."""
        for cb in self._indicator_callbacks:
            cb(show, self._progress)

    def on_state_change(self, callback: Callable[[ReplayState], None]) -> None:
        """Register callback for state changes."""
        self._state_callbacks.append(callback)

    def on_progress(self, callback: Callable[[ReplayProgress], None]) -> None:
        """Register callback for progress updates."""
        self._progress_callbacks.append(callback)

    def on_indicator(self, callback: Callable[[bool, ReplayProgress], None]) -> None:
        """
        Register callback for replay indicator (CC2 integration).

        Callback receives (show: bool, progress: ReplayProgress)
        """
        self._indicator_callbacks.append(callback)

    def get_state(self) -> ReplayState:
        """Get current replay state."""
        return self._progress.state

    def get_progress(self) -> ReplayProgress:
        """Get current replay progress."""
        return self._progress

    def is_replaying(self) -> bool:
        """Check if currently in replay mode."""
        return self._progress.is_active()


# ============================================================================
# REPLAY INDICATOR DATA (FOR CC2)
# ============================================================================

@dataclass
class ReplayIndicatorData:
    """
    Data structure for CC2 replay indicator component.
    Provides all info needed for visual display.
    """
    visible: bool = False
    state: ReplayState = ReplayState.IDLE
    progress_percent: float = 0.0
    events_replayed: int = 0
    estimated_total: int = 0
    message: str = ""

    @classmethod
    def from_progress(cls, visible: bool, progress: ReplayProgress) -> "ReplayIndicatorData":
        """Create indicator data from replay progress."""
        if progress.state == ReplayState.REPLAYING:
            message = f"Replaying events... {progress.events_replayed}/{progress.estimated_total}"
        elif progress.state == ReplayState.REPLAY_STARTING:
            message = "Starting replay..."
        elif progress.state == ReplayState.REPLAY_ENDING:
            message = "Completing replay..."
        elif progress.state == ReplayState.ERROR:
            message = "Replay error occurred"
        else:
            message = ""

        return cls(
            visible=visible,
            state=progress.state,
            progress_percent=progress.get_progress_percent(),
            events_replayed=progress.events_replayed,
            estimated_total=progress.estimated_total,
            message=message,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "visible": self.visible,
            "state": self.state.value,
            "progress_percent": self.progress_percent,
            "events_replayed": self.events_replayed,
            "estimated_total": self.estimated_total,
            "message": self.message,
        }


# ============================================================================
# REPLAY EVENT HANDLERS
# ============================================================================

class ReplayEventHandler:
    """
    Handles REPLAY_START and REPLAY_END SSE events.
    Bridges SSE events to ReplayModeController.
    """

    def __init__(self, controller: ReplayModeController):
        self._controller = controller

    def handle_replay_start(self, payload: Dict[str, Any]) -> None:
        """
        Handle REPLAY_START event.

        Expected payload:
        {
            "start_sequence": int,
            "end_sequence": int,
            "estimated_total": int (optional),
            "reason": str (optional)
        }
        """
        start_seq = payload.get("start_sequence", 0)
        end_seq = payload.get("end_sequence", 0)
        estimated = payload.get("estimated_total")

        self._controller.start_replay(start_seq, end_seq, estimated)

    def handle_replay_end(self, payload: Dict[str, Any]) -> None:
        """
        Handle REPLAY_END event.

        Expected payload:
        {
            "final_sequence": int,
            "events_sent": int,
            "status": str ("complete" | "partial" | "error")
        }
        """
        status = payload.get("status", "complete")

        if status == "error":
            self._controller.abort_replay(payload.get("error", "Unknown replay error"))
        else:
            self._controller.end_replay()

    def handle_replay_progress(self, sequence: int) -> None:
        """Record progress during replay."""
        self._controller.record_replay_event(sequence)
