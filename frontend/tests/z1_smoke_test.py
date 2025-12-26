"""
Z1 Smoke Test - Document Selector Zone
Verifies z1_document_selector exists and can be imported.
"""

import sys
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

page_path = root / "pages" / "5_📝_Redline_Reviews.py"
assert page_path.exists(), f"Missing: {page_path}"

spec = importlib.util.spec_from_file_location("zpage", page_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert hasattr(mod, "z1_document_selector"), "z1_document_selector() missing"

print("Z1 smoke test passed: module imported, z1_document_selector() exists.")
