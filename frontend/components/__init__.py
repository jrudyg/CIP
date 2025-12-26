"""
CIP Frontend Components
Reusable UI components for contract intelligence
"""

from .contract_context import (
    init_contract_context,
    set_active_contract,
    get_active_contract,
    get_active_contract_data,
    clear_active_contract,
    render_active_contract_header,
    render_recent_contracts_widget
)

from .contract_detail import render_contract_detail

__all__ = [
    'init_contract_context',
    'set_active_contract',
    'get_active_contract',
    'get_active_contract_data',
    'clear_active_contract',
    'render_active_contract_header',
    'render_recent_contracts_widget',
    'render_contract_detail'
]
