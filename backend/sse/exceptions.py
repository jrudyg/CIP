"""
SSE Exception Classes for P7 Streaming Backend.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

Defines custom exceptions for SSE operations:
- InvalidSessionError: Session validation failures
- VersionMismatchError: Client version incompatibility
- RateLimitExceededError: Rate limiting triggered
- SSEInternalError: Internal SSE processing errors

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

from typing import Optional


class SSEBaseException(Exception):
    """Base exception for all SSE-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize SSE base exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Optional additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class InvalidSessionError(SSEBaseException):
    """
    Raised when session validation fails.

    Scenarios:
    - Session ID not found
    - Session expired
    - Session revoked
    - Invalid session token format
    """

    def __init__(
        self,
        message: str = "Invalid or expired session",
        session_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Initialize InvalidSessionError.

        Args:
            message: Error message
            session_id: The invalid session identifier
            reason: Specific reason for invalidity
        """
        details = {}
        if session_id:
            details["session_id"] = session_id
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            error_code="SSE_INVALID_SESSION",
            details=details
        )
        self.session_id = session_id
        self.reason = reason


class VersionMismatchError(SSEBaseException):
    """
    Raised when client version is incompatible.

    Scenarios:
    - Client version too old
    - Client version not recognized
    - Protocol version mismatch
    """

    def __init__(
        self,
        message: str = "Client version mismatch",
        client_version: Optional[str] = None,
        required_version: Optional[str] = None
    ) -> None:
        """
        Initialize VersionMismatchError.

        Args:
            message: Error message
            client_version: Version provided by client
            required_version: Minimum required version
        """
        details = {}
        if client_version:
            details["client_version"] = client_version
        if required_version:
            details["required_version"] = required_version

        super().__init__(
            message=message,
            error_code="SSE_VERSION_MISMATCH",
            details=details
        )
        self.client_version = client_version
        self.required_version = required_version


class RateLimitExceededError(SSEBaseException):
    """
    Raised when rate limit is exceeded.

    Scenarios:
    - Too many connection attempts
    - Message rate exceeded
    - Burst limit exceeded
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: Optional[int] = None
    ) -> None:
        """
        Initialize RateLimitExceededError.

        Args:
            message: Error message
            limit: The rate limit that was exceeded
            window_seconds: Time window for the limit
            retry_after: Seconds until retry is allowed
        """
        details = {}
        if limit is not None:
            details["limit"] = limit
        if window_seconds is not None:
            details["window_seconds"] = window_seconds
        if retry_after is not None:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code="SSE_RATE_LIMIT_EXCEEDED",
            details=details
        )
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after


class SSEInternalError(SSEBaseException):
    """
    Raised for internal SSE processing errors.

    Scenarios:
    - Serialization failure
    - Buffer overflow
    - Connection state corruption
    - Unexpected handler state
    """

    def __init__(
        self,
        message: str = "Internal SSE error",
        component: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize SSEInternalError.

        Args:
            message: Error message
            component: Component where error occurred
            operation: Operation that failed
            original_error: The underlying exception if any
        """
        details = {}
        if component:
            details["component"] = component
        if operation:
            details["operation"] = operation
        if original_error:
            details["original_error"] = str(original_error)

        super().__init__(
            message=message,
            error_code="SSE_INTERNAL_ERROR",
            details=details
        )
        self.component = component
        self.operation = operation
        self.original_error = original_error


class ConnectionClosedError(SSEBaseException):
    """
    Raised when connection is unexpectedly closed.

    Scenarios:
    - Client disconnect
    - Network interruption
    - Timeout
    """

    def __init__(
        self,
        message: str = "SSE connection closed",
        reason: Optional[str] = None,
        was_clean: bool = False
    ) -> None:
        """
        Initialize ConnectionClosedError.

        Args:
            message: Error message
            reason: Reason for closure
            was_clean: Whether closure was clean/expected
        """
        details = {
            "was_clean": was_clean
        }
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            error_code="SSE_CONNECTION_CLOSED",
            details=details
        )
        self.reason = reason
        self.was_clean = was_clean


class BackpressureError(SSEBaseException):
    """
    Raised when backpressure threshold is exceeded.

    Scenarios:
    - Client not consuming events fast enough
    - Buffer overflow imminent
    - Flow control triggered
    """

    def __init__(
        self,
        message: str = "Backpressure threshold exceeded",
        buffer_size: Optional[int] = None,
        threshold: Optional[int] = None
    ) -> None:
        """
        Initialize BackpressureError.

        Args:
            message: Error message
            buffer_size: Current buffer size
            threshold: Threshold that was exceeded
        """
        details = {}
        if buffer_size is not None:
            details["buffer_size"] = buffer_size
        if threshold is not None:
            details["threshold"] = threshold

        super().__init__(
            message=message,
            error_code="SSE_BACKPRESSURE",
            details=details
        )
        self.buffer_size = buffer_size
        self.threshold = threshold
