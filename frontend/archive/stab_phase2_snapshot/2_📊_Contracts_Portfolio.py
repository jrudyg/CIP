# Your Contracts - Main Dashboard
# Contract Intelligence Platform
# v2.0: Zone layout retrofit

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import sys
import os

# MUST BE FIRST
st.set_page_config(
    page_title="Your Contracts",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dataframe width fix
st.markdown(
    """
    <style>
    /* Hard-limit the dataframe component to its parent width */
    [data-testid="stDataFrame"] {
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Make the internal grid respect that width */
    [data-testid="stDataFrame"] > div {
        width: 100% !important;
        max-width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from theme_system import apply_theme, inject_cip_logo
from zone_layout import zone_layout, check_system_health
from ui_components import page_header, section_header, apply_spacing
from components.contract_context import (
    init_contract_context, set_active_contract, clear_active_contract,
    render_active_contract_header, get_active_contract,
    render_recent_contracts_widget
)
from components.contract_detail import render_contract_detail

API_BASE = "http://localhost:5000/api"

# Initialize
apply_theme()
apply_spacing()
init_contract_context()

# Inject centralized dark theme
from components.theme import inject_dark_theme
inject_dark_theme()

# Check system health
api_ok, db_ok, ai_ok = check_system_health()

# Sidebar - navigation only
with st.sidebar:
    inject_cip_logo()

# Session state for filters and KPI selection
if 'filters' not in st.session_state:
    st.session_state.filters = {}
if 'active_kpi' not in st.session_state:
    st.session_state.active_kpi = None
if 'show_archived' not in st.session_state:
    st.session_state.show_archived = False

# Fetch filter options
@st.cache_data(ttl=300)
def get_filter_options():
    try:
        resp = requests.get(f"{API_BASE}/portfolio/filters", timeout=5)
        return resp.json() if resp.ok else {'types': [], 'statuses': [], 'risk_levels': [], 'counterparties': []}
    except:
        return {'types': [], 'statuses': [], 'risk_levels': [], 'counterparties': []}

# Fetch KPIs
def get_kpis(filters):
    try:
        resp = requests.post(f"{API_BASE}/portfolio/kpis", json=filters, timeout=5)
        return resp.json() if resp.ok else {'total_value': 0, 'active_count': 0, 'expiring_90d': 0, 'high_risk': 0}
    except:
        return {'total_value': 0, 'active_count': 0, 'expiring_90d': 0, 'high_risk': 0}

# Fetch contracts
def get_contracts(filters, include_archived=False):
    try:
        payload = filters.copy()
        payload['include_archived'] = include_archived
        resp = requests.post(f"{API_BASE}/portfolio/contracts", json=payload, timeout=10)
        return resp.json() if resp.ok else []
    except:
        return []

# Archive/Restore contract
def archive_contract(contract_id):
    try:
        resp = requests.post(f"{API_BASE}/contracts/{contract_id}/archive", timeout=5)
        return resp.json() if resp.ok else None
    except:
        return None

def restore_contract(contract_id):
    try:
        resp = requests.post(f"{API_BASE}/contracts/{contract_id}/restore", timeout=5)
        return resp.json() if resp.ok else None
    except:
        return None

def delete_contract(contract_id):
    try:
        resp = requests.post(f"{API_BASE}/contracts/{contract_id}/delete", timeout=5)
        return resp.json() if resp.ok else None
    except:
        return None

def delete_contracts_batch(contract_ids):
    try:
        resp = requests.post(f"{API_BASE}/contracts/delete-batch", json={'contract_ids': contract_ids}, timeout=10)
        return resp.json() if resp.ok else None
    except:
        return None


# --- Zone Content Functions ---

def z1_header_and_filters():
    """Z1: Page header and filter controls"""
    page_header("📊 Your Contracts", "Contract Portfolio Dashboard")
    render_active_contract_header()

    with st.expander("🔍 Filters & Options", expanded=False):
        options = get_filter_options()

        type_options = ["All"] + options.get('types', [])
        status_options = ["All"] + options.get('statuses', [])
        risk_options = ["All"] + options.get('risk_levels', [])

        if 'type_select' not in st.session_state:
            st.session_state.type_select = "All"
        if 'status_select' not in st.session_state:
            st.session_state.status_select = "All"
        if 'risk_select' not in st.session_state:
            st.session_state.risk_select = "All"

        col1, col2, col3 = st.columns(3)

        with col1:
            st.selectbox("Contract Type", type_options, key="type_select")
        with col2:
            st.selectbox("Status", status_options, key="status_select")
        with col3:
            st.selectbox("Risk Level", risk_options, key="risk_select")

        col_a, col_b = st.columns([3, 1])
        with col_a:
            show_archived = st.checkbox(
                "📦 Show Archived Contracts",
                value=st.session_state.show_archived,
                key="show_archived_checkbox",
                help="Include archived contracts in the list"
            )
            st.session_state.show_archived = show_archived
        with col_b:
            if st.button("🔄 Clear Filters", use_container_width=True):
                st.session_state.active_kpi = None
                st.session_state.show_archived = False
                st.session_state.type_select = "All"
                st.session_state.status_select = "All"
                st.session_state.risk_select = "All"
                st.rerun()


def z2_kpi_summary():
    """Z2: KPI summary - Active, High Risk, Expiring"""
    section_header("Quick Stats", "📊")
    filters = _build_filters()
    kpis = get_kpis(filters)

    if st.button(
        f"📄 {kpis.get('active_count', 0)} Active",
        use_container_width=True,
        type="primary" if st.session_state.active_kpi == 'active' else "secondary"
    ):
        st.session_state.active_kpi = 'active' if st.session_state.active_kpi != 'active' else None
        st.rerun()

    if st.button(
        f"⚠️ {kpis.get('high_risk', 0)} High Risk",
        use_container_width=True,
        type="primary" if st.session_state.active_kpi == 'risk' else "secondary"
    ):
        st.session_state.active_kpi = 'risk' if st.session_state.active_kpi != 'risk' else None
        st.rerun()

    if st.button(
        f"⏰ {kpis.get('expiring_90d', 0)} Expiring 90d",
        use_container_width=True,
        type="primary" if st.session_state.active_kpi == 'expiring' else "secondary"
    ):
        st.session_state.active_kpi = 'expiring' if st.session_state.active_kpi != 'expiring' else None
        st.rerun()


def z4_contract_list():
    """Z4: Main contract list table with multi-select and delete"""
    filters = _build_filters()
    display_filters = _apply_kpi_filter(filters)
    kpi_label = _get_kpi_label()

    archive_label = " (including archived)" if st.session_state.show_archived else ""
    section_header(f"{kpi_label}{archive_label}", "📋")

    contracts = get_contracts(display_filters, include_archived=st.session_state.show_archived)

    if contracts:
        df = pd.DataFrame(contracts)

        display_cols = ['id', 'title', 'counterparty', 'contract_type', 'contract_stage', 'contract_category', 'status', 'risk_level']
        available_cols = [c for c in display_cols if c in df.columns]

        display_df = df[available_cols].copy()

        if 'contract_value' in display_df.columns:
            display_df['contract_value'] = display_df['contract_value'].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "N/A"
            )

        if 'contract_stage' in display_df.columns:
            stage_icons = {'MNDA': '📝', 'NDA': '🔒', 'COMMERCIAL': '💼', 'EXECUTED': '✅'}
            display_df['contract_stage'] = display_df['contract_stage'].apply(
                lambda x: f"{stage_icons.get(x, '📄')} {x}" if pd.notna(x) else "N/A"
            )

        if 'contract_category' in display_df.columns:
            category_labels = {'A': '🅰️ Final', 'B': '🅱️ Interim', 'C': '🇨 Compare', 'D': '🇩 Dual'}
            display_df['contract_category'] = display_df['contract_category'].apply(
                lambda x: category_labels.get(x, x) if pd.notna(x) else "N/A"
            )

        if 'risk_level' in display_df.columns:
            risk_icons = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
            display_df['risk_level'] = display_df['risk_level'].apply(
                lambda x: f"{risk_icons.get(x, '⚪')} {x}" if pd.notna(x) else "N/A"
            )

        # Show archived status in status column
        if 'status' in display_df.columns and 'archived' in df.columns:
            display_df['status'] = df.apply(
                lambda row: "📦 Archived" if row.get('archived') == 1 else row.get('status', 'N/A'),
                axis=1
            )

        st.markdown("**Select rows (Ctrl+click for multiple):**")

        selection = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )

        selected_rows = selection.selection.rows if selection.selection else []

        if selected_rows:
            # Get selected contract info
            selected_ids = [int(df.iloc[idx]['id']) for idx in selected_rows]
            selected_count = len(selected_ids)

            if selected_count == 1:
                # Single selection - show full controls
                selected_idx = selected_rows[0]
                selected_id = selected_ids[0]
                selected_title = df.iloc[selected_idx].get('title', df.iloc[selected_idx].get('filename', 'Unknown'))
                is_archived = df.iloc[selected_idx].get('archived', 0) == 1

                st.info(f"📋 Selected: **#{selected_id} - {selected_title}**" + (" (Archived)" if is_archived else ""))

                col1, col2, col3 = st.columns(3)

                with col1:
                    if not is_archived:
                        if st.button("🎯 Set Active", type="primary", use_container_width=True):
                            set_active_contract(selected_id)
                            st.success(f"Contract #{selected_id} is now active")
                            st.rerun()

                with col2:
                    if is_archived:
                        if st.button("♻️ Restore", type="primary", use_container_width=True):
                            result = restore_contract(selected_id)
                            if result and result.get('status') == 'success':
                                st.success(f"Contract restored successfully")
                                st.rerun()
                            else:
                                st.error("Failed to restore contract")
                    else:
                        if st.button("📦 Archive", use_container_width=True):
                            st.session_state.confirm_archive = selected_id

                with col3:
                    if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                        st.session_state.confirm_delete = selected_ids

                # Archive confirmation
                if st.session_state.get('confirm_archive') == selected_id:
                    st.warning(f"⚠️ Are you sure you want to archive **{selected_title}**?")
                    conf_col1, conf_col2 = st.columns(2)
                    with conf_col1:
                        if st.button("✅ Yes, Archive", type="primary", use_container_width=True):
                            result = archive_contract(selected_id)
                            if result and result.get('status') == 'success':
                                st.success("Contract archived successfully")
                                st.session_state.confirm_archive = None
                                if get_active_contract() == selected_id:
                                    clear_active_contract()
                                st.rerun()
                            else:
                                st.error("Failed to archive contract")
                    with conf_col2:
                        if st.button("❌ Cancel", use_container_width=True, key="cancel_archive"):
                            st.session_state.confirm_archive = None
                            st.rerun()

            else:
                # Multiple selection - show batch actions
                st.info(f"📋 Selected **{selected_count} contracts**: {', '.join([f'#{id}' for id in selected_ids])}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🗑️ Delete {selected_count} Contracts", use_container_width=True, type="secondary"):
                        st.session_state.confirm_delete = selected_ids
                with col2:
                    pass

            # Delete confirmation (single or batch)
            if st.session_state.get('confirm_delete'):
                ids_to_delete = st.session_state.confirm_delete
                count = len(ids_to_delete)
                st.error(f"⚠️ **PERMANENT DELETE** - This will permanently delete {count} contract(s). This cannot be undone!")
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    if st.button(f"🗑️ Yes, Delete Permanently", type="primary", use_container_width=True):
                        if count == 1:
                            result = delete_contract(ids_to_delete[0])
                            if result and result.get('status') == 'success':
                                st.success("Contract deleted permanently")
                                if get_active_contract() in ids_to_delete:
                                    clear_active_contract()
                            else:
                                st.error("Failed to delete contract")
                        else:
                            result = delete_contracts_batch(ids_to_delete)
                            if result and result.get('status') == 'success':
                                st.success(f"Deleted {result.get('deleted_count', count)} contracts permanently")
                                if get_active_contract() in ids_to_delete:
                                    clear_active_contract()
                            else:
                                st.error("Failed to delete contracts")
                        st.session_state.confirm_delete = None
                        st.rerun()
                with conf_col2:
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_delete"):
                        st.session_state.confirm_delete = None
                        st.rerun()
        else:
            st.caption("👆 Click rows above to select (Ctrl+click for multiple)")
    else:
        st.info("No contracts match current filters")

    if st.session_state.active_kpi:
        if st.button("🔄 Clear Filter", help="Clear KPI filter", use_container_width=True):
            st.session_state.active_kpi = None
            st.rerun()


def z5_contract_detail():
    """Z5: Contract detail panel"""
    section_header("Contract Details", "📄")
    active_id = get_active_contract()
    if active_id:
        render_contract_detail(active_id)
    else:
        st.info("Select a contract to view details")


def z6_actions():
    """Z6: Quick actions"""
    section_header("Actions", "⚡")
    if st.button("➕ Add Contract", use_container_width=True):
        st.switch_page("pages/3_🧠_Intelligent_Intake.py")
    if st.button("🔍 Risk Analysis", use_container_width=True):
        st.switch_page("pages/4_🔍_Risk_Analysis.py")
    if st.button("📑 Reports", use_container_width=True):
        st.switch_page("pages/8_📑_Reports.py")


def z7_footer():
    """Z7: Footer with timestamp"""
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# --- Helper Functions ---

def _build_filters():
    """Build filter dictionary from session state"""
    filters = {}
    if st.session_state.get('type_select', 'All') != "All":
        filters['type'] = st.session_state.type_select
    if st.session_state.get('status_select', 'All') != "All":
        filters['status'] = st.session_state.status_select
    if st.session_state.get('risk_select', 'All') != "All":
        filters['risk'] = st.session_state.risk_select
    return filters


def _apply_kpi_filter(filters):
    """Apply KPI-based filter modifications"""
    display_filters = filters.copy()
    if st.session_state.active_kpi == 'active':
        display_filters['status'] = 'active'
    elif st.session_state.active_kpi == 'risk':
        display_filters['risk_high'] = True
    elif st.session_state.active_kpi == 'expiring':
        display_filters['expiring_days'] = 90
    return display_filters


def _get_kpi_label():
    """Get label based on active KPI"""
    if st.session_state.active_kpi == 'active':
        return "Active Contracts"
    elif st.session_state.active_kpi == 'risk':
        return "High Risk Contracts"
    elif st.session_state.active_kpi == 'expiring':
        return "Contracts Expiring in 90 Days"
    return "All Contracts"


# --- Render Zone Layout ---
zone_layout(
    z1=z1_header_and_filters,
    z2=z2_kpi_summary,
    z3=z6_actions,
    z4=z4_contract_list,
    z5=z5_contract_detail,
    z6=None,
    z7=z7_footer,
    z7_system_status=True,
    api_healthy=api_ok,
    db_healthy=db_ok,
    ai_healthy=ai_ok
)
