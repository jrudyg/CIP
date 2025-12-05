"""
Compare v3 Data Models - Phase 4E Implementation
Dataclasses for SAE/ERCE/BIRL/FAR pipeline components.

Phase 4E: Infrastructure only - no real semantics.
All logic uses deterministic placeholders for test safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================================
# SAE (Semantic Alignment Engine) MODELS
# ============================================================================

@dataclass
class ClauseMatch:
    """
    Represents a matched clause pair between two contract versions.

    SAE output - identifies which clauses in v1 correspond to v2.
    """
    v1_clause_id: int
    v2_clause_id: int
    similarity_score: float  # 0.0 to 1.0
    threshold_used: float  # The threshold applied for this match
    match_confidence: str  # "HIGH" | "MEDIUM" | "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "v1_clause_id": self.v1_clause_id,
            "v2_clause_id": self.v2_clause_id,
            "similarity_score": self.similarity_score,
            "threshold_used": self.threshold_used,
            "match_confidence": self.match_confidence,
        }


# ============================================================================
# ERCE (Enterprise Risk Classification Engine) MODELS
# ============================================================================

@dataclass
class RiskDelta:
    """
    Represents a risk change between matched clause pairs.

    ERCE output - classifies risk severity and provides probability.
    """
    clause_pair_id: int
    risk_category: str  # "CRITICAL" | "HIGH" | "MODERATE" | "ADMIN"
    pattern_ref: Optional[str]  # Reference to risk pattern, if matched
    success_probability: Optional[float]  # Probability of successful negotiation
    confidence: float  # ERCE confidence in this classification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_pair_id": self.clause_pair_id,
            "risk_category": self.risk_category,
            "pattern_ref": self.pattern_ref,
            "success_probability": self.success_probability,
            "confidence": self.confidence,
        }


# ============================================================================
# BIRL (Business Impact & Risk Language) MODELS
# ============================================================================

@dataclass
class BusinessImpact:
    """
    Represents the business impact narrative for a clause change.

    BIRL output - human-readable impact explanation.
    """
    clause_pair_id: int
    narrative: str  # Human-readable impact description
    impact_dimensions: List[str]  # ["MARGIN", "RISK", "COMPLIANCE", etc.]
    token_count: int  # Token count for narrative (for cost tracking)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_pair_id": self.clause_pair_id,
            "narrative": self.narrative,
            "impact_dimensions": self.impact_dimensions,
            "token_count": self.token_count,
        }


# ============================================================================
# FAR (Flowdown Analysis & Requirements) MODELS
# ============================================================================

@dataclass
class FlowdownGap:
    """
    Represents a gap in flowdown requirements between contracts.

    FAR output - identifies compliance gaps in contract hierarchy.
    """
    gap_type: str  # Type of gap identified
    severity: str  # "CRITICAL" | "HIGH" | "MODERATE"
    upstream_value: str  # Value from upstream (prime) contract
    downstream_value: str  # Value in downstream (sub) contract
    recommendation: str  # Suggested resolution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_type": self.gap_type,
            "severity": self.severity,
            "upstream_value": self.upstream_value,
            "downstream_value": self.downstream_value,
            "recommendation": self.recommendation,
        }


# ============================================================================
# COMPARISON SNAPSHOT (AGGREGATE)
# ============================================================================

@dataclass
class ComparisonSnapshot:
    """
    Complete snapshot of a Compare v3 analysis.

    Aggregates all pipeline outputs into a single serializable structure.
    """
    id: int
    v1_snapshot_id: int
    v2_snapshot_id: int
    created_at: datetime
    sae_matches: List[ClauseMatch] = field(default_factory=list)
    erce_results: List[RiskDelta] = field(default_factory=list)
    birl_narratives: List[BusinessImpact] = field(default_factory=list)
    flowdown_gaps: List[FlowdownGap] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "v1_snapshot_id": self.v1_snapshot_id,
            "v2_snapshot_id": self.v2_snapshot_id,
            "created_at": self.created_at.isoformat(),
            "sae_matches": [m.to_dict() for m in self.sae_matches],
            "erce_results": [r.to_dict() for r in self.erce_results],
            "birl_narratives": [n.to_dict() for n in self.birl_narratives],
            "flowdown_gaps": [g.to_dict() for g in self.flowdown_gaps],
        }


# ============================================================================
# COMPARE V3 RESULT (API RESPONSE SHAPE)
# ============================================================================

@dataclass
class CompareV3Result:
    """
    Result container for Compare v3 API responses.
    """
    success: bool
    snapshot: Optional[ComparisonSnapshot] = None
    error_category: Optional[str] = None
    error_message_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"success": self.success}
        if self.snapshot:
            result["data"] = self.snapshot.to_dict()
        if self.error_category:
            result["error_category"] = self.error_category
        if self.error_message_key:
            result["error_message_key"] = self.error_message_key
        return result
