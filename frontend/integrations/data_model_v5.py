"""
Phase 5 Data Model Definitions
CIP Frontend Integration Layer

This module defines the canonical data models for the Phase 5 API shape,
providing type-safe structures for all four intelligence engines:
- SAE (Semantic Alignment Engine)
- ERCE (Enterprise Risk Classification Engine)
- BIRL (Business Impact & Risk Language)
- FAR (Flowdown Analysis & Requirements)

CC3 Task 5: API Data Model Update
Version: 5.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


# ============================================================================
# ENUMS - Canonical Value Sets
# ============================================================================

class SAEConfidence(str, Enum):
    """SAE match confidence levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ERCERiskCategory(str, Enum):
    """ERCE risk classification categories."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    ADMIN = "ADMIN"


class BIRLImpactDimension(str, Enum):
    """BIRL business impact dimensions."""
    MARGIN = "MARGIN"
    RISK = "RISK"
    COMPLIANCE = "COMPLIANCE"
    SCHEDULE = "SCHEDULE"
    QUALITY = "QUALITY"
    CASH_FLOW = "CASH_FLOW"
    ADMIN = "ADMIN"


class FARSeverity(str, Enum):
    """FAR flowdown gap severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"


class AIErrorCategory(str, Enum):
    """AI error categories from backend."""
    NETWORK_ERROR = "network_error"
    AUTH_ERROR = "auth_error"
    PAYLOAD_ERROR = "payload_error"
    INTERNAL_ERROR = "internal_error"


# ============================================================================
# SAE DATA MODEL
# ============================================================================

@dataclass
class ClauseMatch:
    """
    SAE Semantic Alignment Engine output.
    Represents a matched pair of clauses between V1 and V2 contracts.
    """
    v1_clause_id: int
    v2_clause_id: int
    similarity_score: float  # 0.0 to 1.0
    threshold_used: float    # Threshold applied for this match
    match_confidence: str    # HIGH | MEDIUM | LOW

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClauseMatch":
        """Create ClauseMatch from API response dict."""
        return cls(
            v1_clause_id=data.get("v1_clause_id", 0),
            v2_clause_id=data.get("v2_clause_id", 0),
            similarity_score=float(data.get("similarity_score", 0.0)),
            threshold_used=float(data.get("threshold_used", 0.6)),
            match_confidence=data.get("match_confidence", "LOW"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "v1_clause_id": self.v1_clause_id,
            "v2_clause_id": self.v2_clause_id,
            "similarity_score": self.similarity_score,
            "threshold_used": self.threshold_used,
            "match_confidence": self.match_confidence,
        }

    def is_high_confidence(self) -> bool:
        """Check if match is high confidence."""
        return self.match_confidence == SAEConfidence.HIGH.value


# ============================================================================
# ERCE DATA MODEL
# ============================================================================

@dataclass
class RiskDelta:
    """
    ERCE Enterprise Risk Classification Engine output.
    Represents risk classification for a clause pair.
    """
    clause_pair_id: int
    risk_category: str           # CRITICAL | HIGH | MODERATE | ADMIN
    pattern_ref: Optional[str]   # Pattern library reference (e.g., "UNLIMITED_LIABILITY")
    success_probability: Optional[float]  # Negotiation success probability (0.0-1.0)
    confidence: float            # ERCE confidence in classification (0.0-1.0)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskDelta":
        """Create RiskDelta from API response dict."""
        return cls(
            clause_pair_id=data.get("clause_pair_id", 0),
            risk_category=data.get("risk_category", "ADMIN"),
            pattern_ref=data.get("pattern_ref"),
            success_probability=data.get("success_probability"),
            confidence=float(data.get("confidence", 0.0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "clause_pair_id": self.clause_pair_id,
            "risk_category": self.risk_category,
            "pattern_ref": self.pattern_ref,
            "success_probability": self.success_probability,
            "confidence": self.confidence,
        }

    def is_critical(self) -> bool:
        """Check if risk is critical."""
        return self.risk_category == ERCERiskCategory.CRITICAL.value

    def is_actionable(self) -> bool:
        """Check if risk requires action (CRITICAL or HIGH)."""
        return self.risk_category in [
            ERCERiskCategory.CRITICAL.value,
            ERCERiskCategory.HIGH.value,
        ]


# ============================================================================
# BIRL DATA MODEL
# ============================================================================

@dataclass
class BusinessImpact:
    """
    BIRL Business Impact & Risk Language output.
    Represents AI-generated business impact narrative.
    """
    clause_pair_id: int
    narrative: str                      # Human-readable impact (max 150 tokens)
    impact_dimensions: List[str]        # List of impacted dimensions
    token_count: int                    # Token count of narrative

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessImpact":
        """Create BusinessImpact from API response dict."""
        return cls(
            clause_pair_id=data.get("clause_pair_id", 0),
            narrative=data.get("narrative", ""),
            impact_dimensions=data.get("impact_dimensions", ["ADMIN"]),
            token_count=int(data.get("token_count", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "clause_pair_id": self.clause_pair_id,
            "narrative": self.narrative,
            "impact_dimensions": self.impact_dimensions,
            "token_count": self.token_count,
        }

    def has_financial_impact(self) -> bool:
        """Check if narrative has financial dimensions."""
        financial_dims = [
            BIRLImpactDimension.MARGIN.value,
            BIRLImpactDimension.CASH_FLOW.value,
        ]
        return any(dim in self.impact_dimensions for dim in financial_dims)

    def has_risk_impact(self) -> bool:
        """Check if narrative has risk dimension."""
        return BIRLImpactDimension.RISK.value in self.impact_dimensions


# ============================================================================
# FAR DATA MODEL
# ============================================================================

@dataclass
class FlowdownGap:
    """
    FAR Flowdown Analysis & Requirements output.
    Represents a gap between prime and sub contract terms.
    """
    gap_type: str              # Type of gap (e.g., "Payment Terms", "Liability Cap")
    severity: str              # CRITICAL | HIGH | MODERATE
    upstream_value: str        # Value from prime contract
    downstream_value: str      # Value in sub contract
    recommendation: str        # Suggested resolution

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowdownGap":
        """Create FlowdownGap from API response dict."""
        return cls(
            gap_type=data.get("gap_type", "Unknown Gap"),
            severity=data.get("severity", "MODERATE"),
            upstream_value=data.get("upstream_value", "N/A"),
            downstream_value=data.get("downstream_value", "N/A"),
            recommendation=data.get("recommendation", "Review and address"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "gap_type": self.gap_type,
            "severity": self.severity,
            "upstream_value": self.upstream_value,
            "downstream_value": self.downstream_value,
            "recommendation": self.recommendation,
        }

    def is_critical(self) -> bool:
        """Check if gap is critical severity."""
        return self.severity == FARSeverity.CRITICAL.value

    def requires_immediate_action(self) -> bool:
        """Check if gap requires immediate resolution."""
        return self.severity in [
            FARSeverity.CRITICAL.value,
            FARSeverity.HIGH.value,
        ]


# ============================================================================
# COMPARISON SNAPSHOT (AGGREGATE)
# ============================================================================

@dataclass
class ComparisonSnapshot:
    """
    Aggregate container for all intelligence engine outputs.
    Represents a complete comparison result.
    """
    id: int
    v1_snapshot_id: int
    v2_snapshot_id: int
    created_at: str  # ISO timestamp

    # Engine outputs
    sae_matches: List[ClauseMatch] = field(default_factory=list)
    erce_results: List[RiskDelta] = field(default_factory=list)
    birl_narratives: List[BusinessImpact] = field(default_factory=list)
    flowdown_gaps: List[FlowdownGap] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComparisonSnapshot":
        """Create ComparisonSnapshot from API response data payload."""
        return cls(
            id=data.get("id", 0),
            v1_snapshot_id=data.get("v1_snapshot_id", 0),
            v2_snapshot_id=data.get("v2_snapshot_id", 0),
            created_at=data.get("created_at", ""),
            sae_matches=[
                ClauseMatch.from_dict(m)
                for m in data.get("sae_matches", [])
            ],
            erce_results=[
                RiskDelta.from_dict(r)
                for r in data.get("erce_results", [])
            ],
            birl_narratives=[
                BusinessImpact.from_dict(n)
                for n in data.get("birl_narratives", [])
            ],
            flowdown_gaps=[
                FlowdownGap.from_dict(g)
                for g in data.get("flowdown_gaps", [])
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "v1_snapshot_id": self.v1_snapshot_id,
            "v2_snapshot_id": self.v2_snapshot_id,
            "created_at": self.created_at,
            "sae_matches": [m.to_dict() for m in self.sae_matches],
            "erce_results": [r.to_dict() for r in self.erce_results],
            "birl_narratives": [n.to_dict() for n in self.birl_narratives],
            "flowdown_gaps": [g.to_dict() for g in self.flowdown_gaps],
        }

    def get_summary(self) -> Dict[str, int]:
        """Get count summary for all engines."""
        return {
            "sae_count": len(self.sae_matches),
            "erce_count": len(self.erce_results),
            "birl_count": len(self.birl_narratives),
            "far_count": len(self.flowdown_gaps),
        }

    def has_critical_items(self) -> bool:
        """Check if any critical items exist."""
        critical_erce = any(r.is_critical() for r in self.erce_results)
        critical_far = any(g.is_critical() for g in self.flowdown_gaps)
        return critical_erce or critical_far


# ============================================================================
# API RESPONSE WRAPPER
# ============================================================================

@dataclass
class CompareV3Result:
    """
    Full Compare v3 API response wrapper.
    Matches the Phase 5 API shape specification.
    """
    success: bool
    snapshot: Optional[ComparisonSnapshot] = None
    error_category: Optional[str] = None
    error_message_key: Optional[str] = None
    intelligence_active: bool = False

    # Metadata from _meta field
    engine_version: str = "3.0.0"
    pipeline_status: str = "UNKNOWN"

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "CompareV3Result":
        """Create CompareV3Result from full API response."""
        if not response:
            return cls(success=False, error_category="internal_error")

        success = response.get("success", False)
        snapshot = None

        if success:
            data = response.get("data", {})
            if data:
                snapshot = ComparisonSnapshot.from_dict(data)

        # Extract metadata
        meta = response.get("data", {}).get("_meta", {})

        return cls(
            success=success,
            snapshot=snapshot,
            error_category=response.get("error_category"),
            error_message_key=response.get("error_message_key"),
            intelligence_active=response.get("intelligence_active", False),
            engine_version=meta.get("engine_version", "3.0.0"),
            pipeline_status=meta.get("pipeline_status", "UNKNOWN"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        result = {
            "success": self.success,
            "error_category": self.error_category,
            "error_message_key": self.error_message_key,
            "intelligence_active": self.intelligence_active,
        }

        if self.snapshot:
            result["data"] = self.snapshot.to_dict()
            result["data"]["_meta"] = {
                "engine_version": self.engine_version,
                "pipeline_status": self.pipeline_status,
            }

        return result

    def is_valid(self) -> bool:
        """Check if response was successful with data."""
        return self.success and self.snapshot is not None

    def get_sae_matches(self) -> List[ClauseMatch]:
        """Get SAE matches or empty list."""
        return self.snapshot.sae_matches if self.snapshot else []

    def get_erce_results(self) -> List[RiskDelta]:
        """Get ERCE results or empty list."""
        return self.snapshot.erce_results if self.snapshot else []

    def get_birl_narratives(self) -> List[BusinessImpact]:
        """Get BIRL narratives or empty list."""
        return self.snapshot.birl_narratives if self.snapshot else []

    def get_flowdown_gaps(self) -> List[FlowdownGap]:
        """Get FAR flowdown gaps or empty list."""
        return self.snapshot.flowdown_gaps if self.snapshot else []


# ============================================================================
# FIELD SPECIFICATIONS (For Validation)
# ============================================================================

SAE_REQUIRED_FIELDS = [
    "v1_clause_id",
    "v2_clause_id",
    "similarity_score",
    "threshold_used",
    "match_confidence",
]

ERCE_REQUIRED_FIELDS = [
    "clause_pair_id",
    "risk_category",
    "confidence",
]

ERCE_OPTIONAL_FIELDS = [
    "pattern_ref",
    "success_probability",
]

BIRL_REQUIRED_FIELDS = [
    "clause_pair_id",
    "narrative",
    "impact_dimensions",
    "token_count",
]

FAR_REQUIRED_FIELDS = [
    "gap_type",
    "severity",
    "upstream_value",
    "downstream_value",
    "recommendation",
]

# Valid enum values
VALID_SAE_CONFIDENCE = [e.value for e in SAEConfidence]
VALID_ERCE_RISK_CATEGORY = [e.value for e in ERCERiskCategory]
VALID_BIRL_DIMENSIONS = [e.value for e in BIRLImpactDimension]
VALID_FAR_SEVERITY = [e.value for e in FARSeverity]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_sae_item(item: Dict[str, Any]) -> List[str]:
    """Validate SAE match item fields."""
    errors = []

    for field_name in SAE_REQUIRED_FIELDS:
        if field_name not in item:
            errors.append(f"Missing required SAE field: {field_name}")

    if "match_confidence" in item:
        if item["match_confidence"] not in VALID_SAE_CONFIDENCE:
            errors.append(f"Invalid match_confidence: {item['match_confidence']}")

    if "similarity_score" in item:
        score = item["similarity_score"]
        if not isinstance(score, (int, float)) or score < 0 or score > 1:
            errors.append(f"similarity_score must be 0.0-1.0: {score}")

    return errors


def validate_erce_item(item: Dict[str, Any]) -> List[str]:
    """Validate ERCE risk delta item fields."""
    errors = []

    for field_name in ERCE_REQUIRED_FIELDS:
        if field_name not in item:
            errors.append(f"Missing required ERCE field: {field_name}")

    if "risk_category" in item:
        if item["risk_category"] not in VALID_ERCE_RISK_CATEGORY:
            errors.append(f"Invalid risk_category: {item['risk_category']}")

    if "confidence" in item:
        conf = item["confidence"]
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            errors.append(f"confidence must be 0.0-1.0: {conf}")

    return errors


def validate_birl_item(item: Dict[str, Any]) -> List[str]:
    """Validate BIRL business impact item fields."""
    errors = []

    for field_name in BIRL_REQUIRED_FIELDS:
        if field_name not in item:
            errors.append(f"Missing required BIRL field: {field_name}")

    if "impact_dimensions" in item:
        dims = item["impact_dimensions"]
        if not isinstance(dims, list):
            errors.append(f"impact_dimensions must be list: {type(dims)}")
        else:
            for dim in dims:
                if dim not in VALID_BIRL_DIMENSIONS:
                    errors.append(f"Invalid impact_dimension: {dim}")

    return errors


def validate_far_item(item: Dict[str, Any]) -> List[str]:
    """Validate FAR flowdown gap item fields."""
    errors = []

    for field_name in FAR_REQUIRED_FIELDS:
        if field_name not in item:
            errors.append(f"Missing required FAR field: {field_name}")

    if "severity" in item:
        if item["severity"] not in VALID_FAR_SEVERITY:
            errors.append(f"Invalid FAR severity: {item['severity']}")

    return errors


def validate_api_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete API response against Phase 5 shape.

    Returns:
        Dict with 'valid' bool and 'errors' list
    """
    errors = []

    if not response:
        return {"valid": False, "errors": ["Response is null or empty"]}

    if not isinstance(response, dict):
        return {"valid": False, "errors": [f"Response must be dict: {type(response)}"]}

    # Check success field
    if "success" not in response:
        errors.append("Missing required field: success")

    # If success, validate data payload
    if response.get("success"):
        data = response.get("data")
        if not data:
            errors.append("success=True but data field is missing")
        elif not isinstance(data, dict):
            errors.append(f"data must be dict: {type(data)}")
        else:
            # Validate each engine's items
            for idx, item in enumerate(data.get("sae_matches", [])):
                item_errors = validate_sae_item(item)
                errors.extend([f"sae_matches[{idx}]: {e}" for e in item_errors])

            for idx, item in enumerate(data.get("erce_results", [])):
                item_errors = validate_erce_item(item)
                errors.extend([f"erce_results[{idx}]: {e}" for e in item_errors])

            for idx, item in enumerate(data.get("birl_narratives", [])):
                item_errors = validate_birl_item(item)
                errors.extend([f"birl_narratives[{idx}]: {e}" for e in item_errors])

            for idx, item in enumerate(data.get("flowdown_gaps", [])):
                item_errors = validate_far_item(item)
                errors.extend([f"flowdown_gaps[{idx}]: {e}" for e in item_errors])

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "5.0.0"
__phase__ = "Phase 5"
__engines__ = ["SAE", "ERCE", "BIRL", "FAR"]
