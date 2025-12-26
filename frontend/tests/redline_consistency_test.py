from pathlib import Path
import importlib.util
from typing import Any, Dict


def _load_validator():
    root = Path(__file__).resolve().parents[1]
    validator_path = root / "validators" / "redline_consistency.py"
    if not validator_path.exists():
        raise SystemExit(f"Validator not found: {validator_path}")

    spec = importlib.util.spec_from_file_location("redline_consistency", validator_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Failed to load redline_consistency module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _sample_redline() -> Dict[str, Any]:
    return {
        "inserted_count": 1,
        "removed_count": 1,
        "modified_count": 1,
        "clause_changes": [
            {
                "clause_id": "1.1",
                "section_title": "Definitions",
                "change_type": "inserted",
                "impact": "low",
                "position_shift": "favors_customer",
                "focus_first": False,
            },
            {
                "clause_id": "5.2",
                "section_title": "Payment Terms",
                "change_type": "modified",
                "impact": "high",
                "position_shift": "favors_counterparty",
                "focus_first": True,
            },
            {
                "clause_id": "7.4",
                "section_title": "Limitation of Liability",
                "change_type": "removed",
                "impact": "medium",
                "position_shift": "balanced",
                "focus_first": False,
            },
        ],
    }


def main() -> None:
    module = _load_validator()
    validate = getattr(module, "validate_redline_consistency", None)
    if validate is None:
        raise SystemExit("validate_redline_consistency() not found in validator module")

    redline = _sample_redline()
    errors = validate(redline)
    if errors:
        raise SystemExit("Redline consistency validation failed: " + "; ".join(errors))

    print("Redline consistency test passed: Z2/Z3 invariants hold for sample data.")


if __name__ == "__main__":
    main()
