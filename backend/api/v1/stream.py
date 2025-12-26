"""
SSE Stream API — P7.S2
FastAPI/Flask blueprint for SSE streaming endpoints.

Phase: P7.S2
Task: S2.T3
Author: CAI (Backend Architect)

Endpoints:
- GET /api/v1/stream/{session_id} — SSE event stream
- GET /api/v1/stream/{session_id}/replay — Historical event retrieval
- GET /api/v1/stream/{session_id}/status — Connection status
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Generator, Optional

from flask import Blueprint, Response, request, jsonify, g

# Local imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from session_state import (
    SessionStateRepository,
    SSEConnectionInfo,
    SSEConnectionStatus,
    get_session_repository,
)
from event_log import (
    EventLogRepository,
    EventLogEntry,
    get_event_log_repository,
)
from shared.p7_streaming_contract import (
    P7_TIMING,
    P7EventType,
    P7_CONTRACT_VERSION,
)

logger = logging.getLogger("api.stream")

# Blueprint
stream_bp = Blueprint("stream", __name__, url_prefix="/api/v1/stream")

# Configuration
SSE_KEEPALIVE_INTERVAL = P7_TIMING.KEEPALIVE_INTERVAL_MS / 1000  # 30 seconds
MAX_CONNECTIONS_PER_SESSION = 5
MIN_CLIENT_VERSION = "1.0.0"


class SSEStreamHandler:
    """
    Handler for a single SSE connection.
    Manages lifecycle, keepalives, and event streaming.
    """

    def __init__(
        self,
        session_id: str,
        connection_id: str,
        session_repo: SessionStateRepository,
        event_repo: EventLogRepository,
        last_event_id: Optional[int] = None,
    ):
        self.session_id = session_id
        self.connection_id = connection_id
        self.session_repo = session_repo
        self.event_repo = event_repo
        self.last_event_id = last_event_id
        self.sequence = 0
        self.connected = False
        self.closed = False

    def _format_sse_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> str:
        """Format data as SSE event."""
        self.sequence += 1
        
        envelope = {
            "event_id": event_id or str(uuid.uuid4()),
            "sequence": self.sequence,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": data,
            "session_id": self.session_id,
        }
        
        lines = []
        if event_id:
            lines.append(f"id: {self.sequence}")
        lines.append(f"event: {event_type}")
        lines.append(f"data: {json.dumps(envelope)}")
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)

    def _handshake_event(self) -> str:
        """Generate handshake complete event."""
        return self._format_sse_event(
            P7EventType.HANDSHAKE_COMPLETE.value,
            {
                "session_id": self.session_id,
                "connection_id": self.connection_id,
                "server_time": datetime.now(timezone.utc).isoformat(),
                "contract_version": P7_CONTRACT_VERSION,
                "keepalive_interval_ms": P7_TIMING.KEEPALIVE_INTERVAL_MS,
            }
        )

    def _keepalive_event(self) -> str:
        """Generate keepalive event."""
        return self._format_sse_event(
            P7EventType.KEEPALIVE.value,
            {
                "server_time": datetime.now(timezone.utc).isoformat(),
                "sequence": self.sequence,
            }
        )

    def _replay_start_event(self, from_seq: int, to_seq: int, count: int) -> str:
        """Generate replay start event."""
        return self._format_sse_event(
            P7EventType.REPLAY_START.value,
            {
                "from_sequence": from_seq,
                "to_sequence": to_seq,
                "event_count": count,
            }
        )

    def _replay_end_event(self, count: int) -> str:
        """Generate replay end event."""
        return self._format_sse_event(
            P7EventType.REPLAY_END.value,
            {
                "events_replayed": count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _close_event(self, reason: str = "normal") -> str:
        """Generate connection close event."""
        return self._format_sse_event(
            P7EventType.CONNECTION_CLOSE.value,
            {
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def generate_stream(self) -> Generator:
        """
        Generate SSE event stream.
        Yields SSE-formatted events.
        """
        try:
            # Send handshake
            yield self._handshake_event()
            self.connected = True
            logger.info(f"SSE connected: session={self.session_id}, conn={self.connection_id}")

            # Handle replay if last_event_id provided
            if self.last_event_id is not None:
                replay_events = self.event_repo.get_events_from_sequence(
                    self.session_id,
                    from_seq=self.last_event_id + 1,
                    max_events=100,
                )
                if replay_events:
                    yield self._replay_start_event(
                        from_seq=self.last_event_id + 1,
                        to_seq=replay_events[-1].sequence,
                        count=len(replay_events),
                    )
                    for event in replay_events:
                        yield self._format_sse_event(
                            P7EventType.REPLAY_EVENT.value,
                            event.to_sse_data(),
                        )
                    yield self._replay_end_event(len(replay_events))

            # Keepalive loop
            import time
            last_keepalive = time.time()
            
            while not self.closed:
                # Check if keepalive needed
                now = time.time()
                if now - last_keepalive >= SSE_KEEPALIVE_INTERVAL:
                    yield self._keepalive_event()
                    last_keepalive = now
                    
                    # Update connection status
                    session = self.session_repo.get_session(self.session_id)
                    if session:
                        conn = session.get_connection(self.connection_id)
                        if conn:
                            conn.mark_keepalive()
                            self.session_repo.save_session(session)

                # Small sleep to prevent busy loop
                time.sleep(0.1)
                yield ""  # Keep connection alive

        except GeneratorExit:
            logger.info(f"SSE disconnected: session={self.session_id}")
        finally:
            self.closed = True
            self._cleanup()

    def _cleanup(self):
        """Cleanup on disconnect."""
        try:
            self.session_repo.update_connection_status(
                self.connection_id,
                SSEConnectionStatus.TERMINATED
            )
        except Exception as e:
            logger.error(f"Cleanup error: {e}")



def _check_version(client_version: Optional[str]) -> bool:
    """Check if client version is compatible."""
    if not client_version:
        return True  # Allow if not provided
    
    try:
        client_parts = [int(x) for x in client_version.split(".")[:3]]
        min_parts = [int(x) for x in MIN_CLIENT_VERSION.split(".")[:3]]
        return client_parts >= min_parts
    except (ValueError, AttributeError):
        return True  # Allow on parse error


def _get_last_event_id() -> Optional[int]:
    """Extract Last-Event-ID from request headers."""
    last_event_id = request.headers.get("Last-Event-ID")
    if last_event_id:
        try:
            return int(last_event_id)
        except ValueError:
            pass
    return None


@stream_bp.route("/<session_id>", methods=["GET"])
def stream_events(session_id: str):
    """
    SSE stream endpoint.
    
    Headers:
        Accept: text/event-stream
        Authorization: Bearer <token> (optional)
        X-Client-Version: <version> (optional)
        Last-Event-ID: <sequence> (for replay)
    
    Returns:
        SSE event stream
    """
    # Validate Accept header
    accept = request.headers.get("Accept", "")
    if "text/event-stream" not in accept and "*/*" not in accept:
        return jsonify({"error": "Accept header must include text/event-stream"}), 406

    # Check client version
    client_version = request.headers.get("X-Client-Version")
    if not _check_version(client_version):
        return jsonify({
            "error": "Client version too old",
            "min_version": MIN_CLIENT_VERSION,
        }), 426  # Upgrade Required

    # Get repositories
    session_repo = get_session_repository()
    event_repo = get_event_log_repository()

    # Get or create session
    session = session_repo.get_or_create_session(session_id)

    # Check connection limit
    active_count = session.get_active_count()
    if active_count >= MAX_CONNECTIONS_PER_SESSION:
        return jsonify({
            "error": "Max connections exceeded",
            "max": MAX_CONNECTIONS_PER_SESSION,
            "current": active_count,
        }), 429  # Too Many Requests

    # Create connection
    connection = SSEConnectionInfo(
        client_version=client_version,
        client_ip=request.remote_addr,
    )
    connection.mark_connected()

    if not session.add_connection(connection):
        return jsonify({"error": "Failed to add connection"}), 500

    session_repo.save_session(session)

    # Get last event ID for replay
    last_event_id = _get_last_event_id()

    # Create handler
    handler = SSEStreamHandler(
        session_id=session_id,
        connection_id=connection.connection_id,
        session_repo=session_repo,
        event_repo=event_repo,
        last_event_id=last_event_id,
    )

    # Return SSE response
    return Response(
        handler.generate_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Connection-ID": connection.connection_id,
        },
    )


@stream_bp.route("/<session_id>/replay", methods=["GET"])
def replay_events(session_id: str):
    """
    Replay endpoint for historical events.
    
    Query params:
        from_seq: Starting sequence (required)
        to_seq: Ending sequence (optional)
        max_events: Limit (default 100)
    
    Returns:
        JSON array of events
    """
    from_seq = request.args.get("from_seq", type=int)
    if from_seq is None:
        return jsonify({"error": "from_seq parameter required"}), 400

    to_seq = request.args.get("to_seq", type=int)
    max_events = request.args.get("max_events", default=100, type=int)

    event_repo = get_event_log_repository()

    if to_seq is not None:
        events = event_repo.get_events_in_range(session_id, from_seq, to_seq)
    else:
        events = event_repo.get_events_from_sequence(session_id, from_seq, max_events)

    return jsonify({
        "session_id": session_id,
        "from_sequence": from_seq,
        "to_sequence": to_seq,
        "count": len(events),
        "events": [e.to_sse_data() for e in events],
    })


@stream_bp.route("/<session_id>/status", methods=["GET"])
def connection_status(session_id: str):
    """
    Get session connection status.
    
    Returns:
        JSON with session state and connections
    """
    session_repo = get_session_repository()
    session = session_repo.get_session(session_id)

    if not session:
        return jsonify({
            "session_id": session_id,
            "exists": False,
        })

    return jsonify({
        "session_id": session_id,
        "exists": True,
        "active_connections": session.get_active_count(),
        "max_connections": session.max_connections,
        "total_events_sent": session.total_events_sent,
        "total_reconnects": session.total_reconnects,
        "connections": [c.to_dict() for c in session.sse_connections],
    })


@stream_bp.route("/<session_id>/publish", methods=["POST"])
def publish_event(session_id: str):
    """
    Publish event to session (for testing/diagnostics).
    
    Body:
        event_type: Type of event
        payload: Event data
    
    Returns:
        Published event details
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    event_type = data.get("event_type", "test_event")
    payload = data.get("payload", {})

    event_repo = get_event_log_repository()
    
    # Get next sequence
    latest = event_repo.get_latest_sequence(session_id) or 0
    
    entry = EventLogEntry.create(
        session_id=session_id,
        sequence=latest + 1,
        event_type=event_type,
        payload=payload,
    )
    
    event_repo.append(entry)

    return jsonify({
        "status": "published",
        "event_id": entry.event_id,
        "sequence": entry.sequence,
        "event_type": entry.event_type,
    })


@stream_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    session_repo = get_session_repository()
    event_repo = get_event_log_repository()

    return jsonify({
        "status": "healthy",
        "contract_version": P7_CONTRACT_VERSION,
        "session_stats": session_repo.get_stats(),
        "event_stats": event_repo.get_stats(),
    })
