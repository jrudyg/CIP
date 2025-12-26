"""
BIRL Narrative Pane Demo Page
Phase 5 UX Upgrade - Task 3 Validation

This page demonstrates the BIRL Narrative Pane component for GEM UX validation.
Shows collapsible context pane with scrollable narrative content.
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
from components.birl_narrative import (
    inject_birl_narrative_css,
    render_birl_context_pane,
    render_birl_narrative_card,
    render_birl_inline_narrative,
    render_birl_expander,
    render_birl_dimension_badge,
    get_birl_summary_stats,
    BIRL_IMPACT_DIMENSIONS,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="BIRL Narrative Demo",
    page_icon="📖",
    layout="wide"
)

apply_spacing()
apply_theme()
inject_dark_theme()

# Sidebar
with st.sidebar:
    inject_cip_logo()

# ============================================================================
# DEMO DATA
# ============================================================================

DEMO_BIRL_NARRATIVES = [
    {
        "clause_pair_id": 1,
        "narrative": "The modification to the liability limitation clause significantly increases risk exposure. The original cap of $1M has been removed, creating potential for unlimited liability in breach scenarios. This change directly impacts margin protection and requires executive review before acceptance.",
        "impact_dimensions": ["RISK", "MARGIN"],
        "token_count": 52,
    },
    {
        "clause_pair_id": 2,
        "narrative": "The indemnification scope has been expanded to include third-party claims and consequential damages. This represents a substantial shift in risk allocation that may affect insurance requirements and overall contract profitability. Legal counsel review is recommended.",
        "impact_dimensions": ["RISK", "COMPLIANCE", "MARGIN"],
        "token_count": 48,
    },
    {
        "clause_pair_id": 3,
        "narrative": "Payment terms have been extended from Net-30 to Net-60, which will impact cash flow projections for the project duration. The additional 30-day delay in receivables should be factored into working capital requirements.",
        "impact_dimensions": ["CASH_FLOW", "SCHEDULE"],
        "token_count": 42,
    },
    {
        "clause_pair_id": 4,
        "narrative": "The quality assurance requirements have been enhanced with additional inspection checkpoints. While this adds operational overhead, it aligns with industry best practices and reduces the risk of rework or quality-related disputes.",
        "impact_dimensions": ["QUALITY", "SCHEDULE"],
        "token_count": 38,
    },
    {
        "clause_pair_id": 5,
        "narrative": "A new regulatory compliance clause has been added referencing GDPR and CCPA requirements. This creates ongoing compliance obligations and may require additional data handling procedures. The impact is primarily administrative but essential for legal compliance.",
        "impact_dimensions": ["COMPLIANCE", "ADMIN"],
        "token_count": 44,
    },
    {
        "clause_pair_id": 6,
        "narrative": "The notice period for termination has been reduced from 90 days to 30 days. This change reduces scheduling predictability but provides more flexibility for both parties. Consider the impact on resource planning and transition activities.",
        "impact_dimensions": ["SCHEDULE", "ADMIN"],
        "token_count": 40,
    },
    {
        "clause_pair_id": 7,
        "narrative": "Standard administrative updates to contact information and notice addresses. These changes are procedural in nature with no material business impact. Routine update for contract maintenance.",
        "impact_dimensions": ["ADMIN"],
        "token_count": 28,
    },
]

# ============================================================================
# PAGE CONTENT
# ============================================================================

# Inject CSS
inject_birl_narrative_css()

page_header("BIRL Narrative Pane Demo", "📖")

st.markdown("""
**Phase 5 UX Upgrade - Task 3: BIRL Narrative Integration**

This demo page showcases the BIRL Narrative Pane component that provides:
- Collapsible context pane for business impact narratives
- Clean, readable formatting with scrollable content
- Impact dimension badges with color coding
- Token count tracking
- Default collapsed state to preserve screen real estate
""")

st.info("👇 **Click the toggle button below to expand/collapse the narrative pane**")

st.markdown("---")

# ============================================================================
# SECTION 1: MAIN CONTEXT PANE (COLLAPSIBLE)
# ============================================================================

section_header("Collapsible Context Pane", "📊")

st.markdown("**The main BIRL Context Pane with collapse/expand functionality:**")

render_birl_context_pane(
    birl_narratives=DEMO_BIRL_NARRATIVES,
    pane_id="demo_main",
    title="Business Rationale & Impact Narrative",
    subtitle="AI-generated business impact analysis for clause changes",
    default_collapsed=True,
    max_display=5,
)

st.markdown("---")

# ============================================================================
# SECTION 2: INDIVIDUAL NARRATIVE CARDS
# ============================================================================

section_header("Individual Narrative Cards", "🃏")

st.markdown("**Standalone narrative cards for direct embedding:**")

col1, col2 = st.columns(2)

with col1:
    render_birl_narrative_card(
        clause_pair_id=100,
        narrative="The warranty period has been extended from 12 months to 24 months, doubling our exposure window for defect claims. This change should be reflected in pricing models and reserve calculations.",
        impact_dimensions=["RISK", "MARGIN"],
        token_count=35,
    )

with col2:
    render_birl_narrative_card(
        clause_pair_id=101,
        narrative="Force majeure provisions now explicitly include pandemic events and supply chain disruptions. This provides clearer risk allocation during extraordinary circumstances.",
        impact_dimensions=["RISK", "COMPLIANCE"],
        token_count=30,
    )

st.markdown("---")

# ============================================================================
# SECTION 3: IMPACT DIMENSION BADGES
# ============================================================================

section_header("Impact Dimension Badges", "🏷️")

st.markdown("**All available impact dimension badges:**")

cols = st.columns(4)
dimensions = list(BIRL_IMPACT_DIMENSIONS.keys())

for idx, dim in enumerate(dimensions):
    with cols[idx % 4]:
        config = BIRL_IMPACT_DIMENSIONS[dim]
        st.markdown(f"""
        <div style="margin-bottom: 16px;">
            {render_birl_dimension_badge(dim)}
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">
                {config['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# SECTION 4: INLINE NARRATIVE
# ============================================================================

section_header("Inline Narrative Block", "📝")

st.markdown("**Non-collapsible inline narrative for embedded content:**")

render_birl_inline_narrative(
    narrative="The intellectual property assignment clause has been modified to include derivative works and improvements made during the contract term. This represents a significant expansion of IP transfer scope that requires careful evaluation against company IP policy.",
    impact_dimensions=["RISK", "COMPLIANCE", "MARGIN"],
    clause_pair_id=200,
)

st.markdown("---")

# ============================================================================
# SECTION 5: EXPANDER INTEGRATION
# ============================================================================

section_header("Expander Integration", "📂")

st.markdown("**BIRL narratives in a Streamlit expander:**")

render_birl_expander(
    birl_narratives=DEMO_BIRL_NARRATIVES[:4],
    title="Business Impact (BIRL) - Demo Data",
    expanded=True,
    max_display=3,
)

st.markdown("---")

# ============================================================================
# SECTION 6: SUMMARY STATISTICS
# ============================================================================

section_header("Summary Statistics", "📈")

st.markdown("**Aggregate statistics from BIRL narratives:**")

stats = get_birl_summary_stats(DEMO_BIRL_NARRATIVES)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Narratives", stats["total_narratives"])

with col2:
    st.metric("Total Tokens", stats["total_tokens"])

with col3:
    st.metric("Avg Tokens/Narrative", stats["avg_tokens"])

st.markdown("**Dimension Distribution:**")

dim_cols = st.columns(len(stats["dimensions_count"]))
for idx, (dim, count) in enumerate(sorted(stats["dimensions_count"].items(), key=lambda x: -x[1])):
    config = BIRL_IMPACT_DIMENSIONS.get(dim, BIRL_IMPACT_DIMENSIONS["ADMIN"])
    with dim_cols[idx % len(dim_cols)]:
        st.markdown(f"{config['icon']} **{config['label']}**: {count}")

st.markdown("---")

# ============================================================================
# SECTION 7: COMPACT MODE
# ============================================================================

section_header("Compact Mode", "📦")

st.markdown("**Context pane in compact display mode:**")

render_birl_context_pane(
    birl_narratives=DEMO_BIRL_NARRATIVES[:3],
    pane_id="demo_compact",
    title="Compact Narrative View",
    subtitle="Reduced padding for space-constrained layouts",
    default_collapsed=False,
    max_display=3,
    compact=True,
)

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Component Features
    - Collapsible context pane (default collapsed)
    - Clear title and state indicator
    - Scrollable narrative container (max 500px)
    - Impact dimension badges with colors
    - Token count tracking
    - Summary statistics bar
    - Compact display mode
    - Session state persistence
    """)

with col2:
    st.markdown("""
    ### Integration Points
    - Compare Versions page (below z4)
    - Compare v3 result display
    - BIRL expander section
    - Contract analysis views
    - Standalone narrative displays
    """)

st.caption(f"BIRL Narrative Demo | Phase 5 UX Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
