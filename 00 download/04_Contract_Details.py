# pages/3_Contract_Details.py
"""
CIP Contract Details v2.0
- All 16 metadata fields displayed
- Always-editable fields (no Edit button)
- Dynamic Save/Cancel buttons (appear on change)
- "Not found" for missing AI extractions
- N/A handling for inapplicable fields
"""

import streamlit as st
import requests
import os
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

RISK_LEVEL_CONFIG = {
    "CRITICAL": {"icon": "🔴", "color": "#EF4444", "label": "Critical"},
    "HIGH": {"icon": "🔴", "color": "#EF4444", "label": "High"},
    "MEDIUM": {"icon": "🟠", "color": "#F97316", "label": "Medium"},
    "LOW": {"icon": "🟢", "color": "#22C55E", "label": "Low"},
}

CONTRACT_TYPES = [
    "MSA", "SOW", "NDA", "MNDA", "Amendment", "Addendum", 
    "Service Agreement", "License Agreement", "Other"
]

ROLE_OPTIONS = ["Customer", "Vendor", "Partner", "Licensor", "Licensee", "Not found"]

AUTO_RENEWAL_OPTIONS = [("Not found", None), ("Yes", True), ("No", False), ("N/A", "N/A")]

CATEGORY_LABELS = {
    "indemnification": {"abbr": "IND", "full": "Indemnification"},
    "liability": {"abbr": "LIA", "full": "Liability"},
    "ip": {"abbr": "IP", "full": "Intellectual Property"},
    "payment": {"abbr": "PAY", "full": "Payment"},
    "termination": {"abbr": "TRM", "full": "Termination"},
    "confidentiality": {"abbr": "CNF", "full": "Confidentiality"},
    "warranties": {"abbr": "WAR", "full": "Warranties"},
    "insurance": {"abbr": "INS", "full": "Insurance"},
    "compliance": {"abbr": "CMP", "full": "Compliance"},
    "operational": {"abbr": "OPS", "full": "Operational"},
    "closeout": {"abbr": "CLO", "full": "Closeout"},
}

# ============================================================================
# SESSION STATE
# ============================================================================

def init_details_state():
    defaults = {
        "details_contract_id": None,
        "details_contract_data": None,
        "details_error": None,
        "details_original_values": {},
        "details_has_changes": False,
        "details_save_success": False,
        "portfolio_scroll_position": 0,
        "portfolio_filters_snapshot": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_portfolio_state():
    st.session_state["portfolio_filters_snapshot"] = {
        "pf_filter_status": st.session_state.get("pf_filter_status", "All"),
        "pf_filter_type": st.session_state.get("pf_filter_type", "All"),
        "pf_filter_party": st.session_state.get("pf_filter_party", "All"),
        "pf_filter_role": st.session_state.get("pf_filter_role", "All"),
        "pf_filter_risk": st.session_state.get("pf_filter_risk", "All"),
        "pf_search": st.session_state.get("pf_search", ""),
        "pf_view_mode": st.session_state.get("pf_view_mode", "compact"),
        "pf_show_all": st.session_state.get("pf_show_all", False),
    }


def restore_portfolio_state():
    snapshot = st.session_state.get("portfolio_filters_snapshot", {})
    for key, value in snapshot.items():
        st.session_state[key] = value


def store_original_values(contract: Dict):
    """Store original values to detect changes."""
    # Get contract_value, handle None/string values
    cv = contract.get("contract_value")
    if cv in [None, "Not found", "N/A", ""]:
        cv = 0.0
    else:
        try:
            cv = float(cv)
        except (ValueError, TypeError):
            cv = 0.0
    
    # Get termination_notice_days, handle None/string values
    tn = contract.get("termination_notice_days")
    if tn in [None, "Not found", "N/A", ""]:
        tn = 0
    else:
        try:
            tn = int(tn)
        except (ValueError, TypeError):
            tn = 0
    
    st.session_state["details_original_values"] = {
        "title": contract.get("title") or contract.get("filename") or "Untitled Contract",
        "contract_type": contract.get("contract_type") or "Other",
        "effective_date": contract.get("effective_date"),
        "expiration_date": contract.get("expiration_date"),
        "our_entity": contract.get("our_entity") or "",
        "position": contract.get("position") or "Not found",
        "counterparty": contract.get("counterparty") or "",
        "counterparty_role": contract.get("counterparty_role") or "Not found",
        "contract_value": cv,
        "payment_terms": contract.get("payment_terms") or "",
        "liability_cap": contract.get("liability_cap") or "",
        "auto_renewal": contract.get("auto_renewal"),
        "termination_notice_days": tn,
        "governing_law": contract.get("governing_law") or "",
        "warranty_period": contract.get("warranty_period") or "",
    }


def check_for_changes() -> bool:
    """Check if any field has changed from original."""
    original = st.session_state.get("details_original_values", {})
    
    fields_to_check = [
        ("edit_title", "title"),
        ("edit_contract_type", "contract_type"),
        ("edit_our_entity", "our_entity"),
        ("edit_position", "position"),
        ("edit_counterparty", "counterparty"),
        ("edit_counterparty_role", "counterparty_role"),
        ("edit_payment_terms", "payment_terms"),
        ("edit_liability_cap", "liability_cap"),
        ("edit_governing_law", "governing_law"),
        ("edit_warranty_period", "warranty_period"),
    ]
    
    for session_key, orig_key in fields_to_check:
        if session_key in st.session_state:
            current = st.session_state[session_key]
            orig = original.get(orig_key, "")
            if current != orig:
                return True
    
    # Check dates
    if "edit_effective_date" in st.session_state:
        orig_date = parse_date_for_input(original.get("effective_date"))
        if st.session_state["edit_effective_date"] != orig_date:
            return True
    
    if "edit_expiration_date" in st.session_state:
        orig_date = parse_date_for_input(original.get("expiration_date"))
        if st.session_state["edit_expiration_date"] != orig_date:
            return True
    
    # Check numeric fields
    if "edit_contract_value" in st.session_state:
        orig_val = original.get("contract_value")
        # Handle string values like "Not found" or "N/A"
        if orig_val in [None, "Not found", "N/A", ""]:
            orig_val = 0.0
        else:
            try:
                orig_val = float(orig_val)
            except (ValueError, TypeError):
                orig_val = 0.0
        if st.session_state["edit_contract_value"] != orig_val:
            return True
    
    if "edit_termination_notice" in st.session_state:
        orig_val = original.get("termination_notice_days")
        # Handle string values like "Not found" or "N/A"
        if orig_val in [None, "Not found", "N/A", ""]:
            orig_val = 0
        else:
            try:
                orig_val = int(orig_val)
            except (ValueError, TypeError):
                orig_val = 0
        if st.session_state["edit_termination_notice"] != orig_val:
            return True
    
    # Check auto_renewal (compare display label to avoid type issues)
    if "edit_auto_renewal_display" in st.session_state:
        current_label = st.session_state["edit_auto_renewal_display"]
        orig_val = original.get("auto_renewal")
        # Map original value to label
        orig_label = "Not found"
        for label, val in AUTO_RENEWAL_OPTIONS:
            if val == orig_val:
                orig_label = label
                break
        if current_label != orig_label:
            return True
    
    return False


# ============================================================================
# API CALLS
# ============================================================================

def api_get_contract(contract_id: int) -> Optional[Dict]:
    """Fetch single contract with full details."""
    try:
        response = requests.get(f"{API_BASE}/contract/{contract_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            contract = data.get("contract", {})
            contract["clauses"] = data.get("clauses", [])
            contract["assessments"] = data.get("assessments", [])
            contract["statistics"] = data.get("statistics", {})
            return contract
        return None
    except Exception as e:
        st.session_state["details_error"] = str(e)
        return None


def api_update_contract(contract_id: int, updates: Dict) -> tuple[bool, str]:
    """Update contract metadata."""
    try:
        response = requests.put(
            f"{API_BASE}/contract/{contract_id}",
            json=updates,
            timeout=10
        )
        if response.status_code == 200:
            return True, "Contract updated successfully"
        else:
            error = response.json().get('error', 'Update failed')
            return False, error
    except Exception as e:
        return False, str(e)


def api_get_versions(contract_id: int, parent_id: Optional[int]) -> List[Dict]:
    """Fetch version history for contract family."""
    try:
        response = requests.get(f"{API_BASE}/contracts", timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        contracts = data if isinstance(data, list) else data.get("contracts", [])
        
        versions = []
        root_id = parent_id if parent_id else contract_id
        
        for c in contracts:
            c_parent = c.get("parent_id")
            c_id = c.get("id")
            if c_id == root_id or c_parent == root_id or c_parent == contract_id or c_id == contract_id:
                versions.append(c)
        
        versions.sort(key=lambda x: x.get("version_number", x.get("created_at", "")), reverse=True)
        return versions
    except Exception:
        return []


def api_get_related_contracts(parent_id: int, current_id: int) -> List[Dict]:
    """Fetch contracts related by parent_id."""
    try:
        response = requests.get(f"{API_BASE}/contracts", timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        contracts = data if isinstance(data, list) else data.get("contracts", [])
        
        related = []
        for c in contracts:
            if c.get("id") == current_id:
                continue
            if c.get("parent_id") == parent_id or c.get("id") == parent_id:
                related.append(c)
            if c.get("parent_id") == current_id:
                related.append(c)
        return related
    except Exception:
        return []


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_file_size(size_bytes: Optional[int]) -> str:
    """Format file size for display."""
    if not size_bytes:
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display."""
    if not date_str:
        return "Not found"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str[:10] if len(str(date_str)) >= 10 else str(date_str)


def parse_date_for_input(date_str: Optional[str]):
    """Parse date string to date for date_input widget."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except:
            return None


def format_currency(value) -> str:
    """Format currency value."""
    if value is None or value == "Not found" or value == "N/A":
        return str(value) if value else "Not found"
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return str(value)


def display_value(value, default="Not found") -> str:
    """Display value or default for missing."""
    if value is None or value == "" or value == "NOT_FOUND":
        return default
    return str(value)


def calculate_duration(effective: Optional[str], expiration: Optional[str]) -> str:
    """Calculate contract duration."""
    if not effective or not expiration:
        return "Not found"
    try:
        eff_dt = datetime.fromisoformat(effective.replace("Z", "+00:00"))
        exp_dt = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
        delta = exp_dt - eff_dt
        months = delta.days // 30
        if months >= 12:
            years = months // 12
            remaining_months = months % 12
            if remaining_months:
                return f"{years} year(s), {remaining_months} month(s)"
            return f"{years} year(s)"
        return f"{months} month(s)"
    except Exception:
        return "Not found"


# ============================================================================
# RENDER SECTIONS
# ============================================================================

def render_top_bar(contract: Dict):
    """Render back button and dynamic Save/Cancel."""
    has_changes = check_for_changes()
    
    col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
    
    with col1:
        if st.button("← Back to Portfolio", key="back_btn", type="secondary"):
            restore_portfolio_state()
            st.switch_page("pages/2_Contracts_Portfolio.py")
    
    # Show Save/Cancel only when changes detected
    if has_changes:
        with col3:
            if st.button("💾 Save", key="save_btn", type="primary", use_container_width=True):
                save_changes(contract)
        with col4:
            if st.button("✖ Cancel", key="cancel_btn", type="secondary", use_container_width=True):
                # Reset to original values
                st.session_state["details_original_values"] = {}
                st.rerun()


def save_changes(contract: Dict):
    """Collect and save all changes."""
    updates = {}
    
    # Text fields
    if "edit_title" in st.session_state:
        updates["title"] = st.session_state["edit_title"]
    if "edit_contract_type" in st.session_state:
        updates["contract_type"] = st.session_state["edit_contract_type"]
    if "edit_our_entity" in st.session_state:
        updates["our_entity"] = st.session_state["edit_our_entity"] or None
    if "edit_position" in st.session_state:
        updates["position"] = st.session_state["edit_position"]
    if "edit_counterparty" in st.session_state:
        updates["counterparty"] = st.session_state["edit_counterparty"] or None
    if "edit_counterparty_role" in st.session_state:
        updates["counterparty_role"] = st.session_state["edit_counterparty_role"]
    if "edit_payment_terms" in st.session_state:
        updates["payment_terms"] = st.session_state["edit_payment_terms"] or None
    if "edit_liability_cap" in st.session_state:
        updates["liability_cap"] = st.session_state["edit_liability_cap"] or None
    if "edit_governing_law" in st.session_state:
        updates["governing_law"] = st.session_state["edit_governing_law"] or None
    if "edit_warranty_period" in st.session_state:
        updates["warranty_period"] = st.session_state["edit_warranty_period"] or None
    
    # Dates
    if "edit_effective_date" in st.session_state:
        date_val = st.session_state["edit_effective_date"]
        updates["effective_date"] = date_val.isoformat() if date_val else None
    if "edit_expiration_date" in st.session_state:
        date_val = st.session_state["edit_expiration_date"]
        updates["expiration_date"] = date_val.isoformat() if date_val else None
    
    # Numeric
    if "edit_contract_value" in st.session_state:
        val = st.session_state["edit_contract_value"]
        updates["contract_value"] = val if val > 0 else None
    if "edit_termination_notice" in st.session_state:
        val = st.session_state["edit_termination_notice"]
        updates["termination_notice_days"] = val if val > 0 else None
    
    # Auto-renewal
    if "edit_auto_renewal" in st.session_state:
        updates["auto_renewal"] = st.session_state["edit_auto_renewal"]
    
    # Call API
    contract_id = contract.get("id")
    success, message = api_update_contract(contract_id, updates)
    
    if success:
        st.session_state["details_save_success"] = True
        st.session_state["details_original_values"] = {}
        st.rerun()
    else:
        st.error(f"❌ {message}")


def render_header(contract: Dict):
    """Section 1: Header with title, status, risk."""
    title = contract.get("title") or contract.get("filename") or "Untitled Contract"
    status = str(contract.get("status", "intake")).lower()
    status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["intake"])
    risk = str(contract.get("risk_level", "")).upper()
    risk_cfg = RISK_LEVEL_CONFIG.get(risk, None)
    
    # Editable title
    st.text_input(
        "Contract Title",
        value=title,
        key="edit_title",
        label_visibility="collapsed",
        placeholder="Contract Title"
    )
    
    # Status + Risk badges (read-only)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"{status_cfg['icon']} **Status:** {status_cfg['label']}")
    with col2:
        if risk_cfg:
            st.markdown(f"{risk_cfg['icon']} **Risk:** {risk_cfg['label']}")
        else:
            st.caption("Risk: Not assessed")


def render_metadata(contract: Dict):
    """Section 2: Metadata - type, dates, file size."""
    st.markdown("---")
    st.markdown("### 📋 Metadata")
    
    contract_type = contract.get("contract_type") or "Other"
    created_at = contract.get("created_at")
    effective_date = contract.get("effective_date")
    expiration_date = contract.get("expiration_date")
    file_size = contract.get("file_size")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Contract Type dropdown
        type_options = CONTRACT_TYPES
        type_idx = type_options.index(contract_type) if contract_type in type_options else len(type_options) - 1
        st.selectbox(
            "Type",
            options=type_options,
            index=type_idx,
            key="edit_contract_type"
        )
        
        st.markdown(f"**Uploaded:** {format_date(created_at)}")
        st.markdown(f"**File Size:** {format_file_size(file_size)}")
    
    with col2:
        # Effective Date picker
        eff_date = parse_date_for_input(effective_date)
        st.date_input(
            "Effective Date",
            value=eff_date,
            key="edit_effective_date"
        )
        
        # Expiration Date picker
        exp_date = parse_date_for_input(expiration_date)
        st.date_input(
            "Expiration Date",
            value=exp_date,
            key="edit_expiration_date"
        )
        
        # Duration (calculated, read-only)
        if effective_date and expiration_date:
            duration = calculate_duration(effective_date, expiration_date)
            st.caption(f"Duration: {duration}")


def render_parties(contract: Dict):
    """Section 3: Parties - both sides editable."""
    st.markdown("---")
    st.markdown("### 👥 Parties")
    
    our_entity = contract.get("our_entity") or ""
    counterparty = contract.get("counterparty") or ""
    position = contract.get("position") or "Not found"
    counterparty_role = contract.get("counterparty_role") or "Not found"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Our Organization**")
        st.text_input(
            "Our Entity",
            value=our_entity,
            key="edit_our_entity",
            placeholder="Your company name"
        )
        
        pos_idx = ROLE_OPTIONS.index(position) if position in ROLE_OPTIONS else len(ROLE_OPTIONS) - 1
        st.selectbox(
            "Our Role",
            options=ROLE_OPTIONS,
            index=pos_idx,
            key="edit_position"
        )
    
    with col2:
        st.markdown("**Counterparty**")
        st.text_input(
            "Counterparty",
            value=counterparty,
            key="edit_counterparty",
            placeholder="Counterparty name"
        )
        
        cp_idx = ROLE_OPTIONS.index(counterparty_role) if counterparty_role in ROLE_OPTIONS else len(ROLE_OPTIONS) - 1
        st.selectbox(
            "Counterparty Role",
            options=ROLE_OPTIONS,
            index=cp_idx,
            key="edit_counterparty_role"
        )


def render_key_terms(contract: Dict):
    """Section 4: Key Terms - financial and termination."""
    st.markdown("---")
    st.markdown("### 📝 Key Terms")
    
    contract_value = contract.get("contract_value")
    payment_terms = contract.get("payment_terms") or ""
    auto_renewal = contract.get("auto_renewal")
    termination_notice = contract.get("termination_notice_days")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            "Contract Value ($)",
            value=float(contract_value) if contract_value and contract_value not in ["Not found", "N/A"] else 0.0,
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            key="edit_contract_value",
            help="Enter 0 if not applicable or not found"
        )
        
        st.text_input(
            "Payment Terms",
            value=payment_terms if payment_terms not in ["Not found", "N/A"] else "",
            key="edit_payment_terms",
            placeholder="e.g., Net 30, Net 60"
        )
    
    with col2:
        # Auto-renewal dropdown
        renewal_options = [opt[0] for opt in AUTO_RENEWAL_OPTIONS]
        current_idx = 0
        for i, (label, val) in enumerate(AUTO_RENEWAL_OPTIONS):
            if val == auto_renewal:
                current_idx = i
                break
        
        selected_renewal = st.selectbox(
            "Auto-Renewal",
            options=renewal_options,
            index=current_idx,
            key="edit_auto_renewal_display"
        )
        # Store actual value
        for label, val in AUTO_RENEWAL_OPTIONS:
            if label == selected_renewal:
                st.session_state["edit_auto_renewal"] = val
                break
        
        st.number_input(
            "Termination Notice (days)",
            value=int(termination_notice) if termination_notice and termination_notice not in ["Not found", "N/A"] else 0,
            min_value=0,
            step=1,
            key="edit_termination_notice",
            help="Enter 0 if not found"
        )


def render_legal_terms(contract: Dict):
    """Section 5: Legal Terms - liability, governing law, warranty."""
    st.markdown("---")
    st.markdown("### ⚖️ Legal Terms")
    
    liability_cap = contract.get("liability_cap") or ""
    governing_law = contract.get("governing_law") or ""
    warranty_period = contract.get("warranty_period") or ""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input(
            "Liability Cap",
            value=liability_cap if liability_cap not in ["Not found", "N/A"] else "",
            key="edit_liability_cap",
            placeholder="e.g., $500,000 or fees paid"
        )
        
        st.text_input(
            "Governing Law",
            value=governing_law if governing_law not in ["Not found", "N/A"] else "",
            key="edit_governing_law",
            placeholder="e.g., Delaware, State of New York"
        )
    
    with col2:
        st.text_input(
            "Warranty Period",
            value=warranty_period if warranty_period not in ["Not found", "N/A"] else "",
            key="edit_warranty_period",
            placeholder="e.g., 12 months, 1 year"
        )


def render_risk_summary(contract: Dict):
    """Section 6: Risk Summary - read-only."""
    st.markdown("---")
    st.markdown("### ⚠️ Risk Summary")
    
    assessments = contract.get("assessments", [])
    risk_level = str(contract.get("risk_level", "")).upper()
    
    if not assessments and not risk_level:
        st.info("No risk analysis available. Run analysis to see risk summary.")
        return
    
    risk_cfg = RISK_LEVEL_CONFIG.get(risk_level, None)
    if risk_cfg:
        if risk_level in ["CRITICAL", "HIGH"]:
            st.error(f"{risk_cfg['icon']} **Overall Risk: {risk_cfg['label']}**")
        elif risk_level == "MEDIUM":
            st.warning(f"{risk_cfg['icon']} **Overall Risk: {risk_cfg['label']}**")
        else:
            st.success(f"{risk_cfg['icon']} **Overall Risk: {risk_cfg['label']}**")
    
    if assessments:
        latest = assessments[0] if assessments else {}
        severity_counts = latest.get("severity_counts", {})
        
        if severity_counts:
            st.markdown("**By Severity:**")
            cols = st.columns(4)
            with cols[0]:
                st.markdown(f"🔴 **{severity_counts.get('dealbreaker', 0)}** Dealbreaker")
            with cols[1]:
                st.markdown(f"🟠 **{severity_counts.get('critical', 0)}** Critical")
            with cols[2]:
                st.markdown(f"🟡 **{severity_counts.get('important', 0)}** Important")
            with cols[3]:
                st.markdown(f"🟢 **{severity_counts.get('low', 0)}** Low")


def render_versions(contract: Dict, versions: List[Dict]):
    """Section 7: Version history - read-only."""
    st.markdown("---")
    st.markdown("### 📚 Versions")
    
    current_id = contract.get("id")
    version_number = contract.get("version_number", "1.0")
    is_latest = contract.get("is_latest_version", True)
    
    st.markdown(f"**Current Version:** {version_number}" + (" (Latest)" if is_latest else ""))
    
    if not versions or len(versions) <= 1:
        st.caption("No other versions found")
        return
    
    st.markdown("**Version History:**")
    for v in versions:
        if v.get("id") == current_id:
            continue
        v_title = v.get("title") or v.get("filename") or "Untitled"
        v_num = v.get("version_number", "1.0")
        v_date = format_date(v.get("created_at"))
        v_latest = " (Latest)" if v.get("is_latest_version") else ""
        st.caption(f"• v{v_num} - {v_title[:30]} - {v_date}{v_latest}")


def render_related_documents(contract: Dict, related: List[Dict]):
    """Section 8: Related documents - read-only."""
    st.markdown("---")
    st.markdown("### 🔗 Related Documents")
    
    parent_id = contract.get("parent_id")
    
    if related:
        for r in related:
            r_title = r.get("title") or r.get("filename") or "Untitled"
            r_type = r.get("contract_type", "")
            r_id = r.get("id")
            relationship = "Parent" if r_id == parent_id else "Related"
            st.caption(f"• {r_title[:40]} ({r_type}) - {relationship}")
    else:
        st.caption("No related documents")


def render_actions(contract: Dict):
    """Action buttons: Download, Analyze."""
    st.markdown("---")

    contract_id = contract.get("id")
    filepath = contract.get("filepath")

    col1, col2 = st.columns(2)

    with col1:
        if filepath and os.path.exists(filepath):
            with open(filepath, "rb") as f:
                filename = os.path.basename(filepath)
                st.download_button(
                    label="⬇️ Download",
                    data=f.read(),
                    file_name=filename,
                    mime="application/octet-stream",
                    use_container_width=True
                )
        else:
            st.button("⬇️ Download", disabled=True, use_container_width=True, help="File not available")

    with col2:
        if st.button("🔍 Analyze", key="btn_analyze", use_container_width=True):
            st.session_state["risk_selected_contract"] = contract_id
            st.switch_page("pages/4_Risk_Analysis.py")


# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Contract Details", "📄", max_width=1200)

page_header(
    "Contract Details",
    subtitle="View and edit contract information",
    show_status=True,
    show_version=True
)

init_details_state()

# Show success message after save
if st.session_state.get("details_save_success"):
    st.success("✅ Contract updated successfully!")
    st.session_state["details_save_success"] = False

with content_container():
    contract_id = st.session_state.get("details_contract_id") or st.session_state.get("pf_selected_contract")
    
    if not contract_id:
        st.warning("No contract selected. Please select a contract from the Portfolio.")
        if st.button("← Go to Portfolio"):
            st.switch_page("pages/2_Contracts_Portfolio.py")
        st.stop()
    
    contract = api_get_contract(contract_id)
    
    if not contract:
        st.error(f"Could not load contract #{contract_id}")
        if st.session_state.get("details_error"):
            st.caption(f"Error: {st.session_state['details_error']}")
        if st.button("← Go to Portfolio"):
            st.switch_page("pages/2_Contracts_Portfolio.py")
        st.stop()
    
    # Store original values for change detection (only once per load)
    if not st.session_state.get("details_original_values"):
        store_original_values(contract)
    
    # Top bar with Back and dynamic Save/Cancel
    render_top_bar(contract)
    
    st.markdown("")
    
    # Main content - two column layout
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        render_header(contract)
        render_metadata(contract)
        render_parties(contract)
        render_key_terms(contract)
        render_legal_terms(contract)
    
    with col_side:
        render_risk_summary(contract)
        
        parent_id = contract.get("parent_id")
        versions = api_get_versions(contract_id, parent_id)
        render_versions(contract, versions)
        
        related = api_get_related_contracts(parent_id, contract_id) if parent_id else []
        render_related_documents(contract, related)
    
    # Actions row at bottom
    render_actions(contract)
