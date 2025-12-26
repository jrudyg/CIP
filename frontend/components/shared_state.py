"""
P3.28 - Shared Session State Management
Provides a single, consistent way to access global state like active_contract_id.
"""

import streamlit as st

def get_active_contract_id():
    """
    Safely retrieves the active_contract_id from the session state.
    
    Returns:
        str | None: The active contract ID or None if not set.
    """
    return st.session_state.get('active_contract_id')

def set_active_contract_id(contract_id: str | None):
    """
    Sets the active_contract_id in the session state.
    
    Args:
        contract_id: The ID of the contract to set as active, or None to clear.
    """
    st.session_state.active_contract_id = contract_id
