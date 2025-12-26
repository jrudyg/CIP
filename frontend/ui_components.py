"""
CIP UI Components Library
Provides consistent visual elements across all pages
"""
import streamlit as st
from typing import Optional, Literal
import requests
import sqlite3
from datetime import datetime, date
import time

# Color scheme for risk levels (Modern Dark design)
RISK_COLORS = {
    "critical": "#EF4444",  # Red (CRITICAL from design)
    "high": "#F97316",      # Orange (HIGH from design)
    "medium": "#FBBF24",    # Amber (MODERATE from design)
    "low": "#10B981",       # Green (LOW from design)
    "minimal": "#10B981"    # Green (same as low)
}

STATUS_COLORS = {
    "active": "#10B981",    # Green (success)
    "pending": "#F59E0B",   # Amber (warning)
    "completed": "#10B981", # Green (success)
    "failed": "#EF4444",    # Red (error)
    "draft": "#64748B"      # Gray (subtle)
}

def risk_badge(level: str, text: Optional[str] = None) -> None:
    """Display colored risk level badge"""
    if text is None:
        text = level.title()

    color = RISK_COLORS.get(level.lower(), "#6C757D")
    st.markdown(
        f"""
        <span style="
            background-color: {color};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            display: inline-block;
        ">{text}</span>
        """,
        unsafe_allow_html=True
    )

def status_badge(status: str) -> None:
    """Display colored status badge"""
    color = STATUS_COLORS.get(status.lower(), "#6C757D")
    st.markdown(
        f"""
        <span style="
            background-color: {color};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            display: inline-block;
        ">{status.upper()}</span>
        """,
        unsafe_allow_html=True
    )

def metric_card(label: str, value: str, delta: Optional[str] = None, risk_level: Optional[str] = None) -> None:
    """Enhanced metric card with optional risk border"""
    border_color = RISK_COLORS.get(risk_level, "#334155") if risk_level else "#334155"

    card_html = f"""
    <div style="
        border: 2px solid {border_color};
        border-radius: 8px;
        padding: 16px;
        background-color: #1E293B;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.15);
    ">
        <div style="color: #94A3B8; font-size: 14px; margin-bottom: 4px;">{label}</div>
        <div style="font-size: 28px; font-weight: 600; color: #E2E8F0;">{value}</div>
        {f'<div style="font-size: 14px; color: {border_color}; margin-top: 4px;">{delta}</div>' if delta else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def section_header(title: str, emoji: str = "📊") -> None:
    """Consistent section headers with emoji"""
    st.markdown(f"### {emoji} {title}")
    st.divider()

def page_header(title: str, description: Optional[str] = None) -> None:
    """Page-level header with optional description"""
    st.markdown(f"# {title}")
    if description:
        st.markdown(f"*{description}*")
    st.divider()

def toast_success(message: str) -> None:
    """Success toast notification"""
    st.success(f"✅ {message}")

def toast_warning(message: str) -> None:
    """Warning toast notification"""
    st.warning(f"⚠️ {message}")

def toast_error(message: str) -> None:
    """Error toast notification"""
    st.error(f"❌ {message}")

def toast_info(message: str) -> None:
    """Info toast notification"""
    st.info(f"ℹ️ {message}")

def loading_spinner(text: str = "Processing..."):
    """Consistent loading spinner"""
    return st.spinner(f"⏳ {text}")


def loading_placeholder(message: str = "Loading...", height: int = 200) -> None:
    """Display a loading placeholder with animation hint"""
    st.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: {height}px;
            background-color: #1E293B;
            border-radius: 8px;
            color: #94A3B8;
            border: 1px solid #334155;
        ">
            <div style="font-size: 24px; margin-bottom: 8px;">⏳</div>
            <div>{message}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def risk_summary_card(contract_name: str, risk_score: float, critical_count: int, high_count: int):
    """Display contract risk summary with visual indicators"""

    if risk_score >= 8.0 or critical_count > 0:
        risk_level = "critical"
        risk_text = "CRITICAL"
    elif risk_score >= 6.0 or high_count > 2:
        risk_level = "high"
        risk_text = "HIGH"
    elif risk_score >= 4.0:
        risk_level = "medium"
        risk_text = "MEDIUM"
    else:
        risk_level = "low"
        risk_text = "LOW"

    border_color = RISK_COLORS[risk_level]

    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {border_color};
            padding: 16px;
            background-color: #1E293B;
            border-radius: 4px;
            margin: 16px 0;
        ">
            <h3 style="margin: 0 0 12px 0; color: #E2E8F0;">{contract_name}</h3>
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="
                    background-color: {border_color};
                    color: white;
                    padding: 6px 16px;
                    border-radius: 16px;
                    font-weight: 600;
                ">{risk_text} RISK</span>
                <span style="color: #94A3B8;">Score: {risk_score:.1f}/10</span>
            </div>
            <div style="margin-top: 12px; color: #E2E8F0;">
                🔴 Critical Issues: {critical_count} | 🟠 High Priority: {high_count}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

SPACING_CSS = """
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        margin-bottom: 1rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    hr {
        margin: 2rem 0;
    }

    /* Enhanced table styling */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Expander styling */
    div[data-testid="stExpander"] {
        border-radius: 8px;
        border: 1px solid #334155;
    }

    /* Tab styling */
    div[data-testid="stTabs"] button {
        font-weight: 500;
    }

    /* Sidebar styling - uses theme_system.py */

    /* Alert box consistency */
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }

    /* Form styling */
    div[data-testid="stForm"] {
        border-radius: 8px;
        padding: 1rem;
        background-color: #1E293B;
        border: 1px solid #334155;
    }
</style>
"""

def apply_spacing():
    """Apply consistent spacing CSS"""
    st.markdown(SPACING_CSS, unsafe_allow_html=True)


# ============================================================================
# PRESERVED FOR FUTURE USE - NOT CURRENTLY IN USE
# This function is available but not imported or called anywhere in the app
# Kept for potential future implementation of system health monitoring
# ============================================================================
def system_info_check():
    """
    System Info auto-check component with animation
    Checks backend health and database connectivity
    Shows response times, last checked time, and version

    NOTE: This function is preserved but not currently used in the application.
    """
    # Initialize session state for health check
    if 'health_check_result' not in st.session_state:
        st.session_state.health_check_result = None
    if 'health_check_time' not in st.session_state:
        st.session_state.health_check_time = None

    # Create placeholder for animation
    placeholder = st.empty()

    # Show loading animation
    with placeholder.container():
        st.markdown("""
            <div class="system-info-box system-info-animating" style="
                padding: 16px;
                border-radius: 12px;
                border: 2px solid #EF4444;
                background: rgba(255,255,255,0.02);
                animation: system-check-pulse 1.2s ease-in-out;
            ">
                <div style="text-align: center; color: #94A3B8;">
                    ⏳ Checking system status...
                </div>
            </div>
            <style>
            @keyframes system-check-pulse {
                0% { border-color: #EF4444; } /* Red */
                25% { border-color: #F97316; } /* Orange */
                50% { border-color: #FBBF24; } /* Yellow */
                75% { border-color: #10B981; } /* Green */
                100% { border-color: #3B82F6; } /* Blue */
            }
            </style>
        """, unsafe_allow_html=True)

    # Perform health check
    start_time = time.time()
    health_status = {
        'backend': 'unknown',
        'backend_ms': 0,
        'database': 'unknown',
        'database_ms': 0,
        'version': 'CIP v1.0.0'
    }

    # Check backend health
    try:
        backend_start = time.time()
        response = requests.get("http://localhost:5000/health", timeout=5)
        backend_time = (time.time() - backend_start) * 1000  # Convert to ms

        if response.ok:
            health_status['backend'] = 'ok'
            health_status['backend_ms'] = round(backend_time, 1)
        else:
            health_status['backend'] = 'error'
    except requests.exceptions.Timeout:
        health_status['backend'] = 'timeout'
    except requests.exceptions.ConnectionError:
        health_status['backend'] = 'offline'
    except Exception as e:
        health_status['backend'] = 'error'

    # Check database connectivity
    try:
        db_start = time.time()
        conn = sqlite3.connect("C:\\Users\\jrudy\\CIP\\data\\contracts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contracts")
        cursor.fetchone()
        conn.close()
        db_time = (time.time() - db_start) * 1000
        health_status['database'] = 'connected'
        health_status['database_ms'] = round(db_time, 1)
    except Exception as e:
        health_status['database'] = 'error'

    # Store results
    st.session_state.health_check_result = health_status
    st.session_state.health_check_time = datetime.now()

    # Wait for animation to complete (1.2s)
    elapsed = time.time() - start_time
    if elapsed < 1.2:
        time.sleep(1.2 - elapsed)

    # Replace with results
    with placeholder.container():
        # Determine overall status
        overall_status = 'ok' if health_status['backend'] == 'ok' and health_status['database'] == 'connected' else 'offline'
        border_color = '#3B82F6' if overall_status == 'ok' else '#EF4444'  # Blue or Red

        # Time since check
        time_ago = "Just now"
        if st.session_state.health_check_time:
            delta = datetime.now() - st.session_state.health_check_time
            if delta.seconds < 60:
                time_ago = f"{delta.seconds}s ago"
            elif delta.seconds < 3600:
                time_ago = f"{delta.seconds // 60}m ago"

        st.markdown(f"""
            <div style="
                padding: 16px;
                border-radius: 12px;
                border: 2px solid {border_color};
                background: rgba(255,255,255,0.02);
            ">
                <div style="color: #E2E8F0; font-weight: 600; margin-bottom: 12px;">
                    {health_status['version']}
                </div>
                <div style="font-size: 13px; color: #94A3B8; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Backend:</span>
                        <span style="color: {'#10B981' if health_status['backend'] == 'ok' else '#EF4444'};">
                            {health_status['backend'].upper()} {'(' + str(health_status['backend_ms']) + 'ms)' if health_status['backend_ms'] else ''}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                        <span>Database:</span>
                        <span style="color: {'#10B981' if health_status['database'] == 'connected' else '#EF4444'};">
                            {health_status['database'].upper()} {'(' + str(health_status['database_ms']) + 'ms)' if health_status['database_ms'] else ''}
                        </span>
                    </div>
                </div>
                <div style="font-size: 11px; color: #64748B; text-align: right;">
                    Last checked: {time_ago}
                </div>
            </div>
        """, unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📭", action_label: Optional[str] = None) -> bool:
    """Display empty state with optional action button. Returns True if action clicked."""
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 3rem;
            background-color: #1E293B;
            border-radius: 12px;
            margin: 1rem 0;
            border: 1px solid #334155;
        ">
            <div style="font-size: 48px; margin-bottom: 1rem;">{icon}</div>
            <div style="color: #94A3B8; font-size: 16px;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if action_label:
        return st.button(action_label, type="primary", use_container_width=True)
    return False


def progress_card(title: str, current: int, total: int, subtitle: Optional[str] = None) -> None:
    """Display progress card with bar"""
    progress = (current / total) if total > 0 else 0
    color = "#10B981" if progress >= 0.8 else "#F59E0B" if progress >= 0.5 else "#EF4444"

    st.markdown(
        f"""
        <div style="
            padding: 1rem;
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: 500; color: #E2E8F0;">{title}</span>
                <span style="color: #94A3B8;">{current}/{total}</span>
            </div>
            <div style="
                background-color: #334155;
                border-radius: 4px;
                height: 8px;
                overflow: hidden;
            ">
                <div style="
                    background-color: {color};
                    width: {progress * 100}%;
                    height: 100%;
                    transition: width 0.3s ease;
                "></div>
            </div>
            {f'<div style="color: #94A3B8; font-size: 12px; margin-top: 0.5rem;">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================================
# NEW FORM INPUT COMPONENTS
# Added for enhanced UI consistency
# ============================================================================

def toggle_group(
    label: str,
    options: list[str],
    default: str | None = None,
    key: str | None = None
) -> str:
    """Horizontal toggle group using radio buttons."""
    index = options.index(default) if default and default in options else 0
    return st.radio(label, options=options, index=index, horizontal=True, key=key)


def button_group(
    buttons: list[str],
    key_prefix: str | None = None
) -> str | None:
    """Row of buttons, returns which button was clicked."""
    cols = st.columns(len(buttons))
    for idx, (col, label) in enumerate(zip(cols, buttons)):
        with col:
            key = f"{key_prefix}_{idx}" if key_prefix else f"btn_group_{idx}_{label}"
            if st.button(label, key=key, use_container_width=True):
                return label
    return None


def date_picker(
    label: str,
    default: date | tuple | None = None,
    range_mode: bool = False,
    key: str | None = None
) -> date | tuple:
    """Date picker supporting single date or date range."""
    if range_mode:
        col1, col2 = st.columns(2)
        start_default = default[0] if default else None
        end_default = default[1] if default and len(default) > 1 else None
        with col1:
            start_date = st.date_input(f"{label} - Start", value=start_default, key=f"{key}_start" if key else None)
        with col2:
            end_date = st.date_input(f"{label} - End", value=end_default, key=f"{key}_end" if key else None)
        return (start_date, end_date)
    return st.date_input(label, value=default, key=key)


def text_input_with_icon(
    label: str,
    placeholder: str = "",
    icon: str | None = None,
    key: str | None = None
) -> str:
    """Text input with optional icon prefix."""
    display_label = f"{icon} {label}" if icon else label
    return st.text_input(display_label, placeholder=placeholder, key=key)


def text_area_input(
    label: str,
    placeholder: str = "",
    height: int = 200,
    key: str | None = None
) -> str:
    """Multi-line text input area."""
    return st.text_area(label, placeholder=placeholder, height=height, key=key)


def primary_button(
    label: str,
    key: str | None = None,
    loading: bool = False
) -> bool:
    """Primary action button with optional loading state."""
    if loading:
        return st.button(f"⏳ {label}", key=key, type="primary", disabled=True, use_container_width=True)
    return st.button(label, key=key, type="primary", use_container_width=True)


def secondary_button(
    label: str,
    key: str | None = None
) -> bool:
    """Secondary action button."""
    return st.button(label, key=key, use_container_width=True)


def content_block(
    text: str,
    variant: Literal["summary", "narrative", "tip"] = "summary"
) -> None:
    """Styled content block with different visual treatments."""
    styles = {
        "summary": {"bg": "#1E293B", "border": "#3B82F6", "icon": "📋"},
        "narrative": {"bg": "#1E293B", "border": "#8B5CF6", "icon": "📖"},
        "tip": {"bg": "#1E293B", "border": "#F59E0B", "icon": "💡"},
    }
    style = styles.get(variant, styles["summary"])
    html = f'''<div style="background-color:{style['bg']};border-left:4px solid {style['border']};padding:1rem;border-radius:0.25rem;margin:1rem 0;">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{style['icon']}</span>
        <span style="color:#E2E8F0;line-height:1.6;">{text}</span>
    </div>'''
    st.markdown(html, unsafe_allow_html=True)
