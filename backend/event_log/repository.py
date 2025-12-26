"""
Event Log Repository — P7.S2
Database operations for event persistence and replay.

Phase: P7.S2
Task: S2.T2
Author: CAI (Backend Architect)

Provides:
- SQLite schema for event_log
- Append/retrieve operations
- TTL-based pruning
- Max events per session enforcement
- Sequence-based retrieval for replay
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .models import EventLogEntry

logger = logging.getLogger("event_log.repository")


class EventLogRepository:
    """
    Repository for event log persistence.
    Uses SQLite for storage with thread-safe operations.
    """

    # Defaults
    DEFAULT_TTL_HOURS = 1.0
    DEFAULT_MAX_EVENTS_PER_SESSION = 1000

    def __init__(
        self,
        db_path: str = "data/cip_events.db",
        ttl_hours: float = DEFAULT_TTL_HOURS,
        max_events_per_session: int = DEFAULT_MAX_EVENTS_PER_SESSION,
    ):
        """
        Initialize repository.
        
        Args:
            db_path: Path to SQLite database file
            ttl_hours: Default time-to-live for events
            max_events_per_session: Maximum events to retain per session
        """
        self._db_path = db_path
        self._ttl_hours = ttl_hours
        self._max_events = max_events_per_session
        self._lock = threading.Lock()
        self._ensure_directory()
        self._ensure_schema()

    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Create tables if not exist."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                -- Event log table
                CREATE TABLE IF NOT EXISTS event_log (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                );

                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_event_log_session_seq
                    ON event_log(session_id, sequence);
                CREATE INDEX IF NOT EXISTS idx_event_log_expires
                    ON event_log(expires_at);
                CREATE INDEX IF NOT EXISTS idx_event_log_event_type
                    ON event_log(event_type);
                CREATE INDEX IF NOT EXISTS idx_event_log_created
                    ON event_log(session_id, created_at);
            """)
            conn.commit()
            logger.info(f"Event log schema initialized: {self._db_path}")
        finally:
            conn.close()

    def append(
        self,
        entry: EventLogEntry,
        enforce_max: bool = True,
    ) -> bool:
        """
        Append event to log.
        
        Args:
            entry: EventLogEntry to append
            enforce_max: If True, prune oldest if max exceeded
            
        Returns:
            True if appended successfully
        """
        with self._lock:
            conn = self._get_connection()
            try:
                # Insert event
                conn.execute("""
                    INSERT INTO event_log (
                        event_id, session_id, sequence, event_type,
                        timestamp, payload, metadata, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.event_id,
                    entry.session_id,
                    entry.sequence,
                    entry.event_type,
                    entry.timestamp,
                    json.dumps(entry.payload) if entry.payload else None,
                    json.dumps(entry.metadata) if entry.metadata else None,
                    entry.created_at.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                ))
                conn.commit()

                # Enforce max events
                if enforce_max:
                    self._prune_excess_events(conn, entry.session_id)

                logger.debug(f"Event appended: seq={entry.sequence}, session={entry.session_id}")
                return True

            except sqlite3.IntegrityError as e:
                logger.warning(f"Duplicate event_id: {entry.event_id}")
                return False
            finally:
                conn.close()

    def append_batch(self, entries: List[EventLogEntry]) -> int:
        """
        Append multiple events atomically.
        
        Args:
            entries: List of EventLogEntry to append
            
        Returns:
            Count of events appended
        """
        if not entries:
            return 0

        with self._lock:
            conn = self._get_connection()
            try:
                count = 0
                for entry in entries:
                    try:
                        conn.execute("""
                            INSERT INTO event_log (
                                event_id, session_id, sequence, event_type,
                                timestamp, payload, metadata, created_at, expires_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entry.event_id,
                            entry.session_id,
                            entry.sequence,
                            entry.event_type,
                            entry.timestamp,
                            json.dumps(entry.payload) if entry.payload else None,
                            json.dumps(entry.metadata) if entry.metadata else None,
                            entry.created_at.isoformat(),
                            entry.expires_at.isoformat() if entry.expires_at else None,
                        ))
                        count += 1
                    except sqlite3.IntegrityError:
                        continue  # Skip duplicates

                conn.commit()

                # Prune excess for affected sessions
                session_ids = set(e.session_id for e in entries)
                for session_id in session_ids:
                    self._prune_excess_events(conn, session_id)

                return count
            finally:
                conn.close()

    def get_events_from_sequence(
        self,
        session_id: str,
        from_seq: int,
        max_events: int = 100,
    ) -> List[EventLogEntry]:
        """
        Get events starting from sequence number.
        Used for replay after reconnection.
        
        Args:
            session_id: Session identifier
            from_seq: Starting sequence (inclusive)
            max_events: Maximum events to return
            
        Returns:
            List of EventLogEntry in sequence order
        """
        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute("""
                    SELECT * FROM event_log
                    WHERE session_id = ? AND sequence >= ?
                    ORDER BY sequence ASC
                    LIMIT ?
                """, (session_id, from_seq, max_events)).fetchall()

                return [self._row_to_entry(r) for r in rows]
            finally:
                conn.close()

    def get_events_in_range(
        self,
        session_id: str,
        from_seq: int,
        to_seq: int,
    ) -> List[EventLogEntry]:
        """
        Get events in sequence range.
        
        Args:
            session_id: Session identifier
            from_seq: Starting sequence (inclusive)
            to_seq: Ending sequence (inclusive)
            
        Returns:
            List of EventLogEntry in sequence order
        """
        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute("""
                    SELECT * FROM event_log
                    WHERE session_id = ? AND sequence >= ? AND sequence <= ?
                    ORDER BY sequence ASC
                """, (session_id, from_seq, to_seq)).fetchall()

                return [self._row_to_entry(r) for r in rows]
            finally:
                conn.close()

    def get_latest_sequence(self, session_id: str) -> Optional[int]:
        """
        Get the latest sequence number for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Latest sequence number or None if no events
        """
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute("""
                    SELECT MAX(sequence) as max_seq FROM event_log
                    WHERE session_id = ?
                """, (session_id,)).fetchone()

                return row["max_seq"] if row and row["max_seq"] is not None else None
            finally:
                conn.close()

    def get_event_count(self, session_id: str) -> int:
        """
        Get event count for session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Event count
        """
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute("""
                    SELECT COUNT(*) as count FROM event_log
                    WHERE session_id = ?
                """, (session_id,)).fetchone()

                return row["count"] if row else 0
            finally:
                conn.close()

    def detect_gaps(
        self,
        session_id: str,
        from_seq: int,
        to_seq: int,
    ) -> List[Tuple[int, int]]:
        """
        Detect sequence gaps in range.
        
        Args:
            session_id: Session identifier
            from_seq: Starting sequence
            to_seq: Ending sequence
            
        Returns:
            List of (gap_start, gap_end) tuples
        """
        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute("""
                    SELECT sequence FROM event_log
                    WHERE session_id = ? AND sequence >= ? AND sequence <= ?
                    ORDER BY sequence ASC
                """, (session_id, from_seq, to_seq)).fetchall()

                sequences = set(r["sequence"] for r in rows)
                gaps = []
                
                gap_start = None
                for seq in range(from_seq, to_seq + 1):
                    if seq not in sequences:
                        if gap_start is None:
                            gap_start = seq
                    else:
                        if gap_start is not None:
                            gaps.append((gap_start, seq - 1))
                            gap_start = None

                if gap_start is not None:
                    gaps.append((gap_start, to_seq))

                return gaps
            finally:
                conn.close()

    def prune_expired(self) -> int:
        """
        Remove expired events.
        
        Returns:
            Count of events pruned
        """
        with self._lock:
            conn = self._get_connection()
            try:
                now = datetime.now(timezone.utc).isoformat()
                cursor = conn.execute("""
                    DELETE FROM event_log
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (now,))
                conn.commit()
                count = cursor.rowcount
                if count > 0:
                    logger.info(f"Pruned {count} expired events")
                return count
            finally:
                conn.close()

    def _prune_excess_events(self, conn: sqlite3.Connection, session_id: str) -> int:
        """
        Prune oldest events if session exceeds max.
        FIFO eviction policy.
        
        Args:
            conn: Active connection
            session_id: Session identifier
            
        Returns:
            Count of events pruned
        """
        # Count current events
        row = conn.execute("""
            SELECT COUNT(*) as count FROM event_log WHERE session_id = ?
        """, (session_id,)).fetchone()

        count = row["count"] if row else 0
        excess = count - self._max_events

        if excess <= 0:
            return 0

        # Delete oldest events
        cursor = conn.execute("""
            DELETE FROM event_log
            WHERE event_id IN (
                SELECT event_id FROM event_log
                WHERE session_id = ?
                ORDER BY sequence ASC
                LIMIT ?
            )
        """, (session_id, excess))
        conn.commit()

        pruned = cursor.rowcount
        if pruned > 0:
            logger.debug(f"Pruned {pruned} excess events for session {session_id}")
        return pruned

    def delete_session_events(self, session_id: str) -> int:
        """
        Delete all events for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Count of events deleted
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("""
                    DELETE FROM event_log WHERE session_id = ?
                """, (session_id,))
                conn.commit()
                return cursor.rowcount
            finally:
                conn.close()

    def _row_to_entry(self, row: sqlite3.Row) -> EventLogEntry:
        """Convert database row to EventLogEntry."""
        return EventLogEntry(
            event_id=row["event_id"],
            session_id=row["session_id"],
            sequence=row["sequence"],
            event_type=row["event_type"],
            timestamp=row["timestamp"],
            payload=json.loads(row["payload"]) if row["payload"] else {},
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        )

    def get_stats(self) -> dict:
        """
        Get repository statistics.
        
        Returns:
            Dict with event counts and metadata
        """
        with self._lock:
            conn = self._get_connection()
            try:
                total = conn.execute(
                    "SELECT COUNT(*) as count FROM event_log"
                ).fetchone()["count"]

                sessions = conn.execute(
                    "SELECT COUNT(DISTINCT session_id) as count FROM event_log"
                ).fetchone()["count"]

                return {
                    "total_events": total,
                    "sessions_with_events": sessions,
                    "max_events_per_session": self._max_events,
                    "ttl_hours": self._ttl_hours,
                    "db_path": self._db_path,
                }
            finally:
                conn.close()


# Module-level singleton
_default_repository: Optional[EventLogRepository] = None


def get_event_log_repository(
    db_path: str = "data/cip_events.db",
    ttl_hours: float = 1.0,
    max_events: int = 1000,
) -> EventLogRepository:
    """
    Get or create the default event log repository.
    
    Args:
        db_path: Database path (only used on first call)
        ttl_hours: Event TTL
        max_events: Max events per session
        
    Returns:
        EventLogRepository singleton
    """
    global _default_repository
    if _default_repository is None:
        _default_repository = EventLogRepository(db_path, ttl_hours, max_events)
    return _default_repository
