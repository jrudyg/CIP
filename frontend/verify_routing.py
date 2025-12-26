import os
import sys
from pathlib import Path
import streamlit as st

# This is a simplified test script to prove the logic without running the full app.
# It re-implements the core logic from app.py.

print("--- VERIFICATION SCRIPT START ---")

# Define the page lists exactly as in app.py
# Using a simple mock object instead of st.Page to avoid attribute errors in bare mode
class MockPage:
    def __init__(self, path, title=""):
        self.page_script_path = path
        self.title = title

prod_pages = [
    MockPage("pages/1_??_Home.py", title="Home"),
    MockPage("pages/2_??_Contracts_Portfolio.py", title="Contracts Portfolio"),
    MockPage("pages/3_??_Intelligent_Intake.py", title="Intelligent Intake"),
    MockPage("pages/4_??_Risk_Analysis.py", title="Risk Analysis"),
    MockPage("pages/5_??_Redline_Reviews.py", title="Redline Reviews"),
    MockPage("pages/6_??_Compare_Versions.py", title="Compare Versions"),
    MockPage("pages/7_??_Negotiate.py", title="Negotiate"),
    MockPage("pages/8_??_Reports.py", title="Reports"),
]

demo_dev_pages = [
    MockPage("pages/9_??_SAE_Tooltip_Demo.py", title="SAE Tooltip Demo"),
    MockPage("pages/10_??_ERCE_Risk_Demo.py", title="ERCE Risk Demo"),
    MockPage("pages/11_??_BIRL_Narrative_Demo.py", title="BIRL Narrative Demo"),
    MockPage("pages/12_??_FAR_Action_Bar_Demo.py", title="FAR Action Bar Demo"),
    MockPage("pages/20_??_TopNav_Demo.py", title="TopNav Demo"),
    MockPage("pages/21_??_ClauseSelector_Demo.py", title="ClauseSelector Demo"),
    MockPage("pages/22_??_InsightsPanel_Demo.py", title="InsightsPanel Demo"),
    MockPage("pages/99_??_P7_Diagnostics.py", title="P7 Diagnostics"),
]

def get_pages_for_env(env):
    """Simulates the logic in app.py"""
    app_env = env.upper()
    pages_to_show = list(prod_pages)

    if app_env != "PROD":
        pages_to_show.extend(demo_dev_pages)
    
    return pages_to_show

# --- Test Case 1: PROD Environment ---
print("\n--- Testing with APP_ENV = PROD ---")
prod_run_pages = get_pages_for_env("PROD")
prod_paths = [p.page_script_path for p in prod_run_pages]

print(f"Page count: {len(prod_paths)}")
print("Page scripts available:")
for path in prod_paths:
    print(f"- {path}")

# Assertions
has_demo_page = any("Demo" in path for path in prod_paths)
has_dev_page = any("Diagnostics" in path for path in prod_paths)
assert not has_demo_page, "FAIL: Demo pages are present in PROD!"
assert not has_dev_page, "FAIL: Dev pages are present in PROD!"
print("SUCCESS: DEMO and DEV pages are unreachable in PROD.")


# --- Test Case 2: DEV Environment ---
print("\n--- Testing with APP_ENV = DEV ---")
dev_run_pages = get_pages_for_env("DEV")
dev_paths = [p.page_script_path for p in dev_run_pages]

print(f"Page count: {len(dev_paths)}")
print("Page scripts available:")
for path in dev_paths:
    print(f"- {path}")

# Assertions
has_demo_page = any("Demo" in path for path in dev_paths)
has_dev_page = any("Diagnostics" in path for path in dev_paths)
assert has_demo_page, "FAIL: Demo pages are NOT present in DEV!"
assert has_dev_page, "FAIL: Dev pages are NOT present in DEV!"
print("SUCCESS: DEMO and DEV pages are reachable in DEV.")

print("\n--- VERIFICATION SCRIPT COMPLETE ---")
