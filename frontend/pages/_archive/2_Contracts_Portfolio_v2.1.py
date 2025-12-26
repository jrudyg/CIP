# pages/2_Contracts_Portfolio.py
"""
CIP Contracts Portfolio v2.1
- Fixed HTML rendering issue using native Streamlit
- 2-column layout (Summary + List)
- 3 view modes: List, Compact, Table
- Filters: Status, Type, Party
- Search with keyboard shortcut (/)
"""

import streamlit as st
import requests
from typing import Dict, List, Optional
from datetime import datetime

from components.page_wrapper import (
    init_page,
    page_header,
    content_container
)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:5000/api"

STATUS_CONFIG = {
    "active": {"icon": "🟢", "color": "#22C55E", "label": "Active"},
    "intake": {"icon": "🟡", "color": "#EAB308", "label": "Intake"},
    "negotiating": {"icon": "🟠", "color": "#F97316", "label": "Negotiating"},
    "review": {"icon": "🔵", "color": "#3B82F6", "label": "Review"},
    "expired": {"icon": "⚫", "color": "#6B7280", "label": "Expired"},
    "archived": {"icon": "📁", "color": "#64748B", "label": "Archived"},
}

RISK_CONFIG = {
    "CRITICAL": {"icon": "🔴", "color": "#EF4444", "bg": "rgba(239,68,68,0.15)"},
    "HIGH": {"icon": "🟠", "color": "#F97316", "bg": "rgba(249,115,22,0.15)"},
    "MEDIUM": {"icon": "🟡", "color": "#EAB308", "bg": "rgba(234,179,8,0.15)"},
    "LOW": {"icon": "🟢", "color": "#22C55E", "bg": "rgba(34,197,94,0.15)"},
}

# ============================================================================
# SESSION STATE
# ============================================================================

def init_portfolio_state():
    defaults = {
        "pf_filter_status": "All",
        "pf_filter_type": "All",
        "pf_filter_party": "All",
        "pf_search": "",
        "pf_view_mode": "list",
        "pf_show_all": False,
        "pf_selected_contract": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================================
# API CALLS
# ============================================================================

@st.cache_data(ttl=30)
def api_get_contracts() -> List[Dict]:
    try:
        response = requests.get(f"{API_BASE}/contracts", timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        contracts = data if isinstance(data, list) else data.get("contracts", data.get("data", []))
        return [c for c in contracts if c and isinstance(c, dict)]
    except Exception:
        return []

# ============================================================================
# FILTERING & SEARCH
# ============================================================================

def get_filter_options(contracts: List[Dict]) -> Dict:
    """Extract unique filter options from contracts."""
    statuses = set()
    types = set()
    parties = set()
    
    for c in contracts:
        if c.get("status"):
            statuses.add(c["status"])
        if c.get("contract_type"):
            types.add(c["contract_type"])
        if c.get("position"):
            parties.add(c["position"])
    
    return {
        "statuses": ["All"] + sorted(list(statuses)),
        "types": ["All"] + sorted(list(types)),
        "parties": ["All"] + sorted(list(parties)) if parties else ["All", "Customer", "Vendor"],
    }

def filter_contracts(contracts: List[Dict]) -> List[Dict]:
    """Apply filters and search to contracts."""
    filtered = contracts
    
    status = st.session_state.get("pf_filter_status", "All")
    if status != "All":
        filtered = [c for c in filtered if c.get("status", "").lower() == status.lower()]
    
    ctype = st.session_state.get("pf_filter_type", "All")
    if ctype != "All":
        filtered = [c for c in filtered if c.get("contract_type") == ctype]
    
    party = st.session_state.get("pf_filter_party", "All")
    if party != "All":
        filtered = [c for c in filtered if c.get("position", "").lower() == party.lower()]
    
    search = st.session_state.get("pf_search", "").strip().lower()
    if search:
        filtered = [
            c for c in filtered
            if search in str(c.get("title", "")).lower()
            or search in str(c.get("counterparty", "")).lower()
            or search in str(c.get("contract_type", "")).lower()
        ]
    
    filtered.sort(key=lambda x: x.get("id", 0), reverse=True)
    return filtered

# ============================================================================
# SUMMARY STATS
# ============================================================================

def calculate_summary(contracts: List[Dict]) -> Dict:
    """Calculate summary statistics."""
    summary = {
        "total": len(contracts),
        "active": 0,
        "intake": 0,
        "negotiating": 0,
        "review": 0,
        "expired": 0,
        "archived": 0,
    }
    
    for c in contracts:
        status = str(c.get("status", "")).lower()
        if status in summary:
            summary[status] += 1
    
    return summary

def render_summary(contracts: List[Dict]):
    """Render summary stats panel using native Streamlit."""
    summary = calculate_summary(contracts)
    
    st.markdown("**Summary**")
    
    # Total
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("📄 Total")
    with col2:
        st.write(f"**{summary['total']}**")
    
    # By status
    for status, cfg in STATUS_CONFIG.items():
        count = summary.get(status, 0)
        if count > 0 or status in ["active", "intake"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"{cfg['icon']} {cfg['label']}")
            with col2:
                st.write(f"**{count}**")

# ============================================================================
# FILTER CONTROLS
# ============================================================================

def render_filters(filter_options: Dict):
    """Render filter dropdowns and search."""
    st.markdown("---")
    st.markdown("**Filters**")
    
    st.selectbox(
        "Status",
        filter_options["statuses"],
        key="pf_filter_status",
        label_visibility="collapsed"
    )
    
    st.selectbox(
        "Type", 
        filter_options["types"],
        key="pf_filter_type",
        label_visibility="collapsed"
    )
    
    st.selectbox(
        "Party",
        filter_options["parties"],
        key="pf_filter_party",
        label_visibility="collapsed"
    )
    
    st.text_input(
        "Search",
        placeholder="🔍 Search... (press /)",
        key="pf_search",
        label_visibility="collapsed"
    )

# ============================================================================
# VIEW CONTROLS
# ============================================================================

def render_view_toggle():
    """Render view mode toggle."""
    col1, col2, col3 = st.columns(3)
    
    current = st.session_state.get("pf_view_mode", "list")
    
    with col1:
        if st.button("☰ List", key="v_list", type="primary" if current == "list" else "secondary", use_container_width=True):
            st.session_state["pf_view_mode"] = "list"
            st.rerun()
    with col2:
        if st.button("▤ Compact", key="v_compact", type="primary" if current == "compact" else "secondary", use_container_width=True):
            st.session_state["pf_view_mode"] = "compact"
            st.rerun()
    with col3:
        if st.button("▦ Table", key="v_table", type="primary" if current == "table" else "secondary", use_container_width=True):
            st.session_state["pf_view_mode"] = "table"
            st.rerun()

# ============================================================================
# CONTRACT CARDS - LIST VIEW (NATIVE STREAMLIT)
# ============================================================================

def render_contract_card_list(contract: Dict):
    """Render full contract card for list view using native Streamlit."""
    c = contract
    status = str(c.get("status", "active")).lower()
    status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["active"])
    
    risk = str(c.get("risk_level", "")).upper()
    risk_cfg = RISK_CONFIG.get(risk, None)
    
    title = (c.get("title") or "Untitled")[:40]
    counterparty = (c.get("counterparty") or "Unknown")[:25]
    ctype = c.get("contract_type", "")
    position = c.get("position", "")
    contract_id = c.get("id")
    
    # Card container
    with st.container():
        # Header row
        col_icon, col_title, col_id = st.columns([0.5, 5, 1])
        with col_icon:
            st.write(status_cfg['icon'])
        with col_title:
            risk_text = f" {risk_cfg['icon']} {risk}" if risk_cfg else ""
            st.markdown(f"**{title}**{risk_text}")
        with col_id:
            st.caption(f"#{contract_id}")
        
        # Details row
        details = f"{counterparty} · {ctype}"
        if position:
            details += f" · {position}"
        st.caption(details)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("View", key=f"view_{contract_id}", use_container_width=True):
                st.session_state["pf_selected_contract"] = contract_id
                st.switch_page("pages/7_Contract_Details.py")
        with col2:
            if st.button("Analyze", key=f"analyze_{contract_id}", use_container_width=True):
                st.session_state["risk_selected_contract"] = contract_id
                st.switch_page("pages/4_Risk_Analysis.py")
        with col3:
            if st.button("Compare", key=f"compare_{contract_id}", use_container_width=True):
                st.info("Compare coming soon")
        with col4:
            if status == "intake":
                if st.button("Delete", key=f"delete_{contract_id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{contract_id}"] = True
                    st.rerun()
            else:
                if st.button("Archive", key=f"archive_{contract_id}", use_container_width=True):
                    st.info("Archive coming soon")

        st.divider()

        # Delete confirmation dialog
        if st.session_state.get(f"confirm_delete_{contract_id}"):
            st.warning(f"Are you sure you want to delete contract #{contract_id}?")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("Yes, Delete", key=f"confirm_yes_{contract_id}", type="primary"):
                    response = requests.delete(f"{API_BASE}/contracts/{contract_id}/delete")
                    if response.ok:
                        st.success("Contract deleted")
                        del st.session_state[f"confirm_delete_{contract_id}"]
                        api_get_contracts.clear()  # Clear cache
                        st.rerun()
                    else:
                        st.error("Delete failed")
            with confirm_col2:
                if st.button("Cancel", key=f"confirm_no_{contract_id}"):
                    del st.session_state[f"confirm_delete_{contract_id}"]
                    st.rerun()

# ============================================================================
# CONTRACT CARDS - COMPACT VIEW
# ============================================================================

def render_contract_card_compact(contract: Dict):
    """Render compact contract row using native Streamlit."""
    c = contract
    status = str(c.get("status", "active")).lower()
    status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["active"])
    
    risk = str(c.get("risk_level", "")).upper()
    risk_cfg = RISK_CONFIG.get(risk, None)
    
    title = (c.get("title") or "Untitled")[:35]
    counterparty = (c.get("counterparty") or "Unknown")[:20]
    contract_id = c.get("id")
    
    risk_icon = f" {risk_cfg['icon']}" if risk_cfg else ""
    
    col1, col2, col3 = st.columns([0.5, 4, 0.5])
    
    with col1:
        st.write(status_cfg['icon'])
    with col2:
        st.write(f"**{title}** · {counterparty}{risk_icon}")
    with col3:
        if st.button("→", key=f"go_{contract_id}", help="View details"):
            st.session_state["pf_selected_contract"] = contract_id
            st.switch_page("pages/7_Contract_Details.py")

# ============================================================================
# CONTRACT TABLE VIEW
# ============================================================================

def render_contract_table(contracts: List[Dict]):
    """Render contracts as sortable table."""
    if not contracts:
        return
    
    import pandas as pd
    
    rows = []
    for c in contracts:
        status = str(c.get("status", "")).lower()
        status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["active"])
        risk = str(c.get("risk_level", "")).upper() or "-"
        
        rows.append({
            "ID": c.get("id"),
            "Status": f"{status_cfg['icon']} {status_cfg['label']}",
            "Title": (c.get("title") or "Untitled")[:30],
            "Counterparty": (c.get("counterparty") or "")[:20],
            "Type": c.get("contract_type", ""),
            "Risk": risk,
        })
    
    df = pd.DataFrame(rows)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Counterparty": st.column_config.TextColumn("Counterparty", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Risk": st.column_config.TextColumn("Risk", width="small"),
        }
    )

# ============================================================================
# CONTRACTS PANEL
# ============================================================================

def render_contracts_panel(contracts: List[Dict], filtered: List[Dict]):
    """Render the main contracts panel."""
    total = len(contracts)
    showing = len(filtered)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if showing == total:
            st.markdown(f"**Contracts** ({total})")
        else:
            st.markdown(f"**Contracts** ({showing} of {total})")
    with col2:
        if st.button("+ Upload", key="upload_btn", type="primary"):
            st.switch_page("pages/3_Intelligent_Intake.py")
    
    render_view_toggle()
    
    # Empty state
    if not filtered:
        if total == 0:
            st.info("📄 No contracts yet. Upload your first contract to get started.")
        else:
            st.info("No contracts match your filters")
        return
    
    view_mode = st.session_state.get("pf_view_mode", "list")
    
    if view_mode == "table":
        render_contract_table(filtered)
    else:
        show_all = st.session_state.get("pf_show_all", False)
        visible_count = 20 if show_all else 7
        visible = filtered[:visible_count]
        
        for c in visible:
            if view_mode == "compact":
                render_contract_card_compact(c)
            else:
                render_contract_card_list(c)
        
        remaining = len(filtered) - len(visible)
        if remaining > 0:
            st.caption(f"+ {remaining} more contracts")
            if st.button("Load More", key="load_more", use_container_width=True):
                st.session_state["pf_show_all"] = True
                st.rerun()
        
        if show_all and len(filtered) > 7:
            if st.button("Show Less", key="show_less", use_container_width=True):
                st.session_state["pf_show_all"] = False
                st.rerun()

# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Contracts Portfolio", "📊", max_width=1400)

page_header(
    "Contracts Portfolio",
    subtitle="Manage and monitor your contract portfolio",
    show_status=True,
    show_version=True
)

init_portfolio_state()

with content_container():
    contracts = api_get_contracts()
    filter_options = get_filter_options(contracts)
    filtered = filter_contracts(contracts)
    
    col_left, col_right = st.columns([1, 2.5])
    
    with col_left:
        render_summary(contracts)
        render_filters(filter_options)
        
        st.markdown("---")
        if st.button("+ New Contract", key="new_btn", use_container_width=True, type="secondary"):
            st.switch_page("pages/3_Intelligent_Intake.py")
    
    with col_right:
        render_contracts_panel(contracts, filtered)
