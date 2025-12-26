import logging
import sys
from pathlib import Path

# --- Setup ---
sys.path.append(str(Path(__file__).parent.parent))
from frontend.pages import page_03_intelligent_intake as intake_page

# --- Logging Configuration ---
log_file = "C:\\Users\\jrudy\\CIP\\validation_sim.log"
logger = logging.getLogger("validation_sim")
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(logging.FileHandler(log_file, mode='w'))
logger.addHandler(logging.StreamHandler(sys.stdout))

# --- Mock Streamlit Session State ---
class MockSessionState(dict):
    def __init__(self, *args, **kwargs):
        super(MockSessionState, self).__init__(*args, **kwargs)
        self.__dict__ = self
# Replace the real st.session_state with our mock
intake_page.st.session_state = MockSessionState()

# --- Simulation Execution ---

def log_status(header):
    """Helper function to log the current validation status."""
    statuses, confirmed_count = intake_page.compute_validation_status()
    all_confirmed = confirmed_count == 6
    logger.info(f"--- {header} ---")
    logger.info(f"Completion: {confirmed_count}/6. Proceed Enabled: {all_confirmed}")
    for field, status in statuses.items():
        logger.info(f"  - {field.ljust(15)}: {status.value}")
    logger.info("")

if __name__ == "__main__":
    
    # --- 1. Initial State ---
    # Set up the initial state with some fields missing or needing review
    intake_page.init_validation_state()
    state = intake_page.st.session_state.validation_state
    state['title'] = ''             # Missing
    state['party'] = None           # Missing
    state['counterparty'] = None
    state['contract_type'] = None   # Missing
    state['orientation'] = None     # Missing
    state['purpose'] = 'Other'      # Missing (because other text is empty)
    state['purpose_other'] = ''
    state['leverage'] = None        # Needs Review
    log_status("Initial State")

    # --- 2. Prove Party -> Counterparty Auto-Resolve ---
    logger.info("ACTION: User selects 'Innovate LLC' as Our Party.")
    party_a, party_b = state['party_candidates']
    state['party'] = party_b # User selects Innovate LLC
    # Logic from UI: state.counterparty = party_b if selected_party == party_a else party_a
    state['counterparty'] = party_a if state['party'] == party_b else party_b
    log_status("Party Selected")

    # --- 3. Prove "Other" Text Enforcement ---
    logger.info("ACTION: User selects 'Other' for Contract Type, but does not fill the text.")
    state['contract_type'] = 'Other'
    state['contract_type_other'] = ''
    log_status("Contract Type 'Other' (Incomplete)")
    
    logger.info("ACTION: User fills the 'Specify other' text box.")
    state['contract_type_other'] = 'Custom Development Agreement'
    log_status("Contract Type 'Other' (Complete)")

    # --- 4. Prove Proceed Gate ---
    logger.info("ACTION: User completes all remaining fields.")
    state['title'] = 'Finalized Agreement for Custom Dev'
    state['orientation'] = 'Vendor'
    state['purpose'] = 'Professional Services'
    state['leverage'] = 'Medium'
    log_status("All Fields Confirmed")
