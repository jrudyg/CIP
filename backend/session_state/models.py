"""
Session State Models — P7.S2
SSE connection tracking for session management.

Phase: P7.S2
Task: S2.T1
Author: CAI (Backend Architect)

Provides:
- SSEConnectionStatus enum
- SSEConnectionInfo dataclass
- SessionSSEState with max 5 connections enforcement
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SSEConnectionStatus(str, Enum):
    """SSE connection status for session tracking."""
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    TERMINATED = "terminated"


@dataclass
class SSEConnectionInfo:
    """
    SSE connection metadata for a session.
    Tracks connection state, timing, and metrics.
    """
    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SSEConnectionStatus = SSEConnectionStatus.INACTIVE
    connected_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    last_keepalive_at: Optional[datetime] = None
    last_sequence: int = 0
    events_sent: int = 0
    reconnect_count: int = 0
    client_version: Optional[str] = None
    client_ip: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "connection_id": self.connection_id,
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
            "last_keepalive_at": self.last_keepalive_at.isoformat() if self.last_keepalive_at else None,
            "last_sequence": self.last_sequence,
            "events_sent": self.events_sent,
            "reconnect_count": self.reconnect_count,
            "client_version": self.client_version,
            "client_ip": self.client_ip,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SSEConnectionInfo":
        """Create from dictionary."""
        return cls(
            connection_id=data.get("connection_id", str(uuid.uuid4())),
            status=SSEConnectionStatus(data.get("status", "inactive")),
            connected_at=datetime.fromisoformat(data["connected_at"]) if data.get("connected_at") else None,
            last_event_at=datetime.fromisoformat(data["last_event_at"]) if data.get("last_event_at") else None,
            last_keepalive_at=datetime.fromisoformat(data["last_keepalive_at"]) if data.get("last_keepalive_at") else None,
            last_sequence=data.get("last_sequence", 0),
            events_sent=data.get("events_sent", 0),
            reconnect_count=data.get("reconnect_count", 0),
            client_version=data.get("client_version"),
            client_ip=data.get("client_ip"),
        )

    def mark_connected(self) -> None:
        """Mark connection as active."""
        self.status = SSEConnectionStatus.ACTIVE
        self.connected_at = datetime.now()
        self.last_keepalive_at = datetime.now()

    def mark_event_sent(self, sequence: int) -> None:
        """Record event sent."""
        self.last_event_at = datetime.now()
        self.last_sequence = sequence
        self.events_sent += 1

    def mark_keepalive(self) -> None:
        """Record keepalive sent."""
        self.last_keepalive_at = datetime.now()

    def mark_reconnecting(self) -> None:
        """Mark connection as reconnecting."""
        self.status = SSEConnectionStatus.RECONNECTING
        self.reconnect_count += 1

    def mark_terminated(self) -> None:
        """Mark connection as terminated."""
        self.status = SSEConnectionStatus.TERMINATED


@dataclass
class SessionSSEState:
    """
    Extended session state with SSE tracking.
    Supports multiple concurrent connections per session (multi-tab).
    Enforces max 5 connections per session.
    """
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # SSE connection tracking (max 5 per session)
    sse_connections: List[SSEConnectionInfo] = field(default_factory=list)
    max_connections: int = 5

    # Session-level SSE state
    total_events_sent: int = 0
    total_reconnects: int = 0

    def add_connection(self, connection: SSEConnectionInfo) -> bool:
        """
        Add SSE connection to session.
        
        Args:
            connection: Connection info to add
            
        Returns:
            True if added, False if max connections exceeded
        """
        # Remove terminated connections first
        self._cleanup_terminated()

        if len(self.sse_connections) >= self.max_connections:
            return False

        self.sse_connections.append(connection)
        self.updated_at = datetime.now()
        return True

    def remove_connection(self, connection_id: str) -> bool:
        """
        Remove SSE connection by ID.
        
        Args:
            connection_id: ID of connection to remove
            
        Returns:
            True if removed, False if not found
        """
        initial_count = len(self.sse_connections)
        self.sse_connections = [
            c for c in self.sse_connections
            if c.connection_id != connection_id
        ]
        self.updated_at = datetime.now()
        return len(self.sse_connections) < initial_count

    def get_connection(self, connection_id: str) -> Optional[SSEConnectionInfo]:
        """Get connection by ID."""
        for conn in self.sse_connections:
            if conn.connection_id == connection_id:
                return conn
        return None

    def get_active_connections(self) -> List[SSEConnectionInfo]:
        """Get all active connections."""
        return [
            c for c in self.sse_connections
            if c.status == SSEConnectionStatus.ACTIVE
        ]

    def get_active_count(self) -> int:
        """Get count of active connections."""
        return len(self.get_active_connections())

    def _cleanup_terminated(self) -> None:
        """Remove terminated connections."""
        self.sse_connections = [
            c for c in self.sse_connections
            if c.status != SSEConnectionStatus.TERMINATED
        ]

    def record_event_sent(self) -> None:
        """Record event sent at session level."""
        self.total_events_sent += 1
        self.updated_at = datetime.now()

    def record_reconnect(self) -> None:
        """Record reconnection at session level."""
        self.total_reconnects += 1
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sse_connections": [c.to_dict() for c in self.sse_connections],
            "max_connections": self.max_connections,
            "total_events_sent": self.total_events_sent,
            "total_reconnects": self.total_reconnects,
            "active_connection_count": self.get_active_count(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSSEState":
        """Create from dictionary."""
        connections = [
            SSEConnectionInfo.from_dict(c)
            for c in data.get("sse_connections", [])
        ]
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            sse_connections=connections,
            max_connections=data.get("max_connections", 5),
            total_events_sent=data.get("total_events_sent", 0),
            total_reconnects=data.get("total_reconnects", 0),
        )
