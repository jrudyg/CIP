"""
Comparison Snapshot Cache for Phase 5 Compare v3 Pipeline
Stores full comparison results to avoid redundant pipeline runs.

Phase 5 Step 1: Schema and metrics only.
Actual snapshot storage/retrieval activated by comparison_snapshot_active flag.
"""

import hashlib
import json
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
class ComparisonSnapshotRecord:
    """Cached comparison snapshot record"""
    id: int
    v1_hash: str
    v2_hash: str
    comparison_hash: str
    sae_results: Dict[str, Any]
    erce_results: Dict[str, Any]
    birl_results: Dict[str, Any]
    far_results: Dict[str, Any]
    pipeline_meta: Dict[str, Any]
    created_at: datetime
    access_count: int
    last_accessed_at: datetime


# ============================================================================
# COMPARISON SNAPSHOT CACHE CLASS
# ============================================================================

class ComparisonSnapshotCache:
    """
    SQLite-based cache for comparison snapshots.

    Phase 5 Step 1: Schema creation and metrics only.
    Actual snapshot storage/retrieval activated by comparison_snapshot_active flag.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize comparison snapshot cache.

        Args:
            db_path: Path to SQLite database (defaults to data/comparison_snapshots.db)
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "data",
                "comparison_snapshots.db"
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

        # Create comparison_snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparison_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                v1_hash TEXT NOT NULL,
                v2_hash TEXT NOT NULL,
                comparison_hash TEXT UNIQUE NOT NULL,
                sae_results JSON NOT NULL,
                erce_results JSON NOT NULL,
                birl_results JSON NOT NULL,
                far_results JSON NOT NULL,
                pipeline_meta JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)

        # Create index on comparison_hash for O(1) lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comparison_hash
            ON comparison_snapshots(comparison_hash)
        """)

        # Create index on v1_hash and v2_hash for partial lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_v1_hash
            ON comparison_snapshots(v1_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_v2_hash
            ON comparison_snapshots(v2_hash)
        """)

        # Create index on last_accessed_at for LRU eviction
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshot_last_accessed
            ON comparison_snapshots(last_accessed_at)
        """)

        # Create cache_metadata table for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_cache_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initialize metadata
        cursor.execute("""
            INSERT OR IGNORE INTO snapshot_cache_metadata (key, value)
            VALUES ('schema_version', '1.0.0')
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO snapshot_cache_metadata (key, value)
            VALUES ('created_at', ?)
        """, (datetime.now().isoformat(),))

        conn.commit()
        conn.close()

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """
        Compute deterministic hash for contract text.

        Args:
            text: Contract text

        Returns:
            SHA-256 hash hex string
        """
        normalized = text.strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_comparison_hash(v1_hash: str, v2_hash: str) -> str:
        """
        Compute deterministic hash for comparison pair.

        Args:
            v1_hash: Hash of first version
            v2_hash: Hash of second version

        Returns:
            Combined hash for the comparison
        """
        combined = f"{v1_hash}:{v2_hash}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def get(self, v1_text: str, v2_text: str) -> Optional[Dict[str, Any]]:
        """
        Get cached comparison snapshot.

        Args:
            v1_text: First version text
            v2_text: Second version text

        Returns:
            Cached comparison results or None if not cached

        Note: Only returns data if comparison_snapshot_active flag is True.
        """
        # Check feature flag
        if not is_flag_enabled("comparison_snapshot_active"):
            self._metrics["misses"] += 1
            return None

        v1_hash = self.compute_text_hash(v1_text)
        v2_hash = self.compute_text_hash(v2_text)
        comparison_hash = self.compute_comparison_hash(v1_hash, v2_hash)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT sae_results, erce_results, birl_results, far_results, pipeline_meta
                FROM comparison_snapshots
                WHERE comparison_hash = ?
            """, (comparison_hash,))

            row = cursor.fetchone()

            if row:
                # Update access tracking
                cursor.execute("""
                    UPDATE comparison_snapshots
                    SET access_count = access_count + 1,
                        last_accessed_at = CURRENT_TIMESTAMP
                    WHERE comparison_hash = ?
                """, (comparison_hash,))
                conn.commit()

                self._metrics["hits"] += 1
                conn.close()

                return {
                    "sae_results": json.loads(row[0]),
                    "erce_results": json.loads(row[1]),
                    "birl_results": json.loads(row[2]),
                    "far_results": json.loads(row[3]),
                    "pipeline_meta": json.loads(row[4]),
                    "cached": True,
                }
            else:
                self._metrics["misses"] += 1
                conn.close()
                return None

        except (sqlite3.Error, json.JSONDecodeError) as e:
            self._metrics["errors"] += 1
            return None

    def put(
        self,
        v1_text: str,
        v2_text: str,
        sae_results: Dict[str, Any],
        erce_results: Dict[str, Any],
        birl_results: Dict[str, Any],
        far_results: Dict[str, Any],
        pipeline_meta: Dict[str, Any]
    ) -> bool:
        """
        Store comparison snapshot in cache.

        Args:
            v1_text: First version text
            v2_text: Second version text
            sae_results: SAE pipeline results
            erce_results: ERCE pipeline results
            birl_results: BIRL pipeline results
            far_results: FAR pipeline results
            pipeline_meta: Pipeline execution metadata

        Returns:
            True if stored successfully, False otherwise

        Note: Only stores data if comparison_snapshot_active flag is True.
        """
        # Check feature flag
        if not is_flag_enabled("comparison_snapshot_active"):
            return False

        v1_hash = self.compute_text_hash(v1_text)
        v2_hash = self.compute_text_hash(v2_text)
        comparison_hash = self.compute_comparison_hash(v1_hash, v2_hash)

        try:
            # Check max entries limit
            max_entries = get_config("comparison_snapshot_max_entries", 1000)
            if self._get_entry_count() >= max_entries:
                self._evict_lru(count=50)  # Evict oldest 50 entries

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO comparison_snapshots
                (v1_hash, v2_hash, comparison_hash, sae_results, erce_results,
                 birl_results, far_results, pipeline_meta,
                 created_at, last_accessed_at, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """, (
                v1_hash,
                v2_hash,
                comparison_hash,
                json.dumps(sae_results),
                json.dumps(erce_results),
                json.dumps(birl_results),
                json.dumps(far_results),
                json.dumps(pipeline_meta),
            ))

            conn.commit()
            conn.close()

            self._metrics["writes"] += 1
            return True

        except (sqlite3.Error, json.JSONDecodeError) as e:
            self._metrics["errors"] += 1
            return False

    def _get_entry_count(self) -> int:
        """Get current number of cached entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM comparison_snapshots")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except sqlite3.Error:
            return 0

    def _evict_lru(self, count: int = 50) -> int:
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
                DELETE FROM comparison_snapshots
                WHERE id IN (
                    SELECT id FROM comparison_snapshots
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

    def invalidate_by_version(self, version_text: str) -> int:
        """
        Invalidate all snapshots containing a specific version.

        Args:
            version_text: Version text to invalidate

        Returns:
            Number of entries invalidated
        """
        version_hash = self.compute_text_hash(version_text)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM comparison_snapshots
                WHERE v1_hash = ? OR v2_hash = ?
            """, (version_hash, version_hash))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted

        except sqlite3.Error:
            return 0

    def clear(self) -> Dict[str, int]:
        """
        Clear all cached snapshots.

        Returns:
            Statistics about cleared cache
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM comparison_snapshots")
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM comparison_snapshots")
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
            cursor.execute("SELECT COUNT(*) FROM comparison_snapshots")
            entry_count = cursor.fetchone()[0]

            # Total size (approximate via JSON lengths)
            cursor.execute("""
                SELECT SUM(
                    LENGTH(sae_results) + LENGTH(erce_results) +
                    LENGTH(birl_results) + LENGTH(far_results) +
                    LENGTH(pipeline_meta)
                )
                FROM comparison_snapshots
            """)
            total_size = cursor.fetchone()[0] or 0

            # Date range
            cursor.execute("""
                SELECT MIN(created_at), MAX(created_at)
                FROM comparison_snapshots
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
                "oldest_entry": date_range[0] if date_range else None,
                "newest_entry": date_range[1] if date_range else None,
                "metrics": self._metrics.copy(),
                "hit_rate": hit_rate,
                "max_entries": get_config("comparison_snapshot_max_entries", 1000),
                "ttl_hours": get_config("comparison_snapshot_ttl_hours", 720),
                "flag_enabled": is_flag_enabled("comparison_snapshot_active"),
                "db_path": self.db_path,
            }

        except sqlite3.Error as e:
            return {
                "error": str(e),
                "metrics": self._metrics.copy(),
                "flag_enabled": is_flag_enabled("comparison_snapshot_active"),
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

_snapshot_cache: Optional[ComparisonSnapshotCache] = None


def get_snapshot_cache() -> ComparisonSnapshotCache:
    """
    Get global comparison snapshot cache instance.

    Returns:
        ComparisonSnapshotCache singleton
    """
    global _snapshot_cache
    if _snapshot_cache is None:
        _snapshot_cache = ComparisonSnapshotCache()
    return _snapshot_cache


# ============================================================================
# PUBLIC API FUNCTIONS (Step 1 - No call sites yet)
# ============================================================================

@dataclass
class ComparisonSnapshot:
    """Comparison snapshot for store/load operations"""
    id: Optional[int]
    v1_snapshot_id: int
    v2_snapshot_id: int
    sae_results: Dict[str, Any]
    erce_results: Dict[str, Any]
    birl_results: Dict[str, Any]
    far_results: Dict[str, Any]
    pipeline_meta: Dict[str, Any]
    created_at: Optional[datetime] = None


def store_comparison_snapshot(snapshot: ComparisonSnapshot) -> int:
    """
    Store a comparison snapshot in cache.

    Phase 5 Step 1: Function signature only, returns -1 when flag disabled.
    Actual storage happens when comparison_snapshot_active flag is True.

    Args:
        snapshot: ComparisonSnapshot to store

    Returns:
        Snapshot ID if stored, -1 if flag disabled or error
    """
    cache = get_snapshot_cache()

    # Need text to compute hashes - use snapshot IDs as proxy
    # In real usage, caller would provide actual text
    v1_proxy = f"snapshot_{snapshot.v1_snapshot_id}"
    v2_proxy = f"snapshot_{snapshot.v2_snapshot_id}"

    success = cache.put(
        v1_text=v1_proxy,
        v2_text=v2_proxy,
        sae_results=snapshot.sae_results,
        erce_results=snapshot.erce_results,
        birl_results=snapshot.birl_results,
        far_results=snapshot.far_results,
        pipeline_meta=snapshot.pipeline_meta,
    )

    if success:
        # Return a pseudo-ID based on hash
        comparison_hash = cache.compute_comparison_hash(
            cache.compute_text_hash(v1_proxy),
            cache.compute_text_hash(v2_proxy)
        )
        return hash(comparison_hash) % 1000000
    else:
        return -1


def load_comparison_snapshot(snapshot_id: int) -> Optional[ComparisonSnapshot]:
    """
    Load a comparison snapshot from cache by ID.

    Phase 5 Step 1: Function signature only, returns None when flag disabled.
    This is a placeholder - actual ID-based lookup requires schema extension.

    Args:
        snapshot_id: Snapshot ID to load

    Returns:
        ComparisonSnapshot if found, None otherwise

    Note: In Step 1, this always returns None as we don't have ID-based lookup.
          Full implementation requires additional schema work in Step 2+.
    """
    # Step 1: Placeholder implementation
    # Full ID-based lookup requires extending the cache interface
    # For now, return None as the flag is disabled anyway
    if not is_flag_enabled("comparison_snapshot_active"):
        return None

    # TODO Step 2+: Implement actual ID-based lookup
    return None
