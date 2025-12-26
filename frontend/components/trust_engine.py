"""
TRUST Protocol Engine - Phase 4C Implementation
Evaluates trust conditions and generates advisory flags.

FROZEN SPEC:
- NEVER blocks action (T=0 ms trigger)
- Backend call ALWAYS proceeds
- blocking = False (ALWAYS)
- Flags: stale_snapshot, ai_degraded, ai_unavailable, high_risk, multi
"""

import streamlit as st
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum


# ============================================================================
# HEALTH STATUS ENUM
# ============================================================================

class HealthStatus(Enum):
    """AI health status levels"""
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


# ============================================================================
# TRUST CONTEXT DATACLASS (FROZEN SPEC)
# ============================================================================

@dataclass
class TrustContext:
    """
    Trust evaluation context - Phase 4C Frozen Spec.

    Attributes:
        flags: List of active flag strings ["stale_snapshot", "ai_degraded", ...]
        advisory_level: "clear" | "stale_snapshot" | "ai_degraded" | "ai_unavailable" | "high_risk" | "multi"
        message_keys: List of microcopy keys ["trust.stale_snapshot", ...]
        blocking: ALWAYS False - TRUST never blocks actions
    """
    flags: List[str] = field(default_factory=list)
    advisory_level: str = "clear"
    message_keys: List[str] = field(default_factory=list)
    blocking: bool = False  # ALWAYS FALSE - FROZEN SPEC

    def is_clear(self) -> bool:
        """Check if no trust issues"""
        return len(self.flags) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response embedding"""
        return {
            "flags": self.flags,
            "advisory_level": self.advisory_level,
            "message_keys": self.message_keys,
            "blocking": self.blocking,
        }


# ============================================================================
# CONFIGURATION
# ============================================================================

SNAPSHOT_STALE_DAYS = 7  # Snapshots older than 7 days are stale


# ============================================================================
# AI HEALTH CHECK
# ============================================================================

def get_ai_health_status() -> HealthStatus:
    """
    Get current AI health status from zone_layout health check.

    Returns:
        HealthStatus enum value
    """
    try:
        from zone_layout import check_system_health
        _, _, ai_healthy = check_system_health()
        return HealthStatus.OK if ai_healthy else HealthStatus.UNAVAILABLE
    except Exception:
        return HealthStatus.UNAVAILABLE


# ============================================================================
# TRUST EVALUATION ENGINE
# ============================================================================

def evaluate_trust(
    contract_id: int,
    last_analyzed_at: Optional[datetime] = None,
    risk_level: Optional[str] = None,
) -> TrustContext:
    """
    Evaluate trust conditions for a contract operation.

    FROZEN SPEC:
    - Called IMMEDIATELY on button click (before API call)
    - NEVER blocks action
    - Returns TrustContext with flags and advisory_level
    - blocking = False ALWAYS

    Args:
        contract_id: Contract identifier
        last_analyzed_at: Timestamp of last analysis (ContractRecord.last_analyzed_at)
        risk_level: Contract risk level ("low", "medium", "high", "critical")

    Returns:
        TrustContext with evaluated flags
    """
    flags: List[str] = []

    # -------------------------------------------------------------------------
    # A. Snapshot Freshness Check
    # stale_snapshot = (now - ContractRecord.last_analyzed_at) > 7 days
    # -------------------------------------------------------------------------
    if last_analyzed_at is not None:
        age = datetime.now() - last_analyzed_at
        if age > timedelta(days=SNAPSHOT_STALE_DAYS):
            flags.append("stale_snapshot")

    # -------------------------------------------------------------------------
    # B. AI Health Check
    # ai_status: "ok" -> no flag, "degraded" -> ai_degraded, "unavailable" -> ai_unavailable
    # -------------------------------------------------------------------------
    ai_status = get_ai_health_status()

    if ai_status == HealthStatus.UNAVAILABLE:
        flags.append("ai_unavailable")
    elif ai_status == HealthStatus.DEGRADED:
        flags.append("ai_degraded")
    # HealthStatus.OK -> no flag added

    # -------------------------------------------------------------------------
    # C. Risk Tier Check
    # if contract.risk_level in ("high", "critical"): add "high_risk"
    # -------------------------------------------------------------------------
    if risk_level is not None and risk_level.lower() in ("high", "critical"):
        flags.append("high_risk")

    # -------------------------------------------------------------------------
    # D. Advisory-Level Resolution Logic
    # if no flags -> advisory_level = "clear"
    # if 1 flag   -> advisory_level = flag_type
    # if >=2 flags -> advisory_level = "multi"
    # -------------------------------------------------------------------------
    if len(flags) == 0:
        advisory_level = "clear"
    elif len(flags) == 1:
        advisory_level = flags[0]
    else:
        advisory_level = "multi"

    # -------------------------------------------------------------------------
    # E. Construct Keys
    # message_keys = [f"trust.{flag}" for flag in flags]
    # -------------------------------------------------------------------------
    message_keys = [f"trust.{flag}" for flag in flags]

    # -------------------------------------------------------------------------
    # F. NEVER BLOCK
    # blocking = False (ALWAYS)
    # -------------------------------------------------------------------------
    return TrustContext(
        flags=flags,
        advisory_level=advisory_level,
        message_keys=message_keys,
        blocking=False,  # FROZEN SPEC: NEVER BLOCKS
    )


# ============================================================================
# TRUST STATE MANAGEMENT (SESSION)
# ============================================================================

def get_current_trust_state() -> Optional[TrustContext]:
    """Get current trust state from session"""
    return st.session_state.get("_trust_state")


def set_trust_state(state: TrustContext):
    """Set trust state in session"""
    st.session_state["_trust_state"] = state


def clear_trust_state():
    """Clear trust state from session"""
    if "_trust_state" in st.session_state:
        del st.session_state["_trust_state"]


# ============================================================================
# CONVENIENCE FUNCTION FOR PAGE INTEGRATION
# ============================================================================

def run_trust_precheck(
    contract_id: int,
    last_analyzed_at: Optional[datetime] = None,
    risk_level: Optional[str] = None,
) -> TrustContext:
    """
    Run trust precheck and store in session.

    FROZEN SPEC:
    - Must be called IMMEDIATELY on button click
    - BEFORE any backend call
    - NEVER blocks the operation

    Args:
        contract_id: Contract identifier
        last_analyzed_at: From ContractRecord.last_analyzed_at
        risk_level: Contract risk level

    Returns:
        TrustContext for banner rendering
    """
    trust = evaluate_trust(
        contract_id=contract_id,
        last_analyzed_at=last_analyzed_at,
        risk_level=risk_level,
    )
    set_trust_state(trust)
    return trust
