"""
FAR Action Bar Demo Page
Phase 5 UX Upgrade - Task 4 Validation

This page demonstrates the FAR Action Bar component for GEM UX validation.
Shows persistent action bar with fixed positioning and high-contrast styling.
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
from components.far_action_bar import (
    inject_far_action_bar_css,
    render_far_action_bar,
    render_far_inline_summary,
    render_far_gap_list,
    render_far_expander,
    render_far_gap_card,
    render_far_summary_badges,
    get_far_summary_stats,
    should_show_action_bar,
    FAR_SEVERITY_LEVELS,
    FAR_ACTION_TYPES,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="FAR Action Bar Demo",
    page_icon="📋",
    layout="wide"
)

apply_spacing()
apply_theme()
inject_dark_theme()

# Sidebar
with st.sidebar:
    inject_cip_logo()

    st.markdown("---")

    st.markdown("### Action Bar Options")

    fixed_position = st.checkbox("Fixed Position (bottom)", value=False, help="Enable fixed bottom viewport positioning")
    high_contrast = st.checkbox("High Contrast Mode", value=False, help="Enable high contrast styling")
    show_details = st.checkbox("Show Details Panel", value=True, help="Enable expandable details")

    st.markdown("---")

    # Action log
    st.markdown("### Action Log")
    action_key = "far_action_demo"
    if action_key in st.session_state:
        st.success(f"Last action: {st.session_state[action_key]}")
    else:
        st.caption("No actions taken yet")

# ============================================================================
# DEMO DATA
# ============================================================================

DEMO_FLOWDOWN_GAPS = [
    {
        "gap_type": "Liability Cap Mismatch",
        "severity": "CRITICAL",
        "upstream_value": "$5,000,000 aggregate cap",
        "downstream_value": "Unlimited liability",
        "recommendation": "Negotiate liability cap in subcontract to match prime contract limits. Consider adding mutual limitation clause.",
    },
    {
        "gap_type": "Insurance Requirements Gap",
        "severity": "CRITICAL",
        "upstream_value": "$2M General Liability, $1M Professional",
        "downstream_value": "$500K General Liability only",
        "recommendation": "Require subcontractor to increase coverage to meet prime contract minimums before execution.",
    },
    {
        "gap_type": "Indemnification Scope",
        "severity": "HIGH",
        "upstream_value": "Mutual indemnification, capped",
        "downstream_value": "One-way indemnification, uncapped",
        "recommendation": "Add mutual indemnification clause and align caps with prime contract terms.",
    },
    {
        "gap_type": "Termination Notice Period",
        "severity": "HIGH",
        "upstream_value": "90 days written notice",
        "downstream_value": "30 days written notice",
        "recommendation": "Extend subcontract notice period to allow adequate time for transition planning.",
    },
    {
        "gap_type": "Audit Rights",
        "severity": "MODERATE",
        "upstream_value": "Government audit rights included",
        "downstream_value": "No audit provisions",
        "recommendation": "Add flowdown clause for government audit rights to ensure prime contract compliance.",
    },
    {
        "gap_type": "IP Ownership",
        "severity": "HIGH",
        "upstream_value": "Client owns all deliverables",
        "downstream_value": "Contractor retains derivative works",
        "recommendation": "Clarify IP assignment to ensure flowdown of ownership requirements.",
    },
    {
        "gap_type": "Confidentiality Duration",
        "severity": "MODERATE",
        "upstream_value": "5 years post-termination",
        "downstream_value": "2 years post-termination",
        "recommendation": "Extend confidentiality period in subcontract to meet prime requirements.",
    },
    {
        "gap_type": "Force Majeure Definition",
        "severity": "MODERATE",
        "upstream_value": "Includes pandemic, cyber events",
        "downstream_value": "Traditional definition only",
        "recommendation": "Update force majeure clause to include expanded events matching prime contract.",
    },
]

# ============================================================================
# PAGE CONTENT
# ============================================================================

# Inject CSS
inject_far_action_bar_css()

page_header("FAR Action Bar Demo", "📋")

st.markdown("""
**Phase 5 UX Upgrade - Task 4: FAR Action Bar**

This demo page showcases the FAR (Flowdown Analysis & Requirements) Action Bar component that provides:
- Persistent action bar with fixed bottom viewport positioning
- High-contrast, non-dismissible styling for critical actions
- Summary badges showing gap counts by severity
- Expandable details panel with gap cards
- Action buttons for common workflow operations
""")

st.warning("👈 **Use the sidebar options to toggle fixed positioning and high contrast mode**")

st.markdown("---")

# ============================================================================
# SECTION 1: SUMMARY STATISTICS
# ============================================================================

section_header("Gap Statistics", "📊")

stats = get_far_summary_stats(DEMO_FLOWDOWN_GAPS)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Gaps", stats["total_gaps"])

with col2:
    st.metric("Critical", stats["critical_count"], delta="Action Required" if stats["critical_count"] > 0 else None, delta_color="inverse")

with col3:
    st.metric("High", stats["high_count"])

with col4:
    st.metric("Moderate", stats["moderate_count"])

# Show action bar indicator
if should_show_action_bar(DEMO_FLOWDOWN_GAPS):
    st.error("🚨 **Action Bar Recommended** - Critical or High severity gaps detected")
else:
    st.success("✅ No critical gaps - Action bar optional")

st.markdown("---")

# ============================================================================
# SECTION 2: MAIN ACTION BAR
# ============================================================================

section_header("Persistent Action Bar", "⚡")

st.markdown("**The main FAR Action Bar with configurable positioning:**")

render_far_action_bar(
    flowdown_gaps=DEMO_FLOWDOWN_GAPS,
    bar_id="demo",
    title="Flowdown Gap Analysis",
    subtitle="8 gaps identified requiring action",
    show_details=show_details,
    fixed_position=fixed_position,
    high_contrast=high_contrast,
)

st.markdown("---")

# ============================================================================
# SECTION 3: SEVERITY LEVEL REFERENCE
# ============================================================================

section_header("Severity Levels", "🎨")

st.markdown("**FAR gap severity classifications:**")

for severity, config in FAR_SEVERITY_LEVELS.items():
    st.markdown(f"""
    **{config['icon']} {config['label']}** (`{severity}`)
    - Color: `{config['color']}`
    - {config['description']}
    """)

st.markdown("---")

# ============================================================================
# SECTION 4: ACTION TYPES
# ============================================================================

section_header("Available Actions", "🎯")

st.markdown("**Action buttons available in the action bar:**")

cols = st.columns(5)
for idx, (action_id, config) in enumerate(FAR_ACTION_TYPES.items()):
    with cols[idx % 5]:
        st.markdown(f"""
        **{config['icon']} {config['label']}**

        {config['description']}
        """)

st.markdown("---")

# ============================================================================
# SECTION 5: INDIVIDUAL GAP CARDS
# ============================================================================

section_header("Gap Card Examples", "🃏")

st.markdown("**Individual gap cards showing different severity levels:**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Critical Gap")
    card_html = render_far_gap_card(
        gap_type="Liability Cap Missing",
        severity="CRITICAL",
        upstream_value="$5M cap required",
        downstream_value="No cap specified",
        recommendation="Add liability cap clause before execution",
    )
    st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("##### Moderate Gap")
    card_html = render_far_gap_card(
        gap_type="Notice Period",
        severity="MODERATE",
        upstream_value="60 days",
        downstream_value="30 days",
        recommendation="Consider extending notice period",
    )
    st.markdown(card_html, unsafe_allow_html=True)

with col2:
    st.markdown("##### High Gap")
    card_html = render_far_gap_card(
        gap_type="Insurance Shortfall",
        severity="HIGH",
        upstream_value="$2M coverage",
        downstream_value="$500K coverage",
        recommendation="Require increased coverage",
    )
    st.markdown(card_html, unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# SECTION 6: SUMMARY BADGES
# ============================================================================

section_header("Summary Badges", "🏷️")

st.markdown("**Severity summary badges (rendered inline):**")

badges_html = render_far_summary_badges(DEMO_FLOWDOWN_GAPS)
st.markdown(badges_html, unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# SECTION 7: INLINE SUMMARY
# ============================================================================

section_header("Inline Summary View", "📝")

st.markdown("**Compact inline summary for embedded displays:**")

render_far_inline_summary(DEMO_FLOWDOWN_GAPS, "Contract A vs Contract B")

st.markdown("---")

# ============================================================================
# SECTION 8: EXPANDER INTEGRATION
# ============================================================================

section_header("Expander Integration", "📂")

st.markdown("**FAR gaps in a Streamlit expander:**")

render_far_expander(
    flowdown_gaps=DEMO_FLOWDOWN_GAPS,
    title="Flowdown Gaps (FAR)",
    expanded=True,
    max_display=4
)

st.markdown("---")

# ============================================================================
# SECTION 9: GAP LIST
# ============================================================================

section_header("Gap List View", "📋")

st.markdown("**Full gap list display:**")

render_far_gap_list(DEMO_FLOWDOWN_GAPS, max_display=5)

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Component Features
    - Fixed bottom viewport positioning
    - High-contrast, non-dismissible styling
    - Animated gradient indicator bar
    - Severity-coded summary badges
    - Expandable details panel
    - Action buttons with callbacks
    - Gap cards with recommendations
    - Session state persistence
    - Print-friendly styles
    """)

with col2:
    st.markdown("""
    ### Integration Points
    - Compare Versions page (when FAR gaps detected)
    - Contract analysis completion
    - Flowdown compliance reviews
    - Subcontract generation workflows
    - Risk assessment dashboards
    """)

st.caption(f"FAR Action Bar Demo | Phase 5 UX Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
