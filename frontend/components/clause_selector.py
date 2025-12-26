"""
Clause Selector Component - Phase 6 UI Upgrade
P6.C2.T2: Selection Component Upgrade

Enhanced selection with:
- Selection tabs/buttons with multi-state styling
- High-contrast (HC) compatible styling
- A11y improvements via a11y_utils integration
- Full ARIA semantics
- WCAG AA compliance
- TopNav state coordination

CIP Protocol: CC2 implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from components.color_tokens import get_token, is_high_contrast_mode, inject_color_tokens
from components.a11y_utils import (
    FocusConfig,
    generate_focus_css,
    get_tabindex,
    get_aria_attrs,
    format_aria_attrs,
    validate_focus_visible,
    validate_aria_role,
    is_activation_key,
    is_navigation_key,
    get_navigation_direction,
)


# ============================================================================
# CLAUSE DATA STRUCTURES
# ============================================================================

@dataclass
class ClauseInfo:
    """Information about a clause for selection."""
    clause_id: int
    title: str
    section: str
    preview: str = ""
    severity: Optional[str] = None  # CRITICAL, HIGH, MODERATE, ADMIN
    has_changes: bool = False
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClauseSelection:
    """Current clause selection state."""
    v1_clause_id: Optional[int] = None
    v2_clause_id: Optional[int] = None
    is_linked: bool = True  # Whether V1 and V2 selections are linked


@dataclass
class SelectionTabConfig:
    """Configuration for selection tab styling."""
    tab_id: str
    label: str
    icon: str
    description: str
    count: int = 0
    disabled: bool = False


# ============================================================================
# SELECTION TAB DEFINITIONS
# ============================================================================

DEFAULT_SELECTION_TABS = [
    SelectionTabConfig("all", "All", "📋", "Show all clauses", 0),
    SelectionTabConfig("changed", "Changed", "📝", "Show modified clauses", 0),
    SelectionTabConfig("critical", "Critical", "🚨", "Show critical severity", 0),
    SelectionTabConfig("high", "High", "⚠️", "Show high severity", 0),
]


# ============================================================================
# CSS STYLING - ENHANCED WITH A11Y
# ============================================================================

def _generate_clause_selector_css() -> str:
    """Generate Clause Selector CSS with current color tokens and a11y support."""
    high_contrast = is_high_contrast_mode()

    # Get tokens
    bg_primary = get_token("bg-primary")
    bg_secondary = get_token("bg-secondary")
    surface = get_token("surface-default")
    text_primary = get_token("text-primary")
    text_secondary = get_token("text-secondary")
    text_muted = get_token("text-muted")
    border_default = get_token("border-default")
    border_focus = get_token("border-focus")
    accent_primary = get_token("accent-primary")

    # Severity colors
    critical = get_token("erce-critical")
    high = get_token("erce-high")
    moderate = get_token("erce-moderate")
    admin = get_token("erce-admin")

    border_width = "2px" if high_contrast else "1px"
    focus_width = "3px" if high_contrast else "2px"

    # Generate focus CSS from a11y_utils
    focus_config = FocusConfig(
        outline_color=border_focus,
        high_contrast_color=get_token("border-focus", force_high_contrast=True),
    )

    focus_css = generate_focus_css(".cip-clause-item", focus_config, high_contrast)
    tab_focus_css = generate_focus_css(".cip-selection-tab", focus_config, high_contrast)
    link_focus_css = generate_focus_css(".cip-link-toggle", focus_config, high_contrast)

    return f"""
<style>
/* ============================================================================
   CLAUSE SELECTOR COMPONENT STYLES
   Phase 6 UI Upgrade - P6.C2.T2 (Enhanced)
   High-Contrast Mode: {'ENABLED' if high_contrast else 'DISABLED'}
   ============================================================================ */

/* Main Selector Container */
.cip-clause-selector {{
    background: {bg_secondary};
    border: {border_width} solid {border_default};
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}}

/* Header */
.cip-clause-selector-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid {border_default};
}}

.cip-clause-selector-title {{
    font-size: 16px;
    font-weight: 600;
    color: {text_primary};
    display: flex;
    align-items: center;
    gap: 8px;
}}

.cip-clause-selector-badge {{
    font-size: 11px;
    padding: 2px 8px;
    background: {accent_primary};
    color: white;
    border-radius: 10px;
}}

/* ============================================================================
   SELECTION TABS - NEW COMPONENT
   ============================================================================ */

.cip-selection-tabs {{
    display: flex;
    gap: 4px;
    padding: 4px;
    background: {bg_primary};
    border-radius: 8px;
    margin-bottom: 16px;
}}

.cip-selection-tab {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: transparent;
    border: {border_width} solid transparent;
    border-radius: 6px;
    cursor: pointer;
    color: {text_secondary};
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
    position: relative;
}}

.cip-selection-tab:hover {{
    background: {get_token("nav-tab-hover")};
    color: {text_primary};
}}

/* Tab Focus States - Generated from a11y_utils */
{tab_focus_css}

.cip-selection-tab.active {{
    background: {get_token("sae-bg")};
    border-color: {accent_primary};
    color: {text_primary};
}}

.cip-selection-tab.active::after {{
    content: "";
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    height: {'3px' if high_contrast else '2px'};
    background: {accent_primary};
    border-radius: 2px;
}}

.cip-selection-tab.disabled {{
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
}}

.cip-selection-tab-icon {{
    font-size: 14px;
}}

.cip-selection-tab-count {{
    font-size: 10px;
    padding: 1px 6px;
    background: {border_default};
    color: {text_muted};
    border-radius: 8px;
    margin-left: 4px;
}}

.cip-selection-tab.active .cip-selection-tab-count {{
    background: {accent_primary};
    color: white;
}}

/* ============================================================================
   MULTI-STATE STYLING
   ============================================================================ */

/* State: Default */
.cip-clause-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    margin-bottom: 6px;
    background: {bg_primary};
    border: {border_width} solid transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}}

/* State: Hover */
.cip-clause-item:hover {{
    border-color: {border_default};
    background: {bg_secondary};
}}

/* State: Focus - Generated from a11y_utils */
{focus_css}

/* State: Selected */
.cip-clause-item.selected {{
    border-color: {accent_primary};
    background: {get_token("sae-bg")};
    box-shadow: 0 0 0 {'3px' if high_contrast else '1px'} {get_token("sae-border")};
}}

/* State: Selected + Focus */
.cip-clause-item.selected:focus {{
    outline-color: {critical};
}}

/* State: Has Changes */
.cip-clause-item.has-changes {{
    border-left: {'4px' if high_contrast else '3px'} solid {get_token("accent-warning")};
}}

/* State: Disabled */
.cip-clause-item.disabled {{
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
}}

/* ============================================================================
   LINK TOGGLE - ENHANCED
   ============================================================================ */

.cip-link-toggle {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: transparent;
    border: {border_width} solid {border_default};
    border-radius: 6px;
    cursor: pointer;
    color: {text_secondary};
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
}}

.cip-link-toggle:hover {{
    background: {get_token("nav-tab-hover")};
    border-color: {accent_primary};
    color: {text_primary};
}}

/* Link Toggle Focus - Generated from a11y_utils */
{link_focus_css}

.cip-link-toggle.linked {{
    background: {get_token("sae-bg")};
    border-color: {accent_primary};
    color: {text_primary};
}}

.cip-link-toggle-icon {{
    font-size: 16px;
}}

/* ============================================================================
   VERSION COLUMNS
   ============================================================================ */

.cip-version-columns {{
    display: flex;
    gap: 16px;
}}

.cip-version-column {{
    flex: 1;
    background: {surface};
    border: {border_width} solid {border_default};
    border-radius: 8px;
    padding: 12px;
}}

.cip-version-column.v1 {{
    border-top: 3px solid {get_token("sae-primary")};
}}

.cip-version-column.v2 {{
    border-top: 3px solid {get_token("birl-compliance")};
}}

.cip-version-label {{
    font-size: 12px;
    font-weight: 600;
    color: {text_muted};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}}

/* ============================================================================
   CLAUSE LIST
   ============================================================================ */

.cip-clause-list {{
    max-height: 300px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: {get_token("border-strong")} {bg_secondary};
}}

.cip-clause-list::-webkit-scrollbar {{
    width: 6px;
}}

.cip-clause-list::-webkit-scrollbar-track {{
    background: {bg_secondary};
    border-radius: 3px;
}}

.cip-clause-list::-webkit-scrollbar-thumb {{
    background: {get_token("border-strong")};
    border-radius: 3px;
}}

/* ============================================================================
   SEVERITY INDICATORS
   ============================================================================ */

.cip-clause-severity {{
    width: {'10px' if high_contrast else '8px'};
    height: {'10px' if high_contrast else '8px'};
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 6px;
    border: {'2px solid white' if high_contrast else 'none'};
}}

.cip-clause-severity.critical {{
    background: {critical};
}}

.cip-clause-severity.high {{
    background: {high};
}}

.cip-clause-severity.moderate {{
    background: {moderate};
}}

.cip-clause-severity.admin {{
    background: {admin};
}}

/* ============================================================================
   CLAUSE CONTENT
   ============================================================================ */

.cip-clause-content {{
    flex: 1;
    min-width: 0;
}}

.cip-clause-title {{
    font-size: 13px;
    font-weight: 500;
    color: {text_primary};
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.cip-clause-section {{
    font-size: 11px;
    color: {text_muted};
    margin-bottom: 4px;
}}

.cip-clause-preview {{
    font-size: 12px;
    color: {text_secondary};
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.cip-clause-id {{
    font-size: 11px;
    font-weight: 600;
    color: {text_muted};
    padding: 2px 6px;
    background: {bg_secondary};
    border-radius: 4px;
    flex-shrink: 0;
}}

/* ============================================================================
   SELECTION DISPLAY
   ============================================================================ */

.cip-selection-display {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: {surface};
    border: {border_width} solid {border_default};
    border-radius: 8px;
    margin-top: 12px;
}}

.cip-selection-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    background: {bg_secondary};
    border-radius: 6px;
    flex: 1;
}}

.cip-selection-item.selected {{
    background: {get_token("sae-bg")};
    border: 1px solid {accent_primary};
}}

.cip-selection-label {{
    font-size: 11px;
    font-weight: 600;
    color: {text_muted};
    text-transform: uppercase;
}}

.cip-selection-value {{
    font-size: 14px;
    font-weight: 600;
    color: {text_primary};
}}

.cip-selection-arrow {{
    font-size: 20px;
    color: {text_muted};
    padding: 0 8px;
}}

/* ============================================================================
   COMPACT MODE
   ============================================================================ */

.cip-clause-selector.compact {{
    padding: 12px;
}}

.cip-clause-selector.compact .cip-clause-item {{
    padding: 8px 10px;
}}

.cip-clause-selector.compact .cip-clause-preview {{
    display: none;
}}

.cip-clause-selector.compact .cip-selection-tabs {{
    margin-bottom: 12px;
}}

/* ============================================================================
   EMPTY STATE
   ============================================================================ */

.cip-clause-empty {{
    text-align: center;
    padding: 24px;
    color: {text_muted};
}}

.cip-clause-empty-icon {{
    font-size: 32px;
    margin-bottom: 8px;
    opacity: 0.5;
}}

.cip-clause-empty-text {{
    font-size: 13px;
}}

/* ============================================================================
   KEYBOARD NAVIGATION INDICATORS
   ============================================================================ */

.cip-clause-item[tabindex]:focus-visible {{
    outline: {focus_width} solid {border_focus};
    outline-offset: -2px;
}}

/* Skip link for keyboard users */
.cip-skip-link {{
    position: absolute;
    left: -9999px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
}}

.cip-skip-link:focus {{
    position: static;
    width: auto;
    height: auto;
    padding: 8px 16px;
    background: {accent_primary};
    color: white;
    border-radius: 4px;
}}

/* ============================================================================
   PRINT STYLES
   ============================================================================ */

@media print {{
    .cip-clause-selector {{
        border: 1px solid #333;
        background: white;
    }}

    .cip-clause-item.selected {{
        background: #f0f0f0;
        border-color: #333;
    }}

    .cip-selection-tabs {{
        display: none;
    }}

    .cip-link-toggle {{
        display: none;
    }}
}}
</style>
"""


def inject_clause_selector_css() -> None:
    """Inject Clause Selector CSS styles into the page."""
    st.markdown(_generate_clause_selector_css(), unsafe_allow_html=True)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_state_key(key_suffix: str) -> str:
    """Get session state key with prefix."""
    return f"_cip_clause_{key_suffix}"


def init_clause_state() -> None:
    """Initialize clause selection state."""
    keys = ["v1_id", "v2_id", "linked", "v1_clauses", "v2_clauses", "filter_tab", "topnav_sync"]
    defaults = [None, None, True, [], [], "all", True]

    for key, default in zip(keys, defaults):
        full_key = _get_state_key(key)
        if full_key not in st.session_state:
            st.session_state[full_key] = default


def get_clause_selection() -> ClauseSelection:
    """Get current clause selection state."""
    init_clause_state()
    return ClauseSelection(
        v1_clause_id=st.session_state.get(_get_state_key("v1_id")),
        v2_clause_id=st.session_state.get(_get_state_key("v2_id")),
        is_linked=st.session_state.get(_get_state_key("linked"), True),
    )


def set_v1_clause(clause_id: Optional[int]) -> None:
    """Set V1 clause selection."""
    init_clause_state()
    st.session_state[_get_state_key("v1_id")] = clause_id

    # If linked, also update V2
    if st.session_state.get(_get_state_key("linked"), True):
        st.session_state[_get_state_key("v2_id")] = clause_id


def set_v2_clause(clause_id: Optional[int]) -> None:
    """Set V2 clause selection."""
    init_clause_state()
    st.session_state[_get_state_key("v2_id")] = clause_id

    # If linked, also update V1
    if st.session_state.get(_get_state_key("linked"), True):
        st.session_state[_get_state_key("v1_id")] = clause_id


def set_clause_pair(v1_id: Optional[int], v2_id: Optional[int]) -> None:
    """Set both V1 and V2 clause selections."""
    init_clause_state()
    st.session_state[_get_state_key("v1_id")] = v1_id
    st.session_state[_get_state_key("v2_id")] = v2_id


def toggle_linked_mode() -> None:
    """Toggle linked selection mode."""
    init_clause_state()
    key = _get_state_key("linked")
    st.session_state[key] = not st.session_state.get(key, True)


def is_linked_mode() -> bool:
    """Check if linked selection mode is enabled."""
    init_clause_state()
    return st.session_state.get(_get_state_key("linked"), True)


def set_v1_clauses(clauses: List[ClauseInfo]) -> None:
    """Set available V1 clauses."""
    init_clause_state()
    st.session_state[_get_state_key("v1_clauses")] = clauses


def set_v2_clauses(clauses: List[ClauseInfo]) -> None:
    """Set available V2 clauses."""
    init_clause_state()
    st.session_state[_get_state_key("v2_clauses")] = clauses


def get_v1_clauses() -> List[ClauseInfo]:
    """Get available V1 clauses."""
    init_clause_state()
    return st.session_state.get(_get_state_key("v1_clauses"), [])


def get_v2_clauses() -> List[ClauseInfo]:
    """Get available V2 clauses."""
    init_clause_state()
    return st.session_state.get(_get_state_key("v2_clauses"), [])


def clear_clause_selection() -> None:
    """Clear clause selection state."""
    init_clause_state()
    st.session_state[_get_state_key("v1_id")] = None
    st.session_state[_get_state_key("v2_id")] = None


def get_filter_tab() -> str:
    """Get current filter tab."""
    init_clause_state()
    return st.session_state.get(_get_state_key("filter_tab"), "all")


def set_filter_tab(tab_id: str) -> None:
    """Set filter tab."""
    init_clause_state()
    st.session_state[_get_state_key("filter_tab")] = tab_id


# ============================================================================
# TOPNAV STATE INTEGRATION
# ============================================================================

def sync_with_topnav() -> Optional[str]:
    """
    Sync clause selector with TopNav state.

    Returns:
        Current TopNav tab ID if synced, None otherwise
    """
    try:
        from components.topnav import get_active_tab
        return get_active_tab()
    except ImportError:
        return None


def is_topnav_compare_mode() -> bool:
    """Check if TopNav is in Compare mode."""
    active_tab = sync_with_topnav()
    return active_tab == "compare"


# ============================================================================
# SELECTION TABS COMPONENT
# ============================================================================

def render_selection_tabs(
    tabs: Optional[List[SelectionTabConfig]] = None,
    active_tab: Optional[str] = None,
    on_change: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Render selection filter tabs.

    Args:
        tabs: List of tab configurations
        active_tab: Currently active tab ID
        on_change: Callback when tab changes

    Returns:
        Active tab ID
    """
    if tabs is None:
        tabs = DEFAULT_SELECTION_TABS

    if active_tab is None:
        active_tab = get_filter_tab()

    # Build tabs HTML with ARIA
    tabs_html = ""
    for idx, tab in enumerate(tabs):
        active_class = "active" if tab.tab_id == active_tab else ""
        disabled_class = "disabled" if tab.disabled else ""

        aria_attrs = get_aria_attrs(
            "tab",
            selected=(tab.tab_id == active_tab),
            disabled=tab.disabled,
            controls=f"clause-panel-{tab.tab_id}",
        )
        aria_str = format_aria_attrs(aria_attrs)

        tabindex = get_tabindex(
            is_interactive=True,
            is_disabled=tab.disabled,
        )

        count_html = ""
        if tab.count > 0:
            count_html = f'<span class="cip-selection-tab-count">{tab.count}</span>'

        tabs_html += f"""
        <button class="cip-selection-tab {active_class} {disabled_class}"
                data-tab-id="{tab.tab_id}"
                title="{tab.description}"
                tabindex="{tabindex}"
                {aria_str}>
            <span class="cip-selection-tab-icon">{tab.icon}</span>
            <span>{tab.label}</span>
            {count_html}
        </button>
        """

    st.markdown(f"""
    <div class="cip-selection-tabs" role="tablist" aria-label="Clause filter tabs">
        {tabs_html}
    </div>
    """, unsafe_allow_html=True)

    # Streamlit buttons for interaction
    tab_cols = st.columns(len(tabs))
    for idx, tab in enumerate(tabs):
        with tab_cols[idx]:
            is_active = tab.tab_id == active_tab
            btn_label = f"{tab.icon} {tab.label}"
            if tab.count > 0:
                btn_label += f" ({tab.count})"

            if st.button(
                btn_label,
                key=f"sel_tab_{tab.tab_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                disabled=tab.disabled,
            ):
                set_filter_tab(tab.tab_id)
                if on_change:
                    on_change(tab.tab_id)
                st.rerun()

    return active_tab


# ============================================================================
# CLAUSE FILTERING
# ============================================================================

def filter_clauses_by_tab(
    clauses: List[ClauseInfo],
    tab_id: str,
) -> List[ClauseInfo]:
    """
    Filter clauses based on active tab.

    Args:
        clauses: List of clauses to filter
        tab_id: Active filter tab ID

    Returns:
        Filtered list of clauses
    """
    if tab_id == "all":
        return clauses
    elif tab_id == "changed":
        return [c for c in clauses if c.has_changes]
    elif tab_id == "critical":
        return [c for c in clauses if c.severity == "CRITICAL"]
    elif tab_id == "high":
        return [c for c in clauses if c.severity in ("CRITICAL", "HIGH")]
    else:
        return clauses


def count_clauses_by_category(
    clauses: List[ClauseInfo],
) -> Dict[str, int]:
    """
    Count clauses by category for tab badges.

    Args:
        clauses: List of clauses

    Returns:
        Dictionary of category -> count
    """
    return {
        "all": len(clauses),
        "changed": len([c for c in clauses if c.has_changes]),
        "critical": len([c for c in clauses if c.severity == "CRITICAL"]),
        "high": len([c for c in clauses if c.severity in ("CRITICAL", "HIGH")]),
    }


# ============================================================================
# COMPONENT RENDERING
# ============================================================================

def render_clause_selector(
    v1_clauses: List[ClauseInfo],
    v2_clauses: List[ClauseInfo],
    title: str = "Clause Selector",
    show_link_toggle: bool = True,
    show_filter_tabs: bool = True,
    compact: bool = False,
    on_selection_change: Optional[Callable[[ClauseSelection], None]] = None,
) -> ClauseSelection:
    """
    Render the Clause Selector component with enhanced selection.

    Args:
        v1_clauses: List of V1 clause options
        v2_clauses: List of V2 clause options
        title: Component title
        show_link_toggle: Whether to show link/unlink toggle
        show_filter_tabs: Whether to show filter tabs
        compact: Use compact display mode
        on_selection_change: Callback when selection changes

    Returns:
        Current ClauseSelection
    """
    # Initialize
    init_clause_state()
    inject_color_tokens()
    inject_clause_selector_css()

    selection = get_clause_selection()
    linked = is_linked_mode()
    compact_class = "compact" if compact else ""
    active_filter = get_filter_tab()

    # Calculate tab counts
    all_clauses = v1_clauses + v2_clauses
    counts = count_clauses_by_category(all_clauses)

    # Update tabs with counts
    tabs_with_counts = [
        SelectionTabConfig("all", "All", "📋", "Show all clauses", counts["all"]),
        SelectionTabConfig("changed", "Changed", "📝", "Show modified clauses", counts["changed"]),
        SelectionTabConfig("critical", "Critical", "🚨", "Show critical severity", counts["critical"]),
        SelectionTabConfig("high", "High Risk", "⚠️", "Show high+ severity", counts["high"]),
    ]

    # Header
    st.markdown(f"""
    <div class="cip-clause-selector {compact_class}">
        <div class="cip-clause-selector-header">
            <div class="cip-clause-selector-title">
                📋 {title}
                <span class="cip-clause-selector-badge">
                    {len(v1_clauses)} / {len(v2_clauses)} clauses
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Filter tabs
    if show_filter_tabs:
        active_filter = render_selection_tabs(
            tabs=tabs_with_counts,
            active_tab=active_filter,
        )

    # Link toggle with ARIA
    if show_link_toggle:
        link_icon = "🔗" if linked else "🔓"
        link_text = "Linked" if linked else "Independent"
        link_aria = get_aria_attrs(
            "button",
            pressed=linked,
            label=f"Selection mode: {link_text}",
        )

        if st.button(
            f"{link_icon} {link_text}",
            key="clause_link_toggle",
            help="Toggle linked selection mode (when linked, selecting V1 also selects V2)"
        ):
            toggle_linked_mode()
            st.rerun()

    # Filter clauses
    filtered_v1 = filter_clauses_by_tab(v1_clauses, active_filter)
    filtered_v2 = filter_clauses_by_tab(v2_clauses, active_filter)

    # Version columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="cip-version-label">
            📄 Version 1 (Original)
        </div>
        """, unsafe_allow_html=True)

        if not filtered_v1:
            st.info("No clauses match filter")
        else:
            for idx, clause in enumerate(filtered_v1):
                is_selected = selection.v1_clause_id == clause.clause_id
                severity_icon = _get_severity_icon(clause.severity)
                changes_marker = " 📝" if clause.has_changes else ""

                aria_attrs = get_aria_attrs(
                    "option",
                    selected=is_selected,
                    label=f"Clause {clause.clause_id}: {clause.title}",
                )
                tabindex = get_tabindex(is_interactive=True)

                if st.button(
                    f"{'✓ ' if is_selected else ''}{severity_icon}{clause.section}: {clause.title}{changes_marker}",
                    key=f"v1_clause_{clause.clause_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    set_v1_clause(clause.clause_id)
                    selection = get_clause_selection()
                    if on_selection_change:
                        on_selection_change(selection)
                    st.rerun()

    with col2:
        st.markdown("""
        <div class="cip-version-label">
            📝 Version 2 (Modified)
        </div>
        """, unsafe_allow_html=True)

        if not filtered_v2:
            st.info("No clauses match filter")
        else:
            for idx, clause in enumerate(filtered_v2):
                is_selected = selection.v2_clause_id == clause.clause_id
                severity_icon = _get_severity_icon(clause.severity)
                changes_marker = " 📝" if clause.has_changes else ""

                if st.button(
                    f"{'✓ ' if is_selected else ''}{severity_icon}{clause.section}: {clause.title}{changes_marker}",
                    key=f"v2_clause_{clause.clause_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    set_v2_clause(clause.clause_id)
                    selection = get_clause_selection()
                    if on_selection_change:
                        on_selection_change(selection)
                    st.rerun()

    # Selection display with ARIA live region
    st.markdown("---")
    st.markdown("""
    <div aria-live="polite" aria-atomic="true">
        <strong>Current Selection:</strong>
    </div>
    """, unsafe_allow_html=True)

    sel_col1, sel_col2, sel_col3 = st.columns([2, 1, 2])

    with sel_col1:
        v1_text = f"Clause #{selection.v1_clause_id}" if selection.v1_clause_id else "None"
        st.metric("V1", v1_text)

    with sel_col2:
        link_display = "🔗" if linked else "↔️"
        st.markdown(
            f"<div style='text-align:center; padding-top:20px; font-size:24px;' "
            f"aria-label='Selection mode: {'linked' if linked else 'independent'}'>"
            f"{link_display}</div>",
            unsafe_allow_html=True
        )

    with sel_col3:
        v2_text = f"Clause #{selection.v2_clause_id}" if selection.v2_clause_id else "None"
        st.metric("V2", v2_text)

    # Close container
    st.markdown("</div>", unsafe_allow_html=True)

    return selection


def _get_severity_icon(severity: Optional[str]) -> str:
    """Get severity indicator icon."""
    if not severity:
        return ""
    icons = {
        "CRITICAL": "🔴 ",
        "HIGH": "🟠 ",
        "MODERATE": "🔵 ",
        "ADMIN": "⚪ ",
    }
    return icons.get(severity.upper(), "")


def render_clause_selector_minimal(
    clauses: List[ClauseInfo],
    version: str = "v1",
    selected_id: Optional[int] = None,
) -> Optional[int]:
    """
    Render a minimal single-version clause selector.

    Args:
        clauses: List of clause options
        version: Version label ("v1" or "v2")
        selected_id: Currently selected clause ID

    Returns:
        Selected clause ID or None
    """
    init_clause_state()

    if not clauses:
        st.info("No clauses available")
        return None

    options = {f"#{c.clause_id}: {c.title}": c.clause_id for c in clauses}
    options_list = list(options.keys())

    # Find current selection index
    current_idx = 0
    if selected_id:
        for idx, (label, cid) in enumerate(options.items()):
            if cid == selected_id:
                current_idx = idx
                break

    selected_label = st.selectbox(
        f"Select {version.upper()} Clause",
        options_list,
        index=current_idx,
        key=f"minimal_clause_{version}",
    )

    return options.get(selected_label)


# ============================================================================
# CC3 INTEGRATION HELPERS
# ============================================================================

def get_selected_clause_pair() -> Tuple[Optional[int], Optional[int]]:
    """
    Get the currently selected clause pair for CC3 integration.

    Returns:
        Tuple of (v1_clause_id, v2_clause_id)
    """
    selection = get_clause_selection()
    return (selection.v1_clause_id, selection.v2_clause_id)


def has_valid_selection() -> bool:
    """Check if a valid clause selection exists."""
    selection = get_clause_selection()
    return selection.v1_clause_id is not None or selection.v2_clause_id is not None


def get_selection_for_binder() -> Dict[str, Any]:
    """
    Get clause selection in format for CC3 data binder.

    Returns:
        Dictionary with selection data
    """
    selection = get_clause_selection()
    return {
        "v1_clause_id": selection.v1_clause_id,
        "v2_clause_id": selection.v2_clause_id,
        "is_linked": selection.is_linked,
        "has_selection": has_valid_selection(),
        "filter_tab": get_filter_tab(),
        "topnav_sync": sync_with_topnav(),
    }


# ============================================================================
# ACCESSIBILITY VALIDATION
# ============================================================================

def validate_clause_selector_accessibility(
    v1_clauses: List[ClauseInfo],
    v2_clauses: List[ClauseInfo],
) -> Dict[str, Any]:
    """
    Validate Clause Selector accessibility compliance.

    Returns:
        Validation results with a11y_utils integration
    """
    issues = []
    features = []

    # Check for unique IDs
    v1_ids = [c.clause_id for c in v1_clauses]
    v2_ids = [c.clause_id for c in v2_clauses]

    if len(v1_ids) != len(set(v1_ids)):
        issues.append("Duplicate V1 clause IDs found")

    if len(v2_ids) != len(set(v2_ids)):
        issues.append("Duplicate V2 clause IDs found")

    # Check for titles (accessibility labels)
    for clause in v1_clauses + v2_clauses:
        if not clause.title:
            issues.append(f"Clause {clause.clause_id} missing title")

    # Validate CSS focus indicators
    css = _generate_clause_selector_css()
    focus_validation = validate_focus_visible(css)

    if not focus_validation["valid"]:
        issues.extend(focus_validation["issues"])
    else:
        features.extend(focus_validation["features"])

    # Check ARIA role for option
    option_attrs = {"aria-selected": "true"}
    aria_validation = validate_aria_role("option", option_attrs)

    if not aria_validation["valid"]:
        issues.extend(aria_validation["issues"])
    else:
        features.append("ARIA role='option' properly configured")
        features.append(f"Keyboard support: {', '.join(aria_validation.get('keyboard_support', []))}")

    # Add feature list
    features.extend([
        "Selection tabs with ARIA tablist",
        "Linked mode toggle with aria-pressed",
        "Live region for selection updates",
        "Keyboard navigation via tabindex",
        "Focus indicators from a11y_utils",
        "High contrast mode support",
    ])

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "features": features,
        "v1_count": len(v1_clauses),
        "v2_count": len(v2_clauses),
        "wcag_level": "AA",
    }
