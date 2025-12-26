import logging
import time
import sys
from pathlib import Path
import streamlit as st

# --- Setup to import from the pages directory ---
sys.path.append(str(Path(__file__).parent.parent))
from frontend.pages import page_03_intelligent_intake as intake_page

# --- Logging Configuration ---
log_file = "C:\\Users\\jrudy\\CIP\\intake_run.log"
# Ensure the logger is configured only once
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='w'), # Overwrite log each run
            logging.StreamHandler(sys.stdout)
        ]
    )

# --- Mock Streamlit Session State ---
class MockSessionState(dict):
    def __init__(self, *args, **kwargs):
        super(MockSessionState, self).__init__(*args, **kwargs)
        self.__dict__ = self
    def __getattr__(self, key):
        return self.get(key)

st.session_state = MockSessionState()

def mock_rerun():
    # In a real app, this would rerun the script. Here we just log it.
    logging.info("--> st.rerun() called")

# Replace Streamlit's native objects with our mocks
intake_page.st.session_state = st.session_state
intake_page.st.rerun = mock_rerun
intake_page.logger = logging.getLogger()


# --- Simulation Execution ---
if __name__ == "__main__":
    logging.info("--- Starting Intake Simulation ---")
    
    # Initialize the state as the real app would
    intake_page.init_intake_state()
    
    # Get the state object
    state = intake_page.st.session_state.conv_intake
    
    # Define a mock uploaded file
    class MockUploadedFile:
        name = "TestContract.docx"
    
    # Call the handler function which contains the simulation logic
    intake_page.handle_uploaded_file(MockUploadedFile(), state)
    
    logging.info("--- Intake Simulation Complete ---")
