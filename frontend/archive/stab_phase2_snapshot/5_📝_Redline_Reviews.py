"""
CIP - Review Changes Page
Interactive clause-by-clause redline review with minimal revision suggestions
v1.5: Zone layout retrofit
"""

import streamlit as st
import pandas as pd
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import UI components
from ui_components import (
    page_header, section_header,
    risk_badge, toast_success,
    toast_warning, toast_info, apply_spacing
)
from shared_components import contract_selector, api_call_with_spinner, API_BASE_URL
from components.contract_context import (
    init_contract_context,
    get_active_contract,
    get_active_contract_data,
    render_active_contract_header,
    render_recent_contracts_widget
)
from theme_system import apply_theme, inject_cip_logo
from zone_layout import zone_layout, check_system_health, system_status
from cip_components import document_viewer, smart_list
import requests

# Page config
st.set_page_config(page_title="Review Changes", page_icon="📝", layout="wide")
apply_theme()
apply_spacing()

# Inject centralized dark theme
from components.theme import inject_dark_theme
inject_dark_theme()

# Sidebar
with st.sidebar:
    inject_cip_logo()

# Initialize contract context
init_contract_context()

# Check system health
api_healthy, db_healthy, ai_healthy = check_system_health()

# Initialize session state
if 'selected_contract_id' not in st.session_state:
    st.session_state.selected_contract_id = None
if 'redline_result' not in st.session_state:
    st.session_state.redline_result = None
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False
if 'current_clause_index' not in st.session_state:
    st.session_state.current_clause_index = 0
if 'clause_decisions' not in st.session_state:
    st.session_state.clause_decisions = {}
if 'modified_revisions' not in st.session_state:
    st.session_state.modified_revisions = {}
if 'change_filter' not in st.session_state:
    st.session_state.change_filter = "All"

# Page header
page_header("📝 Review Changes", "Clause-by-clause minimal revision suggestions")
render_active_contract_header()

# Auto-load active contract from context
active_id = get_active_contract()
active_data = get_active_contract_data()

if active_id and not st.session_state.selected_contract_id:
    st.session_state.selected_contract_id = active_id


# Zone content functions
def z1_document_selector():
    """Z1: Document selector, version picker"""
    section_header("Select Document", "📄")

    if active_id:
        st.info(f"📋 Auto-loaded: #{active_id} - {active_data.get('title', 'Unknown')}")

    selected_contract_id, selected_contract, contracts = contract_selector(
        label="Choose a contract for review",
        key="contract_selector_z1",
        show_details=True
    )

    if selected_contract_id:
        st.session_state.selected_contract_id = selected_contract_id

    st.markdown("**Review Context**")
    col1, col2 = st.columns(2)
    with col1:
        position = st.selectbox("Position", ["Vendor", "Customer"], key="position_z1")
    with col2:
        leverage = st.selectbox("Leverage", ["Strong", "Moderate", "Weak"], key="leverage_z1", index=1)

    contract_type = st.text_input("Contract Type", value="Services Agreement", key="contract_type_z1")

    if st.button("🚀 Start Review", type="primary", use_container_width=True, key="start_review_z1"):
        if st.session_state.selected_contract_id:
            st.session_state.analyzing = True
            st.session_state.clause_decisions = {}
            st.session_state.modified_revisions = {}
            st.session_state.current_clause_index = 0
            st.rerun()
        else:
            st.warning("Select a contract first")


def z2_change_summary():
    """Z2: Change summary stats"""
    section_header("Change Summary", "📊")

    if st.session_state.redline_result:
        clauses = st.session_state.redline_result.get('clauses', [])
        total_clauses = len(clauses)
        suggestions_count = sum(1 for c in clauses if c.get('suggested_revision'))
        approved_count = sum(1 for status in st.session_state.clause_decisions.values() if status == 'approved')
        rejected_count = sum(1 for status in st.session_state.clause_decisions.values() if status == 'rejected')
        modified_count = sum(1 for status in st.session_state.clause_decisions.values() if status == 'modified')

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Clauses", total_clauses)
            st.metric("Suggestions", suggestions_count)
        with col2:
            st.metric("✅ Approved", approved_count)
            st.metric("❌ Rejected", rejected_count)

        st.metric("✏️ Modified", modified_count)

        # Progress
        if suggestions_count > 0:
            reviewed = approved_count + rejected_count + modified_count
            progress = reviewed / suggestions_count
            st.progress(progress)
            st.caption(f"{reviewed}/{suggestions_count} reviewed")
    else:
        st.info("Start a review to see summary")


def z3_change_filters():
    """Z3: Change type filters"""
    section_header("Filter Changes", "🔽")

    change_filter = st.radio(
        "Show",
        ["All", "Pending", "Approved", "Rejected", "Modified"],
        key="change_filter_z3",
        horizontal=False
    )
    st.session_state.change_filter = change_filter

    if st.session_state.redline_result:
        clauses = st.session_state.redline_result.get('clauses', [])
        st.markdown("---")
        st.markdown("**Risk Levels**")

        high_risk = sum(1 for c in clauses if c.get('risk_level') in ['HIGH', 'CRITICAL'])
        medium_risk = sum(1 for c in clauses if c.get('risk_level') == 'MEDIUM')
        low_risk = sum(1 for c in clauses if c.get('risk_level') == 'LOW')

        st.caption(f"🔴 High: {high_risk}")
        st.caption(f"🟡 Medium: {medium_risk}")
        st.caption(f"🟢 Low: {low_risk}")


def z4_redline_view():
    """Z4: Redline document view, tracked changes display"""
    section_header("Review Changes", "📝")

    if st.session_state.redline_result:
        clauses = st.session_state.redline_result.get('clauses', [])

        if not clauses:
            st.warning("No clauses found")
            return

        current_idx = st.session_state.current_clause_index
        current_clause = clauses[current_idx]

        # Clause header
        st.markdown(f"### {current_clause.get('section_number', 'N/A')}: {current_clause.get('section_title', 'Unknown')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Risk:** {risk_badge(current_clause.get('risk_level', 'UNKNOWN'))}")
        with col2:
            st.markdown(f"**Pattern:** {current_clause.get('pattern_applied', 'N/A')}")
        with col3:
            decision = st.session_state.clause_decisions.get(current_idx, 'pending')
            st.markdown(f"**Status:** {decision.upper()}")

        # Original text
        st.markdown("#### Original Text")
        original_text = current_clause.get('clause_text', 'No text available')
        st.text_area("Original", value=original_text, height=120, key=f"original_{current_idx}", disabled=True)

        # Suggested revision
        if current_clause.get('suggested_revision'):
            st.markdown("#### Suggested Revision")

            # Change metrics
            metrics = current_clause.get('change_metrics', {})
            change_ratio = metrics.get('change_ratio', 0)
            word_retention = metrics.get('word_retention', 0)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Change Ratio", f"{change_ratio:.1%}")
            with col2:
                st.metric("Word Retention", f"{word_retention:.1%}")

            # HTML redline
            html_redline = current_clause.get('html_redline', '')
            if html_redline:
                st.markdown(
                    f'<div style="border:1px solid #334155;padding:10px;border-radius:5px;background:#1E293B;max-height:200px;overflow-y:auto;color:#E2E8F0;">{html_redline}</div>',
                    unsafe_allow_html=True
                )

            # Editable revision
            revision_text = st.session_state.modified_revisions.get(current_idx, current_clause.get('suggested_revision', ''))
            modified_text = st.text_area("Edit if needed", value=revision_text, height=120, key=f"revision_{current_idx}")

            # Action buttons
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("✅ Approve", use_container_width=True, type="primary", key=f"approve_{current_idx}"):
                    st.session_state.clause_decisions[current_idx] = 'approved'
                    _advance_to_next(clauses, current_idx)

            with col2:
                if st.button("✏️ Modify", use_container_width=True, key=f"modify_{current_idx}"):
                    st.session_state.clause_decisions[current_idx] = 'modified'
                    st.session_state.modified_revisions[current_idx] = modified_text
                    _advance_to_next(clauses, current_idx)

            with col3:
                if st.button("❌ Reject", use_container_width=True, key=f"reject_{current_idx}"):
                    st.session_state.clause_decisions[current_idx] = 'rejected'
                    _advance_to_next(clauses, current_idx)

            with col4:
                if st.button("⏭️ Skip", use_container_width=True, key=f"skip_{current_idx}"):
                    st.session_state.current_clause_index = (current_idx + 1) % len(clauses)
                    st.rerun()
        else:
            st.info("No revision suggested for this clause")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⏮️ Previous", use_container_width=True, key="prev_no_rev"):
                    st.session_state.current_clause_index = (current_idx - 1) % len(clauses)
                    st.rerun()
            with col2:
                if st.button("⏭️ Next", use_container_width=True, key="next_no_rev"):
                    st.session_state.current_clause_index = (current_idx + 1) % len(clauses)
                    st.rerun()
    else:
        st.info("Start a review to see changes")


def _advance_to_next(clauses, current_idx):
    """Helper to advance to next pending clause"""
    next_pending = next(
        (i for i in range(current_idx + 1, len(clauses))
         if clauses[i].get('suggested_revision') and i not in st.session_state.clause_decisions),
        None
    )
    if next_pending:
        st.session_state.current_clause_index = next_pending
    st.rerun()


def z5_change_history():
    """Z5: Change history"""
    section_header("Change History", "📚")

    if st.session_state.redline_result:
        clauses = st.session_state.redline_result.get('clauses', [])

        # Build history list
        history_items = []
        for idx, (clause_idx, decision) in enumerate(st.session_state.clause_decisions.items()):
            if clause_idx < len(clauses):
                clause = clauses[clause_idx]
                icon = {'approved': '✅', 'rejected': '❌', 'modified': '✏️'}.get(decision, '⚪')
                history_items.append({
                    'title': f"{icon} {clause.get('section_number', 'N/A')}",
                    'subtitle': clause.get('section_title', 'Unknown')[:30],
                    'status': decision
                })

        if history_items:
            for item in history_items[-10:]:  # Show last 10
                st.markdown(f"**{item['title']}**")
                st.caption(f"{item['subtitle']} - {item['status']}")
                st.divider()
        else:
            st.info("No decisions yet")
    else:
        st.info("Start review to see history")


def z6_review_guidance():
    """Z6: Review guidance"""
    section_header("Review Guidance", "💡")

    st.markdown("**Quick Tips:**")
    st.markdown("• Red strikethrough = deleted")
    st.markdown("• Green bold = inserted")
    st.markdown("• Focus on HIGH risk first")
    st.markdown("• Modify suggestions if needed")

    if st.session_state.redline_result:
        st.markdown("---")
        approved_count = sum(1 for status in st.session_state.clause_decisions.values() if status in ['approved', 'modified'])

        if st.button("📤 Export Approved", use_container_width=True, key="export_z6"):
            if approved_count > 0:
                toast_success(f"Exporting {approved_count} changes...")
            else:
                toast_warning("No approved changes to export")


def z7_extra():
    """Z7: Additional controls"""
    pass


# Render zone layout
zone_layout(
    z1=z1_document_selector,
    z2=z2_change_summary,
    z3=z3_change_filters,
    z4=z4_redline_view,
    z5=z5_change_history,
    z6=z6_review_guidance,
    z7=z7_extra,
    z7_system_status=True,
    api_healthy=api_healthy,
    db_healthy=db_healthy,
    ai_healthy=ai_healthy
)

# Run analysis if triggered
if st.session_state.analyzing:
    position = st.session_state.get('position_z1', 'Vendor')
    leverage = st.session_state.get('leverage_z1', 'Moderate')
    contract_type = st.session_state.get('contract_type_z1', 'Services Agreement')

    context = {
        'position': position,
        'leverage': leverage,
        'contract_type': contract_type
    }

    result, error = api_call_with_spinner(
        endpoint="/api/redline-review",
        method="POST",
        data={
            'contract_id': st.session_state.selected_contract_id,
            'context': context
        },
        spinner_message="Analyzing contract and generating redlines... This may take 1-3 minutes...",
        timeout=300
    )

    if error:
        st.error(f"Analysis failed: {error}")
    else:
        st.session_state.redline_result = result
        toast_success(f"Generated {len(result.get('clauses', []))} redline suggestions!")

    st.session_state.analyzing = False
    if result:
        st.rerun()

