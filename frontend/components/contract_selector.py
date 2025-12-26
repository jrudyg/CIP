"""
P3.28 - Global Contract Selector Component
"""

import streamlit as st
import logging
import requests
from components.shared_state import get_active_contract_id, set_active_contract_id

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# ============================================================================
# API DATA SOURCE
# ============================================================================
API_BASE = "http://localhost:5000/api"

@st.cache_data(ttl=10)
def _get_contracts_from_backend():
    """Fetch all contracts from the backend API."""
    logger.info("ContractSelector: Fetching contracts from backend API...")
    try:
        resp = requests.get(f"{API_BASE}/contracts", timeout=5)
        if resp.ok:
            data = resp.json()
            contracts = data.get("contracts", []) if isinstance(data, dict) else data
            return [
                {
                    "id": c.get("id"),
                    "display_id": str(c.get("id", "")),
                    "title": c.get("title") or c.get("filename", "Untitled"),
                    "counterparty": c.get("counterparty", "Unknown")
                }
                for c in contracts
            ]
        else:
            logger.warning(f"ContractSelector: API returned {resp.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"ContractSelector: API error - {e}")
        return []

# ============================================================================
# SELECTOR COMPONENT
# ============================================================================

def render_contract_selector():
    """
    Renders a searchable, session-state-aware contract selector dropdown.
    """
    st.subheader("Active Contract")

    contracts = _get_contracts_from_backend()

    option_to_id_map = {
        f"#{c["display_id"]} - {c["title"]} - {c["counterparty"]}": c["id"]
        for c in contracts
    }
    id_to_option_map = {v: k for k, v in option_to_id_map.items()}

    current_id = get_active_contract_id()
    current_selection_formatted = id_to_option_map.get(current_id)

    # Determine the index for the selectbox
    options = [None] + list(option_to_id_map.keys())
    try:
        index = options.index(current_selection_formatted)
    except ValueError:
        index = 0 # Default to "Select a contract..." if current_id is not in options

    # When a user makes a selection, Streamlit writes the selected *option* to the key.
    # We use a callback to process this selection and update our canonical state.
    def on_change():
        selected_option = st.session_state.global_contract_selector
        newly_selected_id = option_to_id_map.get(selected_option)

        if get_active_contract_id() != newly_selected_id:
            set_active_contract_id(newly_selected_id)
            logger.info(f"ContractSelector: active_contract_id set to '{newly_selected_id}' via callback.")
            # No rerun here, as on_change handles it before the next script run.

    selected_option = st.selectbox(
        label="Select a contract to work on. Type to filter.",
        options=options,
        index=index,
        format_func=lambda x: "Select a contract..." if x is None else x,
        key="global_contract_selector", # Use a dedicated key for the widget
        on_change=on_change,
        label_visibility="collapsed"
    )

    # --- Display feedback ---
    active_id = get_active_contract_id()
    if active_id:
        return active_id
    else:
        st.warning("Select a contract to continue.")
        return None
