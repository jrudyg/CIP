"""
CIP Data Models
Dataclasses for AnalysisSnapshot, ComparisonSnapshot, ContractRelationship, and Redline models
v4.0: Added EPC fields, dealbreaker flag, flowdown impact to RedlineClause
v4.1: Added AIResult for unified cross-module error handling (Phase 4B)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Any


# ============================================================================
# PHASE 4B: UNIFIED AI ERROR FRAMEWORK
# ============================================================================

# Error category literals (CAI taxonomy)
AIErrorCategory = Literal["network_error", "auth_error", "payload_error", "internal_error"]

# Module purpose literals
AIModulePurpose = Literal["analyze", "compare", "redline", "chat"]

# Maximum retries per CAI policy
AI_MAX_RETRIES = 2

# Retry policy: which error categories allow retry
AI_RETRY_ALLOWED_CATEGORIES = ["network_error", "internal_error"]


@dataclass
class AIResult:
    """
    Phase 4B: Unified result wrapper for ALL Claude API calls.
    Used by Analyze v2, Compare v2, Redline v4, and future AI modules.

    Error Categories (CAI taxonomy):
    - network_error: Connectivity/TLS/DNS/timeouts (ConnectionResetError, Timeout, OSError, ssl.SSLError)
    - auth_error: Credential/config failures (HTTP 401/403)
    - payload_error: Bad request/token/size issues (HTTP 400/413/422)
    - internal_error: Everything else (JSON errors, model failures)

    Retry Policy (CAI):
    - MAX_RETRIES = 2
    - Retry only for network_error and internal_error
    - Auth + payload errors are NEVER retried

    Frontend Contract:
    - Uses error_message_key to lookup GEM copy
    - Shows retry button only if retry_allowed=True
    - Never displays raw exception text
    """
    success: bool
    data: Optional[Any] = None
    error_category: Optional[AIErrorCategory] = None
    error_message_key: Optional[str] = None
    retry_allowed: bool = False
    retry_count: int = 0
    max_retries: int = AI_MAX_RETRIES

    # Internal diagnostic fields (logged, never shown to UI)
    _exception_type: Optional[str] = field(default=None, repr=False)
    _module: Optional[AIModulePurpose] = field(default=None, repr=False)

    def to_api_response(self) -> dict:
        """Convert to JSON-safe dict for API response (excludes internal fields)."""
        return {
            'success': self.success,
            'data': self.data,
            'error_category': self.error_category,
            'error_message_key': self.error_message_key,
            'retry_allowed': self.retry_allowed,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

    @classmethod
    def success_result(cls, data: Any, module: AIModulePurpose = None) -> 'AIResult':
        """Factory for successful results."""
        return cls(success=True, data=data, _module=module)

    @classmethod
    def error_result(
        cls,
        error_category: AIErrorCategory,
        error_message_key: str,
        module: AIModulePurpose = None,
        exception_type: str = None,
        retry_count: int = 0
    ) -> 'AIResult':
        """Factory for error results with automatic retry_allowed calculation."""
        retry_allowed = (
            error_category in AI_RETRY_ALLOWED_CATEGORIES and
            retry_count < AI_MAX_RETRIES
        )
        return cls(
            success=False,
            error_category=error_category,
            error_message_key=error_message_key,
            retry_allowed=retry_allowed,
            retry_count=retry_count,
            _exception_type=exception_type,
            _module=module
        )


# Error message key mappings by module (maps to GEM copy in frontend)
AI_ERROR_KEYS = {
    "analyze": {
        "network_error": "analyze.network_failure",
        "auth_error": "analyze.auth_failure",
        "payload_error": "analyze.payload_failure",
        "internal_error": "analyze.internal_failure",
    },
    "compare": {
        "network_error": "compare.network_failure",
        "auth_error": "compare.auth_failure",
        "payload_error": "compare.payload_failure",
        "internal_error": "compare.internal_failure",
    },
    "redline": {
        "network_error": "redline.network_failure",
        "auth_error": "redline.auth_failure",
        "payload_error": "redline.payload_failure",
        "internal_error": "redline.internal_failure",
    },
    "chat": {
        "network_error": "chat.network_failure",
        "auth_error": "chat.auth_failure",
        "payload_error": "chat.payload_failure",
        "internal_error": "chat.internal_failure",
    },
}


# ============================================================================
# REDLINE v4 DATA MODELS
# ============================================================================

RedlineStatus = Literal["suggested", "accepted", "modified", "rejected", "needs_cm_legal_review"]

# Contract position for flowdown analysis
ContractPosition = Literal["upstream", "downstream", "teaming", "other"]

# Risk priority levels for clause ordering
RiskPriority = Literal["CRITICAL", "HIGH", "MODERATE", "ADMINISTRATIVE"]

# Snapshot status
SnapshotStatus = Literal["draft", "complete"]

# Critical categories requiring 0.93 confidence threshold
CRITICAL_CATEGORIES = ["liability", "indemnity", "ip", "intellectual_property", "limitation_of_liability"]

# Standard confidence threshold
CONFIDENCE_THRESHOLD_STANDARD = 0.85

# Critical confidence threshold
CONFIDENCE_THRESHOLD_CRITICAL = 0.93


@dataclass
class RedlineClause:
    """
    Represents a single clause with redline suggestion.
    Created by the Redline engine; displayed in Redline Review page.
    v4: Added EPC fields, dealbreaker flag, flowdown impact
    """
    clause_id: int              # index from Analyze clause list
    section_number: str
    title: str
    risk_category: str
    current_text: str
    suggested_text: str
    rationale: str
    pattern_ref: Optional[str]
    confidence: float
    status: RedlineStatus
    user_notes: Optional[str]
    # v4: New fields
    success_probability: Optional[float]   # EPC: probability of successful negotiation (0-1)
    leverage_context: Optional[str]        # EPC: quality / schedule / margin impact
    flowdown_impact: Optional[str]         # Flowdown gap analysis result
    dealbreaker_flag: bool                 # True if clause triggers dealbreaker pattern
    risk_priority: Optional[RiskPriority]  # CRITICAL / HIGH / MODERATE / ADMINISTRATIVE


@dataclass
class RedlineSnapshot:
    """
    Stores a complete redline session for a contract.
    Contains all clause-level suggestions and their statuses.
    v4: Added status field and contract_position
    """
    redline_id: int
    contract_id: int
    base_version_contract_id: int
    source_mode: str           # "single" | "compare"
    created_at: str
    overall_risk_before: str
    overall_risk_after: Optional[str]
    clauses: List[RedlineClause]
    # v4: New fields
    status: SnapshotStatus     # "draft" during generation, "complete" after export
    contract_position: Optional[ContractPosition]  # upstream / downstream / teaming / other
    dealbreakers_detected: int  # Count of dealbreaker clauses found


@dataclass
class AnalysisSnapshot:
    """
    Stores a point-in-time analysis of a contract.
    Created by the Analyze module; consumed by Compare and Redline.
    """
    snapshot_id: int
    contract_id: int
    created_at: str  # ISO timestamp
    overall_risk: str  # "low" | "medium" | "high" | "critical"
    categories: list  # List of {name, risk, clauseCount}
    clauses: list  # List of {clauseId, number, title, category, severity}


@dataclass
class ComparisonSnapshot:
    """
    Stores a comparison between two contract versions.
    References AnalysisSnapshots for risk data.
    """
    comparison_id: int
    v1_contract_id: int
    v2_contract_id: int
    v1_snapshot_id: int | None  # AnalysisSnapshot.snapshot_id for V1
    v2_snapshot_id: int | None  # AnalysisSnapshot.snapshot_id for V2
    similarity_score: float  # 0-100
    changed_clauses: list  # List of {clauseId, category, type, severityDelta, summary}
    risk_delta: list  # List of {category, v1Risk, v2Risk}


@dataclass
class ContractRelationship:
    """
    Defines relationships between contracts (parent/child, versions).
    """
    contract_id: int
    parent_id: int | None  # Master or umbrella contract ID
    children: list  # List of child contract IDs (SOWs, exhibits, amendments)
    versions: list  # Ordered list of version IDs for this contract lineage
