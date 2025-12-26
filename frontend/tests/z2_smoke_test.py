from pathlib import Path
import importlib.util


def main() -> None:
    # Assume this file lives in C:\\Users\\jrudy\\CIP\\frontend\\tests
    root = Path(__file__).resolve().parents[1]
    page_path = root / "pages" / "5_📝_Redline_Reviews.py"

    if not page_path.exists():
        raise SystemExit(f"Z2 smoke test failed: {page_path} not found")

    spec = importlib.util.spec_from_file_location("z2_page", page_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Z2 smoke test failed: cannot load page module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    if not hasattr(module, "z2_change_summary"):
        raise SystemExit("Z2 smoke test failed: z2_change_summary() not found")

    print("Z2 smoke test passed: module imported, z2_change_summary() exists.")


if __name__ == "__main__":
    main()
