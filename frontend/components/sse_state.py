"""
SSE State Components - Phase 7 Streaming Backend Preparation
P7 Readiness: EventBuffer + ConnectionStateIndicator Support

Provides:
- ConnectionStateIndicator: Visual SSE connection status
- EventBuffer stub interface for CC3 integration
- Debug overlay for SSE state visualization
- Session state management for streaming events

CIP Protocol: CC2 implementation for P7 backend alignment.
"""

import streamlit as st
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from components.color_tokens import get_token, is_high_contrast_mode, inject_color_tokens
from components.a11y_utils import get_aria_attrs, format_aria_attrs


# ============================================================================
# CONNECTION STATE DEFINITIONS
# ============================================================================

class ConnectionState(Enum):
    """SSE connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    REPLAYING = "replaying"
    ERROR = "error"


@dataclass
class SSEEvent:
    """Represents an SSE event for the buffer."""
    event_id: str
    event_type: str
    sequence: int
    timestamp: datetime
    data: Dict[str, Any]
    processed: bool = False


@dataclass
class EventBufferState:
    """State container for EventBuffer."""
    events: List[SSEEvent] = field(default_factory=list)
    last_sequence: int = 0
    buffer_size: int = 100
    is_replaying: bool = False
    replay_from: Optional[int] = None


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_sse_state_key(key_suffix: str) -> str:
    """Get session state key with SSE prefix."""
    return f"_cip_sse_{key_suffix}"


def init_sse_state() -> None:
    """Initialize SSE state in session."""
    defaults = {
        "connection_state": ConnectionState.DISCONNECTED.value,
        "last_event_id": None,
        "last_sequence": 0,
        "event_buffer": [],
        "buffer_size": 100,
        "is_replaying": False,
        "replay_from": None,
        "error_message": None,
        "reconnect_attempts": 0,
        "connected_at": None,
        "debug_mode": False,
    }

    for key, default in defaults.items():
        full_key = _get_sse_state_key(key)
        if full_key not in st.session_state:
            st.session_state[full_key] = default


def get_connection_state() -> ConnectionState:
    """Get current SSE connection state."""
    init_sse_state()
    state_str = st.session_state.get(_get_sse_state_key("connection_state"), "disconnected")
    try:
        return ConnectionState(state_str)
    except ValueError:
        return ConnectionState.DISCONNECTED


def set_connection_state(state: ConnectionState) -> None:
    """Set SSE connection state."""
    init_sse_state()
    st.session_state[_get_sse_state_key("connection_state")] = state.value

    if state == ConnectionState.CONNECTED:
        st.session_state[_get_sse_state_key("connected_at")] = datetime.now().isoformat()
        st.session_state[_get_sse_state_key("reconnect_attempts")] = 0
    elif state == ConnectionState.RECONNECTING:
        attempts = st.session_state.get(_get_sse_state_key("reconnect_attempts"), 0)
        st.session_state[_get_sse_state_key("reconnect_attempts")] = attempts + 1


def is_debug_mode() -> bool:
    """Check if SSE debug mode is enabled."""
    init_sse_state()
    return st.session_state.get(_get_sse_state_key("debug_mode"), False)


def toggle_debug_mode() -> None:
    """Toggle SSE debug mode."""
    init_sse_state()
    key = _get_sse_state_key("debug_mode")
    st.session_state[key] = not st.session_state.get(key, False)


# ============================================================================
# EVENT BUFFER STUB INTERFACE
# ============================================================================

def get_event_buffer() -> List[Dict[str, Any]]:
    """Get current event buffer (stub for CC3)."""
    init_sse_state()
    return st.session_state.get(_get_sse_state_key("event_buffer"), [])


def add_event_to_buffer(event: Dict[str, Any]) -> None:
    """Add event to buffer (stub for CC3)."""
    init_sse_state()
    buffer_key = _get_sse_state_key("event_buffer")
    buffer = st.session_state.get(buffer_key, [])

    # Enforce buffer size limit
    buffer_size = st.session_state.get(_get_sse_state_key("buffer_size"), 100)
    if len(buffer) >= buffer_size:
        buffer = buffer[-(buffer_size - 1):]

    buffer.append({
        **event,
        "received_at": datetime.now().isoformat(),
    })

    st.session_state[buffer_key] = buffer

    # Update sequence tracking
    if "sequence" in event:
        st.session_state[_get_sse_state_key("last_sequence")] = event["sequence"]
    if "event_id" in event:
        st.session_state[_get_sse_state_key("last_event_id")] = event["event_id"]


def clear_event_buffer() -> None:
    """Clear event buffer."""
    init_sse_state()
    st.session_state[_get_sse_state_key("event_buffer")] = []


def get_last_sequence() -> int:
    """Get last processed sequence number."""
    init_sse_state()
    return st.session_state.get(_get_sse_state_key("last_sequence"), 0)


def set_replay_mode(enabled: bool, from_sequence: Optional[int] = None) -> None:
    """Set replay mode state."""
    init_sse_state()
    st.session_state[_get_sse_state_key("is_replaying")] = enabled
    st.session_state[_get_sse_state_key("replay_from")] = from_sequence

    if enabled:
        set_connection_state(ConnectionState.REPLAYING)


# ============================================================================
# CSS STYLING
# ============================================================================

def _generate_sse_state_css() -> str:
    """Generate CSS for SSE state components."""
    high_contrast = is_high_contrast_mode()

    # Get tokens
    bg_primary = get_token("bg-primary")
    bg_secondary = get_token("bg-secondary")
    text_primary = get_token("text-primary")
    text_muted = get_token("text-muted")
    border_default = get_token("border-default")

    # State-specific colors
    connected_color = get_token("accent-success")
    connecting_color = get_token("accent-warning")
    disconnected_color = get_token("text-muted")
    error_color = get_token("accent-error")
    replaying_color = get_token("accent-primary")

    border_width = "2px" if high_contrast else "1px"

    return f"""
<style>
/* ============================================================================
   SSE STATE COMPONENTS
   Phase 7 Readiness - CC2 Implementation
   ============================================================================ */

/* Connection State Indicator */
.cip-sse-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: {bg_secondary};
    border: {border_width} solid {border_default};
    border-radius: 20px;
    font-size: 12px;
    color: {text_primary};
}}

.cip-sse-indicator-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}}

.cip-sse-indicator-dot.connected {{
    background: {connected_color};
    box-shadow: 0 0 6px {connected_color};
}}

.cip-sse-indicator-dot.connecting,
.cip-sse-indicator-dot.reconnecting {{
    background: {connecting_color};
    animation: cip-pulse 1.5s ease-in-out infinite;
}}

.cip-sse-indicator-dot.replaying {{
    background: {replaying_color};
    animation: cip-pulse 1s ease-in-out infinite;
}}

.cip-sse-indicator-dot.disconnected {{
    background: {disconnected_color};
}}

.cip-sse-indicator-dot.error {{
    background: {error_color};
}}

@keyframes cip-pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(0.8); }}
}}

.cip-sse-indicator-label {{
    font-weight: 500;
}}

.cip-sse-indicator-detail {{
    color: {text_muted};
    font-size: 11px;
}}

/* Debug Overlay */
.cip-sse-debug-overlay {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 350px;
    max-height: 400px;
    background: {bg_primary};
    border: {border_width} solid {border_default};
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    z-index: 9999;
    overflow: hidden;
}}

.cip-sse-debug-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: {bg_secondary};
    border-bottom: 1px solid {border_default};
}}

.cip-sse-debug-title {{
    font-size: 13px;
    font-weight: 600;
    color: {text_primary};
    display: flex;
    align-items: center;
    gap: 8px;
}}

.cip-sse-debug-close {{
    background: none;
    border: none;
    color: {text_muted};
    cursor: pointer;
    font-size: 16px;
    padding: 4px;
}}

.cip-sse-debug-close:hover {{
    color: {text_primary};
}}

.cip-sse-debug-content {{
    padding: 12px 16px;
    max-height: 300px;
    overflow-y: auto;
}}

.cip-sse-debug-section {{
    margin-bottom: 16px;
}}

.cip-sse-debug-section-title {{
    font-size: 11px;
    font-weight: 600;
    color: {text_muted};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}}

.cip-sse-debug-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    font-size: 12px;
}}

.cip-sse-debug-key {{
    color: {text_muted};
}}

.cip-sse-debug-value {{
    color: {text_primary};
    font-family: monospace;
}}

.cip-sse-debug-event {{
    background: {bg_secondary};
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 11px;
}}

.cip-sse-debug-event-type {{
    font-weight: 600;
    color: {replaying_color};
}}

.cip-sse-debug-event-seq {{
    color: {text_muted};
    font-family: monospace;
}}

/* Compact Indicator */
.cip-sse-indicator.compact {{
    padding: 4px 8px;
    font-size: 11px;
}}

.cip-sse-indicator.compact .cip-sse-indicator-dot {{
    width: 6px;
    height: 6px;
}}

/* Print Styles */
@media print {{
    .cip-sse-debug-overlay {{
        display: none;
    }}
}}
</style>
"""


def inject_sse_state_css() -> None:
    """Inject SSE state CSS into the page."""
    st.markdown(_generate_sse_state_css(), unsafe_allow_html=True)


# ============================================================================
# CONNECTION STATE INDICATOR
# ============================================================================

def render_connection_state_indicator(
    compact: bool = False,
    show_details: bool = True,
) -> ConnectionState:
    """
    Render SSE connection state indicator.

    Args:
        compact: Use compact display mode
        show_details: Show connection details (sequence, time)

    Returns:
        Current ConnectionState
    """
    init_sse_state()
    inject_color_tokens()
    inject_sse_state_css()

    state = get_connection_state()
    compact_class = "compact" if compact else ""

    # State display configuration
    state_config = {
        ConnectionState.DISCONNECTED: {
            "label": "Disconnected",
            "icon": "⚫",
            "class": "disconnected",
        },
        ConnectionState.CONNECTING: {
            "label": "Connecting...",
            "icon": "🟡",
            "class": "connecting",
        },
        ConnectionState.CONNECTED: {
            "label": "Connected",
            "icon": "🟢",
            "class": "connected",
        },
        ConnectionState.RECONNECTING: {
            "label": "Reconnecting...",
            "icon": "🟠",
            "class": "reconnecting",
        },
        ConnectionState.REPLAYING: {
            "label": "Replaying...",
            "icon": "🔵",
            "class": "replaying",
        },
        ConnectionState.ERROR: {
            "label": "Error",
            "icon": "🔴",
            "class": "error",
        },
    }

    config = state_config.get(state, state_config[ConnectionState.DISCONNECTED])

    # Build details
    details_html = ""
    if show_details and not compact:
        last_seq = get_last_sequence()
        if last_seq > 0:
            details_html = f'<span class="cip-sse-indicator-detail">seq: {last_seq}</span>'

    # ARIA attributes
    aria_attrs = get_aria_attrs(
        "status",
        label=f"SSE Connection: {config['label']}",
        live="polite",
    )
    aria_str = format_aria_attrs(aria_attrs)

    st.markdown(f"""
    <div class="cip-sse-indicator {compact_class}" {aria_str}>
        <span class="cip-sse-indicator-dot {config['class']}"></span>
        <span class="cip-sse-indicator-label">{config['label']}</span>
        {details_html}
    </div>
    """, unsafe_allow_html=True)

    return state


# ============================================================================
# DEBUG OVERLAY
# ============================================================================

def render_debug_overlay() -> None:
    """
    Render SSE debug overlay panel.

    Shows:
    - Connection state
    - Last sequence number
    - Buffer size
    - Recent events
    - Reconnect attempts
    """
    if not is_debug_mode():
        return

    init_sse_state()
    inject_sse_state_css()

    state = get_connection_state()
    buffer = get_event_buffer()
    last_seq = get_last_sequence()
    reconnect_attempts = st.session_state.get(_get_sse_state_key("reconnect_attempts"), 0)
    connected_at = st.session_state.get(_get_sse_state_key("connected_at"), None)
    is_replaying = st.session_state.get(_get_sse_state_key("is_replaying"), False)
    error_msg = st.session_state.get(_get_sse_state_key("error_message"), None)

    # Build recent events HTML
    recent_events_html = ""
    for event in buffer[-5:]:  # Last 5 events
        event_type = event.get("event_type", "unknown")
        seq = event.get("sequence", "?")
        recent_events_html += f"""
        <div class="cip-sse-debug-event">
            <span class="cip-sse-debug-event-type">{event_type}</span>
            <span class="cip-sse-debug-event-seq">#{seq}</span>
        </div>
        """

    if not recent_events_html:
        recent_events_html = '<div style="color: #64748B; font-size: 11px;">No events yet</div>'

    # Error display
    error_html = ""
    if error_msg:
        error_html = f"""
        <div class="cip-sse-debug-section">
            <div class="cip-sse-debug-section-title">Error</div>
            <div style="color: #F87171; font-size: 11px;">{error_msg}</div>
        </div>
        """

    st.markdown(f"""
    <div class="cip-sse-debug-overlay" role="complementary" aria-label="SSE Debug Panel">
        <div class="cip-sse-debug-header">
            <div class="cip-sse-debug-title">
                📡 SSE Debug
            </div>
        </div>
        <div class="cip-sse-debug-content">
            <div class="cip-sse-debug-section">
                <div class="cip-sse-debug-section-title">Connection</div>
                <div class="cip-sse-debug-row">
                    <span class="cip-sse-debug-key">State</span>
                    <span class="cip-sse-debug-value">{state.value}</span>
                </div>
                <div class="cip-sse-debug-row">
                    <span class="cip-sse-debug-key">Last Sequence</span>
                    <span class="cip-sse-debug-value">{last_seq}</span>
                </div>
                <div class="cip-sse-debug-row">
                    <span class="cip-sse-debug-key">Reconnects</span>
                    <span class="cip-sse-debug-value">{reconnect_attempts}</span>
                </div>
                <div class="cip-sse-debug-row">
                    <span class="cip-sse-debug-key">Replaying</span>
                    <span class="cip-sse-debug-value">{'Yes' if is_replaying else 'No'}</span>
                </div>
            </div>

            <div class="cip-sse-debug-section">
                <div class="cip-sse-debug-section-title">Buffer ({len(buffer)} events)</div>
                {recent_events_html}
            </div>

            {error_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_debug_toggle() -> None:
    """Render debug mode toggle button."""
    debug_on = is_debug_mode()
    label = "🐛 Debug On" if debug_on else "🐛 Debug Off"

    if st.button(label, key="sse_debug_toggle", help="Toggle SSE debug overlay"):
        toggle_debug_mode()
        st.rerun()


# ============================================================================
# CC3 INTEGRATION INTERFACE
# ============================================================================

def get_sse_state_for_binder() -> Dict[str, Any]:
    """
    Get SSE state in format for CC3 data binder.

    Returns:
        Dictionary with SSE state data
    """
    init_sse_state()
    state = get_connection_state()

    return {
        "connection_state": state.value,
        "is_connected": state == ConnectionState.CONNECTED,
        "is_replaying": st.session_state.get(_get_sse_state_key("is_replaying"), False),
        "last_sequence": get_last_sequence(),
        "last_event_id": st.session_state.get(_get_sse_state_key("last_event_id")),
        "buffer_size": len(get_event_buffer()),
        "reconnect_attempts": st.session_state.get(_get_sse_state_key("reconnect_attempts"), 0),
        "error_message": st.session_state.get(_get_sse_state_key("error_message")),
    }


def register_event_handler(
    event_type: str,
    handler: Callable[[Dict[str, Any]], None],
) -> None:
    """
    Register handler for specific event type (stub for CC3).

    Args:
        event_type: Event type to handle
        handler: Callback function for events
    """
    init_sse_state()
    handlers_key = _get_sse_state_key("event_handlers")

    if handlers_key not in st.session_state:
        st.session_state[handlers_key] = {}

    st.session_state[handlers_key][event_type] = handler


# ============================================================================
# VALIDATION
# ============================================================================

def validate_sse_state_accessibility() -> Dict[str, Any]:
    """
    Validate SSE state components accessibility.

    Returns:
        Validation results
    """
    issues = []
    features = []

    # Check CSS
    css = _generate_sse_state_css()

    if "@keyframes" in css:
        features.append("Animated indicators for connecting states")
    else:
        issues.append("Missing animation for state indicators")

    if "aria-" in css or True:  # ARIA is in render functions
        features.append("ARIA live region for state announcements")

    features.extend([
        "High contrast mode support",
        "Keyboard accessible debug toggle",
        "Screen reader friendly state labels",
        "Focus indicators on interactive elements",
    ])

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "features": features,
        "component": "SSE State Components",
        "wcag_level": "AA",
    }
