"""
CIP Diagnostics Panel

Comprehensive diagnostics page with multiple tabs:
- Overview: System health dashboard
- Backend Logs: Log viewer with filtering
- API History: Recent API calls
- Database: Connection health and table stats
- System Resources: CPU/Memory/Disk usage
- P7 Streaming: SSE streaming diagnostics (original P7 implementation)

CIP Protocol: Enhanced diagnostics for development and monitoring.
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Any, Dict, Optional

# Backend API URL
API_BASE = "http://localhost:5000"

# Page configuration
st.set_page_config(
    page_title="CIP Diagnostics",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Import components (with fallbacks for standalone testing)
try:
    from components.color_tokens import inject_color_tokens, get_token, is_high_contrast_mode
    from components.connection_indicator import (
        render_connection_indicator,
        get_connection_state,
        get_indicator_metrics,
        P7ConnectionState,
        check_and_update_state,
    )
    from components.sse_ui_pack.state_schema_v2 import (
        get_state_v2,
        get_health_summary,
        get_state_v2_for_binder,
    )
    from components.sse_ui_pack.diagnostics_tray import (
        get_diagnostics_data,
    )
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False

# Import DiagnosticsSSEContext for real SSE support (P7.S2)
try:
    from integrations.event_buffer_stub import (
        get_diagnostics_context,
        USE_REAL_SSE,
        DiagnosticsSSEContext,
    )
    DIAG_SSE_AVAILABLE = True
except ImportError:
    DIAG_SSE_AVAILABLE = False
    USE_REAL_SSE = False

# Import Gap Metadata Reporting (P7.S2 Task 8)
try:
    from integrations.sequence_validator_hooks import (
        get_current_gap_report,
        get_gap_statistics,
        clear_all_gaps,
    )
    GAP_HOOKS_AVAILABLE = True
except ImportError:
    GAP_HOOKS_AVAILABLE = False


# ============================================================================
# STYLING
# ============================================================================

def inject_diagnostics_page_css():
    """Inject CSS for diagnostics page."""
    st.markdown("""
    <style>
    /* P7 Diagnostics Page Styling */
    .p7-diag-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0;
        border-bottom: 1px solid #334155;
        margin-bottom: 24px;
    }

    .p7-diag-title {
        font-size: 24px;
        font-weight: 700;
        color: #F1F5F9;
    }

    .p7-diag-subtitle {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .p7-diag-section {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .p7-diag-section-title {
        font-size: 14px;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .p7-diag-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }

    .p7-diag-metric {
        background: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
    }

    .p7-diag-metric-label {
        font-size: 11px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    .p7-diag-metric-value {
        font-size: 24px;
        font-weight: 700;
        font-family: monospace;
        color: #F1F5F9;
    }

    .p7-diag-metric-value.success { color: #22C55E; }
    .p7-diag-metric-value.warning { color: #F59E0B; }
    .p7-diag-metric-value.error { color: #EF4444; }
    .p7-diag-metric-value.info { color: #3B82F6; }

    .p7-diag-metric-detail {
        font-size: 11px;
        color: #64748B;
        margin-top: 6px;
    }

    .p7-diag-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }

    .p7-diag-table th {
        text-align: left;
        padding: 10px 12px;
        background: #0F172A;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #334155;
    }

    .p7-diag-table td {
        padding: 10px 12px;
        color: #F1F5F9;
        border-bottom: 1px solid #1E293B;
    }

    .p7-diag-table tr:hover td {
        background: rgba(59, 130, 246, 0.1);
    }

    .p7-diag-badge {
        display: inline-flex;
        align-items: center;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }

    .p7-diag-badge.healthy { background: rgba(34, 197, 94, 0.2); color: #22C55E; }
    .p7-diag-badge.degraded { background: rgba(245, 158, 11, 0.2); color: #F59E0B; }
    .p7-diag-badge.unhealthy { background: rgba(239, 68, 68, 0.2); color: #EF4444; }

    .p7-diag-timestamp {
        font-family: monospace;
        font-size: 11px;
        color: #64748B;
    }

    .p7-diag-warning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid #F59E0B;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 13px;
        color: #FCD34D;
    }

    .p7-diag-empty {
        text-align: center;
        padding: 24px;
        color: #64748B;
        font-size: 13px;
    }

    /* Health Score Gauge */
    .p7-health-gauge {
        width: 100%;
        height: 8px;
        background: #334155;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 8px;
    }

    .p7-health-gauge-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .p7-health-gauge-fill.healthy { background: #22C55E; }
    .p7-health-gauge-fill.degraded { background: #F59E0B; }
    .p7-health-gauge-fill.unhealthy { background: #EF4444; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# MOCK DATA (for standalone testing)
# ============================================================================

def get_mock_metrics() -> Dict[str, Any]:
    """Get mock metrics when components unavailable."""
    return {
        "connection": {
            "state": "active",
            "last_keepalive_at": datetime.now().isoformat(),
            "last_event_at": datetime.now().isoformat(),
            "last_sequence_id": 1247,
            "reconnect_attempt": 0,
        },
        "state_v2": {
            "total_events_received": 1247,
            "reconnection_count": 2,
            "gaps_detected": 1,
            "gaps_resolved": 1,
            "keepalive_lag_ms": 450,
            "availability_pct": 99.7,
        },
        "health": {
            "health_score": 95,
            "status": "healthy",
        },
        "buffer": {
            "events_count": 15,
            "last_seq": 1247,
            "expected_seq": 1248,
        },
        "gaps": [
            {"expected": 1100, "received": 1105, "gap_size": 5, "resolved": True},
        ],
        "reconnections": [
            {"attempt": 1, "duration_ms": 1200, "success": True, "reason": "network"},
            {"attempt": 2, "duration_ms": 800, "success": True, "reason": "timeout"},
        ],
    }


# ============================================================================
# BACKEND API FUNCTIONS
# ============================================================================

def fetch_backend_logs(log_file: str = "cip", level: str = "INFO", limit: int = 100) -> Dict:
    """Fetch logs from backend diagnostics API."""
    try:
        resp = requests.get(
            f"{API_BASE}/api/diagnostics/logs",
            params={"file": log_file, "level": level, "limit": limit},
            timeout=5
        )
        if resp.ok:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}", "entries": []}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "entries": []}


def fetch_api_history(limit: int = 50) -> Dict:
    """Fetch API call history from backend."""
    try:
        resp = requests.get(
            f"{API_BASE}/api/diagnostics/api-history",
            params={"limit": limit},
            timeout=5
        )
        if resp.ok:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}", "calls": []}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "calls": []}


def fetch_db_stats() -> Dict:
    """Fetch database statistics from backend."""
    try:
        resp = requests.get(f"{API_BASE}/api/diagnostics/db-stats", timeout=5)
        if resp.ok:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def fetch_system_resources() -> Dict:
    """Fetch system resource usage from backend."""
    try:
        resp = requests.get(f"{API_BASE}/api/diagnostics/system-resources", timeout=5)
        if resp.ok:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def check_backend_health() -> Dict:
    """Quick health check for backend connectivity."""
    try:
        resp = requests.get(f"{API_BASE}/api/health", timeout=3)
        return {"connected": resp.ok, "status": resp.status_code}
    except requests.exceptions.RequestException:
        return {"connected": False, "status": None}


# ============================================================================
# NEW TAB RENDERERS
# ============================================================================

def render_overview_tab():
    """Render overview tab with system health metrics."""
    st.subheader("System Overview")

    # Backend connectivity check
    health = check_backend_health()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_icon = "🟢" if health["connected"] else "🔴"
        st.metric("Backend API", f"{status_icon} {'Connected' if health['connected'] else 'Disconnected'}")

    if health["connected"]:
        # Fetch system resources
        resources = fetch_system_resources()
        if "error" not in resources:
            with col2:
                cpu_color = "normal" if resources["cpu_percent"] < 80 else "inverse"
                st.metric("CPU Usage", f"{resources['cpu_percent']}%")
            with col3:
                mem_pct = resources["memory_percent"]
                st.metric("Memory", f"{resources['memory_used_gb']:.1f} GB ({mem_pct:.0f}%)")
            with col4:
                disk_free = resources["disk_free_gb"]
                st.metric("Disk Free", f"{disk_free:.1f} GB")

            # Process info
            st.markdown("---")
            st.markdown("**Backend Process**")
            proc = resources.get("process", {})
            st.markdown(f"- PID: `{proc.get('pid', 'N/A')}`")
            st.markdown(f"- Memory: `{proc.get('memory_mb', 0):.1f} MB`")
            st.markdown(f"- Timestamp: `{resources.get('timestamp', 'N/A')}`")
        else:
            st.warning(f"Could not fetch resources: {resources['error']}")
    else:
        st.error("Backend API not reachable. Start the backend server with: `python backend/api.py`")


def render_logs_tab():
    """Render backend logs viewer tab."""
    st.subheader("Backend Logs")

    # Filters
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        log_file = st.selectbox("Log File", ["cip", "error", "api"], key="log_file")
    with col2:
        level = st.selectbox("Min Level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], index=1, key="log_level")
    with col3:
        limit = st.slider("Entries", 10, 500, 100, key="log_limit")

    if st.button("Refresh Logs", key="refresh_logs"):
        st.rerun()

    # Fetch and display logs
    logs = fetch_backend_logs(log_file, level, limit)

    if "error" in logs and logs["error"]:
        st.error(f"Error fetching logs: {logs['error']}")
    else:
        entries = logs.get("entries", [])
        if entries:
            st.markdown(f"**{len(entries)} entries** from `{log_file}.log` (level >= {level})")

            for entry in reversed(entries):
                level_color = {
                    "DEBUG": "#64748B",
                    "INFO": "#3B82F6",
                    "WARNING": "#F59E0B",
                    "ERROR": "#EF4444",
                    "CRITICAL": "#DC2626",
                }.get(entry.get("level", "INFO"), "#64748B")

                ts = entry.get("timestamp", "")
                logger = entry.get("logger", "unknown")
                msg = entry.get("message", "")

                st.markdown(f"""
                <div style="font-family: monospace; font-size: 12px; padding: 4px 8px; border-left: 3px solid {level_color}; background: #0F172A; margin: 2px 0;">
                    <span style="color: #64748B;">{ts}</span>
                    <span style="color: {level_color}; font-weight: bold;">[{entry.get("level", "?")}]</span>
                    <span style="color: #94A3B8;">{logger}:</span>
                    <span style="color: #F1F5F9;">{msg}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No log entries found matching the criteria.")


def render_api_history_tab():
    """Render API call history tab."""
    st.subheader("API Call History")

    limit = st.slider("Number of calls", 10, 100, 50, key="api_history_limit")

    if st.button("Refresh History", key="refresh_api_history"):
        st.rerun()

    history = fetch_api_history(limit)

    if "error" in history and history["error"]:
        st.error(f"Error fetching API history: {history['error']}")
    else:
        calls = history.get("calls", [])
        if calls:
            st.markdown(f"**{len(calls)} recent API calls**")

            # Display as table
            for call in reversed(calls):
                method = call.get("method", "?")
                endpoint = call.get("endpoint", "?")
                status = call.get("status")
                ts = call.get("timestamp", "")

                method_color = {
                    "GET": "#22C55E",
                    "POST": "#3B82F6",
                    "PUT": "#F59E0B",
                    "DELETE": "#EF4444",
                }.get(method, "#64748B")

                status_color = "#22C55E" if status and status < 400 else "#EF4444"

                st.markdown(f"""
                <div style="font-family: monospace; font-size: 12px; padding: 4px 8px; background: #0F172A; margin: 2px 0; display: flex; gap: 12px;">
                    <span style="color: #64748B; min-width: 150px;">{ts}</span>
                    <span style="color: {method_color}; font-weight: bold; min-width: 50px;">{method}</span>
                    <span style="color: #F1F5F9; flex: 1;">{endpoint}</span>
                    <span style="color: {status_color};">{status or 'N/A'}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No API calls recorded yet.")


def render_database_tab():
    """Render database statistics tab."""
    st.subheader("Database Statistics")

    if st.button("Refresh Stats", key="refresh_db_stats"):
        st.rerun()

    stats = fetch_db_stats()

    if "error" in stats and stats["error"]:
        st.error(f"Error fetching database stats: {stats['error']}")
    else:
        for db_name, db_info in stats.items():
            st.markdown(f"### {db_name.replace('_', ' ').title()}")

            if db_info.get("exists"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Size", db_info.get("size_human", "Unknown"))
                with col2:
                    table_count = len(db_info.get("tables", {}))
                    st.metric("Tables", table_count)

                # Tables breakdown
                tables = db_info.get("tables", {})
                if tables:
                    st.markdown("**Tables:**")
                    for table_name, row_count in tables.items():
                        st.markdown(f"- `{table_name}`: {row_count:,} rows")
            else:
                st.warning(f"{db_name} does not exist")

            st.markdown("---")


def render_resources_tab():
    """Render system resources tab."""
    st.subheader("System Resources")

    if st.button("Refresh Resources", key="refresh_resources"):
        st.rerun()

    resources = fetch_system_resources()

    if "error" in resources and resources["error"]:
        st.error(f"Error fetching resources: {resources['error']}")
    else:
        # CPU
        st.markdown("### CPU")
        cpu_pct = resources.get("cpu_percent", 0)
        st.progress(cpu_pct / 100)
        st.markdown(f"**{cpu_pct}%** utilized")

        # Memory
        st.markdown("### Memory")
        mem_pct = resources.get("memory_percent", 0)
        st.progress(mem_pct / 100)
        st.markdown(f"**{resources.get('memory_used_gb', 0):.1f} GB** / {resources.get('memory_total_gb', 0):.1f} GB ({mem_pct:.1f}%)")

        # Disk
        st.markdown("### Disk (C:)")
        disk_pct = resources.get("disk_percent", 0)
        st.progress(disk_pct / 100)
        st.markdown(f"**{resources.get('disk_free_gb', 0):.1f} GB** free / {resources.get('disk_total_gb', 0):.1f} GB total ({disk_pct:.1f}% used)")

        # Process
        st.markdown("### Backend Process")
        proc = resources.get("process", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PID", proc.get("pid", "N/A"))
        with col2:
            st.metric("CPU", f"{proc.get('cpu_percent', 0):.1f}%")
        with col3:
            st.metric("Memory", f"{proc.get('memory_mb', 0):.1f} MB")


def render_p7_streaming_tab():
    """Render original P7 streaming diagnostics."""
    st.subheader("P7 Streaming Diagnostics")

    # Get metrics (existing code)
    if COMPONENTS_AVAILABLE:
        check_and_update_state()
        metrics = {
            "connection": get_indicator_metrics(),
            "state_v2": get_state_v2_for_binder(),
            "health": get_health_summary(),
            "buffer": get_diagnostics_data(),
            "gaps": get_state_v2().gaps if hasattr(get_state_v2(), 'gaps') else [],
            "reconnections": [
                {
                    "attempt": r.attempt_number,
                    "duration_ms": r.duration_ms,
                    "reason": r.reason,
                    "success": r.success,
                }
                for r in get_state_v2().reconnections
            ] if hasattr(get_state_v2(), 'reconnections') else [],
        }
    else:
        metrics = get_mock_metrics()

    render_core_metrics(metrics)
    render_health_section(metrics)
    render_buffer_status(metrics)

    col1, col2 = st.columns(2)
    with col1:
        render_sequence_gaps(metrics)
    with col2:
        render_reconnection_history(metrics)

    render_sse_diagnostics()

    if GAP_HOOKS_AVAILABLE:
        render_gap_metadata_report()

    render_raw_state()


# ============================================================================
# PAGE CONTENT
# ============================================================================

def render_header():
    """Render page header with connection indicator."""
    st.markdown("""
    <div class="p7-diag-header">
        <div>
            <div class="p7-diag-subtitle">Phase 7 Streaming</div>
            <div class="p7-diag-title">⚙️ Diagnostics Panel</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if COMPONENTS_AVAILABLE:
        render_connection_indicator()


def render_core_metrics(metrics: Dict[str, Any]):
    """Render core P7 metrics section."""
    st.markdown("""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">📊 Core Metrics</div>
        <div class="p7-diag-grid">
    """, unsafe_allow_html=True)

    # Last Sequence ID
    seq_id = metrics.get("connection", {}).get("last_sequence_id", 0)
    st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Last Sequence ID</div>
                <div class="p7-diag-metric-value info">{seq_id}</div>
                <div class="p7-diag-metric-detail">Latest processed event</div>
            </div>
    """, unsafe_allow_html=True)

    # Keepalive Delta
    keepalive_lag = metrics.get("state_v2", {}).get("keepalive_lag_ms", 0)
    lag_class = "success" if keepalive_lag < 5000 else ("warning" if keepalive_lag < 30000 else "error")
    st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Keepalive Delta</div>
                <div class="p7-diag-metric-value {lag_class}">{keepalive_lag}ms</div>
                <div class="p7-diag-metric-detail">Time since last keepalive</div>
            </div>
    """, unsafe_allow_html=True)

    # Total Events
    total_events = metrics.get("state_v2", {}).get("total_events_received", 0)
    st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Total Events</div>
                <div class="p7-diag-metric-value">{total_events}</div>
                <div class="p7-diag-metric-detail">Events this session</div>
            </div>
    """, unsafe_allow_html=True)

    # Connection State
    state = metrics.get("connection", {}).get("state", "unknown")
    state_class = {
        "active": "success",
        "stale": "warning",
        "reconnecting": "info",
        "terminated": "error",
    }.get(state, "")
    st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Connection State</div>
                <div class="p7-diag-metric-value {state_class}">{state.upper()}</div>
                <div class="p7-diag-metric-detail">Current SSE state</div>
            </div>
    """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


def render_health_section(metrics: Dict[str, Any]):
    """Render health metrics section."""
    health = metrics.get("health", {})
    health_score = health.get("health_score", 100)
    status = health.get("status", "healthy")

    status_class = {
        "healthy": "healthy",
        "degraded": "degraded",
        "unhealthy": "unhealthy",
    }.get(status, "healthy")

    st.markdown(f"""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">🏥 Health Status</div>
        <div class="p7-diag-grid">
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Health Score</div>
                <div class="p7-diag-metric-value">{health_score}</div>
                <div class="p7-health-gauge">
                    <div class="p7-health-gauge-fill {status_class}" style="width: {health_score}%"></div>
                </div>
            </div>
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Status</div>
                <span class="p7-diag-badge {status_class}">{status.upper()}</span>
            </div>
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Availability</div>
                <div class="p7-diag-metric-value">{metrics.get("state_v2", {}).get("availability_pct", 100):.1f}%</div>
            </div>
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Reconnections</div>
                <div class="p7-diag-metric-value">{metrics.get("state_v2", {}).get("reconnection_count", 0)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_buffer_status(metrics: Dict[str, Any]):
    """Render event buffer status section."""
    buffer = metrics.get("buffer", {})

    st.markdown(f"""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">📦 Event Buffer</div>
        <div class="p7-diag-grid">
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Buffered Events</div>
                <div class="p7-diag-metric-value">{buffer.get("events_count", 0)}</div>
            </div>
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Last Processed Seq</div>
                <div class="p7-diag-metric-value info">{buffer.get("last_seq", 0)}</div>
            </div>
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Expected Next Seq</div>
                <div class="p7-diag-metric-value">{buffer.get("expected_seq", 0)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sequence_gaps(metrics: Dict[str, Any]):
    """Render sequence gap history."""
    gaps = metrics.get("gaps", [])
    state_v2 = metrics.get("state_v2", {})

    gaps_detected = state_v2.get("gaps_detected", len(gaps))
    gaps_resolved = state_v2.get("gaps_resolved", sum(1 for g in gaps if g.get("resolved")))

    st.markdown(f"""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">
            🔍 Sequence Gaps
            <span style="margin-left: auto; font-size: 12px; color: #64748B;">
                {gaps_resolved}/{gaps_detected} resolved
            </span>
        </div>
    """, unsafe_allow_html=True)

    if gaps:
        st.markdown("""
        <table class="p7-diag-table">
            <thead>
                <tr>
                    <th>Expected</th>
                    <th>Received</th>
                    <th>Gap Size</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)

        for gap in gaps[-10:]:  # Show last 10
            resolved = gap.get("resolved", False)
            status_badge = '<span class="p7-diag-badge healthy">Resolved</span>' if resolved else \
                          '<span class="p7-diag-badge warning">Pending</span>'

            st.markdown(f"""
                <tr>
                    <td>{gap.get("expected", "?")}</td>
                    <td>{gap.get("received", "?")}</td>
                    <td>{gap.get("gap_size", "?")}</td>
                    <td>{status_badge}</td>
                </tr>
            """, unsafe_allow_html=True)

        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="p7-diag-empty">No sequence gaps detected</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_reconnection_history(metrics: Dict[str, Any]):
    """Render reconnection history."""
    reconnections = metrics.get("reconnections", [])

    st.markdown(f"""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">
            🔄 Reconnection History
            <span style="margin-left: auto; font-size: 12px; color: #64748B;">
                {len(reconnections)} total
            </span>
        </div>
    """, unsafe_allow_html=True)

    if reconnections:
        st.markdown("""
        <table class="p7-diag-table">
            <thead>
                <tr>
                    <th>Attempt</th>
                    <th>Duration</th>
                    <th>Reason</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)

        for recon in reconnections[-10:]:  # Show last 10
            success = recon.get("success", False)
            status_badge = '<span class="p7-diag-badge healthy">Success</span>' if success else \
                          '<span class="p7-diag-badge error">Failed</span>'

            duration = recon.get("duration_ms", 0)

            st.markdown(f"""
                <tr>
                    <td>#{recon.get("attempt", "?")}</td>
                    <td>{duration}ms</td>
                    <td>{recon.get("reason", "unknown")}</td>
                    <td>{status_badge}</td>
                </tr>
            """, unsafe_allow_html=True)

        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="p7-diag-empty">No reconnections recorded</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_sse_diagnostics():
    """Render P7.S2 SSE diagnostics metrics."""
    st.markdown("""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">📡 P7.S2 SSE Diagnostics</div>
    </div>
    """, unsafe_allow_html=True)

    if DIAG_SSE_AVAILABLE:
        ctx = get_diagnostics_context()
        
        # Connect button (only if not connected)
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Connect SSE"):
                ctx.connect()
                st.rerun()
        with col2:
            mode_label = "REAL" if USE_REAL_SSE else "MOCK"
            st.markdown(f"**Mode:** `{mode_label}`")
        
        # Get metrics
        metrics = ctx.get_diagnostics_metrics()
        
        # Display required metrics
        st.markdown("""
        <div class="p7-diag-grid">
        """, unsafe_allow_html=True)
        
        # last_sequence_id
        seq_class = "info" if metrics["last_sequence_id"] >= 0 else "warning"
        st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Last Sequence ID</div>
                <div class="p7-diag-metric-value {seq_class}">{metrics["last_sequence_id"]}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # buffer_size
        st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Buffer Size</div>
                <div class="p7-diag-metric-value">{metrics["buffer_size"]}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # gap_count
        gap_class = "success" if metrics["gap_count"] == 0 else "warning"
        st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Gap Count</div>
                <div class="p7-diag-metric-value {gap_class}">{metrics["gap_count"]}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # connection_state
        state = metrics["connection_state"]
        state_class = {
            "connected": "success",
            "connecting": "info",
            "disconnected": "warning",
            "error": "error",
        }.get(state, "")
        st.markdown(f"""
            <div class="p7-diag-metric">
                <div class="p7-diag-metric-label">Connection State</div>
                <div class="p7-diag-metric-value {state_class}">{state.upper()}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Simulate event button (mock mode only)
        if not USE_REAL_SSE:
            st.markdown("---")
            if st.button("Simulate Event"):
                ctx.simulate_event("test_event", {"test": True, "timestamp": datetime.now().isoformat()})
                st.rerun()
        
        # Raw metrics expander
        with st.expander("Raw SSE Metrics"):
            st.json(metrics)
    else:
        st.warning("DiagnosticsSSEContext not available. Check integrations/event_buffer_stub.py")


def render_raw_state():
    """Render raw state JSON for debugging."""
    st.markdown("""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">🔧 Raw State (Debug)</div>
    </div>
    """, unsafe_allow_html=True)

    if COMPONENTS_AVAILABLE:
        with st.expander("Connection Indicator State"):
            st.json(get_indicator_metrics())

        with st.expander("State Schema v2"):
            st.json(get_state_v2_for_binder())

        with st.expander("Diagnostics Data"):
            st.json(get_diagnostics_data())
    else:
        st.info("Components not available. Using mock data.")
        st.json(get_mock_metrics())




# ============================================================================
# GAP METADATA REPORT (P7.S2 Task 8)
# ============================================================================

def render_gap_metadata_report():
    """Render Gap Metadata Report per GEM Task 8."""
    if not GAP_HOOKS_AVAILABLE:
        return
    
    st.markdown("""
    <div class="p7-diag-section">
        <div class="p7-diag-section-title">
            📊 Gap Metadata Report (Task 8)
        </div>
    """, unsafe_allow_html=True)
    
    try:
        report = get_current_gap_report()
        stats = get_gap_statistics()
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Gaps", stats["total_active"])
        with col2:
            st.metric("Resolved (24h)", stats["total_resolved_24h"])
        with col3:
            severity_breakdown = stats.get("active_by_severity", {})
            critical = severity_breakdown.get("CRITICAL", 0)
            warn = severity_breakdown.get("WARN", 0)
            info = severity_breakdown.get("INFO", 0)
            st.metric("By Severity", f"C:{critical} W:{warn} I:{info}")
        
        # Open gaps table
        open_gaps = report.get("open_gaps", [])
        if open_gaps:
            st.markdown("**Open Gaps:**")
            for gap in open_gaps:
                severity_color = {
                    "CRITICAL": "#EF4444",
                    "WARN": "#F59E0B",
                    "INFO": "#3B82F6"
                }.get(gap["severity"], "#64748B")
                
                st.markdown(f"""
                <div style="background: #0F172A; border: 1px solid #334155; border-radius: 4px; padding: 8px; margin: 4px 0;">
                    <span style="color: {severity_color}; font-weight: bold;">[{gap["severity"]}]</span>
                    Gap ID: <code>{gap["gap_id"][:8]}...</code> |
                    Seq: {gap["start_sequence"]} → {gap["end_sequence"]} |
                    State: {gap["lifecycle_state"]} |
                    Provenance: {gap["provenance"]}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="p7-diag-empty">No active gaps</div>', unsafe_allow_html=True)
        
        # Resolved gaps (last 24h)
        resolved = report.get("resolved_gaps_24h", [])
        if resolved:
            with st.expander(f"Resolved Gaps (24h): {len(resolved)}"):
                for gap in resolved[-5:]:  # Show last 5
                    st.text(f"  {gap['gap_id'][:8]}: {gap['start_sequence']} → {gap['end_sequence']} [{gap['lifecycle_state']}]")
        
        # Clear button (for testing)
        if st.button("Clear All Gaps", key="clear_gaps"):
            clear_all_gaps()
            st.success("Gap history cleared")
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading gap report: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# MAIN PAGE
# ============================================================================

def main():
    """Main diagnostics page with tabs."""
    inject_diagnostics_page_css()

    # Developer warning
    st.markdown("""
    <div class="p7-diag-warning">
        ⚠️ <strong>Developer Tool</strong> — This page is for debugging and monitoring
        CIP backend services and P7 streaming infrastructure. Not intended for end users.
    </div>
    """, unsafe_allow_html=True)

    # Page title
    st.markdown("""
    <div class="p7-diag-header">
        <div>
            <div class="p7-diag-subtitle">CIP System</div>
            <div class="p7-diag-title">⚙️ Diagnostics Panel</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs
    tab_overview, tab_logs, tab_api, tab_db, tab_resources, tab_p7 = st.tabs([
        "Overview",
        "Backend Logs",
        "API History",
        "Database",
        "Resources",
        "P7 Streaming"
    ])

    with tab_overview:
        render_overview_tab()

    with tab_logs:
        render_logs_tab()

    with tab_api:
        render_api_history_tab()

    with tab_db:
        render_database_tab()

    with tab_resources:
        render_resources_tab()

    with tab_p7:
        render_p7_streaming_tab()

    # Auto-refresh option (footer)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Refresh All"):
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (10s)")

    if auto_refresh:
        import time
        time.sleep(10)
        st.rerun()


if __name__ == "__main__":
    main()
