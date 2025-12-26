"""
SSE Backend Package for P7 Streaming.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

This package provides Server-Sent Events (SSE) functionality for the
CIP intelligence pipeline, enabling real-time streaming of:
- Engine execution events
- Stage activation notifications
- Flag change broadcasts
- Connection lifecycle management

Components:
- handler: SSEHandler with lifecycle state machine
- envelope: EventEnvelope and EventType definitions
- sequence: Sequence generators (memory, database, redis)
- replay: Event buffering and replay on reconnection
- middleware: Auth, rate limiting, version checking
- exceptions: SSE-specific error types

CIP Protocol: This package is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

from .envelope import EventEnvelope, EventType
from .exceptions import (
    BackpressureError,
    ConnectionClosedError,
    InvalidSessionError,
    RateLimitExceededError,
    SSEBaseException,
    SSEInternalError,
    VersionMismatchError,
)
from .handler import (
    ConnectionState,
    HandlerConfig,
    SSEHandler,
    SSEHandlerFactory,
)
from .middleware import (
    AuthMiddleware,
    MiddlewareBase,
    MiddlewareChain,
    MiddlewareContext,
    RateLimitMiddleware,
    VersionCheckMiddleware,
    create_default_middleware_chain,
)
from .replay import (
    BufferConfig,
    EventBuffer,
    ReplayController,
    ReplayRequest,
    ReplayResult,
    create_replay_controller,
)
from .sequence import (
    DatabaseSequenceGenerator,
    InMemorySequenceGenerator,
    ISequenceGenerator,
    RedisSequenceGenerator,
    SequenceGeneratorBase,
    TimestampSequenceGenerator,
    create_sequence_generator,
)

__version__ = "7.0.0"
__phase__ = "P7.S1"
__author__ = "CC1 (Backend Mechanic)"

__all__ = [
    # Envelope
    "EventEnvelope",
    "EventType",
    # Handler
    "SSEHandler",
    "SSEHandlerFactory",
    "HandlerConfig",
    "ConnectionState",
    # Sequence
    "ISequenceGenerator",
    "SequenceGeneratorBase",
    "InMemorySequenceGenerator",
    "DatabaseSequenceGenerator",
    "RedisSequenceGenerator",
    "TimestampSequenceGenerator",
    "create_sequence_generator",
    # Replay
    "EventBuffer",
    "ReplayController",
    "ReplayRequest",
    "ReplayResult",
    "BufferConfig",
    "create_replay_controller",
    # Middleware
    "MiddlewareBase",
    "MiddlewareChain",
    "MiddlewareContext",
    "AuthMiddleware",
    "RateLimitMiddleware",
    "VersionCheckMiddleware",
    "create_default_middleware_chain",
    # Exceptions
    "SSEBaseException",
    "InvalidSessionError",
    "VersionMismatchError",
    "RateLimitExceededError",
    "SSEInternalError",
    "ConnectionClosedError",
    "BackpressureError",
]
