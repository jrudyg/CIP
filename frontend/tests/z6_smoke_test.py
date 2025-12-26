from pathlib import Path
import importlib.util


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    page_path = root / "pages" / "5_📝_Redline_Reviews.py"

    if not page_path.exists():
        raise SystemExit(f"Z6 smoke test failed: {page_path} not found")

    spec = importlib.util.spec_from_file_location("redline_page", page_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Z6 smoke test failed: cannot create module spec")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    if not hasattr(module, "z6_scenario_zone"):
        raise SystemExit("Z6 smoke test failed: z6_scenario_zone() not found")

    print("Z6 smoke test passed: module imported, z6_scenario_zone() exists.")


if __name__ == "__main__":
    main()
