"""
P7 Connection State Indicator
P7.S1 CC2 Task 1

Visual representation of P7 Connection States:
- ACTIVE: Connected and receiving events
- STALE: Connected but no recent keepalive
- RECONNECTING: Attempting to restore connection
- TERMINATED: Connection closed/failed

Uses High-Contrast tokens (P6.C2.T1) and implements
P7 Degraded-Mode UX Playbook visual cues.

CIP Protocol: CC2 implementation for P7 streaming UI.
"""

import streamlit as st
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from components.color_tokens import get_token, is_high_contrast_mode, inject_color_tokens
from components.a11y_utils import get_aria_attrs, format_aria_attrs, generate_focus_css, FocusConfig


# ============================================================================
# P7 CONNECTION STATES
# ============================================================================

class P7ConnectionState(Enum):
    """
    P7 Connection States per P7 Degraded-Mode UX Playbook.

    State transitions:
    ACTIVE <-> STALE <-> RECONNECTING -> TERMINATED
                |                            ^
                +----------------------------+
    """
    ACTIVE = "active"           # Connected, receiving events
    STALE = "stale"             # Connected, no recent keepalive
    RECONNECTING = "reconnecting"  # Attempting reconnection
    TERMINATED = "terminated"   # Connection closed/failed


@dataclass
class ConnectionIndicatorConfig:
    """Configuration for connection indicator."""
    # Display options
    show_label: bool = True
    show_details: bool = True
    compact_mode: bool = False

    # Timing thresholds (ms)
    stale_threshold_ms: int = 45000      # 45s without keepalive = STALE
    terminated_threshold_ms: int = 120000  # 120s = TERMINATED

    # Animation
    animate_reconnecting: bool = True
    pulse_on_active: bool = False

    # Accessibility
    announce_state_changes: bool = True


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_indicator_key(suffix: str) -> str:
    """Get session state key for connection indicator."""
    return f"_cip_p7_conn_{suffix}"


def init_connection_indicator_state() -> None:
    """Initialize connection indicator state."""
    defaults = {
        "current_state": P7ConnectionState.ACTIVE.value,
        "previous_state": None,
        "last_keepalive_at": None,
        "last_event_at": None,
        "reconnect_attempt": 0,
        "max_reconnect_attempts": 5,
        "last_sequence_id": 0,
        "connection_start_time": None,
        "termination_reason": None,
        "state_changed_at": datetime.now().isoformat(),
    }

    for key, default in defaults.items():
        full_key = _get_indicator_key(key)
        if full_key not in st.session_state:
            st.session_state[full_key] = default


def get_connection_state() -> P7ConnectionState:
    """Get current P7 connection state."""
    init_connection_indicator_state()
    state_str = st.session_state.get(_get_indicator_key("current_state"), "active")
    try:
        return P7ConnectionState(state_str)
    except ValueError:
        return P7ConnectionState.ACTIVE


def set_connection_state(
    state: P7ConnectionState,
    reason: Optional[str] = None,
) -> None:
    """
    Set P7 connection state.

    Args:
        state: New connection state
        reason: Optional reason for state change (for TERMINATED)
    """
    init_connection_indicator_state()

    current = st.session_state.get(_get_indicator_key("current_state"))

    # Store previous state for transition tracking
    if current != state.value:
        st.session_state[_get_indicator_key("previous_state")] = current
        st.session_state[_get_indicator_key("state_changed_at")] = datetime.now().isoformat()

    st.session_state[_get_indicator_key("current_state")] = state.value

    if state == P7ConnectionState.TERMINATED and reason:
        st.session_state[_get_indicator_key("termination_reason")] = reason

    if state == P7ConnectionState.ACTIVE:
        st.session_state[_get_indicator_key("reconnect_attempt")] = 0
        st.session_state[_get_indicator_key("termination_reason")] = None


def record_keepalive() -> None:
    """Record receipt of keepalive signal."""
    init_connection_indicator_state()
    st.session_state[_get_indicator_key("last_keepalive_at")] = datetime.now().isoformat()

    # If we were STALE, transition back to ACTIVE
    if get_connection_state() == P7ConnectionState.STALE:
        set_connection_state(P7ConnectionState.ACTIVE)


def record_event(sequence_id: int) -> None:
    """Record receipt of an SSE event."""
    init_connection_indicator_state()
    st.session_state[_get_indicator_key("last_event_at")] = datetime.now().isoformat()
    st.session_state[_get_indicator_key("last_sequence_id")] = sequence_id


def increment_reconnect_attempt() -> int:
    """Increment reconnection attempt counter."""
    init_connection_indicator_state()
    attempt = st.session_state.get(_get_indicator_key("reconnect_attempt"), 0) + 1
    st.session_state[_get_indicator_key("reconnect_attempt")] = attempt
    return attempt


def get_indicator_metrics() -> Dict[str, Any]:
    """Get all indicator metrics."""
    init_connection_indicator_state()

    return {
        "state": get_connection_state().value,
        "last_keepalive_at": st.session_state.get(_get_indicator_key("last_keepalive_at")),
        "last_event_at": st.session_state.get(_get_indicator_key("last_event_at")),
        "last_sequence_id": st.session_state.get(_get_indicator_key("last_sequence_id"), 0),
        "reconnect_attempt": st.session_state.get(_get_indicator_key("reconnect_attempt"), 0),
        "max_reconnect_attempts": st.session_state.get(_get_indicator_key("max_reconnect_attempts"), 5),
        "state_changed_at": st.session_state.get(_get_indicator_key("state_changed_at")),
        "termination_reason": st.session_state.get(_get_indicator_key("termination_reason")),
    }


# ============================================================================
# CSS STYLING (P6.C2.T1 HIGH-CONTRAST TOKENS)
# ============================================================================

def _generate_indicator_css() -> str:
    """Generate CSS for connection indicator using High-Contrast tokens."""
    high_contrast = is_high_contrast_mode()

    # P6.C2.T1 High-Contrast Tokens
    bg_primary = get_token("bg-primary")
    bg_secondary = get_token("bg-secondary")
    text_primary = get_token("text-primary")
    text_muted = get_token("text-muted")
    border_default = get_token("border-default")
    border_strong = get_token("border-strong")

    # State colors
    accent_success = get_token("accent-success")    # ACTIVE
    accent_warning = get_token("accent-warning")    # STALE
    accent_primary = get_token("accent-primary")    # RECONNECTING
    accent_error = get_token("accent-error")        # TERMINATED

    # High-contrast adjustments
    border_width = "2px" if high_contrast else "1px"
    indicator_size = "12px" if high_contrast else "10px"
    glow_intensity = "8px" if high_contrast else "6px"

    # Focus configuration for accessibility
    focus_config = FocusConfig(
        outline_width="2px" if not high_contrast else "3px",
        outline_color=get_token("border-focus"),
        high_contrast_width="3px",
        high_contrast_color=get_token("accent-primary"),
    )
    focus_css = generate_focus_css(".cip-conn-indicator", focus_config, high_contrast)

    return f"""
<style>
/* ============================================================================
   P7 CONNECTION STATE INDICATOR
   P7.S1 CC2 Task 1 - Uses P6.C2.T1 High-Contrast Tokens
   ============================================================================ */

/* Main Indicator Container */
.cip-conn-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    background: {bg_secondary};
    border: {border_width} solid {border_default};
    border-radius: 24px;
    font-size: 13px;
    color: {text_primary};
    cursor: default;
    transition: all 0.2s ease;
}}

.cip-conn-indicator:hover {{
    border-color: {border_strong};
}}

/* Compact Mode */
.cip-conn-indicator.compact {{
    padding: 5px 10px;
    gap: 6px;
    font-size: 11px;
    border-radius: 16px;
}}

/* State Indicator Dot */
.cip-conn-dot {{
    width: {indicator_size};
    height: {indicator_size};
    border-radius: 50%;
    flex-shrink: 0;
    transition: all 0.3s ease;
}}

/* ACTIVE State - Green with optional pulse */
.cip-conn-dot.active {{
    background: {accent_success};
    box-shadow: 0 0 {glow_intensity} {accent_success};
}}

.cip-conn-dot.active.pulse {{
    animation: cip-pulse-active 2s ease-in-out infinite;
}}

@keyframes cip-pulse-active {{
    0%, 100% {{
        box-shadow: 0 0 {glow_intensity} {accent_success};
        transform: scale(1);
    }}
    50% {{
        box-shadow: 0 0 12px {accent_success};
        transform: scale(1.1);
    }}
}}

/* STALE State - Yellow/Amber warning */
.cip-conn-dot.stale {{
    background: {accent_warning};
    box-shadow: 0 0 {glow_intensity} {accent_warning};
    animation: cip-blink-stale 1.5s ease-in-out infinite;
}}

@keyframes cip-blink-stale {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}

/* RECONNECTING State - Blue with spinner effect */
.cip-conn-dot.reconnecting {{
    background: {accent_primary};
    box-shadow: 0 0 {glow_intensity} {accent_primary};
    animation: cip-spin-reconnect 1s linear infinite;
}}

@keyframes cip-spin-reconnect {{
    0% {{
        transform: scale(1);
        box-shadow: 0 0 {glow_intensity} {accent_primary};
    }}
    50% {{
        transform: scale(0.8);
        box-shadow: 0 0 12px {accent_primary};
    }}
    100% {{
        transform: scale(1);
        box-shadow: 0 0 {glow_intensity} {accent_primary};
    }}
}}

/* TERMINATED State - Red, static */
.cip-conn-dot.terminated {{
    background: {accent_error};
    box-shadow: none;
    opacity: 0.8;
}}

/* State Label */
.cip-conn-label {{
    font-weight: 500;
    letter-spacing: 0.3px;
}}

.cip-conn-label.active {{ color: {accent_success}; }}
.cip-conn-label.stale {{ color: {accent_warning}; }}
.cip-conn-label.reconnecting {{ color: {accent_primary}; }}
.cip-conn-label.terminated {{ color: {accent_error}; }}

/* Details Section */
.cip-conn-details {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 8px;
    border-left: 1px solid {border_default};
    font-size: 11px;
    color: {text_muted};
}}

.cip-conn-detail-item {{
    display: flex;
    align-items: center;
    gap: 4px;
}}

.cip-conn-detail-value {{
    font-family: monospace;
    font-weight: 500;
}}

/* Reconnection Counter */
.cip-conn-reconnect-count {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    background: {bg_primary};
    border: 1px solid {border_default};
    border-radius: 10px;
    font-size: 10px;
    font-weight: 600;
    color: {text_muted};
}}

/* State-specific border colors */
.cip-conn-indicator.state-active {{
    border-color: {accent_success};
}}

.cip-conn-indicator.state-stale {{
    border-color: {accent_warning};
}}

.cip-conn-indicator.state-reconnecting {{
    border-color: {accent_primary};
}}

.cip-conn-indicator.state-terminated {{
    border-color: {accent_error};
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), {bg_secondary});
}}

/* High Contrast Mode Enhancements */
.cip-conn-indicator.high-contrast {{
    border-width: 2px;
}}

.cip-conn-indicator.high-contrast .cip-conn-dot {{
    width: 14px;
    height: 14px;
}}

.cip-conn-indicator.high-contrast .cip-conn-label {{
    font-weight: 600;
}}

/* Focus Styles (Accessibility) */
{focus_css}

/* Print Styles */
@media print {{
    .cip-conn-indicator {{
        border: 1px solid #333;
        background: white;
    }}

    .cip-conn-dot {{
        box-shadow: none;
        animation: none;
    }}
}}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {{
    .cip-conn-dot {{
        animation: none !important;
    }}

    .cip-conn-indicator {{
        transition: none;
    }}
}}
</style>
"""


def inject_indicator_css() -> None:
    """Inject connection indicator CSS into page."""
    st.markdown(_generate_indicator_css(), unsafe_allow_html=True)


# ============================================================================
# UI COMPONENT
# ============================================================================

def render_connection_indicator(
    config: Optional[ConnectionIndicatorConfig] = None,
) -> P7ConnectionState:
    """
    Render P7 Connection State Indicator.

    Visual representation per P7 Degraded-Mode UX Playbook:
    - ACTIVE: Green dot with glow, "Connected" label
    - STALE: Amber dot blinking, "Stale" label
    - RECONNECTING: Blue dot pulsing, "Reconnecting" label + attempt count
    - TERMINATED: Red dot static, "Disconnected" label

    Args:
        config: Optional configuration

    Returns:
        Current P7ConnectionState
    """
    init_connection_indicator_state()
    inject_color_tokens()
    inject_indicator_css()

    config = config or ConnectionIndicatorConfig()
    state = get_connection_state()
    metrics = get_indicator_metrics()
    high_contrast = is_high_contrast_mode()

    # State-specific configuration
    state_config = {
        P7ConnectionState.ACTIVE: {
            "label": "Connected",
            "dot_class": "active",
            "border_class": "state-active",
        },
        P7ConnectionState.STALE: {
            "label": "Stale",
            "dot_class": "stale",
            "border_class": "state-stale",
        },
        P7ConnectionState.RECONNECTING: {
            "label": "Reconnecting",
            "dot_class": "reconnecting",
            "border_class": "state-reconnecting",
        },
        P7ConnectionState.TERMINATED: {
            "label": "Disconnected",
            "dot_class": "terminated",
            "border_class": "state-terminated",
        },
    }

    cfg = state_config.get(state, state_config[P7ConnectionState.ACTIVE])

    # Build CSS classes
    classes = ["cip-conn-indicator", cfg["border_class"]]
    if config.compact_mode:
        classes.append("compact")
    if high_contrast:
        classes.append("high-contrast")

    # Dot classes
    dot_classes = ["cip-conn-dot", cfg["dot_class"]]
    if config.pulse_on_active and state == P7ConnectionState.ACTIVE:
        dot_classes.append("pulse")
    if not config.animate_reconnecting and state == P7ConnectionState.RECONNECTING:
        dot_classes = ["cip-conn-dot", cfg["dot_class"]]  # Remove animation

    # Build label HTML
    label_html = ""
    if config.show_label:
        label_html = f'<span class="cip-conn-label {cfg["dot_class"]}">{cfg["label"]}</span>'

    # Build details HTML
    details_html = ""
    if config.show_details and not config.compact_mode:
        details_items = []

        if state == P7ConnectionState.RECONNECTING:
            attempt = metrics["reconnect_attempt"]
            max_attempts = metrics["max_reconnect_attempts"]
            details_items.append(
                f'<span class="cip-conn-reconnect-count">{attempt}/{max_attempts}</span>'
            )

        if metrics["last_sequence_id"] > 0:
            details_items.append(
                f'<span class="cip-conn-detail-item">'
                f'<span>seq:</span>'
                f'<span class="cip-conn-detail-value">{metrics["last_sequence_id"]}</span>'
                f'</span>'
            )

        if details_items:
            details_html = f'<div class="cip-conn-details">{"".join(details_items)}</div>'

    # ARIA attributes for accessibility
    aria_label = f"Connection status: {cfg['label']}"
    if state == P7ConnectionState.RECONNECTING:
        aria_label += f", attempt {metrics['reconnect_attempt']} of {metrics['max_reconnect_attempts']}"
    if state == P7ConnectionState.TERMINATED and metrics["termination_reason"]:
        aria_label += f", reason: {metrics['termination_reason']}"

    aria_attrs = get_aria_attrs(
        "status",
        live="polite" if config.announce_state_changes else "off",
        label=aria_label,
    )
    aria_str = format_aria_attrs(aria_attrs)

    st.markdown(f"""
    <div class="{' '.join(classes)}" {aria_str} tabindex="0">
        <span class="{' '.join(dot_classes)}"></span>
        {label_html}
        {details_html}
    </div>
    """, unsafe_allow_html=True)

    return state


def render_connection_indicator_minimal() -> P7ConnectionState:
    """Render minimal connection indicator (dot only)."""
    return render_connection_indicator(ConnectionIndicatorConfig(
        show_label=False,
        show_details=False,
        compact_mode=True,
    ))


# ============================================================================
# DEGRADED MODE UX HELPERS
# ============================================================================

def check_and_update_state(
    config: Optional[ConnectionIndicatorConfig] = None,
) -> P7ConnectionState:
    """
    Check timing thresholds and update state if needed.

    This implements the P7 Degraded-Mode UX Playbook timing rules:
    - No keepalive for stale_threshold_ms → STALE
    - No keepalive for terminated_threshold_ms → TERMINATED

    Args:
        config: Optional configuration with timing thresholds

    Returns:
        Updated P7ConnectionState
    """
    init_connection_indicator_state()
    config = config or ConnectionIndicatorConfig()

    current_state = get_connection_state()

    # Don't auto-update if already TERMINATED or RECONNECTING
    if current_state in (P7ConnectionState.TERMINATED, P7ConnectionState.RECONNECTING):
        return current_state

    last_keepalive = st.session_state.get(_get_indicator_key("last_keepalive_at"))

    if last_keepalive:
        last_dt = datetime.fromisoformat(last_keepalive)
        elapsed_ms = int((datetime.now() - last_dt).total_seconds() * 1000)

        if elapsed_ms >= config.terminated_threshold_ms:
            set_connection_state(P7ConnectionState.TERMINATED, "Keepalive timeout")
            return P7ConnectionState.TERMINATED
        elif elapsed_ms >= config.stale_threshold_ms:
            set_connection_state(P7ConnectionState.STALE)
            return P7ConnectionState.STALE
        else:
            # Within threshold, ensure ACTIVE
            if current_state == P7ConnectionState.STALE:
                set_connection_state(P7ConnectionState.ACTIVE)
            return P7ConnectionState.ACTIVE

    return current_state


def get_degraded_mode_message(state: P7ConnectionState) -> Optional[str]:
    """
    Get user-facing message for degraded mode states.

    Args:
        state: Current connection state

    Returns:
        User-friendly message or None for ACTIVE state
    """
    messages = {
        P7ConnectionState.STALE:
            "Connection may be unstable. Some updates might be delayed.",
        P7ConnectionState.RECONNECTING:
            "Reconnecting to server. Your work is saved locally.",
        P7ConnectionState.TERMINATED:
            "Connection lost. Please check your network and refresh the page.",
    }
    return messages.get(state)


# ============================================================================
# CC3 INTEGRATION
# ============================================================================

def get_indicator_state_for_binder() -> Dict[str, Any]:
    """
    Get connection indicator state for CC3 data binder.

    Returns:
        Dictionary with indicator state for CC3 integration
    """
    metrics = get_indicator_metrics()
    state = get_connection_state()

    return {
        "state": state.value,
        "is_connected": state == P7ConnectionState.ACTIVE,
        "is_degraded": state in (P7ConnectionState.STALE, P7ConnectionState.RECONNECTING),
        "is_terminated": state == P7ConnectionState.TERMINATED,
        "last_sequence_id": metrics["last_sequence_id"],
        "reconnect_attempt": metrics["reconnect_attempt"],
        "termination_reason": metrics["termination_reason"],
        "state_changed_at": metrics["state_changed_at"],
    }
