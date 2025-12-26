"""
TopNav Component - Phase 6 UI Upgrade
P6.C2.T1: High-Contrast TopNav

Tabbed navigation component with high-contrast mode support.
Tabs: Upload, Compare, Analyze, Export

CIP Protocol: CC2 implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from components.color_tokens import (
    get_token,
    is_high_contrast_mode,
    inject_color_tokens,
    render_contrast_toggle,
)


# ============================================================================
# NAVIGATION TAB DEFINITIONS
# ============================================================================

@dataclass
class NavTab:
    """Definition of a navigation tab."""
    tab_id: str
    label: str
    icon: str
    description: str
    disabled: bool = False
    badge_count: Optional[int] = None


DEFAULT_NAV_TABS = [
    NavTab(
        tab_id="upload",
        label="Upload",
        icon="📤",
        description="Upload contract documents",
    ),
    NavTab(
        tab_id="compare",
        label="Compare",
        icon="⚖️",
        description="Compare contract versions",
    ),
    NavTab(
        tab_id="analyze",
        label="Analyze",
        icon="🔍",
        description="Analyze contract risks",
    ),
    NavTab(
        tab_id="export",
        label="Export",
        icon="📥",
        description="Export reports and data",
    ),
]


# ============================================================================
# CSS STYLING
# ============================================================================

def _generate_topnav_css() -> str:
    """Generate TopNav CSS with current color tokens."""
    high_contrast = is_high_contrast_mode()

    # Get tokens
    nav_bg = get_token("nav-bg")
    nav_border = get_token("nav-border")
    tab_active = get_token("nav-tab-active")
    tab_hover = get_token("nav-tab-hover")
    tab_text = get_token("nav-tab-text")
    tab_text_inactive = get_token("nav-tab-text-inactive")
    text_muted = get_token("text-muted")
    border_focus = get_token("border-focus")

    # High contrast adjustments
    border_width = "3px" if high_contrast else "2px"
    focus_outline = "3px" if high_contrast else "2px"

    return f"""
<style>
/* ============================================================================
   TOPNAV COMPONENT STYLES
   Phase 6 UI Upgrade - P6.C2.T1
   High-Contrast Mode: {'ENABLED' if high_contrast else 'DISABLED'}
   ============================================================================ */

/* Main TopNav Container */
.cip-topnav {{
    position: sticky;
    top: 0;
    z-index: 1000;
    background: {nav_bg};
    border-bottom: {border_width} solid {nav_border};
    padding: 0;
    margin: -1rem -1rem 1rem -1rem;
    width: calc(100% + 2rem);
}}

/* Nav Inner Container */
.cip-topnav-inner {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 24px;
    max-width: 1400px;
    margin: 0 auto;
}}

/* Logo Section */
.cip-topnav-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 0;
}}

.cip-topnav-logo-icon {{
    font-size: 28px;
}}

.cip-topnav-logo-text {{
    font-size: 18px;
    font-weight: 700;
    color: {tab_text};
    letter-spacing: 0.5px;
}}

/* Tabs Container */
.cip-topnav-tabs {{
    display: flex;
    gap: 4px;
    padding: 0;
    margin: 0;
    list-style: none;
}}

/* Individual Tab */
.cip-topnav-tab {{
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 24px;
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 8px 8px 0 0;
    text-decoration: none;
    color: {tab_text_inactive};
    background: transparent;
    border: none;
    font-family: inherit;
    font-size: 14px;
}}

.cip-topnav-tab:hover {{
    background: {tab_hover};
    color: {tab_text};
}}

.cip-topnav-tab:focus {{
    outline: {focus_outline} solid {border_focus};
    outline-offset: -2px;
}}

.cip-topnav-tab:focus-visible {{
    outline: {focus_outline} solid {border_focus};
    outline-offset: -2px;
}}

.cip-topnav-tab.active {{
    color: {tab_text};
    background: {tab_hover};
}}

.cip-topnav-tab.active::after {{
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: {border_width};
    background: {tab_active};
}}

.cip-topnav-tab.disabled {{
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
}}

/* Tab Icon */
.cip-topnav-tab-icon {{
    font-size: 20px;
    margin-bottom: 4px;
}}

/* Tab Label */
.cip-topnav-tab-label {{
    font-weight: 500;
    font-size: 13px;
}}

/* Tab Badge */
.cip-topnav-tab-badge {{
    position: absolute;
    top: 8px;
    right: 8px;
    min-width: 18px;
    height: 18px;
    padding: 0 6px;
    background: {get_token("accent-error")};
    color: white;
    font-size: 11px;
    font-weight: 600;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* Actions Section */
.cip-topnav-actions {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

/* Contrast Toggle Button */
.cip-topnav-contrast-btn {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: transparent;
    border: 1px solid {nav_border};
    border-radius: 6px;
    color: {tab_text_inactive};
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s ease;
}}

.cip-topnav-contrast-btn:hover {{
    background: {tab_hover};
    color: {tab_text};
    border-color: {tab_active};
}}

.cip-topnav-contrast-btn:focus {{
    outline: {focus_outline} solid {border_focus};
    outline-offset: 2px;
}}

.cip-topnav-contrast-btn.active {{
    background: {tab_hover};
    color: {tab_text};
    border-color: {tab_active};
}}

/* Mobile Responsive */
@media (max-width: 768px) {{
    .cip-topnav-inner {{
        flex-direction: column;
        padding: 12px;
    }}

    .cip-topnav-tabs {{
        width: 100%;
        justify-content: space-around;
    }}

    .cip-topnav-tab {{
        padding: 12px 16px;
    }}

    .cip-topnav-tab-label {{
        font-size: 11px;
    }}
}}

/* High Contrast Enhancements */
.cip-high-contrast .cip-topnav {{
    border-bottom-width: 3px;
}}

.cip-high-contrast .cip-topnav-tab:focus {{
    outline-width: 3px;
}}

.cip-high-contrast .cip-topnav-tab.active::after {{
    height: 4px;
}}

/* Print Styles */
@media print {{
    .cip-topnav {{
        position: relative;
        background: white;
        border-bottom: 2px solid #333;
    }}

    .cip-topnav-tab {{
        color: #333;
    }}

    .cip-topnav-actions {{
        display: none;
    }}
}}
</style>
"""


def inject_topnav_css() -> None:
    """Inject TopNav CSS styles into the page."""
    st.markdown(_generate_topnav_css(), unsafe_allow_html=True)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_active_tab_key() -> str:
    """Get session state key for active tab."""
    return "_cip_topnav_active_tab"


def init_topnav_state(default_tab: str = "upload") -> None:
    """Initialize TopNav state."""
    key = _get_active_tab_key()
    if key not in st.session_state:
        st.session_state[key] = default_tab


def get_active_tab() -> str:
    """Get the currently active tab ID."""
    init_topnav_state()
    return st.session_state.get(_get_active_tab_key(), "upload")


def set_active_tab(tab_id: str) -> None:
    """Set the active tab."""
    st.session_state[_get_active_tab_key()] = tab_id


# ============================================================================
# COMPONENT RENDERING
# ============================================================================

def render_topnav(
    tabs: Optional[List[NavTab]] = None,
    logo_text: str = "CIP",
    logo_icon: str = "📋",
    show_contrast_toggle: bool = True,
    on_tab_change: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Render the TopNav component.

    Args:
        tabs: List of NavTab definitions (defaults to DEFAULT_NAV_TABS)
        logo_text: Text for logo section
        logo_icon: Icon for logo section
        show_contrast_toggle: Whether to show contrast mode toggle
        on_tab_change: Callback when tab changes

    Returns:
        Currently active tab ID
    """
    # Initialize
    if tabs is None:
        tabs = DEFAULT_NAV_TABS

    init_topnav_state()
    inject_color_tokens()
    inject_topnav_css()

    active_tab = get_active_tab()
    high_contrast = is_high_contrast_mode()
    contrast_class = "cip-high-contrast" if high_contrast else ""

    # Build tabs HTML
    tabs_html = ""
    for tab in tabs:
        active_class = "active" if tab.tab_id == active_tab else ""
        disabled_class = "disabled" if tab.disabled else ""

        badge_html = ""
        if tab.badge_count is not None and tab.badge_count > 0:
            badge_html = f'<span class="cip-topnav-tab-badge">{tab.badge_count}</span>'

        tabs_html += f"""
        <button class="cip-topnav-tab {active_class} {disabled_class}"
                data-tab-id="{tab.tab_id}"
                title="{tab.description}"
                {'disabled' if tab.disabled else ''}
                tabindex="0"
                role="tab"
                aria-selected="{'true' if tab.tab_id == active_tab else 'false'}">
            <span class="cip-topnav-tab-icon">{tab.icon}</span>
            <span class="cip-topnav-tab-label">{tab.label}</span>
            {badge_html}
        </button>
        """

    # Contrast toggle HTML
    contrast_btn_class = "active" if high_contrast else ""
    contrast_html = f"""
    <button class="cip-topnav-contrast-btn {contrast_btn_class}"
            title="Toggle High Contrast Mode"
            tabindex="0">
        {'🔳' if high_contrast else '🔲'} Contrast
    </button>
    """ if show_contrast_toggle else ""

    # Render full nav
    st.markdown(f"""
    <div class="{contrast_class}">
        <nav class="cip-topnav" role="navigation" aria-label="Main navigation">
            <div class="cip-topnav-inner">
                <div class="cip-topnav-logo">
                    <span class="cip-topnav-logo-icon">{logo_icon}</span>
                    <span class="cip-topnav-logo-text">{logo_text}</span>
                </div>
                <div class="cip-topnav-tabs" role="tablist">
                    {tabs_html}
                </div>
                <div class="cip-topnav-actions">
                    {contrast_html}
                </div>
            </div>
        </nav>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit buttons for actual interaction
    tab_cols = st.columns(len(tabs) + 2)

    # Spacer
    with tab_cols[0]:
        st.empty()

    # Tab buttons
    for idx, tab in enumerate(tabs):
        with tab_cols[idx + 1]:
            if not tab.disabled:
                if st.button(
                    f"{tab.icon} {tab.label}",
                    key=f"topnav_tab_{tab.tab_id}",
                    use_container_width=True,
                    type="primary" if tab.tab_id == active_tab else "secondary",
                ):
                    set_active_tab(tab.tab_id)
                    if on_tab_change:
                        on_tab_change(tab.tab_id)
                    st.rerun()

    # Contrast toggle
    with tab_cols[-1]:
        if show_contrast_toggle:
            contrast_label = "🔳 HC On" if high_contrast else "🔲 HC Off"
            if st.button(contrast_label, key="topnav_contrast_toggle"):
                from components.color_tokens import toggle_high_contrast_mode
                toggle_high_contrast_mode()
                st.rerun()

    return active_tab


def render_topnav_minimal(
    tabs: Optional[List[NavTab]] = None,
) -> str:
    """
    Render a minimal TopNav without visual HTML (buttons only).

    Args:
        tabs: List of NavTab definitions

    Returns:
        Currently active tab ID
    """
    if tabs is None:
        tabs = DEFAULT_NAV_TABS

    init_topnav_state()
    active_tab = get_active_tab()

    cols = st.columns(len(tabs))

    for idx, tab in enumerate(tabs):
        with cols[idx]:
            btn_type = "primary" if tab.tab_id == active_tab else "secondary"
            if st.button(
                f"{tab.icon} {tab.label}",
                key=f"topnav_min_{tab.tab_id}",
                use_container_width=True,
                type=btn_type,
                disabled=tab.disabled,
            ):
                set_active_tab(tab.tab_id)
                st.rerun()

    return active_tab


# ============================================================================
# ACCESSIBILITY HELPERS
# ============================================================================

def get_topnav_aria_attributes() -> Dict[str, str]:
    """Get ARIA attributes for TopNav accessibility."""
    return {
        "role": "navigation",
        "aria-label": "Main navigation",
        "tablist_role": "tablist",
        "tab_role": "tab",
        "aria-selected": "true/false based on active state",
    }


def validate_topnav_accessibility(tabs: List[NavTab]) -> Dict[str, Any]:
    """
    Validate TopNav accessibility compliance.

    Returns:
        Validation results
    """
    issues = []

    # Check for unique IDs
    tab_ids = [t.tab_id for t in tabs]
    if len(tab_ids) != len(set(tab_ids)):
        issues.append("Duplicate tab IDs found")

    # Check for labels
    for tab in tabs:
        if not tab.label:
            issues.append(f"Tab {tab.tab_id} missing label")
        if not tab.description:
            issues.append(f"Tab {tab.tab_id} missing description (title)")

    # Check at least one tab is enabled
    enabled_tabs = [t for t in tabs if not t.disabled]
    if len(enabled_tabs) == 0:
        issues.append("All tabs are disabled")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "tab_count": len(tabs),
        "enabled_count": len(enabled_tabs),
    }
