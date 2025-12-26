"""
Compare v3 Monitor - Event emission and logging for intelligence pipeline.

Emits structured envelopes for:
- Engine execution events
- Stage activation reports
- Health integration with SystemHealthTracker

CIP Protocol: This module provides monitoring for CC operations.
Events are logged for CAI audit and GEM UX evaluation.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Log output path (JSONL format)
LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "logs", "compare_v3_events.jsonl"
)

# Reports output path
REPORTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "activation"
)


@dataclass
class MonitorEnvelope:
    """
    Structured envelope for monitor events.

    Fields:
        timestamp: ISO format timestamp
        event_type: Type of event (engine_execution, stage_activation, flag_change)
        stage_id: Stage identifier (stage_0, stage_1, etc.)
        engine: Engine name (sae, erce, birl, far)
        agent_role: Agent role tag for logs (cip-severity, cip-reasoning, far)
        flags_state: Current state of all flags
        status: Event status (success, error, no_op, skipped)
        details: Additional event details
        request_id: Request correlation ID
    """
    timestamp: str
    event_type: str
    stage_id: Optional[str]
    engine: Optional[str]
    agent_role: Optional[str]
    flags_state: Dict[str, bool]
    status: str
    details: Dict[str, Any]
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "stage_id": self.stage_id,
            "engine": self.engine,
            "agent_role": self.agent_role,
            "flags_state": self.flags_state,
            "status": self.status,
            "details": self.details,
            "request_id": self.request_id
        }


def _get_flag_state_dict() -> Dict[str, bool]:
    """Get current flag state as dictionary."""
    try:
        from flag_registry import get_flag_state
        return get_flag_state().to_dict()
    except ImportError:
        # Fallback if flag_registry not available
        return {
            "flag_sae": False,
            "flag_erce": False,
            "flag_birl": False,
            "flag_far": False
        }


def _append_to_log(envelope: MonitorEnvelope) -> None:
    """Append envelope to JSONL log file."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(envelope.to_dict()) + "\n")


def monitor_event(
    event_type: str,
    engine: Optional[str] = None,
    agent_role: Optional[str] = None,
    stage_id: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> MonitorEnvelope:
    """
    Emit a structured monitoring event.

    Logs to JSONL file and returns envelope for inline use.

    Args:
        event_type: Type of event (engine_execution, stage_activation, flag_change)
        engine: Engine name if applicable (sae, erce, birl, far)
        agent_role: Agent role tag for logs (cip-severity, cip-reasoning, far)
        stage_id: Stage identifier (stage_0, stage_1, etc.)
        status: Event status (success, error, no_op, skipped)
        details: Additional event details
        request_id: Request correlation ID

    Returns:
        MonitorEnvelope for the event
    """
    flags = _get_flag_state_dict()

    envelope = MonitorEnvelope(
        timestamp=datetime.now().isoformat(),
        event_type=event_type,
        stage_id=stage_id,
        engine=engine,
        agent_role=agent_role,
        flags_state=flags,
        status=status,
        details=details or {},
        request_id=request_id
    )

    # Append to JSONL log
    _append_to_log(envelope)

    return envelope


def generate_activation_report(
    stage_id: str,
    flags_before: Dict[str, bool],
    flags_after: Dict[str, bool],
    validation_results: Dict[str, Any],
    no_op: bool = False
) -> str:
    """
    Generate JSON activation report for a stage.

    Args:
        stage_id: Stage identifier (e.g., stage_0, stage_1)
        flags_before: Flag state before activation
        flags_after: Flag state after activation
        validation_results: Results of validation checks
        no_op: True if this was a dry run (Stage 0)

    Returns:
        Path to generated report file
    """
    os.makedirs(REPORTS_PATH, exist_ok=True)

    # Calculate diff
    diff = {}
    for k in set(flags_before.keys()) | set(flags_after.keys()):
        if flags_before.get(k) != flags_after.get(k):
            diff[k] = {"was": flags_before.get(k), "now": flags_after.get(k)}

    # Determine previous and next stages
    stage_num = int(stage_id.replace("stage_", "")) if stage_id.startswith("stage_") else 0
    previous_stage = f"stage_{stage_num - 1}" if stage_num > 0 else None
    next_stage = f"stage_{stage_num + 1}" if stage_num < 4 else None

    report = {
        "report_id": f"activation_report_{stage_id}",
        "stage_id": stage_id,
        "generated_at": datetime.now().isoformat(),
        "no_op": no_op,
        "flags": {
            "before": flags_before,
            "after": flags_after,
            "diff": diff
        },
        "validation": validation_results,
        "reversible": True,
        "rollback_command": f"python stage_runner.py rollback {stage_id}",
        "previous_stage": previous_stage,
        "next_stage": next_stage
    }

    filename = f"activation_report_{stage_id}.json"
    filepath = os.path.join(REPORTS_PATH, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return filepath


def get_recent_events(
    limit: int = 100,
    event_type: Optional[str] = None,
    engine: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Read recent events from the log file.

    Args:
        limit: Maximum number of events to return
        event_type: Filter by event type
        engine: Filter by engine

    Returns:
        List of event dictionaries
    """
    if not os.path.exists(LOG_PATH):
        return []

    events = []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())

                # Apply filters
                if event_type and event.get("event_type") != event_type:
                    continue
                if engine and event.get("engine") != engine:
                    continue

                events.append(event)
            except json.JSONDecodeError:
                continue

    # Return most recent events
    return events[-limit:]


def count_events_by_status(since: Optional[datetime] = None) -> Dict[str, int]:
    """
    Count events by status.

    Args:
        since: Only count events after this datetime

    Returns:
        Dict mapping status to count
    """
    counts = {"success": 0, "error": 0, "no_op": 0, "skipped": 0}

    if not os.path.exists(LOG_PATH):
        return counts

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())

                # Apply time filter
                if since:
                    event_time = datetime.fromisoformat(event["timestamp"])
                    if event_time < since:
                        continue

                status = event.get("status", "unknown")
                if status in counts:
                    counts[status] += 1

            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return counts


def clear_event_log() -> None:
    """Clear the event log file (for testing)."""
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
