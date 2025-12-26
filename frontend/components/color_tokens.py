"""
Unified Color Token Definitions - Phase 6 UI Upgrade
P6.C2.T1: High-Contrast TopNav

Systemwide color token definitions following the Unified Visual Language (SAE→FAR).
Provides both standard and high-contrast mode color schemes.

CIP Protocol: CC2 implementation for GEM UX validation.
"""

import streamlit as st
from typing import Dict, Any, Optional
from dataclasses import dataclass


# ============================================================================
# COLOR TOKEN DEFINITIONS
# ============================================================================

@dataclass
class ColorToken:
    """Represents a color token with standard and high-contrast variants."""
    name: str
    standard: str
    high_contrast: str
    description: str


# Base palette tokens
BASE_TOKENS = {
    # Primary backgrounds
    "bg-primary": ColorToken(
        "bg-primary",
        "#0F172A",
        "#000000",
        "Primary background color"
    ),
    "bg-secondary": ColorToken(
        "bg-secondary",
        "#1E293B",
        "#0A0A0A",
        "Secondary background color"
    ),
    "bg-tertiary": ColorToken(
        "bg-tertiary",
        "#334155",
        "#1A1A1A",
        "Tertiary background color"
    ),

    # Surface colors
    "surface-default": ColorToken(
        "surface-default",
        "#1E293B",
        "#0F0F0F",
        "Default surface color"
    ),
    "surface-elevated": ColorToken(
        "surface-elevated",
        "#334155",
        "#1A1A1A",
        "Elevated surface color"
    ),
    "surface-overlay": ColorToken(
        "surface-overlay",
        "rgba(15, 23, 42, 0.95)",
        "rgba(0, 0, 0, 0.98)",
        "Overlay surface color"
    ),

    # Text colors
    "text-primary": ColorToken(
        "text-primary",
        "#F1F5F9",
        "#FFFFFF",
        "Primary text color"
    ),
    "text-secondary": ColorToken(
        "text-secondary",
        "#94A3B8",
        "#E0E0E0",
        "Secondary text color"
    ),
    "text-muted": ColorToken(
        "text-muted",
        "#64748B",
        "#A0A0A0",
        "Muted text color"
    ),
    "text-disabled": ColorToken(
        "text-disabled",
        "#475569",
        "#606060",
        "Disabled text color"
    ),

    # Border colors
    "border-default": ColorToken(
        "border-default",
        "#334155",
        "#404040",
        "Default border color"
    ),
    "border-strong": ColorToken(
        "border-strong",
        "#475569",
        "#606060",
        "Strong border color"
    ),
    "border-focus": ColorToken(
        "border-focus",
        "#3B82F6",
        "#60A5FA",
        "Focus border color"
    ),

    # Accent colors
    "accent-primary": ColorToken(
        "accent-primary",
        "#3B82F6",
        "#60A5FA",
        "Primary accent (blue)"
    ),
    "accent-success": ColorToken(
        "accent-success",
        "#10B981",
        "#34D399",
        "Success accent (green)"
    ),
    "accent-warning": ColorToken(
        "accent-warning",
        "#F59E0B",
        "#FBBF24",
        "Warning accent (amber)"
    ),
    "accent-error": ColorToken(
        "accent-error",
        "#EF4444",
        "#F87171",
        "Error accent (red)"
    ),
}

# Pipeline-specific tokens (SAE → ERCE → BIRL → FAR)
PIPELINE_TOKENS = {
    # SAE (Semantic Alignment Engine)
    "sae-primary": ColorToken(
        "sae-primary",
        "#3B82F6",
        "#60A5FA",
        "SAE primary color"
    ),
    "sae-bg": ColorToken(
        "sae-bg",
        "rgba(59, 130, 246, 0.15)",
        "rgba(96, 165, 250, 0.25)",
        "SAE background tint"
    ),
    "sae-border": ColorToken(
        "sae-border",
        "rgba(59, 130, 246, 0.4)",
        "rgba(96, 165, 250, 0.6)",
        "SAE border color"
    ),

    # ERCE Severity Colors
    "erce-critical": ColorToken(
        "erce-critical",
        "#DC2626",
        "#F87171",
        "ERCE critical severity"
    ),
    "erce-critical-bg": ColorToken(
        "erce-critical-bg",
        "rgba(220, 38, 38, 0.15)",
        "rgba(248, 113, 113, 0.25)",
        "ERCE critical background"
    ),
    "erce-high": ColorToken(
        "erce-high",
        "#D97706",
        "#FBBF24",
        "ERCE high severity"
    ),
    "erce-high-bg": ColorToken(
        "erce-high-bg",
        "rgba(217, 119, 6, 0.15)",
        "rgba(251, 191, 36, 0.25)",
        "ERCE high background"
    ),
    "erce-moderate": ColorToken(
        "erce-moderate",
        "#2563EB",
        "#60A5FA",
        "ERCE moderate severity"
    ),
    "erce-moderate-bg": ColorToken(
        "erce-moderate-bg",
        "rgba(37, 99, 235, 0.15)",
        "rgba(96, 165, 250, 0.25)",
        "ERCE moderate background"
    ),
    "erce-admin": ColorToken(
        "erce-admin",
        "#6B7280",
        "#9CA3AF",
        "ERCE admin/low severity"
    ),
    "erce-admin-bg": ColorToken(
        "erce-admin-bg",
        "rgba(107, 114, 128, 0.15)",
        "rgba(156, 163, 175, 0.25)",
        "ERCE admin background"
    ),

    # BIRL Impact Dimensions
    "birl-margin": ColorToken(
        "birl-margin",
        "#059669",
        "#34D399",
        "BIRL margin impact"
    ),
    "birl-risk": ColorToken(
        "birl-risk",
        "#DC2626",
        "#F87171",
        "BIRL risk exposure"
    ),
    "birl-compliance": ColorToken(
        "birl-compliance",
        "#7C3AED",
        "#A78BFA",
        "BIRL compliance"
    ),
    "birl-schedule": ColorToken(
        "birl-schedule",
        "#2563EB",
        "#60A5FA",
        "BIRL schedule impact"
    ),
    "birl-quality": ColorToken(
        "birl-quality",
        "#0891B2",
        "#22D3EE",
        "BIRL quality"
    ),
    "birl-cashflow": ColorToken(
        "birl-cashflow",
        "#CA8A04",
        "#FACC15",
        "BIRL cash flow"
    ),

    # FAR Severity
    "far-critical": ColorToken(
        "far-critical",
        "#DC2626",
        "#F87171",
        "FAR critical gap"
    ),
    "far-high": ColorToken(
        "far-high",
        "#D97706",
        "#FBBF24",
        "FAR high gap"
    ),
    "far-moderate": ColorToken(
        "far-moderate",
        "#2563EB",
        "#60A5FA",
        "FAR moderate gap"
    ),
}

# Navigation tokens
NAV_TOKENS = {
    "nav-bg": ColorToken(
        "nav-bg",
        "linear-gradient(180deg, #0F172A 0%, #1E293B 100%)",
        "linear-gradient(180deg, #000000 0%, #0A0A0A 100%)",
        "Navigation background"
    ),
    "nav-border": ColorToken(
        "nav-border",
        "#334155",
        "#404040",
        "Navigation border"
    ),
    "nav-tab-active": ColorToken(
        "nav-tab-active",
        "#3B82F6",
        "#60A5FA",
        "Active tab indicator"
    ),
    "nav-tab-hover": ColorToken(
        "nav-tab-hover",
        "rgba(59, 130, 246, 0.15)",
        "rgba(96, 165, 250, 0.25)",
        "Tab hover background"
    ),
    "nav-tab-text": ColorToken(
        "nav-tab-text",
        "#F1F5F9",
        "#FFFFFF",
        "Tab text color"
    ),
    "nav-tab-text-inactive": ColorToken(
        "nav-tab-text-inactive",
        "#94A3B8",
        "#D0D0D0",
        "Inactive tab text"
    ),
}


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def _get_contrast_mode_key() -> str:
    """Get session state key for contrast mode."""
    return "_cip_high_contrast_mode"


def init_contrast_mode(default: bool = False) -> None:
    """Initialize high-contrast mode state."""
    key = _get_contrast_mode_key()
    if key not in st.session_state:
        st.session_state[key] = default


def is_high_contrast_mode() -> bool:
    """Check if high-contrast mode is enabled."""
    init_contrast_mode()
    return st.session_state.get(_get_contrast_mode_key(), False)


def set_high_contrast_mode(enabled: bool) -> None:
    """Set high-contrast mode state."""
    st.session_state[_get_contrast_mode_key()] = enabled


def toggle_high_contrast_mode() -> None:
    """Toggle high-contrast mode."""
    init_contrast_mode()
    key = _get_contrast_mode_key()
    st.session_state[key] = not st.session_state[key]


# ============================================================================
# TOKEN ACCESS
# ============================================================================

def get_token(token_name: str, force_high_contrast: Optional[bool] = None) -> str:
    """
    Get a color token value based on current contrast mode.

    Args:
        token_name: Name of the token to retrieve
        force_high_contrast: Override current mode (None uses session state)

    Returns:
        Color value string
    """
    # Determine which mode to use
    if force_high_contrast is not None:
        use_high_contrast = force_high_contrast
    else:
        use_high_contrast = is_high_contrast_mode()

    # Search in all token sets
    all_tokens = {**BASE_TOKENS, **PIPELINE_TOKENS, **NAV_TOKENS}

    if token_name in all_tokens:
        token = all_tokens[token_name]
        return token.high_contrast if use_high_contrast else token.standard

    # Return fallback if not found
    return "#FFFFFF" if use_high_contrast else "#F1F5F9"


def get_all_tokens(force_high_contrast: Optional[bool] = None) -> Dict[str, str]:
    """
    Get all color tokens as a dictionary.

    Args:
        force_high_contrast: Override current mode (None uses session state)

    Returns:
        Dictionary of token_name -> color_value
    """
    if force_high_contrast is not None:
        use_high_contrast = force_high_contrast
    else:
        use_high_contrast = is_high_contrast_mode()

    all_tokens = {**BASE_TOKENS, **PIPELINE_TOKENS, **NAV_TOKENS}

    return {
        name: (token.high_contrast if use_high_contrast else token.standard)
        for name, token in all_tokens.items()
    }


def generate_css_variables(force_high_contrast: Optional[bool] = None) -> str:
    """
    Generate CSS custom properties for all tokens.

    Returns:
        CSS string with :root custom properties
    """
    tokens = get_all_tokens(force_high_contrast)

    css_vars = ":root {\n"
    for name, value in tokens.items():
        css_name = f"--cip-{name}"
        css_vars += f"  {css_name}: {value};\n"
    css_vars += "}\n"

    return css_vars


def inject_color_tokens() -> None:
    """Inject color token CSS variables into the page."""
    css = f"<style>{generate_css_variables()}</style>"
    st.markdown(css, unsafe_allow_html=True)


# ============================================================================
# CONTRAST MODE UI
# ============================================================================

def render_contrast_toggle(location: str = "sidebar") -> None:
    """
    Render high-contrast mode toggle.

    Args:
        location: Where to render ("sidebar" or "inline")
    """
    init_contrast_mode()
    current_mode = is_high_contrast_mode()

    label = "High Contrast Mode"
    icon = "🔳" if current_mode else "🔲"

    if location == "sidebar":
        if st.sidebar.checkbox(
            f"{icon} {label}",
            value=current_mode,
            key="_contrast_toggle_sidebar"
        ):
            if not current_mode:
                set_high_contrast_mode(True)
                st.rerun()
        else:
            if current_mode:
                set_high_contrast_mode(False)
                st.rerun()
    else:
        if st.checkbox(
            f"{icon} {label}",
            value=current_mode,
            key="_contrast_toggle_inline"
        ):
            if not current_mode:
                set_high_contrast_mode(True)
                st.rerun()
        else:
            if current_mode:
                set_high_contrast_mode(False)
                st.rerun()


# ============================================================================
# TOKEN REFERENCE
# ============================================================================

def get_token_reference() -> Dict[str, Dict[str, Any]]:
    """
    Get full token reference with metadata.

    Returns:
        Dictionary with token information
    """
    all_tokens = {**BASE_TOKENS, **PIPELINE_TOKENS, **NAV_TOKENS}

    return {
        name: {
            "standard": token.standard,
            "high_contrast": token.high_contrast,
            "description": token.description,
        }
        for name, token in all_tokens.items()
    }
