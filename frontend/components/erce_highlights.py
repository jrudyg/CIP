"""
ERCE Risk Highlight Component - Phase 5 UX Upgrade Task 2

Provides color-coded risk highlighting and filtering controls for ERCE output.
Surfaces ERCE severity levels (CRITICAL, HIGH, MODERATE, ADMIN) with visual
distinction and allows users to filter by severity.

CIP Protocol: CC implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Set
import hashlib


# ============================================================================
# ERCE SEVERITY LEVELS
# ============================================================================

ERCE_SEVERITY_LEVELS = {
    "CRITICAL": {
        "color": "#DC2626",       # Red-600
        "bg_color": "#FEF2F2",    # Red-50
        "border_color": "#FECACA", # Red-200
        "icon": "🔴",
        "label": "Critical Risk",
        "description": "Immediate action required - significant exposure",
        "css_class": "risk-critical",
    },
    "HIGH": {
        "color": "#D97706",       # Amber-600
        "bg_color": "#FFFBEB",    # Amber-50
        "border_color": "#FDE68A", # Amber-200
        "icon": "🟠",
        "label": "High Risk",
        "description": "Requires review - material risk exposure",
        "css_class": "risk-high",
    },
    "MODERATE": {
        "color": "#2563EB",       # Blue-600
        "bg_color": "#EFF6FF",    # Blue-50
        "border_color": "#BFDBFE", # Blue-200
        "icon": "🟡",
        "label": "Moderate Risk",
        "description": "Monitor - some risk exposure",
        "css_class": "risk-moderate",
    },
    "ADMIN": {
        "color": "#6B7280",       # Gray-500
        "bg_color": "#F9FAFB",    # Gray-50
        "border_color": "#E5E7EB", # Gray-200
        "icon": "🟢",
        "label": "Administrative",
        "description": "Low priority - administrative changes",
        "css_class": "risk-admin",
    },
}

# Default filter state - all enabled
DEFAULT_FILTER_STATE = {"CRITICAL": True, "HIGH": True, "MODERATE": True, "ADMIN": True}


# ============================================================================
# CSS STYLING
# ============================================================================

ERCE_HIGHLIGHT_CSS = """
<style>
/* ============================================================================
   ERCE RISK HIGHLIGHT COMPONENT STYLES
   Phase 5 UX Upgrade - Task 2
   ============================================================================ */

/* Risk Card Base */
.erce-risk-card {
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 4px solid;
    transition: all 0.2s ease;
    animation: erceSlideIn 0.3s ease-out;
}

.erce-risk-card:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

@keyframes erceSlideIn {
    from {
        opacity: 0;
        transform: translateX(-10px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* CRITICAL Risk */
.risk-critical {
    background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
    border-left-color: #DC2626;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.15);
}

.risk-critical:hover {
    box-shadow: 0 4px 16px rgba(220, 38, 38, 0.25);
}

.risk-critical .erce-severity-badge {
    background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
    color: white;
}

/* HIGH Risk */
.risk-high {
    background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
    border-left-color: #D97706;
    box-shadow: 0 2px 8px rgba(217, 119, 6, 0.15);
}

.risk-high:hover {
    box-shadow: 0 4px 16px rgba(217, 119, 6, 0.25);
}

.risk-high .erce-severity-badge {
    background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
    color: white;
}

/* MODERATE Risk */
.risk-moderate {
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    border-left-color: #2563EB;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.risk-moderate:hover {
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.25);
}

.risk-moderate .erce-severity-badge {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
    color: white;
}

/* ADMIN Risk */
.risk-admin {
    background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
    border-left-color: #6B7280;
    box-shadow: 0 2px 8px rgba(107, 114, 128, 0.1);
}

.risk-admin:hover {
    box-shadow: 0 4px 16px rgba(107, 114, 128, 0.2);
}

.risk-admin .erce-severity-badge {
    background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
    color: white;
}

/* Card Header */
.erce-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.erce-card-title {
    font-size: 14px;
    font-weight: 600;
    color: #1F2937;
    display: flex;
    align-items: center;
    gap: 8px;
}

.erce-severity-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Card Body */
.erce-card-body {
    font-size: 13px;
    color: #374151;
    line-height: 1.6;
}

.erce-detail-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.erce-detail-row:last-child {
    border-bottom: none;
}

.erce-detail-key {
    color: #6B7280;
    font-size: 12px;
}

.erce-detail-value {
    font-weight: 500;
    color: #1F2937;
    font-size: 13px;
}

/* Pattern Reference */
.erce-pattern-ref {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
    font-size: 11px;
    font-family: 'Monaco', 'Consolas', monospace;
    color: #4B5563;
}

/* Confidence Bar */
.erce-confidence-bar {
    width: 100%;
    height: 4px;
    background: rgba(0, 0, 0, 0.1);
    border-radius: 2px;
    margin-top: 8px;
    overflow: hidden;
}

.erce-confidence-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
}

.erce-confidence-fill.critical { background: #DC2626; }
.erce-confidence-fill.high { background: #D97706; }
.erce-confidence-fill.moderate { background: #2563EB; }
.erce-confidence-fill.admin { background: #6B7280; }

/* Success Probability Indicator */
.erce-probability {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
}

.erce-probability-good { color: #059669; }
.erce-probability-medium { color: #D97706; }
.erce-probability-low { color: #DC2626; }

/* Filter Sidebar Controls */
.erce-filter-container {
    background: #1E293B;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.erce-filter-title {
    font-size: 14px;
    font-weight: 600;
    color: #F1F5F9;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.erce-filter-option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s ease;
}

.erce-filter-option:hover {
    background: rgba(255, 255, 255, 0.1);
}

.erce-filter-checkbox {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid currentColor;
    display: flex;
    align-items: center;
    justify-content: center;
}

.erce-filter-checkbox.checked::after {
    content: '✓';
    font-size: 10px;
    color: white;
}

.erce-filter-label {
    flex: 1;
    font-size: 13px;
    color: #E2E8F0;
}

.erce-filter-count {
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.1);
    color: #94A3B8;
}

/* Inline Highlight */
.erce-inline-highlight {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
}

.erce-inline-critical {
    background: rgba(220, 38, 38, 0.15);
    color: #DC2626;
    border: 1px solid rgba(220, 38, 38, 0.3);
}

.erce-inline-high {
    background: rgba(217, 119, 6, 0.15);
    color: #B45309;
    border: 1px solid rgba(217, 119, 6, 0.3);
}

.erce-inline-moderate {
    background: rgba(37, 99, 235, 0.15);
    color: #2563EB;
    border: 1px solid rgba(37, 99, 235, 0.3);
}

.erce-inline-admin {
    background: rgba(107, 114, 128, 0.15);
    color: #6B7280;
    border: 1px solid rgba(107, 114, 128, 0.3);
}

/* Summary Stats */
.erce-summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}

.erce-summary-stat {
    text-align: center;
    padding: 12px;
    border-radius: 8px;
    background: #1E293B;
}

.erce-summary-count {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
}

.erce-summary-label {
    font-size: 11px;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.erce-summary-critical .erce-summary-count { color: #EF4444; }
.erce-summary-high .erce-summary-count { color: #F59E0B; }
.erce-summary-moderate .erce-summary-count { color: #3B82F6; }
.erce-summary-admin .erce-summary-count { color: #9CA3AF; }

/* Hidden state for filtering */
.erce-hidden {
    display: none !important;
}
</style>
"""


def inject_erce_highlight_css() -> None:
    """Inject ERCE highlight CSS styles into the page."""
    st.markdown(ERCE_HIGHLIGHT_CSS, unsafe_allow_html=True)


# ============================================================================
# FILTER STATE MANAGEMENT
# ============================================================================

def _get_filter_state_key() -> str:
    """Get session state key for ERCE filter."""
    return "_erce_filter_state"


def init_erce_filter_state() -> None:
    """Initialize ERCE filter state in session."""
    key = _get_filter_state_key()
    if key not in st.session_state:
        st.session_state[key] = DEFAULT_FILTER_STATE.copy()


def get_erce_filter_state() -> Dict[str, bool]:
    """Get current ERCE filter state."""
    init_erce_filter_state()
    return st.session_state[_get_filter_state_key()]


def set_erce_filter(severity: str, enabled: bool) -> None:
    """Set filter state for a specific severity level."""
    init_erce_filter_state()
    st.session_state[_get_filter_state_key()][severity] = enabled


def toggle_erce_filter(severity: str) -> None:
    """Toggle filter state for a specific severity level."""
    init_erce_filter_state()
    current = st.session_state[_get_filter_state_key()].get(severity, True)
    st.session_state[_get_filter_state_key()][severity] = not current


def reset_erce_filters() -> None:
    """Reset all filters to default (all enabled)."""
    st.session_state[_get_filter_state_key()] = DEFAULT_FILTER_STATE.copy()


def is_severity_visible(severity: str) -> bool:
    """Check if a severity level is visible based on current filter state."""
    filter_state = get_erce_filter_state()
    return filter_state.get(severity.upper(), True)


# ============================================================================
# FILTER SIDEBAR COMPONENT
# ============================================================================

def render_erce_filter_sidebar(
    erce_results: List[Dict[str, Any]],
    title: str = "Risk Filter"
) -> None:
    """
    Render ERCE severity filter controls in the sidebar.

    Args:
        erce_results: List of ERCE result dictionaries
        title: Title for the filter section
    """
    init_erce_filter_state()
    filter_state = get_erce_filter_state()

    # Count by severity
    counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "ADMIN": 0}
    for result in erce_results:
        cat = result.get("risk_category", "ADMIN").upper()
        if cat in counts:
            counts[cat] += 1

    st.markdown(f"### {title}")
    st.caption("Toggle visibility by risk level")

    # Render filter checkboxes
    for severity in ["CRITICAL", "HIGH", "MODERATE", "ADMIN"]:
        config = ERCE_SEVERITY_LEVELS[severity]
        count = counts[severity]
        is_checked = filter_state.get(severity, True)

        col1, col2 = st.columns([3, 1])

        with col1:
            new_state = st.checkbox(
                f"{config['icon']} {config['label']}",
                value=is_checked,
                key=f"erce_filter_{severity}",
                help=config["description"],
            )

            # Update state if changed
            if new_state != is_checked:
                set_erce_filter(severity, new_state)
                st.rerun()

        with col2:
            st.markdown(f"<span style='color: {config['color']}; font-weight: 600;'>{count}</span>", unsafe_allow_html=True)

    st.markdown("---")

    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("All On", key="erce_all_on", use_container_width=True):
            for severity in ERCE_SEVERITY_LEVELS:
                set_erce_filter(severity, True)
            st.rerun()

    with col2:
        if st.button("All Off", key="erce_all_off", use_container_width=True):
            for severity in ERCE_SEVERITY_LEVELS:
                set_erce_filter(severity, False)
            st.rerun()


# ============================================================================
# RISK CARD COMPONENTS
# ============================================================================

def _get_probability_class(probability: Optional[float]) -> str:
    """Get CSS class for success probability."""
    if probability is None:
        return ""
    if probability >= 0.7:
        return "erce-probability-good"
    elif probability >= 0.4:
        return "erce-probability-medium"
    return "erce-probability-low"


def render_erce_risk_card(
    clause_pair_id: int,
    risk_category: str,
    pattern_ref: Optional[str] = None,
    success_probability: Optional[float] = None,
    confidence: float = 0.0,
    show_if_filtered: bool = True
) -> None:
    """
    Render a single ERCE risk card with color coding.

    Args:
        clause_pair_id: ID of the clause pair
        risk_category: Risk category (CRITICAL, HIGH, MODERATE, ADMIN)
        pattern_ref: Optional pattern reference
        success_probability: Optional negotiation success probability
        confidence: ERCE confidence score
        show_if_filtered: Whether to respect filter state
    """
    category = risk_category.upper()
    config = ERCE_SEVERITY_LEVELS.get(category, ERCE_SEVERITY_LEVELS["ADMIN"])

    # Check filter state
    if show_if_filtered and not is_severity_visible(category):
        return

    # Build pattern ref HTML
    pattern_html = ""
    if pattern_ref:
        pattern_html = f'<span class="erce-pattern-ref">📋 {pattern_ref}</span>'

    # Build probability HTML
    prob_html = ""
    if success_probability is not None:
        prob_class = _get_probability_class(success_probability)
        prob_pct = success_probability * 100
        prob_html = f'<span class="erce-probability {prob_class}">🎯 {prob_pct:.0f}% success</span>'

    # Build confidence bar
    conf_pct = confidence * 100
    conf_class = category.lower()

    card_html = f"""
    <div class="erce-risk-card {config['css_class']}">
        <div class="erce-card-header">
            <span class="erce-card-title">
                {config['icon']} Clause Pair {clause_pair_id}
            </span>
            <span class="erce-severity-badge">{config['label']}</span>
        </div>
        <div class="erce-card-body">
            <div class="erce-detail-row">
                <span class="erce-detail-key">Risk Category</span>
                <span class="erce-detail-value">{category}</span>
            </div>
            <div class="erce-detail-row">
                <span class="erce-detail-key">Pattern Match</span>
                <span class="erce-detail-value">{pattern_html if pattern_ref else 'None'}</span>
            </div>
            <div class="erce-detail-row">
                <span class="erce-detail-key">Negotiation Outlook</span>
                <span class="erce-detail-value">{prob_html if success_probability else 'N/A'}</span>
            </div>
            <div class="erce-detail-row">
                <span class="erce-detail-key">ERCE Confidence</span>
                <span class="erce-detail-value">{conf_pct:.0f}%</span>
            </div>
            <div class="erce-confidence-bar">
                <div class="erce-confidence-fill {conf_class}" style="width: {conf_pct}%"></div>
            </div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_erce_inline_highlight(
    text: str,
    risk_category: str
) -> None:
    """
    Render inline highlighted text with ERCE risk color.

    Args:
        text: Text to highlight
        risk_category: Risk category for color coding
    """
    category = risk_category.upper()
    config = ERCE_SEVERITY_LEVELS.get(category, ERCE_SEVERITY_LEVELS["ADMIN"])

    html = f"""
    <span class="erce-inline-highlight erce-inline-{category.lower()}">
        {config['icon']} {text}
    </span>
    """
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# SUMMARY AND LIST COMPONENTS
# ============================================================================

def render_erce_summary_stats(erce_results: List[Dict[str, Any]]) -> None:
    """
    Render summary statistics for ERCE results.

    Args:
        erce_results: List of ERCE result dictionaries
    """
    # Count by severity
    counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "ADMIN": 0}
    for result in erce_results:
        cat = result.get("risk_category", "ADMIN").upper()
        if cat in counts:
            counts[cat] += 1

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="erce-summary-stat erce-summary-critical">
            <div class="erce-summary-count">{counts['CRITICAL']}</div>
            <div class="erce-summary-label">Critical</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="erce-summary-stat erce-summary-high">
            <div class="erce-summary-count">{counts['HIGH']}</div>
            <div class="erce-summary-label">High</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="erce-summary-stat erce-summary-moderate">
            <div class="erce-summary-count">{counts['MODERATE']}</div>
            <div class="erce-summary-label">Moderate</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="erce-summary-stat erce-summary-admin">
            <div class="erce-summary-count">{counts['ADMIN']}</div>
            <div class="erce-summary-label">Admin</div>
        </div>
        """, unsafe_allow_html=True)


def render_erce_results_list(
    erce_results: List[Dict[str, Any]],
    max_display: int = 15,
    respect_filters: bool = True
) -> None:
    """
    Render a list of ERCE risk cards with filtering.

    Args:
        erce_results: List of ERCE result dictionaries
        max_display: Maximum items to display
        respect_filters: Whether to respect sidebar filter state
    """
    if not erce_results:
        st.info("No ERCE risk classifications to display")
        return

    # Filter results based on state
    if respect_filters:
        filter_state = get_erce_filter_state()
        visible_results = [
            r for r in erce_results
            if filter_state.get(r.get("risk_category", "ADMIN").upper(), True)
        ]
    else:
        visible_results = erce_results

    if not visible_results:
        st.info("No results match current filter settings")
        return

    # Render cards
    for result in visible_results[:max_display]:
        render_erce_risk_card(
            clause_pair_id=result.get("clause_pair_id", 0),
            risk_category=result.get("risk_category", "ADMIN"),
            pattern_ref=result.get("pattern_ref"),
            success_probability=result.get("success_probability"),
            confidence=result.get("confidence", 0.0),
            show_if_filtered=False,  # Already filtered above
        )

    # Truncation notice
    if len(visible_results) > max_display:
        st.caption(f"Showing {max_display} of {len(visible_results)} filtered results")


def render_erce_expander_with_filters(
    erce_results: List[Dict[str, Any]],
    title: str = "Risk Classification (ERCE)",
    expanded: bool = False,
    max_display: int = 15
) -> None:
    """
    Render ERCE results in an expander with inline filter summary.

    Args:
        erce_results: List of ERCE result dictionaries
        title: Expander title
        expanded: Whether to start expanded
        max_display: Maximum results to show
    """
    inject_erce_highlight_css()

    with st.expander(title, expanded=expanded):
        if not erce_results:
            st.info("No risk classifications found")
            return

        # Summary stats
        render_erce_summary_stats(erce_results)

        st.markdown("---")

        # Results list
        render_erce_results_list(erce_results, max_display=max_display)


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def extract_erce_data_from_v3_result(compare_v3_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract ERCE result data from Compare v3 API result.

    Args:
        compare_v3_result: Full Compare v3 API response

    Returns:
        List of ERCE result dictionaries
    """
    if not compare_v3_result:
        return []

    if not compare_v3_result.get("success"):
        return []

    data = compare_v3_result.get("data", {})
    return data.get("erce_results", [])


def get_visible_erce_count(erce_results: List[Dict[str, Any]]) -> int:
    """
    Get count of ERCE results visible with current filters.

    Args:
        erce_results: List of ERCE result dictionaries

    Returns:
        Count of visible results
    """
    filter_state = get_erce_filter_state()
    return sum(
        1 for r in erce_results
        if filter_state.get(r.get("risk_category", "ADMIN").upper(), True)
    )
