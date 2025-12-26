"""
Embedding Cache for Phase 5 SAE (Semantic Alignment Engine)
Stores clause embeddings to avoid redundant API calls.

Phase 5 Step 1: Schema and metrics only.
Intelligence activation happens in Step 2.
"""

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from phase5_flags import is_flag_enabled, get_config


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CachedEmbedding:
    """Cached embedding record"""
    id: int
    clause_text_hash: str
    embedding_vector: bytes
    model_version: str
    created_at: datetime
    access_count: int
    last_accessed_at: datetime


# ============================================================================
# EMBEDDING CACHE CLASS
# ============================================================================

class EmbeddingCache:
    """
    SQLite-based cache for clause embeddings.

    Phase 5 Step 1: Schema creation and metrics only.
    Actual embedding storage/retrieval activated by embedding_cache_active flag.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize embedding cache.

        Args:
            db_path: Path to SQLite database (defaults to data/clause_embeddings.db)
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "data",
                "clause_embeddings.db"
            )

        self.db_path = os.path.abspath(db_path)
        self._ensure_directory()
        self._init_schema()

        # Metrics counters (in-memory)
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0,
            "errors": 0,
        }

    def _ensure_directory(self) -> None:
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_schema(self) -> None:
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create clause_embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clause_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clause_text_hash TEXT UNIQUE NOT NULL,
                embedding_vector BLOB NOT NULL,
                model_version TEXT NOT NULL,
                vector_dimensions INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)

        # Create index on clause_text_hash for O(1) lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_clause_text_hash
            ON clause_embeddings(clause_text_hash)
        """)

        # Create index on last_accessed_at for LRU eviction
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed
            ON clause_embeddings(last_accessed_at)
        """)

        # Create cache_metadata table for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initialize metadata
        cursor.execute("""
            INSERT OR IGNORE INTO cache_metadata (key, value)
            VALUES ('schema_version', '1.0.0')
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO cache_metadata (key, value)
            VALUES ('created_at', ?)
        """, (datetime.now().isoformat(),))

        conn.commit()
        conn.close()

    @staticmethod
    def compute_hash(clause_text: str) -> str:
        """
        Compute deterministic hash for clause text.

        Args:
            clause_text: Raw clause text

        Returns:
            SHA-256 hash hex string
        """
        normalized = clause_text.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def get(self, clause_text: str) -> Optional[bytes]:
        """
        Get cached embedding for clause text.

        Args:
            clause_text: Clause text to look up

        Returns:
            Embedding vector bytes or None if not cached

        Note: Only returns data if embedding_cache_active flag is True.
        """
        # Check feature flag
        if not is_flag_enabled("embedding_cache_active"):
            self._metrics["misses"] += 1
            return None

        clause_hash = self.compute_hash(clause_text)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT embedding_vector FROM clause_embeddings
                WHERE clause_text_hash = ?
            """, (clause_hash,))

            row = cursor.fetchone()

            if row:
                # Update access tracking
                cursor.execute("""
                    UPDATE clause_embeddings
                    SET access_count = access_count + 1,
                        last_accessed_at = CURRENT_TIMESTAMP
                    WHERE clause_text_hash = ?
                """, (clause_hash,))
                conn.commit()

                self._metrics["hits"] += 1
                conn.close()
                return row[0]
            else:
                self._metrics["misses"] += 1
                conn.close()
                return None

        except sqlite3.Error as e:
            self._metrics["errors"] += 1
            return None

    def put(
        self,
        clause_text: str,
        embedding_vector: bytes,
        model_version: str,
        vector_dimensions: int
    ) -> bool:
        """
        Store embedding in cache.

        Args:
            clause_text: Original clause text
            embedding_vector: Embedding as bytes (BLOB)
            model_version: Model that generated the embedding
            vector_dimensions: Number of dimensions in vector

        Returns:
            True if stored successfully, False otherwise

        Note: Only stores data if embedding_cache_active flag is True.
        """
        # Check feature flag
        if not is_flag_enabled("embedding_cache_active"):
            return False

        clause_hash = self.compute_hash(clause_text)

        try:
            # Check max entries limit
            max_entries = get_config("embedding_cache_max_entries", 10000)
            if self._get_entry_count() >= max_entries:
                self._evict_lru(count=100)  # Evict oldest 100 entries

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO clause_embeddings
                (clause_text_hash, embedding_vector, model_version,
                 vector_dimensions, created_at, last_accessed_at, access_count)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """, (clause_hash, embedding_vector, model_version, vector_dimensions))

            conn.commit()
            conn.close()

            self._metrics["writes"] += 1
            return True

        except sqlite3.Error as e:
            self._metrics["errors"] += 1
            return False

    def _get_entry_count(self) -> int:
        """Get current number of cached entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clause_embeddings")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except sqlite3.Error:
            return 0

    def _evict_lru(self, count: int = 100) -> int:
        """
        Evict least recently used entries.

        Args:
            count: Number of entries to evict

        Returns:
            Number of entries evicted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM clause_embeddings
                WHERE id IN (
                    SELECT id FROM clause_embeddings
                    ORDER BY last_accessed_at ASC
                    LIMIT ?
                )
            """, (count,))

            evicted = cursor.rowcount
            conn.commit()
            conn.close()

            self._metrics["evictions"] += evicted
            return evicted

        except sqlite3.Error:
            return 0

    def invalidate(self, clause_text: str) -> bool:
        """
        Invalidate cached embedding for specific clause.

        Args:
            clause_text: Clause text to invalidate

        Returns:
            True if invalidated, False otherwise
        """
        clause_hash = self.compute_hash(clause_text)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM clause_embeddings
                WHERE clause_text_hash = ?
            """, (clause_hash,))

            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted

        except sqlite3.Error:
            return False

    def clear(self) -> Dict[str, int]:
        """
        Clear all cached embeddings.

        Returns:
            Statistics about cleared cache
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM clause_embeddings")
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM clause_embeddings")
            conn.commit()
            conn.close()

            self._metrics["evictions"] += count
            return {"deleted_entries": count}

        except sqlite3.Error:
            return {"deleted_entries": 0}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics and metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Entry count
            cursor.execute("SELECT COUNT(*) FROM clause_embeddings")
            entry_count = cursor.fetchone()[0]

            # Total size
            cursor.execute("""
                SELECT SUM(LENGTH(embedding_vector)) FROM clause_embeddings
            """)
            total_size = cursor.fetchone()[0] or 0

            # Model versions
            cursor.execute("""
                SELECT model_version, COUNT(*) as cnt
                FROM clause_embeddings
                GROUP BY model_version
            """)
            model_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Oldest and newest entries
            cursor.execute("""
                SELECT MIN(created_at), MAX(created_at)
                FROM clause_embeddings
            """)
            date_range = cursor.fetchone()

            conn.close()

            # Calculate hit rate
            total_requests = self._metrics["hits"] + self._metrics["misses"]
            hit_rate = (
                self._metrics["hits"] / total_requests
                if total_requests > 0 else 0.0
            )

            return {
                "entry_count": entry_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "model_versions": model_counts,
                "oldest_entry": date_range[0] if date_range else None,
                "newest_entry": date_range[1] if date_range else None,
                "metrics": self._metrics.copy(),
                "hit_rate": hit_rate,
                "max_entries": get_config("embedding_cache_max_entries", 10000),
                "ttl_hours": get_config("embedding_cache_ttl_hours", 168),
                "flag_enabled": is_flag_enabled("embedding_cache_active"),
                "db_path": self.db_path,
            }

        except sqlite3.Error as e:
            return {
                "error": str(e),
                "metrics": self._metrics.copy(),
                "flag_enabled": is_flag_enabled("embedding_cache_active"),
            }

    def get_metrics(self) -> Dict[str, int]:
        """
        Get cache metrics counters.

        Returns:
            Dictionary with hits, misses, writes, evictions, errors
        """
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset metrics counters to zero"""
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0,
            "errors": 0,
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """
    Get global embedding cache instance.

    Returns:
        EmbeddingCache singleton
    """
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache


# ============================================================================
# PUBLIC API FUNCTIONS (Step 1 - No call sites yet)
# ============================================================================

@dataclass
class EmbeddingRecord:
    """Embedding record returned by get_or_create_clause_embedding"""
    clause_text_hash: str
    embedding_vector: Optional[bytes]
    model_version: str
    cached: bool
    created_at: Optional[datetime] = None


def get_or_create_clause_embedding(
    clause_text: str,
    model_version: str
) -> EmbeddingRecord:
    """
    Get cached embedding or create placeholder for new embedding.

    Phase 5 Step 1: Returns cache lookup result only.
    Actual embedding generation happens in Step 2 when SAE is activated.

    Args:
        clause_text: Clause text to get/create embedding for
        model_version: Model version string (e.g., "text-embedding-3-small")

    Returns:
        EmbeddingRecord with cached embedding or None if not cached

    Note: This function does NOT generate embeddings in Step 1.
          It only checks the cache and returns what's there.
    """
    cache = get_embedding_cache()
    clause_hash = cache.compute_hash(clause_text)

    # Try to get from cache
    cached_vector = cache.get(clause_text)

    if cached_vector is not None:
        return EmbeddingRecord(
            clause_text_hash=clause_hash,
            embedding_vector=cached_vector,
            model_version=model_version,
            cached=True,
            created_at=datetime.now(),  # Approximation
        )
    else:
        # Cache miss - return empty record
        # Actual embedding generation will be added in Step 2
        return EmbeddingRecord(
            clause_text_hash=clause_hash,
            embedding_vector=None,
            model_version=model_version,
            cached=False,
            created_at=None,
        )


# ============================================================================
# STEP 2: SAE INTELLIGENCE HELPERS
# ============================================================================

# Semantic truncation boundary markers (don't cut mid-sentence)
SENTENCE_BOUNDARIES = ['. ', '.\n', '? ', '?\n', '! ', '!\n', '; ', ';\n']
CLAUSE_BOUNDARIES = ['\n\n', '\n(', '\n•', '\n-', '\n*']


def truncate_for_embedding(
    text: str,
    max_tokens: int = 512,
    chars_per_token: float = 4.0
) -> str:
    """
    Truncate text for embedding with semantic safety.

    Avoids cutting mid-sentence or mid-clause where possible.
    Uses ~4 chars per token approximation for text-embedding-3-large.

    Args:
        text: Raw clause text
        max_tokens: Maximum tokens (default 512)
        chars_per_token: Chars per token estimate (default 4.0)

    Returns:
        Truncated text preserving semantic boundaries
    """
    if not text:
        return ""

    max_chars = int(max_tokens * chars_per_token)

    # If already under limit, return as-is
    if len(text) <= max_chars:
        return text.strip()

    # Try to find a semantic boundary before the hard limit
    candidate = text[:max_chars]

    # First try clause boundaries (stronger)
    best_boundary = -1
    for boundary in CLAUSE_BOUNDARIES:
        idx = candidate.rfind(boundary)
        if idx > best_boundary and idx > max_chars * 0.5:  # At least 50% of content
            best_boundary = idx

    if best_boundary > 0:
        return text[:best_boundary].strip()

    # Fall back to sentence boundaries
    for boundary in SENTENCE_BOUNDARIES:
        idx = candidate.rfind(boundary)
        if idx > best_boundary and idx > max_chars * 0.5:
            best_boundary = idx + len(boundary) - 1  # Include the period

    if best_boundary > 0:
        return text[:best_boundary].strip()

    # Last resort: hard cut at max_chars
    return text[:max_chars].strip()


def vectors_to_bytes(vector: list) -> bytes:
    """
    Convert embedding vector (list of floats) to bytes for storage.

    Args:
        vector: List of float values

    Returns:
        Bytes representation (JSON encoded)
    """
    import json
    return json.dumps(vector).encode('utf-8')


def bytes_to_vector(data: bytes) -> Optional[list]:
    """
    Convert bytes back to embedding vector.

    Args:
        data: Bytes from cache storage

    Returns:
        List of floats or None on error
    """
    import json
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def compute_cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Compute cosine similarity between two embedding vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    if not vec1 or not vec2:
        return 0.0

    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


@dataclass
class SAEEmbeddingResult:
    """Result from SAE embedding operation"""
    clause_hash: str
    vector: Optional[list]
    model_version: str
    dimensions: int
    cached: bool
    error: Optional[str] = None


def get_sae_embedding(
    clause_text: str,
    openai_client: Any,
    model: str = "text-embedding-3-large",
    max_tokens: int = 512
) -> SAEEmbeddingResult:
    """
    Get embedding for clause text with Phase 5 cache integration.

    Respects sae_intelligence_active flag.
    When flag is False, returns placeholder result.
    When flag is True, uses cache + API with error fallback.

    Args:
        clause_text: Clause text to embed
        openai_client: OpenAI client instance
        model: Embedding model name
        max_tokens: Max tokens for truncation

    Returns:
        SAEEmbeddingResult with vector or error
    """
    cache = get_embedding_cache()

    # Truncate with semantic safety
    truncated = truncate_for_embedding(clause_text, max_tokens)
    clause_hash = cache.compute_hash(truncated)

    # Check feature flag
    if not is_flag_enabled("sae_intelligence_active"):
        # Flag disabled - return empty result (placeholder behavior)
        return SAEEmbeddingResult(
            clause_hash=clause_hash,
            vector=None,
            model_version=model,
            dimensions=0,
            cached=False,
            error="sae_intelligence_active flag is False"
        )

    # Try cache first
    cached_bytes = cache.get(truncated)
    if cached_bytes is not None:
        vector = bytes_to_vector(cached_bytes)
        if vector:
            return SAEEmbeddingResult(
                clause_hash=clause_hash,
                vector=vector,
                model_version=model,
                dimensions=len(vector),
                cached=True
            )

    # Cache miss - call OpenAI API
    if openai_client is None:
        return SAEEmbeddingResult(
            clause_hash=clause_hash,
            vector=None,
            model_version=model,
            dimensions=0,
            cached=False,
            error="OpenAI client unavailable"
        )

    try:
        response = openai_client.embeddings.create(
            model=model,
            input=truncated
        )
        vector = response.data[0].embedding
        dimensions = len(vector)

        # Store in cache
        cache.put(
            clause_text=truncated,
            embedding_vector=vectors_to_bytes(vector),
            model_version=model,
            vector_dimensions=dimensions
        )

        return SAEEmbeddingResult(
            clause_hash=clause_hash,
            vector=vector,
            model_version=model,
            dimensions=dimensions,
            cached=False
        )

    except Exception as e:
        return SAEEmbeddingResult(
            clause_hash=clause_hash,
            vector=None,
            model_version=model,
            dimensions=0,
            cached=False,
            error=str(e)
        )
