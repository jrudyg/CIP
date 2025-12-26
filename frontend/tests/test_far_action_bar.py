"""
FAR Action Bar Component Test
Phase 5 UX Upgrade - Task 4 Validation

This test file validates the FAR Action Bar component functionality
and generates test artifacts for GEM UX validation.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.far_action_bar import (
    FAR_SEVERITY_LEVELS,
    FAR_ACTION_TYPES,
    FAR_ACTION_BAR_CSS,
    _get_severity_config,
    _count_gaps_by_severity,
    render_far_summary_badges,
    render_far_gap_card,
    extract_far_data_from_v3_result,
    get_far_summary_stats,
    should_show_action_bar,
)


def test_severity_levels_defined():
    """Test all severity levels are properly defined."""
    required_levels = ["CRITICAL", "HIGH", "MODERATE"]

    for level in required_levels:
        assert level in FAR_SEVERITY_LEVELS, f"Missing severity level: {level}"

        config = FAR_SEVERITY_LEVELS[level]
        assert "icon" in config, f"Missing icon for {level}"
        assert "label" in config, f"Missing label for {level}"
        assert "color" in config, f"Missing color for {level}"
        assert "bg_color" in config, f"Missing bg_color for {level}"
        assert "border_color" in config, f"Missing border_color for {level}"
        assert "description" in config, f"Missing description for {level}"
        assert "css_class" in config, f"Missing css_class for {level}"

    print("[PASS] test_severity_levels_defined")


def test_action_types_defined():
    """Test all action types are properly defined."""
    required_actions = ["RESOLVE", "ESCALATE", "DEFER", "NEGOTIATE", "EXPORT"]

    for action in required_actions:
        assert action in FAR_ACTION_TYPES, f"Missing action type: {action}"

        config = FAR_ACTION_TYPES[action]
        assert "icon" in config, f"Missing icon for {action}"
        assert "label" in config, f"Missing label for {action}"
        assert "description" in config, f"Missing description for {action}"
        assert "color" in config, f"Missing color for {action}"

    print("[PASS] test_action_types_defined")


def test_severity_config():
    """Test severity configuration retrieval."""
    critical_config = _get_severity_config("CRITICAL")
    assert critical_config["icon"] == "🔴"
    assert critical_config["color"] == "#DC2626"

    high_config = _get_severity_config("HIGH")
    assert high_config["icon"] == "🟠"

    moderate_config = _get_severity_config("MODERATE")
    assert moderate_config["icon"] == "🟡"

    # Test fallback
    unknown_config = _get_severity_config("UNKNOWN")
    assert unknown_config["icon"] == "🟡"  # Falls back to MODERATE

    print("[PASS] test_severity_config")


def test_count_gaps_by_severity():
    """Test gap counting by severity."""
    mock_gaps = [
        {"severity": "CRITICAL"},
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "MODERATE"},
    ]

    counts = _count_gaps_by_severity(mock_gaps)

    assert counts["CRITICAL"] == 2
    assert counts["HIGH"] == 3
    assert counts["MODERATE"] == 1

    # Test empty list
    empty_counts = _count_gaps_by_severity([])
    assert empty_counts["CRITICAL"] == 0
    assert empty_counts["HIGH"] == 0
    assert empty_counts["MODERATE"] == 0

    print("[PASS] test_count_gaps_by_severity")


def test_summary_badges_html():
    """Test summary badges HTML generation."""
    mock_gaps = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "MODERATE"},
    ]

    badges_html = render_far_summary_badges(mock_gaps)

    assert "far-summary-badges" in badges_html
    assert "far-summary-badge critical" in badges_html
    assert "1 Critical" in badges_html
    assert "2 High" in badges_html
    assert "1 Moderate" in badges_html

    print("[PASS] test_summary_badges_html")


def test_gap_card_html():
    """Test gap card HTML generation."""
    card_html = render_far_gap_card(
        gap_type="Liability Cap",
        severity="CRITICAL",
        upstream_value="$5M cap",
        downstream_value="No cap",
        recommendation="Add liability cap",
    )

    assert "far-gap-card" in card_html
    assert "critical" in card_html
    assert "Liability Cap" in card_html
    assert "$5M cap" in card_html
    assert "No cap" in card_html
    assert "Add liability cap" in card_html

    print("[PASS] test_gap_card_html")


def test_extract_far_data():
    """Test FAR data extraction from Compare v3 result."""
    # Test with valid result
    mock_result = {
        "success": True,
        "data": {
            "flowdown_gaps": [
                {
                    "gap_type": "Insurance",
                    "severity": "HIGH",
                    "upstream_value": "$2M",
                    "downstream_value": "$500K",
                    "recommendation": "Increase coverage",
                },
                {
                    "gap_type": "Liability",
                    "severity": "CRITICAL",
                    "upstream_value": "Capped",
                    "downstream_value": "Uncapped",
                    "recommendation": "Add cap",
                },
            ]
        }
    }

    far_data = extract_far_data_from_v3_result(mock_result)
    assert len(far_data) == 2
    assert far_data[0]["gap_type"] == "Insurance"
    assert far_data[1]["severity"] == "CRITICAL"

    # Test with failed result
    failed_result = {"success": False}
    assert extract_far_data_from_v3_result(failed_result) == []

    # Test with None
    assert extract_far_data_from_v3_result(None) == []

    # Test with missing data key
    missing_data = {"success": True}
    assert extract_far_data_from_v3_result(missing_data) == []

    print("[PASS] test_extract_far_data")


def test_summary_stats():
    """Test FAR summary statistics calculation."""
    mock_gaps = [
        {"gap_type": "Insurance", "severity": "CRITICAL"},
        {"gap_type": "Liability", "severity": "CRITICAL"},
        {"gap_type": "IP Rights", "severity": "HIGH"},
        {"gap_type": "Notice Period", "severity": "MODERATE"},
        {"gap_type": "Insurance", "severity": "HIGH"},
    ]

    stats = get_far_summary_stats(mock_gaps)

    assert stats["total_gaps"] == 5
    assert stats["critical_count"] == 2
    assert stats["high_count"] == 2
    assert stats["moderate_count"] == 1
    assert stats["has_critical"] is True
    assert stats["gap_types"]["Insurance"] == 2
    assert stats["gap_types"]["Liability"] == 1

    # Test empty gaps
    empty_stats = get_far_summary_stats([])
    assert empty_stats["total_gaps"] == 0
    assert empty_stats["critical_count"] == 0
    assert empty_stats["has_critical"] is False
    assert empty_stats["gap_types"] == {}

    print("[PASS] test_summary_stats")


def test_should_show_action_bar():
    """Test action bar visibility determination."""
    # Should show for critical gaps
    critical_gaps = [{"severity": "CRITICAL"}]
    assert should_show_action_bar(critical_gaps) is True

    # Should show for high gaps
    high_gaps = [{"severity": "HIGH"}]
    assert should_show_action_bar(high_gaps) is True

    # Should NOT show for moderate only
    moderate_gaps = [{"severity": "MODERATE"}, {"severity": "MODERATE"}]
    assert should_show_action_bar(moderate_gaps) is False

    # Should NOT show for empty
    assert should_show_action_bar([]) is False

    print("[PASS] test_should_show_action_bar")


def test_css_classes_defined():
    """Test CSS contains all required classes."""
    required_classes = [
        ".far-action-bar",
        ".far-bar-header",
        ".far-summary-badges",
        ".far-summary-badge",
        ".far-summary-badge.critical",
        ".far-summary-badge.high",
        ".far-summary-badge.moderate",
        ".far-action-btn",
        ".far-action-btn.primary",
        ".far-action-btn.secondary",
        ".far-details-panel",
        ".far-gap-card",
        ".far-gap-card.critical",
        ".far-gap-card.high",
        ".far-gap-card.moderate",
        ".far-persistent-badge",
        ".far-action-bar-spacer",
        ".far-high-contrast",
    ]

    for cls in required_classes:
        assert cls in FAR_ACTION_BAR_CSS, f"Missing CSS class: {cls}"

    print("[PASS] test_css_classes_defined")


def test_fixed_positioning():
    """Test CSS includes fixed positioning properties."""
    assert "position: fixed" in FAR_ACTION_BAR_CSS
    assert "bottom: 0" in FAR_ACTION_BAR_CSS
    assert "z-index: 9999" in FAR_ACTION_BAR_CSS

    print("[PASS] test_fixed_positioning")


def test_non_dismissible_styling():
    """Test CSS includes non-dismissible indicator styling."""
    # Check for persistent badge
    assert ".far-persistent-badge" in FAR_ACTION_BAR_CSS
    # Check for animated indicator
    assert "@keyframes farBarPulse" in FAR_ACTION_BAR_CSS
    assert "animation: farBarPulse" in FAR_ACTION_BAR_CSS

    print("[PASS] test_non_dismissible_styling")


def test_high_contrast_mode():
    """Test CSS includes high contrast mode styling."""
    assert ".far-high-contrast" in FAR_ACTION_BAR_CSS
    assert "border: 2px solid white" in FAR_ACTION_BAR_CSS
    assert "border-width: 2px" in FAR_ACTION_BAR_CSS
    assert "border-left-width: 5px" in FAR_ACTION_BAR_CSS

    print("[PASS] test_high_contrast_mode")


def test_color_coding():
    """Test color coding is distinct for each severity."""
    colors = set()
    for level, config in FAR_SEVERITY_LEVELS.items():
        color = config["color"]
        assert color not in colors, f"Duplicate color found: {color}"
        colors.add(color)

    print("[PASS] test_color_coding")


def generate_test_report():
    """Generate test report for GEM validation."""
    report = {
        "component": "FAR Action Bar",
        "phase": "Phase 5 UX Upgrade - Task 4",
        "status": "IMPLEMENTED",
        "tests_passed": 14,
        "tests_failed": 0,
        "features": [
            "Fixed bottom viewport positioning (z-index 9999)",
            "High-contrast, non-dismissible styling",
            "Animated gradient indicator bar",
            "Severity-coded summary badges (CRITICAL/HIGH/MODERATE)",
            "Expandable details panel with gap cards",
            "5 action buttons (Resolve, Escalate, Defer, Negotiate, Export)",
            "Gap cards with recommendations",
            "Session state persistence for details panel",
            "Inline summary view option",
            "Expander integration helper",
            "Print-friendly CSS styles",
            "High contrast mode toggle",
            "Action callback support",
        ],
        "css_classes_implemented": [
            "far-action-bar (fixed container)",
            "far-bar-header (title section)",
            "far-summary-badges (severity counts)",
            "far-summary-badge.* (severity-specific)",
            "far-action-btn.* (button variants)",
            "far-details-panel (expandable)",
            "far-gap-card.* (severity cards)",
            "far-persistent-badge (action required)",
            "far-action-bar-spacer (content offset)",
            "far-high-contrast (accessibility mode)",
            "far-action-bar-inline (non-fixed variant)",
        ],
        "severity_levels": {
            "CRITICAL": {
                "icon": "🔴",
                "color": "#DC2626",
                "description": "Requires immediate resolution",
            },
            "HIGH": {
                "icon": "🟠",
                "color": "#D97706",
                "description": "Should be addressed before execution",
            },
            "MODERATE": {
                "icon": "🟡",
                "color": "#2563EB",
                "description": "Monitor and review",
            },
        },
        "action_types": {
            "RESOLVE": {"icon": "✅", "color": "#10B981"},
            "ESCALATE": {"icon": "⬆️", "color": "#F59E0B"},
            "DEFER": {"icon": "⏳", "color": "#6B7280"},
            "NEGOTIATE": {"icon": "🤝", "color": "#3B82F6"},
            "EXPORT": {"icon": "📤", "color": "#8B5CF6"},
        },
        "positioning": {
            "type": "fixed",
            "location": "bottom viewport",
            "z_index": 9999,
            "spacer_height": "140px",
        },
        "state_management": {
            "state_key_pattern": "_far_details_expanded_{bar_id}",
            "default_state": "collapsed",
            "persistence": "st.session_state",
        },
        "integration_points": [
            "Compare Versions page (when FAR gaps detected)",
            "Contract analysis completion",
            "Flowdown compliance reviews",
            "Subcontract generation workflows",
            "Risk assessment dashboards",
        ],
        "file_location": "frontend/components/far_action_bar.py",
        "demo_page": "frontend/pages/12_📋_FAR_Action_Bar_Demo.py",
        "data_structure": {
            "input_format": {
                "gap_type": "str",
                "severity": "str (CRITICAL|HIGH|MODERATE)",
                "upstream_value": "str",
                "downstream_value": "str",
                "recommendation": "str",
            },
            "extraction_function": "extract_far_data_from_v3_result()",
            "stats_function": "get_far_summary_stats()",
            "visibility_function": "should_show_action_bar()",
        },
    }

    return report


def main():
    """Run all tests and generate report."""
    print("=" * 60)
    print("FAR ACTION BAR COMPONENT - TEST SUITE")
    print("Phase 5 UX Upgrade - Task 4 Validation")
    print("=" * 60)
    print()

    # Run tests
    test_severity_levels_defined()
    test_action_types_defined()
    test_severity_config()
    test_count_gaps_by_severity()
    test_summary_badges_html()
    test_gap_card_html()
    test_extract_far_data()
    test_summary_stats()
    test_should_show_action_bar()
    test_css_classes_defined()
    test_fixed_positioning()
    test_non_dismissible_styling()
    test_high_contrast_mode()
    test_color_coding()

    print()
    print("=" * 60)
    print("ALL TESTS PASSED (14/14)")
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
        "far_action_bar_test_report.json"
    )

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print(f"Report saved to: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
