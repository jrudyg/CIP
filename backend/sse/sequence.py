"""
SSE Sequence Generator for P7 Streaming Backend.

Phase: P7.S1
Author: CC1 (Backend Mechanic)
Directive: P7.S1_IMPLEMENT_SSE_BACKEND

Defines:
- ISequenceGenerator protocol (interface)
- DatabaseSequenceGenerator scaffold
- RedisSequenceGenerator scaffold
- InMemorySequenceGenerator (for testing)

CIP Protocol: This module is part of the P7 SSE backend.
Frozen surfaces (TRUST, GEM, Z7, API shapes) are NOT modified.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Protocol, runtime_checkable

# Diagnostic logging hook
logger = logging.getLogger("sse.sequence")


@runtime_checkable
class ISequenceGenerator(Protocol):
    """
    Protocol (interface) for sequence number generation.

    Sequence generators must provide:
    - Monotonically increasing sequence numbers
    - Thread-safe generation
    - Optional persistence for durability
    - Current sequence retrieval
    """

    def next(self) -> int:
        """
        Generate and return the next sequence number.

        Returns:
            Next monotonically increasing sequence number
        """
        ...

    def current(self) -> int:
        """
        Get the current sequence number without incrementing.

        Returns:
            Current sequence number
        """
        ...

    def reset(self, value: int = 0) -> None:
        """
        Reset the sequence to a specific value.

        Args:
            value: Value to reset to (default 0)
        """
        ...


class SequenceGeneratorBase(ABC):
    """
    Abstract base class for sequence generators.

    Provides common functionality and enforces interface.
    """

    @abstractmethod
    def next(self) -> int:
        """Generate next sequence number."""
        pass

    @abstractmethod
    def current(self) -> int:
        """Get current sequence number."""
        pass

    @abstractmethod
    def reset(self, value: int = 0) -> None:
        """Reset sequence to value."""
        pass

    def validate_sequence(self, sequence: int) -> bool:
        """
        Validate a sequence number.

        Args:
            sequence: Sequence number to validate

        Returns:
            True if valid, False otherwise
        """
        return isinstance(sequence, int) and sequence >= 0


class InMemorySequenceGenerator(SequenceGeneratorBase):
    """
    Thread-safe in-memory sequence generator.

    Use for:
    - Testing
    - Single-instance deployments
    - Development environments

    NOT recommended for:
    - Multi-instance deployments (no shared state)
    - Production (no persistence)
    """

    def __init__(self, start: int = 0) -> None:
        """
        Initialize in-memory sequence generator.

        Args:
            start: Starting sequence number (default 0)
        """
        self._sequence = start
        self._lock = threading.Lock()

        logger.info(f"InMemorySequenceGenerator initialized at {start}")

    def next(self) -> int:
        """
        Generate next sequence number (thread-safe).

        Returns:
            Next sequence number
        """
        with self._lock:
            self._sequence += 1
            seq = self._sequence

        logger.debug(f"Sequence generated: {seq}")
        return seq

    def current(self) -> int:
        """
        Get current sequence number.

        Returns:
            Current sequence number
        """
        with self._lock:
            return self._sequence

    def reset(self, value: int = 0) -> None:
        """
        Reset sequence to value.

        Args:
            value: Value to reset to
        """
        with self._lock:
            self._sequence = value

        logger.info(f"Sequence reset to {value}")


class DatabaseSequenceGenerator(SequenceGeneratorBase):
    """
    Database-backed sequence generator scaffold.

    Provides persistent sequence numbers via database storage.
    Suitable for multi-instance deployments with shared database.

    NOTE: This is a scaffold - actual database implementation
    to be completed in P7.S2.
    """

    def __init__(
        self,
        table_name: str = "sse_sequences",
        sequence_name: str = "default",
        connection_string: Optional[str] = None
    ) -> None:
        """
        Initialize database sequence generator.

        Args:
            table_name: Database table for sequences
            sequence_name: Name of this sequence
            connection_string: Database connection string
        """
        self._table_name = table_name
        self._sequence_name = sequence_name
        self._connection_string = connection_string
        self._local_cache: Optional[int] = None
        self._lock = threading.Lock()

        logger.info(
            f"DatabaseSequenceGenerator initialized: "
            f"table={table_name}, name={sequence_name}"
        )

    def next(self) -> int:
        """
        Generate next sequence number from database.

        Returns:
            Next sequence number

        NOTE: Scaffold implementation - returns local increment.
        Full database implementation in P7.S2.
        """
        with self._lock:
            if self._local_cache is None:
                self._local_cache = self._fetch_from_database()

            self._local_cache += 1
            seq = self._local_cache

            # Scaffold: Would persist to database here
            self._persist_to_database(seq)

        logger.debug(f"Database sequence generated: {seq}")
        return seq

    def current(self) -> int:
        """
        Get current sequence from database.

        Returns:
            Current sequence number
        """
        with self._lock:
            if self._local_cache is None:
                self._local_cache = self._fetch_from_database()
            return self._local_cache

    def reset(self, value: int = 0) -> None:
        """
        Reset sequence in database.

        Args:
            value: Value to reset to
        """
        with self._lock:
            self._local_cache = value
            self._persist_to_database(value)

        logger.info(f"Database sequence reset to {value}")

    def _fetch_from_database(self) -> int:
        """
        Fetch current sequence from database.

        Returns:
            Sequence value from database

        NOTE: Scaffold - returns 0. Implement in P7.S2.
        """
        # Scaffold: Would execute:
        # SELECT sequence_value FROM {table} WHERE name = {name}
        logger.debug("Scaffold: fetch_from_database called")
        return 0

    def _persist_to_database(self, value: int) -> None:
        """
        Persist sequence value to database.

        Args:
            value: Sequence value to persist

        NOTE: Scaffold - no-op. Implement in P7.S2.
        """
        # Scaffold: Would execute:
        # UPDATE {table} SET sequence_value = {value} WHERE name = {name}
        logger.debug(f"Scaffold: persist_to_database({value}) called")


class RedisSequenceGenerator(SequenceGeneratorBase):
    """
    Redis-backed sequence generator scaffold.

    Provides distributed sequence numbers via Redis INCR.
    Suitable for high-throughput multi-instance deployments.

    NOTE: This is a scaffold - actual Redis implementation
    to be completed in P7.S2.
    """

    def __init__(
        self,
        key: str = "sse:sequence:default",
        redis_url: Optional[str] = None
    ) -> None:
        """
        Initialize Redis sequence generator.

        Args:
            key: Redis key for this sequence
            redis_url: Redis connection URL
        """
        self._key = key
        self._redis_url = redis_url
        self._local_fallback = 0
        self._lock = threading.Lock()

        logger.info(f"RedisSequenceGenerator initialized: key={key}")

    def next(self) -> int:
        """
        Generate next sequence number via Redis INCR.

        Returns:
            Next sequence number

        NOTE: Scaffold implementation - returns local increment.
        Full Redis implementation in P7.S2.
        """
        with self._lock:
            # Scaffold: Would execute INCR on Redis
            # seq = redis_client.incr(self._key)
            self._local_fallback += 1
            seq = self._local_fallback

        logger.debug(f"Redis sequence generated: {seq}")
        return seq

    def current(self) -> int:
        """
        Get current sequence from Redis.

        Returns:
            Current sequence number
        """
        with self._lock:
            # Scaffold: Would execute GET on Redis
            # return int(redis_client.get(self._key) or 0)
            return self._local_fallback

    def reset(self, value: int = 0) -> None:
        """
        Reset sequence in Redis.

        Args:
            value: Value to reset to
        """
        with self._lock:
            # Scaffold: Would execute SET on Redis
            # redis_client.set(self._key, value)
            self._local_fallback = value

        logger.info(f"Redis sequence reset to {value}")


class TimestampSequenceGenerator(SequenceGeneratorBase):
    """
    Timestamp-based sequence generator.

    Uses high-resolution timestamp combined with counter
    for unique, time-ordered sequences.

    Format: timestamp_millis * 1000 + counter
    """

    def __init__(self) -> None:
        """Initialize timestamp sequence generator."""
        self._last_timestamp: int = 0
        self._counter: int = 0
        self._lock = threading.Lock()

        logger.info("TimestampSequenceGenerator initialized")

    def next(self) -> int:
        """
        Generate next timestamp-based sequence.

        Returns:
            Unique timestamp-based sequence number
        """
        with self._lock:
            current_ms = int(time.time() * 1000)

            if current_ms == self._last_timestamp:
                self._counter += 1
            else:
                self._last_timestamp = current_ms
                self._counter = 0

            seq = (current_ms * 1000) + self._counter

        logger.debug(f"Timestamp sequence generated: {seq}")
        return seq

    def current(self) -> int:
        """
        Get current sequence (last generated).

        Returns:
            Last generated sequence number
        """
        with self._lock:
            return (self._last_timestamp * 1000) + self._counter

    def reset(self, value: int = 0) -> None:
        """
        Reset sequence (clears counter, not timestamp).

        Args:
            value: Ignored for timestamp generator
        """
        with self._lock:
            self._counter = 0
            self._last_timestamp = 0

        logger.info("Timestamp sequence reset")


# Factory function for sequence generator selection
def create_sequence_generator(
    generator_type: str = "memory",
    **kwargs
) -> SequenceGeneratorBase:
    """
    Factory function to create sequence generators.

    Args:
        generator_type: Type of generator ("memory", "database", "redis", "timestamp")
        **kwargs: Additional arguments for specific generator

    Returns:
        Configured sequence generator instance
    """
    generators = {
        "memory": InMemorySequenceGenerator,
        "database": DatabaseSequenceGenerator,
        "redis": RedisSequenceGenerator,
        "timestamp": TimestampSequenceGenerator
    }

    generator_class = generators.get(generator_type)
    if generator_class is None:
        logger.warning(f"Unknown generator type: {generator_type}, using memory")
        generator_class = InMemorySequenceGenerator

    return generator_class(**kwargs)
