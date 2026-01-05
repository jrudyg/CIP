# pages/2_Contracts_Portfolio.py
"""
CIP Contracts Portfolio v4.0 - CCE-Plus Integration
- Compact view with checkboxes
- Multi-select with floating action bar (always visible): Delete (1+), View (1), Analyze (1), Compare (2), Link (2)
- Filters: Role, Contract Type, Other Party
- CCE-Plus: Workflow gate status display (Intake → Risk → Redline → Compare)
"""

import streamlit as st
import requests
from typing import Dict, List
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from components.page_wrapper import (
    init_page,
    page_header,
    content_container
)

# Import workflow gates
try:
    from workflow_gates import WorkflowGate
    WORKFLOW_GATES_AVAILABLE = True
except ImportError:
    WORKFLOW_GATES_AVAILABLE = False

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

# CCE-Plus Workflow Status Icons
WORKFLOW_STATUS_ICONS = {
    "COMPLETE": "✅",
    "APPROVED": "✅",
    "IN_PROGRESS": "⏳",
    "PENDING": "🔓",
    "BLOCKED": "🔒",
    "REJECTED": "❌",
}

# ============================================================================
# WORKFLOW GATE HELPER
# ============================================================================

def get_workflow_status_for_contract(contract_id: int) -> Dict:
    """
    Get workflow status for a contract from workflow gates.

    Returns:
        {
            'intake': 'COMPLETE',
            'risk': 'PENDING',
            'redline': 'BLOCKED',
            'compare': 'BLOCKED'
        }
    """
    if not WORKFLOW_GATES_AVAILABLE:
        return {
            'intake': 'PENDING',
            'risk': 'BLOCKED',
            'redline': 'BLOCKED',
            'compare': 'BLOCKED'
        }

    try:
        db_path = str(backend_path.parent / "data" / "contracts.db")
        gate = WorkflowGate(db_path)
        status = gate.get_workflow_status(contract_id)

        return {
            'intake': status.get('intake', 'PENDING'),
            'risk': status.get('risk', 'BLOCKED'),
            'redline': status.get('redline', 'BLOCKED'),
            'compare': status.get('compare', 'BLOCKED')
        }
    except Exception:
        return {
            'intake': 'PENDING',
            'risk': 'BLOCKED',
            'redline': 'BLOCKED',
            'compare': 'BLOCKED'
        }

def format_workflow_badges(workflow_status: Dict) -> str:
    """
    Format workflow status as compact badge string.

    Returns:
        "✅ 🔓 🔒 🔒" (Intake complete, Risk pending, Redline/Compare blocked)
    """
    intake_icon = WORKFLOW_STATUS_ICONS.get(workflow_status.get('intake', 'BLOCKED'), '🔒')
    risk_icon = WORKFLOW_STATUS_ICONS.get(workflow_status.get('risk', 'BLOCKED'), '🔒')
    redline_icon = WORKFLOW_STATUS_ICONS.get(workflow_status.get('redline', 'BLOCKED'), '🔒')
    compare_icon = WORKFLOW_STATUS_ICONS.get(workflow_status.get('compare', 'BLOCKED'), '🔒')

    return f"{intake_icon} {risk_icon} {redline_icon} {compare_icon}"

# ============================================================================
# SESSION STATE
# ============================================================================

def init_portfolio_state():
    defaults = {
        "pf_filter_status": "All",
        "pf_filter_risk": "All",
        "pf_filter_role": "All",
        "pf_filter_party": "All",
        "pf_filter_type": "All",
        "pf_show_status": False,
        "pf_show_risk": False,
        "pf_show_role": False,
        "pf_show_party": False,
        "pf_show_type": False,
        "pf_search": "",
        "pf_show_all": False,
        "pf_selected_ids": set(),
        "pf_selected_contract": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if not isinstance(st.session_state.get("pf_selected_ids"), set):
        st.session_state["pf_selected_ids"] = set()

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

def api_delete_contract(contract_id: int) -> bool:
    try:
        response = requests.delete(f"{API_BASE}/contracts/{contract_id}/delete", timeout=10)
        return response.ok
    except Exception:
        return False

# ============================================================================
# SELECTION HELPERS
# ============================================================================

def toggle_selection(contract_id: int):
    selected = st.session_state.get("pf_selected_ids", set())
    if not isinstance(selected, set):
        selected = set()
    if contract_id in selected:
        selected.discard(contract_id)
    else:
        selected.add(contract_id)
    st.session_state["pf_selected_ids"] = selected

def clear_selection():
    st.session_state["pf_selected_ids"] = set()

# ============================================================================
# FILTERING & SEARCH
# ============================================================================

def get_filter_options(contracts: List[Dict]) -> Dict:
    """Extract unique filter options from contracts."""
    statuses, risks, roles, parties, types = set(), set(), set(), set(), set()
    for c in contracts:
        if c.get("status"): statuses.add(c["status"])
        if c.get("risk_level"): risks.add(c["risk_level"].upper())
        if c.get("party_relationship"): roles.add(c["party_relationship"])
        if c.get("counterparty"): parties.add(c["counterparty"])
        if c.get("contract_type"): types.add(c["contract_type"])
    return {
        "statuses": ["All"] + sorted(list(statuses)),
        "risks": ["All"] + sorted(list(risks)),
        "roles": ["All"] + sorted(list(roles)) if roles else ["All", "Customer", "Vendor"],
        "parties": ["All"] + sorted(list(parties)),
        "types": ["All"] + sorted(list(types)),
    }

def filter_contracts(contracts: List[Dict]) -> List[Dict]:
    """Apply filters and search to contracts."""
    filtered = contracts

    role = st.session_state.get("pf_filter_role", "All")
    if role != "All":
        filtered = [c for c in filtered if str(c.get("party_relationship") or "").lower() == role.lower()]

    ctype = st.session_state.get("pf_filter_type", "All")
    if ctype != "All":
        filtered = [c for c in filtered if c.get("contract_type") == ctype]

    party = st.session_state.get("pf_filter_party", "All")
    if party != "All":
        filtered = [c for c in filtered if c.get("counterparty", "") == party]

    search = st.session_state.get("pf_search", "").strip().lower()
    if search:
        filtered = [c for c in filtered if search in str(c.get("title", "")).lower() or search in str(c.get("counterparty", "")).lower() or search in str(c.get("contract_type", "")).lower()]

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

def render_filters(filter_options: Dict, contracts: List[Dict]):
    """Render 3 collapsible filters: Customer/Vendor, Contract Type, Other Party."""

    # Calculate counts
    role_counts = {}
    type_counts = {}

    for c in contracts:
        role = c.get("party_relationship", "")
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1

        ctype = c.get("contract_type", "")
        if ctype:
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

    st.markdown("---")
    st.markdown("**Filters**")

    # === 1. BY CUSTOMER OR VENDOR ===
    show_role = st.session_state.get("pf_show_role", False)
    toggle_label = "▼ By Customer or Vendor" if show_role else "▶ By Customer or Vendor"
    if st.button(toggle_label, key="toggle_role", use_container_width=True, type="secondary"):
        st.session_state["pf_show_role"] = not show_role
        st.rerun()

    if show_role:
        current = st.session_state.get("pf_filter_role", "All")
        cols = st.columns(3)

        # Customer button - blue
        cust_count = role_counts.get("Customer", 0)
        is_cust_active = current == "Customer"
        with cols[0]:
            if st.button(f"👤 {cust_count}", key="role_Customer",
                         type="primary" if is_cust_active else "secondary",
                         use_container_width=True, help="Customer"):
                st.session_state["pf_filter_role"] = "Customer" if not is_cust_active else "All"
                st.rerun()

        # Vendor button - orange
        vend_count = role_counts.get("Vendor", 0)
        is_vend_active = current == "Vendor"
        with cols[1]:
            if st.button(f"🏢 {vend_count}", key="role_Vendor",
                         type="primary" if is_vend_active else "secondary",
                         use_container_width=True, help="Vendor"):
                st.session_state["pf_filter_role"] = "Vendor" if not is_vend_active else "All"
                st.rerun()

        # All button
        is_all = current == "All"
        with cols[2]:
            if st.button("All", key="role_all",
                         type="primary" if is_all else "secondary",
                         use_container_width=True):
                st.session_state["pf_filter_role"] = "All"
                st.rerun()

    # === 2. BY CONTRACT TYPE ===
    show_type = st.session_state.get("pf_show_type", False)
    toggle_label = "▼ By Contract Type" if show_type else "▶ By Contract Type"
    if st.button(toggle_label, key="toggle_type", use_container_width=True, type="secondary"):
        st.session_state["pf_show_type"] = not show_type
        st.rerun()

    if show_type:
        current = st.session_state.get("pf_filter_type", "All")
        types = list(type_counts.keys())

        # 4 buttons per row
        all_items = types + ["All"]
        cols_per_row = 4
        rows_needed = (len(all_items) + cols_per_row - 1) // cols_per_row

        for row in range(rows_needed):
            cols = st.columns(cols_per_row)
            for col_idx in range(cols_per_row):
                item_idx = row * cols_per_row + col_idx
                if item_idx < len(all_items):
                    item = all_items[item_idx]
                    if item == "All":
                        is_active = current == "All"
                        with cols[col_idx]:
                            if st.button("All", key="type_all",
                                         type="primary" if is_active else "secondary",
                                         use_container_width=True):
                                st.session_state["pf_filter_type"] = "All"
                                st.rerun()
                    else:
                        count = type_counts.get(item, 0)
                        is_active = current == item
                        # Abbreviate long type names
                        abbr = item[:3].upper()
                        with cols[col_idx]:
                            if st.button(f"{count} {abbr}", key=f"type_{item}",
                                         type="primary" if is_active else "secondary",
                                         use_container_width=True, help=item):
                                st.session_state["pf_filter_type"] = item if not is_active else "All"
                                st.rerun()

    # === 3. BY OTHER PARTY - Direct dropdown, no toggle ===
    st.markdown("**By Other Party**")
    st.selectbox("Party", filter_options["parties"], key="pf_filter_party", label_visibility="collapsed")

    st.markdown("---")
    st.text_input("Search", placeholder="🔍 Search...", key="pf_search", label_visibility="collapsed")

# ============================================================================
# FLOATING ACTION BAR
# ============================================================================

def render_floating_action_bar(filtered: List[Dict]):
    """Render floating action bar - always visible, buttons enabled based on selection count."""
    selected_ids = st.session_state.get("pf_selected_ids", set())
    if not isinstance(selected_ids, set):
        selected_ids = set()
    count = len(selected_ids)
    st.markdown("---")
    col_info, col_clear = st.columns([3, 1])
    with col_info:
        st.markdown(f"**{count}** selected")
    with col_clear:
        if count > 0:
            if st.button("Clear", key="clear_selection"):
                clear_selection()
                st.rerun()
        else:
            st.button("Clear", key="clear_selection_disabled", disabled=True)

    # Action bar always visible - buttons enabled based on selection count
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if count >= 1:
            if st.button("🗑️ Delete", key="bulk_delete", use_container_width=True, type="primary"):
                st.session_state["confirm_bulk_delete"] = True
                st.rerun()
        else:
            st.button("🗑️ Delete", key="bulk_delete_disabled", use_container_width=True, disabled=True, help="Select 1+ contracts")

    with col2:
        if count == 1:
            if st.button("👁️ View", key="bulk_view", use_container_width=True):
                contract_id = list(selected_ids)[0]
                st.session_state["pf_selected_contract"] = contract_id
                clear_selection()
                st.switch_page("pages/9_Contract_Details.py")
        else:
            st.button("👁️ View", key="bulk_view_disabled", use_container_width=True, disabled=True, help="Select exactly 1 contract")

    with col3:
        if count == 1:
            if st.button("🔍 Analyze", key="bulk_analyze", use_container_width=True):
                contract_id = list(selected_ids)[0]
                st.session_state["risk_selected_contract"] = contract_id
                st.session_state["risk_scanning"] = True
                st.session_state["risk_scan_contract"] = contract_id
                clear_selection()
                st.switch_page("pages/4_Risk_Analysis.py")
        else:
            st.button("🔍 Analyze", key="bulk_analyze_disabled", use_container_width=True, disabled=True, help="Select exactly 1 contract")

    with col4:
        if count == 2:
            if st.button("⚖️ Compare", key="bulk_compare", use_container_width=True):
                ids = list(selected_ids)
                st.session_state["v1_id"] = ids[0]
                st.session_state["v2_id"] = ids[1]
                # Clear dropdown widget keys so they pick up new values
                st.session_state.pop("v1_selector_dropdown", None)
                st.session_state.pop("v2_selector_dropdown", None)
                clear_selection()
                st.switch_page("pages/6_Compare_Versions.py")
        else:
            st.button("⚖️ Compare", key="bulk_compare_disabled", use_container_width=True, disabled=True, help="Select exactly 2 contracts")

    with col5:
        if count == 2:
            if st.button("🔗 Link", key="bulk_link", use_container_width=True):
                st.info("Link feature coming soon")
        else:
            st.button("🔗 Link", key="bulk_link_disabled", use_container_width=True, disabled=True, help="Select exactly 2 contracts")
    if st.session_state.get("confirm_bulk_delete"):
        st.warning(f"Delete {count} contract{'s' if count != 1 else ''}?")
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("Yes, Delete All", key="confirm_bulk_yes", type="primary"):
                success_count = 0
                for cid in selected_ids:
                    if api_delete_contract(cid):
                        success_count += 1
                if success_count > 0:
                    st.success(f"Deleted {success_count} contract{'s' if success_count != 1 else ''}")
                    api_get_contracts.clear()
                    clear_selection()
                    del st.session_state["confirm_bulk_delete"]
                    st.rerun()
                else:
                    st.error("Delete failed")
        with conf_col2:
            if st.button("Cancel", key="confirm_bulk_no"):
                del st.session_state["confirm_bulk_delete"]
                st.rerun()

# ============================================================================
# CONTRACT ROWS - COMPACT VIEW WITH CHECKBOXES + WORKFLOW STATUS
# ============================================================================

def render_contract_row_compact(contract: Dict):
    """Render compact contract row with checkbox, info, workflow status, View and Delete."""
    c = contract
    contract_id = c.get("id")
    status = str(c.get("status", "active")).lower()
    status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["active"])
    risk = str(c.get("risk_level", "")).upper()
    risk_cfg = RISK_CONFIG.get(risk, None)
    title = (c.get("title") or "Untitled")[:35]
    counterparty = (c.get("counterparty") or "Unknown")[:20]
    selected_ids = st.session_state.get("pf_selected_ids", set())
    if not isinstance(selected_ids, set):
        selected_ids = set()
    is_selected = contract_id in selected_ids
    risk_icon = f" {risk_cfg['icon']}" if risk_cfg else ""

    # Get CCE-Plus workflow status
    workflow_status = get_workflow_status_for_contract(contract_id)
    workflow_badges = format_workflow_badges(workflow_status)

    col_check, col_status, col_info, col_workflow = st.columns([0.5, 0.5, 3, 1])

    with col_check:
        if st.checkbox("Select", value=is_selected, key=f"chk_{contract_id}", label_visibility="collapsed"):
            if not is_selected:
                toggle_selection(contract_id)
                st.rerun()
        else:
            if is_selected:
                toggle_selection(contract_id)
                st.rerun()
    with col_status:
        st.write(status_cfg['icon'])
    with col_info:
        st.write(f"**{title}** · {counterparty}{risk_icon}")
    with col_workflow:
        st.caption(workflow_badges)

    if st.session_state.get(f"confirm_delete_{contract_id}"):
        st.warning(f"Delete contract #{contract_id}?")
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("Yes", key=f"conf_yes_{contract_id}", type="primary"):
                if api_delete_contract(contract_id):
                    st.success("Deleted")
                    del st.session_state[f"confirm_delete_{contract_id}"]
                    api_get_contracts.clear()
                    st.rerun()
                else:
                    st.error("Failed")
        with conf_col2:
            if st.button("No", key=f"conf_no_{contract_id}"):
                del st.session_state[f"confirm_delete_{contract_id}"]
                st.rerun()

# ============================================================================
# CONTRACTS PANEL
# ============================================================================

def render_contracts_panel(contracts: List[Dict], filtered: List[Dict]):
    """Render the main contracts panel."""
    total = len(contracts)
    showing = len(filtered)
    if showing == total:
        st.markdown(f"**Contracts** ({total})")
    else:
        st.markdown(f"**Contracts** ({showing} of {total})")

    # Workflow legend
    st.caption("Workflow: ✅ Complete | 🔓 Pending | 🔒 Blocked | ⏳ In Progress")
    st.caption("Stages: Intake · Risk · Redline · Compare")

    render_floating_action_bar(filtered)
    if not filtered:
        if total == 0:
            st.info("📄 No contracts yet. Upload your first contract to get started.")
        else:
            st.info("No contracts match your filters")
        return
    show_all = st.session_state.get("pf_show_all", False)
    visible_count = 20 if show_all else 10
    visible = filtered[:visible_count]
    for c in visible:
        render_contract_row_compact(c)
    remaining = len(filtered) - len(visible)
    if remaining > 0:
        st.caption(f"+ {remaining} more contracts")
        if st.button("Load More", key="load_more", use_container_width=True):
            st.session_state["pf_show_all"] = True
            st.rerun()
    if show_all and len(filtered) > 10:
        if st.button("Show Less", key="show_less", use_container_width=True):
            st.session_state["pf_show_all"] = False
            st.rerun()

# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Contracts Portfolio", "📊", max_width=1400)

page_header(
    "Contracts Portfolio",
    subtitle="Manage and monitor your contract portfolio with CCE-Plus workflow tracking",
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
        render_filters(filter_options, contracts)

    with col_right:
        render_contracts_panel(contracts, filtered)
