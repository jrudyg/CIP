# pages/3_Intelligent_Intake.py
"""
CIP Intelligent Intake v4.0
- REVERTED to original working flow
- Upload → Extract → Questions → Store (at end only)
- Removed mid-flow DB record creation that caused freeze
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
        response = requests.post(f"{API_BASE}/intake/upload", files=files, timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def api_extract_metadata(file_path: str) -> Dict:
    """Extract metadata from uploaded file."""
    try:
        response = requests.post(
            f"{API_BASE}/intake/extract",
            json={"file_path": file_path},
            timeout=120
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
        
        contracts = []
        if isinstance(data, list):
            contracts = data
        elif isinstance(data, dict):
            contracts = data.get("contracts", data.get("data", []))
        
        valid_contracts = []
        for c in contracts:
            if c is not None and isinstance(c, dict):
                valid_contracts.append(c)
        
        return valid_contracts
    except Exception:
        return []


def api_store_contract(data: Dict) -> Dict:
    """Store contract to database (called at END of intake flow)."""
    try:
        response = requests.post(
            f"{API_BASE}/intake/store",
            json=data,
            timeout=15
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# PROGRESS COMPONENTS
# ============================================================================

def render_system_health():
    """Render compact system health indicator."""
    st.caption("🟢 System Online")


def render_intake_progress(stage: str = "idle", contract_id: int = None):
    """Render vertical progress steps."""
    complete = st.session_state.get("intake_complete", False)
    
    stages = [
        ("upload", "Upload"),
        ("extract", "Extract"),
        ("analyze", "Analyze"),
    ]
    
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
            st.write(f"✅ {label}")
        elif current_idx == stage_num:
            st.write(f"🔵 **{label}**")
        else:
            st.caption(f"○ {label}")


def render_upload_another():
    """Render upload another link."""
    if st.button("↻ Upload Another", key="btn_upload_another", type="secondary"):
        for key in list(st.session_state.keys()):
            if key.startswith("intake_"):
                del st.session_state[key]
        st.rerun()


# ============================================================================
# FILE UPLOADER - ORIGINAL WORKING FLOW
# ============================================================================

def render_file_uploader():
    """Render file upload section - ORIGINAL 2-STEP FLOW."""
    uploaded_file = st.file_uploader(
        "Drop contract here or click to browse",
        type=["docx"],
        key="intake_file_uploader",
        help="Only .docx files supported"
    )
    
    if uploaded_file and not st.session_state.get("intake_file_id"):
        # STEP 1: Upload file
        with st.spinner("Uploading file..."):
            st.session_state["intake_progress_stage"] = "upload"
            result = api_upload_file(uploaded_file)
            
            if "error" in result:
                st.session_state["intake_error"] = f"Upload failed: {result['error']}"
                return
            
            file_path = result.get("file_path")
            filename = result.get("filename", uploaded_file.name)
            
            st.session_state["intake_file_id"] = result.get("file_id", "temp")
            st.session_state["intake_file_path"] = file_path
            st.session_state["intake_filename"] = filename
        
        # STEP 2: Extract metadata (NO DB record creation here!)
        with st.spinner("Extracting metadata (30-60 seconds)..."):
            st.session_state["intake_progress_stage"] = "extract"
            result = api_extract_metadata(st.session_state["intake_file_path"])
            
            if "error" in result and "extraction" not in result:
                st.session_state["intake_error"] = f"Extraction failed: {result['error']}"
                return
            
            st.session_state["intake_extraction"] = result.get("extraction", {})
            st.session_state["intake_all_contracts"] = api_get_all_contracts()
            st.session_state["intake_progress_stage"] = "analyze"
            st.session_state["intake_step"] = 1
            st.rerun()


# ============================================================================
# QUESTION PANEL
# ============================================================================

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
        
        has_two_parties = isinstance(parties, list) and len(parties) == 2
        use_manual = st.checkbox("Enter parties manually", key="chk_parties_manual", 
                                  value=(not has_two_parties))
        
        if use_manual or not has_two_parties:
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
            st.markdown("*Which party is **ours**?*")
            our_party = st.radio("Select our party", parties, key="q_our_party", horizontal=True)

            # Auto-suggest counterparty but allow edit
            suggested_counterparty = parties[1] if our_party == parties[0] else parties[0]
            counterparty = st.text_input(
                "Counterparty",
                value=suggested_counterparty,
                key="q_counterparty_edit"
            )

            if st.button("Confirm Parties", key="btn_parties_select", type="primary",
                        disabled=not (our_party and counterparty)):
                confirmed["party"] = our_party
                confirmed["counterparty"] = counterparty
                st.session_state["intake_confirmed"] = confirmed
                st.session_state["intake_step"] += 1
                st.rerun()
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
        
        options = ["None - No related contract"]
        valid_contracts = []
        
        for c in all_contracts:
            if c is None or not isinstance(c, dict):
                continue
            
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
    """Save contract to database - called at END of intake flow."""
    st.session_state["intake_progress_stage"] = "complete"
    confirmed = st.session_state.get("intake_confirmed", {})

    # Validate required fields before save
    required = ["title", "contract_type", "party", "counterparty"]
    missing = [f for f in required if not confirmed.get(f)]

    if missing:
        st.session_state["intake_error"] = f"Missing required fields: {', '.join(missing)}"
        return

    # Build payload with ALL data
    # NOTE: 'purpose' removed - DB column doesn't exist
    payload = {
        "file_path": st.session_state.get("intake_file_path"),
        "title": confirmed.get("title"),
        "contract_type": confirmed.get("contract_type"),
        "party": confirmed.get("party"),
        "counterparty": confirmed.get("counterparty"),
        "orientation": confirmed.get("orientation"),
        "leverage": confirmed.get("leverage"),
        "related_contract_id": confirmed.get("related_contract_id"),
        "status": "active",
    }
    
    # Call /api/intake/store to CREATE the record (only call, at the end)
    result = api_store_contract(payload)
    
    if "error" in result:
        st.session_state["intake_error"] = f"Save failed: {result['error']}"
        return
    
    # Get the contract_id from response
    contract_id = result.get("contract_id") or result.get("id")
    st.session_state["intake_contract_id"] = contract_id
    st.session_state["intake_complete"] = True
    st.rerun()


def render_complete_summary():
    """Render summary in left column when complete."""
    confirmed = st.session_state.get("intake_confirmed", {})
    filename = st.session_state.get("intake_filename", "Unknown")
    
    st.markdown("**✅ Intake Complete**")
    st.caption(f"Uploaded: {filename}")
    
    st.markdown("---")
    st.write(f"**Title:** {confirmed.get('title', 'N/A')}")
    st.write(f"**Type:** {confirmed.get('contract_type', 'N/A')}")
    st.write(f"**Our Party:** {confirmed.get('party', 'N/A')}")


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
            st.write(f"✓ **{label}:** {display}")
        else:
            st.caption(f"○ {label}")
    
    if complete:
        st.markdown("---")
        contract_id = st.session_state.get("intake_contract_id")
        st.success(f"Saved as Contract #{contract_id}")


def render_progress_panel():
    """Render progress (right column)."""
    stage = st.session_state.get("intake_progress_stage", "idle")
    complete = st.session_state.get("intake_complete", False)
    contract_id = st.session_state.get("intake_contract_id") if complete else None
    
    render_system_health()
    render_intake_progress(stage=stage, contract_id=contract_id)
    
    if complete:
        st.markdown("---")
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
    if st.session_state.get("intake_error"):
        st.error(st.session_state["intake_error"])
        if st.button("↻ Start Over", type="primary"):
            for key in list(st.session_state.keys()):
                if key.startswith("intake_"):
                    del st.session_state[key]
            st.rerun()
    
    if not st.session_state.get("intake_file_id"):
        render_file_uploader()
    else:
        filename = st.session_state.get("intake_filename", "Unknown")
        contract_id = st.session_state.get("intake_contract_id")
        id_badge = f" (ID: {contract_id})" if contract_id else ""
        st.success(f"📄 {filename}{id_badge}")
    
    if st.session_state.get("intake_step", 0) > 0 or st.session_state.get("intake_complete"):
        col_left, col_mid, col_right = st.columns([1.3, 1.1, 0.9])
        
        with col_left:
            render_question_panel()
        
        with col_mid:
            render_confirmed_panel()
        
        with col_right:
            render_progress_panel()
