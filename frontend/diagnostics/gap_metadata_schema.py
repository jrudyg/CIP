"""
Gap Metadata Schema for P7 Sequence Integrity Observability

GEM Task 8 - Gap Metadata Reporting
CC3 Implementation

This module defines the schema for sequence gap reporting, enabling
comprehensive observability of SSE stream integrity issues.
"""

from typing import TypedDict, List, Literal, Optional


# --- CLASSIFICATION ENUMS ---
GapSeverity = Literal["INFO", "WARN", "CRITICAL"]
GapLifecycle = Literal["DETECTED", "CLASSIFIED", "REPLAY_PENDING", "REPLAY_INITIATED", "RESOLVED", "TERMINATED"]
GapProvenance = Literal["NETWORK_LOSS", "BACKEND_FAILURE", "REPLAY_ERROR", "FLOWDOWN"]


# --- GAP METADATA SCHEMA ---

class GapMetadata(TypedDict):
    """Schema for a single sequence gap report entry."""
    gap_id: str
    detection_timestamp: str
    start_sequence: int
    end_sequence: int
    severity: GapSeverity
    provenance: GapProvenance
    lifecycle_state: GapLifecycle
    metadata: Optional[dict]
    resolution_sequence: Optional[int]


class GapReport(TypedDict):
    """Container for all open and recently closed gaps."""
    open_gaps: List[GapMetadata]
    resolved_gaps_24h: List[GapMetadata]


__version__ = "1.0.0"
__phase__ = "P7.S2"
__task__ = "Task 8 - Gap Metadata Reporting"
