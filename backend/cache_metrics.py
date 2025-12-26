"""
Unified Cache Metrics for Phase 5 Infrastructure
Aggregates metrics from all cache subsystems.

Phase 5 Step 1: Metrics collection infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from phase5_flags import get_phase5_status


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CacheMetricSnapshot:
    """Point-in-time snapshot of cache metrics"""
    timestamp: datetime
    cache_name: str
    hits: int
    misses: int
    writes: int
    evictions: int
    errors: int
    entry_count: int
    size_bytes: int

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cache_name": self.cache_name,
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
            "evictions": self.evictions,
            "errors": self.errors,
            "entry_count": self.entry_count,
            "size_bytes": self.size_bytes,
            "hit_rate": self.hit_rate,
        }


# ============================================================================
# UNIFIED METRICS COLLECTOR
# ============================================================================

class Phase5MetricsCollector:
    """
    Unified metrics collector for all Phase 5 cache subsystems.

    Aggregates metrics from:
    - EmbeddingCache (clause_embeddings)
    - ComparisonSnapshotCache (comparison_snapshots)
    - PatternCache (pattern_library)
    """

    def __init__(self):
        self._history: List[CacheMetricSnapshot] = []
        self._max_history = 1000  # Keep last 1000 snapshots

    def collect_embedding_metrics(self) -> Optional[CacheMetricSnapshot]:
        """Collect metrics from embedding cache"""
        try:
            from embedding_cache import get_embedding_cache
            cache = get_embedding_cache()
            stats = cache.get_stats()

            snapshot = CacheMetricSnapshot(
                timestamp=datetime.now(),
                cache_name="embedding_cache",
                hits=stats.get("metrics", {}).get("hits", 0),
                misses=stats.get("metrics", {}).get("misses", 0),
                writes=stats.get("metrics", {}).get("writes", 0),
                evictions=stats.get("metrics", {}).get("evictions", 0),
                errors=stats.get("metrics", {}).get("errors", 0),
                entry_count=stats.get("entry_count", 0),
                size_bytes=stats.get("total_size_bytes", 0),
            )

            self._add_to_history(snapshot)
            return snapshot

        except ImportError:
            return None

    def collect_snapshot_metrics(self) -> Optional[CacheMetricSnapshot]:
        """Collect metrics from comparison snapshot cache"""
        try:
            from comparison_snapshot_cache import get_snapshot_cache
            cache = get_snapshot_cache()
            stats = cache.get_stats()

            snapshot = CacheMetricSnapshot(
                timestamp=datetime.now(),
                cache_name="snapshot_cache",
                hits=stats.get("metrics", {}).get("hits", 0),
                misses=stats.get("metrics", {}).get("misses", 0),
                writes=stats.get("metrics", {}).get("writes", 0),
                evictions=stats.get("metrics", {}).get("evictions", 0),
                errors=stats.get("metrics", {}).get("errors", 0),
                entry_count=stats.get("entry_count", 0),
                size_bytes=stats.get("total_size_bytes", 0),
            )

            self._add_to_history(snapshot)
            return snapshot

        except ImportError:
            return None

    def collect_pattern_metrics(self) -> Optional[CacheMetricSnapshot]:
        """Collect metrics from pattern cache"""
        try:
            from pattern_cache import get_pattern_cache
            cache = get_pattern_cache()
            stats = cache.get_stats()

            # Pattern cache doesn't have size_bytes, estimate from pattern count
            estimated_size = stats.get("total_patterns", 0) * 500  # ~500 bytes per pattern

            snapshot = CacheMetricSnapshot(
                timestamp=datetime.now(),
                cache_name="pattern_cache",
                hits=stats.get("metrics", {}).get("pattern_matches", 0),
                misses=stats.get("metrics", {}).get("pattern_misses", 0),
                writes=stats.get("metrics", {}).get("cache_writes", 0),
                evictions=0,  # Pattern cache doesn't evict
                errors=stats.get("metrics", {}).get("errors", 0),
                entry_count=stats.get("total_patterns", 0),
                size_bytes=estimated_size,
            )

            self._add_to_history(snapshot)
            return snapshot

        except ImportError:
            return None

    def _add_to_history(self, snapshot: CacheMetricSnapshot) -> None:
        """Add snapshot to history, pruning if needed"""
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect metrics from all cache subsystems.

        Returns:
            Aggregated metrics dictionary
        """
        embedding = self.collect_embedding_metrics()
        snapshot = self.collect_snapshot_metrics()
        pattern = self.collect_pattern_metrics()

        # Aggregate totals
        total_hits = 0
        total_misses = 0
        total_writes = 0
        total_evictions = 0
        total_errors = 0
        total_entries = 0
        total_size = 0

        caches = {}

        if embedding:
            total_hits += embedding.hits
            total_misses += embedding.misses
            total_writes += embedding.writes
            total_evictions += embedding.evictions
            total_errors += embedding.errors
            total_entries += embedding.entry_count
            total_size += embedding.size_bytes
            caches["embedding_cache"] = embedding.to_dict()

        if snapshot:
            total_hits += snapshot.hits
            total_misses += snapshot.misses
            total_writes += snapshot.writes
            total_evictions += snapshot.evictions
            total_errors += snapshot.errors
            total_entries += snapshot.entry_count
            total_size += snapshot.size_bytes
            caches["snapshot_cache"] = snapshot.to_dict()

        if pattern:
            total_hits += pattern.hits
            total_misses += pattern.misses
            total_writes += pattern.writes
            total_evictions += pattern.evictions
            total_errors += pattern.errors
            total_entries += pattern.entry_count
            total_size += pattern.size_bytes
            caches["pattern_cache"] = pattern.to_dict()

        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

        return {
            "collected_at": datetime.now().isoformat(),
            "aggregated": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_writes": total_writes,
                "total_evictions": total_evictions,
                "total_errors": total_errors,
                "total_entries": total_entries,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "overall_hit_rate": overall_hit_rate,
            },
            "caches": caches,
            "phase5_flags": get_phase5_status()["flags"],
        }

    def get_history(
        self,
        cache_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical metrics.

        Args:
            cache_name: Filter by cache name (optional)
            limit: Maximum number of snapshots to return

        Returns:
            List of metric snapshots as dictionaries
        """
        history = self._history

        if cache_name:
            history = [s for s in history if s.cache_name == cache_name]

        # Return most recent first
        return [s.to_dict() for s in history[-limit:][::-1]]

    def reset_all_metrics(self) -> Dict[str, bool]:
        """
        Reset metrics counters in all cache subsystems.

        Returns:
            Status of reset for each cache
        """
        results = {}

        try:
            from embedding_cache import get_embedding_cache
            get_embedding_cache().reset_metrics()
            results["embedding_cache"] = True
        except ImportError:
            results["embedding_cache"] = False

        try:
            from comparison_snapshot_cache import get_snapshot_cache
            get_snapshot_cache().reset_metrics()
            results["snapshot_cache"] = True
        except ImportError:
            results["snapshot_cache"] = False

        try:
            from pattern_cache import get_pattern_cache
            get_pattern_cache().reset_metrics()
            results["pattern_cache"] = True
        except ImportError:
            results["pattern_cache"] = False

        # Clear history
        self._history.clear()
        results["history_cleared"] = True

        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary for monitoring/alerting.

        Returns:
            Dictionary with health indicators
        """
        metrics = self.collect_all()
        agg = metrics.get("aggregated", {})

        # Health thresholds
        error_threshold = 100
        hit_rate_threshold = 0.5

        health_status = "OK"
        issues = []

        if agg.get("total_errors", 0) > error_threshold:
            health_status = "DEGRADED"
            issues.append(f"High error count: {agg['total_errors']}")

        if agg.get("overall_hit_rate", 1.0) < hit_rate_threshold:
            total_requests = agg.get("total_hits", 0) + agg.get("total_misses", 0)
            if total_requests > 100:  # Only flag if enough requests
                health_status = "DEGRADED"
                issues.append(f"Low hit rate: {agg['overall_hit_rate']:.2%}")

        return {
            "status": health_status,
            "issues": issues,
            "metrics_summary": {
                "hit_rate": agg.get("overall_hit_rate", 0.0),
                "total_entries": agg.get("total_entries", 0),
                "total_size_mb": agg.get("total_size_mb", 0.0),
                "total_errors": agg.get("total_errors", 0),
            },
            "checked_at": datetime.now().isoformat(),
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_metrics_collector: Optional[Phase5MetricsCollector] = None


def get_metrics_collector() -> Phase5MetricsCollector:
    """
    Get global metrics collector instance.

    Returns:
        Phase5MetricsCollector singleton
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = Phase5MetricsCollector()
    return _metrics_collector


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def collect_cache_metrics() -> Dict[str, Any]:
    """
    Collect metrics from all Phase 5 caches.

    Returns:
        Aggregated metrics dictionary
    """
    return get_metrics_collector().collect_all()


def get_cache_health() -> Dict[str, Any]:
    """
    Get cache health summary.

    Returns:
        Health status dictionary
    """
    return get_metrics_collector().get_health_summary()


def reset_cache_metrics() -> Dict[str, bool]:
    """
    Reset all cache metrics.

    Returns:
        Reset status for each cache
    """
    return get_metrics_collector().reset_all_metrics()
