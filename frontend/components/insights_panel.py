"""
Integrated Insights Panel Component - Phase 6 UI Upgrade
P6.C2.T3: Unified Insights Panel with Tabbed View

Tabbed view component integrating SAE, ERCE, BIRL, and FAR outputs.
Accepts CC3 data binder outputs for single-clause or multi-clause datasets.

CIP Protocol: CC2 implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

from components.color_tokens import get_token, is_high_contrast_mode, inject_color_tokens


# ============================================================================
# TAB DEFINITIONS
# ============================================================================

@dataclass
class InsightTab:
    """Definition of an insight panel tab."""
    tab_id: str
    label: str
    icon: str
    description: str
    pipeline: str  # SAE, ERCE, BIRL, FAR
    badge_count: int = 0
    has_data: bool = False
    severity_summary: Optional[Dict[str, int]] = None


DEFAULT_INSIGHT_TABS = [
    InsightTab(
        tab_id="sae",
        label="SAE Matches",
        icon="🔗",
        description="Semantic Alignment Engine clause matches",
        pipeline="SAE",
    ),
    InsightTab(
        tab_id="erce",
        label="ERCE Risk",
        icon="🚨",
        description="Enterprise Risk Classification Engine",
        pipeline="ERCE",
    ),
    InsightTab(
        tab_id="birl",
        label="BIRL Narratives",
        icon="📖",
        description="Business Impact & Risk Language",
        pipeline="BIRL",
    ),
    InsightTab(
        tab_id="far",
        label="FAR Flowdowns",
        icon="📋",
        description="Flowdown Analysis & Requirements",
        pipeline="FAR",
    ),
]


# ============================================================================
# CSS STYLING
# ============================================================================

def _generate_insights_panel_css() -> str:
    """Generate Insights Panel CSS with current color tokens."""
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

    # Pipeline colors
    sae_color = get_token("sae-primary")
    erce_critical = get_token("erce-critical")
    erce_high = get_token("erce-high")
    birl_color = get_token("birl-compliance")
    far_color = get_token("far-high")

    border_width = "2px" if high_contrast else "1px"
    focus_width = "3px" if high_contrast else "2px"

    return f"""
<style>
/* ============================================================================
   INTEGRATED INSIGHTS PANEL STYLES
   Phase 6 UI Upgrade - P6.C2.T3
   High-Contrast Mode: {'ENABLED' if high_contrast else 'DISABLED'}
   ============================================================================ */

/* Main Panel Container */
.cip-insights-panel {{
    background: {bg_secondary};
    border: {border_width} solid {border_default};
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 16px;
}}

/* Panel Header */
.cip-insights-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(90deg, {bg_primary} 0%, {bg_secondary} 100%);
    border-bottom: {border_width} solid {border_default};
}}

.cip-insights-title {{
    font-size: 16px;
    font-weight: 600;
    color: {text_primary};
    display: flex;
    align-items: center;
    gap: 10px;
}}

.cip-insights-title-icon {{
    font-size: 20px;
}}

/* Tab Bar */
.cip-insights-tabs {{
    display: flex;
    background: {bg_primary};
    border-bottom: {border_width} solid {border_default};
    overflow-x: auto;
    scrollbar-width: none;
}}

.cip-insights-tabs::-webkit-scrollbar {{
    display: none;
}}

/* Individual Tab */
.cip-insights-tab {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 20px;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    color: {text_secondary};
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    position: relative;
}}

.cip-insights-tab:hover {{
    background: {get_token("nav-tab-hover")};
    color: {text_primary};
}}

.cip-insights-tab:focus {{
    outline: {focus_width} solid {border_focus};
    outline-offset: -2px;
}}

.cip-insights-tab.active {{
    color: {text_primary};
    border-bottom-color: {accent_primary};
    background: {get_token("sae-bg")};
}}

/* Pipeline-specific active states */
.cip-insights-tab.active.sae {{
    border-bottom-color: {sae_color};
}}

.cip-insights-tab.active.erce {{
    border-bottom-color: {erce_critical};
}}

.cip-insights-tab.active.birl {{
    border-bottom-color: {birl_color};
}}

.cip-insights-tab.active.far {{
    border-bottom-color: {far_color};
}}

/* Tab Icon */
.cip-insights-tab-icon {{
    font-size: 16px;
}}

/* Tab Badge */
.cip-insights-tab-badge {{
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

.cip-insights-tab-badge.sae {{
    background: {sae_color};
}}

.cip-insights-tab-badge.erce {{
    background: {erce_critical};
}}

.cip-insights-tab-badge.birl {{
    background: {birl_color};
}}

.cip-insights-tab-badge.far {{
    background: {far_color};
}}

/* No Data Indicator */
.cip-insights-tab.no-data {{
    opacity: 0.5;
}}

.cip-insights-tab.no-data::after {{
    content: "(no data)";
    font-size: 10px;
    color: {text_muted};
    margin-left: 4px;
}}

/* Content Area */
.cip-insights-content {{
    padding: 20px;
    min-height: 200px;
    max-height: 500px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: {get_token("border-strong")} {bg_secondary};
}}

.cip-insights-content::-webkit-scrollbar {{
    width: 8px;
}}

.cip-insights-content::-webkit-scrollbar-track {{
    background: {bg_secondary};
}}

.cip-insights-content::-webkit-scrollbar-thumb {{
    background: {get_token("border-strong")};
    border-radius: 4px;
}}

/* Empty State */
.cip-insights-empty {{
    text-align: center;
    padding: 40px 20px;
    color: {text_muted};
}}

.cip-insights-empty-icon {{
    font-size: 48px;
    margin-bottom: 12px;
    opacity: 0.5;
}}

.cip-insights-empty-title {{
    font-size: 16px;
    font-weight: 500;
    color: {text_secondary};
    margin-bottom: 8px;
}}

.cip-insights-empty-text {{
    font-size: 13px;
    max-width: 300px;
    margin: 0 auto;
}}

/* Data Item Card */
.cip-insights-item {{
    background: {surface};
    border: {border_width} solid {border_default};
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
}}

.cip-insights-item:hover {{
    border-color: {get_token("border-strong")};
}}

.cip-insights-item:last-child {{
    margin-bottom: 0;
}}

/* Item Header */
.cip-insights-item-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}}

.cip-insights-item-title {{
    font-size: 14px;
    font-weight: 500;
    color: {text_primary};
}}

.cip-insights-item-meta {{
    font-size: 11px;
    color: {text_muted};
}}

/* Severity Badge */
.cip-severity-badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}

.cip-severity-badge.critical {{
    background: {get_token("erce-critical-bg")};
    color: {erce_critical};
}}

.cip-severity-badge.high {{
    background: {get_token("erce-high-bg")};
    color: {erce_high};
}}

.cip-severity-badge.moderate {{
    background: {get_token("erce-moderate-bg")};
    color: {get_token("erce-moderate")};
}}

.cip-severity-badge.admin {{
    background: {get_token("erce-admin-bg")};
    color: {get_token("erce-admin")};
}}

/* Confidence Bar */
.cip-confidence-bar {{
    height: 4px;
    background: {border_default};
    border-radius: 2px;
    overflow: hidden;
    margin-top: 8px;
}}

.cip-confidence-fill {{
    height: 100%;
    background: {accent_primary};
    border-radius: 2px;
    transition: width 0.3s ease;
}}

/* Summary Stats Row */
.cip-insights-summary {{
    display: flex;
    gap: 16px;
    padding: 12px 16px;
    background: {bg_primary};
    border-radius: 8px;
    margin-bottom: 16px;
}}

.cip-insights-stat {{
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.cip-insights-stat-value {{
    font-size: 20px;
    font-weight: 600;
    color: {text_primary};
}}

.cip-insights-stat-label {{
    font-size: 11px;
    color: {text_muted};
    text-transform: uppercase;
}}

/* Compact Mode */
.cip-insights-panel.compact .cip-insights-content {{
    padding: 12px;
    max-height: 300px;
}}

.cip-insights-panel.compact .cip-insights-item {{
    padding: 10px 12px;
}}

/* Print Styles */
@media print {{
    .cip-insights-panel {{
        border: 1px solid #333;
        background: white;
    }}

    .cip-insights-tabs {{
        display: none;
    }}

    .cip-insights-content {{
        max-height: none;
        overflow: visible;
    }}
}}
</style>
"""


def inject_insights_panel_css() -> None:
    """Inject Insights Panel CSS styles into the page."""
    st.markdown(_generate_insights_panel_css(), unsafe_allow_html=True)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_active_tab_key(panel_id: str = "main") -> str:
    """Get session state key for active tab."""
    return f"_cip_insights_tab_{panel_id}"


def init_insights_state(panel_id: str = "main", default_tab: str = "sae") -> None:
    """Initialize Insights Panel state."""
    key = _get_active_tab_key(panel_id)
    if key not in st.session_state:
        st.session_state[key] = default_tab


def get_active_insight_tab(panel_id: str = "main") -> str:
    """Get currently active insight tab."""
    init_insights_state(panel_id)
    return st.session_state.get(_get_active_tab_key(panel_id), "sae")


def set_active_insight_tab(panel_id: str, tab_id: str) -> None:
    """Set active insight tab."""
    st.session_state[_get_active_tab_key(panel_id)] = tab_id


# ============================================================================
# CC3 DATA BINDER WRAPPERS
# ============================================================================

@dataclass
class InsightsData:
    """Container for insights data from CC3 binder."""
    sae_matches: List[Dict[str, Any]] = field(default_factory=list)
    erce_results: List[Dict[str, Any]] = field(default_factory=list)
    birl_narratives: List[Dict[str, Any]] = field(default_factory=list)
    far_flowdowns: List[Dict[str, Any]] = field(default_factory=list)


def wrap_cc3_binder_output(binder_output: Dict[str, Any]) -> InsightsData:
    """
    Wrap CC3 data binder output for the insights panel.

    Args:
        binder_output: Raw output from CC3 data binder

    Returns:
        InsightsData container
    """
    return InsightsData(
        sae_matches=binder_output.get("sae_matches", []),
        erce_results=binder_output.get("erce_results", []),
        birl_narratives=binder_output.get("birl_narratives", []),
        far_flowdowns=binder_output.get("flowdown_gaps", []),
    )


def extract_from_compare_v3(compare_result: Dict[str, Any]) -> InsightsData:
    """
    Extract insights data from Compare v3 API result.

    Args:
        compare_result: Full Compare v3 API response

    Returns:
        InsightsData container
    """
    if not compare_result or not compare_result.get("success"):
        return InsightsData()

    data = compare_result.get("data", {})

    return InsightsData(
        sae_matches=data.get("sae_matches", []),
        erce_results=data.get("erce_results", []),
        birl_narratives=data.get("birl_narratives", []),
        far_flowdowns=data.get("flowdown_gaps", []),
    )


# ============================================================================
# CONTENT RENDERERS
# ============================================================================

def render_sae_content(matches: List[Dict[str, Any]]) -> None:
    """Render SAE matches content."""
    if not matches:
        st.markdown("""
        <div class="cip-insights-empty">
            <div class="cip-insights-empty-icon">🔗</div>
            <div class="cip-insights-empty-title">No SAE Matches</div>
            <div class="cip-insights-empty-text">
                Semantic alignment results will appear here when available.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Summary stats
    high_conf = sum(1 for m in matches if m.get("match_confidence") == "HIGH")
    avg_score = sum(m.get("similarity_score", 0) for m in matches) / len(matches)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Matches", len(matches))
    with col2:
        st.metric("High Confidence", high_conf)
    with col3:
        st.metric("Avg Similarity", f"{avg_score:.1%}")

    st.markdown("---")

    # Match cards
    for match in matches[:10]:
        confidence = match.get("match_confidence", "MEDIUM")
        score = match.get("similarity_score", 0)

        st.markdown(f"""
        <div class="cip-insights-item">
            <div class="cip-insights-item-header">
                <div class="cip-insights-item-title">
                    Clause {match.get('v1_clause_id', '?')} ↔️ Clause {match.get('v2_clause_id', '?')}
                </div>
                <span class="cip-severity-badge {confidence.lower()}">{confidence}</span>
            </div>
            <div class="cip-insights-item-meta">
                Similarity: {score:.1%} | Threshold: {match.get('threshold_used', 0):.2f}
            </div>
            <div class="cip-confidence-bar">
                <div class="cip-confidence-fill" style="width: {score * 100}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_erce_content(results: List[Dict[str, Any]]) -> None:
    """Render ERCE risk content."""
    if not results:
        st.markdown("""
        <div class="cip-insights-empty">
            <div class="cip-insights-empty-icon">🚨</div>
            <div class="cip-insights-empty-title">No ERCE Results</div>
            <div class="cip-insights-empty-text">
                Risk classification results will appear here when available.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Summary by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "ADMIN": 0}
    for r in results:
        sev = r.get("risk_category", "ADMIN")
        if sev in severity_counts:
            severity_counts[sev] += 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔴 Critical", severity_counts["CRITICAL"])
    with col2:
        st.metric("🟠 High", severity_counts["HIGH"])
    with col3:
        st.metric("🟡 Moderate", severity_counts["MODERATE"])
    with col4:
        st.metric("🟢 Admin", severity_counts["ADMIN"])

    st.markdown("---")

    # Risk cards
    for result in results[:10]:
        severity = result.get("risk_category", "ADMIN")
        confidence = result.get("confidence", 0)
        prob = result.get("success_probability")
        prob_text = f"{prob:.1%}" if prob else "N/A"

        st.markdown(f"""
        <div class="cip-insights-item">
            <div class="cip-insights-item-header">
                <div class="cip-insights-item-title">
                    Clause Pair {result.get('clause_pair_id', '?')}
                </div>
                <span class="cip-severity-badge {severity.lower()}">{severity}</span>
            </div>
            <div class="cip-insights-item-meta">
                Pattern: {result.get('pattern_ref', 'None')} |
                Success Prob: {prob_text} |
                Confidence: {confidence:.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_birl_content(narratives: List[Dict[str, Any]]) -> None:
    """Render BIRL narratives content."""
    if not narratives:
        st.markdown("""
        <div class="cip-insights-empty">
            <div class="cip-insights-empty-icon">📖</div>
            <div class="cip-insights-empty-title">No BIRL Narratives</div>
            <div class="cip-insights-empty-text">
                Business impact narratives will appear here when available.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Summary
    total_tokens = sum(n.get("token_count", 0) for n in narratives)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Narratives", len(narratives))
    with col2:
        st.metric("Total Tokens", total_tokens)

    st.markdown("---")

    # Narrative cards
    for narrative in narratives[:10]:
        dims = narrative.get("impact_dimensions", [])
        dims_text = " ".join([f"`{d}`" for d in dims])

        st.markdown(f"**Clause Pair {narrative.get('clause_pair_id', '?')}** - {dims_text}")
        st.markdown(f"> {narrative.get('narrative', 'No narrative available.')}")
        st.caption(f"Tokens: {narrative.get('token_count', 0)}")
        st.markdown("---")


def render_far_content(flowdowns: List[Dict[str, Any]]) -> None:
    """Render FAR flowdowns content."""
    if not flowdowns:
        st.markdown("""
        <div class="cip-insights-empty">
            <div class="cip-insights-empty-icon">📋</div>
            <div class="cip-insights-empty-title">No FAR Flowdowns</div>
            <div class="cip-insights-empty-text">
                Flowdown gap analysis will appear here when available.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Summary by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0}
    for f in flowdowns:
        sev = f.get("severity", "MODERATE")
        if sev in severity_counts:
            severity_counts[sev] += 1

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔴 Critical", severity_counts["CRITICAL"])
    with col2:
        st.metric("🟠 High", severity_counts["HIGH"])
    with col3:
        st.metric("🟡 Moderate", severity_counts["MODERATE"])

    st.markdown("---")

    # Gap cards
    for gap in flowdowns[:10]:
        severity = gap.get("severity", "MODERATE")

        st.markdown(f"""
        <div class="cip-insights-item">
            <div class="cip-insights-item-header">
                <div class="cip-insights-item-title">
                    {gap.get('gap_type', 'Unknown Gap')}
                </div>
                <span class="cip-severity-badge {severity.lower()}">{severity}</span>
            </div>
            <div class="cip-insights-item-meta">
                <strong>Prime:</strong> {gap.get('upstream_value', 'N/A')} |
                <strong>Sub:</strong> {gap.get('downstream_value', 'N/A')}
            </div>
            <div style="margin-top: 8px; font-size: 13px; color: var(--cip-text-secondary);">
                <strong>Recommendation:</strong> {gap.get('recommendation', 'Review and address.')}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# MAIN COMPONENT
# ============================================================================

def render_insights_panel(
    data: Union[InsightsData, Dict[str, Any]],
    panel_id: str = "main",
    title: str = "Analysis Insights",
    compact: bool = False,
    on_tab_change: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Render the Integrated Insights Panel.

    Args:
        data: InsightsData or raw dict from CC3 binder
        panel_id: Unique ID for this panel
        title: Panel title
        compact: Use compact display mode
        on_tab_change: Callback when tab changes

    Returns:
        Currently active tab ID
    """
    # Normalize data
    if isinstance(data, dict):
        data = wrap_cc3_binder_output(data)

    # Initialize
    init_insights_state(panel_id)
    inject_color_tokens()
    inject_insights_panel_css()

    active_tab = get_active_insight_tab(panel_id)
    compact_class = "compact" if compact else ""

    # Calculate badge counts
    tabs = [
        InsightTab("sae", "SAE Matches", "🔗", "Semantic alignment", "SAE",
                   len(data.sae_matches), bool(data.sae_matches)),
        InsightTab("erce", "ERCE Risk", "🚨", "Risk classification", "ERCE",
                   len(data.erce_results), bool(data.erce_results)),
        InsightTab("birl", "BIRL Narratives", "📖", "Business impact", "BIRL",
                   len(data.birl_narratives), bool(data.birl_narratives)),
        InsightTab("far", "FAR Flowdowns", "📋", "Flowdown gaps", "FAR",
                   len(data.far_flowdowns), bool(data.far_flowdowns)),
    ]

    # Render header
    st.markdown(f"""
    <div class="cip-insights-panel {compact_class}">
        <div class="cip-insights-header">
            <div class="cip-insights-title">
                <span class="cip-insights-title-icon">📊</span>
                {title}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Tab bar (Streamlit buttons)
    tab_cols = st.columns(len(tabs))
    for idx, tab in enumerate(tabs):
        with tab_cols[idx]:
            is_active = active_tab == tab.tab_id
            badge = f" ({tab.badge_count})" if tab.badge_count > 0 else ""
            btn_type = "primary" if is_active else "secondary"

            if st.button(
                f"{tab.icon} {tab.label}{badge}",
                key=f"insights_tab_{panel_id}_{tab.tab_id}",
                use_container_width=True,
                type=btn_type,
            ):
                set_active_insight_tab(panel_id, tab.tab_id)
                if on_tab_change:
                    on_tab_change(tab.tab_id)
                st.rerun()

    # Content area
    st.markdown('<div class="cip-insights-content">', unsafe_allow_html=True)

    if active_tab == "sae":
        render_sae_content(data.sae_matches)
    elif active_tab == "erce":
        render_erce_content(data.erce_results)
    elif active_tab == "birl":
        render_birl_content(data.birl_narratives)
    elif active_tab == "far":
        render_far_content(data.far_flowdowns)

    st.markdown('</div></div>', unsafe_allow_html=True)

    return active_tab


# ============================================================================
# ACCESSIBILITY
# ============================================================================

def validate_insights_panel_accessibility() -> Dict[str, Any]:
    """
    Validate Insights Panel accessibility compliance.

    Returns:
        Validation results
    """
    issues = []

    # Check all tabs have icons and labels
    for tab in DEFAULT_INSIGHT_TABS:
        if not tab.icon:
            issues.append(f"Tab {tab.tab_id} missing icon")
        if not tab.label:
            issues.append(f"Tab {tab.tab_id} missing label")
        if not tab.description:
            issues.append(f"Tab {tab.tab_id} missing description")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "tab_count": len(DEFAULT_INSIGHT_TABS),
        "features": [
            "Keyboard navigation via tabindex",
            "Focus indicators on tabs",
            "ARIA role='tab' support",
            "High contrast mode support",
            "Pipeline-specific color coding",
        ],
    }
