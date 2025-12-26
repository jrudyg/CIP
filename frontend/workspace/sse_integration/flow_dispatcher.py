"""
Workspace SSE Flow Dispatcher
Ingress → Buffer → Validator → Dispatcher → UI Component

Defines the complete SSE flow map for workspace events.

CC3 P7.CC3.01 - Flow Dispatcher
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import logging

if TYPE_CHECKING:
    from ...integrations.event_buffer_stub import EventBuffer, EventEnvelope, SequenceValidator
    from .event_bindings import BindingRegistry, BindingResult, SSEEventType


# ============================================================================
# FLOW STAGES
# ============================================================================

class SSEFlowStage(str, Enum):
    """Stages in the SSE event flow pipeline."""
    INGRESS = "ingress"           # Raw SSE data received
    BUFFER = "buffer"             # Event buffered
    VALIDATE = "validate"         # Sequence validated
    DISPATCH = "dispatch"         # Routed to binding
    COMPONENT = "component"       # Applied to UI component
    COMPLETE = "complete"         # Flow completed
    ERROR = "error"               # Error occurred


# ============================================================================
# FLOW MAP ENTRY
# ============================================================================

@dataclass
class FlowMapEntry:
    """
    Flow map entry defining the path for an event type.
    Documents: Ingress → Buffer → Validator → Dispatcher → UI Component
    """
    event_type: str
    ingress_handler: str
    buffer_strategy: str
    validation_rules: List[str]
    dispatcher_target: str
    ui_component: str
    fallback_behavior: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "ingress_handler": self.ingress_handler,
            "buffer_strategy": self.buffer_strategy,
            "validation_rules": self.validation_rules,
            "dispatcher_target": self.dispatcher_target,
            "ui_component": self.ui_component,
            "fallback_behavior": self.fallback_behavior,
            "notes": self.notes,
        }


# ============================================================================
# FLOW TRACE
# ============================================================================

@dataclass
class FlowTrace:
    """Trace of an event through the flow pipeline."""
    event_id: str
    event_type: str
    stages: List[Dict[str, Any]] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    success: bool = True
    error_stage: Optional[SSEFlowStage] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()

    def add_stage(self, stage: SSEFlowStage, data: Optional[Dict[str, Any]] = None) -> None:
        """Record passing through a stage."""
        self.stages.append({
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        })

    def mark_error(self, stage: SSEFlowStage, message: str) -> None:
        """Mark an error at a stage."""
        self.success = False
        self.error_stage = stage
        self.error_message = message
        self.add_stage(SSEFlowStage.ERROR, {"message": message})

    def complete(self) -> None:
        """Mark flow as complete."""
        self.end_time = datetime.now().isoformat()
        if self.success:
            self.add_stage(SSEFlowStage.COMPLETE)

    def get_duration_ms(self) -> float:
        """Get flow duration in milliseconds."""
        if not self.end_time:
            return 0.0
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return (end - start).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "stages": self.stages,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.get_duration_ms(),
            "success": self.success,
            "error_stage": self.error_stage.value if self.error_stage else None,
            "error_message": self.error_message,
        }


# ============================================================================
# WORKSPACE SSE FLOW MAP
# ============================================================================

class WorkspaceSSEFlowMap:
    """
    Static flow map defining all event type paths.
    Documents the complete pipeline for each event type.
    """

    FLOW_MAP: Dict[str, FlowMapEntry] = {
        "panel_state": FlowMapEntry(
            event_type="panel_state",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="replace_latest",
            validation_rules=["sequence_check", "schema_validate"],
            dispatcher_target="PanelStateBinding",
            ui_component="PanelLayoutController",
            fallback_behavior="retain_current_state",
            notes="Panel state updates replace previous state",
        ),
        "scroll_sync": FlowMapEntry(
            event_type="scroll_sync",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="append_with_jitter_filter",
            validation_rules=["sequence_check", "sat_authority_check"],
            dispatcher_target="ScrollSyncBinding",
            ui_component="SAT_ScrollSync",
            fallback_behavior="ignore_if_local_authority",
            notes="Jitter filter prevents rapid successive events",
        ),
        "highlight": FlowMapEntry(
            event_type="highlight",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="append",
            validation_rules=["sequence_check", "clause_id_validate"],
            dispatcher_target="HighlightBinding",
            ui_component="HighlightOverlay",
            fallback_behavior="queue_for_retry",
            notes="Highlights persist until explicitly removed",
        ),
        "intelligence_update": FlowMapEntry(
            event_type="intelligence_update",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="append_merge_partial",
            validation_rules=["sequence_check", "engine_validate", "clause_id_validate"],
            dispatcher_target="IntelligenceUpdateBinding",
            ui_component="IntelligenceRenderer",
            fallback_behavior="store_pending",
            notes="Partial updates merge with existing data",
        ),
        "replay_start": FlowMapEntry(
            event_type="replay_start",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="immediate",
            validation_rules=["sequence_check"],
            dispatcher_target="ReplayModeController",
            ui_component="WorkspaceRoot",
            fallback_behavior="force_replay_mode",
            notes="Disables live bindings during replay",
        ),
        "replay_end": FlowMapEntry(
            event_type="replay_end",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="immediate",
            validation_rules=["sequence_check"],
            dispatcher_target="ReplayModeController",
            ui_component="WorkspaceRoot",
            fallback_behavior="restore_live_mode",
            notes="Re-enables live bindings after replay",
        ),
        "engine_status": FlowMapEntry(
            event_type="engine_status",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="replace_per_engine",
            validation_rules=["sequence_check"],
            dispatcher_target="EngineStatusBinding",
            ui_component="EngineStatusPanel",
            fallback_behavior="show_unknown_status",
            notes="Status per engine (SAE, ERCE, BIRL, FAR)",
        ),
        "heartbeat": FlowMapEntry(
            event_type="heartbeat",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="discard_after_ack",
            validation_rules=["timestamp_check"],
            dispatcher_target="HeartbeatHandler",
            ui_component="ConnectionIndicator",
            fallback_behavior="trigger_reconnect",
            notes="Connection health monitoring",
        ),
        "error": FlowMapEntry(
            event_type="error",
            ingress_handler="SSEConnection.onMessage",
            buffer_strategy="append_limited",
            validation_rules=["sequence_check"],
            dispatcher_target="ErrorHandler",
            ui_component="ErrorNotification",
            fallback_behavior="log_and_display",
            notes="Server-side error notifications",
        ),
    }

    @classmethod
    def get_flow(cls, event_type: str) -> Optional[FlowMapEntry]:
        """Get flow map entry for event type."""
        return cls.FLOW_MAP.get(event_type)

    @classmethod
    def get_all_flows(cls) -> Dict[str, FlowMapEntry]:
        """Get all flow map entries."""
        return cls.FLOW_MAP.copy()

    @classmethod
    def export_flow_map(cls) -> List[Dict[str, Any]]:
        """Export complete flow map as list of dicts."""
        return [entry.to_dict() for entry in cls.FLOW_MAP.values()]


# ============================================================================
# WORKSPACE SSE DISPATCHER
# ============================================================================

class WorkspaceSSEDispatcher:
    """
    Main dispatcher coordinating SSE event flow.
    Implements: Ingress → Buffer → Validator → Dispatcher → UI Component
    """

    def __init__(
        self,
        event_buffer: "EventBuffer",
        binding_registry: "BindingRegistry",
        sequence_validator: Optional["SequenceValidator"] = None,
    ):
        self._buffer = event_buffer
        self._registry = binding_registry
        self._validator = sequence_validator or event_buffer.get_sequence_validator()

        self._flow_traces: List[FlowTrace] = []
        self._max_traces = 1000

        self._stage_callbacks: Dict[SSEFlowStage, List[Callable[[FlowTrace], None]]] = {
            stage: [] for stage in SSEFlowStage
        }

        self._replay_mode = False
        self._logger = logging.getLogger("WorkspaceSSEDispatcher")

    def dispatch(self, event: "EventEnvelope") -> FlowTrace:
        """
        Dispatch an event through the complete flow pipeline.

        Pipeline:
        1. INGRESS - Receive raw event
        2. BUFFER - Add to buffer
        3. VALIDATE - Check sequence
        4. DISPATCH - Route to binding
        5. COMPONENT - Apply to UI
        6. COMPLETE - Flow finished

        Args:
            event: SSE event envelope

        Returns:
            FlowTrace documenting the event's path
        """
        trace = FlowTrace(
            event_id=event.event_id,
            event_type=event.event_type,
        )

        try:
            # Stage 1: INGRESS
            trace.add_stage(SSEFlowStage.INGRESS, {
                "event_id": event.event_id,
                "sequence": event.sequence_number,
            })
            self._notify_stage(SSEFlowStage.INGRESS, trace)

            # Stage 2: BUFFER
            self._buffer.push(event)
            trace.add_stage(SSEFlowStage.BUFFER, {
                "buffer_size": len(self._buffer.get_recent(1000)),
            })
            self._notify_stage(SSEFlowStage.BUFFER, trace)

            # Stage 3: VALIDATE
            seq_valid = self._validator.validate(event.sequence_number)
            if not seq_valid:
                gaps = self._validator.get_gaps()
                trace.add_stage(SSEFlowStage.VALIDATE, {
                    "valid": False,
                    "gaps": gaps[-1] if gaps else None,
                })
                # Continue processing despite gap (gap handler will request replay)
            else:
                trace.add_stage(SSEFlowStage.VALIDATE, {"valid": True})
            self._notify_stage(SSEFlowStage.VALIDATE, trace)

            # Stage 4: DISPATCH
            # Skip dispatch if in replay mode (except replay control events)
            if self._replay_mode and event.event_type not in ["replay_start", "replay_end"]:
                trace.add_stage(SSEFlowStage.DISPATCH, {
                    "skipped": "replay_mode",
                })
                trace.complete()
                self._store_trace(trace)
                return trace

            result = self._registry.bind_event(event)
            if result:
                trace.add_stage(SSEFlowStage.DISPATCH, {
                    "binding": result.target_component,
                    "success": result.success,
                })
                self._notify_stage(SSEFlowStage.DISPATCH, trace)

                # Stage 5: COMPONENT
                if result.success:
                    trace.add_stage(SSEFlowStage.COMPONENT, {
                        "component": result.target_component,
                        "data_applied": result.data_applied,
                    })
                    self._notify_stage(SSEFlowStage.COMPONENT, trace)
                else:
                    trace.mark_error(SSEFlowStage.COMPONENT, result.error_message or "Binding failed")
            else:
                trace.add_stage(SSEFlowStage.DISPATCH, {
                    "skipped": "no_binding_found",
                })

            # Stage 6: COMPLETE
            trace.complete()
            self._notify_stage(SSEFlowStage.COMPLETE, trace)

        except Exception as e:
            trace.mark_error(SSEFlowStage.ERROR, str(e))
            self._logger.error(f"Dispatch error: {e}")

        self._store_trace(trace)
        return trace

    def set_replay_mode(self, enabled: bool) -> None:
        """Enable/disable replay mode."""
        self._replay_mode = enabled
        if enabled:
            self._registry.disable_all()
        else:
            self._registry.enable_all()

    def is_replay_mode(self) -> bool:
        """Check if in replay mode."""
        return self._replay_mode

    def on_stage(self, stage: SSEFlowStage, callback: Callable[[FlowTrace], None]) -> None:
        """Register callback for a flow stage."""
        self._stage_callbacks[stage].append(callback)

    def _notify_stage(self, stage: SSEFlowStage, trace: FlowTrace) -> None:
        """Notify callbacks for a stage."""
        for cb in self._stage_callbacks.get(stage, []):
            try:
                cb(trace)
            except Exception as e:
                self._logger.error(f"Stage callback error: {e}")

    def _store_trace(self, trace: FlowTrace) -> None:
        """Store trace in history."""
        self._flow_traces.append(trace)
        if len(self._flow_traces) > self._max_traces:
            self._flow_traces = self._flow_traces[-self._max_traces:]

    def get_flow_traces(self, limit: int = 100) -> List[FlowTrace]:
        """Get recent flow traces."""
        return self._flow_traces[-limit:]

    def get_traces_by_type(self, event_type: str) -> List[FlowTrace]:
        """Get traces for a specific event type."""
        return [t for t in self._flow_traces if t.event_type == event_type]

    def get_error_traces(self) -> List[FlowTrace]:
        """Get traces that encountered errors."""
        return [t for t in self._flow_traces if not t.success]

    def get_flow_stats(self) -> Dict[str, Any]:
        """Get flow statistics."""
        total = len(self._flow_traces)
        errors = len(self.get_error_traces())
        by_type: Dict[str, int] = {}
        avg_duration = 0.0

        if total > 0:
            for trace in self._flow_traces:
                by_type[trace.event_type] = by_type.get(trace.event_type, 0) + 1
            avg_duration = sum(t.get_duration_ms() for t in self._flow_traces) / total

        return {
            "total_events": total,
            "error_count": errors,
            "success_rate": (total - errors) / total if total > 0 else 1.0,
            "by_event_type": by_type,
            "avg_duration_ms": avg_duration,
            "replay_mode": self._replay_mode,
        }

    def export_flow_map(self) -> List[Dict[str, Any]]:
        """Export the static flow map."""
        return WorkspaceSSEFlowMap.export_flow_map()
