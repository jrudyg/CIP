"""
SAE Semantic Tooltip Component - Phase 5 UX Upgrade Task 1

Provides inline hover tooltips displaying SAE structured data for clause matches.
Surfaces atomic SAE output (similarity scores, confidence levels, thresholds)
on-demand without cluttering the main UI.

CIP Protocol: CC implementation for GEM UX validation.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
import hashlib


# ============================================================================
# TOOLTIP STYLING
# ============================================================================

SAE_TOOLTIP_CSS = """
<style>
/* SAE Semantic Tooltip Base Styles */
.sae-tooltip-container {
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: pointer;
}

.sae-tooltip-trigger {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 4px;
    background: linear-gradient(135deg, #1E3A5F 0%, #2D4A6F 100%);
    border: 1px solid #3D5A7F;
    color: #E0E7FF;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
    text-decoration: none;
}

.sae-tooltip-trigger:hover {
    background: linear-gradient(135deg, #2D4A6F 0%, #3D5A8F 100%);
    border-color: #60A5FA;
    box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);
    transform: translateY(-1px);
}

.sae-tooltip-icon {
    font-size: 11px;
    opacity: 0.8;
}

/* Confidence Badge Colors */
.sae-conf-high {
    background: linear-gradient(135deg, #065F46 0%, #047857 100%);
    border-color: #10B981;
}

.sae-conf-high:hover {
    background: linear-gradient(135deg, #047857 0%, #059669 100%);
    border-color: #34D399;
}

.sae-conf-medium {
    background: linear-gradient(135deg, #92400E 0%, #B45309 100%);
    border-color: #F59E0B;
}

.sae-conf-medium:hover {
    background: linear-gradient(135deg, #B45309 0%, #D97706 100%);
    border-color: #FBBF24;
}

.sae-conf-low {
    background: linear-gradient(135deg, #7C2D12 0%, #9A3412 100%);
    border-color: #F97316;
}

.sae-conf-low:hover {
    background: linear-gradient(135deg, #9A3412 0%, #C2410C 100%);
    border-color: #FB923C;
}

/* Tooltip Popup */
.sae-tooltip-popup {
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    min-width: 280px;
    max-width: 360px;
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05);
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s ease;
    pointer-events: none;
}

.sae-tooltip-container:hover .sae-tooltip-popup {
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
}

.sae-tooltip-popup::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 8px solid transparent;
    border-top-color: #0F172A;
}

/* Tooltip Content */
.sae-tooltip-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #334155;
}

.sae-tooltip-title {
    font-size: 14px;
    font-weight: 600;
    color: #F1F5F9;
}

.sae-tooltip-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sae-badge-high {
    background: #065F46;
    color: #6EE7B7;
}

.sae-badge-medium {
    background: #92400E;
    color: #FCD34D;
}

.sae-badge-low {
    background: #7C2D12;
    color: #FDBA74;
}

/* Key-Value Rows */
.sae-tooltip-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.sae-tooltip-row:last-child {
    border-bottom: none;
}

.sae-tooltip-key {
    font-size: 12px;
    color: #94A3B8;
    font-weight: 500;
}

.sae-tooltip-value {
    font-size: 13px;
    color: #E2E8F0;
    font-weight: 600;
    font-family: 'Monaco', 'Consolas', monospace;
}

/* Score Bar Visualization */
.sae-score-bar-container {
    width: 100%;
    margin-top: 12px;
}

.sae-score-bar-label {
    font-size: 11px;
    color: #64748B;
    margin-bottom: 4px;
}

.sae-score-bar-track {
    width: 100%;
    height: 6px;
    background: #1E293B;
    border-radius: 3px;
    overflow: hidden;
}

.sae-score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
}

.sae-score-bar-high {
    background: linear-gradient(90deg, #10B981 0%, #34D399 100%);
}

.sae-score-bar-medium {
    background: linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%);
}

.sae-score-bar-low {
    background: linear-gradient(90deg, #F97316 0%, #FB923C 100%);
}

/* Threshold Marker */
.sae-threshold-marker {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 8px;
    font-size: 11px;
    color: #64748B;
}

.sae-threshold-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #60A5FA;
}

/* Inline SAE Preview (for tables) */
.sae-inline-preview {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: rgba(30, 58, 95, 0.6);
    border: 1px solid rgba(61, 90, 127, 0.6);
    border-radius: 6px;
    font-size: 12px;
    color: #CBD5E1;
}

.sae-inline-score {
    font-weight: 600;
    color: #F1F5F9;
}

/* Animation */
@keyframes saeTooltipFadeIn {
    from {
        opacity: 0;
        transform: translateX(-50%) translateY(4px);
    }
    to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
}

.sae-tooltip-container:hover .sae-tooltip-popup {
    animation: saeTooltipFadeIn 0.2s ease forwards;
}
</style>
"""


def inject_sae_tooltip_css() -> None:
    """Inject SAE tooltip CSS styles into the page."""
    st.markdown(SAE_TOOLTIP_CSS, unsafe_allow_html=True)


# ============================================================================
# TOOLTIP COMPONENTS
# ============================================================================

def _get_confidence_class(confidence: str) -> str:
    """Get CSS class for confidence level."""
    confidence_lower = confidence.lower() if confidence else "low"
    if confidence_lower == "high":
        return "high"
    elif confidence_lower == "medium":
        return "medium"
    return "low"


def _get_score_bar_class(score: float) -> str:
    """Get CSS class for score bar based on value."""
    if score >= 0.90:
        return "high"
    elif score >= 0.75:
        return "medium"
    return "low"


def _generate_tooltip_id(v1_id: int, v2_id: int) -> str:
    """Generate unique ID for tooltip."""
    return hashlib.md5(f"sae_{v1_id}_{v2_id}".encode()).hexdigest()[:8]


def render_sae_tooltip(
    v1_clause_id: int,
    v2_clause_id: int,
    similarity_score: float,
    match_confidence: str,
    threshold_used: float,
    display_label: Optional[str] = None,
    show_score_bar: bool = True
) -> None:
    """
    Render an inline SAE semantic tooltip with hover preview.

    Args:
        v1_clause_id: Clause ID from version 1
        v2_clause_id: Clause ID from version 2
        similarity_score: Similarity score (0.0 to 1.0)
        match_confidence: Confidence level (HIGH, MEDIUM, LOW)
        threshold_used: Threshold value used for matching
        display_label: Optional custom label (defaults to showing clause pair)
        show_score_bar: Whether to show the visual score bar
    """
    tooltip_id = _generate_tooltip_id(v1_clause_id, v2_clause_id)
    conf_class = _get_confidence_class(match_confidence)
    score_class = _get_score_bar_class(similarity_score)
    score_pct = similarity_score * 100

    # Default label shows clause pair
    if display_label is None:
        display_label = f"C{v1_clause_id} ↔ C{v2_clause_id}"

    # Build score bar HTML
    score_bar_html = ""
    if show_score_bar:
        score_bar_html = f"""
        <div class="sae-score-bar-container">
            <div class="sae-score-bar-label">Similarity Score</div>
            <div class="sae-score-bar-track">
                <div class="sae-score-bar-fill sae-score-bar-{score_class}"
                     style="width: {score_pct}%"></div>
            </div>
        </div>
        """

    tooltip_html = f"""
    <div class="sae-tooltip-container" id="sae-tip-{tooltip_id}">
        <span class="sae-tooltip-trigger sae-conf-{conf_class}">
            <span class="sae-tooltip-icon">🔗</span>
            {display_label}
        </span>
        <div class="sae-tooltip-popup">
            <div class="sae-tooltip-header">
                <span class="sae-tooltip-title">SAE Semantic Match</span>
                <span class="sae-tooltip-badge sae-badge-{conf_class}">{match_confidence}</span>
            </div>
            <div class="sae-tooltip-row">
                <span class="sae-tooltip-key">V1 Clause ID</span>
                <span class="sae-tooltip-value">{v1_clause_id}</span>
            </div>
            <div class="sae-tooltip-row">
                <span class="sae-tooltip-key">V2 Clause ID</span>
                <span class="sae-tooltip-value">{v2_clause_id}</span>
            </div>
            <div class="sae-tooltip-row">
                <span class="sae-tooltip-key">Similarity Score</span>
                <span class="sae-tooltip-value">{score_pct:.1f}%</span>
            </div>
            <div class="sae-tooltip-row">
                <span class="sae-tooltip-key">Threshold Used</span>
                <span class="sae-tooltip-value">{threshold_used:.2f}</span>
            </div>
            <div class="sae-tooltip-row">
                <span class="sae-tooltip-key">Match Confidence</span>
                <span class="sae-tooltip-value">{match_confidence}</span>
            </div>
            {score_bar_html}
            <div class="sae-threshold-marker">
                <span class="sae-threshold-dot"></span>
                Threshold: {threshold_used:.0%} minimum for {conf_class.title()} match
            </div>
        </div>
    </div>
    """

    st.markdown(tooltip_html, unsafe_allow_html=True)


def render_sae_inline_preview(
    similarity_score: float,
    match_confidence: str,
    compact: bool = False
) -> None:
    """
    Render a compact inline SAE preview (for use in tables/lists).

    Args:
        similarity_score: Similarity score (0.0 to 1.0)
        match_confidence: Confidence level (HIGH, MEDIUM, LOW)
        compact: If True, shows only score without label
    """
    conf_class = _get_confidence_class(match_confidence)
    score_pct = similarity_score * 100

    if compact:
        html = f"""
        <span class="sae-inline-preview">
            <span class="sae-inline-score">{score_pct:.0f}%</span>
        </span>
        """
    else:
        html = f"""
        <span class="sae-inline-preview">
            <span class="sae-tooltip-badge sae-badge-{conf_class}">{match_confidence}</span>
            <span class="sae-inline-score">{score_pct:.1f}%</span>
        </span>
        """

    st.markdown(html, unsafe_allow_html=True)


def render_sae_matches_with_tooltips(
    sae_matches: List[Dict[str, Any]],
    max_display: int = 10,
    columns: int = 2
) -> None:
    """
    Render a grid of SAE matches with interactive tooltips.

    Args:
        sae_matches: List of SAE match dictionaries from Compare v3
        max_display: Maximum number of matches to display
        columns: Number of columns in the grid
    """
    if not sae_matches:
        st.info("No SAE matches to display")
        return

    # Inject CSS once
    inject_sae_tooltip_css()

    # Render matches in grid
    displayed = sae_matches[:max_display]
    cols = st.columns(columns)

    for idx, match in enumerate(displayed):
        with cols[idx % columns]:
            render_sae_tooltip(
                v1_clause_id=match.get("v1_clause_id", 0),
                v2_clause_id=match.get("v2_clause_id", 0),
                similarity_score=match.get("similarity_score", 0.0),
                match_confidence=match.get("match_confidence", "LOW"),
                threshold_used=match.get("threshold_used", 0.6),
            )

    # Show truncation notice
    if len(sae_matches) > max_display:
        st.caption(f"Showing {max_display} of {len(sae_matches)} matches")


def render_sae_expander_with_tooltips(
    sae_matches: List[Dict[str, Any]],
    title: str = "Semantic Alignment (SAE)",
    expanded: bool = False,
    max_display: int = 15
) -> None:
    """
    Render SAE matches inside an expander with tooltips.

    Args:
        sae_matches: List of SAE match dictionaries
        title: Expander title
        expanded: Whether expander starts expanded
        max_display: Maximum matches to show
    """
    # Inject CSS before expander
    inject_sae_tooltip_css()

    with st.expander(title, expanded=expanded):
        if not sae_matches:
            st.info("No semantic matches found")
            return

        # Summary stats
        high_count = sum(1 for m in sae_matches if m.get("match_confidence") == "HIGH")
        medium_count = sum(1 for m in sae_matches if m.get("match_confidence") == "MEDIUM")
        low_count = sum(1 for m in sae_matches if m.get("match_confidence") == "LOW")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", len(sae_matches))
        with col2:
            st.metric("High Conf.", high_count)
        with col3:
            st.metric("Medium Conf.", medium_count)
        with col4:
            st.metric("Low Conf.", low_count)

        st.markdown("---")
        st.markdown("**Hover over matches for detailed SAE data:**")

        # Render tooltips
        render_sae_matches_with_tooltips(sae_matches, max_display=max_display)


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def extract_sae_data_from_v3_result(compare_v3_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract SAE match data from Compare v3 API result.

    Args:
        compare_v3_result: Full Compare v3 API response

    Returns:
        List of SAE match dictionaries
    """
    if not compare_v3_result:
        return []

    if not compare_v3_result.get("success"):
        return []

    data = compare_v3_result.get("data", {})
    return data.get("sae_matches", [])


def get_sae_tooltip_for_clause_pair(
    sae_matches: List[Dict[str, Any]],
    v1_clause_id: int,
    v2_clause_id: int
) -> Optional[Dict[str, Any]]:
    """
    Find SAE match data for a specific clause pair.

    Args:
        sae_matches: List of SAE matches
        v1_clause_id: V1 clause ID to find
        v2_clause_id: V2 clause ID to find

    Returns:
        SAE match dict if found, None otherwise
    """
    for match in sae_matches:
        if (match.get("v1_clause_id") == v1_clause_id and
            match.get("v2_clause_id") == v2_clause_id):
            return match
    return None
