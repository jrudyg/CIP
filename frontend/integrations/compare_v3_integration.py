"""
Compare v3 Integration Module
Phase 5 - Unified Data Binding for Intelligence Engines

CC3 Task 5: API Data Model Update
Ensures frontend models match Phase 5 API shape with no truncation or mismatch.

This module consolidates all four engine data extraction functions
and provides unified data binding for the Compare v3 pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

# Import engine-specific extraction functions
from components.sae_tooltip import extract_sae_data_from_v3_result
from components.erce_highlights import extract_erce_data_from_v3_result
from components.birl_narrative import extract_birl_data_from_v3_result
from components.far_action_bar import extract_far_data_from_v3_result


# ============================================================================
# PHASE 5 API SHAPE SPECIFICATION
# ============================================================================

PHASE_5_API_SHAPE = {
    "success": bool,
    "data": {
        "id": int,
        "v1_snapshot_id": int,
        "v2_snapshot_id": int,
        "created_at": str,  # ISO timestamp
        "sae_matches": list,       # List[ClauseMatch]
        "erce_results": list,      # List[RiskDelta]
        "birl_narratives": list,   # List[BusinessImpact]
        "flowdown_gaps": list,     # List[FlowdownGap]
        "_meta": dict,             # Optional metadata
    },
    "error_category": Optional[str],
    "error_message_key": Optional[str],
}

# Engine field specifications
SAE_FIELDS = ["v1_clause_id", "v2_clause_id", "similarity_score", "threshold_used", "match_confidence"]
ERCE_FIELDS = ["clause_pair_id", "risk_category", "pattern_ref", "success_probability", "confidence"]
BIRL_FIELDS = ["clause_pair_id", "narrative", "impact_dimensions", "token_count"]
FAR_FIELDS = ["gap_type", "severity", "upstream_value", "downstream_value", "recommendation"]


# ============================================================================
# DATA BINDING CLASS
# ============================================================================

@dataclass
class EngineOutputs:
    """Container for all four engine outputs with metadata."""
    sae_matches: List[Dict[str, Any]] = field(default_factory=list)
    erce_results: List[Dict[str, Any]] = field(default_factory=list)
    birl_narratives: List[Dict[str, Any]] = field(default_factory=list)
    flowdown_gaps: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    success: bool = False
    error_category: Optional[str] = None
    error_message_key: Optional[str] = None
    snapshot_id: Optional[int] = None
    created_at: Optional[str] = None
    intelligence_active: bool = False
    pipeline_status: str = "UNKNOWN"

    def is_valid(self) -> bool:
        """Check if response was successful."""
        return self.success

    def has_sae_data(self) -> bool:
        return len(self.sae_matches) > 0

    def has_erce_data(self) -> bool:
        return len(self.erce_results) > 0

    def has_birl_data(self) -> bool:
        return len(self.birl_narratives) > 0

    def has_far_data(self) -> bool:
        return len(self.flowdown_gaps) > 0

    def get_summary(self) -> Dict[str, int]:
        """Get count summary for all engines."""
        return {
            "sae_count": len(self.sae_matches),
            "erce_count": len(self.erce_results),
            "birl_count": len(self.birl_narratives),
            "far_count": len(self.flowdown_gaps),
        }


class CompareV3DataBinder:
    """
    Unified data binder for Compare v3 API responses.

    Handles extraction, validation, and binding of all four
    intelligence engine outputs to frontend state.
    """

    def __init__(self, api_response: Optional[Dict[str, Any]] = None):
        """Initialize with optional API response."""
        self._response = api_response
        self._outputs: Optional[EngineOutputs] = None
        self._validation_errors: List[str] = []

        if api_response:
            self.bind(api_response)

    def bind(self, api_response: Dict[str, Any]) -> "CompareV3DataBinder":
        """
        Bind API response to engine outputs.

        Args:
            api_response: Full Compare v3 API response

        Returns:
            Self for chaining
        """
        self._response = api_response
        self._validation_errors = []

        # Validate response shape
        is_valid, errors = validate_api_response_shape(api_response)
        self._validation_errors = errors

        # Extract all engine outputs
        self._outputs = extract_all_engine_outputs(api_response)

        return self

    def get_outputs(self) -> EngineOutputs:
        """Get extracted engine outputs."""
        if self._outputs is None:
            return EngineOutputs()
        return self._outputs

    def get_sae_matches(self) -> List[Dict[str, Any]]:
        """Get SAE semantic matches."""
        return self._outputs.sae_matches if self._outputs else []

    def get_erce_results(self) -> List[Dict[str, Any]]:
        """Get ERCE risk classifications."""
        return self._outputs.erce_results if self._outputs else []

    def get_birl_narratives(self) -> List[Dict[str, Any]]:
        """Get BIRL business impact narratives."""
        return self._outputs.birl_narratives if self._outputs else []

    def get_flowdown_gaps(self) -> List[Dict[str, Any]]:
        """Get FAR flowdown gaps."""
        return self._outputs.flowdown_gaps if self._outputs else []

    def is_valid(self) -> bool:
        """Check if binding was successful."""
        return self._outputs is not None and self._outputs.success

    def get_validation_errors(self) -> List[str]:
        """Get any validation errors encountered."""
        return self._validation_errors

    def store_in_session(self, key: str = "compare_v3_outputs") -> None:
        """Store outputs in Streamlit session state."""
        if self._outputs:
            st.session_state[key] = self._outputs

    @staticmethod
    def load_from_session(key: str = "compare_v3_outputs") -> Optional[EngineOutputs]:
        """Load outputs from Streamlit session state."""
        return st.session_state.get(key)


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_all_engine_outputs(api_response: Dict[str, Any]) -> EngineOutputs:
    """
    Extract all four engine outputs from Compare v3 API response.

    Args:
        api_response: Full Compare v3 API response

    Returns:
        EngineOutputs dataclass with all engine data
    """
    outputs = EngineOutputs()

    if not api_response:
        return outputs

    # Set success status
    outputs.success = api_response.get("success", False)
    outputs.error_category = api_response.get("error_category")
    outputs.error_message_key = api_response.get("error_message_key")

    if not outputs.success:
        return outputs

    # Get data payload
    data = api_response.get("data", {})

    # Extract metadata
    outputs.snapshot_id = data.get("id")
    outputs.created_at = data.get("created_at")

    meta = data.get("_meta", {})
    outputs.intelligence_active = api_response.get("intelligence_active", False)
    outputs.pipeline_status = meta.get("pipeline_status", "UNKNOWN")

    # Extract engine outputs using component functions
    outputs.sae_matches = extract_sae_data_from_v3_result(api_response)
    outputs.erce_results = extract_erce_data_from_v3_result(api_response)
    outputs.birl_narratives = extract_birl_data_from_v3_result(api_response)
    outputs.flowdown_gaps = extract_far_data_from_v3_result(api_response)

    return outputs


def validate_api_response_shape(api_response: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate API response matches Phase 5 shape specification.

    Args:
        api_response: API response to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if not api_response:
        errors.append("API response is null or empty")
        return False, errors

    if not isinstance(api_response, dict):
        errors.append(f"API response must be dict, got {type(api_response)}")
        return False, errors

    # Check required top-level field
    if "success" not in api_response:
        errors.append("Missing required field: success")

    # If success=True, validate data structure
    if api_response.get("success"):
        data = api_response.get("data")

        if data is None:
            errors.append("success=True but data field is missing")
        elif not isinstance(data, dict):
            errors.append(f"data must be dict, got {type(data)}")
        else:
            # Validate engine output arrays
            for field_name in ["sae_matches", "erce_results", "birl_narratives", "flowdown_gaps"]:
                field_value = data.get(field_name)
                if field_value is not None and not isinstance(field_value, list):
                    errors.append(f"{field_name} must be list, got {type(field_value)}")
    else:
        # If success=False, error fields should be present
        if not api_response.get("error_category") and not api_response.get("error_message_key"):
            errors.append("success=False but no error information provided")

    return len(errors) == 0, errors


def validate_engine_fields(engine: str, items: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate engine output items have required fields.

    Args:
        engine: Engine name (SAE, ERCE, BIRL, FAR)
        items: List of engine output items

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    field_specs = {
        "SAE": SAE_FIELDS,
        "ERCE": ERCE_FIELDS,
        "BIRL": BIRL_FIELDS,
        "FAR": FAR_FIELDS,
    }

    required_fields = field_specs.get(engine.upper(), [])

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{engine}[{idx}]: item must be dict, got {type(item)}")
            continue

        for field in required_fields:
            if field not in item:
                # Only warn for truly required fields (not Optional ones)
                if field not in ["pattern_ref", "success_probability"]:
                    errors.append(f"{engine}[{idx}]: missing field '{field}'")

    return len(errors) == 0, errors


# ============================================================================
# STATUS AND DIAGNOSTICS
# ============================================================================

def get_engine_status(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get status information for all engines from API response.

    Args:
        api_response: Full Compare v3 API response

    Returns:
        Dict with engine status information
    """
    outputs = extract_all_engine_outputs(api_response)

    return {
        "success": outputs.success,
        "intelligence_active": outputs.intelligence_active,
        "pipeline_status": outputs.pipeline_status,
        "engines": {
            "SAE": {
                "active": outputs.has_sae_data(),
                "count": len(outputs.sae_matches),
            },
            "ERCE": {
                "active": outputs.has_erce_data(),
                "count": len(outputs.erce_results),
            },
            "BIRL": {
                "active": outputs.has_birl_data(),
                "count": len(outputs.birl_narratives),
            },
            "FAR": {
                "active": outputs.has_far_data(),
                "count": len(outputs.flowdown_gaps),
            },
        },
        "error_category": outputs.error_category,
        "error_message_key": outputs.error_message_key,
    }


def run_integration_diagnostics(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full integration diagnostics on API response.

    Args:
        api_response: Full Compare v3 API response

    Returns:
        Diagnostic report dict
    """
    # Validate shape
    shape_valid, shape_errors = validate_api_response_shape(api_response)

    # Extract outputs
    outputs = extract_all_engine_outputs(api_response)

    # Validate each engine's fields
    sae_valid, sae_errors = validate_engine_fields("SAE", outputs.sae_matches)
    erce_valid, erce_errors = validate_engine_fields("ERCE", outputs.erce_results)
    birl_valid, birl_errors = validate_engine_fields("BIRL", outputs.birl_narratives)
    far_valid, far_errors = validate_engine_fields("FAR", outputs.flowdown_gaps)

    all_valid = shape_valid and sae_valid and erce_valid and birl_valid and far_valid

    return {
        "overall_valid": all_valid,
        "shape_validation": {
            "valid": shape_valid,
            "errors": shape_errors,
        },
        "engine_validation": {
            "SAE": {"valid": sae_valid, "errors": sae_errors},
            "ERCE": {"valid": erce_valid, "errors": erce_errors},
            "BIRL": {"valid": birl_valid, "errors": birl_errors},
            "FAR": {"valid": far_valid, "errors": far_errors},
        },
        "output_summary": outputs.get_summary(),
        "metadata": {
            "success": outputs.success,
            "intelligence_active": outputs.intelligence_active,
            "pipeline_status": outputs.pipeline_status,
        },
    }
