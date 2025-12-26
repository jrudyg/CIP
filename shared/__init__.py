"""
Shared Contracts Package.

This package contains cross-domain contracts shared between
frontend and backend components.

Phase: P7
"""

from .p7_streaming_contract import (
    P7_CONTRACT_STATUS,
    P7_CONTRACT_VERSION,
    P7_GAP_RULES,
    P7_TIMING,
    P7ConnectionState,
    P7EventEnvelopeSchema,
    P7EventType,
    P7GapDetectionRules,
    P7HighlightEvent,
    P7ObservabilityHooks,
    P7ScrollSyncEvent,
    P7TimingSpec,
)

__all__ = [
    "P7ConnectionState",
    "P7EventType",
    "P7TimingSpec",
    "P7_TIMING",
    "P7EventEnvelopeSchema",
    "P7GapDetectionRules",
    "P7_GAP_RULES",
    "P7ScrollSyncEvent",
    "P7HighlightEvent",
    "P7ObservabilityHooks",
    "P7_CONTRACT_VERSION",
    "P7_CONTRACT_STATUS",
]
