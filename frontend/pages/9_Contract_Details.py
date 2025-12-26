# pages/3_Contract_Details.py
"""
CIP Contract Details v1.0
- Full contract information display
- Sections: Header, Metadata, Parties, Key Terms, Risk Summary, Versions, Related Documents
- Static risk heatmaps (level + category)
- Back navigation preserves Portfolio state
- Placeholders for missing extracted fields
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
        # Portfolio state preservation
        "portfolio_scroll_position": 0,
        "portfolio_filters_snapshot": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_portfolio_state():
    """Save current portfolio state before navigating to details."""
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
    """Restore portfolio state when navigating back."""
    snapshot = st.session_state.get("portfolio_filters_snapshot", {})
    for key, value in snapshot.items():
        st.session_state[key] = value


# ============================================================================
# API CALLS
# ============================================================================

def api_get_contract(contract_id: int) -> Optional[Dict]:
    """Fetch single contract with full details."""
    try:
        response = requests.get(f"{API_BASE}/contract/{contract_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Unwrap nested structure - API returns { contract: {...}, clauses: [...], ... }
            contract = data.get("contract", {})
            contract["clauses"] = data.get("clauses", [])
            contract["assessments"] = data.get("assessments", [])
            contract["statistics"] = data.get("statistics", {})
            return contract
        return None
    except Exception as e:
        st.session_state["details_error"] = str(e)
        return None


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
            # Same parent or is the parent
            if c.get("parent_id") == parent_id or c.get("id") == parent_id:
                related.append(c)
            # Current contract is parent of this one
            if c.get("parent_id") == current_id:
                related.append(c)
        return related
    except Exception:
        return []


def api_get_versions(contract_id: int, parent_id: Optional[int]) -> List[Dict]:
    """Fetch version history for contract family."""
    try:
        response = requests.get(f"{API_BASE}/contracts", timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        contracts = data if isinstance(data, list) else data.get("contracts", [])
        
        # Find all contracts in same version chain
        versions = []
        root_id = parent_id if parent_id else contract_id
        
        for c in contracts:
            c_parent = c.get("parent_id")
            c_id = c.get("id")
            # Part of same chain
            if c_id == root_id or c_parent == root_id or c_parent == contract_id or c_id == contract_id:
                versions.append(c)
        
        # Sort by version_number or created_at
        versions.sort(key=lambda x: x.get("version_number", x.get("created_at", "")), reverse=True)
        return versions
    except Exception:
        return []


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_file_size(filepath: str) -> str:
    """Get human-readable file size."""
    if not filepath:
        return "Unknown"
    try:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
    except Exception:
        pass
    return "Unknown"


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display."""
    if not date_str:
        return "Not set"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str[:10] if len(str(date_str)) >= 10 else str(date_str)


def format_currency(value: Optional[float]) -> str:
    """Format currency value."""
    if value is None:
        return "Not extracted"
    try:
        return f"${value:,.2f}"
    except Exception:
        return str(value)


def calculate_duration(effective: Optional[str], expiration: Optional[str]) -> str:
    """Calculate contract duration."""
    if not effective or not expiration:
        return "Not extracted"
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
        return "Not extracted"


# ============================================================================
# RENDER SECTIONS
# ============================================================================

def render_back_button():
    """Render back navigation to Portfolio."""
    if st.button("← Back to Portfolio", key="back_btn", type="secondary"):
        restore_portfolio_state()
        st.switch_page("pages/2_Contracts_Portfolio.py")


def render_header(contract: Dict):
    """Section 1: Header with name, status, risk, counterparty."""
    title = contract.get("title") or contract.get("filename") or "Untitled Contract"
    status = str(contract.get("status", "intake")).lower()
    status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["intake"])
    risk = str(contract.get("risk_level", "")).upper()
    risk_cfg = RISK_LEVEL_CONFIG.get(risk, None)
    counterparty = contract.get("counterparty") or "Unknown"
    
    # Title row
    st.markdown(f"## {title}")
    
    # Status + Risk badges
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        st.markdown(f"{status_cfg['icon']} **{status_cfg['label']}**")
    with col2:
        if risk_cfg:
            st.markdown(f"{risk_cfg['icon']} **{risk_cfg['label']} Risk**")
        else:
            st.caption("Risk: Not assessed")
    with col3:
        st.markdown(f"**Counterparty:** {counterparty}")


def render_metadata(contract: Dict):
    """Section 2: Metadata - type, dates, file size."""
    st.markdown("---")
    st.markdown("### 📋 Metadata")
    
    contract_type = contract.get("contract_type") or "Unknown"
    created_at = contract.get("created_at")
    effective_date = contract.get("effective_date")
    expiration_date = contract.get("expiration_date")
    filepath = contract.get("filepath")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Type:** {contract_type}")
        st.markdown(f"**Uploaded:** {format_date(created_at)}")
        st.markdown(f"**File Size:** {get_file_size(filepath)}")
    
    with col2:
        st.markdown(f"**Effective Date:** {format_date(effective_date)}")
        st.markdown(f"**Expiration Date:** {format_date(expiration_date)}")
        
        # Days remaining if active
        if expiration_date:
            try:
                exp_dt = datetime.fromisoformat(expiration_date.replace("Z", "+00:00"))
                days_remaining = (exp_dt - datetime.now(exp_dt.tzinfo)).days
                if days_remaining > 0:
                    if days_remaining <= 30:
                        st.warning(f"⚠️ Expires in {days_remaining} days")
                    elif days_remaining <= 90:
                        st.info(f"📅 {days_remaining} days remaining")
                elif days_remaining < 0:
                    st.error(f"❌ Expired {abs(days_remaining)} days ago")
            except Exception:
                pass


def render_parties(contract: Dict):
    """Section 3: Parties - your role, counterparty details."""
    st.markdown("---")
    st.markdown("### 👥 Parties")
    
    our_entity = contract.get("our_entity") or "Not specified"
    counterparty = contract.get("counterparty") or "Unknown"
    position = contract.get("position") or "Not specified"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Our Organization**")
        st.markdown(f"• Entity: {our_entity}")
        st.markdown(f"• Role: {position}")
    
    with col2:
        st.markdown("**Counterparty**")
        st.markdown(f"• Entity: {counterparty}")
        # Infer counterparty role
        if position.lower() == "customer":
            st.markdown("• Role: Vendor")
        elif position.lower() == "vendor":
            st.markdown("• Role: Customer")
        else:
            st.markdown("• Role: Not specified")


def render_key_terms(contract: Dict):
    """Section 4: Key Terms - auto-extracted with placeholders."""
    st.markdown("---")
    st.markdown("### 📝 Key Terms")
    
    contract_value = contract.get("contract_value")
    effective_date = contract.get("effective_date")
    expiration_date = contract.get("expiration_date")
    auto_renewal = contract.get("auto_renewal")
    termination_notice = contract.get("termination_notice_days")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Contract Value:** {format_currency(contract_value)}")
        st.markdown(f"**Duration:** {calculate_duration(effective_date, expiration_date)}")
    
    with col2:
        # Renewal
        if auto_renewal is not None:
            renewal_text = "Yes" if auto_renewal else "No"
            st.markdown(f"**Auto-Renewal:** {renewal_text}")
        else:
            st.markdown("**Auto-Renewal:** Not extracted")
        
        # Termination notice
        if termination_notice:
            st.markdown(f"**Termination Notice:** {termination_notice} days")
        else:
            st.markdown("**Termination Notice:** Not extracted")


def render_risk_summary(contract: Dict):
    """Section 5: Risk Summary - static heatmaps, no links."""
    st.markdown("---")
    st.markdown("### ⚠️ Risk Summary")
    
    assessments = contract.get("assessments", [])
    risk_level = str(contract.get("risk_level", "")).upper()
    
    if not assessments and not risk_level:
        st.info("No risk analysis available. Run analysis from Portfolio to see risk summary.")
        return
    
    # Overall risk display
    risk_cfg = RISK_LEVEL_CONFIG.get(risk_level, None)
    if risk_cfg:
        if risk_level in ["CRITICAL", "HIGH"]:
            st.error(f"{risk_cfg['icon']} **Overall Risk: {risk_cfg['label']}**")
        elif risk_level == "MEDIUM":
            st.warning(f"{risk_cfg['icon']} **Overall Risk: {risk_cfg['label']}**")
        else:
            st.success(f"{risk_cfg['icon']} **Overall Risk: {risk_cfg['label']}**")
    
    # If we have detailed assessment data
    if assessments:
        latest = assessments[0] if assessments else {}
        risk_by_category = latest.get("risk_by_category", {})
        severity_counts = latest.get("severity_counts", {})
        
        # Severity heatmap row
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
        
        # Category heatmap
        if risk_by_category:
            st.markdown("")
            st.markdown("**By Category:**")
            
            cat_items = []
            for cat_key, cat_data in risk_by_category.items():
                if isinstance(cat_data, dict):
                    flagged = cat_data.get("flagged", 0)
                    if flagged > 0:
                        cat_info = CATEGORY_LABELS.get(cat_key.lower(), {"abbr": cat_key[:3].upper(), "full": cat_key})
                        cat_items.append((cat_info["abbr"], cat_info["full"], flagged))
            
            if cat_items:
                # Display in 4-column grid
                rows = (len(cat_items) + 3) // 4
                for row in range(rows):
                    cols = st.columns(4)
                    for col_idx in range(4):
                        item_idx = row * 4 + col_idx
                        if item_idx < len(cat_items):
                            abbr, full, count = cat_items[item_idx]
                            with cols[col_idx]:
                                st.markdown(f"**{abbr}** ({count})", help=full)


def render_versions(contract: Dict, versions: List[Dict]):
    """Section 6: Version history."""
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
    """Section 7: Related documents + placeholder for relationship management."""
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
        st.caption("No related documents linked during intake")
    
    # Placeholder for future relationship management
    st.markdown("")
    with st.container():
        st.markdown(
            """
            <div style="background: rgba(30,41,59,0.4); padding: 16px; border-radius: 8px; border: 1px dashed rgba(148,163,184,0.3);">
                <div style="color: #94A3B8; font-size: 0.9rem;">
                    🔗 <strong>Manage Relationships</strong><br/>
                    <span style="font-size: 0.8rem;">Coming soon</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_actions(contract: Dict):
    """Action buttons: Download, Analyze."""
    st.markdown("---")

    contract_id = contract.get("id")
    filepath = contract.get("filepath")

    col1, col2 = st.columns(2)

    with col1:
        # Download
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
        # Analyze - navigate to Risk Analysis
        if st.button("🔍 Analyze", key="btn_analyze", use_container_width=True):
            st.session_state["risk_selected_contract"] = contract_id
            st.switch_page("pages/4_Risk_Analysis.py")


# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Contract Details", "📄", max_width=1200)

page_header(
    "Contract Details",
    subtitle="View contract information and analysis",
    show_status=True,
    show_version=True
)

init_details_state()

# DEBUG: Show session state for troubleshooting
st.sidebar.caption(f"pf_selected_contract: {st.session_state.get('pf_selected_contract')}")

with content_container():
    # Check if contract ID is set
    contract_id = st.session_state.get("details_contract_id") or st.session_state.get("pf_selected_contract")
    
    if not contract_id:
        st.warning("No contract selected. Please select a contract from the Portfolio.")
        if st.button("← Go to Portfolio"):
            st.switch_page("pages/2_Contracts_Portfolio.py")
        st.stop()
    
    # Fetch contract data
    contract = api_get_contract(contract_id)
    
    if not contract:
        st.error(f"Could not load contract #{contract_id}")
        if st.session_state.get("details_error"):
            st.caption(f"Error: {st.session_state['details_error']}")
        if st.button("← Go to Portfolio"):
            st.switch_page("pages/2_Contracts_Portfolio.py")
        st.stop()
    
    # Back button
    render_back_button()
    
    st.markdown("")
    
    # Main content - two column layout
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        # Section 1: Header
        render_header(contract)
        
        # Section 2: Metadata
        render_metadata(contract)
        
        # Section 3: Parties
        render_parties(contract)
        
        # Section 4: Key Terms
        render_key_terms(contract)
    
    with col_side:
        # Section 5: Risk Summary
        render_risk_summary(contract)
        
        # Section 6: Versions
        parent_id = contract.get("parent_id")
        versions = api_get_versions(contract_id, parent_id)
        render_versions(contract, versions)
        
        # Section 7: Related Documents
        related = api_get_related_contracts(parent_id, contract_id) if parent_id else []
        render_related_documents(contract, related)
    
    # Actions row at bottom
    render_actions(contract)
