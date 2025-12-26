"""
SSE Handler for P7 Streaming Backend.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

Defines:
- SSEHandler class with lifecycle state machine
- HANDSHAKE_COMPLETE emission
- Keepalive scheduler
- Backpressure handling stub
- Frame formatting

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from .envelope import EventEnvelope, EventType
from .exceptions import (
    BackpressureError,
    ConnectionClosedError,
    InvalidSessionError,
    SSEInternalError,
)
from .middleware import MiddlewareChain, MiddlewareContext
from .replay import EventBuffer, ReplayController, ReplayRequest
from .sequence import ISequenceGenerator, InMemorySequenceGenerator

# Diagnostic logging hook
logger = logging.getLogger("sse.handler")


class ConnectionState(Enum):
    """SSE connection lifecycle states."""

    INITIALIZING = auto()
    HANDSHAKING = auto()
    REPLAYING = auto()
    CONNECTED = auto()
    PAUSED = auto()
    BACKPRESSURE = auto()
    CLOSING = auto()
    CLOSED = auto()
    ERROR = auto()


@dataclass
class HandlerConfig:
    """Configuration for SSEHandler."""

    keepalive_interval_seconds: float = 30.0
    handshake_timeout_seconds: float = 10.0
    backpressure_threshold: int = 100
    max_queue_size: int = 1000
    server_version: str = "1.0.0"
    capabilities: Dict[str, Any] = field(default_factory=lambda: {
        "replay": True,
        "backpressure": True,
        "keepalive": True
    })


@dataclass
class ConnectionMetrics:
    """Metrics for an SSE connection."""

    connected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    events_sent: int = 0
    bytes_sent: int = 0
    keepalives_sent: int = 0
    replays_performed: int = 0
    backpressure_events: int = 0
    last_event_at: Optional[str] = None
    state_transitions: List[str] = field(default_factory=list)


class SSEHandler:
    """
    Server-Sent Events handler with lifecycle management.

    Features:
    - State machine for connection lifecycle
    - Handshake protocol with HANDSHAKE_COMPLETE
    - Keepalive scheduler
    - Backpressure handling
    - Event replay on reconnection
    - Frame formatting
    """

    def __init__(
        self,
        session_id: str,
        config: Optional[HandlerConfig] = None,
        sequence_generator: Optional[ISequenceGenerator] = None,
        event_buffer: Optional[EventBuffer] = None,
        replay_controller: Optional[ReplayController] = None,
        middleware_chain: Optional[MiddlewareChain] = None
    ) -> None:
        """
        Initialize SSE handler.

        Args:
            session_id: Unique session identifier
            config: Handler configuration
            sequence_generator: Sequence number generator
            event_buffer: Buffer for event storage
            replay_controller: Controller for event replay
            middleware_chain: Middleware chain for request processing
        """
        self._session_id = session_id
        self._config = config or HandlerConfig()
        self._sequence_generator = sequence_generator or InMemorySequenceGenerator()
        self._event_buffer = event_buffer
        self._replay_controller = replay_controller
        self._middleware_chain = middleware_chain

        # State management
        self._state = ConnectionState.INITIALIZING
        self._state_lock = asyncio.Lock()

        # Event queue for backpressure
        self._event_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self._config.max_queue_size
        )

        # Keepalive task
        self._keepalive_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = ConnectionMetrics()

        # Callbacks
        self._on_state_change: Optional[Callable[[ConnectionState], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

        logger.info(f"SSEHandler created: session={session_id}")

    @property
    def session_id(self) -> str:
        """Get session identifier."""
        return self._session_id

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def metrics(self) -> ConnectionMetrics:
        """Get connection metrics."""
        return self._metrics

    async def _set_state(self, new_state: ConnectionState) -> None:
        """
        Transition to a new state.

        Args:
            new_state: Target state
        """
        async with self._state_lock:
            old_state = self._state
            self._state = new_state
            self._metrics.state_transitions.append(
                f"{old_state.name}->{new_state.name}@{datetime.now().isoformat()}"
            )

        logger.info(f"State transition: {old_state.name} -> {new_state.name}")

        if self._on_state_change:
            self._on_state_change(new_state)

    async def initialize(
        self,
        context: Optional[MiddlewareContext] = None
    ) -> bool:
        """
        Initialize the SSE connection.

        Args:
            context: Optional middleware context

        Returns:
            True if initialization successful
        """
        try:
            await self._set_state(ConnectionState.HANDSHAKING)

            # Process middleware if provided
            if self._middleware_chain and context:
                try:
                    context = self._middleware_chain.process(context)
                except Exception as e:
                    logger.error(f"Middleware failed: {e}")
                    await self._set_state(ConnectionState.ERROR)
                    raise

            logger.debug(f"Handler initialized: session={self._session_id}")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            await self._set_state(ConnectionState.ERROR)
            return False

    async def handshake(self) -> EventEnvelope:
        """
        Perform connection handshake.

        Returns:
            HANDSHAKE_COMPLETE event envelope
        """
        if self._state != ConnectionState.HANDSHAKING:
            raise SSEInternalError(
                message="Invalid state for handshake",
                component="handler",
                operation="handshake"
            )

        # Generate handshake complete event
        event_id = f"hs_{uuid.uuid4().hex[:8]}"
        sequence = self._sequence_generator.next()

        handshake_event = EventEnvelope.create_handshake_complete(
            event_id=event_id,
            sequence=sequence,
            session_id=self._session_id,
            server_version=self._config.server_version,
            capabilities=self._config.capabilities
        )

        # Transition to connected state
        await self._set_state(ConnectionState.CONNECTED)

        # Start keepalive scheduler
        await self._start_keepalive()

        logger.info(f"Handshake complete: session={self._session_id}")

        # Update metrics
        self._metrics.events_sent += 1
        self._metrics.last_event_at = datetime.now().isoformat()

        return handshake_event

    async def _start_keepalive(self) -> None:
        """Start the keepalive scheduler task."""
        if self._keepalive_task is not None:
            return

        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        logger.debug(f"Keepalive scheduler started: interval={self._config.keepalive_interval_seconds}s")

    async def _keepalive_loop(self) -> None:
        """Keepalive scheduler loop."""
        while self._state in {ConnectionState.CONNECTED, ConnectionState.PAUSED}:
            try:
                await asyncio.sleep(self._config.keepalive_interval_seconds)

                if self._state == ConnectionState.CONNECTED:
                    keepalive = await self._create_keepalive()
                    await self._event_queue.put(keepalive)
                    self._metrics.keepalives_sent += 1

            except asyncio.CancelledError:
                logger.debug("Keepalive loop cancelled")
                break
            except Exception as e:
                logger.error(f"Keepalive error: {e}")

    async def _create_keepalive(self) -> EventEnvelope:
        """
        Create a keepalive event.

        Returns:
            KEEPALIVE event envelope
        """
        event_id = f"ka_{uuid.uuid4().hex[:8]}"
        sequence = self._sequence_generator.next()

        return EventEnvelope.create_keepalive(
            event_id=event_id,
            sequence=sequence,
            session_id=self._session_id
        )

    async def send_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventEnvelope:
        """
        Send an event to the client.

        Args:
            event_type: Type of event
            payload: Event payload
            metadata: Optional metadata

        Returns:
            Created event envelope
        """
        if self._state not in {ConnectionState.CONNECTED, ConnectionState.REPLAYING}:
            raise SSEInternalError(
                message=f"Cannot send event in state {self._state.name}",
                component="handler",
                operation="send_event"
            )

        # Check backpressure
        await self._check_backpressure()

        # Create event envelope
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        sequence = self._sequence_generator.next()

        envelope = EventEnvelope(
            event_id=event_id,
            sequence=sequence,
            event_type=event_type,
            payload=payload,
            metadata=metadata or {},
            session_id=self._session_id
        )

        # Add to queue
        await self._event_queue.put(envelope)

        # Store in buffer for replay
        if self._event_buffer:
            self._event_buffer.append(envelope)

        # Update metrics
        self._metrics.events_sent += 1
        self._metrics.last_event_at = datetime.now().isoformat()

        logger.debug(f"Event queued: type={event_type.value}, seq={sequence}")

        return envelope

    async def _check_backpressure(self) -> None:
        """
        Check and handle backpressure conditions.

        Raises:
            BackpressureError: If backpressure threshold exceeded
        """
        queue_size = self._event_queue.qsize()

        if queue_size >= self._config.backpressure_threshold:
            self._metrics.backpressure_events += 1
            await self._set_state(ConnectionState.BACKPRESSURE)

            logger.warning(
                f"Backpressure triggered: queue_size={queue_size}, "
                f"threshold={self._config.backpressure_threshold}"
            )

            # Stub: In full implementation, would:
            # - Signal client to slow down
            # - Drop low-priority events
            # - Apply flow control

            if queue_size >= self._config.max_queue_size:
                raise BackpressureError(
                    message="Event queue full",
                    buffer_size=queue_size,
                    threshold=self._config.max_queue_size
                )

    async def replay_events(
        self,
        from_sequence: int,
        max_events: Optional[int] = None
    ) -> AsyncGenerator[EventEnvelope, None]:
        """
        Replay events from a sequence number.

        Args:
            from_sequence: Starting sequence for replay
            max_events: Maximum events to replay

        Yields:
            Event envelopes for replay
        """
        if not self._replay_controller:
            raise SSEInternalError(
                message="Replay not available",
                component="handler",
                operation="replay"
            )

        await self._set_state(ConnectionState.REPLAYING)

        try:
            request = ReplayRequest(
                session_id=self._session_id,
                from_sequence=from_sequence,
                max_events=max_events
            )

            # Yield REPLAY_START
            start_event = self._replay_controller.create_replay_start_event(
                event_id=f"rs_{uuid.uuid4().hex[:8]}",
                sequence=self._sequence_generator.next(),
                from_sequence=from_sequence,
                event_count=0,  # Unknown until complete
                session_id=self._session_id
            )
            yield start_event

            # Yield replay events
            event_count = 0
            async for event in self._replay_controller.replay_events_async(request):
                yield event
                event_count += 1

            # Yield REPLAY_END
            end_event = self._replay_controller.create_replay_end_event(
                event_id=f"re_{uuid.uuid4().hex[:8]}",
                sequence=self._sequence_generator.next(),
                events_replayed=event_count,
                session_id=self._session_id
            )
            yield end_event

            self._metrics.replays_performed += 1
            logger.info(f"Replay complete: {event_count} events")

        finally:
            await self._set_state(ConnectionState.CONNECTED)

    async def stream_events(self) -> AsyncGenerator[str, None]:
        """
        Stream events as SSE frames.

        Yields:
            Formatted SSE frame strings
        """
        try:
            while self._state not in {ConnectionState.CLOSING, ConnectionState.CLOSED, ConnectionState.ERROR}:
                try:
                    # Wait for event with timeout for keepalive
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=self._config.keepalive_interval_seconds
                    )

                    # Format as SSE frame
                    frame = event.to_sse_frame()
                    self._metrics.bytes_sent += len(frame.encode("utf-8"))

                    yield frame

                except asyncio.TimeoutError:
                    # Generate keepalive on timeout
                    if self._state == ConnectionState.CONNECTED:
                        keepalive = await self._create_keepalive()
                        frame = keepalive.to_sse_frame()
                        self._metrics.keepalives_sent += 1
                        yield frame

        except Exception as e:
            logger.error(f"Stream error: {e}")
            await self._set_state(ConnectionState.ERROR)
            raise

    async def close(self, reason: Optional[str] = None) -> EventEnvelope:
        """
        Close the SSE connection.

        Args:
            reason: Optional close reason

        Returns:
            CONNECTION_CLOSE event envelope
        """
        await self._set_state(ConnectionState.CLOSING)

        # Stop keepalive
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass

        # Create close event
        event_id = f"close_{uuid.uuid4().hex[:8]}"
        sequence = self._sequence_generator.next()

        close_event = EventEnvelope(
            event_id=event_id,
            sequence=sequence,
            event_type=EventType.CONNECTION_CLOSE,
            payload={"reason": reason or "normal_closure"},
            session_id=self._session_id
        )

        await self._set_state(ConnectionState.CLOSED)

        logger.info(f"Connection closed: session={self._session_id}, reason={reason}")

        return close_event

    def set_on_state_change(
        self,
        callback: Callable[[ConnectionState], None]
    ) -> None:
        """
        Set state change callback.

        Args:
            callback: Function to call on state change
        """
        self._on_state_change = callback

    def set_on_error(
        self,
        callback: Callable[[Exception], None]
    ) -> None:
        """
        Set error callback.

        Args:
            callback: Function to call on error
        """
        self._on_error = callback


class SSEHandlerFactory:
    """
    Factory for creating SSE handlers.

    Provides shared resources and consistent configuration.
    """

    def __init__(
        self,
        config: Optional[HandlerConfig] = None,
        sequence_generator: Optional[ISequenceGenerator] = None,
        event_buffer: Optional[EventBuffer] = None,
        middleware_chain: Optional[MiddlewareChain] = None
    ) -> None:
        """
        Initialize handler factory.

        Args:
            config: Default handler configuration
            sequence_generator: Shared sequence generator
            event_buffer: Shared event buffer
            middleware_chain: Shared middleware chain
        """
        self._config = config or HandlerConfig()
        self._sequence_generator = sequence_generator or InMemorySequenceGenerator()
        self._event_buffer = event_buffer or EventBuffer()
        self._replay_controller = ReplayController(self._event_buffer)
        self._middleware_chain = middleware_chain

        self._active_handlers: Dict[str, SSEHandler] = {}

        logger.info("SSEHandlerFactory initialized")

    def create_handler(
        self,
        session_id: Optional[str] = None
    ) -> SSEHandler:
        """
        Create a new SSE handler.

        Args:
            session_id: Optional session ID (generated if not provided)

        Returns:
            Configured SSEHandler instance
        """
        if session_id is None:
            session_id = f"sse_{uuid.uuid4().hex}"

        handler = SSEHandler(
            session_id=session_id,
            config=self._config,
            sequence_generator=self._sequence_generator,
            event_buffer=self._event_buffer,
            replay_controller=self._replay_controller,
            middleware_chain=self._middleware_chain
        )

        self._active_handlers[session_id] = handler

        logger.debug(f"Handler created: session={session_id}")

        return handler

    def get_handler(self, session_id: str) -> Optional[SSEHandler]:
        """
        Get an existing handler by session ID.

        Args:
            session_id: Session identifier

        Returns:
            SSEHandler if found, None otherwise
        """
        return self._active_handlers.get(session_id)

    def remove_handler(self, session_id: str) -> bool:
        """
        Remove a handler from tracking.

        Args:
            session_id: Session identifier

        Returns:
            True if removed, False if not found
        """
        if session_id in self._active_handlers:
            del self._active_handlers[session_id]
            logger.debug(f"Handler removed: session={session_id}")
            return True
        return False

    def get_active_count(self) -> int:
        """Get count of active handlers."""
        return len(self._active_handlers)
