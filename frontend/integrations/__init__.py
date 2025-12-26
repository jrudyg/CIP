"""
CIP Frontend Integrations Module
Phase 5 - Intelligence Engine Data Layer
Phase 6 - Workspace Mode Preparation

This module provides consolidated data binding and extraction
for all four intelligence engines (SAE, ERCE, BIRL, FAR),
plus Phase 6 workspace mode support.
"""

# Data Models (Phase 5 API Shape)
from .data_model_v5 import (
    # Enums
    SAEConfidence,
    ERCERiskCategory,
    BIRLImpactDimension,
    FARSeverity,
    AIErrorCategory,
    # Data Classes
    ClauseMatch,
    RiskDelta,
    BusinessImpact,
    FlowdownGap,
    ComparisonSnapshot,
    CompareV3Result,
    # Validation
    validate_api_response,
    validate_sae_item,
    validate_erce_item,
    validate_birl_item,
    validate_far_item,
    # Field Specs
    SAE_REQUIRED_FIELDS,
    ERCE_REQUIRED_FIELDS,
    BIRL_REQUIRED_FIELDS,
    FAR_REQUIRED_FIELDS,
)

# Integration Layer
from .compare_v3_integration import (
    CompareV3DataBinder,
    EngineOutputs,
    extract_all_engine_outputs,
    validate_api_response_shape,
    get_engine_status,
    run_integration_diagnostics,
)

# Phase 6 Workspace Mode (Prep)
from .workspace_mode import (
    # Enums
    PanelPosition,
    ScrollSyncMode,
    WorkspaceViewMode,
    SSEEventType,
    # Data Classes
    ClausePosition,
    AlignedClausePair,
    ScrollState,
    WorkspaceState,
    ClauseDataPacket,
    SSEEvent,
    # Engines
    ScrollSyncEngine,
    MultiClauseDataFlow,
    SSEStreamHandler,
)

__all__ = [
    # Phase 5 Enums
    "SAEConfidence",
    "ERCERiskCategory",
    "BIRLImpactDimension",
    "FARSeverity",
    "AIErrorCategory",
    # Phase 5 Data Classes
    "ClauseMatch",
    "RiskDelta",
    "BusinessImpact",
    "FlowdownGap",
    "ComparisonSnapshot",
    "CompareV3Result",
    # Phase 5 Validation
    "validate_api_response",
    "validate_sae_item",
    "validate_erce_item",
    "validate_birl_item",
    "validate_far_item",
    # Phase 5 Field Specs
    "SAE_REQUIRED_FIELDS",
    "ERCE_REQUIRED_FIELDS",
    "BIRL_REQUIRED_FIELDS",
    "FAR_REQUIRED_FIELDS",
    # Phase 5 Integration
    "CompareV3DataBinder",
    "EngineOutputs",
    "extract_all_engine_outputs",
    "validate_api_response_shape",
    "get_engine_status",
    "run_integration_diagnostics",
    # Phase 6 Enums
    "PanelPosition",
    "ScrollSyncMode",
    "WorkspaceViewMode",
    "SSEEventType",
    # Phase 6 Data Classes
    "ClausePosition",
    "AlignedClausePair",
    "ScrollState",
    "WorkspaceState",
    "ClauseDataPacket",
    "SSEEvent",
    # Phase 6 Engines
    "ScrollSyncEngine",
    "MultiClauseDataFlow",
    "SSEStreamHandler",
]
