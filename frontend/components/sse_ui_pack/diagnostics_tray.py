"""
SSE Diagnostics Tray v1
P7.CC2.01 - Task 2

Provides:
- Recent events list with type filtering
- Client sequence monitor
- Replay mode notification panel
- Error inspector with stack traces

CIP Protocol: CC2 implementation for P7 debugging/monitoring.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from components.color_tokens import get_token, is_high_contrast_mode, inject_color_tokens
from components.a11y_utils import get_aria_attrs, format_aria_attrs


# ============================================================================
# CONFIGURATION
# ============================================================================

class EventSeverity(Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


@dataclass
class DiagnosticsTrayConfig:
    """Configuration for diagnostics tray."""
    max_events_displayed: int = 20
    show_timestamps: bool = True
    show_sequence_numbers: bool = True
    show_event_data: bool = False  # Collapsed by default
    auto_scroll: bool = True
    filter_event_types: Optional[List[str]] = None
    position: str = "bottom-right"  # bottom-right, bottom-left, sidebar


@dataclass
class DiagnosticEvent:
    """A diagnostic event entry."""
    event_id: str
    event_type: str
    sequence: int
    timestamp: str
    severity: EventSeverity = EventSeverity.INFO
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_diag_key(suffix: str) -> str:
    """Get session state key for diagnostics."""
    return f"_cip_diag_{suffix}"


def init_diagnostics_state() -> None:
    """Initialize diagnostics state."""
    defaults = {
        "tray_open": False,
        "tray_minimized": False,
        "events": [],
        "filter_type": "all",
        "filter_severity": "all",
        "selected_event_id": None,
        "seq_monitor_enabled": True,
        "last_received_seq": 0,
        "expected_seq": 0,
        "seq_gaps": [],
        "replay_active": False,
        "replay_events_pending": 0,
        "errors": [],
        "warnings_count": 0,
        "errors_count": 0,
    }

    for key, default in defaults.items():
        full_key = _get_diag_key(key)
        if full_key not in st.session_state:
            st.session_state[full_key] = default


def is_tray_open() -> bool:
    """Check if diagnostics tray is open."""
    init_diagnostics_state()
    return st.session_state.get(_get_diag_key("tray_open"), False)


def toggle_tray() -> None:
    """Toggle diagnostics tray."""
    init_diagnostics_state()
    key = _get_diag_key("tray_open")
    st.session_state[key] = not st.session_state.get(key, False)


def add_diagnostic_event(event: DiagnosticEvent) -> None:
    """Add event to diagnostics."""
    init_diagnostics_state()
    events_key = _get_diag_key("events")
    events = st.session_state.get(events_key, [])

    # Convert to dict for storage
    event_dict = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "sequence": event.sequence,
        "timestamp": event.timestamp,
        "severity": event.severity.value,
        "data": event.data,
        "error_message": event.error_message,
        "stack_trace": event.stack_trace,
    }

    events.append(event_dict)

    # Limit events
    if len(events) > 100:
        events = events[-100:]

    st.session_state[events_key] = events

    # Update counters
    if event.severity == EventSeverity.ERROR:
        st.session_state[_get_diag_key("errors_count")] = \
            st.session_state.get(_get_diag_key("errors_count"), 0) + 1
    elif event.severity == EventSeverity.WARNING:
        st.session_state[_get_diag_key("warnings_count")] = \
            st.session_state.get(_get_diag_key("warnings_count"), 0) + 1


def update_sequence_monitor(received_seq: int, expected_seq: int) -> None:
    """Update sequence monitor state."""
    init_diagnostics_state()
    st.session_state[_get_diag_key("last_received_seq")] = received_seq
    st.session_state[_get_diag_key("expected_seq")] = expected_seq

    # Record gap if detected
    if received_seq > expected_seq:
        gaps = st.session_state.get(_get_diag_key("seq_gaps"), [])
        gaps.append({
            "expected": expected_seq,
            "received": received_seq,
            "gap_size": received_seq - expected_seq,
            "timestamp": datetime.now().isoformat(),
        })
        st.session_state[_get_diag_key("seq_gaps")] = gaps[-20:]  # Keep last 20


def set_replay_status(active: bool, pending_count: int = 0) -> None:
    """Set replay status in diagnostics."""
    init_diagnostics_state()
    st.session_state[_get_diag_key("replay_active")] = active
    st.session_state[_get_diag_key("replay_events_pending")] = pending_count


def add_error(error_message: str, stack_trace: Optional[str] = None) -> None:
    """Add error to diagnostics."""
    init_diagnostics_state()
    errors = st.session_state.get(_get_diag_key("errors"), [])
    errors.append({
        "message": error_message,
        "stack_trace": stack_trace,
        "timestamp": datetime.now().isoformat(),
    })
    st.session_state[_get_diag_key("errors")] = errors[-10:]  # Keep last 10


def get_diagnostics_data() -> Dict[str, Any]:
    """Get all diagnostics data."""
    init_diagnostics_state()

    return {
        "events": st.session_state.get(_get_diag_key("events"), []),
        "last_received_seq": st.session_state.get(_get_diag_key("last_received_seq"), 0),
        "expected_seq": st.session_state.get(_get_diag_key("expected_seq"), 0),
        "seq_gaps": st.session_state.get(_get_diag_key("seq_gaps"), []),
        "replay_active": st.session_state.get(_get_diag_key("replay_active"), False),
        "replay_events_pending": st.session_state.get(_get_diag_key("replay_events_pending"), 0),
        "errors": st.session_state.get(_get_diag_key("errors"), []),
        "warnings_count": st.session_state.get(_get_diag_key("warnings_count"), 0),
        "errors_count": st.session_state.get(_get_diag_key("errors_count"), 0),
    }


def clear_diagnostics() -> None:
    """Clear all diagnostics data."""
    init_diagnostics_state()
    st.session_state[_get_diag_key("events")] = []
    st.session_state[_get_diag_key("seq_gaps")] = []
    st.session_state[_get_diag_key("errors")] = []
    st.session_state[_get_diag_key("warnings_count")] = 0
    st.session_state[_get_diag_key("errors_count")] = 0


# ============================================================================
# CSS STYLING
# ============================================================================

def _generate_diagnostics_css() -> str:
    """Generate CSS for diagnostics tray."""
    high_contrast = is_high_contrast_mode()

    # Get tokens
    bg_primary = get_token("bg-primary")
    bg_secondary = get_token("bg-secondary")
    bg_tertiary = get_token("bg-tertiary")
    text_primary = get_token("text-primary")
    text_muted = get_token("text-muted")
    border_default = get_token("border-default")
    border_strong = get_token("border-strong")
    accent_primary = get_token("accent-primary")
    accent_success = get_token("accent-success")
    accent_warning = get_token("accent-warning")
    accent_error = get_token("accent-error")

    border_width = "2px" if high_contrast else "1px"

    return f"""
<style>
/* ============================================================================
   SSE DIAGNOSTICS TRAY v1
   P7.CC2.01 - Task 2: Monitoring & Debugging
   ============================================================================ */

/* Diagnostics Tray Container */
.cip-diag-tray {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    max-height: 500px;
    background: {bg_primary};
    border: {border_width} solid {border_strong};
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    z-index: 10000;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}}

.cip-diag-tray.minimized {{
    max-height: 44px;
}}

/* Tray Header */
.cip-diag-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: {bg_secondary};
    border-bottom: 1px solid {border_default};
    cursor: pointer;
}}

.cip-diag-title {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 600;
    color: {text_primary};
}}

.cip-diag-title-icon {{
    font-size: 16px;
}}

.cip-diag-badges {{
    display: flex;
    gap: 6px;
}}

.cip-diag-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 9px;
    font-size: 10px;
    font-weight: 600;
}}

.cip-diag-badge.error {{
    background: {accent_error};
    color: white;
}}

.cip-diag-badge.warning {{
    background: {accent_warning};
    color: black;
}}

.cip-diag-badge.info {{
    background: {accent_primary};
    color: white;
}}

.cip-diag-controls {{
    display: flex;
    gap: 4px;
}}

.cip-diag-control-btn {{
    background: none;
    border: none;
    color: {text_muted};
    cursor: pointer;
    padding: 4px;
    font-size: 14px;
    border-radius: 4px;
}}

.cip-diag-control-btn:hover {{
    background: {bg_tertiary};
    color: {text_primary};
}}

/* Tab Bar */
.cip-diag-tabs {{
    display: flex;
    background: {bg_secondary};
    border-bottom: 1px solid {border_default};
}}

.cip-diag-tab {{
    flex: 1;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 500;
    color: {text_muted};
    background: none;
    border: none;
    cursor: pointer;
    text-align: center;
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
}}

.cip-diag-tab:hover {{
    color: {text_primary};
    background: {bg_tertiary};
}}

.cip-diag-tab.active {{
    color: {accent_primary};
    border-bottom-color: {accent_primary};
}}

/* Content Area */
.cip-diag-content {{
    flex: 1;
    overflow-y: auto;
    padding: 12px;
}}

/* Events List */
.cip-diag-events {{
    display: flex;
    flex-direction: column;
    gap: 6px;
}}

.cip-diag-event {{
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px 10px;
    background: {bg_secondary};
    border-radius: 6px;
    font-size: 11px;
    border-left: 3px solid {border_default};
}}

.cip-diag-event.info {{
    border-left-color: {accent_primary};
}}

.cip-diag-event.warning {{
    border-left-color: {accent_warning};
}}

.cip-diag-event.error {{
    border-left-color: {accent_error};
}}

.cip-diag-event.debug {{
    border-left-color: {text_muted};
    opacity: 0.7;
}}

.cip-diag-event-seq {{
    font-family: monospace;
    color: {text_muted};
    min-width: 40px;
}}

.cip-diag-event-type {{
    font-weight: 600;
    color: {text_primary};
}}

.cip-diag-event-time {{
    color: {text_muted};
    margin-left: auto;
    font-family: monospace;
    font-size: 10px;
}}

/* Sequence Monitor */
.cip-diag-seq-monitor {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
}}

.cip-diag-seq-stat {{
    padding: 10px 12px;
    background: {bg_secondary};
    border-radius: 8px;
}}

.cip-diag-seq-label {{
    font-size: 10px;
    color: {text_muted};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}}

.cip-diag-seq-value {{
    font-size: 20px;
    font-weight: 700;
    font-family: monospace;
    color: {text_primary};
}}

.cip-diag-seq-value.gap {{
    color: {accent_warning};
}}

/* Replay Panel */
.cip-diag-replay {{
    padding: 12px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
    border: 1px solid {accent_primary};
    border-radius: 8px;
    margin-bottom: 12px;
}}

.cip-diag-replay-title {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    color: {text_primary};
    margin-bottom: 8px;
}}

.cip-diag-replay-icon {{
    animation: cip-spin 2s linear infinite;
}}

.cip-diag-replay-stats {{
    font-size: 11px;
    color: {text_muted};
}}

/* Error Inspector */
.cip-diag-error {{
    padding: 10px 12px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid {accent_error};
    border-radius: 8px;
    margin-bottom: 8px;
}}

.cip-diag-error-msg {{
    font-size: 12px;
    color: {text_primary};
    margin-bottom: 6px;
}}

.cip-diag-error-time {{
    font-size: 10px;
    color: {text_muted};
    font-family: monospace;
}}

.cip-diag-error-stack {{
    margin-top: 8px;
    padding: 8px;
    background: {bg_tertiary};
    border-radius: 4px;
    font-size: 10px;
    font-family: monospace;
    color: {text_muted};
    white-space: pre-wrap;
    overflow-x: auto;
}}

/* Gap Warning */
.cip-diag-gap-warning {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid {accent_warning};
    border-radius: 6px;
    margin-bottom: 8px;
    font-size: 11px;
}}

.cip-diag-gap-icon {{
    font-size: 14px;
}}

.cip-diag-gap-text {{
    color: {text_primary};
}}

.cip-diag-gap-detail {{
    color: {text_muted};
    font-family: monospace;
}}

/* Empty State */
.cip-diag-empty {{
    text-align: center;
    padding: 24px;
    color: {text_muted};
    font-size: 12px;
}}

.cip-diag-empty-icon {{
    font-size: 32px;
    margin-bottom: 8px;
    opacity: 0.5;
}}

/* Footer */
.cip-diag-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: {bg_secondary};
    border-top: 1px solid {border_default};
    font-size: 10px;
    color: {text_muted};
}}

/* Print Styles */
@media print {{
    .cip-diag-tray {{
        display: none;
    }}
}}
</style>
"""


def inject_diagnostics_css() -> None:
    """Inject diagnostics CSS into page."""
    st.markdown(_generate_diagnostics_css(), unsafe_allow_html=True)


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_diagnostics_toggle() -> None:
    """Render toggle button for diagnostics tray."""
    init_diagnostics_state()
    data = get_diagnostics_data()

    errors = data["errors_count"]
    warnings = data["warnings_count"]

    label_parts = ["📊 Diagnostics"]
    if errors > 0:
        label_parts.append(f"({errors} errors)")
    elif warnings > 0:
        label_parts.append(f"({warnings} warnings)")

    if st.button(" ".join(label_parts), key="diag_toggle_btn"):
        toggle_tray()
        st.rerun()


def render_diagnostics_tray(
    config: Optional[DiagnosticsTrayConfig] = None,
) -> None:
    """
    Render the SSE Diagnostics Tray.

    Args:
        config: Optional configuration
    """
    if not is_tray_open():
        return

    init_diagnostics_state()
    inject_color_tokens()
    inject_diagnostics_css()

    config = config or DiagnosticsTrayConfig()
    data = get_diagnostics_data()

    # Filter events
    events = data["events"][-config.max_events_displayed:]
    if config.filter_event_types:
        events = [e for e in events if e["event_type"] in config.filter_event_types]

    # Build events HTML
    events_html = ""
    if events:
        for event in reversed(events):  # Most recent first
            severity_class = event.get("severity", "info")
            timestamp = event.get("timestamp", "")
            if config.show_timestamps and timestamp:
                time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
            else:
                time_str = ""

            seq_html = f'<span class="cip-diag-event-seq">#{event.get("sequence", "?")}</span>' \
                if config.show_sequence_numbers else ""

            events_html += f"""
            <div class="cip-diag-event {severity_class}">
                {seq_html}
                <span class="cip-diag-event-type">{event.get("event_type", "unknown")}</span>
                <span class="cip-diag-event-time">{time_str}</span>
            </div>
            """
    else:
        events_html = """
        <div class="cip-diag-empty">
            <div class="cip-diag-empty-icon">📭</div>
            No events received yet
        </div>
        """

    # Build sequence monitor HTML
    last_seq = data["last_received_seq"]
    expected_seq = data["expected_seq"]
    has_gap = last_seq > expected_seq and expected_seq > 0

    seq_monitor_html = f"""
    <div class="cip-diag-seq-monitor">
        <div class="cip-diag-seq-stat">
            <div class="cip-diag-seq-label">Last Received</div>
            <div class="cip-diag-seq-value">{last_seq}</div>
        </div>
        <div class="cip-diag-seq-stat">
            <div class="cip-diag-seq-label">Expected Next</div>
            <div class="cip-diag-seq-value {'gap' if has_gap else ''}">{expected_seq}</div>
        </div>
    </div>
    """

    # Gaps warning
    gaps_html = ""
    if data["seq_gaps"]:
        recent_gap = data["seq_gaps"][-1]
        gaps_html = f"""
        <div class="cip-diag-gap-warning">
            <span class="cip-diag-gap-icon">⚠️</span>
            <span class="cip-diag-gap-text">Sequence gap detected</span>
            <span class="cip-diag-gap-detail">
                Expected #{recent_gap['expected']}, got #{recent_gap['received']}
            </span>
        </div>
        """

    # Replay panel
    replay_html = ""
    if data["replay_active"]:
        replay_html = f"""
        <div class="cip-diag-replay">
            <div class="cip-diag-replay-title">
                <span class="cip-diag-replay-icon">🔄</span>
                Replay in Progress
            </div>
            <div class="cip-diag-replay-stats">
                {data['replay_events_pending']} events pending
            </div>
        </div>
        """

    # Errors panel
    errors_html = ""
    if data["errors"]:
        for error in data["errors"][-3:]:  # Show last 3
            stack_html = ""
            if error.get("stack_trace"):
                stack_html = f'<div class="cip-diag-error-stack">{error["stack_trace"]}</div>'

            errors_html += f"""
            <div class="cip-diag-error">
                <div class="cip-diag-error-msg">{error['message']}</div>
                <div class="cip-diag-error-time">{error['timestamp']}</div>
                {stack_html}
            </div>
            """

    # Badge counts
    badge_html = ""
    if data["errors_count"] > 0:
        badge_html += f'<span class="cip-diag-badge error">{data["errors_count"]}</span>'
    if data["warnings_count"] > 0:
        badge_html += f'<span class="cip-diag-badge warning">{data["warnings_count"]}</span>'

    aria_attrs = get_aria_attrs(
        "dialog",
        label="SSE Diagnostics Tray",
        modal="false",
    )
    aria_str = format_aria_attrs(aria_attrs)

    st.markdown(f"""
    <div class="cip-diag-tray" {aria_str}>
        <div class="cip-diag-header">
            <div class="cip-diag-title">
                <span class="cip-diag-title-icon">📊</span>
                SSE Diagnostics
                <div class="cip-diag-badges">{badge_html}</div>
            </div>
        </div>

        <div class="cip-diag-content">
            {replay_html}
            {gaps_html}
            {errors_html}
            {seq_monitor_html}

            <div class="cip-diag-events">
                {events_html}
            </div>
        </div>

        <div class="cip-diag-footer">
            <span>{len(events)} events</span>
            <span>{len(data['seq_gaps'])} gaps</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Close button (Streamlit button for interactivity)
    if st.button("Close Diagnostics", key="diag_close_btn"):
        toggle_tray()
        st.rerun()


# ============================================================================
# CC3 INTEGRATION
# ============================================================================

def get_diagnostics_for_binder() -> Dict[str, Any]:
    """
    Get diagnostics data for CC3 binder.

    Returns:
        Dictionary with diagnostics summary
    """
    data = get_diagnostics_data()

    return {
        "events_count": len(data["events"]),
        "last_seq": data["last_received_seq"],
        "expected_seq": data["expected_seq"],
        "gaps_count": len(data["seq_gaps"]),
        "has_gaps": len(data["seq_gaps"]) > 0,
        "replay_active": data["replay_active"],
        "errors_count": data["errors_count"],
        "warnings_count": data["warnings_count"],
        "health_status": "error" if data["errors_count"] > 0 else (
            "warning" if data["warnings_count"] > 0 or len(data["seq_gaps"]) > 0 else "healthy"
        ),
    }
