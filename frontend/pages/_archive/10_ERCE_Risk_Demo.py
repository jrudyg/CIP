"""
ERCE Risk Highlight Demo Page
Phase 5 UX Upgrade - Task 2 Validation

This page demonstrates the ERCE Risk Highlight component for GEM UX validation.
Shows color-coded risk cards and sidebar filtering controls.
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui_components import page_header, section_header, apply_spacing
from theme_system import apply_theme, inject_cip_logo
from components.theme import inject_dark_theme
from components.erce_highlights import (
    inject_erce_highlight_css,
    init_erce_filter_state,
    render_erce_filter_sidebar,
    render_erce_risk_card,
    render_erce_inline_highlight,
    render_erce_summary_stats,
    render_erce_results_list,
    render_erce_expander_with_filters,
    ERCE_SEVERITY_LEVELS,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="ERCE Risk Demo",
    page_icon="🚨",
    layout="wide"
)

apply_spacing()
apply_theme()
inject_dark_theme()

# Initialize filter state
init_erce_filter_state()

# ============================================================================
# DEMO DATA
# ============================================================================

DEMO_ERCE_RESULTS = [
    {
        "clause_pair_id": 1,
        "risk_category": "CRITICAL",
        "pattern_ref": "UNLIMITED_LIABILITY",
        "success_probability": 0.35,
        "confidence": 0.92,
    },
    {
        "clause_pair_id": 2,
        "risk_category": "HIGH",
        "pattern_ref": "INDEMNIFICATION_UNLIMITED",
        "success_probability": 0.55,
        "confidence": 0.85,
    },
    {
        "clause_pair_id": 3,
        "risk_category": "HIGH",
        "pattern_ref": "IP_ASSIGNMENT_BROAD",
        "success_probability": 0.62,
        "confidence": 0.78,
    },
    {
        "clause_pair_id": 4,
        "risk_category": "MODERATE",
        "pattern_ref": "TERMINATION_FOR_CONVENIENCE",
        "success_probability": 0.72,
        "confidence": 0.88,
    },
    {
        "clause_pair_id": 5,
        "risk_category": "MODERATE",
        "pattern_ref": None,
        "success_probability": 0.68,
        "confidence": 0.75,
    },
    {
        "clause_pair_id": 6,
        "risk_category": "ADMIN",
        "pattern_ref": None,
        "success_probability": None,
        "confidence": 0.95,
    },
    {
        "clause_pair_id": 7,
        "risk_category": "ADMIN",
        "pattern_ref": "NOTICE_PERIOD",
        "success_probability": None,
        "confidence": 0.91,
    },
    {
        "clause_pair_id": 8,
        "risk_category": "CRITICAL",
        "pattern_ref": "WARRANTY_DISCLAIMER",
        "success_probability": 0.28,
        "confidence": 0.89,
    },
    {
        "clause_pair_id": 9,
        "risk_category": "HIGH",
        "pattern_ref": "AUDIT_RIGHTS",
        "success_probability": 0.58,
        "confidence": 0.82,
    },
    {
        "clause_pair_id": 10,
        "risk_category": "MODERATE",
        "pattern_ref": "CONFIDENTIALITY_DURATION",
        "success_probability": 0.75,
        "confidence": 0.86,
    },
]

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    inject_cip_logo()

    st.markdown("---")

    # ERCE Filter Controls
    render_erce_filter_sidebar(
        erce_results=DEMO_ERCE_RESULTS,
        title="🎚️ Risk Filter"
    )

    st.markdown("---")

    st.caption("Use the filter controls above to toggle visibility of risk categories.")

# ============================================================================
# PAGE CONTENT
# ============================================================================

# Inject CSS
inject_erce_highlight_css()

page_header("ERCE Risk Highlight Demo", "🚨")

st.markdown("""
**Phase 5 UX Upgrade - Task 2: ERCE Risk Highlight Surfaces**

This demo page showcases the ERCE Risk Highlight component that provides:
- Color-coded risk cards by severity (CRITICAL, HIGH, MODERATE, ADMIN)
- Sidebar filter controls to toggle visibility by risk level
- Summary statistics with risk distribution
- Inline highlight badges for text integration
""")

st.info("👈 **Use the sidebar filter to toggle risk visibility**")

st.markdown("---")

# ============================================================================
# SECTION 1: SUMMARY STATS
# ============================================================================

section_header("Risk Distribution Summary", "📊")

render_erce_summary_stats(DEMO_ERCE_RESULTS)

st.markdown("---")

# ============================================================================
# SECTION 2: RISK CARDS WITH FILTERING
# ============================================================================

section_header("Filtered Risk Cards", "🃏")

st.markdown("**Risk cards filtered by sidebar selection:**")

render_erce_results_list(
    erce_results=DEMO_ERCE_RESULTS,
    max_display=10,
    respect_filters=True
)

st.markdown("---")

# ============================================================================
# SECTION 3: INDIVIDUAL CARD EXAMPLES
# ============================================================================

section_header("Risk Category Examples", "🎨")

st.markdown("**Each risk category with its distinct styling:**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### CRITICAL Risk")
    render_erce_risk_card(
        clause_pair_id=100,
        risk_category="CRITICAL",
        pattern_ref="UNLIMITED_LIABILITY",
        success_probability=0.25,
        confidence=0.95,
        show_if_filtered=False,
    )

    st.markdown("##### MODERATE Risk")
    render_erce_risk_card(
        clause_pair_id=102,
        risk_category="MODERATE",
        pattern_ref="TERM_LENGTH",
        success_probability=0.70,
        confidence=0.82,
        show_if_filtered=False,
    )

with col2:
    st.markdown("##### HIGH Risk")
    render_erce_risk_card(
        clause_pair_id=101,
        risk_category="HIGH",
        pattern_ref="INDEMNIFICATION_BROAD",
        success_probability=0.45,
        confidence=0.88,
        show_if_filtered=False,
    )

    st.markdown("##### ADMIN Risk")
    render_erce_risk_card(
        clause_pair_id=103,
        risk_category="ADMIN",
        pattern_ref=None,
        success_probability=None,
        confidence=0.92,
        show_if_filtered=False,
    )

st.markdown("---")

# ============================================================================
# SECTION 4: INLINE HIGHLIGHTS
# ============================================================================

section_header("Inline Risk Highlights", "✨")

st.markdown("**Use inline highlights to mark risk terms in text:**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_erce_inline_highlight("Unlimited Liability", "CRITICAL")

with col2:
    render_erce_inline_highlight("Indemnification", "HIGH")

with col3:
    render_erce_inline_highlight("Term Extension", "MODERATE")

with col4:
    render_erce_inline_highlight("Notice Period", "ADMIN")

st.markdown("")
st.markdown("**Example paragraph with embedded highlights:**")

st.markdown("""
The contract contains several provisions requiring attention. The
<span class="erce-inline-highlight erce-inline-critical">🔴 unlimited liability clause</span>
presents significant exposure, while the
<span class="erce-inline-highlight erce-inline-high">🟠 indemnification terms</span>
require negotiation. The
<span class="erce-inline-highlight erce-inline-moderate">🟡 confidentiality duration</span>
is within acceptable bounds, and the
<span class="erce-inline-highlight erce-inline-admin">🟢 notice requirements</span>
are standard.
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# SECTION 5: EXPANDER INTEGRATION
# ============================================================================

section_header("Expander Integration", "📂")

st.markdown("**ERCE results in an expander with summary and filtering:**")

render_erce_expander_with_filters(
    erce_results=DEMO_ERCE_RESULTS,
    title="Risk Classification (ERCE) - Demo Data",
    expanded=True,
    max_display=8
)

st.markdown("---")

# ============================================================================
# SECTION 6: SEVERITY LEVEL REFERENCE
# ============================================================================

section_header("Severity Level Reference", "📋")

st.markdown("**Complete severity level configuration:**")

for severity, config in ERCE_SEVERITY_LEVELS.items():
    st.markdown(f"""
    **{config['icon']} {config['label']}** (`{severity}`)
    - Color: `{config['color']}`
    - CSS Class: `{config['css_class']}`
    - {config['description']}
    """)

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Component Features
    - Color-coded risk cards (4 severity levels)
    - Sidebar filter controls with counts
    - Session state management for filters
    - Summary statistics grid
    - Inline highlight badges
    - Expander integration
    - Confidence bars with gradients
    - Success probability indicators
    """)

with col2:
    st.markdown("""
    ### Integration Points
    - Compare Versions page (z6_export_actions)
    - Compare v3 result display
    - ERCE expander section
    - Any clause risk display UI
    - Sidebar filter zones
    """)

st.caption(f"ERCE Risk Demo | Phase 5 UX Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
