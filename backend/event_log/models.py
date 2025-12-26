"""
Event Log Models — P7.S2
Event persistence for replay and audit.

Phase: P7.S2
Task: S2.T2
Author: CAI (Backend Architect)

Provides:
- EventLogEntry dataclass
- Factory methods for envelope conversion
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


@dataclass
class EventLogEntry:
    """
    Persistent event log entry.
    Stores SSE events for replay and audit purposes.
    """
    event_id: str
    session_id: str
    sequence: int
    event_type: str
    timestamp: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    
    # TTL management
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default expiration if not provided."""
        if self.expires_at is None:
            # Default 1 hour TTL
            self.expires_at = self.created_at + timedelta(hours=1)

    @classmethod
    def from_envelope(
        cls,
        envelope: Any,
        session_id: str,
        ttl_hours: float = 1.0
    ) -> "EventLogEntry":
        """
        Create from SSE EventEnvelope.
        
        Args:
            envelope: EventEnvelope instance (from sse/envelope.py)
            session_id: Session identifier
            ttl_hours: Time-to-live in hours
            
        Returns:
            EventLogEntry
        """
        now = datetime.now(timezone.utc)
        return cls(
            event_id=envelope.event_id,
            session_id=session_id,
            sequence=envelope.sequence,
            event_type=envelope.event_type.value if hasattr(envelope.event_type, 'value') else str(envelope.event_type),
            timestamp=envelope.timestamp,
            payload=envelope.payload or {},
            metadata=envelope.metadata,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )

    @classmethod
    def create(
        cls,
        session_id: str,
        sequence: int,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        ttl_hours: float = 1.0,
    ) -> "EventLogEntry":
        """
        Factory method for direct creation.
        
        Args:
            session_id: Session identifier
            sequence: Event sequence number
            event_type: Type of event
            payload: Event payload
            ttl_hours: Time-to-live in hours
            
        Returns:
            EventLogEntry
        """
        now = datetime.now(timezone.utc)
        return cls(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            sequence=sequence,
            event_type=event_type,
            timestamp=now.isoformat(),
            payload=payload or {},
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def to_sse_data(self) -> Dict[str, Any]:
        """
        Convert to SSE event data format for replay.
        Matches EventEnvelope.to_dict() structure.
        """
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventLogEntry":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            session_id=data["session_id"],
            sequence=data["sequence"],
            event_type=data["event_type"],
            timestamp=data["timestamp"],
            payload=data.get("payload", {}),
            metadata=data.get("metadata"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
        )

    def __repr__(self) -> str:
        return f"EventLogEntry(seq={self.sequence}, type={self.event_type}, session={self.session_id[:8]}...)"
