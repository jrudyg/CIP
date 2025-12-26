from __future__ import annotations

from typing import Any, Dict, List


def validate_redline_consistency(redline_result: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if redline_result is None:
        errors.append("redline_result is None.")
        return errors

    clause_changes = redline_result.get("clause_changes") or redline_result.get("clauses") or []
    if not isinstance(clause_changes, list):
        errors.append("clause_changes/clauses must be a list.")
        return errors

    if not clause_changes:
        return errors

    required_fields = ("clause_id", "section_title", "change_type")
    valid_change_types = {"inserted", "removed", "modified"}
    valid_impacts = {"low", "medium", "high"}
    valid_position_shifts = {"favors_customer", "balanced", "favors_counterparty"}

    focus_first_count = 0
    inserted_count = removed_count = modified_count = 0

    for idx, clause in enumerate(clause_changes):
        if not isinstance(clause, dict):
            errors.append(f"Clause #{idx} is not a dict.")
            continue

        for field in required_fields:
            if field not in clause:
                errors.append(f"Clause #{idx} missing required field: {field}")

        change_type = str(clause.get("change_type", "")).lower()
        if change_type not in valid_change_types:
            errors.append(f"Clause #{idx} has invalid change_type: {change_type!r}")
        else:
            if change_type == "inserted":
                inserted_count += 1
            elif change_type == "removed":
                removed_count += 1
            elif change_type == "modified":
                modified_count += 1

        impact = str(clause.get("impact", "medium")).lower()
        if impact not in valid_impacts:
            errors.append(f"Clause #{idx} has invalid impact: {impact!r}")

        position_shift = str(clause.get("position_shift", "balanced"))
        if position_shift not in valid_position_shifts:
            errors.append(f"Clause #{idx} has invalid position_shift: {position_shift!r}")

        if clause.get("focus_first"):
            focus_first_count += 1

    if focus_first_count > 1:
        errors.append(
            f"Multiple focus_first clauses detected (count={focus_first_count}); "
            "Z2/Z3 expect at most one."
        )

    summary_inserted = redline_result.get("inserted_count")
    summary_removed = redline_result.get("removed_count")
    summary_modified = redline_result.get("modified_count")

    def _check_count(name: str, summary_value: Any, derived_value: int) -> None:
        if summary_value is None:
            return
        try:
            summary_int = int(summary_value)
        except (TypeError, ValueError):
            errors.append(f"Summary {name} is not an int: {summary_value!r}")
            return
        if summary_int != derived_value:
            errors.append(
                f"Summary {name}={summary_int} does not match clause_changes-derived "
                f"value {derived_value}."
            )

    _check_count("inserted_count", summary_inserted, inserted_count)
    _check_count("removed_count", summary_removed, removed_count)
    _check_count("modified_count", summary_modified, modified_count)

    return errors
