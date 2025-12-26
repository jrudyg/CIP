"""
FAR Action Bar Component - Phase 5 UX Upgrade Task 4

Implements a persistent Action Bar for FAR (Flowdown Analysis & Requirements)
gap handling. The bar uses fixed positioning (bottom viewport) with high-contrast,
non-dismissible styling for critical action visibility.

CIP Protocol: CC implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Callable
import hashlib


# ============================================================================
# FAR GAP SEVERITY LEVELS
# ============================================================================

FAR_SEVERITY_LEVELS = {
    "CRITICAL": {
        "icon": "🔴",
        "label": "Critical",
        "color": "#DC2626",
        "bg_color": "rgba(220, 38, 38, 0.15)",
        "border_color": "rgba(220, 38, 38, 0.5)",
        "description": "Requires immediate resolution",
        "css_class": "far-severity-critical",
    },
    "HIGH": {
        "icon": "🟠",
        "label": "High",
        "color": "#D97706",
        "bg_color": "rgba(217, 119, 6, 0.15)",
        "border_color": "rgba(217, 119, 6, 0.5)",
        "description": "Should be addressed before execution",
        "css_class": "far-severity-high",
    },
    "MODERATE": {
        "icon": "🟡",
        "label": "Moderate",
        "color": "#2563EB",
        "bg_color": "rgba(37, 99, 235, 0.15)",
        "border_color": "rgba(37, 99, 235, 0.5)",
        "description": "Monitor and review",
        "css_class": "far-severity-moderate",
    },
}


# ============================================================================
# ACTION TYPES
# ============================================================================

FAR_ACTION_TYPES = {
    "RESOLVE": {
        "icon": "✅",
        "label": "Resolve Gap",
        "description": "Mark gap as resolved",
        "color": "#10B981",
    },
    "ESCALATE": {
        "icon": "⬆️",
        "label": "Escalate",
        "description": "Escalate to management",
        "color": "#F59E0B",
    },
    "DEFER": {
        "icon": "⏳",
        "label": "Defer",
        "description": "Defer for later review",
        "color": "#6B7280",
    },
    "NEGOTIATE": {
        "icon": "🤝",
        "label": "Negotiate",
        "description": "Open negotiation workflow",
        "color": "#3B82F6",
    },
    "EXPORT": {
        "icon": "📤",
        "label": "Export Report",
        "description": "Export gap analysis report",
        "color": "#8B5CF6",
    },
}


# ============================================================================
# CSS STYLING
# ============================================================================

FAR_ACTION_BAR_CSS = """
<style>
/* ============================================================================
   FAR ACTION BAR COMPONENT STYLES
   Phase 5 UX Upgrade - Task 4
   ============================================================================ */

/* Fixed Bottom Action Bar */
.far-action-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border-top: 2px solid #3B82F6;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
    padding: 0;
    display: flex;
    flex-direction: column;
}

/* Non-dismissible indicator */
.far-action-bar::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #DC2626, #F59E0B, #10B981);
    animation: farBarPulse 3s ease-in-out infinite;
}

@keyframes farBarPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Bar Header */
.far-bar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: rgba(15, 23, 42, 0.9);
    border-bottom: 1px solid #334155;
}

.far-bar-title {
    display: flex;
    align-items: center;
    gap: 12px;
}

.far-bar-icon {
    font-size: 24px;
}

.far-bar-title-text {
    font-size: 16px;
    font-weight: 600;
    color: #F1F5F9;
}

.far-bar-subtitle {
    font-size: 12px;
    color: #64748B;
    margin-left: 8px;
}

/* Gap Summary Badges */
.far-summary-badges {
    display: flex;
    gap: 12px;
    align-items: center;
}

.far-summary-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 13px;
    font-weight: 600;
}

.far-summary-badge.critical {
    background: rgba(220, 38, 38, 0.2);
    color: #FCA5A5;
    border: 1px solid rgba(220, 38, 38, 0.4);
}

.far-summary-badge.high {
    background: rgba(217, 119, 6, 0.2);
    color: #FCD34D;
    border: 1px solid rgba(217, 119, 6, 0.4);
}

.far-summary-badge.moderate {
    background: rgba(37, 99, 235, 0.2);
    color: #93C5FD;
    border: 1px solid rgba(37, 99, 235, 0.4);
}

/* Action Buttons Container */
.far-actions-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
}

.far-actions-group {
    display: flex;
    gap: 12px;
}

/* Individual Action Button */
.far-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
    text-decoration: none;
}

.far-action-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.far-action-btn:active {
    transform: translateY(0);
}

/* Primary action button */
.far-action-btn.primary {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: white;
    border-color: #10B981;
}

.far-action-btn.primary:hover {
    background: linear-gradient(135deg, #34D399 0%, #10B981 100%);
}

/* Secondary action button */
.far-action-btn.secondary {
    background: rgba(59, 130, 246, 0.15);
    color: #93C5FD;
    border-color: rgba(59, 130, 246, 0.4);
}

.far-action-btn.secondary:hover {
    background: rgba(59, 130, 246, 0.25);
    border-color: rgba(59, 130, 246, 0.6);
}

/* Warning action button */
.far-action-btn.warning {
    background: rgba(245, 158, 11, 0.15);
    color: #FCD34D;
    border-color: rgba(245, 158, 11, 0.4);
}

.far-action-btn.warning:hover {
    background: rgba(245, 158, 11, 0.25);
    border-color: rgba(245, 158, 11, 0.6);
}

/* Neutral action button */
.far-action-btn.neutral {
    background: rgba(107, 114, 128, 0.15);
    color: #D1D5DB;
    border-color: rgba(107, 114, 128, 0.4);
}

.far-action-btn.neutral:hover {
    background: rgba(107, 114, 128, 0.25);
    border-color: rgba(107, 114, 128, 0.6);
}

/* Gap Details Panel (expandable within bar) */
.far-details-panel {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease, padding 0.3s ease;
    background: rgba(15, 23, 42, 0.95);
    border-top: 1px solid #334155;
}

.far-details-panel.expanded {
    max-height: 300px;
    padding: 16px 24px;
    overflow-y: auto;
}

/* Individual Gap Card in Details */
.far-gap-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 12px 16px;
    background: rgba(30, 41, 59, 0.8);
    border-radius: 8px;
    margin-bottom: 12px;
    border-left: 3px solid #3B82F6;
}

.far-gap-card.critical {
    border-left-color: #DC2626;
}

.far-gap-card.high {
    border-left-color: #D97706;
}

.far-gap-card.moderate {
    border-left-color: #2563EB;
}

.far-gap-card:last-child {
    margin-bottom: 0;
}

.far-gap-severity {
    font-size: 20px;
}

.far-gap-content {
    flex: 1;
}

.far-gap-type {
    font-size: 14px;
    font-weight: 600;
    color: #E2E8F0;
    margin-bottom: 4px;
}

.far-gap-values {
    font-size: 12px;
    color: #94A3B8;
    margin-bottom: 8px;
}

.far-gap-recommendation {
    font-size: 13px;
    color: #CBD5E1;
    padding: 8px 12px;
    background: rgba(59, 130, 246, 0.1);
    border-radius: 6px;
    border-left: 2px solid #3B82F6;
}

/* Collapse Toggle */
.far-details-toggle {
    display: flex;
    justify-content: center;
    padding: 8px;
    background: rgba(30, 41, 59, 0.5);
    cursor: pointer;
    transition: background 0.2s ease;
}

.far-details-toggle:hover {
    background: rgba(30, 41, 59, 0.8);
}

.far-toggle-text {
    font-size: 12px;
    color: #94A3B8;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Persistent Indicator (always visible) */
.far-persistent-badge {
    position: absolute;
    top: 8px;
    right: 24px;
    font-size: 10px;
    padding: 2px 8px;
    background: rgba(220, 38, 38, 0.2);
    color: #FCA5A5;
    border-radius: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}

/* Spacer to prevent content overlap */
.far-action-bar-spacer {
    height: 140px;
    width: 100%;
}

/* Inline Compact Version (non-fixed) */
.far-action-bar-inline {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    margin-top: 24px;
    overflow: hidden;
}

.far-action-bar-inline .far-bar-header {
    border-radius: 12px 12px 0 0;
}

/* High Contrast Mode */
.far-high-contrast .far-action-btn.primary {
    background: #10B981;
    border: 2px solid white;
}

.far-high-contrast .far-summary-badge {
    border-width: 2px;
}

.far-high-contrast .far-gap-card {
    border-left-width: 5px;
}

/* Print-friendly */
@media print {
    .far-action-bar {
        position: relative;
        box-shadow: none;
        border: 2px solid #333;
    }

    .far-action-btn {
        background: white !important;
        color: #333 !important;
        border: 1px solid #333 !important;
    }
}
</style>
"""


def inject_far_action_bar_css() -> None:
    """Inject FAR Action Bar CSS styles into the page."""
    st.markdown(FAR_ACTION_BAR_CSS, unsafe_allow_html=True)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_details_state_key(bar_id: str = "main") -> str:
    """Get session state key for details panel expansion."""
    return f"_far_details_expanded_{bar_id}"


def init_far_bar_state(bar_id: str = "main") -> None:
    """Initialize FAR action bar state."""
    key = _get_details_state_key(bar_id)
    if key not in st.session_state:
        st.session_state[key] = False


def is_far_details_expanded(bar_id: str = "main") -> bool:
    """Check if FAR details panel is expanded."""
    init_far_bar_state(bar_id)
    return st.session_state.get(_get_details_state_key(bar_id), False)


def toggle_far_details(bar_id: str = "main") -> None:
    """Toggle FAR details panel expansion."""
    init_far_bar_state(bar_id)
    key = _get_details_state_key(bar_id)
    st.session_state[key] = not st.session_state[key]


# ============================================================================
# COMPONENT RENDERING
# ============================================================================

def _get_severity_config(severity: str) -> Dict[str, str]:
    """Get configuration for a severity level."""
    return FAR_SEVERITY_LEVELS.get(severity.upper(), FAR_SEVERITY_LEVELS["MODERATE"])


def _count_gaps_by_severity(flowdown_gaps: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count gaps by severity level."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0}
    for gap in flowdown_gaps:
        severity = gap.get("severity", "MODERATE").upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def render_far_summary_badges(flowdown_gaps: List[Dict[str, Any]]) -> str:
    """Render HTML for summary badges showing gap counts."""
    counts = _count_gaps_by_severity(flowdown_gaps)

    html = '<div class="far-summary-badges">'

    if counts["CRITICAL"] > 0:
        html += f'''
        <div class="far-summary-badge critical">
            🔴 {counts["CRITICAL"]} Critical
        </div>
        '''

    if counts["HIGH"] > 0:
        html += f'''
        <div class="far-summary-badge high">
            🟠 {counts["HIGH"]} High
        </div>
        '''

    if counts["MODERATE"] > 0:
        html += f'''
        <div class="far-summary-badge moderate">
            🟡 {counts["MODERATE"]} Moderate
        </div>
        '''

    html += '</div>'
    return html


def render_far_gap_card(
    gap_type: str,
    severity: str,
    upstream_value: str,
    downstream_value: str,
    recommendation: str,
) -> str:
    """Render HTML for a single gap card."""
    config = _get_severity_config(severity)
    severity_class = severity.lower()

    return f'''
    <div class="far-gap-card {severity_class}">
        <div class="far-gap-severity">{config["icon"]}</div>
        <div class="far-gap-content">
            <div class="far-gap-type">{gap_type}</div>
            <div class="far-gap-values">
                <strong>Prime:</strong> {upstream_value} |
                <strong>Sub:</strong> {downstream_value}
            </div>
            <div class="far-gap-recommendation">
                <strong>Recommendation:</strong> {recommendation}
            </div>
        </div>
    </div>
    '''


def render_far_action_bar(
    flowdown_gaps: List[Dict[str, Any]],
    bar_id: str = "main",
    title: str = "Flowdown Gap Analysis",
    subtitle: str = "FAR-identified compliance gaps requiring action",
    show_details: bool = True,
    fixed_position: bool = True,
    high_contrast: bool = False,
    on_resolve: Optional[Callable] = None,
    on_escalate: Optional[Callable] = None,
    on_defer: Optional[Callable] = None,
    on_negotiate: Optional[Callable] = None,
    on_export: Optional[Callable] = None,
) -> None:
    """
    Render the FAR Action Bar component.

    Args:
        flowdown_gaps: List of FlowdownGap dictionaries
        bar_id: Unique ID for this bar instance
        title: Bar title text
        subtitle: Bar subtitle text
        show_details: Whether to show expandable details panel
        fixed_position: Use fixed bottom positioning (True) or inline (False)
        high_contrast: Enable high contrast mode
        on_resolve: Callback for resolve action
        on_escalate: Callback for escalate action
        on_defer: Callback for defer action
        on_negotiate: Callback for negotiate action
        on_export: Callback for export action
    """
    # Initialize state
    init_far_bar_state(bar_id)
    is_expanded = is_far_details_expanded(bar_id)

    # Inject CSS
    inject_far_action_bar_css()

    # Calculate stats
    total_gaps = len(flowdown_gaps)
    counts = _count_gaps_by_severity(flowdown_gaps)
    has_critical = counts["CRITICAL"] > 0

    # Container class
    container_class = "far-action-bar" if fixed_position else "far-action-bar-inline"
    contrast_class = "far-high-contrast" if high_contrast else ""
    details_class = "expanded" if is_expanded else ""

    # Build summary badges HTML
    badges_html = render_far_summary_badges(flowdown_gaps)

    # Persistent indicator
    persistent_html = '<span class="far-persistent-badge">Action Required</span>' if has_critical else ''

    # Start bar HTML
    st.markdown(f'''
    <div class="{container_class} {contrast_class}">
        {persistent_html}
        <div class="far-bar-header">
            <div class="far-bar-title">
                <span class="far-bar-icon">📋</span>
                <div>
                    <span class="far-bar-title-text">{title}</span>
                    <span class="far-bar-subtitle">{subtitle}</span>
                </div>
            </div>
            {badges_html}
        </div>
    ''', unsafe_allow_html=True)

    # Action buttons (Streamlit interactive)
    col1, col2, col3, col4, col5, col_spacer = st.columns([1, 1, 1, 1, 1, 2])

    with col1:
        if st.button("✅ Resolve", key=f"far_resolve_{bar_id}", use_container_width=True):
            if on_resolve:
                on_resolve()
            else:
                st.session_state[f"far_action_{bar_id}"] = "resolve"

    with col2:
        if st.button("⬆️ Escalate", key=f"far_escalate_{bar_id}", use_container_width=True):
            if on_escalate:
                on_escalate()
            else:
                st.session_state[f"far_action_{bar_id}"] = "escalate"

    with col3:
        if st.button("⏳ Defer", key=f"far_defer_{bar_id}", use_container_width=True):
            if on_defer:
                on_defer()
            else:
                st.session_state[f"far_action_{bar_id}"] = "defer"

    with col4:
        if st.button("🤝 Negotiate", key=f"far_negotiate_{bar_id}", use_container_width=True):
            if on_negotiate:
                on_negotiate()
            else:
                st.session_state[f"far_action_{bar_id}"] = "negotiate"

    with col5:
        if st.button("📤 Export", key=f"far_export_{bar_id}", use_container_width=True):
            if on_export:
                on_export()
            else:
                st.session_state[f"far_action_{bar_id}"] = "export"

    # Details toggle
    if show_details and flowdown_gaps:
        if st.button(
            f"{'▲ Hide' if is_expanded else '▼ Show'} Gap Details ({total_gaps})",
            key=f"far_toggle_{bar_id}",
            use_container_width=True,
            type="secondary"
        ):
            toggle_far_details(bar_id)
            st.rerun()

        # Render details panel if expanded
        if is_expanded:
            st.markdown(f'''
            <div class="far-details-panel {details_class}">
            ''', unsafe_allow_html=True)

            for gap in flowdown_gaps:
                card_html = render_far_gap_card(
                    gap_type=gap.get("gap_type", "Unknown Gap"),
                    severity=gap.get("severity", "MODERATE"),
                    upstream_value=gap.get("upstream_value", "N/A"),
                    downstream_value=gap.get("downstream_value", "N/A"),
                    recommendation=gap.get("recommendation", "Review and address"),
                )
                st.markdown(card_html, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # Close bar container
    st.markdown('</div>', unsafe_allow_html=True)

    # Add spacer for fixed position to prevent content overlap
    if fixed_position:
        st.markdown('<div class="far-action-bar-spacer"></div>', unsafe_allow_html=True)


def render_far_inline_summary(
    flowdown_gaps: List[Dict[str, Any]],
    title: str = "Flowdown Gaps Summary"
) -> None:
    """
    Render a compact inline summary of FAR gaps.

    Args:
        flowdown_gaps: List of FlowdownGap dictionaries
        title: Summary title
    """
    inject_far_action_bar_css()

    counts = _count_gaps_by_severity(flowdown_gaps)
    total = len(flowdown_gaps)

    st.markdown(f"**{title}** ({total} total)")

    cols = st.columns(3)

    with cols[0]:
        config = FAR_SEVERITY_LEVELS["CRITICAL"]
        st.markdown(f"{config['icon']} **Critical:** {counts['CRITICAL']}")

    with cols[1]:
        config = FAR_SEVERITY_LEVELS["HIGH"]
        st.markdown(f"{config['icon']} **High:** {counts['HIGH']}")

    with cols[2]:
        config = FAR_SEVERITY_LEVELS["MODERATE"]
        st.markdown(f"{config['icon']} **Moderate:** {counts['MODERATE']}")


def render_far_gap_list(
    flowdown_gaps: List[Dict[str, Any]],
    max_display: int = 10
) -> None:
    """
    Render a list of FAR gap cards.

    Args:
        flowdown_gaps: List of FlowdownGap dictionaries
        max_display: Maximum gaps to display
    """
    inject_far_action_bar_css()

    if not flowdown_gaps:
        st.info("No flowdown gaps identified.")
        return

    for gap in flowdown_gaps[:max_display]:
        card_html = render_far_gap_card(
            gap_type=gap.get("gap_type", "Unknown Gap"),
            severity=gap.get("severity", "MODERATE"),
            upstream_value=gap.get("upstream_value", "N/A"),
            downstream_value=gap.get("downstream_value", "N/A"),
            recommendation=gap.get("recommendation", "Review and address"),
        )
        st.markdown(card_html, unsafe_allow_html=True)

    if len(flowdown_gaps) > max_display:
        st.caption(f"Showing {max_display} of {len(flowdown_gaps)} gaps")


def render_far_expander(
    flowdown_gaps: List[Dict[str, Any]],
    title: str = "Flowdown Gaps (FAR)",
    expanded: bool = False,
    max_display: int = 5
) -> None:
    """
    Render FAR gaps in a Streamlit expander.

    Args:
        flowdown_gaps: List of FlowdownGap dictionaries
        title: Expander title
        expanded: Whether to start expanded
        max_display: Maximum gaps to show
    """
    inject_far_action_bar_css()

    counts = _count_gaps_by_severity(flowdown_gaps)
    summary = f"{len(flowdown_gaps)} gaps"
    if counts["CRITICAL"] > 0:
        summary += f" ({counts['CRITICAL']} critical)"

    with st.expander(f"{title} - {summary}", expanded=expanded):
        if not flowdown_gaps:
            st.info("No flowdown gaps identified in this comparison.")
            return

        # Summary stats
        render_far_inline_summary(flowdown_gaps, "Gap Distribution")

        st.markdown("---")

        # Gap cards
        render_far_gap_list(flowdown_gaps, max_display)


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def extract_far_data_from_v3_result(compare_v3_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract FAR flowdown gap data from Compare v3 API result.

    Args:
        compare_v3_result: Full Compare v3 API response

    Returns:
        List of FlowdownGap dictionaries
    """
    if not compare_v3_result:
        return []

    if not compare_v3_result.get("success"):
        return []

    data = compare_v3_result.get("data", {})
    return data.get("flowdown_gaps", [])


def get_far_summary_stats(flowdown_gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for FAR gaps.

    Args:
        flowdown_gaps: List of FlowdownGap dictionaries

    Returns:
        Dictionary with summary stats
    """
    if not flowdown_gaps:
        return {
            "total_gaps": 0,
            "critical_count": 0,
            "high_count": 0,
            "moderate_count": 0,
            "gap_types": {},
            "has_critical": False,
        }

    counts = _count_gaps_by_severity(flowdown_gaps)

    # Count by gap type
    gap_types = {}
    for gap in flowdown_gaps:
        gap_type = gap.get("gap_type", "Unknown")
        gap_types[gap_type] = gap_types.get(gap_type, 0) + 1

    return {
        "total_gaps": len(flowdown_gaps),
        "critical_count": counts["CRITICAL"],
        "high_count": counts["HIGH"],
        "moderate_count": counts["MODERATE"],
        "gap_types": gap_types,
        "has_critical": counts["CRITICAL"] > 0,
    }


def should_show_action_bar(flowdown_gaps: List[Dict[str, Any]]) -> bool:
    """
    Determine if the action bar should be displayed.

    Returns True if there are any gaps that require action.
    """
    if not flowdown_gaps:
        return False

    counts = _count_gaps_by_severity(flowdown_gaps)
    return counts["CRITICAL"] > 0 or counts["HIGH"] > 0
