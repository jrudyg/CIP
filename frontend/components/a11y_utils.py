"""
Accessibility Utilities - Phase 6 UI Upgrade
Micro-Enhancement Package: Keyboard Navigation Foundations

Self-contained a11y helpers for WCAG AA compliance.
No dependencies on TopNav or color_tokens (GEM audit protection).

CIP Protocol: CC2 implementation.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass


# ============================================================================
# FOCUS STATE HELPERS
# ============================================================================

@dataclass
class FocusConfig:
    """Configuration for focus state management."""
    outline_width: str = "2px"
    outline_style: str = "solid"
    outline_color: str = "#3B82F6"
    outline_offset: str = "-2px"
    high_contrast_width: str = "3px"
    high_contrast_color: str = "#60A5FA"


def generate_focus_css(
    selector: str,
    config: Optional[FocusConfig] = None,
    high_contrast: bool = False,
) -> str:
    """
    Generate CSS for focus states with WCAG AA compliance.

    Args:
        selector: CSS selector for the element
        config: Focus configuration (uses defaults if None)
        high_contrast: Use high-contrast mode values

    Returns:
        CSS string for :focus and :focus-visible states
    """
    if config is None:
        config = FocusConfig()

    width = config.high_contrast_width if high_contrast else config.outline_width
    color = config.high_contrast_color if high_contrast else config.outline_color

    return f"""
{selector}:focus {{
    outline: {width} {config.outline_style} {color};
    outline-offset: {config.outline_offset};
}}

{selector}:focus-visible {{
    outline: {width} {config.outline_style} {color};
    outline-offset: {config.outline_offset};
}}

{selector}:focus:not(:focus-visible) {{
    outline: none;
}}
"""


def get_tabindex(
    is_interactive: bool = True,
    is_disabled: bool = False,
    custom_order: Optional[int] = None,
) -> str:
    """
    Get appropriate tabindex value for an element.

    Args:
        is_interactive: Whether element should be focusable
        is_disabled: Whether element is disabled
        custom_order: Custom tab order (use sparingly)

    Returns:
        tabindex attribute value as string
    """
    if is_disabled:
        return "-1"
    if custom_order is not None:
        return str(custom_order)
    if is_interactive:
        return "0"
    return "-1"


# ============================================================================
# KEYBOARD EVENT NORMALIZATION
# ============================================================================

# Standard key codes for keyboard navigation
KEY_CODES = {
    "enter": ["Enter", "13"],
    "space": [" ", "Spacebar", "32"],
    "escape": ["Escape", "Esc", "27"],
    "tab": ["Tab", "9"],
    "arrow_up": ["ArrowUp", "Up", "38"],
    "arrow_down": ["ArrowDown", "Down", "40"],
    "arrow_left": ["ArrowLeft", "Left", "37"],
    "arrow_right": ["ArrowRight", "Right", "39"],
    "home": ["Home", "36"],
    "end": ["End", "35"],
}


def normalize_key(key: str) -> str:
    """
    Normalize keyboard event key to standard name.

    Args:
        key: Raw key value from event

    Returns:
        Normalized key name (e.g., "enter", "escape")
    """
    for name, variants in KEY_CODES.items():
        if key in variants or str(key) in variants:
            return name
    return key.lower()


def is_activation_key(key: str) -> bool:
    """
    Check if key is an activation key (Enter or Space).

    Args:
        key: Raw key value from event

    Returns:
        True if key activates interactive elements
    """
    normalized = normalize_key(key)
    return normalized in ("enter", "space")


def is_navigation_key(key: str) -> bool:
    """
    Check if key is a navigation key (arrows, home, end).

    Args:
        key: Raw key value from event

    Returns:
        True if key is used for navigation
    """
    normalized = normalize_key(key)
    return normalized in ("arrow_up", "arrow_down", "arrow_left", "arrow_right", "home", "end")


def get_navigation_direction(key: str) -> Optional[str]:
    """
    Get navigation direction from arrow key.

    Args:
        key: Raw key value from event

    Returns:
        Direction string or None if not an arrow key
    """
    normalized = normalize_key(key)
    directions = {
        "arrow_up": "up",
        "arrow_down": "down",
        "arrow_left": "left",
        "arrow_right": "right",
    }
    return directions.get(normalized)


# ============================================================================
# ARIA ROLE CONVENIENCE MAPPING
# ============================================================================

@dataclass
class AriaRole:
    """ARIA role definition with required/supported attributes."""
    role: str
    description: str
    required_attrs: List[str]
    supported_attrs: List[str]
    keyboard_support: List[str]


# Common interactive widget roles
ARIA_ROLES = {
    "button": AriaRole(
        role="button",
        description="Clickable button element",
        required_attrs=[],
        supported_attrs=["aria-pressed", "aria-expanded", "aria-disabled"],
        keyboard_support=["Enter", "Space"],
    ),
    "tab": AriaRole(
        role="tab",
        description="Tab in a tablist",
        required_attrs=["aria-selected"],
        supported_attrs=["aria-controls", "aria-disabled"],
        keyboard_support=["Arrow keys", "Home", "End"],
    ),
    "tablist": AriaRole(
        role="tablist",
        description="Container for tabs",
        required_attrs=[],
        supported_attrs=["aria-orientation", "aria-label"],
        keyboard_support=["Arrow keys"],
    ),
    "tabpanel": AriaRole(
        role="tabpanel",
        description="Content panel for a tab",
        required_attrs=["aria-labelledby"],
        supported_attrs=["aria-hidden"],
        keyboard_support=["Tab"],
    ),
    "menu": AriaRole(
        role="menu",
        description="Menu widget",
        required_attrs=[],
        supported_attrs=["aria-orientation", "aria-label"],
        keyboard_support=["Arrow keys", "Enter", "Escape"],
    ),
    "menuitem": AriaRole(
        role="menuitem",
        description="Item in a menu",
        required_attrs=[],
        supported_attrs=["aria-disabled"],
        keyboard_support=["Enter", "Space"],
    ),
    "listbox": AriaRole(
        role="listbox",
        description="Selectable list",
        required_attrs=[],
        supported_attrs=["aria-multiselectable", "aria-orientation"],
        keyboard_support=["Arrow keys", "Home", "End"],
    ),
    "option": AriaRole(
        role="option",
        description="Option in a listbox",
        required_attrs=["aria-selected"],
        supported_attrs=["aria-disabled"],
        keyboard_support=["Enter", "Space"],
    ),
}


def get_aria_attrs(
    role: str,
    **kwargs: Any,
) -> Dict[str, str]:
    """
    Generate ARIA attributes for a given role.

    Args:
        role: ARIA role name
        **kwargs: Attribute values (e.g., selected=True, controls="panel-1")

    Returns:
        Dictionary of ARIA attributes
    """
    attrs = {"role": role}

    # Map common kwargs to ARIA attributes
    attr_mapping = {
        "selected": "aria-selected",
        "expanded": "aria-expanded",
        "pressed": "aria-pressed",
        "disabled": "aria-disabled",
        "hidden": "aria-hidden",
        "controls": "aria-controls",
        "labelledby": "aria-labelledby",
        "label": "aria-label",
        "describedby": "aria-describedby",
        "orientation": "aria-orientation",
        "multiselectable": "aria-multiselectable",
    }

    for key, value in kwargs.items():
        aria_attr = attr_mapping.get(key, f"aria-{key}")
        if isinstance(value, bool):
            attrs[aria_attr] = "true" if value else "false"
        else:
            attrs[aria_attr] = str(value)

    return attrs


def format_aria_attrs(attrs: Dict[str, str]) -> str:
    """
    Format ARIA attributes as HTML attribute string.

    Args:
        attrs: Dictionary of attribute name -> value

    Returns:
        HTML attribute string (e.g., 'role="tab" aria-selected="true"')
    """
    return " ".join(f'{k}="{v}"' for k, v in attrs.items())


def get_role_info(role: str) -> Optional[AriaRole]:
    """
    Get ARIA role information.

    Args:
        role: Role name

    Returns:
        AriaRole object or None if not found
    """
    return ARIA_ROLES.get(role)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_focus_visible(css: str) -> Dict[str, Any]:
    """
    Validate CSS contains proper focus indicators.

    Args:
        css: CSS string to validate

    Returns:
        Validation result dictionary
    """
    issues = []
    features = []

    if ":focus" in css:
        features.append("Basic :focus selector present")
    else:
        issues.append("Missing :focus selector")

    if ":focus-visible" in css:
        features.append(":focus-visible selector present (keyboard-only focus)")
    else:
        issues.append("Missing :focus-visible selector (recommended)")

    if "outline" in css:
        features.append("Outline property used for focus indicator")
    else:
        issues.append("No outline property found for focus indicator")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "features": features,
    }


def validate_aria_role(role: str, attrs: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate ARIA attributes for a given role.

    Args:
        role: ARIA role name
        attrs: Current attributes on element

    Returns:
        Validation result dictionary
    """
    role_info = get_role_info(role)
    if not role_info:
        return {
            "valid": True,
            "issues": [],
            "warnings": [f"Unknown role '{role}' - cannot validate"],
        }

    issues = []
    warnings = []

    # Check required attributes
    for required in role_info.required_attrs:
        if required not in attrs:
            issues.append(f"Missing required attribute: {required}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "keyboard_support": role_info.keyboard_support,
    }
