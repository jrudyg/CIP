import logging
import sys
from pathlib import Path
import time

# --- Setup ---
# Ensure the parent directory is on the path to allow `from components import ...`
sys.path.insert(0, str(Path(__file__).parent.parent))
from frontend.components import contract_selector, shared_state

# --- Logging Configuration ---
log_file = "C:\\Users\\jrudy\\CIP\\selector_sim.log"
# Get the root logger and configure it. This will capture logs from all modules.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True # Force re-configuration
)
logger = logging.getLogger("selector_sim")

# --- Mock Streamlit Objects ---
# A more robust mock to handle attribute access and prevent warnings
class MockSessionState(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
    def __setattr__(self, key, value):
        logger.info(f"SESSION_STATE: Set st.session_state['{key}'] = '{value}'")
        super().__setattr__(key, value)

class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()
        # Pre-populate the session state dict to avoid attribute errors on first access
        self.session_state['global_contract_selector'] = None
        self.session_state['active_contract_id'] = None

    def subheader(self, text): pass
    def warning(self, text): logger.warning(f"UI: {text}")
    def rerun(self): logger.info("--> st.rerun() called")
    
    @staticmethod
    def cache_data(ttl=None):
        def decorator(func):
            return func
        return decorator

    def selectbox(self, label, options, index, format_func, key, on_change, label_visibility):
        # Simulate the user selecting an option on the first run
        selected_option = self.session_state.get(key)
        if selected_option is None: # First run
             selected_option = options[3] # Corresponds to "Project Alpha NDA"
        
        self.session_state[key] = selected_option
        on_change()
        return selected_option

# Replace the real `st` module with our mock
mock_st = MockStreamlit()
contract_selector.st = mock_st
shared_state.st = mock_st

# --- Mock Downstream API Call ---
def get_latest_analysis_snapshot(contract_id):
    logger.info(f"API_CALL: Downstream call initiated for contract_id='{contract_id}'")
    logger.info(f"API_CALL: GET /contracts/{contract_id}/analysis/latest")
    return {'status': 'ok', 'created_at': '2025-12-15T14:30:00Z'}

# --- Simulation Execution ---
if __name__ == "__main__":
    
    logger.info("--- P3.28 SIMULATION START ---")
    logger.info("Shared state is initially empty.\n")

    # --- 1. Simulate navigating to the Portfolio page ---
    logger.info(">>> USER NAVIGATES TO: Contracts Portfolio <<<")
    active_id = contract_selector.render_contract_selector()
    logger.info(f"Portfolio Page: Component returned active_id: {active_id}\n")

    # --- 2. Simulate navigating to the Risk Analysis page ---
    logger.info(">>> USER NAVIGATES TO: Risk Analysis <<<")
    active_id = contract_selector.render_contract_selector()
    logger.info(f"Risk Analysis Page: Component sees active_id: {active_id}")
    if active_id:
        get_latest_analysis_snapshot(active_id)
    logger.info("Risk Analysis Page: Actions complete.\n")

    # --- 3. Simulate navigating to the Redline Reviews page ---
    logger.info(">>> USER NAVIGATES TO: Redline Reviews <<<")
    active_id = contract_selector.render_contract_selector()
    logger.info(f"Redline Reviews Page: Component sees active_id: {active_id}")
    if active_id:
        logger.info("Redline Reviews Page: Main content enabled.")
    logger.info("Redline Reviews Page: Actions complete.\n")

    logger.info("--- P3.28 SIMULATION COMPLETE ---")
