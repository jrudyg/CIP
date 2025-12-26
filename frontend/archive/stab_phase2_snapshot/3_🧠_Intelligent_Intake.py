"""
CIP - Conversational Add a Contract (v1.5)
Smart contract intake with dialogue-driven metadata collection
v1.5: Zone layout retrofit
"""

import streamlit as st
import requests
from datetime import datetime
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from theme_system import apply_theme, inject_cip_logo
from zone_layout import zone_layout, check_system_health
from ui_components import page_header, section_header, apply_spacing

# Configuration
API_BASE = "http://localhost:5000/api"

st.set_page_config(
    page_title="Add a Contract",
    page_icon="🤖",
    layout="wide"
)
apply_theme()
apply_spacing()

# Inject centralized dark theme
from components.theme import inject_dark_theme
inject_dark_theme()

# Check system health
api_ok, db_ok, ai_ok = check_system_health()

# Sidebar
with st.sidebar:
    inject_cip_logo()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_intake_state():
    """Initialize session state for conversational intake"""
    if 'conv_intake' not in st.session_state:
        st.session_state.conv_intake = {
            'mode': 'upload',  # upload, conversation, confirm, complete, fallback
            'contract_id': None,
            'filename': None,
            'file_path': None,
            'findings': {},
            'confidence': {},
            'overall_confidence': 0,
            'questions': [],
            'current_question_idx': 0,
            'messages': [],  # Chat history
            'turn_count': 0,
            'max_turns': 5,
            'threshold': 90,
            'error': None
        }

def reset_intake():
    """Reset intake to initial state"""
    st.session_state.conv_intake = {
        'mode': 'upload',
        'contract_id': None,
        'filename': None,
        'file_path': None,
        'findings': {},
        'confidence': {},
        'overall_confidence': 0,
        'questions': [],
        'current_question_idx': 0,
        'messages': [],
        'turn_count': 0,
        'max_turns': 5,
        'threshold': 90,
        'error': None
    }

init_intake_state()

# ============================================================================
# API FUNCTIONS
# ============================================================================

def upload_contract(uploaded_file):
    """Upload contract and get contract_id"""
    try:
        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        resp = requests.post(f"{API_BASE}/upload-enhanced", files=files, timeout=30)
        if resp.ok:
            data = resp.json()
            return {
                'success': True,
                'contract_id': data.get('contract_id'),
                'file_path': data.get('file_path'),
                'filename': data.get('filename')
            }
        return {'success': False, 'error': resp.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_contract(contract_id):
    """Call /api/intake/analyze to get initial findings"""
    try:
        resp = requests.post(
            f"{API_BASE}/intake/analyze",
            json={'contract_id': contract_id},
            timeout=60
        )
        if resp.ok:
            return {'success': True, 'data': resp.json()}
        return {'success': False, 'error': resp.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_finding(contract_id, field, value, current_findings):
    """Call /api/intake/update to process user response"""
    try:
        resp = requests.post(
            f"{API_BASE}/intake/update",
            json={
                'contract_id': contract_id,
                'field': field,
                'value': value,
                'current_findings': current_findings
            },
            timeout=10
        )
        if resp.ok:
            return {'success': True, 'data': resp.json()}
        return {'success': False, 'error': resp.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def confirm_intake(contract_id, metadata):
    """Call /api/intake/confirm to save to database"""
    try:
        resp = requests.post(
            f"{API_BASE}/intake/confirm",
            json={
                'contract_id': contract_id,
                'confirmed_metadata': metadata
            },
            timeout=10
        )
        if resp.ok:
            return {'success': True, 'data': resp.json()}
        return {'success': False, 'error': resp.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_taxonomy():
    """Get taxonomy options for dropdowns"""
    try:
        resp = requests.get(f"{API_BASE}/intake/taxonomy", timeout=5)
        if resp.ok:
            return resp.json()
        return None
    except:
        return None

def get_pending_intakes():
    """Get contracts with incomplete intake"""
    try:
        resp = requests.get(f"{API_BASE}/intake/pending", timeout=5)
        if resp.ok:
            return resp.json()
        return {'pending': [], 'count': 0}
    except:
        return {'pending': [], 'count': 0}

def delete_contract(contract_id):
    """Delete a contract permanently"""
    try:
        resp = requests.post(f"{API_BASE}/contracts/{contract_id}/delete", timeout=5)
        return resp.json() if resp.ok else None
    except:
        return None

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_confidence_bar(confidence, threshold=90):
    """Render visual confidence progress bar"""
    color = "#10B981" if confidence >= threshold else "#F59E0B" if confidence >= 70 else "#EF4444"

    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: 500; color: #E2E8F0;">Overall Confidence</span>
            <span style="font-weight: 600; color: {color};">{confidence:.0f}%</span>
        </div>
        <div style="background: #334155; border-radius: 10px; height: 20px; overflow: hidden;">
            <div style="background: {color}; width: {min(confidence, 100)}%; height: 100%;
                        border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
        <div style="text-align: right; font-size: 12px; color: #94A3B8; margin-top: 3px;">
            Target: {threshold}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_dimension_confidence(confidence_dict):
    """Render confidence for each dimension"""
    dimensions = {
        'contract_type': ('Contract Type', '📄', 25),
        'our_entity': ('Our Entity', '🏢', 20),
        'party_relationship': ('Relationship', '🤝', 20),
        'clm_stage': ('CLM Stage', '📈', 20),
        'contract_purpose': ('Purpose', '🎯', 15)
    }

    cols = st.columns(5)
    for idx, (field, (label, icon, weight)) in enumerate(dimensions.items()):
        with cols[idx]:
            conf = confidence_dict.get(field, 0)
            color = "#10B981" if conf >= 90 else "#F59E0B" if conf >= 70 else "#EF4444"
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: #1E293B;">
                <div style="font-size: 20px;">{icon}</div>
                <div style="font-size: 11px; color: #94A3B8;">{label}</div>
                <div style="font-weight: 600; color: {color};">{conf:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

def render_cip_message(content, is_question=False):
    """Render a message from CIP"""
    icon = "🤖" if not is_question else "❓"
    st.markdown(f"""
    <div style="display: flex; margin-bottom: 15px;">
        <div style="font-size: 24px; margin-right: 10px;">{icon}</div>
        <div style="background: rgba(59, 130, 246, 0.15); color: #E2E8F0; padding: 12px 16px; border-radius: 12px;
                    border-top-left-radius: 4px; max-width: 80%; border: 1px solid rgba(59, 130, 246, 0.3);">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_user_response(content):
    """Render a user response"""
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
        <div style="background: rgba(16, 185, 129, 0.15); color: #E2E8F0; padding: 12px 16px; border-radius: 12px;
                    border-top-right-radius: 4px; max-width: 80%; border: 1px solid rgba(16, 185, 129, 0.3);">
            {content}
        </div>
        <div style="font-size: 24px; margin-left: 10px;">👤</div>
    </div>
    """, unsafe_allow_html=True)

def render_finding_card(field, value, confidence, editable=False):
    """Render a single finding with confidence"""
    field_labels = {
        'contract_type': 'Contract Type',
        'our_entity': 'Our Entity',
        'counterparty': 'Counterparty',
        'party_relationship': 'Relationship',
        'clm_stage': 'CLM Stage',
        'contract_purpose': 'Purpose',
        'title': 'Title',
        'parties': 'Parties Found'
    }

    label = field_labels.get(field, field.replace('_', ' ').title())
    conf_color = "#10B981" if confidence >= 90 else "#F59E0B" if confidence >= 70 else "#EF4444"

    display_value = value if value else "Unknown"
    if isinstance(value, list):
        display_value = ", ".join(value) if value else "None found"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center;
                padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.1);">
        <div>
            <span style="color: #94A3B8; font-size: 12px;">{label}</span><br/>
            <span style="font-weight: 500; color: #E2E8F0;">{display_value}</span>
        </div>
        <div style="background: {conf_color}; color: white; padding: 2px 8px;
                    border-radius: 12px; font-size: 12px;">
            {confidence:.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ZONE CONTENT FUNCTIONS
# ============================================================================

def z1_header():
    """Z1: Page header only"""
    page_header("🤖 Add a Contract", "Smart contract intake")


def z2_status_and_file():
    """Z2: Intake status + File info combined"""
    section_header("Status", "📊")
    state = st.session_state.conv_intake

    # Mode indicator
    if state['mode'] == 'upload':
        st.info("📤 Awaiting upload")
    elif state['mode'] == 'conversation':
        st.success("💬 Analyzing")
    elif state['mode'] == 'confirm':
        st.success("✅ Ready to confirm")
    elif state['mode'] == 'complete':
        st.success("🎉 Complete!")
    elif state['mode'] == 'fallback':
        st.warning("📝 Manual mode")

    # File info
    if state['filename']:
        st.markdown("---")
        st.markdown(f"**📄 {state['filename'][:20]}{'...' if len(state['filename']) > 20 else ''}**")
        if state['contract_id']:
            st.caption(f"ID: #{state['contract_id']}")


def z3_actions():
    """Z3: Quick actions"""
    section_header("Actions", "⚡")

    if st.button("🔄 Start Over", use_container_width=True, help="Start over"):
        reset_intake()
        st.rerun()

    state = st.session_state.conv_intake
    if state['mode'] == 'conversation':
        if st.button("📝 Manual Form", use_container_width=True, help="Switch to manual form"):
            st.session_state.conv_intake['mode'] = 'fallback'
            st.rerun()


def z4_main_workspace():
    """Z4: Main workspace - renders based on current mode"""
    state = st.session_state.conv_intake
    mode = state['mode']

    if mode == 'upload':
        render_upload_mode()
    elif mode == 'conversation':
        render_conversation_mode()
    elif mode == 'confirm':
        render_confirm_mode()
    elif mode == 'complete':
        render_complete_mode()
    elif mode == 'fallback':
        render_fallback_mode()


def z5_help():
    """Z5: How it works guide"""
    section_header("How It Works", "❓")
    st.markdown("""
    1. **Upload** contract
    2. **CIP analyzes** it
    3. **Answer** questions
    4. **Confirm** & save
    """)


def z7_footer():
    """Z7: Footer - system status only"""
    pass  # System status added by zone_layout


# ============================================================================
# MODE RENDERERS
# ============================================================================

def render_upload_mode():
    """Render upload mode UI"""

    # Check for pending intakes first
    pending = get_pending_intakes()
    if pending.get('count', 0) > 0:
        st.warning(f"⚠️ You have {pending['count']} incomplete intake(s)")

        with st.expander("📋 Pending Intakes - Resume or Delete", expanded=True):
            for contract in pending['pending']:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    filename = contract.get('filename', 'Unknown')
                    st.markdown(f"**{filename[:40]}**" + ("..." if len(filename) > 40 else ""))

                with col2:
                    created = contract.get('created_at', contract.get('upload_date', ''))
                    if created:
                        st.caption(f"Uploaded: {created[:16]}")

                with col3:
                    if st.button("▶️", key=f"resume_{contract['id']}", use_container_width=True, help="Resume intake"):
                        # Set up state to resume this contract
                        st.session_state.conv_intake['contract_id'] = contract['id']
                        st.session_state.conv_intake['filename'] = contract.get('filename', 'Unknown')
                        st.session_state.conv_intake['file_path'] = contract.get('filepath', '')

                        # Re-analyze the contract
                        with st.spinner("🤖 Re-analyzing contract..."):
                            analysis = analyze_contract(contract['id'])

                            if analysis['success']:
                                data = analysis['data']
                                st.session_state.conv_intake['findings'] = data.get('findings', {})
                                raw_conf = data.get('confidence', {})
                                st.session_state.conv_intake['confidence'] = {k: v * 100 for k, v in raw_conf.items()}
                                st.session_state.conv_intake['overall_confidence'] = data.get('overall_confidence', 0) * 100
                                st.session_state.conv_intake['questions'] = data.get('questions', [])
                                st.session_state.conv_intake['threshold'] = data.get('threshold', 0.90) * 100

                                st.session_state.conv_intake['messages'].append({
                                    'role': 'cip',
                                    'content': f"Resuming intake for **{contract.get('filename', 'Unknown')}**."
                                })

                                st.session_state.conv_intake['mode'] = 'conversation'
                                st.rerun()
                            else:
                                st.error(f"Analysis failed: {analysis['error']}")

                with col4:
                    if st.button("🗑️", key=f"delete_{contract['id']}", use_container_width=True, help="Delete permanently"):
                        st.session_state.confirm_delete_pending = contract['id']

                # Delete confirmation
                if st.session_state.get('confirm_delete_pending') == contract['id']:
                    st.error(f"⚠️ Delete **{contract.get('filename', 'Unknown')}** permanently?")
                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        if st.button("✓", key=f"confirm_del_{contract['id']}", type="primary", use_container_width=True, help="Confirm delete"):
                            result = delete_contract(contract['id'])
                            if result and result.get('status') == 'success':
                                st.success("Deleted")
                                st.session_state.confirm_delete_pending = None
                                st.rerun()
                            else:
                                st.error("Delete failed")
                    with dcol2:
                        if st.button("✕", key=f"cancel_del_{contract['id']}", use_container_width=True, help="Cancel"):
                            st.session_state.confirm_delete_pending = None
                            st.rerun()

                st.divider()

        st.markdown("---")

    section_header("Upload Contract", "📤")

    uploaded_file = st.file_uploader(
        "Drop your contract here",
        type=['docx', 'pdf'],
        help="Supported: Word (.docx) or PDF (.pdf)"
    )

    if uploaded_file:
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            with st.spinner("Uploading contract..."):
                result = upload_contract(uploaded_file)

                if result['success']:
                    st.session_state.conv_intake['contract_id'] = result['contract_id']
                    st.session_state.conv_intake['filename'] = result['filename']
                    st.session_state.conv_intake['file_path'] = result['file_path']

                    with st.spinner("🤖 CIP is reading the contract..."):
                        analysis = analyze_contract(result['contract_id'])

                        if analysis['success']:
                            data = analysis['data']
                            st.session_state.conv_intake['findings'] = data.get('findings', {})
                            raw_conf = data.get('confidence', {})
                            st.session_state.conv_intake['confidence'] = {k: v * 100 for k, v in raw_conf.items()}
                            st.session_state.conv_intake['overall_confidence'] = data.get('overall_confidence', 0) * 100
                            st.session_state.conv_intake['questions'] = data.get('questions', [])
                            st.session_state.conv_intake['threshold'] = data.get('threshold', 0.90) * 100

                            st.session_state.conv_intake['messages'].append({
                                'role': 'cip',
                                'content': f"I've analyzed **{result['filename']}**. Let me share what I found."
                            })

                            st.session_state.conv_intake['mode'] = 'conversation'
                            st.rerun()
                        else:
                            st.error(f"Analysis failed: {analysis['error']}")
                            st.session_state.conv_intake['mode'] = 'fallback'
                else:
                    st.error(f"Upload failed: {result['error']}")


def render_findings_grid(findings, confidence):
    """Render findings in a 3x2 grid (3 columns, 2 rows) - full display"""
    fields = [
        ('contract_type', 'Contract Type'),
        ('our_entity', 'Our Entity'),
        ('counterparty', 'Counterparty'),
        ('party_relationship', 'Relationship'),
        ('clm_stage', 'CLM Stage'),
        ('contract_purpose', 'Purpose')
    ]

    # Build 3x2 grid (3 cols, 2 rows)
    row1 = fields[:3]
    row2 = fields[3:]

    for row in [row1, row2]:
        cols = st.columns(3)
        for idx, (field, label) in enumerate(row):
            with cols[idx]:
                value = findings.get(field, '')
                conf = confidence.get(field, 0)
                conf_color = "#10B981" if conf >= 90 else "#F59E0B" if conf >= 70 else "#EF4444"

                display_val = value if value else "—"

                st.markdown(f"""
                <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.1);
                            border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase; margin-bottom: 4px;">{label}</div>
                    <div style="font-size: 14px; color: #E2E8F0; font-weight: 500; margin-bottom: 4px;">{display_val}</div>
                    <div style="font-size: 11px; color: {conf_color}; font-weight: 600;">{conf:.0f}% confidence</div>
                </div>
                """, unsafe_allow_html=True)


def render_conversation_mode():
    """Render conversation mode UI - full width in Z4"""
    state = st.session_state.conv_intake

    # Header with confidence bar
    col_title, col_conf = st.columns([2, 1])
    with col_title:
        section_header(f"Reviewing: {state['filename'][:40]}", "💬")
    with col_conf:
        render_confidence_bar(state['overall_confidence'], state['threshold'])

    st.markdown("---")

    # Main 3-column layout: Questions | Conversation | Findings (full Z4 width)
    col_questions, col_chat, col_findings = st.columns([20, 35, 45])

    # LEFT: Questions table
    with col_questions:
        st.markdown("#### ❓ Questions")

        questions = state['questions']
        q_idx = state['current_question_idx']

        if state['overall_confidence'] >= state['threshold']:
            st.success("✅ Target reached!")
            if st.button("📝 Review and Confirm", type="primary", use_container_width=True):
                st.session_state.conv_intake['mode'] = 'confirm'
                st.rerun()

        elif state['turn_count'] >= state['max_turns']:
            st.warning("⚠️ Max turns reached")
            if st.button("📝 Confirm Anyway", use_container_width=True):
                st.session_state.conv_intake['mode'] = 'confirm'
                st.rerun()
            if st.button("📝 Switch to Manual", use_container_width=True):
                st.session_state.conv_intake['mode'] = 'fallback'
                st.rerun()

        elif q_idx < len(questions):
            question = questions[q_idx]
            st.markdown(f"**{question['question']}**")

            options = question.get('options', [])
            field = question.get('field', '')

            # Radio button style selection
            selected = st.radio(
                "Select option:",
                options,
                key=f"question_{q_idx}",
                label_visibility="collapsed"
            )

            if st.button("✓ Submit", type="primary", use_container_width=True, key=f"submit_{q_idx}"):
                state['messages'].append({
                    'role': 'user',
                    'content': selected
                })

                result = update_finding(state['contract_id'], field, selected, state['findings'])

                if result['success']:
                    data = result['data']
                    state['findings'] = data.get('findings', state['findings'])
                    raw_conf = data.get('confidence', {})
                    state['confidence'] = {k: v * 100 for k, v in raw_conf.items()}
                    state['overall_confidence'] = data.get('overall_confidence', 0) * 100

                    state['messages'].append({
                        'role': 'cip',
                        'content': f"Got it - **{field.replace('_', ' ').title()}** set to **{selected}**."
                    })

                    state['current_question_idx'] += 1
                    state['turn_count'] += 1
                    st.rerun()
                else:
                    st.error(f"Update failed: {result['error']}")
        else:
            st.info("No more questions")
            if st.button("📝 Review and Confirm", type="primary", use_container_width=True):
                st.session_state.conv_intake['mode'] = 'confirm'
                st.rerun()

    # CENTER: Conversation history
    with col_chat:
        st.markdown("#### 💬 Conversation")

        # Use native Streamlit chat display
        chat_container = st.container(height=250)
        with chat_container:
            if state['messages']:
                for msg in state['messages'][-5:]:  # Show last 5 messages
                    if msg['role'] == 'cip':
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(msg['content'])
                    else:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(msg['content'])
            else:
                st.caption("No messages yet")

    # RIGHT: Findings grid
    with col_findings:
        st.markdown("#### 📋 Findings")
        render_findings_grid(state['findings'], state['confidence'])


def render_confirm_mode():
    """Render confirmation mode UI with dark theme"""
    state = st.session_state.conv_intake

    # Dark theme styled header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px;
                padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 28px; margin-right: 12px;">✅</span>
            <span style="font-size: 22px; font-weight: 600; color: #E2E8F0;">Confirm Contract Details</span>
        </div>
        <div style="display: flex; gap: 20px; color: #94A3B8;">
            <span>📄 <strong style="color: #E2E8F0;">{state['filename'][:50]}</strong></span>
            <span>📊 Confidence: <strong style="color: #10B981;">{state['overall_confidence']:.0f}%</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    taxonomy = get_taxonomy()

    with st.form("confirm_form"):
        # Section header styled - Core Information
        st.markdown("""
        <div style="background: #1E293B; border: 1px solid rgba(59, 130, 246, 0.3);
                    border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
            <span style="color: #3B82F6; font-size: 16px; font-weight: 600;">📋 Core Information</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        findings = state['findings']

        with col1:
            title = st.text_input(
                "Contract Title",
                value=findings.get('title', ''),
                placeholder="Enter contract title"
            )

            counterparty = st.text_input(
                "Counterparty",
                value=findings.get('counterparty', ''),
                placeholder="Other party's name"
            )

            # Fallback options if taxonomy is empty
            type_options = taxonomy.get('contract_types', []) if taxonomy else []
            if not type_options:
                type_options = ['NDA', 'MSA', 'SOW', 'SLA', 'LICENSE', 'AMENDMENT', 'OTHER']
            current_type = findings.get('contract_type', '')
            type_idx = type_options.index(current_type) if current_type in type_options else 0
            contract_type = st.selectbox("Contract Type", type_options, index=type_idx)

        with col2:
            our_entity = st.text_input(
                "Our Entity",
                value=findings.get('our_entity', ''),
                placeholder="Your company name"
            )

            rel_options = taxonomy.get('party_relationships', []) if taxonomy else []
            if not rel_options:
                rel_options = ['CUSTOMER', 'VENDOR', 'PARTNER', 'RESELLER', 'CONSULTANT']
            current_rel = findings.get('party_relationship', '')
            rel_idx = rel_options.index(current_rel) if current_rel in rel_options else 0
            relationship = st.selectbox("Our Relationship", rel_options, index=rel_idx)

            purpose_options = taxonomy.get('contract_purposes', []) if taxonomy else []
            if not purpose_options:
                purpose_options = ['SERVICES', 'PRODUCTS', 'LICENSING', 'PARTNERSHIP', 'CONFIDENTIALITY', 'OTHER']
            current_purpose = findings.get('contract_purpose', '')
            purpose_idx = purpose_options.index(current_purpose) if current_purpose in purpose_options else 0
            purpose = st.selectbox("Contract Purpose", purpose_options, index=purpose_idx)

        # Section header styled - CLM Stage & Analysis
        st.markdown("""
        <div style="background: #1E293B; border: 1px solid rgba(59, 130, 246, 0.3);
                    border-radius: 8px; padding: 12px 16px; margin: 20px 0 16px 0;">
            <span style="color: #3B82F6; font-size: 16px; font-weight: 600;">📈 CLM Stage & Analysis</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            stage_options = taxonomy.get('clm_stages', []) if taxonomy else []
            if not stage_options:
                stage_options = ['NEW CONTRACT', 'REVIEWING', 'NEGOTIATING', 'APPROVING', 'EXECUTING', 'IN_EFFECT']
            current_stage = findings.get('clm_stage', 'NEW CONTRACT')
            stage_idx = stage_options.index(current_stage) if current_stage in stage_options else 0
            clm_stage = st.selectbox("CLM Stage", stage_options, index=stage_idx)

            mode_options = taxonomy.get('analysis_modes', []) if taxonomy else []
            if not mode_options:
                mode_options = ['FULL', 'NDA_ONLY', 'COMPARISON']
            analysis_mode = st.selectbox("Analysis Mode", mode_options, index=0)

        with col2:
            position_options = ['customer', 'vendor', 'partner', 'landlord', 'tenant']
            position = st.selectbox("Our Position", position_options, index=0)

            leverage_options = ['strong', 'balanced', 'weak']
            leverage = st.selectbox("Negotiation Leverage", leverage_options, index=1)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        confirmed = st.checkbox("I confirm these details are correct")

        col1, col2 = st.columns(2)
        with col1:
            back_btn = st.form_submit_button("← Back to Conversation", use_container_width=True)
        with col2:
            confirm_btn = st.form_submit_button("✅ Save Contract", type="primary", use_container_width=True)

    if back_btn:
        st.session_state.conv_intake['mode'] = 'conversation'
        st.rerun()

    if confirm_btn:
        if not confirmed:
            st.warning("Please check the confirmation box")
        else:
            metadata = {
                'title': title,
                'counterparty': counterparty,
                'contract_type': contract_type,
                'our_entity': our_entity,
                'party_relationship': relationship,
                'contract_purpose': purpose,
                'clm_stage': clm_stage,
                'analysis_mode': analysis_mode,
                'position': position,
                'leverage': leverage
            }

            with st.spinner("Saving contract..."):
                result = confirm_intake(state['contract_id'], metadata)

                if result['success']:
                    st.session_state.conv_intake['mode'] = 'complete'
                    st.rerun()
                else:
                    st.error(f"Save failed: {result['error']}")


def render_complete_mode():
    """Render completion mode UI"""
    state = st.session_state.conv_intake

    section_header("Intake Complete!", "🎉")

    st.success(f"**{state['filename']}** has been added to your contract database.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Contract ID", state['contract_id'])
    with col2:
        st.metric("Confidence", f"{state['overall_confidence']:.0f}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤 Upload Another", type="primary", use_container_width=True):
            reset_intake()
            st.rerun()

    with col2:
        if st.button("📊 Go to Portfolio", use_container_width=True):
            st.switch_page("pages/2_📊_Contracts_Portfolio.py")


def render_fallback_mode():
    """Render manual fallback mode UI"""
    state = st.session_state.conv_intake

    section_header("Manual Intake Form", "📝")
    st.info("Fill in the contract details manually")

    taxonomy = get_taxonomy()

    with st.form("manual_form"):
        st.markdown("#### Contract Information")

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Contract Title *", placeholder="Master Service Agreement")
            counterparty = st.text_input("Counterparty *", placeholder="Acme Corporation")
            our_entity = st.text_input("Our Entity *", placeholder="Your Company Name")

            type_options = taxonomy.get('contract_types', ['NDA', 'MSA', 'SOW', 'Other']) if taxonomy else ['NDA', 'MSA', 'SOW', 'Other']
            contract_type = st.selectbox("Contract Type *", type_options)

        with col2:
            rel_options = taxonomy.get('party_relationships', ['BUYER', 'SELLER', 'PARTNER']) if taxonomy else ['BUYER', 'SELLER', 'PARTNER']
            relationship = st.selectbox("Our Relationship *", rel_options)

            purpose_options = taxonomy.get('contract_purposes', ['PROCUREMENT', 'SALES', 'PARTNERSHIP']) if taxonomy else ['PROCUREMENT', 'SALES', 'PARTNERSHIP']
            purpose = st.selectbox("Purpose *", purpose_options)

            stage_options = taxonomy.get('clm_stages', ['NEW CONTRACT', 'REVIEWING', 'NEGOTIATING']) if taxonomy else ['NEW CONTRACT', 'REVIEWING', 'NEGOTIATING']
            clm_stage = st.selectbox("CLM Stage", stage_options, index=0)

            position_options = ['customer', 'vendor', 'partner']
            position = st.selectbox("Our Position", position_options)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            cancel_btn = st.form_submit_button("← Cancel", use_container_width=True)
        with col2:
            save_btn = st.form_submit_button("✅ Save Contract", type="primary", use_container_width=True)

    if cancel_btn:
        if state['contract_id']:
            st.session_state.conv_intake['mode'] = 'conversation'
        else:
            reset_intake()
        st.rerun()

    if save_btn:
        if not title or not counterparty:
            st.warning("Please fill in required fields (Title, Counterparty)")
        else:
            metadata = {
                'title': title,
                'counterparty': counterparty,
                'contract_type': contract_type,
                'our_entity': our_entity,
                'party_relationship': relationship,
                'contract_purpose': purpose,
                'clm_stage': clm_stage,
                'position': position
            }

            if state['contract_id']:
                with st.spinner("Saving..."):
                    result = confirm_intake(state['contract_id'], metadata)
                    if result['success']:
                        st.session_state.conv_intake['mode'] = 'complete'
                        st.rerun()
                    else:
                        st.error(f"Save failed: {result['error']}")
            else:
                st.error("No contract uploaded. Please upload a file first.")


# ============================================================================
# RENDER ZONE LAYOUT
# ============================================================================

zone_layout(
    z1=z1_header,
    z2=z2_status_and_file,
    z3=z3_actions,
    z4=z4_main_workspace,
    z5=z5_help,
    z6=None,
    z7=z7_footer,
    z7_system_status=True,
    api_healthy=api_ok,
    db_healthy=db_ok,
    ai_healthy=ai_ok
)
