"""
Clause Selector Demo Page
Phase 6 UI Upgrade - P6.C2.T2 Validation

This page demonstrates the Clause Selector component with persistent state.
Shows global V1/V2 clause ID state management.
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
from components.clause_selector import (
    ClauseInfo,
    ClauseSelection,
    render_clause_selector,
    render_clause_selector_minimal,
    get_clause_selection,
    set_clause_pair,
    clear_clause_selection,
    is_linked_mode,
    get_selected_clause_pair,
    has_valid_selection,
    get_selection_for_binder,
    validate_clause_selector_accessibility,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Clause Selector Demo",
    page_icon="📋",
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
    st.markdown("### Selection State")

    selection = get_clause_selection()
    st.info(f"V1: **{selection.v1_clause_id or 'None'}**")
    st.info(f"V2: **{selection.v2_clause_id or 'None'}**")
    st.info(f"Linked: **{selection.is_linked}**")

    st.markdown("---")

    if st.button("🗑️ Clear Selection", use_container_width=True):
        clear_clause_selection()
        st.rerun()

# ============================================================================
# DEMO DATA
# ============================================================================

DEMO_V1_CLAUSES = [
    ClauseInfo(
        clause_id=1,
        title="Limitation of Liability",
        section="Section 8.1",
        preview="Neither party shall be liable for any indirect, incidental, or consequential damages...",
        severity="CRITICAL",
        has_changes=True,
        word_count=245,
    ),
    ClauseInfo(
        clause_id=2,
        title="Indemnification",
        section="Section 8.2",
        preview="Each party shall indemnify and hold harmless the other party from any claims...",
        severity="HIGH",
        has_changes=True,
        word_count=312,
    ),
    ClauseInfo(
        clause_id=3,
        title="Intellectual Property",
        section="Section 9.1",
        preview="All intellectual property developed under this agreement shall be owned by...",
        severity="HIGH",
        has_changes=False,
        word_count=198,
    ),
    ClauseInfo(
        clause_id=4,
        title="Confidentiality",
        section="Section 10.1",
        preview="Each party agrees to maintain the confidentiality of all proprietary information...",
        severity="MODERATE",
        has_changes=True,
        word_count=276,
    ),
    ClauseInfo(
        clause_id=5,
        title="Term and Termination",
        section="Section 11.1",
        preview="This agreement shall commence on the effective date and continue for a period of...",
        severity="MODERATE",
        has_changes=False,
        word_count=189,
    ),
    ClauseInfo(
        clause_id=6,
        title="Notice Provisions",
        section="Section 12.1",
        preview="All notices required under this agreement shall be in writing and delivered to...",
        severity="ADMIN",
        has_changes=True,
        word_count=124,
    ),
    ClauseInfo(
        clause_id=7,
        title="Force Majeure",
        section="Section 13.1",
        preview="Neither party shall be liable for failure to perform due to circumstances beyond...",
        severity="MODERATE",
        has_changes=False,
        word_count=156,
    ),
]

DEMO_V2_CLAUSES = [
    ClauseInfo(
        clause_id=1,
        title="Limitation of Liability (Amended)",
        section="Section 8.1",
        preview="Liability shall be limited to the total fees paid under this agreement...",
        severity="HIGH",  # Changed from CRITICAL
        has_changes=True,
        word_count=267,
    ),
    ClauseInfo(
        clause_id=2,
        title="Indemnification (Expanded)",
        section="Section 8.2",
        preview="Each party shall indemnify, defend, and hold harmless the other party...",
        severity="HIGH",
        has_changes=True,
        word_count=356,
    ),
    ClauseInfo(
        clause_id=3,
        title="Intellectual Property",
        section="Section 9.1",
        preview="All intellectual property developed under this agreement shall be owned by...",
        severity="HIGH",
        has_changes=False,
        word_count=198,
    ),
    ClauseInfo(
        clause_id=4,
        title="Confidentiality (Extended)",
        section="Section 10.1",
        preview="Each party agrees to maintain the confidentiality of all proprietary information for 5 years...",
        severity="MODERATE",
        has_changes=True,
        word_count=298,
    ),
    ClauseInfo(
        clause_id=5,
        title="Term and Termination",
        section="Section 11.1",
        preview="This agreement shall commence on the effective date and continue for a period of...",
        severity="MODERATE",
        has_changes=False,
        word_count=189,
    ),
    ClauseInfo(
        clause_id=6,
        title="Notice Provisions (Updated)",
        section="Section 12.1",
        preview="All notices shall be delivered electronically to the designated contacts...",
        severity="ADMIN",
        has_changes=True,
        word_count=118,
    ),
    ClauseInfo(
        clause_id=7,
        title="Force Majeure",
        section="Section 13.1",
        preview="Neither party shall be liable for failure to perform due to circumstances beyond...",
        severity="MODERATE",
        has_changes=False,
        word_count=156,
    ),
    ClauseInfo(
        clause_id=8,
        title="Data Protection (NEW)",
        section="Section 14.1",
        preview="Both parties shall comply with applicable data protection laws including GDPR...",
        severity="HIGH",
        has_changes=True,
        word_count=234,
    ),
]

# ============================================================================
# PAGE CONTENT
# ============================================================================

page_header("Clause Selector Demo", "📋")

st.markdown("""
**Phase 6 UI Upgrade - P6.C2.T2: Clause Selector Component**

This demo showcases the Clause Selector with:
- Persistent V1/V2 clause ID state management
- Linked/independent selection modes
- Severity indicators and change markers
- Session state persistence across reruns
- WCAG AA keyboard navigation
""")

st.markdown("---")

# ============================================================================
# SECTION 1: MAIN CLAUSE SELECTOR
# ============================================================================

section_header("Clause Selector", "📋")

st.markdown("**Select clauses from V1 and V2 to compare:**")

selection = render_clause_selector(
    v1_clauses=DEMO_V1_CLAUSES,
    v2_clauses=DEMO_V2_CLAUSES,
    title="Contract Clause Selection",
    show_link_toggle=True,
    compact=False,
)

st.markdown("---")

# ============================================================================
# SECTION 2: SELECTION STATE
# ============================================================================

section_header("Selection State (Persisted)", "💾")

st.markdown("**Current selection survives page reruns:**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### Raw State")
    st.json(get_selection_for_binder())

with col2:
    st.markdown("##### Clause Pair")
    v1, v2 = get_selected_clause_pair()
    st.code(f"V1: {v1}\nV2: {v2}")

with col3:
    st.markdown("##### Validation")
    st.success(f"Valid: {has_valid_selection()}")
    st.info(f"Linked: {is_linked_mode()}")

st.markdown("---")

# ============================================================================
# SECTION 3: MINIMAL SELECTOR
# ============================================================================

section_header("Minimal Selector Variant", "📍")

st.markdown("**Dropdown-style selector for compact layouts:**")

col1, col2 = st.columns(2)

with col1:
    v1_min = render_clause_selector_minimal(
        DEMO_V1_CLAUSES,
        version="v1",
        selected_id=selection.v1_clause_id,
    )
    st.caption(f"Selected: {v1_min}")

with col2:
    v2_min = render_clause_selector_minimal(
        DEMO_V2_CLAUSES,
        version="v2",
        selected_id=selection.v2_clause_id,
    )
    st.caption(f"Selected: {v2_min}")

st.markdown("---")

# ============================================================================
# SECTION 4: PROGRAMMATIC SELECTION
# ============================================================================

section_header("Programmatic Selection", "⚡")

st.markdown("**Set clause pair programmatically:**")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Select Pair 1-1", use_container_width=True):
        set_clause_pair(1, 1)
        st.rerun()

with col2:
    if st.button("Select Pair 2-2", use_container_width=True):
        set_clause_pair(2, 2)
        st.rerun()

with col3:
    if st.button("Select 3-8 (Unmatched)", use_container_width=True):
        set_clause_pair(3, 8)
        st.rerun()

st.markdown("---")

# ============================================================================
# SECTION 5: CLAUSE DETAILS
# ============================================================================

section_header("Selected Clause Details", "🔍")

st.markdown("**Details for currently selected clauses:**")

if selection.v1_clause_id:
    v1_clause = next((c for c in DEMO_V1_CLAUSES if c.clause_id == selection.v1_clause_id), None)
    if v1_clause:
        with st.expander(f"📄 V1: {v1_clause.title}", expanded=True):
            st.markdown(f"**Section:** {v1_clause.section}")
            st.markdown(f"**Severity:** {v1_clause.severity}")
            st.markdown(f"**Word Count:** {v1_clause.word_count}")
            st.markdown(f"**Has Changes:** {'Yes' if v1_clause.has_changes else 'No'}")
            st.markdown(f"**Preview:** {v1_clause.preview}")
else:
    st.info("No V1 clause selected")

if selection.v2_clause_id:
    v2_clause = next((c for c in DEMO_V2_CLAUSES if c.clause_id == selection.v2_clause_id), None)
    if v2_clause:
        with st.expander(f"📝 V2: {v2_clause.title}", expanded=True):
            st.markdown(f"**Section:** {v2_clause.section}")
            st.markdown(f"**Severity:** {v2_clause.severity}")
            st.markdown(f"**Word Count:** {v2_clause.word_count}")
            st.markdown(f"**Has Changes:** {'Yes' if v2_clause.has_changes else 'No'}")
            st.markdown(f"**Preview:** {v2_clause.preview}")
else:
    st.info("No V2 clause selected")

st.markdown("---")

# ============================================================================
# SECTION 6: ACCESSIBILITY VALIDATION
# ============================================================================

section_header("Accessibility Validation", "♿")

st.markdown("**WCAG compliance check:**")

validation = validate_clause_selector_accessibility(DEMO_V1_CLAUSES, DEMO_V2_CLAUSES)

if validation["valid"]:
    st.success("✅ Clause Selector passes accessibility validation")
else:
    st.error("❌ Accessibility issues found:")
    for issue in validation["issues"]:
        st.warning(f"- {issue}")

col1, col2 = st.columns(2)
with col1:
    st.metric("V1 Clauses", validation["v1_count"])
with col2:
    st.metric("V2 Clauses", validation["v2_count"])

st.markdown("**Accessibility Features:**")
st.markdown("""
- `tabindex="0"` for keyboard navigation
- `role="option"` on clause items
- `aria-selected` state tracking
- `:focus-visible` styling
- High contrast mode support
- Clear selection indicators
""")

st.markdown("---")

# ============================================================================
# SECTION 7: CC3 INTEGRATION
# ============================================================================

section_header("CC3 Data Binder Integration", "🔌")

st.markdown("**Selection data formatted for CC3 multi-clause logic:**")

binder_data = get_selection_for_binder()

st.code(f"""
# CC3 Integration Example
from components.clause_selector import get_selection_for_binder

binder_data = get_selection_for_binder()
# Returns: {binder_data}

# Use in data pipeline:
if binder_data['has_selection']:
    process_clause_pair(
        v1_id=binder_data['v1_clause_id'],
        v2_id=binder_data['v2_clause_id'],
        linked=binder_data['is_linked']
    )
""", language="python")

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Component Features
    - Persistent V1/V2 clause ID state
    - Linked/independent selection modes
    - Severity indicators (CRITICAL/HIGH/MODERATE/ADMIN)
    - Change markers for modified clauses
    - Session state persistence
    - Keyboard navigation (tabindex)
    - ARIA attributes for accessibility
    - Minimal dropdown variant
    - CC3 data binder integration
    """)

with col2:
    st.markdown("""
    ### State Management API
    - `get_clause_selection()` - Get current state
    - `set_v1_clause(id)` - Set V1 selection
    - `set_v2_clause(id)` - Set V2 selection
    - `set_clause_pair(v1, v2)` - Set both
    - `clear_clause_selection()` - Reset
    - `is_linked_mode()` - Check link status
    - `get_selection_for_binder()` - CC3 format
    """)

st.caption(f"Clause Selector Demo | Phase 6 UI Upgrade | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
