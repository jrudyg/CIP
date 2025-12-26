"""
TopNav Demo Page
Phase 6 UI Upgrade - P6.C2.T1 Validation

This page demonstrates the TopNav component with high-contrast mode support.
Shows tabbed navigation: Upload, Compare, Analyze, Export
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
from components.color_tokens import (
    inject_color_tokens,
    is_high_contrast_mode,
    get_token,
    get_all_tokens,
    get_token_reference,
    BASE_TOKENS,
    PIPELINE_TOKENS,
    NAV_TOKENS,
)
from components.topnav import (
    render_topnav,
    render_topnav_minimal,
    get_active_tab,
    set_active_tab,
    validate_topnav_accessibility,
    DEFAULT_NAV_TABS,
    NavTab,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="TopNav Demo",
    page_icon="🧭",
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
    st.markdown("### Navigation State")

    active = get_active_tab()
    st.info(f"Active Tab: **{active}**")

    st.markdown("---")
    st.markdown("### Contrast Mode")
    mode = "HIGH CONTRAST" if is_high_contrast_mode() else "Standard"
    st.success(f"Mode: **{mode}**")

# ============================================================================
# PAGE CONTENT
# ============================================================================

page_header("TopNav Component Demo", "🧭")

st.markdown("""
**Phase 6 UI Upgrade - P6.C2.T1: High-Contrast TopNav**

This demo showcases the TopNav component featuring:
- Tabbed navigation: Upload, Compare, Analyze, Export
- Systemwide high-contrast mode toggle
- Unified color token definitions
- WCAG AA accessibility compliance
""")

st.markdown("---")

# ============================================================================
# SECTION 1: MAIN TOPNAV
# ============================================================================

section_header("TopNav Component", "🧭")

st.markdown("**Full TopNav with contrast toggle:**")

active_tab = render_topnav(
    tabs=DEFAULT_NAV_TABS,
    logo_text="CIP Protocol",
    logo_icon="📋",
    show_contrast_toggle=True,
)

st.success(f"Currently active tab: **{active_tab}**")

st.markdown("---")

# ============================================================================
# SECTION 2: TAB CONTENT DEMO
# ============================================================================

section_header("Tab Content Area", "📄")

st.markdown("**Content changes based on active tab:**")

if active_tab == "upload":
    st.markdown("""
    ### 📤 Upload Section
    Upload your contract documents for analysis.

    - Supported formats: PDF, DOCX, TXT
    - Maximum file size: 10MB
    - Drag and drop or click to browse
    """)
    st.file_uploader("Upload Contract", type=["pdf", "docx", "txt"], key="demo_upload")

elif active_tab == "compare":
    st.markdown("""
    ### ⚖️ Compare Section
    Compare two versions of a contract.

    - Side-by-side diff view
    - Clause-level matching (SAE)
    - Risk delta analysis (ERCE)
    """)
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Version 1", ["Draft 1", "Draft 2", "Final"], key="demo_v1")
    with col2:
        st.selectbox("Version 2", ["Draft 1", "Draft 2", "Final"], key="demo_v2")

elif active_tab == "analyze":
    st.markdown("""
    ### 🔍 Analyze Section
    Deep analysis of contract risks and business impact.

    - ERCE Risk Classification
    - BIRL Business Narratives
    - FAR Flowdown Analysis
    """)
    st.slider("Risk Threshold", 0.0, 1.0, 0.7, key="demo_threshold")

elif active_tab == "export":
    st.markdown("""
    ### 📥 Export Section
    Export analysis reports and data.

    - PDF Report Generation
    - Excel Data Export
    - JSON API Format
    """)
    st.selectbox("Export Format", ["PDF Report", "Excel", "JSON"], key="demo_format")

st.markdown("---")

# ============================================================================
# SECTION 3: MINIMAL TOPNAV
# ============================================================================

section_header("Minimal TopNav Variant", "📍")

st.markdown("**Streamlit-native buttons only (no custom HTML):**")

minimal_active = render_topnav_minimal(DEFAULT_NAV_TABS)

st.caption(f"Selected: {minimal_active}")

st.markdown("---")

# ============================================================================
# SECTION 4: CUSTOM TABS EXAMPLE
# ============================================================================

section_header("Custom Tabs Configuration", "⚙️")

st.markdown("**TopNav with custom tabs and badges:**")

custom_tabs = [
    NavTab("inbox", "Inbox", "📥", "View incoming items", badge_count=5),
    NavTab("drafts", "Drafts", "📝", "Work in progress", badge_count=2),
    NavTab("sent", "Sent", "📤", "Sent items"),
    NavTab("archive", "Archive", "📦", "Archived items", disabled=True),
]

# Store custom tab state separately
if "_custom_tab_active" not in st.session_state:
    st.session_state["_custom_tab_active"] = "inbox"

custom_cols = st.columns(len(custom_tabs))
for idx, tab in enumerate(custom_tabs):
    with custom_cols[idx]:
        is_active = st.session_state["_custom_tab_active"] == tab.tab_id
        badge = f" ({tab.badge_count})" if tab.badge_count else ""
        if st.button(
            f"{tab.icon} {tab.label}{badge}",
            key=f"custom_tab_{tab.tab_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            disabled=tab.disabled,
        ):
            st.session_state["_custom_tab_active"] = tab.tab_id
            st.rerun()

st.info(f"Custom tab selected: **{st.session_state['_custom_tab_active']}**")

st.markdown("---")

# ============================================================================
# SECTION 5: COLOR TOKENS
# ============================================================================

section_header("Unified Color Tokens", "🎨")

st.markdown("**Current color token values (changes with contrast mode):**")

# Show token categories
token_tabs = st.tabs(["Base Tokens", "Pipeline Tokens", "Navigation Tokens"])

with token_tabs[0]:
    for name, token in list(BASE_TOKENS.items())[:8]:
        current_value = get_token(name)
        st.markdown(f"""
        `{name}`: <span style="background:{current_value}; padding:2px 8px; border-radius:4px; color:{'#000' if 'bg' not in name else '#fff'}">{current_value}</span> - {token.description}
        """, unsafe_allow_html=True)

with token_tabs[1]:
    st.markdown("**SAE Tokens:**")
    for name in ["sae-primary", "sae-bg", "sae-border"]:
        current_value = get_token(name)
        st.markdown(f"`{name}`: `{current_value}`")

    st.markdown("**ERCE Severity Tokens:**")
    for severity in ["critical", "high", "moderate", "admin"]:
        name = f"erce-{severity}"
        current_value = get_token(name)
        st.markdown(f"`{name}`: `{current_value}`")

with token_tabs[2]:
    for name, token in NAV_TOKENS.items():
        current_value = get_token(name)
        st.markdown(f"`{name}`: `{current_value}`")

st.markdown("---")

# ============================================================================
# SECTION 6: ACCESSIBILITY VALIDATION
# ============================================================================

section_header("Accessibility Validation", "♿")

st.markdown("**WCAG compliance check for TopNav:**")

validation = validate_topnav_accessibility(DEFAULT_NAV_TABS)

if validation["valid"]:
    st.success("✅ TopNav passes accessibility validation")
else:
    st.error("❌ Accessibility issues found:")
    for issue in validation["issues"]:
        st.warning(f"- {issue}")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Tabs", validation["tab_count"])
with col2:
    st.metric("Enabled Tabs", validation["enabled_count"])

st.markdown("**Accessibility Features:**")
st.markdown("""
- `role="navigation"` on nav element
- `role="tablist"` on tabs container
- `role="tab"` on individual tabs
- `aria-selected` state management
- `tabindex="0"` for keyboard navigation
- `:focus` and `:focus-visible` styling
- High contrast mode support
""")

st.markdown("---")

# ============================================================================
# SECTION 7: CONTRAST MODE COMPARISON
# ============================================================================

section_header("Contrast Mode Comparison", "🔳")

st.markdown("**Visual comparison of standard vs high-contrast:**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Standard Mode")
    standard_tokens = {
        "Background": get_token("bg-primary", force_high_contrast=False),
        "Text": get_token("text-primary", force_high_contrast=False),
        "Border": get_token("border-default", force_high_contrast=False),
        "Accent": get_token("accent-primary", force_high_contrast=False),
    }
    for name, value in standard_tokens.items():
        st.markdown(f"**{name}:** `{value}`")

with col2:
    st.markdown("##### High Contrast Mode")
    hc_tokens = {
        "Background": get_token("bg-primary", force_high_contrast=True),
        "Text": get_token("text-primary", force_high_contrast=True),
        "Border": get_token("border-default", force_high_contrast=True),
        "Accent": get_token("accent-primary", force_high_contrast=True),
    }
    for name, value in hc_tokens.items():
        st.markdown(f"**{name}:** `{value}`")

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Component Features
    - Tabbed navigation (Upload/Compare/Analyze/Export)
    - High-contrast mode toggle
    - Unified color token system
    - Session state persistence
    - WCAG AA accessibility
    - Keyboard navigation support
    - Badge count indicators
    - Disabled tab states
    - Responsive mobile layout
    """)

with col2:
    st.markdown("""
    ### Integration Points
    - All CIP pages (global navigation)
    - Theme system integration
    - Color token consumption
    - Session state coordination
    - Modular standalone operation
    """)

st.caption(f"TopNav Demo | Phase 6 UI Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
