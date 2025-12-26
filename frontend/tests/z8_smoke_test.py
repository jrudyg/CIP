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

assert hasattr(mod, "z8_cross_document_zone"), "z8_cross_document_zone() missing"

print("Z8 smoke test passed: module imported, z8_cross_document_zone() exists.")
