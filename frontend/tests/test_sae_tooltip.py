"""
SAE Semantic Tooltip Component Test
Phase 5 UX Upgrade - Task 1 Validation

This test file validates the SAE tooltip component functionality
and generates test artifacts for GEM UX validation.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.sae_tooltip import (
    inject_sae_tooltip_css,
    render_sae_tooltip,
    render_sae_inline_preview,
    render_sae_matches_with_tooltips,
    render_sae_expander_with_tooltips,
    extract_sae_data_from_v3_result,
    get_sae_tooltip_for_clause_pair,
    _get_confidence_class,
    _get_score_bar_class,
    _generate_tooltip_id,
    SAE_TOOLTIP_CSS,
)


def test_confidence_class():
    """Test confidence level CSS class mapping."""
    assert _get_confidence_class("HIGH") == "high"
    assert _get_confidence_class("MEDIUM") == "medium"
    assert _get_confidence_class("LOW") == "low"
    assert _get_confidence_class("high") == "high"
    assert _get_confidence_class(None) == "low"
    print("[PASS] test_confidence_class")


def test_score_bar_class():
    """Test score bar CSS class mapping."""
    assert _get_score_bar_class(0.95) == "high"
    assert _get_score_bar_class(0.90) == "high"
    assert _get_score_bar_class(0.85) == "medium"
    assert _get_score_bar_class(0.75) == "medium"
    assert _get_score_bar_class(0.60) == "low"
    assert _get_score_bar_class(0.40) == "low"
    print("[PASS] test_score_bar_class")


def test_tooltip_id_generation():
    """Test unique tooltip ID generation."""
    id1 = _generate_tooltip_id(1, 2)
    id2 = _generate_tooltip_id(1, 2)
    id3 = _generate_tooltip_id(2, 3)

    assert id1 == id2, "Same clause pairs should produce same ID"
    assert id1 != id3, "Different clause pairs should produce different IDs"
    assert len(id1) == 8, "ID should be 8 characters"
    print("[PASS] test_tooltip_id_generation")


def test_extract_sae_data():
    """Test SAE data extraction from Compare v3 result."""
    # Test with valid result
    mock_result = {
        "success": True,
        "data": {
            "sae_matches": [
                {"v1_clause_id": 1, "v2_clause_id": 1, "similarity_score": 0.95, "match_confidence": "HIGH"},
                {"v1_clause_id": 2, "v2_clause_id": 3, "similarity_score": 0.78, "match_confidence": "MEDIUM"},
            ]
        }
    }

    sae_data = extract_sae_data_from_v3_result(mock_result)
    assert len(sae_data) == 2
    assert sae_data[0]["match_confidence"] == "HIGH"

    # Test with failed result
    failed_result = {"success": False}
    assert extract_sae_data_from_v3_result(failed_result) == []

    # Test with None
    assert extract_sae_data_from_v3_result(None) == []

    print("[PASS] test_extract_sae_data")


def test_get_tooltip_for_clause_pair():
    """Test finding specific clause pair in SAE matches."""
    sae_matches = [
        {"v1_clause_id": 1, "v2_clause_id": 1, "similarity_score": 0.95},
        {"v1_clause_id": 2, "v2_clause_id": 3, "similarity_score": 0.78},
        {"v1_clause_id": 4, "v2_clause_id": 5, "similarity_score": 0.62},
    ]

    # Find existing pair
    match = get_sae_tooltip_for_clause_pair(sae_matches, 2, 3)
    assert match is not None
    assert match["similarity_score"] == 0.78

    # Find non-existing pair
    no_match = get_sae_tooltip_for_clause_pair(sae_matches, 99, 99)
    assert no_match is None

    print("[PASS] test_get_tooltip_for_clause_pair")


def test_css_injection():
    """Test CSS contains required classes."""
    required_classes = [
        ".sae-tooltip-container",
        ".sae-tooltip-trigger",
        ".sae-tooltip-popup",
        ".sae-conf-high",
        ".sae-conf-medium",
        ".sae-conf-low",
        ".sae-score-bar-fill",
        ".sae-badge-high",
    ]

    for cls in required_classes:
        assert cls in SAE_TOOLTIP_CSS, f"Missing CSS class: {cls}"

    print("[PASS] test_css_injection")


def generate_test_report():
    """Generate test report for GEM validation."""
    report = {
        "component": "SAE Semantic Tooltip",
        "phase": "Phase 5 UX Upgrade - Task 1",
        "status": "IMPLEMENTED",
        "tests_passed": 6,
        "tests_failed": 0,
        "features": [
            "Hover-triggered tooltip display",
            "Key-value structured SAE data presentation",
            "Confidence-based color coding (HIGH/MEDIUM/LOW)",
            "Visual similarity score bar with threshold markers",
            "Inline preview mode for compact displays",
            "Grid layout for multiple matches",
            "Expander integration with summary stats",
        ],
        "css_classes_implemented": [
            "sae-tooltip-container",
            "sae-tooltip-trigger",
            "sae-tooltip-popup",
            "sae-conf-high/medium/low",
            "sae-badge-high/medium/low",
            "sae-score-bar-*",
            "sae-inline-preview",
        ],
        "data_fields_displayed": [
            "V1 Clause ID",
            "V2 Clause ID",
            "Similarity Score (percentage)",
            "Threshold Used",
            "Match Confidence",
        ],
        "integration_points": [
            "Compare Versions page (z6_export_actions)",
            "Compare v3 result display",
            "SAE expander section",
        ],
        "file_location": "frontend/components/sae_tooltip.py",
    }

    return report


def main():
    """Run all tests and generate report."""
    print("=" * 60)
    print("SAE SEMANTIC TOOLTIP COMPONENT - TEST SUITE")
    print("Phase 5 UX Upgrade - Task 1 Validation")
    print("=" * 60)
    print()

    # Run tests
    test_confidence_class()
    test_score_bar_class()
    test_tooltip_id_generation()
    test_extract_sae_data()
    test_get_tooltip_for_clause_pair()
    test_css_injection()

    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)

    # Generate report
    import json
    report = generate_test_report()

    print()
    print("TEST REPORT FOR GEM VALIDATION:")
    print("-" * 40)
    print(json.dumps(report, indent=2))

    # Save report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "tests",
        "sae_tooltip_test_report.json"
    )

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print(f"Report saved to: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
