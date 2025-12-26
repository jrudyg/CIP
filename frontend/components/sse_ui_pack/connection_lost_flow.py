"""
SSE Connection Lost UI Flow
P7.CC2.01 - Task 1

Provides:
- Auto-reconnect UX with progress indicator
- Replay mode UX with sync status
- Degraded-mode indicators for partial functionality

CIP Protocol: CC2 implementation for P7 connection resilience.
"""

import streamlit as st
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from components.color_tokens import get_token, is_high_contrast_mode, inject_color_tokens
from components.a11y_utils import get_aria_attrs, format_aria_attrs


# ============================================================================
# CONFIGURATION
# ============================================================================

class ConnectionLostReason(Enum):
    """Reasons for connection loss."""
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    MANUAL_DISCONNECT = "manual_disconnect"
    UNKNOWN = "unknown"


class DegradedModeLevel(Enum):
    """Levels of degraded operation."""
    NONE = "none"           # Full functionality
    PARTIAL = "partial"     # Some features unavailable
    READONLY = "readonly"   # Read-only mode
    OFFLINE = "offline"     # Fully offline


@dataclass
class ConnectionLostConfig:
    """Configuration for connection lost UI."""
    max_reconnect_attempts: int = 5
    reconnect_delay_ms: int = 2000
    reconnect_backoff_multiplier: float = 1.5
    show_technical_details: bool = False
    enable_manual_reconnect: bool = True
    degraded_mode_threshold: int = 3  # Attempts before degraded mode


@dataclass
class ReconnectState:
    """State for reconnection process."""
    is_reconnecting: bool = False
    attempt_number: int = 0
    last_attempt_time: Optional[str] = None
    next_retry_ms: int = 2000
    reason: ConnectionLostReason = ConnectionLostReason.UNKNOWN
    error_message: Optional[str] = None


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_conn_lost_key(suffix: str) -> str:
    """Get session state key for connection lost flow."""
    return f"_cip_conn_lost_{suffix}"


def init_connection_lost_state() -> None:
    """Initialize connection lost state."""
    defaults = {
        "is_connection_lost": False,
        "reconnect_attempt": 0,
        "max_attempts": 5,
        "last_disconnect_time": None,
        "last_reconnect_attempt": None,
        "next_retry_delay": 2000,
        "reason": ConnectionLostReason.UNKNOWN.value,
        "error_message": None,
        "is_replay_mode": False,
        "replay_progress": 0,
        "replay_total": 0,
        "degraded_mode": DegradedModeLevel.NONE.value,
        "degraded_features": [],
        "user_dismissed_banner": False,
    }

    for key, default in defaults.items():
        full_key = _get_conn_lost_key(key)
        if full_key not in st.session_state:
            st.session_state[full_key] = default


def get_connection_lost_state() -> Dict[str, Any]:
    """Get current connection lost state."""
    init_connection_lost_state()

    return {
        "is_connection_lost": st.session_state.get(_get_conn_lost_key("is_connection_lost"), False),
        "reconnect_attempt": st.session_state.get(_get_conn_lost_key("reconnect_attempt"), 0),
        "max_attempts": st.session_state.get(_get_conn_lost_key("max_attempts"), 5),
        "last_disconnect_time": st.session_state.get(_get_conn_lost_key("last_disconnect_time")),
        "next_retry_delay": st.session_state.get(_get_conn_lost_key("next_retry_delay"), 2000),
        "reason": st.session_state.get(_get_conn_lost_key("reason"), "unknown"),
        "error_message": st.session_state.get(_get_conn_lost_key("error_message")),
        "is_replay_mode": st.session_state.get(_get_conn_lost_key("is_replay_mode"), False),
        "replay_progress": st.session_state.get(_get_conn_lost_key("replay_progress"), 0),
        "replay_total": st.session_state.get(_get_conn_lost_key("replay_total"), 0),
        "degraded_mode": st.session_state.get(_get_conn_lost_key("degraded_mode"), "none"),
        "degraded_features": st.session_state.get(_get_conn_lost_key("degraded_features"), []),
    }


def set_connection_lost(
    reason: ConnectionLostReason = ConnectionLostReason.UNKNOWN,
    error_message: Optional[str] = None,
) -> None:
    """Set connection as lost."""
    init_connection_lost_state()
    st.session_state[_get_conn_lost_key("is_connection_lost")] = True
    st.session_state[_get_conn_lost_key("last_disconnect_time")] = datetime.now().isoformat()
    st.session_state[_get_conn_lost_key("reason")] = reason.value
    st.session_state[_get_conn_lost_key("error_message")] = error_message
    st.session_state[_get_conn_lost_key("user_dismissed_banner")] = False


def set_reconnecting(attempt: int, next_delay_ms: int) -> None:
    """Set reconnection in progress."""
    init_connection_lost_state()
    st.session_state[_get_conn_lost_key("reconnect_attempt")] = attempt
    st.session_state[_get_conn_lost_key("last_reconnect_attempt")] = datetime.now().isoformat()
    st.session_state[_get_conn_lost_key("next_retry_delay")] = next_delay_ms


def set_reconnected() -> None:
    """Set connection as restored."""
    init_connection_lost_state()
    st.session_state[_get_conn_lost_key("is_connection_lost")] = False
    st.session_state[_get_conn_lost_key("reconnect_attempt")] = 0
    st.session_state[_get_conn_lost_key("degraded_mode")] = DegradedModeLevel.NONE.value
    st.session_state[_get_conn_lost_key("degraded_features")] = []


def set_replay_mode(enabled: bool, total_events: int = 0) -> None:
    """Set replay mode state."""
    init_connection_lost_state()
    st.session_state[_get_conn_lost_key("is_replay_mode")] = enabled
    st.session_state[_get_conn_lost_key("replay_total")] = total_events
    st.session_state[_get_conn_lost_key("replay_progress")] = 0


def update_replay_progress(processed: int) -> None:
    """Update replay progress."""
    st.session_state[_get_conn_lost_key("replay_progress")] = processed


def set_degraded_mode(level: DegradedModeLevel, unavailable_features: list = None) -> None:
    """Set degraded mode level."""
    init_connection_lost_state()
    st.session_state[_get_conn_lost_key("degraded_mode")] = level.value
    st.session_state[_get_conn_lost_key("degraded_features")] = unavailable_features or []


# ============================================================================
# CSS STYLING
# ============================================================================

def _generate_connection_lost_css() -> str:
    """Generate CSS for connection lost UI components."""
    high_contrast = is_high_contrast_mode()

    # Get tokens
    bg_primary = get_token("bg-primary")
    bg_secondary = get_token("bg-secondary")
    text_primary = get_token("text-primary")
    text_muted = get_token("text-muted")
    border_default = get_token("border-default")
    error_color = get_token("accent-error")
    warning_color = get_token("accent-warning")
    success_color = get_token("accent-success")
    accent_primary = get_token("accent-primary")

    border_width = "2px" if high_contrast else "1px"

    return f"""
<style>
/* ============================================================================
   CONNECTION LOST UI FLOW
   P7.CC2.01 - Task 1: Connection Resilience
   ============================================================================ */

/* Connection Lost Banner */
.cip-conn-lost-banner {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
    border: {border_width} solid {error_color};
    border-radius: 8px;
    margin-bottom: 16px;
}}

.cip-conn-lost-banner.warning {{
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05));
    border-color: {warning_color};
}}

.cip-conn-lost-icon {{
    font-size: 24px;
    flex-shrink: 0;
}}

.cip-conn-lost-content {{
    flex: 1;
}}

.cip-conn-lost-title {{
    font-size: 14px;
    font-weight: 600;
    color: {text_primary};
    margin-bottom: 4px;
}}

.cip-conn-lost-message {{
    font-size: 12px;
    color: {text_muted};
}}

.cip-conn-lost-actions {{
    display: flex;
    gap: 8px;
}}

/* Reconnect Progress */
.cip-reconnect-progress {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: {bg_secondary};
    border: {border_width} solid {border_default};
    border-radius: 8px;
    margin-bottom: 12px;
}}

.cip-reconnect-spinner {{
    width: 20px;
    height: 20px;
    border: 2px solid {border_default};
    border-top-color: {accent_primary};
    border-radius: 50%;
    animation: cip-spin 1s linear infinite;
}}

@keyframes cip-spin {{
    to {{ transform: rotate(360deg); }}
}}

.cip-reconnect-info {{
    flex: 1;
}}

.cip-reconnect-status {{
    font-size: 13px;
    font-weight: 500;
    color: {text_primary};
}}

.cip-reconnect-detail {{
    font-size: 11px;
    color: {text_muted};
    margin-top: 2px;
}}

.cip-reconnect-attempt {{
    font-size: 12px;
    color: {text_muted};
    font-family: monospace;
}}

/* Replay Mode Indicator */
.cip-replay-indicator {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05));
    border: {border_width} solid {accent_primary};
    border-radius: 8px;
    margin-bottom: 12px;
}}

.cip-replay-icon {{
    font-size: 18px;
    animation: cip-pulse-replay 1.5s ease-in-out infinite;
}}

@keyframes cip-pulse-replay {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}

.cip-replay-content {{
    flex: 1;
}}

.cip-replay-title {{
    font-size: 13px;
    font-weight: 500;
    color: {text_primary};
}}

.cip-replay-progress-bar {{
    height: 4px;
    background: {border_default};
    border-radius: 2px;
    margin-top: 6px;
    overflow: hidden;
}}

.cip-replay-progress-fill {{
    height: 100%;
    background: {accent_primary};
    border-radius: 2px;
    transition: width 0.3s ease;
}}

.cip-replay-stats {{
    font-size: 11px;
    color: {text_muted};
    font-family: monospace;
}}

/* Degraded Mode Banner */
.cip-degraded-banner {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(245, 158, 11, 0.04));
    border: {border_width} solid {warning_color};
    border-radius: 8px;
    margin-bottom: 16px;
}}

.cip-degraded-banner.offline {{
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.04));
    border-color: {error_color};
}}

.cip-degraded-icon {{
    font-size: 20px;
    flex-shrink: 0;
}}

.cip-degraded-content {{
    flex: 1;
}}

.cip-degraded-title {{
    font-size: 13px;
    font-weight: 600;
    color: {text_primary};
    margin-bottom: 4px;
}}

.cip-degraded-message {{
    font-size: 12px;
    color: {text_muted};
    margin-bottom: 8px;
}}

.cip-degraded-features {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}}

.cip-degraded-feature {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    font-size: 11px;
    color: {text_muted};
}}

.cip-degraded-feature-icon {{
    font-size: 10px;
}}

/* Success Banner (Connection Restored) */
.cip-conn-restored {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
    border: {border_width} solid {success_color};
    border-radius: 8px;
    margin-bottom: 12px;
    animation: cip-fade-in 0.3s ease;
}}

@keyframes cip-fade-in {{
    from {{ opacity: 0; transform: translateY(-10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.cip-conn-restored-icon {{
    font-size: 18px;
    color: {success_color};
}}

.cip-conn-restored-text {{
    font-size: 13px;
    font-weight: 500;
    color: {text_primary};
}}

/* Print Styles */
@media print {{
    .cip-conn-lost-banner,
    .cip-reconnect-progress,
    .cip-replay-indicator,
    .cip-degraded-banner {{
        display: none;
    }}
}}
</style>
"""


def inject_connection_lost_css() -> None:
    """Inject connection lost CSS into page."""
    st.markdown(_generate_connection_lost_css(), unsafe_allow_html=True)


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_connection_lost_banner(
    config: Optional[ConnectionLostConfig] = None,
    show_actions: bool = True,
) -> bool:
    """
    Render connection lost banner.

    Args:
        config: Optional configuration
        show_actions: Whether to show action buttons

    Returns:
        True if banner was rendered
    """
    init_connection_lost_state()
    inject_color_tokens()
    inject_connection_lost_css()

    state = get_connection_lost_state()

    if not state["is_connection_lost"]:
        return False

    if st.session_state.get(_get_conn_lost_key("user_dismissed_banner"), False):
        return False

    config = config or ConnectionLostConfig()

    # Determine severity
    is_critical = state["reconnect_attempt"] >= config.max_reconnect_attempts
    banner_class = "" if is_critical else "warning"
    icon = "🔴" if is_critical else "⚠️"

    # Build message
    reason_messages = {
        "network_error": "Network connection lost",
        "server_error": "Server unavailable",
        "timeout": "Connection timed out",
        "manual_disconnect": "Manually disconnected",
        "unknown": "Connection interrupted",
    }

    title = reason_messages.get(state["reason"], "Connection lost")
    message = state["error_message"] or "Attempting to reconnect..."

    if state["reconnect_attempt"] > 0:
        message = f"Reconnection attempt {state['reconnect_attempt']}/{state['max_attempts']}"

    # ARIA attributes
    aria_attrs = get_aria_attrs(
        "alert",
        live="assertive",
        atomic="true",
    )
    aria_str = format_aria_attrs(aria_attrs)

    st.markdown(f"""
    <div class="cip-conn-lost-banner {banner_class}" {aria_str}>
        <span class="cip-conn-lost-icon">{icon}</span>
        <div class="cip-conn-lost-content">
            <div class="cip-conn-lost-title">{title}</div>
            <div class="cip-conn-lost-message">{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons (using Streamlit buttons for interactivity)
    if show_actions and config.enable_manual_reconnect:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Retry Now", key="conn_retry_btn"):
                st.session_state[_get_conn_lost_key("reconnect_attempt")] = 0
                st.rerun()
        with col2:
            if st.button("✕ Dismiss", key="conn_dismiss_btn"):
                st.session_state[_get_conn_lost_key("user_dismissed_banner")] = True
                st.rerun()

    return True


def render_reconnect_progress(
    attempt: int,
    max_attempts: int,
    next_retry_seconds: float = 2.0,
) -> None:
    """
    Render reconnection progress indicator.

    Args:
        attempt: Current attempt number
        max_attempts: Maximum attempts
        next_retry_seconds: Seconds until next retry
    """
    inject_connection_lost_css()

    aria_attrs = get_aria_attrs(
        "status",
        live="polite",
        label="Reconnection progress",
    )
    aria_str = format_aria_attrs(aria_attrs)

    st.markdown(f"""
    <div class="cip-reconnect-progress" {aria_str}>
        <div class="cip-reconnect-spinner"></div>
        <div class="cip-reconnect-info">
            <div class="cip-reconnect-status">Reconnecting to server...</div>
            <div class="cip-reconnect-detail">Next retry in {next_retry_seconds:.1f}s</div>
        </div>
        <div class="cip-reconnect-attempt">{attempt}/{max_attempts}</div>
    </div>
    """, unsafe_allow_html=True)


def render_replay_mode_indicator(
    events_processed: int,
    events_total: int,
    from_sequence: Optional[int] = None,
) -> None:
    """
    Render replay mode indicator with progress.

    Args:
        events_processed: Number of events replayed
        events_total: Total events to replay
        from_sequence: Starting sequence number
    """
    inject_connection_lost_css()

    progress_pct = (events_processed / events_total * 100) if events_total > 0 else 0

    aria_attrs = get_aria_attrs(
        "status",
        live="polite",
        label=f"Replaying events: {events_processed} of {events_total}",
    )
    aria_str = format_aria_attrs(aria_attrs)

    seq_info = f" from #{from_sequence}" if from_sequence else ""

    st.markdown(f"""
    <div class="cip-replay-indicator" {aria_str}>
        <span class="cip-replay-icon">🔄</span>
        <div class="cip-replay-content">
            <div class="cip-replay-title">Syncing missed events{seq_info}</div>
            <div class="cip-replay-progress-bar">
                <div class="cip-replay-progress-fill" style="width: {progress_pct}%"></div>
            </div>
        </div>
        <div class="cip-replay-stats">{events_processed}/{events_total}</div>
    </div>
    """, unsafe_allow_html=True)


def render_degraded_mode_banner(
    level: DegradedModeLevel,
    unavailable_features: list = None,
    custom_message: Optional[str] = None,
) -> None:
    """
    Render degraded mode banner.

    Args:
        level: Degraded mode level
        unavailable_features: List of unavailable feature names
        custom_message: Optional custom message
    """
    if level == DegradedModeLevel.NONE:
        return

    inject_connection_lost_css()

    level_config = {
        DegradedModeLevel.PARTIAL: {
            "icon": "⚡",
            "title": "Limited Functionality",
            "message": "Some features are temporarily unavailable.",
            "class": "",
        },
        DegradedModeLevel.READONLY: {
            "icon": "👁️",
            "title": "Read-Only Mode",
            "message": "Changes cannot be saved until connection is restored.",
            "class": "",
        },
        DegradedModeLevel.OFFLINE: {
            "icon": "📴",
            "title": "Offline Mode",
            "message": "Working with cached data. Changes will sync when online.",
            "class": "offline",
        },
    }

    config = level_config.get(level, level_config[DegradedModeLevel.PARTIAL])
    message = custom_message or config["message"]

    # Build features list
    features_html = ""
    if unavailable_features:
        features_items = "".join([
            f'<span class="cip-degraded-feature"><span class="cip-degraded-feature-icon">✕</span>{f}</span>'
            for f in unavailable_features
        ])
        features_html = f'<div class="cip-degraded-features">{features_items}</div>'

    aria_attrs = get_aria_attrs(
        "alert",
        live="polite",
    )
    aria_str = format_aria_attrs(aria_attrs)

    st.markdown(f"""
    <div class="cip-degraded-banner {config['class']}" {aria_str}>
        <span class="cip-degraded-icon">{config['icon']}</span>
        <div class="cip-degraded-content">
            <div class="cip-degraded-title">{config['title']}</div>
            <div class="cip-degraded-message">{message}</div>
            {features_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_connection_restored_toast() -> None:
    """Render connection restored success message."""
    inject_connection_lost_css()

    st.markdown("""
    <div class="cip-conn-restored" role="status" aria-live="polite">
        <span class="cip-conn-restored-icon">✓</span>
        <span class="cip-conn-restored-text">Connection restored</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# CC3 INTEGRATION
# ============================================================================

def get_connection_lost_state_for_binder() -> Dict[str, Any]:
    """
    Get connection lost state for CC3 binder.

    Returns:
        Dictionary with connection lost state
    """
    state = get_connection_lost_state()

    return {
        "is_connection_lost": state["is_connection_lost"],
        "reconnect_attempt": state["reconnect_attempt"],
        "max_attempts": state["max_attempts"],
        "reason": state["reason"],
        "is_replay_mode": state["is_replay_mode"],
        "replay_progress": state["replay_progress"],
        "replay_total": state["replay_total"],
        "degraded_mode": state["degraded_mode"],
        "degraded_features": state["degraded_features"],
        "can_retry": state["reconnect_attempt"] < state["max_attempts"],
    }
