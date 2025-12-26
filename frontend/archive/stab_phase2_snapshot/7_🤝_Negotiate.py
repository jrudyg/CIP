"""
CIP - Plan Your Response Page
Strategic negotiation and response planning
v1.5: Zone layout retrofit
"""

import streamlit as st
import requests
import sys
sys.path.append('C:\\Users\\jrudy\\CIP\\frontend')
from ui_components import (
    page_header, section_header, metric_card,
    risk_badge, status_badge, toast_success,
    toast_warning, toast_error, toast_info, apply_spacing
)
from components.contract_context import (
    init_contract_context,
    get_active_contract,
    get_active_contract_data,
    render_active_contract_header,
    render_recent_contracts_widget,
    set_active_contract
)
from theme_system import apply_theme, inject_cip_logo
from zone_layout import zone_layout, check_system_health
from cip_components import action_bar

API_BASE = "http://localhost:5000/api"

st.set_page_config(page_title="Plan Your Response", page_icon="🤝", layout="wide")
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

# Fetch contracts from API
@st.cache_data(ttl=60)
def get_contracts():
    try:
        resp = requests.get(f"{API_BASE}/contracts", timeout=5)
        if resp.ok:
            data = resp.json()
            return data.get('contracts', [])
    except:
        pass
    return []

contracts = get_contracts()

# Auto-load active contract from context
active_id = get_active_contract()
active_data = get_active_contract_data()

# Session state
if 'selected_risk_idx' not in st.session_state:
    st.session_state.selected_risk_idx = 0
if 'response_status' not in st.session_state:
    st.session_state.response_status = {}  # {risk_idx: 'drafted'|'reviewed'|'sent'}
if 'response_notes' not in st.session_state:
    st.session_state.response_notes = {}  # {risk_idx: [notes]}
if 'risk_category_filter' not in st.session_state:
    st.session_state.risk_category_filter = "All"
if 'risk_type_filter' not in st.session_state:
    st.session_state.risk_type_filter = "All"

# Page header
page_header("🤝 Plan Your Response", "Strategic response planning and talking points")
render_active_contract_header()

# Sample risks for demo (would come from analysis)
sample_risks = [
    {"id": 1, "category": "Liability", "type": "Indemnification", "severity": "CRITICAL", "section": "4.2", "clause": "Vendor shall indemnify Customer for all claims arising from Vendor's negligence or willful misconduct."},
    {"id": 2, "category": "Payment", "type": "Late Fees", "severity": "IMPORTANT", "section": "3.5", "clause": "Late payments shall accrue interest at 18% per annum."},
    {"id": 3, "category": "Termination", "type": "For Convenience", "severity": "CRITICAL", "section": "5.1", "clause": "Customer may terminate this Agreement at any time with 30 days written notice."},
    {"id": 4, "category": "IP Rights", "type": "Work Product", "severity": "DEALBREAKER", "section": "6.3", "clause": "All work product created by Vendor shall be owned exclusively by Customer."},
    {"id": 5, "category": "Confidentiality", "type": "Duration", "severity": "STANDARD", "section": "7.2", "clause": "Confidentiality obligations shall survive for 5 years after termination."},
]


# Zone content functions
def z1_contract_and_filters():
    """Z1: Contract selector, risk category filter, risk type filter"""
    section_header("Select Contract & Filter", "📄")

    if active_id:
        st.info(f"📋 Active: #{active_id} - {active_data.get('title', 'Unknown')[:25]}")

    if contracts is not None and len(contracts) > 0:
        contract_options = {c['id']: f"#{c['id']} - {c.get('title', c.get('filename', 'Unknown'))[:20]}" for c in contracts}
        default_idx = 0
        if active_id and active_id in contract_options:
            default_idx = list(contract_options.keys()).index(active_id)

        selected_id = st.selectbox(
            "Contract",
            options=list(contract_options.keys()),
            format_func=lambda x: contract_options[x],
            index=default_idx,
            key="contract_select_z1"
        )
    else:
        st.warning("No contracts available")

    st.markdown("**Filters**")

    # Risk category filter
    categories = ["All"] + list(set(r['category'] for r in sample_risks))
    risk_category = st.selectbox("Category", categories, key="cat_filter_z1")
    st.session_state.risk_category_filter = risk_category

    # Risk type filter
    if risk_category == "All":
        types = ["All"] + list(set(r['type'] for r in sample_risks))
    else:
        types = ["All"] + list(set(r['type'] for r in sample_risks if r['category'] == risk_category))
    risk_type = st.selectbox("Type", types, key="type_filter_z1")
    st.session_state.risk_type_filter = risk_type


def z2_risk_summary():
    """Z2: Selected risk summary (severity, section reference, original clause)"""
    section_header("Risk Summary", "⚠️")

    # Filter risks
    filtered = sample_risks
    if st.session_state.risk_category_filter != "All":
        filtered = [r for r in filtered if r['category'] == st.session_state.risk_category_filter]
    if st.session_state.risk_type_filter != "All":
        filtered = [r for r in filtered if r['type'] == st.session_state.risk_type_filter]

    if filtered:
        idx = st.session_state.selected_risk_idx % len(filtered)
        risk = filtered[idx]

        severity_icon = {'DEALBREAKER': '🚫', 'CRITICAL': '🔴', 'IMPORTANT': '🟡', 'STANDARD': '🟢'}.get(risk['severity'], '⚪')

        st.markdown(f"**Severity:** {severity_icon} {risk['severity']}")
        st.markdown(f"**Section:** {risk['section']}")
        st.markdown(f"**Category:** {risk['category']}")

        st.markdown("**Original Clause:**")
        st.caption(risk['clause'][:150] + "..." if len(risk['clause']) > 150 else risk['clause'])

        # Risk selector
        st.markdown("---")
        if st.button("⏭️ Next Risk", use_container_width=True, key="next_risk_z2"):
            st.session_state.selected_risk_idx = (idx + 1) % len(filtered)
            st.rerun()
    else:
        st.info("No risks match filters")


def z3_response_status():
    """Z3: Response status tracker (drafted/reviewed/sent)"""
    section_header("Response Status", "📊")

    # Count statuses
    drafted = sum(1 for s in st.session_state.response_status.values() if s == 'drafted')
    reviewed = sum(1 for s in st.session_state.response_status.values() if s == 'reviewed')
    sent = sum(1 for s in st.session_state.response_status.values() if s == 'sent')
    total = len(sample_risks)

    st.metric("📝 Drafted", drafted)
    st.metric("✅ Reviewed", reviewed)
    st.metric("📤 Sent", sent)

    # Progress
    completed = drafted + reviewed + sent
    if total > 0:
        st.progress(completed / total)
        st.caption(f"{completed}/{total} responses")


def z4_response_detail():
    """Z4: Risk category + type detail, suggested response language, talking points"""
    section_header("Plan Your Response", "💬")

    # Get current risk
    filtered = sample_risks
    if st.session_state.risk_category_filter != "All":
        filtered = [r for r in filtered if r['category'] == st.session_state.risk_category_filter]
    if st.session_state.risk_type_filter != "All":
        filtered = [r for r in filtered if r['type'] == st.session_state.risk_type_filter]

    if filtered:
        idx = st.session_state.selected_risk_idx % len(filtered)
        risk = filtered[idx]

        st.markdown(f"### {risk['category']}: {risk['type']}")
        st.markdown(f"**Section {risk['section']}** | Severity: {risk['severity']}")

        # Original clause
        st.markdown("#### Original Clause")
        st.code(risk['clause'], language=None)

        # Suggested response
        st.markdown("#### Suggested Response Language")
        response_templates = {
            "Indemnification": "We propose limiting indemnification to direct damages caused by gross negligence, with a cap equal to fees paid in the prior 12 months.",
            "Late Fees": "We request reducing the late payment interest rate to 1.5% per month (18% annually is above market rate).",
            "For Convenience": "We propose mutual termination rights with 60 days notice, or termination for convenience only after the initial term.",
            "Work Product": "We propose that pre-existing IP remains with Vendor, with Customer receiving a perpetual license to use deliverables.",
            "Duration": "The 5-year confidentiality term is acceptable for trade secrets; we propose 3 years for general business information.",
        }
        suggested = response_templates.get(risk['type'], "Review this clause with legal counsel for appropriate response language.")
        st.info(suggested)

        # Editable response
        st.markdown("#### Your Response")
        response_text = st.text_area(
            "Edit response",
            value=suggested,
            height=100,
            key=f"response_{risk['id']}"
        )

        # Talking points
        st.markdown("#### Talking Points")
        talking_points = {
            "Indemnification": ["Industry standard caps at 12-month fees", "Uncapped indemnification creates uninsurable risk", "Focus on mutual indemnification for respective breaches"],
            "Late Fees": ["Market rate is typically 1-1.5% per month", "High interest rates may violate usury laws", "Propose grace period before interest accrues"],
            "For Convenience": ["One-sided termination creates planning uncertainty", "Request mutual termination rights", "Propose minimum term before convenience termination"],
            "Work Product": ["Pre-existing IP should remain with creator", "License approach protects both parties", "Customer gets perpetual use rights"],
            "Duration": ["5 years reasonable for trade secrets", "General business info should have shorter term", "Align with industry standards"],
        }
        points = talking_points.get(risk['type'], ["Consult legal counsel", "Review industry standards", "Consider business impact"])
        for point in points:
            st.markdown(f"• {point}")

        # Set status
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📝 Mark Drafted", use_container_width=True, key="draft_z4"):
                st.session_state.response_status[risk['id']] = 'drafted'
                toast_success("Marked as drafted")
                st.rerun()
        with col2:
            if st.button("✅ Mark Reviewed", use_container_width=True, key="review_z4"):
                st.session_state.response_status[risk['id']] = 'reviewed'
                toast_success("Marked as reviewed")
                st.rerun()
        with col3:
            if st.button("📤 Mark Sent", use_container_width=True, key="sent_z4"):
                st.session_state.response_status[risk['id']] = 'sent'
                toast_success("Marked as sent")
                st.rerun()
    else:
        st.info("Select a risk to plan your response")


def z5_response_history():
    """Z5: Response history for this risk, prior negotiation notes"""
    section_header("Response History", "📚")

    # Get current risk
    filtered = sample_risks
    if st.session_state.risk_category_filter != "All":
        filtered = [r for r in filtered if r['category'] == st.session_state.risk_category_filter]
    if st.session_state.risk_type_filter != "All":
        filtered = [r for r in filtered if r['type'] == st.session_state.risk_type_filter]

    if filtered:
        idx = st.session_state.selected_risk_idx % len(filtered)
        risk = filtered[idx]

        # Show notes for this risk
        notes = st.session_state.response_notes.get(risk['id'], [])

        if notes:
            for note in notes[-5:]:  # Show last 5
                st.markdown(f"**{note['date']}**")
                st.caption(note['text'])
                st.divider()
        else:
            st.info("No prior notes")

        # Add note
        st.markdown("**Add Note**")
        new_note = st.text_input("Note", key=f"note_input_{risk['id']}")
        if st.button("➕ Add", key=f"add_note_{risk['id']}", help="Add note", use_container_width=True):
            if new_note:
                if risk['id'] not in st.session_state.response_notes:
                    st.session_state.response_notes[risk['id']] = []
                from datetime import datetime
                st.session_state.response_notes[risk['id']].append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'text': new_note
                })
                toast_success("Note added")
                st.rerun()
    else:
        st.info("Select a risk to see history")


def z6_quick_actions():
    """Z6: Quick actions using action_bar: Copy, Export, Mark Complete"""
    section_header("Quick Actions", "⚡")

    clicked = action_bar([
        {"icon": "📋", "label": "Copy"},
        {"icon": "📤", "label": "Export"},
        {"icon": "✅", "label": "Complete"}
    ], key_prefix="response_action")

    if clicked == "Copy":
        toast_success("Response copied to clipboard")
    elif clicked == "Export":
        toast_info("Exporting responses...")
    elif clicked == "Complete":
        # Mark current risk as sent
        filtered = sample_risks
        if st.session_state.risk_category_filter != "All":
            filtered = [r for r in filtered if r['category'] == st.session_state.risk_category_filter]
        if filtered:
            idx = st.session_state.selected_risk_idx % len(filtered)
            risk = filtered[idx]
            st.session_state.response_status[risk['id']] = 'sent'
            toast_success("Marked as complete")
            st.rerun()

    # Summary stats
    st.markdown("---")
    st.markdown("**Response Stats**")
    total = len(sample_risks)
    completed = sum(1 for s in st.session_state.response_status.values() if s == 'sent')
    st.caption(f"Completed: {completed}/{total}")


def z7_extra():
    """Z7: Additional controls"""
    pass


# Render zone layout
zone_layout(
    z1=z1_contract_and_filters,
    z2=z2_risk_summary,
    z3=z3_response_status,
    z4=z4_response_detail,
    z5=z5_response_history,
    z6=z6_quick_actions,
    z7=z7_extra,
    z7_system_status=True,
    api_healthy=api_healthy,
    db_healthy=db_healthy,
    ai_healthy=ai_healthy
)

