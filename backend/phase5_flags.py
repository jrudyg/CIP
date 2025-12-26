"""
Phase 5 Feature Flags
Controls activation of new intelligence features.

All flags default to False for safe, incremental rollout.

Flag Alignment Patch (Stage 1 Blocker Fix):
- Intelligence flags now read from FlagState (flag_registry.py -> settings.json)
- Non-intelligence flags preserved as hard-coded defaults (fallback)
- Rollback: Remove flag_registry import and FLAG_NAME_MAP, revert is_flag_enabled()
"""

from typing import Any, Dict

# Import FlagState for intelligence flag alignment
try:
    from flag_registry import get_flag_state
    _FLAG_REGISTRY_AVAILABLE = True
except ImportError:
    _FLAG_REGISTRY_AVAILABLE = False

# Flag name mapping: phase5_flags name -> flag_registry name
FLAG_NAME_MAP = {
    "sae_intelligence_active": "flag_sae",
    "erce_intelligence_active": "flag_erce",
    "birl_intelligence_active": "flag_birl",
    "far_intelligence_active": "flag_far",
}


# ============================================================================
# PHASE 5 FEATURE FLAGS (DEFAULTS - used as fallback)
# ============================================================================

PHASE_5_FLAGS: Dict[str, bool] = {
    # Intelligence activation flags (Steps 2-5) - NOW READ FROM FlagState
    "sae_intelligence_active": False,
    "erce_intelligence_active": False,
    "birl_intelligence_active": False,
    "far_intelligence_active": False,

    # UI activation flag (existing UI stays on)
    "compare_v3_ui_active": True,

    # Cache infrastructure flags (Step 1)
    "embedding_cache_active": False,
    "comparison_snapshot_active": False,
    "pattern_cache_active": False,
}


# ============================================================================
# PHASE 5 CONFIGURATION
# ============================================================================

PHASE_5_CONFIG: Dict[str, Any] = {
    # BIRL configuration
    "birl_max_narratives": 5,  # Configurable cap
    "birl_token_limit": 150,

    # Timeout configuration
    "global_hard_timeout_seconds": 120,  # Configurable
    "sae_timeout_seconds": 30,
    "erce_timeout_seconds": 15,
    "birl_timeout_seconds": 45,
    "far_timeout_seconds": 15,

    # Circuit breaker (in-memory only)
    "circuit_breaker_failure_threshold": 3,
    "circuit_breaker_recovery_seconds": 60,

    # Cache configuration
    "embedding_cache_max_entries": 10000,
    "embedding_cache_ttl_hours": 168,  # 7 days
    "comparison_snapshot_max_entries": 1000,
    "comparison_snapshot_ttl_hours": 720,  # 30 days
    "pattern_cache_ttl_hours": 24,
}


# ============================================================================
# FLAG ACCESS FUNCTIONS
# ============================================================================

def is_flag_enabled(flag_name: str) -> bool:
    """
    Check if a Phase 5 feature flag is enabled.

    Intelligence flags (SAE/ERCE/BIRL/FAR) are read from FlagState (settings.json).
    Other flags use hard-coded defaults as fallback.

    Args:
        flag_name: Name of the flag to check

    Returns:
        True if enabled, False otherwise (defaults to False for unknown flags)
    """
    # Intelligence flags: read from FlagState (canonical source)
    if flag_name in FLAG_NAME_MAP and _FLAG_REGISTRY_AVAILABLE:
        try:
            registry_name = FLAG_NAME_MAP[flag_name]
            state = get_flag_state()
            return getattr(state, registry_name, False)
        except Exception:
            # Fallback to hard-coded default on any error
            return PHASE_5_FLAGS.get(flag_name, False)

    # Non-intelligence flags: use hard-coded defaults
    return PHASE_5_FLAGS.get(flag_name, False)


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a Phase 5 configuration value.

    Args:
        key: Configuration key
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    return PHASE_5_CONFIG.get(key, default)


def get_all_flags() -> Dict[str, bool]:
    """
    Get all Phase 5 feature flags (with live values for intelligence flags).

    Returns:
        Dictionary of all flags and their current states
    """
    flags = PHASE_5_FLAGS.copy()

    # Update intelligence flags with live values from FlagState
    if _FLAG_REGISTRY_AVAILABLE:
        try:
            state = get_flag_state()
            for phase5_name, registry_name in FLAG_NAME_MAP.items():
                flags[phase5_name] = getattr(state, registry_name, False)
        except Exception:
            pass  # Keep defaults on error

    return flags


def get_all_config() -> Dict[str, Any]:
    """
    Get all Phase 5 configuration values.

    Returns:
        Dictionary of all configuration values
    """
    return PHASE_5_CONFIG.copy()


# ============================================================================
# FLAG STATUS SUMMARY (for debugging/monitoring)
# ============================================================================

def get_phase5_status() -> Dict[str, Any]:
    """
    Get comprehensive Phase 5 status for monitoring.

    Returns:
        Dictionary with flags, config, and status summary
    """
    current_flags = get_all_flags()  # Uses live values
    enabled_flags = [k for k, v in current_flags.items() if v]
    disabled_flags = [k for k, v in current_flags.items() if not v]

    return {
        "flags": current_flags,
        "config": PHASE_5_CONFIG.copy(),
        "flag_registry_available": _FLAG_REGISTRY_AVAILABLE,
        "summary": {
            "total_flags": len(current_flags),
            "enabled_count": len(enabled_flags),
            "disabled_count": len(disabled_flags),
            "enabled_flags": enabled_flags,
            "disabled_flags": disabled_flags,
        }
    }
