"""
CIP - Shared UI Components
Reusable components for contract selection, API calls, and common patterns
"""

import streamlit as st
import requests
from typing import Optional, Dict, List, Tuple, Any
from ui_components import toast_success


# ============================================================================
# TRUST MICROCOPY (Phase 4C)
# ============================================================================

TRUST_MESSAGES = {
    "trust.stale_snapshot": "Contract analysis is more than 7 days old. Results may not reflect recent changes.",
    "trust.ai_degraded": "AI service is experiencing delays. Analysis may take longer than usual.",
    "trust.ai_unavailable": "AI service is temporarily unavailable. Some features may be limited.",
    "trust.high_risk": "This is a high-risk contract. Review results carefully before proceeding.",
}

# API Configuration
API_BASE_URL = "http://127.0.0.1:5000"


def fetch_contracts(filter_status: Optional[str] = None) -> Tuple[List[Dict], Optional[str]]:
    """
    Fetch contracts from the API.

    Args:
        filter_status: Optional status filter (e.g., 'analyzed', 'active')

    Returns:
        Tuple of (contracts list, error message or None)
    """
    try:
        url = f"{API_BASE_URL}/api/contracts"
        if filter_status:
            url += f"?status={filter_status}"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get('contracts', []), None
        else:
            return [], f"Failed to fetch contracts: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return [], f"Cannot connect to backend API: {str(e)}"


def build_contract_options(
    contracts: List[Dict],
    include_version: bool = False,
    label_format: str = "default"
) -> Dict[str, int]:
    """
    Build a dictionary mapping display labels to contract IDs.

    Args:
        contracts: List of contract dictionaries
        include_version: Whether to include version number in label
        label_format: Label format ('default', 'compare', 'short')

    Returns:
        Dictionary mapping label strings to contract IDs
    """
    options = {}

    for contract in contracts:
        contract_id = contract['id']
        filename = contract['filename']
        contract_type = contract.get('contract_type', 'Unknown') or 'Unknown'
        upload_date = str(contract.get('upload_date', ''))[:10]
        version = contract.get('version_number', 1)

        if label_format == "compare":
            label = f"ID {contract_id}: {filename} (v{version}) - {contract_type} - {upload_date}"
        elif label_format == "short":
            label = f"ID {contract_id}: {filename}"
        else:  # default
            label = f"ID {contract_id}: {filename} ({contract_type}) - {upload_date}"

        options[label] = contract_id

    return options


def contract_selector(
    label: str = "Select a contract",
    key: str = "contract_selector",
    filter_status: Optional[str] = None,
    include_version: bool = False,
    min_contracts: int = 1,
    label_format: str = "default",
    show_details: bool = True
) -> Tuple[Optional[int], Optional[Dict], List[Dict]]:
    """
    Render a contract selection dropdown with optional details display.

    Args:
        label: Label for the selectbox
        key: Unique key for the selectbox widget
        filter_status: Optional status filter
        include_version: Whether to show version in label
        min_contracts: Minimum contracts required (shows warning if less)
        label_format: Label format ('default', 'compare', 'short')
        show_details: Whether to show contract details metrics

    Returns:
        Tuple of (selected_contract_id, selected_contract_dict, all_contracts)
        Returns (None, None, []) if error or not enough contracts
    """
    contracts, error = fetch_contracts(filter_status)

    if error:
        st.error(f"⚠️ {error}")
        st.info("Make sure the backend is running: `python backend/api.py`")
        return None, None, []

    if len(contracts) < min_contracts:
        if min_contracts == 1:
            st.warning("⚠️ No contracts uploaded yet. Go to the Intake page to add a contract.")
        else:
            st.warning(f"⚠️ Need at least {min_contracts} contracts. Upload more contracts first.")
        return None, None, contracts

    # Build options
    options = build_contract_options(contracts, include_version, label_format)

    # Render selectbox
    selected_label = st.selectbox(
        label,
        options=list(options.keys()),
        key=key
    )

    selected_id = options[selected_label]
    selected_contract = next((c for c in contracts if c['id'] == selected_id), None)

    # Show details if requested
    if show_details and selected_contract:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Contract ID", selected_id)
        with col2:
            st.metric("Type", selected_contract.get('contract_type') or 'N/A')
        with col3:
            st.metric("Position", selected_contract.get('position') or 'N/A')
        with col4:
            st.metric("Status", selected_contract.get('status') or 'N/A')

    return selected_id, selected_contract, contracts


def dual_contract_selector(
    label1: str = "Select first contract",
    label2: str = "Select second contract",
    key1: str = "v1_selector",
    key2: str = "v2_selector",
    filter_status: Optional[str] = None,
    validate_different: bool = True
) -> Tuple[Optional[int], Optional[int], Optional[Dict], Optional[Dict], List[Dict]]:
    """
    Render two contract selection dropdowns side by side (for comparison).

    Args:
        label1: Label for first selectbox
        label2: Label for second selectbox
        key1: Key for first selectbox
        key2: Key for second selectbox
        filter_status: Optional status filter
        validate_different: Whether to require different contracts

    Returns:
        Tuple of (id1, id2, contract1, contract2, all_contracts)
        Returns (None, None, None, None, []) if error
    """
    contracts, error = fetch_contracts(filter_status)

    if error:
        st.error(f"⚠️ {error}")
        st.info("Make sure the backend is running: `python backend/api.py`")
        return None, None, None, None, []

    if len(contracts) < 2:
        st.warning("⚠️ Need at least 2 contracts to compare. Upload more contracts first.")
        return None, None, None, None, contracts

    # Build options with version info for comparison
    options = build_contract_options(contracts, include_version=True, label_format="compare")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Version 1 (Original)")
        v1_label = st.selectbox(label1, options=list(options.keys()), key=key1)
        v1_id = options[v1_label]

    with col2:
        st.markdown("#### Version 2 (Revised)")
        v2_label = st.selectbox(label2, options=list(options.keys()), key=key2)
        v2_id = options[v2_label]

    # Validate different selection
    if validate_different and v1_id == v2_id:
        st.error("⚠️ Please select two different contracts to compare")
        return None, None, None, None, contracts

    v1_contract = next((c for c in contracts if c['id'] == v1_id), None)
    v2_contract = next((c for c in contracts if c['id'] == v2_id), None)

    return v1_id, v2_id, v1_contract, v2_contract, contracts


def api_call_with_spinner(
    endpoint: str,
    method: str = "POST",
    data: Optional[Dict] = None,
    spinner_message: str = "Processing...",
    success_message: Optional[str] = None,
    timeout: int = 300,
    result_key: Optional[str] = None
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Make an API call with spinner and error handling.
    RA-ERR-10054: Returns structured error info, never raw exception strings.

    Args:
        endpoint: API endpoint (e.g., '/api/analyze')
        method: HTTP method ('GET' or 'POST')
        data: JSON data for POST requests
        spinner_message: Message to show in spinner
        success_message: Optional success toast message
        timeout: Request timeout in seconds
        result_key: Key to extract from response (e.g., 'analysis')

    Returns:
        Tuple of (result_data, error_dict_or_message)
        - On success: (result_data, None)
        - On error: (None, error_dict) where error_dict has:
          - error_category: "network_error" | "auth_error" | "payload_error" | "internal_error"
          - error_message_key: GEM copy key for user message
    """
    url = f"{API_BASE_URL}{endpoint}"

    with st.spinner(spinner_message):
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)

            if response.status_code == 200:
                result = response.json()

                # RA-ERR-10054: Check if API returned an error structure
                if result.get('success') is False:
                    return None, {
                        'error_category': result.get('error_category', 'internal_error'),
                        'error_message_key': result.get('error_message_key', 'analyze.internal_failure')
                    }

                if result_key:
                    result = result.get(result_key)

                if success_message:
                    toast_success(success_message)

                return result, None
            else:
                # RA-ERR-10054: Check for structured error in response
                try:
                    error_data = response.json()
                    if 'error_category' in error_data:
                        return None, {
                            'error_category': error_data.get('error_category'),
                            'error_message_key': error_data.get('error_message_key')
                        }
                except Exception:
                    pass

                # Fallback: classify HTTP status code
                if response.status_code in [401, 403]:
                    return None, {
                        'error_category': 'auth_error',
                        'error_message_key': 'analyze.auth_failure'
                    }
                elif response.status_code in [400, 413]:
                    return None, {
                        'error_category': 'payload_error',
                        'error_message_key': 'analyze.payload_failure'
                    }
                else:
                    return None, {
                        'error_category': 'internal_error',
                        'error_message_key': 'analyze.internal_failure'
                    }

        except requests.exceptions.Timeout:
            # RA-ERR-10054: Timeout is a network error
            return None, {
                'error_category': 'network_error',
                'error_message_key': 'analyze.network_failure'
            }
        except requests.exceptions.ConnectionError:
            # RA-ERR-10054: Connection errors (includes ConnectionResetError)
            return None, {
                'error_category': 'network_error',
                'error_message_key': 'analyze.network_failure'
            }
        except requests.exceptions.RequestException:
            # RA-ERR-10054: Other request errors
            return None, {
                'error_category': 'network_error',
                'error_message_key': 'analyze.network_failure'
            }
        except Exception:
            # RA-ERR-10054: Catch-all - never expose raw exception
            return None, {
                'error_category': 'internal_error',
                'error_message_key': 'analyze.internal_failure'
            }


def run_analysis_workflow(
    contract_id: int,
    analyzing_key: str = "analyzing",
    result_key: str = "analysis_result",
    endpoint: str = "/api/analyze",
    spinner_msg: str = "🔄 Analyzing contract... This may take 30-90 seconds...",
    success_msg: str = "Analysis complete!",
    timeout: int = 300,
    extra_data: Optional[Dict] = None
) -> bool:
    """
    Standard analysis workflow with session state management.

    Args:
        contract_id: ID of contract to analyze
        analyzing_key: Session state key for analyzing flag
        result_key: Session state key for result storage
        endpoint: API endpoint to call
        spinner_msg: Spinner message
        success_msg: Success toast message
        timeout: Request timeout
        extra_data: Additional data to include in request

    Returns:
        True if analysis was triggered and completed/failed, False otherwise
    """
    if not st.session_state.get(analyzing_key, False):
        return False

    data = {'contract_id': contract_id}
    if extra_data:
        data.update(extra_data)

    result, error = api_call_with_spinner(
        endpoint=endpoint,
        method="POST",
        data=data,
        spinner_message=spinner_msg,
        success_message=success_msg,
        timeout=timeout,
        result_key="analysis" if "analysis" not in endpoint else None
    )

    if error:
        st.error(f"❌ {error}")
        st.session_state[analyzing_key] = False
        return True

    st.session_state[result_key] = result
    st.session_state[analyzing_key] = False
    st.rerun()

    return True


# ============================================================================
# TRUST BANNER RENDERING (Phase 4C)
# ============================================================================

def render_trust_banner(trust: Optional[Dict[str, Any]]) -> None:
    """
    Render TRUST advisory banner inline.

    FROZEN SPEC:
    - Renders INLINE (no Z1 toasts, no Z7 integration)
    - Evaluates IMMEDIATELY on button click (before API call)
    - NEVER blocks the backend call
    - Dismiss is non-persistent (session only)

    Args:
        trust: TrustContext as dict, or None
    """
    # No trust context or clear status - no banner
    if not trust or trust.get("advisory_level") == "clear":
        return

    # Check if user dismissed the banner this session
    if st.session_state.get("_dismiss_trust_banner", False):
        return

    # Get messages from microcopy dictionary
    message_keys = trust.get("message_keys", [])
    messages = [TRUST_MESSAGES.get(key, "") for key in message_keys if TRUST_MESSAGES.get(key)]

    if not messages:
        return

    # Render inline banner with dismiss capability
    banner_id = f"trust_banner_{id(trust)}"

    st.markdown(
        f"""
        <style>
        .trust-advisory-banner {{
            background: linear-gradient(135deg, #FFC107 0%, #FFB300 100%);
            padding: 14px 18px;
            border-radius: 8px;
            border: 1px solid #d29b00;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            animation: trustFadeIn 0.3s ease-out;
        }}
        .trust-advisory-banner-content {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
        }}
        .trust-advisory-text {{
            color: #5D4E00;
            font-size: 0.95rem;
            line-height: 1.5;
            flex: 1;
        }}
        .trust-advisory-label {{
            font-weight: 600;
            color: #3D3200;
        }}
        @keyframes trustFadeIn {{
            from {{ opacity: 0; transform: translateY(-8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
        <div class="trust-advisory-banner">
            <div class="trust-advisory-banner-content">
                <div class="trust-advisory-text">
                    <span class="trust-advisory-label">Advisory:</span> {'; '.join(messages)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Dismiss button (non-persistent - session only)
    if st.button("Dismiss Advisory", key=f"dismiss_{banner_id}", type="secondary"):
        st.session_state["_dismiss_trust_banner"] = True
        st.rerun()


def clear_trust_banner_dismissal() -> None:
    """
    Clear the trust banner dismissal state.

    Call this when starting a new operation to allow
    the banner to show again if applicable.
    """
    if "_dismiss_trust_banner" in st.session_state:
        del st.session_state["_dismiss_trust_banner"]


# ============================================================================
# GEM ERROR CARD (Phase 4C)
# ============================================================================

def render_error_card(
    error_info: Dict[str, Any],
    module_name: str = "Operation"
) -> None:
    """
    Render GEM-compliant error card.

    Args:
        error_info: Dict with error_category and error_message_key
        module_name: Display name for the module
    """
    # Error message lookup
    error_messages = {
        "compare.network_failure": "We're having trouble reaching the analysis service. Please check your connection and try again.",
        "compare.auth_failure": "Authentication failed. Please verify your API key is configured correctly.",
        "compare.payload_failure": "The contract documents are too large to compare. Try with smaller files.",
        "compare.internal_failure": "Something went wrong during comparison. Please try again in a moment.",
        "analyze.network_failure": "We're having trouble reaching the analysis service. Please check your connection and try again.",
        "analyze.auth_failure": "Authentication failed. Please verify your API key is configured correctly.",
        "analyze.payload_failure": "The document is too large to analyze. Try with a smaller file.",
        "analyze.internal_failure": "Something went wrong during analysis. Please try again in a moment.",
    }

    error_key = error_info.get('error_message_key', 'analyze.internal_failure')
    error_message = error_messages.get(error_key, "An unexpected error occurred. Please try again.")

    st.markdown("""
    <style>
    .gem-error-card {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
        animation: fadeIn 0.3s ease-in-out;
    }
    .gem-error-title {
        color: #dc2626;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .gem-error-body {
        color: #7f1d1d;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="gem-error-card">
        <div class="gem-error-title">{module_name} Failed</div>
        <div class="gem-error-body">{error_message}</div>
    </div>
    """, unsafe_allow_html=True)
