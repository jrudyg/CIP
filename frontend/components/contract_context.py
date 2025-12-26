"""
Contract Context Management
Maintains active contract state across pages
"""
import streamlit as st
import requests
from typing import Optional, Dict, Any

API_BASE = "http://localhost:5000/api"


def init_contract_context():
    """Initialize active contract in session state and handle deep links"""
    if 'active_contract' not in st.session_state:
        st.session_state.active_contract = None
    if 'active_contract_data' not in st.session_state:
        st.session_state.active_contract_data = None
    if 'recent_contracts' not in st.session_state:
        st.session_state.recent_contracts = []  # List of (id, title) tuples

    # Check for contract ID in URL query parameters (deep linking)
    query_params = st.query_params
    if 'contract' in query_params:
        try:
            contract_id = int(query_params['contract'])
            # Only set if different from current to avoid infinite loop
            if st.session_state.active_contract != contract_id:
                set_active_contract(contract_id)
        except (ValueError, TypeError):
            pass  # Invalid contract ID in URL, ignore


def set_active_contract(contract_id: int, update_url: bool = True):
    """Set the active contract for cross-page context"""
    st.session_state.active_contract = contract_id
    try:
        response = requests.get(f"{API_BASE}/contract/{contract_id}", timeout=5)
        if response.ok:
            data = response.json()
            contract_data = data.get('contract') if 'contract' in data else data
            st.session_state.active_contract_data = contract_data

            # Add to recent contracts list (max 5, no duplicates)
            if contract_data:
                title = contract_data.get('title', f'Contract #{contract_id}')
                _add_to_recent(contract_id, title)

            # Update URL with contract parameter for deep linking
            if update_url:
                st.query_params['contract'] = str(contract_id)
    except:
        st.session_state.active_contract_data = None


def _add_to_recent(contract_id: int, title: str):
    """Add contract to recent list (internal helper)"""
    recent = st.session_state.get('recent_contracts', [])

    # Remove if already in list
    recent = [(cid, t) for cid, t in recent if cid != contract_id]

    # Add to front
    recent.insert(0, (contract_id, title))

    # Keep only last 5
    st.session_state.recent_contracts = recent[:5]


def get_active_contract() -> Optional[int]:
    """Get current active contract ID"""
    return st.session_state.get('active_contract')


def get_active_contract_data() -> Optional[Dict[str, Any]]:
    """Get cached active contract data"""
    return st.session_state.get('active_contract_data')


def clear_active_contract():
    """Clear active contract selection and URL parameter"""
    st.session_state.active_contract = None
    st.session_state.active_contract_data = None
    # Clear contract parameter from URL
    if 'contract' in st.query_params:
        del st.query_params['contract']


def render_active_contract_header():
    """Display active contract indicator in header with blue banner"""
    contract = get_active_contract_data()
    if contract:
        # Blue banner styling
        st.markdown("""
        <style>
        .active-contract-banner {
            background: linear-gradient(90deg, #1E40AF 0%, #3B82F6 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .active-contract-banner .contract-info {
            font-size: 14px;
        }
        .active-contract-banner .contract-title {
            font-weight: bold;
            font-size: 16px;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns([5, 1])
        with cols[0]:
            st.info(f"""
            🎯 **Active Contract:** {contract.get('title', 'Unknown')}
            **Counterparty:** {contract.get('counterparty', 'N/A')} |
            **Status:** {contract.get('status', 'N/A')} |
            **Risk:** {contract.get('risk_level', 'N/A')}
            """)
        with cols[1]:
            if st.button("✕", key="clear_active_contract", type="secondary", help="Clear active contract", use_container_width=True):
                clear_active_contract()
                st.rerun()


def render_recent_contracts_widget():
    """Render recent contracts widget for sidebar"""
    recent = st.session_state.get('recent_contracts', [])

    if recent:
        st.markdown("### 🕐 Recent Contracts")
        for contract_id, title in recent:
            # Truncate long titles (handle None)
            title = title or f"Contract {contract_id}"
            display_title = title if len(title) <= 30 else title[:27] + "..."
            if st.button(f"#{contract_id}: {display_title}", key=f"recent_{contract_id}", use_container_width=True):
                set_active_contract(contract_id)
                st.rerun()
        st.divider()
    else:
        st.markdown("### 🕐 Recent Contracts")
        st.caption("No recent contracts")
