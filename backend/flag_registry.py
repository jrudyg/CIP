"""
Flag Registry for Compare v3 Intelligence Pipeline
Phase 4F: Staged activation of SAE/ERCE/BIRL/FAR engines.

Manages:
- Flag state persistence (config/settings.json)
- Flag validation
- Activation history tracking

CIP Protocol: This module is used by CC for flag management.
Frozen surfaces (TRUST, GEM, Z7) are NOT modified by this module.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Constants
CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "settings.json"
)

DEFAULT_FLAGS = {
    "flag_sae": False,
    "flag_erce": False,
    "flag_birl": False,
    "flag_far": False
}

VALID_FLAGS = {"flag_sae", "flag_erce", "flag_birl", "flag_far"}


@dataclass
class FlagState:
    """Current state of all intelligence flags."""
    flag_sae: bool = False
    flag_erce: bool = False
    flag_birl: bool = False
    flag_far: bool = False

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            "flag_sae": self.flag_sae,
            "flag_erce": self.flag_erce,
            "flag_birl": self.flag_birl,
            "flag_far": self.flag_far
        }

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> "FlagState":
        """Create FlagState from dictionary."""
        return cls(
            flag_sae=data.get("flag_sae", False),
            flag_erce=data.get("flag_erce", False),
            flag_birl=data.get("flag_birl", False),
            flag_far=data.get("flag_far", False)
        )

    def active_flags(self) -> List[str]:
        """Return list of active flag names."""
        return [k for k, v in self.to_dict().items() if v]

    def any_active(self) -> bool:
        """Return True if any flag is active."""
        return any(self.to_dict().values())

    def all_active(self) -> bool:
        """Return True if all flags are active."""
        return all(self.to_dict().values())


def load_config() -> Dict[str, Any]:
    """Load full configuration from settings.json."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to settings.json."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def _ensure_compare_v3_section(config: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure compare_v3 section exists in config."""
    if "compare_v3" not in config:
        config["compare_v3"] = {
            "flags": DEFAULT_FLAGS.copy(),
            "version": "4F",
            "last_stage_activated": None,
            "activation_history": []
        }
    return config


def get_flag_state() -> FlagState:
    """Get current flag state from configuration."""
    config = load_config()
    compare_v3 = config.get("compare_v3", {})
    flags = compare_v3.get("flags", DEFAULT_FLAGS)
    return FlagState.from_dict(flags)


def set_flag_state(state: FlagState, stage_id: Optional[str] = None) -> None:
    """
    Update flag state in configuration.

    Args:
        state: New FlagState to persist
        stage_id: Optional stage identifier for history tracking
    """
    config = load_config()
    config = _ensure_compare_v3_section(config)

    config["compare_v3"]["flags"] = state.to_dict()

    if stage_id:
        config["compare_v3"]["last_stage_activated"] = stage_id
        config["compare_v3"]["activation_history"].append({
            "stage_id": stage_id,
            "flags": state.to_dict(),
            "activated_at": datetime.now().isoformat()
        })

    save_config(config)


def get_activation_history() -> List[Dict[str, Any]]:
    """Get the activation history from configuration."""
    config = load_config()
    compare_v3 = config.get("compare_v3", {})
    return compare_v3.get("activation_history", [])


def get_last_stage() -> Optional[str]:
    """Get the last activated stage ID."""
    config = load_config()
    compare_v3 = config.get("compare_v3", {})
    return compare_v3.get("last_stage_activated")


def validate_flags(flags: Dict[str, bool]) -> List[str]:
    """
    Validate flag dictionary.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    for key in flags.keys():
        if key not in VALID_FLAGS:
            errors.append(f"Unknown flag: {key}")
    for key in VALID_FLAGS:
        if key not in flags:
            errors.append(f"Missing flag: {key}")
    return errors


def reset_all_flags() -> FlagState:
    """Reset all flags to False (default state)."""
    state = FlagState()
    set_flag_state(state, "reset")
    return state


def get_flag(flag_name: str) -> bool:
    """
    Get a single flag value.

    Args:
        flag_name: Name of the flag (e.g., "flag_sae")

    Returns:
        Boolean value of the flag
    """
    if flag_name not in VALID_FLAGS:
        raise ValueError(f"Unknown flag: {flag_name}")
    state = get_flag_state()
    return getattr(state, flag_name)


def set_flag(flag_name: str, value: bool, stage_id: Optional[str] = None) -> None:
    """
    Set a single flag value.

    Args:
        flag_name: Name of the flag (e.g., "flag_sae")
        value: Boolean value to set
        stage_id: Optional stage identifier for history
    """
    if flag_name not in VALID_FLAGS:
        raise ValueError(f"Unknown flag: {flag_name}")

    state = get_flag_state()
    setattr(state, flag_name, value)
    set_flag_state(state, stage_id)
