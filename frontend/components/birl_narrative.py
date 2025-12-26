"""
BIRL Narrative Pane Component - Phase 5 UX Upgrade Task 3

Provides a dedicated, collapsible context pane for displaying BIRL-generated
narrative text. Segregates interpretive content from raw data to maintain
clarity and flow in the UI.

CIP Protocol: CC implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
import hashlib


# ============================================================================
# BIRL IMPACT DIMENSIONS
# ============================================================================

BIRL_IMPACT_DIMENSIONS = {
    "MARGIN": {
        "icon": "💰",
        "label": "Margin Impact",
        "color": "#059669",
        "description": "Affects profit margins and pricing",
    },
    "RISK": {
        "icon": "⚠️",
        "label": "Risk Exposure",
        "color": "#DC2626",
        "description": "Changes risk profile or liability",
    },
    "COMPLIANCE": {
        "icon": "📋",
        "label": "Compliance",
        "color": "#7C3AED",
        "description": "Regulatory or compliance implications",
    },
    "SCHEDULE": {
        "icon": "📅",
        "label": "Schedule",
        "color": "#2563EB",
        "description": "Timeline or delivery impact",
    },
    "QUALITY": {
        "icon": "✅",
        "label": "Quality",
        "color": "#0891B2",
        "description": "Quality standards or requirements",
    },
    "CASH_FLOW": {
        "icon": "💵",
        "label": "Cash Flow",
        "color": "#CA8A04",
        "description": "Payment terms or cash flow impact",
    },
    "ADMIN": {
        "icon": "📝",
        "label": "Administrative",
        "color": "#6B7280",
        "description": "Administrative or procedural change",
    },
}


# ============================================================================
# CSS STYLING
# ============================================================================

BIRL_NARRATIVE_CSS = """
<style>
/* ============================================================================
   BIRL NARRATIVE PANE COMPONENT STYLES
   Phase 5 UX Upgrade - Task 3
   ============================================================================ */

/* Main Context Pane Container */
.birl-context-pane {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    margin-top: 24px;
    overflow: hidden;
    transition: all 0.3s ease;
}

/* Pane Header (Always Visible) */
.birl-pane-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
    border-bottom: 1px solid #334155;
    cursor: pointer;
    transition: background 0.2s ease;
}

.birl-pane-header:hover {
    background: linear-gradient(90deg, #334155 0%, #1E293B 100%);
}

.birl-pane-title {
    display: flex;
    align-items: center;
    gap: 12px;
}

.birl-pane-icon {
    font-size: 24px;
}

.birl-pane-title-text {
    font-size: 16px;
    font-weight: 600;
    color: #F1F5F9;
}

.birl-pane-subtitle {
    font-size: 12px;
    color: #64748B;
    margin-top: 2px;
}

.birl-pane-state {
    display: flex;
    align-items: center;
    gap: 8px;
}

.birl-state-badge {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.birl-state-collapsed {
    background: rgba(100, 116, 139, 0.3);
    color: #94A3B8;
}

.birl-state-expanded {
    background: rgba(34, 197, 94, 0.2);
    color: #4ADE80;
}

.birl-toggle-icon {
    font-size: 18px;
    color: #94A3B8;
    transition: transform 0.3s ease;
}

.birl-toggle-icon.expanded {
    transform: rotate(180deg);
}

/* Pane Content (Collapsible) */
.birl-pane-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s ease, padding 0.3s ease;
}

.birl-pane-content.expanded {
    max-height: 2000px;
    padding: 0;
}

/* Scrollable Narrative Container */
.birl-narrative-scroll {
    max-height: 500px;
    overflow-y: auto;
    padding: 20px;
    scrollbar-width: thin;
    scrollbar-color: #475569 #1E293B;
}

.birl-narrative-scroll::-webkit-scrollbar {
    width: 8px;
}

.birl-narrative-scroll::-webkit-scrollbar-track {
    background: #1E293B;
    border-radius: 4px;
}

.birl-narrative-scroll::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 4px;
}

.birl-narrative-scroll::-webkit-scrollbar-thumb:hover {
    background: #64748B;
}

/* Individual Narrative Card */
.birl-narrative-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
    animation: birlCardFadeIn 0.4s ease-out;
}

.birl-narrative-card:hover {
    border-color: #475569;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    transform: translateY(-2px);
}

.birl-narrative-card:last-child {
    margin-bottom: 0;
}

@keyframes birlCardFadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Card Header */
.birl-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #334155;
}

.birl-card-title {
    font-size: 14px;
    font-weight: 600;
    color: #E2E8F0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.birl-card-clause-id {
    font-size: 12px;
    color: #64748B;
    font-weight: 400;
}

.birl-token-count {
    font-size: 11px;
    color: #64748B;
    padding: 2px 8px;
    background: rgba(100, 116, 139, 0.2);
    border-radius: 10px;
}

/* Narrative Text */
.birl-narrative-text {
    font-size: 14px;
    line-height: 1.8;
    color: #CBD5E1;
    margin-bottom: 16px;
    padding: 16px;
    background: rgba(15, 23, 42, 0.5);
    border-radius: 8px;
    border-left: 3px solid #3B82F6;
}

.birl-narrative-text p {
    margin: 0;
}

/* Impact Dimensions */
.birl-dimensions-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.birl-dimension-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
    background: rgba(59, 130, 246, 0.15);
    color: #93C5FD;
    border: 1px solid rgba(59, 130, 246, 0.3);
    transition: all 0.2s ease;
}

.birl-dimension-badge:hover {
    background: rgba(59, 130, 246, 0.25);
    transform: scale(1.05);
}

/* Dimension-specific colors */
.birl-dim-margin {
    background: rgba(5, 150, 105, 0.15);
    color: #6EE7B7;
    border-color: rgba(5, 150, 105, 0.3);
}

.birl-dim-risk {
    background: rgba(220, 38, 38, 0.15);
    color: #FCA5A5;
    border-color: rgba(220, 38, 38, 0.3);
}

.birl-dim-compliance {
    background: rgba(124, 58, 237, 0.15);
    color: #C4B5FD;
    border-color: rgba(124, 58, 237, 0.3);
}

.birl-dim-schedule {
    background: rgba(37, 99, 235, 0.15);
    color: #93C5FD;
    border-color: rgba(37, 99, 235, 0.3);
}

.birl-dim-quality {
    background: rgba(8, 145, 178, 0.15);
    color: #67E8F9;
    border-color: rgba(8, 145, 178, 0.3);
}

.birl-dim-cash_flow {
    background: rgba(202, 138, 4, 0.15);
    color: #FDE047;
    border-color: rgba(202, 138, 4, 0.3);
}

.birl-dim-admin {
    background: rgba(107, 114, 128, 0.15);
    color: #D1D5DB;
    border-color: rgba(107, 114, 128, 0.3);
}

/* Summary Bar */
.birl-summary-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: rgba(30, 41, 59, 0.8);
    border-top: 1px solid #334155;
}

.birl-summary-stat {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #94A3B8;
}

.birl-summary-value {
    font-weight: 600;
    color: #E2E8F0;
}

/* Empty State */
.birl-empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #64748B;
}

.birl-empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}

.birl-empty-title {
    font-size: 16px;
    font-weight: 500;
    color: #94A3B8;
    margin-bottom: 8px;
}

.birl-empty-text {
    font-size: 13px;
}

/* Compact Mode */
.birl-compact .birl-narrative-card {
    padding: 12px 16px;
}

.birl-compact .birl-narrative-text {
    font-size: 13px;
    padding: 12px;
    margin-bottom: 12px;
}

/* Print-friendly */
@media print {
    .birl-context-pane {
        border: 1px solid #ccc;
        background: white;
    }

    .birl-pane-content {
        max-height: none !important;
    }

    .birl-narrative-text {
        color: #333;
        border-left-color: #333;
    }
}
</style>
"""


def inject_birl_narrative_css() -> None:
    """Inject BIRL narrative CSS styles into the page."""
    st.markdown(BIRL_NARRATIVE_CSS, unsafe_allow_html=True)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_pane_state_key(pane_id: str = "main") -> str:
    """Get session state key for pane expansion state."""
    return f"_birl_pane_expanded_{pane_id}"


def init_birl_pane_state(pane_id: str = "main", default_expanded: bool = False) -> None:
    """Initialize BIRL pane expansion state."""
    key = _get_pane_state_key(pane_id)
    if key not in st.session_state:
        st.session_state[key] = default_expanded


def is_birl_pane_expanded(pane_id: str = "main") -> bool:
    """Check if BIRL pane is expanded."""
    init_birl_pane_state(pane_id)
    return st.session_state.get(_get_pane_state_key(pane_id), False)


def toggle_birl_pane(pane_id: str = "main") -> None:
    """Toggle BIRL pane expansion state."""
    init_birl_pane_state(pane_id)
    key = _get_pane_state_key(pane_id)
    st.session_state[key] = not st.session_state[key]


def set_birl_pane_state(pane_id: str, expanded: bool) -> None:
    """Set BIRL pane expansion state."""
    st.session_state[_get_pane_state_key(pane_id)] = expanded


# ============================================================================
# COMPONENT RENDERING
# ============================================================================

def _get_dimension_class(dimension: str) -> str:
    """Get CSS class for impact dimension."""
    dim_lower = dimension.lower().replace("-", "_").replace(" ", "_")
    if dim_lower in ["margin", "risk", "compliance", "schedule", "quality", "cash_flow", "admin"]:
        return f"birl-dim-{dim_lower}"
    return "birl-dim-admin"


def _get_dimension_config(dimension: str) -> Dict[str, str]:
    """Get configuration for an impact dimension."""
    dim_upper = dimension.upper().replace("-", "_").replace(" ", "_")
    return BIRL_IMPACT_DIMENSIONS.get(dim_upper, BIRL_IMPACT_DIMENSIONS["ADMIN"])


def render_birl_dimension_badge(dimension: str) -> str:
    """Render HTML for a single dimension badge."""
    config = _get_dimension_config(dimension)
    css_class = _get_dimension_class(dimension)

    return f"""
    <span class="birl-dimension-badge {css_class}">
        {config['icon']} {config['label']}
    </span>
    """


def render_birl_narrative_card(
    clause_pair_id: int,
    narrative: str,
    impact_dimensions: List[str],
    token_count: int = 0
) -> None:
    """
    Render a single BIRL narrative card.

    Args:
        clause_pair_id: ID of the clause pair
        narrative: The narrative text
        impact_dimensions: List of impact dimension strings
        token_count: Token count for the narrative
    """
    # Build dimensions HTML
    dimensions_html = ""
    for dim in impact_dimensions:
        dimensions_html += render_birl_dimension_badge(dim)

    # Token count display
    token_display = f"{token_count} tokens" if token_count > 0 else ""

    card_html = f"""
    <div class="birl-narrative-card">
        <div class="birl-card-header">
            <div class="birl-card-title">
                📖 Business Impact Analysis
                <span class="birl-card-clause-id">Clause Pair {clause_pair_id}</span>
            </div>
            <span class="birl-token-count">{token_display}</span>
        </div>
        <div class="birl-narrative-text">
            <p>{narrative}</p>
        </div>
        <div class="birl-dimensions-container">
            {dimensions_html}
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_birl_empty_state() -> None:
    """Render empty state when no narratives available."""
    html = """
    <div class="birl-empty-state">
        <div class="birl-empty-icon">📝</div>
        <div class="birl-empty-title">No Business Impact Narratives</div>
        <div class="birl-empty-text">
            BIRL narratives will appear here when available.
            Run a comparison with BIRL enabled to generate impact analysis.
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_birl_context_pane(
    birl_narratives: List[Dict[str, Any]],
    pane_id: str = "main",
    title: str = "Business Rationale & Impact Narrative",
    subtitle: str = "AI-generated business impact analysis for clause changes",
    default_collapsed: bool = True,
    max_display: int = 10,
    compact: bool = False
) -> None:
    """
    Render the main BIRL Context Pane with collapsible functionality.

    Args:
        birl_narratives: List of BIRL narrative dictionaries
        pane_id: Unique ID for this pane instance
        title: Pane title text
        subtitle: Pane subtitle text
        default_collapsed: Whether pane starts collapsed
        max_display: Maximum narratives to display
        compact: Use compact display mode
    """
    # Initialize state
    init_birl_pane_state(pane_id, default_expanded=not default_collapsed)
    is_expanded = is_birl_pane_expanded(pane_id)

    # Inject CSS
    inject_birl_narrative_css()

    # Calculate stats
    total_narratives = len(birl_narratives)
    total_tokens = sum(n.get("token_count", 0) for n in birl_narratives)

    # State badge
    state_class = "birl-state-expanded" if is_expanded else "birl-state-collapsed"
    state_text = "Expanded" if is_expanded else "Collapsed"
    toggle_class = "expanded" if is_expanded else ""
    content_class = "expanded" if is_expanded else ""
    compact_class = "birl-compact" if compact else ""

    # Render pane header with toggle button
    st.markdown(f"""
    <div class="birl-context-pane {compact_class}">
        <div class="birl-pane-header" id="birl-header-{pane_id}">
            <div class="birl-pane-title">
                <span class="birl-pane-icon">📊</span>
                <div>
                    <div class="birl-pane-title-text">{title}</div>
                    <div class="birl-pane-subtitle">{subtitle}</div>
                </div>
            </div>
            <div class="birl-pane-state">
                <span class="birl-state-badge {state_class}">{state_text}</span>
                <span class="birl-toggle-icon {toggle_class}">▼</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Toggle button (Streamlit interactive)
    if st.button(
        f"{'📖 Collapse' if is_expanded else '📖 Expand'} Narrative Pane",
        key=f"birl_toggle_{pane_id}",
        use_container_width=True,
        type="secondary"
    ):
        toggle_birl_pane(pane_id)
        st.rerun()

    # Render content if expanded
    if is_expanded:
        st.markdown(f"""
        <div class="birl-pane-content {content_class}">
            <div class="birl-narrative-scroll">
        """, unsafe_allow_html=True)

        if not birl_narratives:
            render_birl_empty_state()
        else:
            # Render narrative cards
            for narrative in birl_narratives[:max_display]:
                render_birl_narrative_card(
                    clause_pair_id=narrative.get("clause_pair_id", 0),
                    narrative=narrative.get("narrative", "No narrative available."),
                    impact_dimensions=narrative.get("impact_dimensions", ["ADMIN"]),
                    token_count=narrative.get("token_count", 0),
                )

            # Truncation notice
            if total_narratives > max_display:
                st.caption(f"Showing {max_display} of {total_narratives} narratives")

        st.markdown("""
            </div>
        """, unsafe_allow_html=True)

        # Summary bar
        st.markdown(f"""
            <div class="birl-summary-bar">
                <div class="birl-summary-stat">
                    📝 Narratives: <span class="birl-summary-value">{total_narratives}</span>
                </div>
                <div class="birl-summary-stat">
                    🔤 Total Tokens: <span class="birl-summary-value">{total_tokens}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Close pane container
    st.markdown("</div>", unsafe_allow_html=True)


def render_birl_inline_narrative(
    narrative: str,
    impact_dimensions: List[str],
    clause_pair_id: Optional[int] = None
) -> None:
    """
    Render an inline narrative block (non-collapsible).

    Args:
        narrative: The narrative text
        impact_dimensions: List of impact dimensions
        clause_pair_id: Optional clause pair ID
    """
    inject_birl_narrative_css()

    dimensions_html = ""
    for dim in impact_dimensions:
        dimensions_html += render_birl_dimension_badge(dim)

    title_suffix = f" - Clause Pair {clause_pair_id}" if clause_pair_id else ""

    html = f"""
    <div class="birl-narrative-card">
        <div class="birl-card-header">
            <div class="birl-card-title">
                📖 Business Impact{title_suffix}
            </div>
        </div>
        <div class="birl-narrative-text">
            <p>{narrative}</p>
        </div>
        <div class="birl-dimensions-container">
            {dimensions_html}
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_birl_expander(
    birl_narratives: List[Dict[str, Any]],
    title: str = "Business Impact (BIRL)",
    expanded: bool = False,
    max_display: int = 5
) -> None:
    """
    Render BIRL narratives in a Streamlit expander.

    Args:
        birl_narratives: List of BIRL narrative dictionaries
        title: Expander title
        expanded: Whether to start expanded
        max_display: Maximum narratives to show
    """
    inject_birl_narrative_css()

    with st.expander(title, expanded=expanded):
        if not birl_narratives:
            render_birl_empty_state()
            return

        # Summary stats
        total = len(birl_narratives)
        total_tokens = sum(n.get("token_count", 0) for n in birl_narratives)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Narratives", total)
        with col2:
            st.metric("Total Tokens", total_tokens)

        st.markdown("---")

        # Render narratives
        for narrative in birl_narratives[:max_display]:
            render_birl_narrative_card(
                clause_pair_id=narrative.get("clause_pair_id", 0),
                narrative=narrative.get("narrative", ""),
                impact_dimensions=narrative.get("impact_dimensions", []),
                token_count=narrative.get("token_count", 0),
            )

        if total > max_display:
            st.caption(f"Showing {max_display} of {total} narratives")


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def extract_birl_data_from_v3_result(compare_v3_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract BIRL narrative data from Compare v3 API result.

    Args:
        compare_v3_result: Full Compare v3 API response

    Returns:
        List of BIRL narrative dictionaries
    """
    if not compare_v3_result:
        return []

    if not compare_v3_result.get("success"):
        return []

    data = compare_v3_result.get("data", {})
    return data.get("birl_narratives", [])


def get_birl_summary_stats(birl_narratives: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for BIRL narratives.

    Args:
        birl_narratives: List of BIRL narrative dictionaries

    Returns:
        Dictionary with summary stats
    """
    if not birl_narratives:
        return {
            "total_narratives": 0,
            "total_tokens": 0,
            "avg_tokens": 0,
            "dimensions_count": {},
        }

    total_tokens = sum(n.get("token_count", 0) for n in birl_narratives)
    avg_tokens = total_tokens / len(birl_narratives) if birl_narratives else 0

    # Count dimensions
    dimensions_count = {}
    for narrative in birl_narratives:
        for dim in narrative.get("impact_dimensions", []):
            dim_upper = dim.upper()
            dimensions_count[dim_upper] = dimensions_count.get(dim_upper, 0) + 1

    return {
        "total_narratives": len(birl_narratives),
        "total_tokens": total_tokens,
        "avg_tokens": round(avg_tokens, 1),
        "dimensions_count": dimensions_count,
    }
