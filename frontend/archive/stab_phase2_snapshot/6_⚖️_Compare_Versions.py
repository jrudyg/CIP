"""
CIP - Compare Two Versions Page (API Integrated)
Compare contract versions and identify changes
v1.5: Zone layout retrofit
"""

import streamlit as st
import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

sys.path.append('C:\\Users\\jrudy\\CIP\\frontend')
from theme_system import apply_theme, inject_cip_logo
from ui_components import (
    page_header, section_header,
    toast_success, toast_info, apply_spacing
)
from shared_components import dual_contract_selector, api_call_with_spinner
from components.contract_context import (
    init_contract_context,
    get_active_contract,
    get_active_contract_data,
    render_active_contract_header,
    render_recent_contracts_widget
)
from zone_layout import zone_layout, check_system_health, system_status
from cip_components import split_panel, smart_list

API_BASE = "http://localhost:5000/api"

# Page config
st.set_page_config(page_title="Compare Two Versions", page_icon="⚖️", layout="wide")
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


def fetch_risk_assessment(contract_id: int) -> dict:
    """Fetch risk assessment for a contract"""
    try:
        resp = requests.get(f"{API_BASE}/assessment/{contract_id}", timeout=10)
        if resp.ok:
            return resp.json()
        return None
    except:
        return None


def count_risks(assessment: dict) -> dict:
    """Count risks by level from assessment"""
    if not assessment:
        return {'DEALBREAKER': 0, 'CRITICAL': 0, 'IMPORTANT': 0, 'STANDARD': 0, 'total': 0}

    counts = {
        'DEALBREAKER': len(assessment.get('dealbreakers', [])),
        'CRITICAL': len(assessment.get('critical_items', [])),
        'IMPORTANT': len(assessment.get('important_items', [])),
        'STANDARD': len(assessment.get('standard_items', [])),
    }
    counts['total'] = sum(counts.values())
    counts['overall_risk'] = assessment.get('overall_risk', 'N/A')
    return counts


# Initialize session state
if 'comparison_result' not in st.session_state:
    st.session_state.comparison_result = None
if 'comparing' not in st.session_state:
    st.session_state.comparing = False
if 'v1_id' not in st.session_state:
    st.session_state.v1_id = None
if 'v2_id' not in st.session_state:
    st.session_state.v2_id = None
if 'selected_section' not in st.session_state:
    st.session_state.selected_section = None

# Page header
page_header("⚖️ Compare Two Versions", "Compare contract versions and identify changes")
render_active_contract_header()

# Auto-load active contract
active_id = get_active_contract()
active_data = get_active_contract_data()


# Zone content functions
def z1_contract_selection():
    """Z1: Contract selection (V1, V2 dropdowns)"""
    section_header("Select Contracts", "📄")

    if active_id:
        st.info(f"📋 V1 (from Portfolio): #{active_id} - {active_data.get('title', 'Unknown')}")

    v1_id, v2_id, v1_contract, v2_contract, contracts = dual_contract_selector(
        label1="Select V1 (Original)",
        label2="Select V2 (Revised)",
        key1="v1_selector_z1",
        key2="v2_selector_z1",
        validate_different=True
    )

    if v1_id:
        st.session_state.v1_id = v1_id
        st.session_state.v1_contract = v1_contract
    if v2_id:
        st.session_state.v2_id = v2_id
        st.session_state.v2_contract = v2_contract

    if v1_id and v2_id:
        if st.button("🔍 Compare Two Versions", type="primary", use_container_width=True, key="compare_z1"):
            st.session_state.comparing = True
            st.rerun()


def z2_executive_summary():
    """Z2: Executive summary, impact category counts"""
    section_header("Executive Summary", "📊")

    if st.session_state.comparison_result:
        result = st.session_state.comparison_result

        total_changes = result.get('total_changes', 0)
        impact = result.get('impact_breakdown', {})

        st.metric("Total Changes", total_changes)

        col1, col2 = st.columns(2)
        with col1:
            critical = impact.get('CRITICAL', 0) + impact.get('HIGH_PRIORITY', 0)
            st.metric("🔴 Critical", critical)
        with col2:
            important = impact.get('IMPORTANT', 0)
            st.metric("🟡 Important", important)

        admin = impact.get('ADMINISTRATIVE', 0) + impact.get('OPERATIONAL', 0)
        st.metric("🟢 Admin", admin)

        # Executive summary text
        if result.get('executive_summary'):
            st.markdown("---")
            st.caption(result['executive_summary'][:200] + "..." if len(result.get('executive_summary', '')) > 200 else result.get('executive_summary', ''))
    else:
        st.info("Run comparison to see summary")


def z3_classification_legend():
    """Z3: Classification legend, alignment status"""
    section_header("Classification", "📋")

    st.markdown("**Impact Levels:**")
    st.markdown("🔴 **Critical** - Material risk changes")
    st.markdown("🟡 **Important** - Notable changes")
    st.markdown("🟢 **Admin** - Formatting/typos")

    if st.session_state.v1_id and st.session_state.v2_id:
        v1_contract = st.session_state.get('v1_contract', {})
        v2_contract = st.session_state.get('v2_contract', {})

        v1_type = v1_contract.get('contract_type', 'Unknown')
        v2_type = v2_contract.get('contract_type', 'Unknown')

        st.markdown("---")
        st.markdown("**Alignment:**")

        if v1_type == v2_type:
            st.success(f"✅ Same type: {v1_type}")
        else:
            st.warning(f"⚠️ Different: {v1_type} vs {v2_type}")


def z4_split_comparison():
    """Z4: V1 text (left) | V2 redlines (right) using split_panel"""
    section_header("Compare Two Versions", "📝")

    if st.session_state.comparison_result:
        result = st.session_state.comparison_result

        def show_v1():
            st.markdown("#### V1: Original")
            v1_contract = result.get('v1_contract', {})
            st.markdown(f"**{v1_contract.get('title', v1_contract.get('filename', 'Contract'))}**")

            # Show V1 risk summary
            v1_id = st.session_state.v1_id
            v1_assessment = fetch_risk_assessment(v1_id)
            if v1_assessment:
                v1_risks = count_risks(v1_assessment)
                st.caption(f"Risk: {v1_risks['overall_risk']} | Deal: {v1_risks['DEALBREAKER']} | Crit: {v1_risks['CRITICAL']}")
            else:
                st.caption("No risk assessment available")

            # Placeholder for V1 text content
            st.text_area("V1 Content", value="[Original contract text would appear here]", height=250, disabled=True, key="v1_text")

        def show_v2():
            st.markdown("#### V2: Revised")
            v2_contract = result.get('v2_contract', {})
            st.markdown(f"**{v2_contract.get('title', v2_contract.get('filename', 'Contract'))}**")

            # Show V2 risk summary with delta
            v2_id = st.session_state.v2_id
            v2_assessment = fetch_risk_assessment(v2_id)
            if v2_assessment:
                v2_risks = count_risks(v2_assessment)
                st.caption(f"Risk: {v2_risks['overall_risk']} | Deal: {v2_risks['DEALBREAKER']} | Crit: {v2_risks['CRITICAL']}")
            else:
                st.caption("No risk assessment available")

            # Placeholder for V2 redline content
            st.text_area("V2 Content (with redlines)", value="[Revised contract with tracked changes would appear here]", height=250, disabled=True, key="v2_text")

        split_panel(show_v1, show_v2, ratio=(1, 1))
    else:
        st.info("Select contracts and run comparison to see side-by-side view")


def z5_business_impact():
    """Z5: Business impact narrative for selected section"""
    section_header("Business Impact", "💼")

    if st.session_state.comparison_result:
        result = st.session_state.comparison_result

        # Risk comparison
        v1_assessment = fetch_risk_assessment(st.session_state.v1_id)
        v2_assessment = fetch_risk_assessment(st.session_state.v2_id)

        if v1_assessment and v2_assessment:
            v1_risks = count_risks(v1_assessment)
            v2_risks = count_risks(v2_assessment)

            total_high_v1 = v1_risks['DEALBREAKER'] + v1_risks['CRITICAL']
            total_high_v2 = v2_risks['DEALBREAKER'] + v2_risks['CRITICAL']
            delta_high = total_high_v2 - total_high_v1

            if delta_high < 0:
                st.success(f"📈 **Improved**: V2 has {abs(delta_high)} fewer high-severity issues")
            elif delta_high > 0:
                st.error(f"📉 **Regression**: V2 has {delta_high} more high-severity issues")
            else:
                st.info("➡️ **No change** in high-severity issues")

        # Section-specific impact
        if st.session_state.selected_section:
            st.markdown(f"**Selected: {st.session_state.selected_section}**")
            st.markdown("Impact narrative for this section would appear here based on the comparison analysis.")
        else:
            st.caption("Select a section from the navigator to see specific impact")
    else:
        st.info("Run comparison for impact analysis")


def z6_section_navigator():
    """Z6: Section navigator, jump-to controls"""
    section_header("Navigate Sections", "🔍")

    if st.session_state.comparison_result:
        result = st.session_state.comparison_result

        # Create section list from comparison
        sections = [
            "Executive Summary",
            "Definitions",
            "Scope of Services",
            "Payment Terms",
            "Liability",
            "Indemnification",
            "Termination",
            "Confidentiality"
        ]

        selected = st.radio(
            "Jump to section",
            sections,
            key="section_nav_z6",
            horizontal=False
        )

        if selected != st.session_state.selected_section:
            st.session_state.selected_section = selected

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 DOCX", use_container_width=True, key="export_docx_z6"):
                toast_info("Downloading DOCX report...")
        with col2:
            if st.button("📋 JSON", use_container_width=True, key="export_json_z6"):
                json_str = json.dumps(result, indent=2)
                st.download_button(
                    "Download",
                    data=json_str,
                    file_name=f"comparison_{st.session_state.v1_id}_vs_{st.session_state.v2_id}.json",
                    mime="application/json",
                    key="json_download_z6"
                )
    else:
        st.info("Run comparison to navigate sections")


def z7_extra():
    """Z7: Additional controls"""
    pass


# Render zone layout
zone_layout(
    z1=z1_contract_selection,
    z2=z2_executive_summary,
    z3=z3_classification_legend,
    z4=z4_split_comparison,
    z5=z5_business_impact,
    z6=z6_section_navigator,
    z7=z7_extra,
    z7_system_status=True,
    api_healthy=api_healthy,
    db_healthy=db_healthy,
    ai_healthy=ai_healthy
)

# Run comparison if triggered
if st.session_state.comparing:
    v1_id = st.session_state.v1_id
    v2_id = st.session_state.v2_id

    if v1_id and v2_id:
        result, error = api_call_with_spinner(
            endpoint="/api/compare",
            method="POST",
            data={
                'v1_contract_id': v1_id,
                'v2_contract_id': v2_id,
                'include_recommendations': True
            },
            spinner_message="Comparing two versions... This may take 5-8 minutes...",
            success_message="Comparison complete!",
            timeout=600
        )

        if error:
            st.error(f"Comparison failed: {error}")
        else:
            st.session_state.comparison_result = result

        st.session_state.comparing = False
        if result:
            st.rerun()
    else:
        st.error("Please select both contracts")
        st.session_state.comparing = False

