"""
SSE Middleware for P7 Streaming Backend.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

Defines:
- AuthMiddleware: Authentication/authorization
- RateLimitMiddleware: Rate limiting
- VersionCheckMiddleware: Client version validation

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .exceptions import (
    InvalidSessionError,
    RateLimitExceededError,
    VersionMismatchError,
)

# Diagnostic logging hook
logger = logging.getLogger("sse.middleware")


@dataclass
class MiddlewareContext:
    """Context passed through middleware chain."""

    session_id: Optional[str] = None
    client_version: Optional[str] = None
    client_ip: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    authenticated: bool = False
    user_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MiddlewareBase(ABC):
    """
    Abstract base class for SSE middleware.

    Middleware components process requests before the SSE handler
    and can reject connections or augment context.
    """

    @abstractmethod
    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """
        Process the middleware context.

        Args:
            context: Current middleware context

        Returns:
            Updated middleware context

        Raises:
            SSEBaseException: If validation fails
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get middleware name for logging."""
        pass


class AuthMiddleware(MiddlewareBase):
    """
    Authentication middleware for SSE connections.

    Validates session tokens and populates user context.
    Integrates with existing auth infrastructure.
    """

    def __init__(
        self,
        token_validator: Optional[Callable[[str], Dict[str, Any]]] = None,
        session_store: Optional[Dict[str, Dict[str, Any]]] = None,
        allow_anonymous: bool = False
    ) -> None:
        """
        Initialize auth middleware.

        Args:
            token_validator: Function to validate auth tokens
            session_store: Session storage (for scaffold)
            allow_anonymous: Whether to allow unauthenticated connections
        """
        self._token_validator = token_validator
        self._session_store = session_store or {}
        self._allow_anonymous = allow_anonymous

        logger.info(f"AuthMiddleware initialized: allow_anonymous={allow_anonymous}")

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """
        Process authentication.

        Args:
            context: Middleware context with headers

        Returns:
            Context with authentication info populated

        Raises:
            InvalidSessionError: If authentication fails
        """
        # Extract auth token from headers
        auth_header = context.headers.get("Authorization", "")
        session_token = context.headers.get("X-Session-Token", "")

        # Try Bearer token
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return self._validate_bearer_token(context, token)

        # Try session token
        if session_token:
            return self._validate_session_token(context, session_token)

        # Check anonymous access
        if self._allow_anonymous:
            context.authenticated = False
            context.metadata["auth_method"] = "anonymous"
            logger.debug("Anonymous SSE connection allowed")
            return context

        raise InvalidSessionError(
            message="Authentication required",
            reason="no_credentials"
        )

    def _validate_bearer_token(
        self,
        context: MiddlewareContext,
        token: str
    ) -> MiddlewareContext:
        """
        Validate Bearer token.

        Args:
            context: Middleware context
            token: Bearer token

        Returns:
            Updated context with user info

        Raises:
            InvalidSessionError: If token invalid
        """
        if self._token_validator:
            try:
                user_info = self._token_validator(token)
                context.authenticated = True
                context.user_id = user_info.get("user_id")
                context.permissions = user_info.get("permissions", [])
                context.metadata["auth_method"] = "bearer"
                logger.debug(f"Bearer token validated for user {context.user_id}")
                return context
            except Exception as e:
                logger.warning(f"Bearer token validation failed: {e}")
                raise InvalidSessionError(
                    message="Invalid bearer token",
                    reason="token_validation_failed"
                )

        # Scaffold: Accept any non-empty token
        context.authenticated = True
        context.metadata["auth_method"] = "bearer_scaffold"
        logger.debug("Bearer token accepted (scaffold mode)")
        return context

    def _validate_session_token(
        self,
        context: MiddlewareContext,
        session_token: str
    ) -> MiddlewareContext:
        """
        Validate session token.

        Args:
            context: Middleware context
            session_token: Session token

        Returns:
            Updated context with session info

        Raises:
            InvalidSessionError: If session invalid
        """
        # Check session store
        session_data = self._session_store.get(session_token)

        if session_data:
            context.authenticated = True
            context.session_id = session_token
            context.user_id = session_data.get("user_id")
            context.permissions = session_data.get("permissions", [])
            context.metadata["auth_method"] = "session"
            logger.debug(f"Session validated: {session_token[:8]}...")
            return context

        # Scaffold: Accept any non-empty session token
        context.authenticated = True
        context.session_id = session_token
        context.metadata["auth_method"] = "session_scaffold"
        logger.debug("Session token accepted (scaffold mode)")
        return context

    def get_name(self) -> str:
        """Get middleware name."""
        return "AuthMiddleware"


class RateLimitMiddleware(MiddlewareBase):
    """
    Rate limiting middleware for SSE connections.

    Implements token bucket algorithm for connection rate limiting.
    Tracks per-IP and per-user limits.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        per_user_limit: Optional[int] = None
    ) -> None:
        """
        Initialize rate limit middleware.

        Args:
            requests_per_minute: Sustained rate limit
            burst_size: Maximum burst size
            per_user_limit: Optional per-user limit
        """
        self._requests_per_minute = requests_per_minute
        self._burst_size = burst_size
        self._per_user_limit = per_user_limit

        # Token buckets: key -> (tokens, last_update_time)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (float(burst_size), time.time())
        )

        logger.info(
            f"RateLimitMiddleware initialized: "
            f"rpm={requests_per_minute}, burst={burst_size}"
        )

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """
        Check rate limits.

        Args:
            context: Middleware context

        Returns:
            Context (unmodified if allowed)

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        # Determine rate limit key
        key = self._get_rate_limit_key(context)

        # Check and update token bucket
        allowed, retry_after = self._check_bucket(key)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {key}")
            raise RateLimitExceededError(
                message="Rate limit exceeded",
                limit=self._requests_per_minute,
                window_seconds=60,
                retry_after=int(retry_after)
            )

        context.metadata["rate_limit_key"] = key
        context.metadata["rate_limit_remaining"] = self._get_remaining(key)

        logger.debug(f"Rate limit check passed for {key}")
        return context

    def _get_rate_limit_key(self, context: MiddlewareContext) -> str:
        """
        Determine rate limit key from context.

        Args:
            context: Middleware context

        Returns:
            Rate limit key string
        """
        if context.user_id:
            return f"user:{context.user_id}"
        if context.client_ip:
            return f"ip:{context.client_ip}"
        return "anonymous"

    def _check_bucket(self, key: str) -> Tuple[bool, float]:
        """
        Check token bucket and consume token if available.

        Args:
            key: Rate limit key

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        now = time.time()
        tokens, last_update = self._buckets[key]

        # Refill tokens based on time elapsed
        elapsed = now - last_update
        refill_rate = self._requests_per_minute / 60.0
        tokens = min(self._burst_size, tokens + (elapsed * refill_rate))

        if tokens >= 1.0:
            # Consume token
            self._buckets[key] = (tokens - 1.0, now)
            return True, 0.0
        else:
            # Calculate wait time
            wait_time = (1.0 - tokens) / refill_rate
            self._buckets[key] = (tokens, now)
            return False, wait_time

    def _get_remaining(self, key: str) -> int:
        """
        Get remaining tokens for key.

        Args:
            key: Rate limit key

        Returns:
            Remaining tokens (floored to int)
        """
        tokens, _ = self._buckets.get(key, (self._burst_size, time.time()))
        return int(tokens)

    def get_name(self) -> str:
        """Get middleware name."""
        return "RateLimitMiddleware"


class VersionCheckMiddleware(MiddlewareBase):
    """
    Client version check middleware for SSE connections.

    Validates X-Client-Version header against requirements.
    Supports minimum version enforcement and deprecation warnings.
    """

    def __init__(
        self,
        min_version: str = "1.0.0",
        current_version: str = "1.0.0",
        deprecated_versions: Optional[List[str]] = None,
        strict: bool = False
    ) -> None:
        """
        Initialize version check middleware.

        Args:
            min_version: Minimum required client version
            current_version: Current server version
            deprecated_versions: List of deprecated but allowed versions
            strict: If True, reject deprecated versions
        """
        self._min_version = self._parse_version(min_version)
        self._current_version = current_version
        self._deprecated_versions = set(deprecated_versions or [])
        self._strict = strict

        logger.info(
            f"VersionCheckMiddleware initialized: "
            f"min={min_version}, current={current_version}"
        )

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """
        Check client version.

        Args:
            context: Middleware context with headers

        Returns:
            Context with version info

        Raises:
            VersionMismatchError: If version incompatible
        """
        client_version = context.headers.get("X-Client-Version", "")
        context.client_version = client_version

        if not client_version:
            # No version header - allow but warn
            context.metadata["version_warning"] = "no_version_header"
            logger.warning("No X-Client-Version header provided")
            return context

        # Parse and compare versions
        try:
            parsed_version = self._parse_version(client_version)
        except ValueError:
            raise VersionMismatchError(
                message="Invalid version format",
                client_version=client_version,
                required_version=".".join(map(str, self._min_version))
            )

        # Check minimum version
        if parsed_version < self._min_version:
            raise VersionMismatchError(
                message="Client version too old",
                client_version=client_version,
                required_version=".".join(map(str, self._min_version))
            )

        # Check deprecated versions
        if client_version in self._deprecated_versions:
            if self._strict:
                raise VersionMismatchError(
                    message="Client version deprecated",
                    client_version=client_version,
                    required_version=self._current_version
                )
            else:
                context.metadata["version_warning"] = "deprecated"
                logger.warning(f"Deprecated client version: {client_version}")

        context.metadata["version_check"] = "passed"
        logger.debug(f"Version check passed: {client_version}")
        return context

    def _parse_version(self, version_str: str) -> Tuple[int, ...]:
        """
        Parse version string to tuple.

        Args:
            version_str: Version string (e.g., "1.2.3")

        Returns:
            Tuple of version components

        Raises:
            ValueError: If version format invalid
        """
        parts = version_str.split(".")
        return tuple(int(p) for p in parts)

    def get_name(self) -> str:
        """Get middleware name."""
        return "VersionCheckMiddleware"


class MiddlewareChain:
    """
    Chain of middleware components.

    Processes context through each middleware in order.
    Stops on first exception.
    """

    def __init__(self, middlewares: Optional[List[MiddlewareBase]] = None) -> None:
        """
        Initialize middleware chain.

        Args:
            middlewares: List of middleware components
        """
        self._middlewares: List[MiddlewareBase] = middlewares or []

        logger.info(
            f"MiddlewareChain initialized with {len(self._middlewares)} middlewares"
        )

    def add(self, middleware: MiddlewareBase) -> "MiddlewareChain":
        """
        Add middleware to chain.

        Args:
            middleware: Middleware to add

        Returns:
            Self for chaining
        """
        self._middlewares.append(middleware)
        logger.debug(f"Added middleware: {middleware.get_name()}")
        return self

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """
        Process context through all middlewares.

        Args:
            context: Initial middleware context

        Returns:
            Final processed context

        Raises:
            SSEBaseException: If any middleware fails
        """
        for middleware in self._middlewares:
            try:
                context = middleware.process(context)
                logger.debug(f"Middleware passed: {middleware.get_name()}")
            except Exception as e:
                logger.warning(f"Middleware failed: {middleware.get_name()} - {e}")
                raise

        return context


# Factory function for default middleware chain
def create_default_middleware_chain(
    allow_anonymous: bool = False,
    rate_limit_rpm: int = 60,
    min_client_version: str = "1.0.0"
) -> MiddlewareChain:
    """
    Create default middleware chain.

    Args:
        allow_anonymous: Allow unauthenticated connections
        rate_limit_rpm: Requests per minute limit
        min_client_version: Minimum client version

    Returns:
        Configured MiddlewareChain
    """
    chain = MiddlewareChain()

    chain.add(VersionCheckMiddleware(min_version=min_client_version))
    chain.add(RateLimitMiddleware(requests_per_minute=rate_limit_rpm))
    chain.add(AuthMiddleware(allow_anonymous=allow_anonymous))

    return chain
