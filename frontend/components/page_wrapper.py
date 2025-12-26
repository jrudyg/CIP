# components/page_wrapper.py
"""
CIP Page Wrapper - Canonical page shell for all CIP pages.
Handles layout, session state, sidebar logo, and structural elements.

NOTE: Theme and page_config are handled ONCE in app.py.
      This wrapper assumes theme is already active.

Version: wrapper_v1.4 (ULTRA-COMPACT)
"""
import streamlit as st
from contextlib import contextmanager
from typing import Optional

# NOTE: inject_cip_logo is handled in app.py, not here
from components.system_status import render_system_status

DEFAULT_SESSION_STATE = {
    "active_contract_id": None,
    "portfolio_filters": {"status": "All", "stage": "All", "risk": "All"},
    "user_role": "standard",
    "layout_version": "wrapper_v1.4"
}


def _init_session_defaults() -> None:
    """Initialize default session state keys if not present."""
    for key, value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _apply_max_width_css(max_width: int) -> None:
    """Apply max-width constraint and compact top padding to main content area."""
    st.markdown(
        f"""
        <style>
        /* Reduce default Streamlit top padding */
        .block-container {{
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }}
        
        section.main > div {{
            max-width: {max_width}px;
            margin: 0 auto;
            padding-left: 2rem;
            padding-right: 2rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def init_page(
    title: str,
    icon: str,
    max_width: int = 1200,
    show_header: bool = True,
    show_footer: bool = True
) -> None:
    """
    Initialize a CIP page with consistent layout.

    Handles: sidebar logo, session state, max-width.

    NOTE: Does NOT call st.set_page_config or inject theme.
          Those are handled globally in app.py.
    """
    # 1) Session state defaults
    _init_session_defaults()

    # 2) Max-width constraint
    _apply_max_width_css(max_width)

    # 3) Sidebar logo is handled in app.py - DO NOT add here

    # 4) Store current page info for footer/header use
    st.session_state["_current_page"] = {
        "title": title,
        "icon": icon,
        "show_header": show_header,
        "show_footer": show_footer
    }


def page_header(
    title: str,
    subtitle: Optional[str] = None,
    show_divider: bool = False,
    show_status: bool = False,
    show_version: bool = False
) -> None:
    """
    Render compact, integrated page header.
    
    Title and subtitle appear as one visual unit with minimal spacing.
    8px top padding, 6px gap between title/subtitle, 8px bottom margin.
    
    Optional: Status badge and version in upper right.
    """
    version = st.session_state.get("layout_version", "wrapper_v1.4")
    
    # Build status HTML if needed
    status_html = ""
    if show_status or show_version:
        status_parts = []
        if show_status:
            # Make status clickable - links to diagnostics page
            status_parts.append('<a href="/99_P7_Diagnostics" target="_self" style="color: #64748B; text-decoration: none; display: flex; align-items: center; gap: 4px; cursor: pointer;" onmouseover="this.style.color=\'#A78BFA\'" onmouseout="this.style.color=\'#64748B\'"><span style="color: #10B981;">●</span> Online</a>')
        if show_version:
            status_parts.append(f'v{version.split("_v")[-1] if "_v" in version else "0.7.2"}')
        status_html = f'<div style="position: absolute; top: 8px; right: 0; font-size: 0.75rem; color: #64748B; display: flex; gap: 12px; align-items: center;">{"  |  ".join(status_parts)}</div>'
    
    if subtitle:
        st.markdown(
            f'<div style="padding-top: 8px; margin-bottom: 8px; position: relative;">'
            f'{status_html}'
            f'<h1 style="color: #E2E8F0; font-size: 1.75rem; font-weight: 600; margin: 0 0 4px 0; padding: 0; letter-spacing: -0.02em; line-height: 1.2;">{title}</h1>'
            f'<p style="color: #9CA3AF; font-size: 0.9rem; margin: 0; padding: 0; line-height: 1.3;">{subtitle}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="padding-top: 8px; margin-bottom: 8px; position: relative;">'
            f'{status_html}'
            f'<h1 style="color: #E2E8F0; font-size: 1.75rem; font-weight: 600; margin: 0; padding: 0; letter-spacing: -0.02em; line-height: 1.2;">{title}</h1>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Optional divider (off by default for compact look)
    if show_divider:
        st.markdown(
            '<hr style="border: none; border-top: 1px solid #1E293B; margin: 0 0 0.5rem 0;">',
            unsafe_allow_html=True
        )


def context_block(
    block_type: str,
    message: str,
    icon: Optional[str] = None
) -> None:
    """Render contextual info/warning/error block."""
    config = {
        "info": {"icon": "ℹ️", "bg": "#1E3A5F", "border": "#38BDF8", "text": "#E2E8F0"},
        "warning": {"icon": "⚠️", "bg": "#3D2E1F", "border": "#F59E0B", "text": "#FDE68A"},
        "error": {"icon": "❌", "bg": "#3D1F1F", "border": "#EF4444", "text": "#FCA5A5"},
        "success": {"icon": "✅", "bg": "#1F3D2E", "border": "#22C55E", "text": "#BBF7D0"},
        "instructions": {"icon": "📋", "bg": "#1E293B", "border": "#64748B", "text": "#CBD5E1"}
    }
    cfg = config.get(block_type, config["info"])
    display_icon = icon or cfg["icon"]
    st.markdown(
        f'''
        <div style="
            background-color: {cfg["bg"]};
            border-left: 4px solid {cfg["border"]};
            border-radius: 0 8px 8px 0;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            color: {cfg["text"]};
            font-size: 0.9rem;
        ">
            <span style="margin-right: 0.5rem;">{display_icon}</span>
            {message}
        </div>
        ''',
        unsafe_allow_html=True
    )


@contextmanager
def content_container():
    """Context manager for main content area with minimal spacing."""
    container = st.container()
    with container:
        yield
    # Minimal bottom spacing
    st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)


def page_footer(
    show_status: bool = True,
    show_version: bool = True,
    compact: bool = True
) -> None:
    """Render page footer with optional system status."""
    st.markdown(
        '<hr style="border: none; border-top: 1px solid #1E293B; margin: 1rem 0 0.5rem 0;">',
        unsafe_allow_html=True
    )
    footer_cols = st.columns([3, 1]) if show_version else [st.container()]
    with footer_cols[0]:
        if show_status:
            render_system_status(compact=compact)
    if show_version and len(footer_cols) > 1:
        with footer_cols[1]:
            version = st.session_state.get("layout_version", "wrapper_v1.4")
            st.markdown(
                f'<div style="text-align: right; font-size: 0.75rem; color: #475569;">'
                f'Layout: {version}</div>',
                unsafe_allow_html=True
            )
