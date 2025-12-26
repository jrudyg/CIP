"""
P7 Workspace Failure-Mode Matrix
Defines failure modes and recovery strategies

Failure modes covered:
- missing PANEL_STATE
- sequence gaps
- overbuffer
- highlight orphan
- scroll sync jitter

CC3 P7.CC3.01 - Failure Matrix
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import logging

if TYPE_CHECKING:
    from .event_bindings import HighlightBinding
    from .flow_dispatcher import WorkspaceSSEDispatcher
    from ...integrations.event_buffer_stub import EventBuffer


# ============================================================================
# FAILURE MODES
# ============================================================================

class FailureMode(str, Enum):
    """Workspace SSE failure modes."""
    MISSING_PANEL_STATE = "missing_panel_state"
    SEQUENCE_GAP = "sequence_gap"
    OVERBUFFER = "overbuffer"
    HIGHLIGHT_ORPHAN = "highlight_orphan"
    SCROLL_SYNC_JITTER = "scroll_sync_jitter"
    CONNECTION_TIMEOUT = "connection_timeout"
    INVALID_PAYLOAD = "invalid_payload"
    BINDING_ERROR = "binding_error"


class FailureSeverity(str, Enum):
    """Severity levels for failures."""
    LOW = "low"           # Cosmetic, auto-recoverable
    MEDIUM = "medium"     # Functional impact, needs attention
    HIGH = "high"         # Critical, requires immediate action
    CRITICAL = "critical" # System unstable, user intervention needed


class RecoveryStrategy(str, Enum):
    """Recovery strategies for failures."""
    IGNORE = "ignore"               # No action needed
    RETRY = "retry"                 # Retry the operation
    REQUEST_REPLAY = "request_replay"  # Request missing events
    CLEAR_STATE = "clear_state"     # Clear affected state
    RECONNECT = "reconnect"         # Reconnect to SSE
    FALLBACK = "fallback"           # Use fallback behavior
    USER_NOTIFY = "user_notify"     # Notify user of issue


# ============================================================================
# FAILURE DEFINITION
# ============================================================================

@dataclass
class FailureDefinition:
    """Definition of a failure mode with recovery strategy."""
    mode: FailureMode
    severity: FailureSeverity
    description: str
    detection_method: str
    recovery_strategy: RecoveryStrategy
    recovery_steps: List[str]
    max_retries: int = 3
    retry_delay_ms: int = 1000
    user_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "severity": self.severity.value,
            "description": self.description,
            "detection_method": self.detection_method,
            "recovery_strategy": self.recovery_strategy.value,
            "recovery_steps": self.recovery_steps,
            "max_retries": self.max_retries,
            "retry_delay_ms": self.retry_delay_ms,
            "user_message": self.user_message,
        }


# ============================================================================
# FAILURE INSTANCE
# ============================================================================

@dataclass
class FailureInstance:
    """Instance of a detected failure."""
    failure_id: str
    mode: FailureMode
    severity: FailureSeverity
    detected_at: str = ""
    resolved_at: Optional[str] = None
    retry_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    resolution_method: Optional[str] = None

    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()

    def mark_resolved(self, method: str) -> None:
        """Mark failure as resolved."""
        self.resolved_at = datetime.now().isoformat()
        self.recovery_successful = True
        self.resolution_method = method

    def is_resolved(self) -> bool:
        """Check if failure is resolved."""
        return self.resolved_at is not None

    def increment_retry(self) -> int:
        """Increment retry count and return new count."""
        self.retry_count += 1
        self.recovery_attempted = True
        return self.retry_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "mode": self.mode.value,
            "severity": self.severity.value,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "retry_count": self.retry_count,
            "context": self.context,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "resolution_method": self.resolution_method,
        }


# ============================================================================
# FAILURE MODE HANDLER
# ============================================================================

class FailureModeHandler:
    """
    Handler for a specific failure mode.
    Implements detection and recovery logic.
    """

    def __init__(self, definition: FailureDefinition):
        self._definition = definition
        self._instances: List[FailureInstance] = []
        self._recovery_callbacks: List[Callable[[FailureInstance], None]] = []
        self._logger = logging.getLogger(f"FailureHandler.{definition.mode.value}")

    @property
    def mode(self) -> FailureMode:
        return self._definition.mode

    @property
    def definition(self) -> FailureDefinition:
        return self._definition

    def detect(self, context: Dict[str, Any]) -> Optional[FailureInstance]:
        """
        Detect if this failure mode has occurred.
        Override in subclasses for specific detection logic.

        Args:
            context: Context data for detection

        Returns:
            FailureInstance if detected, None otherwise
        """
        # Base implementation - override in subclasses
        return None

    def recover(self, instance: FailureInstance) -> bool:
        """
        Attempt recovery from failure.

        Args:
            instance: The failure instance to recover from

        Returns:
            True if recovery successful
        """
        if instance.retry_count >= self._definition.max_retries:
            self._logger.warning(f"Max retries exceeded for {self.mode.value}")
            return False

        instance.increment_retry()

        # Execute recovery based on strategy
        strategy = self._definition.recovery_strategy
        success = False

        if strategy == RecoveryStrategy.IGNORE:
            success = True
        elif strategy == RecoveryStrategy.RETRY:
            success = self._execute_retry(instance)
        elif strategy == RecoveryStrategy.REQUEST_REPLAY:
            success = self._request_replay(instance)
        elif strategy == RecoveryStrategy.CLEAR_STATE:
            success = self._clear_state(instance)
        elif strategy == RecoveryStrategy.RECONNECT:
            success = self._reconnect(instance)
        elif strategy == RecoveryStrategy.FALLBACK:
            success = self._use_fallback(instance)
        elif strategy == RecoveryStrategy.USER_NOTIFY:
            success = self._notify_user(instance)

        if success:
            instance.mark_resolved(strategy.value)
            for cb in self._recovery_callbacks:
                cb(instance)

        return success

    def _execute_retry(self, instance: FailureInstance) -> bool:
        """Execute retry recovery."""
        self._logger.info(f"Retrying for {self.mode.value}, attempt {instance.retry_count}")
        return True  # Override in subclasses

    def _request_replay(self, instance: FailureInstance) -> bool:
        """Request replay recovery."""
        self._logger.info(f"Requesting replay for {self.mode.value}")
        return True  # Override in subclasses

    def _clear_state(self, instance: FailureInstance) -> bool:
        """Clear state recovery."""
        self._logger.info(f"Clearing state for {self.mode.value}")
        return True  # Override in subclasses

    def _reconnect(self, instance: FailureInstance) -> bool:
        """Reconnect recovery."""
        self._logger.info(f"Reconnecting for {self.mode.value}")
        return True  # Override in subclasses

    def _use_fallback(self, instance: FailureInstance) -> bool:
        """Use fallback behavior."""
        self._logger.info(f"Using fallback for {self.mode.value}")
        return True  # Override in subclasses

    def _notify_user(self, instance: FailureInstance) -> bool:
        """Notify user of failure."""
        self._logger.info(f"Notifying user for {self.mode.value}")
        return True  # Override in subclasses

    def register_instance(self, instance: FailureInstance) -> None:
        """Register a detected failure instance."""
        self._instances.append(instance)

    def get_active_instances(self) -> List[FailureInstance]:
        """Get unresolved failure instances."""
        return [i for i in self._instances if not i.is_resolved()]

    def get_all_instances(self) -> List[FailureInstance]:
        """Get all failure instances."""
        return self._instances.copy()

    def on_recovery(self, callback: Callable[[FailureInstance], None]) -> None:
        """Register recovery callback."""
        self._recovery_callbacks.append(callback)


# ============================================================================
# WORKSPACE FAILURE MATRIX
# ============================================================================

class WorkspaceFailureMatrix:
    """
    Complete failure matrix for workspace SSE integration.
    Defines all failure modes, detection, and recovery.
    """

    # Static failure definitions
    DEFINITIONS: Dict[FailureMode, FailureDefinition] = {
        FailureMode.MISSING_PANEL_STATE: FailureDefinition(
            mode=FailureMode.MISSING_PANEL_STATE,
            severity=FailureSeverity.MEDIUM,
            description="PANEL_STATE event not received within expected timeframe",
            detection_method="Timeout after connection, no initial state received",
            recovery_strategy=RecoveryStrategy.REQUEST_REPLAY,
            recovery_steps=[
                "Wait for timeout threshold (5s)",
                "Request state replay from server",
                "Apply default panel layout if replay fails",
            ],
            max_retries=2,
            retry_delay_ms=2000,
            user_message="Loading panel layout...",
        ),
        FailureMode.SEQUENCE_GAP: FailureDefinition(
            mode=FailureMode.SEQUENCE_GAP,
            severity=FailureSeverity.HIGH,
            description="Gap detected in event sequence numbers",
            detection_method="SequenceValidator detects non-consecutive sequence",
            recovery_strategy=RecoveryStrategy.REQUEST_REPLAY,
            recovery_steps=[
                "Record gap range (start, end)",
                "Request replay for missing sequences",
                "Enter replay mode during catch-up",
                "Resume normal operation after replay",
            ],
            max_retries=3,
            retry_delay_ms=1000,
            user_message="Synchronizing events...",
        ),
        FailureMode.OVERBUFFER: FailureDefinition(
            mode=FailureMode.OVERBUFFER,
            severity=FailureSeverity.LOW,
            description="Event buffer exceeded maximum size",
            detection_method="Buffer size exceeds configured maximum",
            recovery_strategy=RecoveryStrategy.CLEAR_STATE,
            recovery_steps=[
                "Trim oldest events from buffer",
                "Log warning for monitoring",
                "Continue normal operation",
            ],
            max_retries=1,
            retry_delay_ms=0,
        ),
        FailureMode.HIGHLIGHT_ORPHAN: FailureDefinition(
            mode=FailureMode.HIGHLIGHT_ORPHAN,
            severity=FailureSeverity.LOW,
            description="Highlight references clause_id that doesn't exist",
            detection_method="HighlightBinding receives invalid clause_id",
            recovery_strategy=RecoveryStrategy.IGNORE,
            recovery_steps=[
                "Log orphan highlight",
                "Skip application to UI",
                "Queue for potential future clause load",
            ],
            max_retries=0,
            retry_delay_ms=0,
        ),
        FailureMode.SCROLL_SYNC_JITTER: FailureDefinition(
            mode=FailureMode.SCROLL_SYNC_JITTER,
            severity=FailureSeverity.LOW,
            description="Rapid successive scroll events causing jitter",
            detection_method="Scroll events within jitter threshold (<50ms)",
            recovery_strategy=RecoveryStrategy.IGNORE,
            recovery_steps=[
                "Skip intermediate scroll events",
                "Apply only latest scroll position",
                "Debounce subsequent events",
            ],
            max_retries=0,
            retry_delay_ms=0,
        ),
        FailureMode.CONNECTION_TIMEOUT: FailureDefinition(
            mode=FailureMode.CONNECTION_TIMEOUT,
            severity=FailureSeverity.HIGH,
            description="SSE connection timed out or lost",
            detection_method="No heartbeat received within timeout period",
            recovery_strategy=RecoveryStrategy.RECONNECT,
            recovery_steps=[
                "Mark connection as lost",
                "Show reconnecting indicator",
                "Attempt reconnection with backoff",
                "Request state replay after reconnect",
            ],
            max_retries=5,
            retry_delay_ms=2000,
            user_message="Connection lost. Reconnecting...",
        ),
        FailureMode.INVALID_PAYLOAD: FailureDefinition(
            mode=FailureMode.INVALID_PAYLOAD,
            severity=FailureSeverity.MEDIUM,
            description="Event payload failed validation",
            detection_method="Schema validation or required field check failed",
            recovery_strategy=RecoveryStrategy.IGNORE,
            recovery_steps=[
                "Log invalid payload for debugging",
                "Skip event processing",
                "Continue with next event",
            ],
            max_retries=0,
            retry_delay_ms=0,
        ),
        FailureMode.BINDING_ERROR: FailureDefinition(
            mode=FailureMode.BINDING_ERROR,
            severity=FailureSeverity.MEDIUM,
            description="Event binding threw an exception",
            detection_method="Exception caught during bind() execution",
            recovery_strategy=RecoveryStrategy.FALLBACK,
            recovery_steps=[
                "Log exception details",
                "Apply fallback behavior per binding",
                "Notify monitoring system",
            ],
            max_retries=1,
            retry_delay_ms=500,
        ),
    }

    def __init__(self):
        self._handlers: Dict[FailureMode, FailureModeHandler] = {}
        self._failure_callbacks: List[Callable[[FailureInstance], None]] = []
        self._recovery_callbacks: List[Callable[[FailureInstance], None]] = []
        self._failure_counter = 0
        self._logger = logging.getLogger("WorkspaceFailureMatrix")

        # Initialize handlers
        self._initialize_handlers()

    def _initialize_handlers(self) -> None:
        """Initialize handlers for all failure modes."""
        for mode, definition in self.DEFINITIONS.items():
            self._handlers[mode] = FailureModeHandler(definition)
            self._handlers[mode].on_recovery(self._on_handler_recovery)

    def _on_handler_recovery(self, instance: FailureInstance) -> None:
        """Handle recovery from a handler."""
        for cb in self._recovery_callbacks:
            cb(instance)

    def report_failure(
        self,
        mode: FailureMode,
        context: Optional[Dict[str, Any]] = None
    ) -> FailureInstance:
        """
        Report a detected failure.

        Args:
            mode: The failure mode detected
            context: Additional context data

        Returns:
            Created FailureInstance
        """
        self._failure_counter += 1
        instance = FailureInstance(
            failure_id=f"fail-{self._failure_counter}",
            mode=mode,
            severity=self.DEFINITIONS[mode].severity,
            context=context or {},
        )

        handler = self._handlers.get(mode)
        if handler:
            handler.register_instance(instance)

        # Notify callbacks
        for cb in self._failure_callbacks:
            cb(instance)

        self._logger.warning(f"Failure reported: {mode.value}")
        return instance

    def attempt_recovery(self, instance: FailureInstance) -> bool:
        """
        Attempt recovery for a failure instance.

        Args:
            instance: The failure to recover from

        Returns:
            True if recovery successful
        """
        handler = self._handlers.get(instance.mode)
        if handler:
            return handler.recover(instance)
        return False

    def get_handler(self, mode: FailureMode) -> Optional[FailureModeHandler]:
        """Get handler for a failure mode."""
        return self._handlers.get(mode)

    def get_definition(self, mode: FailureMode) -> Optional[FailureDefinition]:
        """Get definition for a failure mode."""
        return self.DEFINITIONS.get(mode)

    def get_active_failures(self) -> List[FailureInstance]:
        """Get all unresolved failures across all handlers."""
        active = []
        for handler in self._handlers.values():
            active.extend(handler.get_active_instances())
        return active

    def get_failure_stats(self) -> Dict[str, Any]:
        """Get failure statistics."""
        total = 0
        resolved = 0
        by_mode: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}

        for handler in self._handlers.values():
            instances = handler.get_all_instances()
            total += len(instances)
            resolved += len([i for i in instances if i.is_resolved()])

            mode_name = handler.mode.value
            by_mode[mode_name] = len(instances)

            for inst in instances:
                sev = inst.severity.value
                by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total_failures": total,
            "resolved_failures": resolved,
            "active_failures": total - resolved,
            "by_mode": by_mode,
            "by_severity": by_severity,
        }

    def on_failure(self, callback: Callable[[FailureInstance], None]) -> None:
        """Register callback for failure detection."""
        self._failure_callbacks.append(callback)

    def on_recovery(self, callback: Callable[[FailureInstance], None]) -> None:
        """Register callback for successful recovery."""
        self._recovery_callbacks.append(callback)

    def export_matrix(self) -> List[Dict[str, Any]]:
        """Export the complete failure matrix."""
        return [defn.to_dict() for defn in self.DEFINITIONS.values()]
