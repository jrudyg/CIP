"""
Session State Repository for P7 Streaming Backend.

Phase: P7.S2
Author: CC1 (Backend Mechanic)
Directive: S2.T1_SESSION_STATE_MODELS

Defines:
- ISessionRepository interface
- InMemorySessionRepository implementation
- Repository exceptions

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import logging
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from .models import SessionState, SessionStatus

# Diagnostic logging hook
logger = logging.getLogger("session_state.repository")


# =============================================================================
# EXCEPTIONS
# =============================================================================


class SessionRepositoryError(Exception):
    """Base exception for session repository errors."""

    def __init__(self, message: str, session_id: Optional[str] = None) -> None:
        self.message = message
        self.session_id = session_id
        super().__init__(message)

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "session_id": self.session_id,
        }


class SessionNotFoundError(SessionRepositoryError):
    """Raised when a session is not found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            message=f"Session not found: {session_id}",
            session_id=session_id
        )


class SessionAlreadyExistsError(SessionRepositoryError):
    """Raised when attempting to create a duplicate session."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            message=f"Session already exists: {session_id}",
            session_id=session_id
        )


# =============================================================================
# REPOSITORY INTERFACE
# =============================================================================


class ISessionRepository(ABC):
    """
    Interface for session state persistence.

    Implementations must be thread-safe.
    """

    @abstractmethod
    def create(self, session: SessionState) -> SessionState:
        """
        Create a new session.

        Args:
            session: Session state to create

        Returns:
            Created session state

        Raises:
            SessionAlreadyExistsError: If session already exists
        """
        pass

    @abstractmethod
    def get(self, session_id: str) -> SessionState:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session state

        Raises:
            SessionNotFoundError: If session not found
        """
        pass

    @abstractmethod
    def get_or_none(self, session_id: str) -> Optional[SessionState]:
        """
        Get a session by ID or None if not found.

        Args:
            session_id: Session identifier

        Returns:
            Session state or None
        """
        pass

    @abstractmethod
    def update(self, session: SessionState) -> SessionState:
        """
        Update an existing session.

        Args:
            session: Session state to update

        Returns:
            Updated session state

        Raises:
            SessionNotFoundError: If session not found
        """
        pass

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_by_status(self, status: SessionStatus) -> List[SessionState]:
        """
        List sessions by status.

        Args:
            status: Session status to filter by

        Returns:
            List of matching sessions
        """
        pass

    @abstractmethod
    def list_active(self) -> List[SessionState]:
        """
        List all active sessions.

        Returns:
            List of active sessions
        """
        pass

    @abstractmethod
    def list_stale(self, threshold_seconds: int) -> List[SessionState]:
        """
        List sessions that are stale (no activity within threshold).

        Args:
            threshold_seconds: Inactivity threshold in seconds

        Returns:
            List of stale sessions
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total session count.

        Returns:
            Number of sessions
        """
        pass

    @abstractmethod
    def count_by_status(self, status: SessionStatus) -> int:
        """
        Get session count by status.

        Args:
            status: Session status to count

        Returns:
            Number of sessions with status
        """
        pass


# =============================================================================
# IN-MEMORY IMPLEMENTATION
# =============================================================================


class InMemorySessionRepository(ISessionRepository):
    """
    In-memory session repository implementation.

    Thread-safe using a read-write lock pattern.
    Suitable for development and single-instance deployments.
    """

    def __init__(self) -> None:
        """Initialize the in-memory repository."""
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.RLock()

        logger.info("InMemorySessionRepository initialized")

    def create(self, session: SessionState) -> SessionState:
        """
        Create a new session.

        Args:
            session: Session state to create

        Returns:
            Created session state

        Raises:
            SessionAlreadyExistsError: If session already exists
        """
        with self._lock:
            if session.session_id in self._sessions:
                raise SessionAlreadyExistsError(session.session_id)

            self._sessions[session.session_id] = session
            logger.debug(f"Session created: {session.session_id}")

            return session

    def get(self, session_id: str) -> SessionState:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session state

        Raises:
            SessionNotFoundError: If session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            return session

    def get_or_none(self, session_id: str) -> Optional[SessionState]:
        """
        Get a session by ID or None if not found.

        Args:
            session_id: Session identifier

        Returns:
            Session state or None
        """
        with self._lock:
            return self._sessions.get(session_id)

    def update(self, session: SessionState) -> SessionState:
        """
        Update an existing session.

        Args:
            session: Session state to update

        Returns:
            Updated session state

        Raises:
            SessionNotFoundError: If session not found
        """
        with self._lock:
            if session.session_id not in self._sessions:
                raise SessionNotFoundError(session.session_id)

            self._sessions[session.session_id] = session
            logger.debug(f"Session updated: {session.session_id}")

            return session

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.debug(f"Session deleted: {session_id}")
                return True
            return False

    def list_by_status(self, status: SessionStatus) -> List[SessionState]:
        """
        List sessions by status.

        Args:
            status: Session status to filter by

        Returns:
            List of matching sessions
        """
        with self._lock:
            return [
                session for session in self._sessions.values()
                if session.status == status
            ]

    def list_active(self) -> List[SessionState]:
        """
        List all active sessions.

        Returns:
            List of active sessions
        """
        with self._lock:
            return [
                session for session in self._sessions.values()
                if session.is_active()
            ]

    def list_stale(self, threshold_seconds: int) -> List[SessionState]:
        """
        List sessions that are stale (no activity within threshold).

        Args:
            threshold_seconds: Inactivity threshold in seconds

        Returns:
            List of stale sessions
        """
        with self._lock:
            now = datetime.now()
            stale_sessions = []

            for session in self._sessions.values():
                if not session.is_active():
                    continue

                # Check last activity
                last_activity = session.last_event_at or session.last_keepalive_at
                if last_activity:
                    last_time = datetime.fromisoformat(last_activity)
                    delta = (now - last_time).total_seconds()
                    if delta > threshold_seconds:
                        stale_sessions.append(session)

            return stale_sessions

    def count(self) -> int:
        """
        Get total session count.

        Returns:
            Number of sessions
        """
        with self._lock:
            return len(self._sessions)

    def count_by_status(self, status: SessionStatus) -> int:
        """
        Get session count by status.

        Args:
            status: Session status to count

        Returns:
            Number of sessions with status
        """
        with self._lock:
            return sum(
                1 for session in self._sessions.values()
                if session.status == status
            )

    def clear(self) -> int:
        """
        Clear all sessions (for testing).

        Returns:
            Number of sessions cleared
        """
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            logger.info(f"Repository cleared: {count} sessions removed")
            return count

    def get_all(self) -> List[SessionState]:
        """
        Get all sessions (for diagnostics).

        Returns:
            List of all sessions
        """
        with self._lock:
            return list(self._sessions.values())
