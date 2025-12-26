import logging
import time
import sys

# --- Logging Configuration ---
log_file = "C:\\Users\\jrudy\\CIP\\intake_run.log"
# Use a unique logger name to avoid conflicts
logger = logging.getLogger("intake_simulation")
logger.setLevel(logging.INFO)
# Remove existing handlers to prevent duplicate logs
if logger.hasHandlers():
    logger.handlers.clear()
# Add new handlers
logger.addHandler(logging.FileHandler(log_file, mode='w'))
logger.addHandler(logging.StreamHandler(sys.stdout))

# --- Mock Streamlit Session State ---
class MockSessionState(dict):
    def __init__(self, *args, **kwargs):
        super(MockSessionState, self).__init__(*args, **kwargs)
        self.__dict__ = self
    def __getattr__(self, key):
        return self.get(key)

st_session_state = MockSessionState()

def mock_rerun():
    logger.info("--> st.rerun() called")

# --- Logic copied from 3_??_Intelligent_Intake.py for simulation ---

INTAKE_PROGRESS_STAGES = {
    'upload': {'percent': 10, 'label': 'Uploading document...'},
    'parse': {'percent': 30, 'label': 'Parsing document structure...'},
    'extract': {'percent': 50, 'label': 'Extracting clauses...'},
    'metadata': {'percent': 75, 'label': 'Detecting metadata...'},
    'findings': {'percent': 90, 'label': 'Generating findings...'},
    'save': {'percent': 100, 'label': 'Saving contract...'}
}

def init_intake_state():
    """Initialize session state for conversational intake v2"""
    st_session_state['conv_intake'] = {
        'progress_percent': 0,
        'progress_label': '',
        'show_progress': False,
        'mode': 'upload',
    }

def handle_contract_run_simulation(state):
    """Simulates the full intake process for the log generation."""

    # --- Upload Stage (Sticks at 10%) ---
    state['show_progress'] = True
    state['progress_percent'] = INTAKE_PROGRESS_STAGES['upload']['percent']
    state['progress_label'] = INTAKE_PROGRESS_STAGES['upload']['label']
    logger.info(f"Progress Update: {{'percent': {state['progress_percent']}, 'label': '{state['progress_label']}'}}")
    mock_rerun()

    # Simulate the delay where it's "stuck" at 10% before analysis begins
    logger.info("(Simulating backend analysis delay...)")
    time.sleep(2) 

    # --- Analysis Stages ---
    for stage_name in ['parse', 'extract', 'metadata', 'findings']:
        stage_info = INTAKE_PROGRESS_STAGES[stage_name]
        state['progress_percent'] = stage_info['percent']
        state['progress_label'] = stage_info['label']
        logger.info(f"Progress Update: {{'percent': {state['progress_percent']}, 'label': '{state['progress_label']}'}}")
        time.sleep(0.5)
    
    # --- Completion Stage ---
    state['progress_percent'] = INTAKE_PROGRESS_STAGES['save']['percent']
    state['progress_label'] = INTAKE_PROGRESS_STAGES['save']['label']
    logger.info(f"Progress Update: {{'percent': {state['progress_percent']}, 'label': '{state['progress_label']}'}}")
    time.sleep(1)

    state['show_progress'] = False
    state['mode'] = 'complete'
    logger.info("Progress Complete: Intake finished.")

# --- Simulation Execution ---
if __name__ == "__main__":
    logger.info("--- Starting Intake Simulation ---")
    init_intake_state()
    state = st_session_state.conv_intake
    handle_contract_run_simulation(state)
    logger.info("--- Intake Simulation Complete ---")
