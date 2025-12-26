# pages/3_Intelligent_Intake.py
"""
CIP Intelligent Intake v3.3 FINAL
- Manual entry option for ALL fields
- Simple dropdown for related contracts (all existing)
- Complete state: Left=summary, Middle=details, Right=progress+health
- All null-safety checks included
"""

import streamlit as st
import requests
from pathlib import Path
from typing import Optional, Dict, List

from components.page_wrapper import (
    init_page,
    page_header,
    content_container
)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:5000/api"

CONTRACT_TYPES = [
    "NDA", "MNDA", "MOU", "MSA", "PSA", "MPA", "SOW", "PO",
    "EULA", "Proposal", "Amendment", "Change Order", "Royalty Agreement", "Other"
]

PURPOSES = [
    "Professional Services", "Consulting Services", "Equipment Purchase",
    "Construction", "Staffing", "Software License", "Maintenance", "Other"
]

LEVERAGE_OPTIONS = ["Low", "Medium", "High"]
ORIENTATION_OPTIONS = ["Customer", "Vendor"]

QUESTION_SEQUENCE = [
    "title",
    "contract_type", 
    "purpose",
    "parties",
    "orientation",
    "leverage",
    "related"
]

# ============================================================================
# SESSION STATE
# ============================================================================

def init_intake_state():
    """Initialize intake-specific session state."""
    defaults = {
        "intake_step": 0,
        "intake_file_id": None,
        "intake_file_path": None,
        "intake_filename": None,
        "intake_extraction": None,
        "intake_all_contracts": [],
        "intake_confirmed": {},
        "intake_progress_stage": "idle",
        "intake_complete": False,
        "intake_contract_id": None,
        "intake_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================================
# API CALLS
# ============================================================================

def api_upload_file(file) -> Dict:
    """Upload file to backend."""
    try:
        files = {"file": (file.name, file.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        response = requests.post(f"{API_BASE}/intake/upload", files=files, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def api_extract_metadata(file_path: str) -> Dict:
    """Extract metadata from uploaded file."""
    try:
        response = requests.post(
            f"{API_BASE}/intake/extract",
            json={"file_path": file_path},
            timeout=15
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def api_get_all_contracts() -> List[Dict]:
    """Fetch all existing contracts for related dropdown."""
    try:
        response = requests.get(f"{API_BASE}/contracts", timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        
        # Handle different response structures
        contracts = []
        if isinstance(data, list):
            contracts = data
        elif isinstance(data, dict):
            contracts = data.get("contracts", data.get("data", []))
        
        # Filter out None values and non-dict items
        valid_contracts = []
        for c in contracts:
            if c is not None and isinstance(c, dict):
                valid_contracts.append(c)
        
        return valid_contracts
    except Exception:
        return []


def api_store_contract(data: Dict) -> Dict:
    """Store confirmed contract in database."""
    try:
        response = requests.post(
            f"{API_BASE}/intake/store",
            json=data,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# PROGRESS & ANIMATION COMPONENTS
# ============================================================================

def render_system_health():
    """Render compact system health indicator."""
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 6px; justify-content: flex-end;">
            <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%;"></span>
            <span style="color: #64748B; font-size: 0.7rem;">System Online</span>
        </div>
    ''', unsafe_allow_html=True)


def render_intake_progress(stage: str = "idle", contract_id: int = None):
    """Render vertical progress steps."""
    complete = (stage == "complete" or contract_id is not None)
    
    stages = [
        ("upload", "Upload"),
        ("extract", "Extract"),
        ("analyze", "Analyze"),
    ]
    
    # Final step text
    if complete and contract_id:
        stages.append(("complete", f"Stored (ID: {contract_id})"))
    else:
        stages.append(("complete", "Complete"))
    
    stage_order = ["idle", "upload", "extract", "analyze", "complete"]
    current_idx = stage_order.index(stage) if stage in stage_order else 0
    if complete:
        current_idx = 5
    
    st.markdown("**Progress**")
    
    for i, (stage_key, label) in enumerate(stages):
        stage_num = i + 1
        
        if complete or current_idx > stage_num:
            # Completed
            st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 8px; padding: 5px 0; border-left: 2px solid #10B981; padding-left: 10px; margin-left: 6px;">
                    <span style="color: #10B981; font-size: 0.9rem;">✓</span>
                    <span style="color: #10B981; font-size: 0.8rem; font-weight: 500;">{label}</span>
                </div>
            ''', unsafe_allow_html=True)
        elif current_idx == stage_num:
            # Active
            st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 8px; padding: 5px 0; border-left: 2px solid #8B5CF6; padding-left: 10px; margin-left: 6px; background: rgba(139, 92, 246, 0.1); border-radius: 0 6px 6px 0;">
                    <span style="color: #8B5CF6; font-size: 0.9rem;">●</span>
                    <span style="color: #A78BFA; font-size: 0.8rem; font-weight: 600;">{label}</span>
                </div>
            ''', unsafe_allow_html=True)
        else:
            # Pending
            st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 8px; padding: 5px 0; border-left: 2px solid #334155; padding-left: 10px; margin-left: 6px;">
                    <span style="color: #475569; font-size: 0.9rem;">○</span>
                    <span style="color: #475569; font-size: 0.8rem;">{label}</span>
                </div>
            ''', unsafe_allow_html=True)


def render_upload_another():
    """Render upload another link."""
    if st.button("↻ Upload Another", key="btn_upload_another", type="secondary"):
        for key in list(st.session_state.keys()):
            if key.startswith("intake_"):
                del st.session_state[key]
        st.rerun()


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_file_uploader():
    """Render file upload section."""
    uploaded_file = st.file_uploader(
        "Drop contract here or click to browse",
        type=["docx"],
        key="intake_file_uploader",
        help="Only .docx files supported"
    )
    
    if uploaded_file and not st.session_state.get("intake_file_id"):
        with st.spinner("Uploading..."):
            st.session_state["intake_progress_stage"] = "upload"
            result = api_upload_file(uploaded_file)
            
            if "error" in result:
                st.session_state["intake_error"] = result["error"]
                return
            
            st.session_state["intake_file_id"] = result.get("file_id")
            st.session_state["intake_file_path"] = result.get("file_path")
            st.session_state["intake_filename"] = result.get("filename")
            
        with st.spinner("Extracting metadata..."):
            st.session_state["intake_progress_stage"] = "extract"
            result = api_extract_metadata(st.session_state["intake_file_path"])
            
            if "error" in result and "extraction" not in result:
                st.session_state["intake_error"] = result["error"]
                return
            
            st.session_state["intake_extraction"] = result.get("extraction", {})
            
            # Fetch all contracts for related dropdown
            st.session_state["intake_all_contracts"] = api_get_all_contracts()
            
            st.session_state["intake_progress_stage"] = "analyze"
            st.session_state["intake_step"] = 1
            st.rerun()


def get_prefilled_value(field: str):
    """Get pre-filled value from extraction."""
    extraction = st.session_state.get("intake_extraction")
    if not extraction or not isinstance(extraction, dict):
        return None
    
    if field == "title":
        return extraction.get("title", "")
    elif field == "contract_type":
        return extraction.get("contract_type")
    elif field == "purpose":
        return extraction.get("purpose")
    elif field == "parties":
        parties = extraction.get("parties")
        if parties and isinstance(parties, list):
            return parties
        return []
    return None


def render_question_panel():
    """Render current question with manual entry option."""
    step = st.session_state.get("intake_step", 0)
    if step == 0 or step > len(QUESTION_SEQUENCE):
        if st.session_state.get("intake_complete"):
            render_complete_summary()
        else:
            st.info("Upload a contract to begin")
        return
    
    current_q = QUESTION_SEQUENCE[step - 1]
    extraction = st.session_state.get("intake_extraction") or {}
    confirmed = st.session_state.get("intake_confirmed", {})
    
    st.caption(f"Question {step} of 7")
    
    # ===================== TITLE =====================
    if current_q == "title":
        prefill = get_prefilled_value("title") or ""
        confidence = extraction.get("title_confidence", 0) if isinstance(extraction, dict) else 0
        
        st.markdown("**📝 Contract Title**")
        if confidence >= 0.7 and prefill:
            st.caption(f"Suggested: {prefill[:50]}{'...' if len(prefill) > 50 else ''} ({confidence:.0%})")
        
        value = st.text_input("Enter title", value=prefill, key="q_title")
        
        if st.button("Confirm Title", key="btn_title", type="primary", disabled=not value):
            confirmed["title"] = value
            st.session_state["intake_confirmed"] = confirmed
            st.session_state["intake_step"] += 1
            st.rerun()
    
    # ===================== CONTRACT TYPE =====================
    elif current_q == "contract_type":
        prefill = get_prefilled_value("contract_type")
        confidence = extraction.get("contract_type_confidence", 0) if isinstance(extraction, dict) else 0
        
        st.markdown("**📋 Contract Type**")
        if confidence >= 0.7 and prefill:
            st.caption(f"Suggested: {prefill} ({confidence:.0%})")
        
        use_manual = st.checkbox("Enter custom type", key="chk_type_manual")
        
        if use_manual:
            value = st.text_input("Custom type", key="q_type_manual")
        else:
            idx = CONTRACT_TYPES.index(prefill) if prefill in CONTRACT_TYPES else 0
            value = st.selectbox("Select type", CONTRACT_TYPES, index=idx, key="q_type")
        
        if st.button("Confirm Type", key="btn_type", type="primary", disabled=not value):
            confirmed["contract_type"] = value
            st.session_state["intake_confirmed"] = confirmed
            st.session_state["intake_step"] += 1
            st.rerun()
    
    # ===================== PURPOSE =====================
    elif current_q == "purpose":
        prefill = get_prefilled_value("purpose")
        confidence = extraction.get("purpose_confidence", 0) if isinstance(extraction, dict) else 0
        
        st.markdown("**🎯 Contract Purpose**")
        if confidence >= 0.7 and prefill:
            st.caption(f"Suggested: {prefill} ({confidence:.0%})")
        
        use_manual = st.checkbox("Enter custom purpose", key="chk_purpose_manual")
        
        if use_manual:
            value = st.text_input("Custom purpose", key="q_purpose_manual")
        else:
            idx = PURPOSES.index(prefill) if prefill in PURPOSES else 0
            value = st.selectbox("Select purpose", PURPOSES, index=idx, key="q_purpose")
        
        if st.button("Confirm Purpose", key="btn_purpose", type="primary", disabled=not value):
            confirmed["purpose"] = value
            st.session_state["intake_confirmed"] = confirmed
            st.session_state["intake_step"] += 1
            st.rerun()
    
    # ===================== PARTIES =====================
    elif current_q == "parties":
        parties = get_prefilled_value("parties") or []
        confidence = extraction.get("parties_confidence", 0) if isinstance(extraction, dict) else 0
        hint = extraction.get("orientation_hint", "") if isinstance(extraction, dict) else ""
        
        st.markdown("**👥 Parties**")
        if parties and len(parties) == 2:
            st.caption(f"Found: {parties[0]}, {parties[1]} ({confidence:.0%})")
            if hint:
                st.caption(f"Hint: {hint}")
        
        # Always show manual entry option
        has_two_parties = isinstance(parties, list) and len(parties) == 2
        use_manual = st.checkbox("Enter parties manually", key="chk_parties_manual", 
                                  value=(not has_two_parties))
        
        if use_manual or not has_two_parties:
            # Manual entry
            default_our = parties[0] if isinstance(parties, list) and len(parties) > 0 else ""
            default_counter = parties[1] if isinstance(parties, list) and len(parties) > 1 else ""
            
            our_party = st.text_input("Our Party", key="q_our_party_manual", value=default_our)
            counterparty = st.text_input("Counterparty", key="q_counterparty_manual", value=default_counter)
            
            if st.button("Confirm Parties", key="btn_parties", type="primary", 
                        disabled=not (our_party and counterparty)):
                confirmed["party"] = our_party
                confirmed["counterparty"] = counterparty
                st.session_state["intake_confirmed"] = confirmed
                st.session_state["intake_step"] += 1
                st.rerun()
        else:
            # Selection from extracted
            st.markdown("*Which party is **ours**?*")
            our_party = st.radio("Select our party", parties, key="q_our_party", horizontal=True)
            counterparty = parties[1] if our_party == parties[0] else parties[0]
            
            st.info(f"**Our Party:** {our_party}\n\n**Counterparty:** {counterparty}")
            
            if st.button("Confirm Parties", key="btn_parties_select", type="primary"):
                confirmed["party"] = our_party
                confirmed["counterparty"] = counterparty
                st.session_state["intake_confirmed"] = confirmed
                st.session_state["intake_step"] += 1
                st.rerun()
    
    # ===================== ORIENTATION =====================
    elif current_q == "orientation":
        hint = extraction.get("orientation_hint", "") if isinstance(extraction, dict) else ""
        
        st.markdown("**🔄 Our Orientation**")
        st.caption("Are we the customer or the vendor in this contract?")
        if hint:
            st.caption(f"Hint: {hint}")
        
        use_manual = st.checkbox("Enter custom orientation", key="chk_orient_manual")
        
        if use_manual:
            value = st.text_input("Custom orientation", key="q_orient_manual")
        else:
            value = st.radio("Select orientation", ORIENTATION_OPTIONS, key="q_orientation", horizontal=True)
        
        if st.button("Confirm Orientation", key="btn_orientation", type="primary", disabled=not value):
            confirmed["orientation"] = value
            st.session_state["intake_confirmed"] = confirmed
            st.session_state["intake_step"] += 1
            st.rerun()
    
    # ===================== LEVERAGE =====================
    elif current_q == "leverage":
        st.markdown("**⚖️ Our Leverage**")
        st.caption("How much negotiating power do we have?")
        
        use_manual = st.checkbox("Enter custom leverage", key="chk_leverage_manual")
        
        if use_manual:
            value = st.text_input("Custom leverage", key="q_leverage_manual")
        else:
            value = st.radio("Select leverage", LEVERAGE_OPTIONS, key="q_leverage", horizontal=True)
        
        if st.button("Confirm Leverage", key="btn_leverage", type="primary", disabled=not value):
            confirmed["leverage"] = value
            st.session_state["intake_confirmed"] = confirmed
            st.session_state["intake_step"] += 1
            st.rerun()
    
    # ===================== RELATED =====================
    elif current_q == "related":
        all_contracts = st.session_state.get("intake_all_contracts") or []
        
        st.markdown("**🔗 Related Contract**")
        st.caption("Link to an existing contract (optional)")
        
        # Build options list safely
        options = ["None - No related contract"]
        valid_contracts = []
        
        for c in all_contracts:
            # Skip None or non-dict items
            if c is None or not isinstance(c, dict):
                continue
            
            # Safely get fields with defaults
            title = c.get("title")
            if title is None:
                title = "Untitled"
            title = str(title)[:30]
            
            ctype = c.get("contract_type")
            if ctype is None:
                ctype = ""
            ctype = str(ctype)
            
            party = c.get("counterparty")
            if party is None:
                party = ""
            party = str(party)[:20]
            
            options.append(f"{title} ({ctype}) - {party}")
            valid_contracts.append(c)
        
        # Show dropdown if we have options
        if len(options) > 1:
            selection = st.selectbox("Select related contract", options, key="q_related")
            
            related_id = None
            if selection != options[0]:
                try:
                    idx = options.index(selection) - 1
                    if 0 <= idx < len(valid_contracts):
                        related_id = valid_contracts[idx].get("id")
                except (ValueError, IndexError):
                    related_id = None
        else:
            st.caption("No existing contracts available")
            related_id = None
        
        if st.button("Confirm & Save", key="btn_related", type="primary"):
            confirmed["related_contract_id"] = related_id
            st.session_state["intake_confirmed"] = confirmed
            save_contract()


def save_contract():
    """Save confirmed contract to database."""
    st.session_state["intake_progress_stage"] = "complete"
    confirmed = st.session_state.get("intake_confirmed", {})
    
    payload = {
        "file_path": st.session_state.get("intake_file_path"),
        "title": confirmed.get("title"),
        "contract_type": confirmed.get("contract_type"),
        "purpose": confirmed.get("purpose"),
        "party": confirmed.get("party"),
        "counterparty": confirmed.get("counterparty"),
        "orientation": confirmed.get("orientation"),
        "leverage": confirmed.get("leverage"),
        "related_contract_id": confirmed.get("related_contract_id"),
    }
    
    result = api_store_contract(payload)
    
    if "error" in result:
        st.session_state["intake_error"] = result["error"]
        return
    
    st.session_state["intake_complete"] = True
    st.session_state["intake_contract_id"] = result.get("contract_id")
    st.rerun()


def render_complete_summary():
    """Render summary in left column when complete."""
    confirmed = st.session_state.get("intake_confirmed", {})
    filename = st.session_state.get("intake_filename", "Unknown")
    
    st.markdown("**✅ Intake Complete**")
    st.caption(f"Uploaded: {filename}")
    
    st.markdown("---")
    st.markdown(f"**Title:** {confirmed.get('title', 'N/A')}")
    st.markdown(f"**Type:** {confirmed.get('contract_type', 'N/A')}")
    st.markdown(f"**Our Party:** {confirmed.get('party', 'N/A')}")


def render_confirmed_panel():
    """Render confirmed fields (middle column)."""
    confirmed = st.session_state.get("intake_confirmed", {})
    complete = st.session_state.get("intake_complete", False)
    
    st.markdown("**Confirmed**")
    
    fields = [
        ("Title", "title"),
        ("Type", "contract_type"),
        ("Purpose", "purpose"),
        ("Our Party", "party"),
        ("Counterparty", "counterparty"),
        ("Orientation", "orientation"),
        ("Leverage", "leverage"),
    ]
    
    for label, key in fields:
        value = confirmed.get(key)
        if value:
            display = str(value)[:20] + "..." if len(str(value)) > 20 else str(value)
            st.markdown(f"<span style='color:#64748B;font-size:0.75rem;'>{label}</span> <span style='color:#10B981;'>✓ {display}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#475569;font-size:0.75rem;'>{label}</span> <span style='color:#475569;'>○</span>", unsafe_allow_html=True)
    
    if complete:
        st.markdown("---")
        contract_id = st.session_state.get("intake_contract_id")
        st.success(f"Saved as Contract #{contract_id}")


def render_progress_panel():
    """Render progress (right column)."""
    stage = st.session_state.get("intake_progress_stage", "idle")
    complete = st.session_state.get("intake_complete", False)
    contract_id = st.session_state.get("intake_contract_id") if complete else None
    
    # System health at top
    render_system_health()
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Progress steps
    render_intake_progress(stage=stage, contract_id=contract_id)
    
    # Upload another when complete
    if complete:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        render_upload_another()


# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Intelligent Intake", "📥", max_width=1200)

page_header(
    "Intelligent Intake",
    subtitle="Upload and process contracts with AI-powered metadata extraction",
    show_status=True,
    show_version=True
)

init_intake_state()

with content_container():
    # Error display
    if st.session_state.get("intake_error"):
        st.error(st.session_state["intake_error"])
        if st.button("Clear Error"):
            st.session_state["intake_error"] = None
            st.rerun()
    
    # File uploader or filename display
    if not st.session_state.get("intake_file_id"):
        render_file_uploader()
    else:
        filename = st.session_state.get("intake_filename", "Unknown")
        st.markdown(f'''
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 8px 12px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                <span style="color: #10B981;">📄</span>
                <span style="color: #E2E8F0; font-size: 0.85rem;">{filename}</span>
            </div>
        ''', unsafe_allow_html=True)
    
    # 3-column layout
    if st.session_state.get("intake_step", 0) > 0 or st.session_state.get("intake_complete"):
        col_left, col_mid, col_right = st.columns([1.3, 1.1, 0.9])
        
        with col_left:
            render_question_panel()
        
        with col_mid:
            render_confirmed_panel()
        
        with col_right:
            render_progress_panel()
