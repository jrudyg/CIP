"""
Session State Repository — P7.S2
Database operations for session and SSE connection state.

Phase: P7.S2
Task: S2.T1
Author: CAI (Backend Architect)

Provides:
- SQLite schema for sessions + sse_connections
- CRUD operations for session state
- Connection status management
- Stale connection cleanup
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import (
    SessionSSEState,
    SSEConnectionInfo,
    SSEConnectionStatus,
)

logger = logging.getLogger("session_state.repository")


class SessionStateRepository:
    """
    Repository for session state persistence.
    Uses SQLite for storage with thread-safe operations.
    """

    def __init__(self, db_path: str = "data/cip_sessions.db"):
        """
        Initialize repository.
        
        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
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
                -- Sessions table with SSE extensions
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    max_connections INTEGER DEFAULT 5,
                    total_events_sent INTEGER DEFAULT 0,
                    total_reconnects INTEGER DEFAULT 0
                );

                -- SSE connections table
                CREATE TABLE IF NOT EXISTS sse_connections (
                    connection_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'inactive',
                    connected_at TEXT,
                    last_event_at TEXT,
                    last_keepalive_at TEXT,
                    last_sequence INTEGER DEFAULT 0,
                    events_sent INTEGER DEFAULT 0,
                    reconnect_count INTEGER DEFAULT 0,
                    client_version TEXT,
                    client_ip TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                        ON DELETE CASCADE
                );

                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_sse_connections_session
                    ON sse_connections(session_id);
                CREATE INDEX IF NOT EXISTS idx_sse_connections_status
                    ON sse_connections(status);
                CREATE INDEX IF NOT EXISTS idx_sse_connections_keepalive
                    ON sse_connections(last_keepalive_at);
            """)
            conn.commit()
            logger.info(f"Session state schema initialized: {self._db_path}")
        finally:
            conn.close()

    def save_session(self, session: SessionSSEState) -> None:
        """
        Save or update session state.
        
        Args:
            session: Session state to save
        """
        with self._lock:
            conn = self._get_connection()
            try:
                # Upsert session
                conn.execute("""
                    INSERT INTO sessions (
                        session_id, user_id, created_at, updated_at,
                        max_connections, total_events_sent, total_reconnects
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        user_id = excluded.user_id,
                        updated_at = excluded.updated_at,
                        max_connections = excluded.max_connections,
                        total_events_sent = excluded.total_events_sent,
                        total_reconnects = excluded.total_reconnects
                """, (
                    session.session_id,
                    session.user_id,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.max_connections,
                    session.total_events_sent,
                    session.total_reconnects,
                ))

                # Save connections
                for conn_info in session.sse_connections:
                    self._save_connection(conn, session.session_id, conn_info)

                conn.commit()
                logger.debug(f"Session saved: {session.session_id}")
            finally:
                conn.close()

    def _save_connection(
        self,
        conn: sqlite3.Connection,
        session_id: str,
        connection: SSEConnectionInfo
    ) -> None:
        """Save SSE connection info."""
        conn.execute("""
            INSERT INTO sse_connections (
                connection_id, session_id, status, connected_at,
                last_event_at, last_keepalive_at, last_sequence,
                events_sent, reconnect_count, client_version, client_ip
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(connection_id) DO UPDATE SET
                status = excluded.status,
                connected_at = excluded.connected_at,
                last_event_at = excluded.last_event_at,
                last_keepalive_at = excluded.last_keepalive_at,
                last_sequence = excluded.last_sequence,
                events_sent = excluded.events_sent,
                reconnect_count = excluded.reconnect_count
        """, (
            connection.connection_id,
            session_id,
            connection.status.value,
            connection.connected_at.isoformat() if connection.connected_at else None,
            connection.last_event_at.isoformat() if connection.last_event_at else None,
            connection.last_keepalive_at.isoformat() if connection.last_keepalive_at else None,
            connection.last_sequence,
            connection.events_sent,
            connection.reconnect_count,
            connection.client_version,
            connection.client_ip,
        ))

    def get_session(self, session_id: str) -> Optional[SessionSSEState]:
        """
        Load session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionSSEState if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute(
                    "SELECT * FROM sessions WHERE session_id = ?",
                    (session_id,)
                ).fetchone()

                if not row:
                    return None

                # Load connections
                conn_rows = conn.execute(
                    "SELECT * FROM sse_connections WHERE session_id = ?",
                    (session_id,)
                ).fetchall()

                connections = [
                    SSEConnectionInfo(
                        connection_id=r["connection_id"],
                        status=SSEConnectionStatus(r["status"]),
                        connected_at=datetime.fromisoformat(r["connected_at"]) if r["connected_at"] else None,
                        last_event_at=datetime.fromisoformat(r["last_event_at"]) if r["last_event_at"] else None,
                        last_keepalive_at=datetime.fromisoformat(r["last_keepalive_at"]) if r["last_keepalive_at"] else None,
                        last_sequence=r["last_sequence"],
                        events_sent=r["events_sent"],
                        reconnect_count=r["reconnect_count"],
                        client_version=r["client_version"],
                        client_ip=r["client_ip"],
                    )
                    for r in conn_rows
                ]

                return SessionSSEState(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    sse_connections=connections,
                    max_connections=row["max_connections"],
                    total_events_sent=row["total_events_sent"],
                    total_reconnects=row["total_reconnects"],
                )
            finally:
                conn.close()

    def create_session(self, session_id: str, user_id: Optional[str] = None) -> SessionSSEState:
        """
        Create a new session.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            
        Returns:
            Created SessionSSEState
        """
        session = SessionSSEState(
            session_id=session_id,
            user_id=user_id,
        )
        self.save_session(session)
        return session

    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> SessionSSEState:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            
        Returns:
            SessionSSEState (existing or new)
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, user_id)
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session and all connections.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            conn = self._get_connection()
            try:
                # Delete connections first (FK constraint)
                conn.execute(
                    "DELETE FROM sse_connections WHERE session_id = ?",
                    (session_id,)
                )
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def update_connection_status(
        self,
        connection_id: str,
        status: SSEConnectionStatus
    ) -> bool:
        """
        Update connection status.
        
        Args:
            connection_id: Connection identifier
            status: New status
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    "UPDATE sse_connections SET status = ? WHERE connection_id = ?",
                    (status.value, connection_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def get_active_connections_count(self, session_id: str) -> int:
        """
        Count active connections for session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Count of active connections
        """
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as count FROM sse_connections WHERE session_id = ? AND status = 'active'",
                    (session_id,)
                ).fetchone()
                return row["count"] if row else 0
            finally:
                conn.close()

    def cleanup_stale_connections(self, max_age_seconds: int = 300) -> int:
        """
        Mark stale connections as terminated.
        
        Args:
            max_age_seconds: Max seconds since last keepalive
            
        Returns:
            Count of connections terminated
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("""
                    UPDATE sse_connections
                    SET status = 'terminated'
                    WHERE status = 'active'
                    AND last_keepalive_at IS NOT NULL
                    AND datetime(last_keepalive_at) < datetime('now', ? || ' seconds')
                """, (f"-{max_age_seconds}",))
                conn.commit()
                count = cursor.rowcount
                if count > 0:
                    logger.info(f"Cleaned up {count} stale connections")
                return count
            finally:
                conn.close()

    def get_all_sessions(self, limit: int = 100) -> List[SessionSSEState]:
        """
        Get all sessions (for admin/diagnostics).
        
        Args:
            limit: Maximum sessions to return
            
        Returns:
            List of SessionSSEState
        """
        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute(
                    "SELECT session_id FROM sessions ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()

                sessions = []
                for row in rows:
                    session = self.get_session(row["session_id"])
                    if session:
                        sessions.append(session)
                return sessions
            finally:
                conn.close()

    def get_stats(self) -> dict:
        """
        Get repository statistics.
        
        Returns:
            Dict with session and connection counts
        """
        with self._lock:
            conn = self._get_connection()
            try:
                session_count = conn.execute(
                    "SELECT COUNT(*) as count FROM sessions"
                ).fetchone()["count"]

                connection_count = conn.execute(
                    "SELECT COUNT(*) as count FROM sse_connections"
                ).fetchone()["count"]

                active_count = conn.execute(
                    "SELECT COUNT(*) as count FROM sse_connections WHERE status = 'active'"
                ).fetchone()["count"]

                return {
                    "total_sessions": session_count,
                    "total_connections": connection_count,
                    "active_connections": active_count,
                    "db_path": self._db_path,
                }
            finally:
                conn.close()


# Module-level singleton for convenience
_default_repository: Optional[SessionStateRepository] = None


def get_session_repository(db_path: str = "data/cip_sessions.db") -> SessionStateRepository:
    """
    Get or create the default session repository.
    
    Args:
        db_path: Database path (only used on first call)
        
    Returns:
        SessionStateRepository singleton
    """
    global _default_repository
    if _default_repository is None:
        _default_repository = SessionStateRepository(db_path)
    return _default_repository
