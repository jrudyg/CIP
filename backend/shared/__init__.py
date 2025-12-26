"""
Shared Module — P7

Shared contracts and types between frontend and backend.
"""

from .p7_streaming_contract import (
    P7ConnectionState,
    P7EventType,
    P7TimingSpec,
    P7_TIMING,
    P7EventEnvelopeSchema,
    P7GapDetectionRules,
    P7_GAP_RULES,
    P7ScrollSyncEvent,
    P7HighlightEvent,
    P7ObservabilityHooks,
    P7_CONTRACT_VERSION,
    P7_CONTRACT_STATUS,
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
