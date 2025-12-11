"""
Session State Package for P7 Streaming Backend.

Phase: P7.S2
Author: CC1 (Backend Mechanic)
Directive: S2.T1_SESSION_STATE_MODELS

This package provides session state management for SSE connections:
- Session lifecycle tracking
- Connection metadata persistence
- Multi-client session coordination
- State recovery on reconnection

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

from .models import (
    SessionState,
    SessionStatus,
    SessionMetadata,
    SessionConfig,
)
from .repository import (
    ISessionRepository,
    InMemorySessionRepository,
    SessionRepositoryError,
    SessionNotFoundError,
    SessionAlreadyExistsError,
)

__version__ = "7.0.0"
__phase__ = "P7.S2"
__author__ = "CC1 (Backend Mechanic)"

__all__ = [
    # Models
    "SessionState",
    "SessionStatus",
    "SessionMetadata",
    "SessionConfig",
    # Repository
    "ISessionRepository",
    "InMemorySessionRepository",
    "SessionRepositoryError",
    "SessionNotFoundError",
    "SessionAlreadyExistsError",
]
