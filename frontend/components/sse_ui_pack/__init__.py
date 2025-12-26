"""
SSE UI Pack - Phase 7 Frontend Streaming Components
P7.CC2.01_FRONTEND_SSE_UI_PACK

Provides:
- Connection Lost UI Flow (auto-reconnect, replay, degraded-mode)
- SSE Diagnostics Tray v1
- State Schema v2 (extended state management)
- A11y Streaming Utilities

CIP Protocol: CC2 implementation for P7 streaming backend.
"""

from components.sse_ui_pack.connection_lost_flow import (
    ConnectionLostConfig,
    render_connection_lost_banner,
    render_reconnect_progress,
    render_replay_mode_indicator,
    render_degraded_mode_banner,
    get_connection_lost_state,
)

from components.sse_ui_pack.diagnostics_tray import (
    DiagnosticsTrayConfig,
    render_diagnostics_tray,
    render_diagnostics_toggle,
    get_diagnostics_data,
)

from components.sse_ui_pack.state_schema_v2 import (
    SSEStateV2,
    ReconnectionRecord,
    SequenceGap,
    init_state_v2,
    get_state_v2,
    update_state_v2,
    record_reconnection,
    record_sequence_gap,
    get_keepalive_lag,
)

from components.sse_ui_pack.a11y_streaming import (
    StreamingA11yConfig,
    A11Y_STREAMING_CHECKLIST,
    get_aria_live_policy,
    should_announce_update,
    get_focus_stability_rules,
    get_scroll_independence_css,
    validate_streaming_a11y,
)

__all__ = [
    # Connection Lost Flow
    "ConnectionLostConfig",
    "render_connection_lost_banner",
    "render_reconnect_progress",
    "render_replay_mode_indicator",
    "render_degraded_mode_banner",
    "get_connection_lost_state",
    # Diagnostics Tray
    "DiagnosticsTrayConfig",
    "render_diagnostics_tray",
    "render_diagnostics_toggle",
    "get_diagnostics_data",
    # State Schema v2
    "SSEStateV2",
    "ReconnectionRecord",
    "SequenceGap",
    "init_state_v2",
    "get_state_v2",
    "update_state_v2",
    "record_reconnection",
    "record_sequence_gap",
    "get_keepalive_lag",
    # A11y Streaming
    "StreamingA11yConfig",
    "A11Y_STREAMING_CHECKLIST",
    "get_aria_live_policy",
    "should_announce_update",
    "get_focus_stability_rules",
    "get_scroll_independence_css",
    "validate_streaming_a11y",
]

__version__ = "1.0.0"
__phase__ = "P7"
