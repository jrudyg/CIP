"""
SAE Semantic Tooltip Demo Page
Phase 5 UX Upgrade - Task 1 Validation

This page demonstrates the SAE Semantic Tooltip component for GEM UX validation.
Shows hover-triggered tooltips displaying SAE structured data.
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
from components.sae_tooltip import (
    inject_sae_tooltip_css,
    render_sae_tooltip,
    render_sae_inline_preview,
    render_sae_matches_with_tooltips,
    render_sae_expander_with_tooltips,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="SAE Tooltip Demo",
    page_icon="🔬",
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

DEMO_SAE_MATCHES = [
    {
        "v1_clause_id": 1,
        "v2_clause_id": 1,
        "similarity_score": 0.97,
        "match_confidence": "HIGH",
        "threshold_used": 0.90,
    },
    {
        "v1_clause_id": 2,
        "v2_clause_id": 3,
        "similarity_score": 0.82,
        "match_confidence": "MEDIUM",
        "threshold_used": 0.75,
    },
    {
        "v1_clause_id": 4,
        "v2_clause_id": 5,
        "similarity_score": 0.68,
        "match_confidence": "LOW",
        "threshold_used": 0.60,
    },
    {
        "v1_clause_id": 6,
        "v2_clause_id": 7,
        "similarity_score": 0.94,
        "match_confidence": "HIGH",
        "threshold_used": 0.90,
    },
    {
        "v1_clause_id": 8,
        "v2_clause_id": 9,
        "similarity_score": 0.77,
        "match_confidence": "MEDIUM",
        "threshold_used": 0.75,
    },
    {
        "v1_clause_id": 10,
        "v2_clause_id": 12,
        "similarity_score": 0.63,
        "match_confidence": "LOW",
        "threshold_used": 0.60,
    },
]

# ============================================================================
# PAGE CONTENT
# ============================================================================

page_header("SAE Semantic Tooltip Demo", "🔬")

st.markdown("""
**Phase 5 UX Upgrade - Task 1: SAE Semantic Previews**

This demo page showcases the SAE Semantic Tooltip component that surfaces
SAE structured data on-demand via hover interactions.
""")

st.info("👆 **Hover over the tooltip triggers below to see the SAE data displayed**")

# Inject CSS
inject_sae_tooltip_css()

st.markdown("---")

# ============================================================================
# SECTION 1: INDIVIDUAL TOOLTIPS
# ============================================================================

section_header("Individual Tooltip Triggers", "🔗")

st.markdown("**Hover over each clause pair to see detailed SAE data:**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**HIGH Confidence:**")
    render_sae_tooltip(
        v1_clause_id=1,
        v2_clause_id=1,
        similarity_score=0.97,
        match_confidence="HIGH",
        threshold_used=0.90,
    )

with col2:
    st.markdown("**MEDIUM Confidence:**")
    render_sae_tooltip(
        v1_clause_id=2,
        v2_clause_id=3,
        similarity_score=0.82,
        match_confidence="MEDIUM",
        threshold_used=0.75,
    )

with col3:
    st.markdown("**LOW Confidence:**")
    render_sae_tooltip(
        v1_clause_id=4,
        v2_clause_id=5,
        similarity_score=0.68,
        match_confidence="LOW",
        threshold_used=0.60,
    )

st.markdown("---")

# ============================================================================
# SECTION 2: INLINE PREVIEWS
# ============================================================================

section_header("Inline Preview Mode", "📊")

st.markdown("**Compact inline previews for use in tables:**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("Standard:")
    render_sae_inline_preview(0.95, "HIGH")

with col2:
    st.markdown("Compact:")
    render_sae_inline_preview(0.78, "MEDIUM", compact=True)

with col3:
    st.markdown("Standard:")
    render_sae_inline_preview(0.62, "LOW")

with col4:
    st.markdown("Compact:")
    render_sae_inline_preview(0.91, "HIGH", compact=True)

st.markdown("---")

# ============================================================================
# SECTION 3: GRID LAYOUT
# ============================================================================

section_header("Grid Layout with Multiple Tooltips", "🔲")

st.markdown("**Hover over any match in the grid:**")

render_sae_matches_with_tooltips(DEMO_SAE_MATCHES, max_display=6, columns=3)

st.markdown("---")

# ============================================================================
# SECTION 4: EXPANDER INTEGRATION
# ============================================================================

section_header("Expander Integration", "📂")

st.markdown("**SAE matches inside an expander with summary stats:**")

render_sae_expander_with_tooltips(
    sae_matches=DEMO_SAE_MATCHES,
    title="Semantic Alignment (SAE) - Demo Data",
    expanded=True,
    max_display=6,
)

st.markdown("---")

# ============================================================================
# SECTION 5: CUSTOM LABELS
# ============================================================================

section_header("Custom Label Examples", "🏷️")

st.markdown("**Tooltips with custom display labels:**")

col1, col2 = st.columns(2)

with col1:
    render_sae_tooltip(
        v1_clause_id=15,
        v2_clause_id=16,
        similarity_score=0.89,
        match_confidence="MEDIUM",
        threshold_used=0.75,
        display_label="Indemnification",
    )

with col2:
    render_sae_tooltip(
        v1_clause_id=20,
        v2_clause_id=21,
        similarity_score=0.95,
        match_confidence="HIGH",
        threshold_used=0.90,
        display_label="Limitation of Liability",
    )

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Component Features
    - Hover-triggered tooltip display
    - Key-value structured SAE data
    - Confidence-based color coding
    - Visual similarity score bars
    - Threshold markers
    - Grid and expander layouts
    """)

with col2:
    st.markdown("""
    ### Integration Points
    - Compare Versions page
    - Compare v3 result display
    - SAE expander section
    - Any clause matching UI
    """)

st.caption(f"SAE Tooltip Demo | Phase 5 UX Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
