"""
Multi-Panel Layout Test Harness
Phase 6 UI Component Preparation

This test harness provides utilities for testing multi-panel layouts,
persistent state management, and WCAG accessibility compliance.

CC2 Environment Preparation for Phase 6 Components:
- High-contrast TopNav
- Clause Selector (persistent global state)
- Integrated Insights Panel (tab system)
"""

import sys
import os
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================================
# LAYOUT TEST UTILITIES
# ============================================================================

@dataclass
class PanelConfig:
    """Configuration for a UI panel."""
    panel_id: str
    title: str
    position: str  # "top", "left", "right", "bottom", "center"
    width: Optional[str] = None  # CSS width value
    height: Optional[str] = None  # CSS height value
    z_index: int = 1
    fixed: bool = False
    collapsible: bool = False
    default_collapsed: bool = False


@dataclass
class LayoutConfig:
    """Configuration for a multi-panel layout."""
    layout_id: str
    panels: List[PanelConfig] = field(default_factory=list)
    responsive_breakpoints: Dict[str, int] = field(default_factory=lambda: {
        "mobile": 480,
        "tablet": 768,
        "desktop": 1024,
        "wide": 1440,
    })


def validate_layout_structure(layout: LayoutConfig) -> Dict[str, Any]:
    """
    Validate a multi-panel layout structure.

    Returns validation results with any issues found.
    """
    issues = []
    warnings = []

    # Check for required panels
    positions = [p.position for p in layout.panels]

    # Check for overlapping fixed panels
    fixed_panels = [p for p in layout.panels if p.fixed]
    fixed_positions = [p.position for p in fixed_panels]
    if len(fixed_positions) != len(set(fixed_positions)):
        issues.append("Multiple fixed panels at same position may overlap")

    # Check z-index conflicts
    z_indices = [(p.panel_id, p.z_index) for p in layout.panels if p.fixed]
    z_values = [z for _, z in z_indices]
    if len(z_values) != len(set(z_values)):
        warnings.append("Fixed panels with same z-index may cause stacking issues")

    # Check for center panel
    if "center" not in positions:
        warnings.append("No center/main content panel defined")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "panel_count": len(layout.panels),
        "fixed_count": len(fixed_panels),
    }


# ============================================================================
# STATE MANAGEMENT TEST UTILITIES
# ============================================================================

class MockSessionState:
    """Mock session state for testing persistent global state."""

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._access_log: List[Dict[str, Any]] = []

    def __getitem__(self, key: str) -> Any:
        self._log_access("get", key)
        return self._state.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._log_access("set", key, value)
        self._state[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._state

    def get(self, key: str, default: Any = None) -> Any:
        self._log_access("get", key)
        return self._state.get(key, default)

    def _log_access(self, operation: str, key: str, value: Any = None) -> None:
        self._access_log.append({
            "operation": operation,
            "key": key,
            "value": value,
        })

    def get_access_log(self) -> List[Dict[str, Any]]:
        return self._access_log.copy()

    def clear_log(self) -> None:
        self._access_log.clear()

    def reset(self) -> None:
        self._state.clear()
        self._access_log.clear()


def test_state_persistence(
    init_func: Callable,
    update_func: Callable,
    state_keys: List[str],
    mock_state: MockSessionState,
) -> Dict[str, Any]:
    """
    Test state persistence across component lifecycle.

    Args:
        init_func: Function that initializes component state
        update_func: Function that updates component state
        state_keys: List of state keys to verify
        mock_state: Mock session state instance

    Returns:
        Test results dictionary
    """
    results = {
        "passed": True,
        "tests": [],
    }

    # Test 1: Initial state creation
    mock_state.reset()
    init_func(mock_state)

    for key in state_keys:
        exists = key in mock_state
        results["tests"].append({
            "name": f"init_creates_{key}",
            "passed": exists,
        })
        if not exists:
            results["passed"] = False

    # Test 2: State persistence after update
    initial_values = {key: mock_state.get(key) for key in state_keys}
    update_func(mock_state)

    for key in state_keys:
        persisted = key in mock_state
        results["tests"].append({
            "name": f"persists_{key}_after_update",
            "passed": persisted,
        })
        if not persisted:
            results["passed"] = False

    return results


# ============================================================================
# WCAG ACCESSIBILITY TEST UTILITIES
# ============================================================================

@dataclass
class WCAGCheck:
    """WCAG compliance check result."""
    criterion: str
    level: str  # "A", "AA", "AAA"
    passed: bool
    details: str


def check_color_contrast(
    foreground: str,
    background: str,
    level: str = "AA",
    large_text: bool = False,
) -> WCAGCheck:
    """
    Check color contrast ratio for WCAG compliance.

    WCAG 2.1 requirements:
    - Level AA: 4.5:1 for normal text, 3:1 for large text
    - Level AAA: 7:1 for normal text, 4.5:1 for large text
    """
    # Convert hex to RGB
    def hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Calculate relative luminance
    def luminance(rgb: tuple) -> float:
        def channel(c):
            c = c / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

    try:
        fg_lum = luminance(hex_to_rgb(foreground))
        bg_lum = luminance(hex_to_rgb(background))

        lighter = max(fg_lum, bg_lum)
        darker = min(fg_lum, bg_lum)
        ratio = (lighter + 0.05) / (darker + 0.05)

        # Determine required ratio
        if level == "AAA":
            required = 4.5 if large_text else 7.0
        else:  # AA
            required = 3.0 if large_text else 4.5

        passed = ratio >= required

        return WCAGCheck(
            criterion="1.4.3" if level == "AA" else "1.4.6",
            level=level,
            passed=passed,
            details=f"Contrast ratio: {ratio:.2f}:1 (required: {required}:1)",
        )
    except Exception as e:
        return WCAGCheck(
            criterion="1.4.3",
            level=level,
            passed=False,
            details=f"Error calculating contrast: {str(e)}",
        )


def check_focus_indicators(css_content: str) -> WCAGCheck:
    """Check for visible focus indicators in CSS."""
    has_focus = ":focus" in css_content or ":focus-visible" in css_content
    has_outline = "outline" in css_content

    passed = has_focus and has_outline

    return WCAGCheck(
        criterion="2.4.7",
        level="AA",
        passed=passed,
        details="Focus indicators present" if passed else "Missing focus indicators",
    )


def check_keyboard_navigation(component_has_tabindex: bool, component_has_keyhandlers: bool) -> WCAGCheck:
    """Check keyboard navigation support."""
    passed = component_has_tabindex or component_has_keyhandlers

    return WCAGCheck(
        criterion="2.1.1",
        level="A",
        passed=passed,
        details="Keyboard accessible" if passed else "Not keyboard accessible",
    )


def run_wcag_audit(
    css_content: str,
    color_pairs: List[tuple],
    has_tabindex: bool = True,
    has_keyhandlers: bool = True,
) -> Dict[str, Any]:
    """
    Run full WCAG accessibility audit.

    Args:
        css_content: CSS string to check
        color_pairs: List of (foreground, background) hex color tuples
        has_tabindex: Component has tabindex attributes
        has_keyhandlers: Component has keyboard event handlers

    Returns:
        Audit results dictionary
    """
    checks = []

    # Color contrast checks
    for fg, bg in color_pairs:
        checks.append(check_color_contrast(fg, bg, "AA"))
        checks.append(check_color_contrast(fg, bg, "AAA"))

    # Focus indicator check
    checks.append(check_focus_indicators(css_content))

    # Keyboard navigation check
    checks.append(check_keyboard_navigation(has_tabindex, has_keyhandlers))

    passed = sum(1 for c in checks if c.passed)
    total = len(checks)

    return {
        "passed": passed,
        "total": total,
        "compliance_rate": passed / total if total > 0 else 0,
        "checks": [
            {
                "criterion": c.criterion,
                "level": c.level,
                "passed": c.passed,
                "details": c.details,
            }
            for c in checks
        ],
        "level_a_compliant": all(c.passed for c in checks if c.level == "A"),
        "level_aa_compliant": all(c.passed for c in checks if c.level in ["A", "AA"]),
    }


# ============================================================================
# TAB SYSTEM TEST UTILITIES
# ============================================================================

@dataclass
class TabConfig:
    """Configuration for a tab in a tab system."""
    tab_id: str
    label: str
    icon: Optional[str] = None
    disabled: bool = False
    badge_count: Optional[int] = None


def validate_tab_system(
    tabs: List[TabConfig],
    active_tab_id: str,
) -> Dict[str, Any]:
    """
    Validate tab system configuration.

    Returns validation results.
    """
    issues = []

    # Check for unique IDs
    tab_ids = [t.tab_id for t in tabs]
    if len(tab_ids) != len(set(tab_ids)):
        issues.append("Duplicate tab IDs found")

    # Check active tab exists
    if active_tab_id not in tab_ids:
        issues.append(f"Active tab '{active_tab_id}' not in tab list")

    # Check at least one enabled tab
    enabled_tabs = [t for t in tabs if not t.disabled]
    if len(enabled_tabs) == 0:
        issues.append("All tabs are disabled")

    # Check active tab is not disabled
    active_tab = next((t for t in tabs if t.tab_id == active_tab_id), None)
    if active_tab and active_tab.disabled:
        issues.append("Active tab is disabled")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "tab_count": len(tabs),
        "enabled_count": len(enabled_tabs),
        "active_tab": active_tab_id,
    }


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_harness_self_test() -> Dict[str, Any]:
    """Run self-test on the test harness utilities."""
    results = {
        "passed": 0,
        "failed": 0,
        "tests": [],
    }

    # Test 1: Layout validation
    test_layout = LayoutConfig(
        layout_id="test",
        panels=[
            PanelConfig("nav", "Navigation", "top", fixed=True, z_index=100),
            PanelConfig("main", "Main Content", "center"),
            PanelConfig("sidebar", "Sidebar", "right", collapsible=True),
        ]
    )
    layout_result = validate_layout_structure(test_layout)
    test_passed = layout_result["valid"]
    results["tests"].append({"name": "layout_validation", "passed": test_passed})
    results["passed" if test_passed else "failed"] += 1

    # Test 2: Mock state
    mock_state = MockSessionState()
    mock_state["test_key"] = "test_value"
    test_passed = mock_state.get("test_key") == "test_value"
    results["tests"].append({"name": "mock_state", "passed": test_passed})
    results["passed" if test_passed else "failed"] += 1

    # Test 3: Color contrast
    contrast_result = check_color_contrast("#FFFFFF", "#000000", "AA")
    test_passed = contrast_result.passed
    results["tests"].append({"name": "color_contrast_check", "passed": test_passed})
    results["passed" if test_passed else "failed"] += 1

    # Test 4: Tab validation
    test_tabs = [
        TabConfig("tab1", "Tab 1"),
        TabConfig("tab2", "Tab 2"),
        TabConfig("tab3", "Tab 3", disabled=True),
    ]
    tab_result = validate_tab_system(test_tabs, "tab1")
    test_passed = tab_result["valid"]
    results["tests"].append({"name": "tab_validation", "passed": test_passed})
    results["passed" if test_passed else "failed"] += 1

    # Test 5: WCAG audit
    test_css = """
    .component:focus { outline: 2px solid blue; }
    .component:focus-visible { outline: 2px solid blue; }
    """
    wcag_result = run_wcag_audit(
        test_css,
        [("#FFFFFF", "#1E293B"), ("#F1F5F9", "#0F172A")],
    )
    test_passed = wcag_result["level_a_compliant"]
    results["tests"].append({"name": "wcag_audit", "passed": test_passed})
    results["passed" if test_passed else "failed"] += 1

    return results


def main():
    """Run test harness self-test."""
    print("=" * 60)
    print("MULTI-PANEL LAYOUT TEST HARNESS - SELF TEST")
    print("Phase 6 UI Component Preparation")
    print("=" * 60)
    print()

    results = run_harness_self_test()

    for test in results["tests"]:
        status = "[PASS]" if test["passed"] else "[FAIL]"
        print(f"{status} {test['name']}")

    print()
    print("=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    if results["failed"] == 0:
        print()
        print("Test harness ready for Phase 6 component development.")

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
