"""
Insights Panel Demo Page
Phase 6 UI Upgrade - P6.C2.T3 Validation

This page demonstrates the Integrated Insights Panel with tabbed view.
Shows SAE, ERCE, BIRL, and FAR tabs with CC3 integration wrappers.
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
from components.color_tokens import inject_color_tokens, is_high_contrast_mode
from components.insights_panel import (
    InsightsData,
    InsightTab,
    DEFAULT_INSIGHT_TABS,
    render_insights_panel,
    get_active_insight_tab,
    wrap_cc3_binder_output,
    extract_from_compare_v3,
    validate_insights_panel_accessibility,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Insights Panel Demo",
    page_icon="📊",
    layout="wide"
)

apply_spacing()
apply_theme()
inject_dark_theme()
inject_color_tokens()

# Sidebar
with st.sidebar:
    inject_cip_logo()

    st.markdown("---")
    st.markdown("### Panel State")

    active_tab = get_active_insight_tab("demo")
    st.info(f"Active Tab: **{active_tab.upper()}**")

    st.markdown("---")
    st.markdown("### Data Mode")

    data_mode = st.radio(
        "Select data source:",
        ["Full Demo Data", "Single Clause", "Empty Data"],
        key="data_mode"
    )

# ============================================================================
# DEMO DATA
# ============================================================================

DEMO_SAE_MATCHES = [
    {"v1_clause_id": 1, "v2_clause_id": 1, "similarity_score": 0.92, "threshold_used": 0.7, "match_confidence": "HIGH"},
    {"v1_clause_id": 2, "v2_clause_id": 2, "similarity_score": 0.78, "threshold_used": 0.7, "match_confidence": "MEDIUM"},
    {"v1_clause_id": 3, "v2_clause_id": 3, "similarity_score": 0.95, "threshold_used": 0.7, "match_confidence": "HIGH"},
    {"v1_clause_id": 4, "v2_clause_id": 4, "similarity_score": 0.68, "threshold_used": 0.7, "match_confidence": "LOW"},
    {"v1_clause_id": 5, "v2_clause_id": 5, "similarity_score": 0.88, "threshold_used": 0.7, "match_confidence": "HIGH"},
]

DEMO_ERCE_RESULTS = [
    {"clause_pair_id": 1, "risk_category": "CRITICAL", "pattern_ref": "UNLIMITED_LIABILITY", "success_probability": 0.35, "confidence": 0.92},
    {"clause_pair_id": 2, "risk_category": "HIGH", "pattern_ref": "INDEMNIFICATION_BROAD", "success_probability": 0.55, "confidence": 0.85},
    {"clause_pair_id": 3, "risk_category": "MODERATE", "pattern_ref": None, "success_probability": 0.72, "confidence": 0.78},
    {"clause_pair_id": 4, "risk_category": "HIGH", "pattern_ref": "IP_ASSIGNMENT", "success_probability": 0.48, "confidence": 0.88},
    {"clause_pair_id": 5, "risk_category": "ADMIN", "pattern_ref": None, "success_probability": None, "confidence": 0.95},
]

DEMO_BIRL_NARRATIVES = [
    {
        "clause_pair_id": 1,
        "narrative": "The modification to the liability limitation clause significantly increases risk exposure. The original cap of $1M has been removed, creating potential for unlimited liability in breach scenarios.",
        "impact_dimensions": ["RISK", "MARGIN"],
        "token_count": 45,
    },
    {
        "clause_pair_id": 2,
        "narrative": "The indemnification scope has been expanded to include third-party claims. This represents a substantial shift in risk allocation that may affect insurance requirements.",
        "impact_dimensions": ["RISK", "COMPLIANCE"],
        "token_count": 38,
    },
    {
        "clause_pair_id": 4,
        "narrative": "IP assignment terms now include derivative works. This change expands the scope of intellectual property transfer and requires careful evaluation against company policy.",
        "impact_dimensions": ["RISK", "MARGIN", "COMPLIANCE"],
        "token_count": 42,
    },
]

DEMO_FAR_FLOWDOWNS = [
    {
        "gap_type": "Liability Cap Mismatch",
        "severity": "CRITICAL",
        "upstream_value": "$5,000,000 aggregate cap",
        "downstream_value": "Unlimited liability",
        "recommendation": "Negotiate liability cap in subcontract to match prime contract limits.",
    },
    {
        "gap_type": "Insurance Requirements",
        "severity": "HIGH",
        "upstream_value": "$2M General Liability",
        "downstream_value": "$500K General Liability",
        "recommendation": "Require subcontractor to increase coverage to meet prime contract minimums.",
    },
    {
        "gap_type": "Audit Rights",
        "severity": "MODERATE",
        "upstream_value": "Government audit rights included",
        "downstream_value": "No audit provisions",
        "recommendation": "Add flowdown clause for government audit rights.",
    },
]

SINGLE_CLAUSE_DATA = InsightsData(
    sae_matches=[DEMO_SAE_MATCHES[0]],
    erce_results=[DEMO_ERCE_RESULTS[0]],
    birl_narratives=[DEMO_BIRL_NARRATIVES[0]],
    far_flowdowns=[DEMO_FAR_FLOWDOWNS[0]],
)

FULL_DEMO_DATA = InsightsData(
    sae_matches=DEMO_SAE_MATCHES,
    erce_results=DEMO_ERCE_RESULTS,
    birl_narratives=DEMO_BIRL_NARRATIVES,
    far_flowdowns=DEMO_FAR_FLOWDOWNS,
)

EMPTY_DATA = InsightsData()

# ============================================================================
# PAGE CONTENT
# ============================================================================

page_header("Insights Panel Demo", "📊")

st.markdown("""
**Phase 6 UI Upgrade - P6.C2.T3: Integrated Insights Panel**

This demo showcases the unified Insights Panel featuring:
- Tabbed view for SAE, ERCE, BIRL, and FAR outputs
- Integration wrappers for CC3 data binder
- Single-clause and multi-clause dataset support
- Pipeline-specific color coding
- WCAG AA accessibility compliance
""")

st.markdown("---")

# ============================================================================
# SECTION 1: MAIN INSIGHTS PANEL
# ============================================================================

section_header("Integrated Insights Panel", "📊")

st.markdown("**Unified view of all analysis outputs:**")

# Select data based on mode
if data_mode == "Full Demo Data":
    demo_data = FULL_DEMO_DATA
elif data_mode == "Single Clause":
    demo_data = SINGLE_CLAUSE_DATA
else:
    demo_data = EMPTY_DATA

active_tab = render_insights_panel(
    data=demo_data,
    panel_id="demo",
    title="Contract Analysis Results",
    compact=False,
)

st.success(f"Currently viewing: **{active_tab.upper()}** tab")

st.markdown("---")

# ============================================================================
# SECTION 2: CC3 BINDER INTEGRATION
# ============================================================================

section_header("CC3 Data Binder Integration", "🔌")

st.markdown("**Wrapper functions for CC3 integration:**")

# Simulate CC3 binder output
mock_binder_output = {
    "sae_matches": DEMO_SAE_MATCHES[:2],
    "erce_results": DEMO_ERCE_RESULTS[:2],
    "birl_narratives": DEMO_BIRL_NARRATIVES[:1],
    "flowdown_gaps": DEMO_FAR_FLOWDOWNS[:1],
}

st.code("""
# CC3 Integration Example
from components.insights_panel import (
    wrap_cc3_binder_output,
    render_insights_panel,
)

# Wrap CC3 binder output
binder_output = cc3_data_binder.get_analysis_results()
insights_data = wrap_cc3_binder_output(binder_output)

# Render panel
render_insights_panel(
    data=insights_data,
    panel_id="main",
    title="Analysis Results"
)
""", language="python")

st.markdown("**Demo with wrapped binder output:**")

wrapped_data = wrap_cc3_binder_output(mock_binder_output)
render_insights_panel(
    data=wrapped_data,
    panel_id="binder_demo",
    title="CC3 Binder Output",
    compact=True,
)

st.markdown("---")

# ============================================================================
# SECTION 3: COMPARE V3 INTEGRATION
# ============================================================================

section_header("Compare v3 API Integration", "⚙️")

st.markdown("**Extract insights from Compare v3 response:**")

mock_compare_v3 = {
    "success": True,
    "data": {
        "sae_matches": DEMO_SAE_MATCHES,
        "erce_results": DEMO_ERCE_RESULTS,
        "birl_narratives": DEMO_BIRL_NARRATIVES,
        "flowdown_gaps": DEMO_FAR_FLOWDOWNS,
    }
}

st.code("""
# Compare v3 Integration
from components.insights_panel import (
    extract_from_compare_v3,
    render_insights_panel,
)

# Extract from API response
compare_result = api.compare_v3(doc1, doc2)
insights_data = extract_from_compare_v3(compare_result)

# Render panel
render_insights_panel(data=insights_data)
""", language="python")

extracted_data = extract_from_compare_v3(mock_compare_v3)
st.json({
    "sae_count": len(extracted_data.sae_matches),
    "erce_count": len(extracted_data.erce_results),
    "birl_count": len(extracted_data.birl_narratives),
    "far_count": len(extracted_data.far_flowdowns),
})

st.markdown("---")

# ============================================================================
# SECTION 4: TAB DEFINITIONS
# ============================================================================

section_header("Tab Configuration", "🏷️")

st.markdown("**Default insight tabs:**")

for tab in DEFAULT_INSIGHT_TABS:
    st.markdown(f"""
    **{tab.icon} {tab.label}** (`{tab.tab_id}`)
    - Pipeline: `{tab.pipeline}`
    - {tab.description}
    """)

st.markdown("---")

# ============================================================================
# SECTION 5: ACCESSIBILITY VALIDATION
# ============================================================================

section_header("Accessibility Audit", "♿")

st.markdown("**WCAG compliance check:**")

validation = validate_insights_panel_accessibility()

if validation["valid"]:
    st.success("✅ Insights Panel passes accessibility validation")
else:
    st.error("❌ Accessibility issues found:")
    for issue in validation["issues"]:
        st.warning(f"- {issue}")

st.markdown("**Accessibility Features:**")
for feature in validation["features"]:
    st.markdown(f"- {feature}")

st.markdown("---")

# ============================================================================
# SECTION 6: COMPACT MODE
# ============================================================================

section_header("Compact Mode", "📦")

st.markdown("**Reduced height panel for space-constrained layouts:**")

render_insights_panel(
    data=FULL_DEMO_DATA,
    panel_id="compact_demo",
    title="Compact View",
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
    - Tabbed navigation (SAE/ERCE/BIRL/FAR)
    - Pipeline-specific color coding
    - Badge counts per tab
    - Empty state handling
    - Summary statistics per tab
    - Scrollable content area
    - Compact display mode
    - Session state persistence
    """)

with col2:
    st.markdown("""
    ### Integration API
    - `InsightsData` - Data container
    - `wrap_cc3_binder_output()` - CC3 wrapper
    - `extract_from_compare_v3()` - API wrapper
    - `render_insights_panel()` - Main render
    - `get_active_insight_tab()` - State access
    - `set_active_insight_tab()` - State update
    """)

st.caption(f"Insights Panel Demo | Phase 6 UI Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
