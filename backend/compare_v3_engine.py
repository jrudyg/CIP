"""
Compare v3 Engine - Phase 4F Implementation
Real intelligence pipeline for SAE/ERCE/BIRL/FAR.

Phase 4F: Real intelligence with fallback to placeholders.
- SAE: text-embedding-3-large with cosine similarity
- ERCE: Pattern library v1.2 keyword matching
- BIRL: Claude narrative generation
- FAR: Rule-based flowdown gap analysis
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import uuid
import logging
import hashlib
import json
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Phase 5 imports
try:
    from phase5_flags import is_flag_enabled, get_config
    from embedding_cache import (
        get_sae_embedding,
        compute_cosine_similarity,
        truncate_for_embedding,
        SAEEmbeddingResult,
    )
    from pattern_cache import (
        get_erce_patterns,
        match_patterns_for_erce,
        classify_erce_risk,
        ERCEMatchResult,
        RiskPattern,
    )
    PHASE5_AVAILABLE = True
except ImportError:
    PHASE5_AVAILABLE = False
    is_flag_enabled = lambda x: False
    get_config = lambda x, default=None: default

# Import models
from compare_v3_models import (
    ClauseMatch,
    RiskDelta,
    BusinessImpact,
    FlowdownGap,
    ComparisonSnapshot,
    CompareV3Result,
)

# Import config
try:
    from config import CONTRACTS_DB, DATA_PATH
except ImportError:
    CONTRACTS_DB = Path("C:/Users/jrudy/CIP/data/contracts.db")
    DATA_PATH = Path("C:/Users/jrudy/CIP/data")

# Import orchestrator for Claude calls
try:
    from orchestrator import call_claude_safe
    from models import AIResult
except ImportError:
    call_claude_safe = None
    AIResult = None

# OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

# SAE Thresholds
SAE_HIGH_THRESHOLD = 0.90
SAE_MEDIUM_THRESHOLD = 0.75
SAE_LOW_THRESHOLD = 0.60

# Embedding settings
EMBEDDING_MODEL = "text-embedding-3-large"
MAX_EMBEDDING_TOKENS = 512

# Cache settings
EMBEDDING_CACHE_TTL_DAYS = 7

# BIRL settings
BIRL_MAX_TOKENS = 150
BIRL_TEMPERATURE = 0.3

# Pattern library path
PATTERN_LIBRARY_PATH = DATA_PATH / "pattern_library_v1.2.json"


# ============================================================================
# PHASE 5 STEP 7: MONITOR AGENT OBSERVABILITY
# ============================================================================

class MonitorMetrics:
    """
    In-memory metrics collector for orchestrator observability.

    Phase 5 Step 7: Tracks per-stage latency, failures, fallbacks, and cache stats.
    Thread-safe for concurrent requests via per-request isolation.
    """

    def __init__(self, request_id: str):
        self.request_id = request_id
        self.events: List[Dict[str, Any]] = []
        self.stage_latencies: Dict[str, int] = {}
        self.errors: List[Dict[str, Any]] = []
        self.fallback_count: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.stages_skipped: int = 0
        self.total_start_ms: Optional[int] = None
        self.total_end_ms: Optional[int] = None

    def record_event(
        self,
        agent_role: str,
        stage: str,
        event_type: str,
        duration_ms: int = 0,
        payload_ref: Optional[str] = None,
        status_code: str = "OK",
        error_detail: Optional[str] = None
    ) -> None:
        """
        Record a monitor event.

        Args:
            agent_role: sae, erce, birl, far, orchestrator
            stage: SAE, ERCE, BIRL, FAR, ORCH
            event_type: stage_start, stage_end, stage_error
            duration_ms: Stage duration in milliseconds
            payload_ref: Hash or cache_id reference
            status_code: OK, FAIL, PARTIAL
            error_detail: Error message if failed
        """
        event = {
            "agent_role": agent_role,
            "stage": stage,
            "event_type": event_type,
            "request_id": self.request_id,
            "duration_ms": duration_ms,
            "payload_ref": payload_ref,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
        }

        if error_detail:
            event["error_detail"] = error_detail

        self.events.append(event)

        # Log the event
        logger.info(
            f"Monitor event: {event_type} for {stage}",
            extra={
                "monitor_event": True,
                "agent_role": agent_role,
                "stage": stage,
                "event_type": event_type,
                "request_id": self.request_id,
                "duration_ms": duration_ms,
                "status_code": status_code,
            },
        )

    def record_stage_latency(self, stage: str, latency_ms: int) -> None:
        """Record latency for a stage."""
        self.stage_latencies[stage] = latency_ms

    def record_error(self, stage: str, error_key: str, error_detail: str) -> None:
        """Record an error for a stage."""
        self.errors.append({
            "stage": stage,
            "error_key": error_key,
            "error_detail": error_detail,
            "timestamp": datetime.now().isoformat(),
        })

    def record_fallback(self) -> None:
        """Increment fallback counter."""
        self.fallback_count += 1

    def record_cache_hit(self) -> None:
        """Increment cache hit counter."""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Increment cache miss counter."""
        self.cache_misses += 1

    def record_stage_skipped(self) -> None:
        """Increment stages skipped counter."""
        self.stages_skipped += 1

    def to_meta_monitor(self) -> Dict[str, Any]:
        """
        Convert metrics to _meta.monitor output contract.

        Returns:
            Dict matching the required output contract
        """
        return {
            "sae_ms": self.stage_latencies.get("SAE", 0),
            "erce_ms": self.stage_latencies.get("ERCE", 0),
            "birl_ms": self.stage_latencies.get("BIRL", 0),
            "far_ms": self.stage_latencies.get("FAR", 0),
            "total_ms": (self.total_end_ms - self.total_start_ms) if self.total_end_ms and self.total_start_ms else 0,
            "errors": self.errors,
            "fallbacks": self.fallback_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "stages_skipped": self.stages_skipped,
            "events_count": len(self.events),
        }


def monitor_event(
    metrics: MonitorMetrics,
    agent_role: str,
    stage: str,
    event_type: str,
    duration_ms: int = 0,
    payload_ref: Optional[str] = None,
    status_code: str = "OK",
    error_detail: Optional[str] = None
) -> None:
    """
    Unified monitoring envelope for intelligence stages.

    Phase 5 Step 7: Wraps each intelligence stage with observability.

    Args:
        metrics: MonitorMetrics instance for the request
        agent_role: sae, erce, birl, far, orchestrator
        stage: SAE, ERCE, BIRL, FAR, ORCH
        event_type: stage_start, stage_end, stage_error
        duration_ms: Stage duration in milliseconds
        payload_ref: Hash or cache_id reference
        status_code: OK, FAIL, PARTIAL
        error_detail: Error message if failed

    Example:
        monitor_event(
            metrics=metrics,
            agent_role="cip-severity",
            stage="SAE",
            event_type="stage_start",
            request_id=request_id,
            duration_ms=0,
            payload_ref=None,
            status_code="OK"
        )
    """
    metrics.record_event(
        agent_role=agent_role,
        stage=stage,
        event_type=event_type,
        duration_ms=duration_ms,
        payload_ref=payload_ref,
        status_code=status_code,
        error_detail=error_detail
    )


def compute_payload_ref(data: Any) -> str:
    """
    Compute a hash reference for payload data.

    Args:
        data: Data to hash (dict, list, or string)

    Returns:
        Short hash string for reference
    """
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, sort_keys=True, default=str)
    else:
        data_str = str(data)

    return hashlib.sha256(data_str.encode()).hexdigest()[:12]


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get database connection with FK enforcement."""
    conn = sqlite3.connect(str(CONTRACTS_DB))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_embedding_cache_table():
    """Create embedding cache table if not exists."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clause_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                clause_id INTEGER NOT NULL,
                text_hash TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                UNIQUE(contract_id, clause_id, text_hash)
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to create embedding cache table: {e}")
        return False


def get_cached_embedding(contract_id: int, clause_id: int, text_hash: str) -> Optional[List[float]]:
    """Get cached embedding if valid."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT embedding FROM clause_embeddings
            WHERE contract_id = ? AND clause_id = ? AND text_hash = ?
            AND expires_at > ?
        """, (contract_id, clause_id, text_hash, datetime.now().isoformat()))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")
        return None


def cache_embedding(contract_id: int, clause_id: int, text_hash: str, embedding: List[float]):
    """Cache embedding with TTL."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        expires_at = (datetime.now() + timedelta(days=EMBEDDING_CACHE_TTL_DAYS)).isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO clause_embeddings
            (contract_id, clause_id, text_hash, embedding, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (contract_id, clause_id, text_hash, json.dumps(embedding),
              datetime.now().isoformat(), expires_at))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")


# ============================================================================
# SAE: SEMANTIC ALIGNMENT ENGINE (REAL)
# ============================================================================

def _get_openai_client() -> Optional[Any]:
    """Get OpenAI client."""
    if not OPENAI_AVAILABLE:
        return None
    try:
        from dotenv import load_dotenv
        load_dotenv(Path("C:/Users/jrudy/CIP/.env"))
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        return None


def _truncate_text(text: str, max_tokens: int = MAX_EMBEDDING_TOKENS) -> str:
    """Truncate text to approximate token limit (4 chars ~ 1 token)."""
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def _compute_text_hash(text: str) -> str:
    """Compute hash of text for caching."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _get_embedding(client: Any, text: str, contract_id: int, clause_id: int) -> Optional[List[float]]:
    """Get embedding for text, using cache if available."""
    truncated = _truncate_text(text)
    text_hash = _compute_text_hash(truncated)

    # Check cache first
    cached = get_cached_embedding(contract_id, clause_id, text_hash)
    if cached:
        logger.debug(f"Embedding cache hit: contract={contract_id}, clause={clause_id}")
        return cached

    # Call OpenAI
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=truncated
        )
        embedding = response.data[0].embedding

        # Cache it
        cache_embedding(contract_id, clause_id, text_hash, embedding)

        return embedding
    except Exception as e:
        logger.error(f"Embedding API call failed: {e}")
        return None


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def _classify_match_confidence(score: float) -> Tuple[str, float]:
    """Classify match based on similarity score."""
    if score >= SAE_HIGH_THRESHOLD:
        return "HIGH", SAE_HIGH_THRESHOLD
    elif score >= SAE_MEDIUM_THRESHOLD:
        return "MEDIUM", SAE_MEDIUM_THRESHOLD
    elif score >= SAE_LOW_THRESHOLD:
        return "LOW", SAE_LOW_THRESHOLD
    else:
        return None, 0.0  # No match


def run_sae_real(
    v1_clauses: List[Dict[str, Any]],
    v2_clauses: List[Dict[str, Any]],
    v1_contract_id: int,
    v2_contract_id: int,
    request_id: str
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run real SAE with embeddings.

    Phase 5 Step 2: Respects sae_intelligence_active flag.
    - When False: Returns placeholder behavior (legacy)
    - When True: Uses Phase 5 cache + OpenAI API with fallback

    Returns:
        Tuple of (matches, stats)
    """
    stats = {"matched_count": 0, "unmatched_v1": 0, "unmatched_v2": 0, "cache_hits": 0, "cache_misses": 0}

    # Check Phase 5 feature flag
    sae_active = PHASE5_AVAILABLE and is_flag_enabled("sae_intelligence_active")

    if not sae_active:
        # Flag disabled - use placeholder behavior
        logger.info(
            "SAE using placeholder (flag disabled)",
            extra={
                "agent_role": "cip-severity",
                "stage": "SAE",
                "request_id": request_id,
                "sae_active": False,
            },
        )
        return _generate_sae_placeholder(), {"matched_count": 3, "unmatched_v1": 0, "unmatched_v2": 0}

    # Phase 5 SAE with real embeddings
    logger.info(
        "SAE starting with Phase 5 cache + API",
        extra={
            "agent_role": "cip-severity",
            "stage": "SAE",
            "request_id": request_id,
            "sae_active": True,
            "v1_clause_count": len(v1_clauses),
            "v2_clause_count": len(v2_clauses),
        },
    )

    # Get OpenAI client
    client = _get_openai_client()
    if not client:
        logger.warning(
            "SAE OpenAI client unavailable, falling back to placeholder",
            extra={
                "agent_role": "cip-severity",
                "stage": "SAE",
                "request_id": request_id,
            },
        )
        return _generate_sae_placeholder(), {"matched_count": 3, "unmatched_v1": 0, "unmatched_v2": 0}

    # Get embeddings for all clauses using Phase 5 infrastructure
    v1_embeddings = {}
    v2_embeddings = {}

    for clause in v1_clauses:
        clause_id = clause.get('id', 0)
        text = clause.get('text', clause.get('title', ''))
        if text:
            # Use Phase 5 get_sae_embedding with semantic truncation
            result = get_sae_embedding(
                clause_text=text,
                openai_client=client,
                model=EMBEDDING_MODEL,
                max_tokens=MAX_EMBEDDING_TOKENS
            )
            if result.vector:
                v1_embeddings[clause_id] = (result.vector, clause)
                if result.cached:
                    stats["cache_hits"] += 1
                else:
                    stats["cache_misses"] += 1
            elif result.error:
                logger.warning(
                    "SAE embedding failed for v1 clause",
                    extra={
                        "agent_role": "cip-severity",
                        "stage": "SAE",
                        "request_id": request_id,
                        "clause_id": clause_id,
                        "error": result.error,
                    },
                )

    for clause in v2_clauses:
        clause_id = clause.get('id', 0)
        text = clause.get('text', clause.get('title', ''))
        if text:
            result = get_sae_embedding(
                clause_text=text,
                openai_client=client,
                model=EMBEDDING_MODEL,
                max_tokens=MAX_EMBEDDING_TOKENS
            )
            if result.vector:
                v2_embeddings[clause_id] = (result.vector, clause)
                if result.cached:
                    stats["cache_hits"] += 1
                else:
                    stats["cache_misses"] += 1
            elif result.error:
                logger.warning(
                    "SAE embedding failed for v2 clause",
                    extra={
                        "agent_role": "cip-severity",
                        "stage": "SAE",
                        "request_id": request_id,
                        "clause_id": clause_id,
                        "error": result.error,
                    },
                )

    # If no embeddings obtained, fall back to placeholder
    if not v1_embeddings or not v2_embeddings:
        logger.warning(
            "SAE no embeddings obtained, falling back to placeholder",
            extra={
                "agent_role": "cip-severity",
                "stage": "SAE",
                "request_id": request_id,
                "v1_embeddings_count": len(v1_embeddings),
                "v2_embeddings_count": len(v2_embeddings),
            },
        )
        return _generate_sae_placeholder(), {"matched_count": 3, "unmatched_v1": 0, "unmatched_v2": 0}

    # Find best matches using Phase 5 cosine similarity
    matches = []
    matched_v2_ids = set()

    for v1_id, (v1_emb, v1_clause) in v1_embeddings.items():
        best_match = None
        best_score = 0.0
        best_v2_id = None

        for v2_id, (v2_emb, v2_clause) in v2_embeddings.items():
            if v2_id in matched_v2_ids:
                continue

            # Use Phase 5 cosine similarity
            score = compute_cosine_similarity(v1_emb, v2_emb)
            if score > best_score:
                best_score = score
                best_match = v2_clause
                best_v2_id = v2_id

        # Classify match
        confidence, threshold = _classify_match_confidence(best_score)

        if confidence:
            matches.append({
                "v1_clause_id": v1_id,
                "v2_clause_id": best_v2_id,
                "similarity_score": round(best_score, 4),
                "threshold_used": threshold,
                "match_confidence": confidence
            })
            matched_v2_ids.add(best_v2_id)
            stats["matched_count"] += 1
        else:
            stats["unmatched_v1"] += 1

    # Count unmatched V2
    stats["unmatched_v2"] = len(v2_embeddings) - len(matched_v2_ids)

    logger.info(
        "SAE complete",
        extra={
            "agent_role": "cip-severity",
            "stage": "SAE",
            "request_id": request_id,
            "matched_count": stats["matched_count"],
            "unmatched_v1": stats["unmatched_v1"],
            "unmatched_v2": stats["unmatched_v2"],
            "cache_hits": stats["cache_hits"],
            "cache_misses": stats["cache_misses"],
        },
    )
    return matches, stats


def _generate_sae_placeholder() -> List[Dict[str, Any]]:
    """SAE placeholder fallback."""
    return [
        {"v1_clause_id": 1, "v2_clause_id": 1, "similarity_score": 0.95, "threshold_used": 0.90, "match_confidence": "HIGH"},
        {"v1_clause_id": 2, "v2_clause_id": 2, "similarity_score": 0.88, "threshold_used": 0.75, "match_confidence": "MEDIUM"},
        {"v1_clause_id": 3, "v2_clause_id": 4, "similarity_score": 0.72, "threshold_used": 0.60, "match_confidence": "LOW"}
    ]


# ============================================================================
# ERCE: ENTERPRISE RISK CLASSIFICATION ENGINE (REAL)
# ============================================================================

def _load_pattern_library() -> List[Dict[str, Any]]:
    """Load pattern library v1.2 (legacy fallback)."""
    try:
        if PATTERN_LIBRARY_PATH.exists():
            with open(PATTERN_LIBRARY_PATH, 'r') as f:
                data = json.load(f)
                return data.get('patterns', data) if isinstance(data, dict) else data
        else:
            logger.warning(f"Pattern library not found: {PATTERN_LIBRARY_PATH}")
            return []
    except Exception as e:
        logger.error(f"Failed to load pattern library: {e}")
        return []


def _classify_risk_category(matched_patterns: List[Dict], clause_text: str) -> Tuple[str, Optional[str], Optional[float], float]:
    """
    Classify risk based on matched patterns (legacy).

    Returns:
        (risk_category, pattern_ref, success_probability, confidence)
    """
    if not matched_patterns:
        return "ADMIN", None, None, 0.75

    # Find highest severity pattern
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "ADMIN": 1}
    best_pattern = None
    best_severity = 0

    for pattern in matched_patterns:
        cat = pattern.get('category', 'ADMIN').upper()
        sev = severity_order.get(cat, 1)
        if sev > best_severity:
            best_severity = sev
            best_pattern = pattern

    if best_pattern:
        return (
            best_pattern.get('category', 'ADMIN').upper(),
            best_pattern.get('pattern_id'),
            best_pattern.get('success_probability'),
            min(0.95, 0.70 + len(matched_patterns) * 0.05)  # Confidence increases with more matches
        )

    return "ADMIN", None, None, 0.75


def run_erce_real(
    sae_matches: List[Dict[str, Any]],
    v1_clauses: List[Dict[str, Any]],
    v2_clauses: List[Dict[str, Any]],
    request_id: str
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run real ERCE with pattern library.

    Phase 5 Step 3: Respects erce_intelligence_active flag.
    - When False: Returns placeholder behavior (legacy)
    - When True: Uses Phase 5 pattern matching

    Returns:
        Tuple of (results, stats)
    """
    stats = {"risk_count": 0, "high_count": 0, "critical_count": 0, "moderate_count": 0, "admin_count": 0}

    # Check Phase 5 feature flag
    erce_active = PHASE5_AVAILABLE and is_flag_enabled("erce_intelligence_active")

    if not erce_active:
        # Flag disabled - use placeholder behavior
        logger.info(
            "ERCE using placeholder (flag disabled)",
            extra={
                "agent_role": "cip-severity",
                "stage": "ERCE",
                "request_id": request_id,
                "erce_active": False,
            },
        )
        return _generate_erce_placeholder(), {"risk_count": 3, "high_count": 1, "critical_count": 0}

    # Phase 5 ERCE with real pattern matching
    logger.info(
        "ERCE starting with Phase 5 pattern matching",
        extra={
            "agent_role": "cip-severity",
            "stage": "ERCE",
            "request_id": request_id,
            "erce_active": True,
            "sae_matches_count": len(sae_matches),
        },
    )

    # Load patterns via Phase 5 infrastructure
    try:
        patterns = get_erce_patterns()
    except Exception as e:
        logger.error(
            "ERCE pattern load failed, falling back to placeholder",
            extra={
                "agent_role": "cip-severity",
                "stage": "ERCE",
                "request_id": request_id,
                "error": str(e),
            },
        )
        return _generate_erce_placeholder(), {"risk_count": 3, "high_count": 1, "critical_count": 0}

    if not patterns:
        logger.warning(
            "ERCE pattern library empty, falling back to placeholder",
            extra={
                "agent_role": "cip-severity",
                "stage": "ERCE",
                "request_id": request_id,
            },
        )
        return _generate_erce_placeholder(), {"risk_count": 3, "high_count": 1, "critical_count": 0}

    # Build clause lookup
    v1_lookup = {c.get('id'): c for c in v1_clauses}
    v2_lookup = {c.get('id'): c for c in v2_clauses}

    results = []

    for idx, match in enumerate(sae_matches):
        v1_id = match.get('v1_clause_id')
        v2_id = match.get('v2_clause_id')

        v1_clause = v1_lookup.get(v1_id, {})
        v2_clause = v2_lookup.get(v2_id, {})

        # Combine clause text for analysis
        v1_text = v1_clause.get('text', v1_clause.get('title', ''))
        v2_text = v2_clause.get('text', v2_clause.get('title', ''))
        combined_text = f"{v1_text} {v2_text}"

        # Match patterns using Phase 5 infrastructure
        matched_patterns = match_patterns_for_erce(combined_text, patterns)

        # Classify risk
        classification = classify_erce_risk(matched_patterns, combined_text)

        # Build RiskDelta-compatible result (frozen shape)
        results.append({
            "clause_pair_id": idx + 1,
            "risk_category": classification.risk_category,
            "pattern_ref": classification.pattern_id,
            "success_probability": classification.success_probability,
            "confidence": classification.confidence,
        })

        stats["risk_count"] += 1
        if classification.risk_category == "HIGH":
            stats["high_count"] += 1
        elif classification.risk_category == "CRITICAL":
            stats["critical_count"] += 1
        elif classification.risk_category == "MODERATE":
            stats["moderate_count"] += 1
        else:
            stats["admin_count"] += 1

    logger.info(
        "ERCE complete",
        extra={
            "agent_role": "cip-severity",
            "stage": "ERCE",
            "request_id": request_id,
            "risk_count": stats["risk_count"],
            "critical_count": stats["critical_count"],
            "high_count": stats["high_count"],
            "moderate_count": stats["moderate_count"],
            "admin_count": stats["admin_count"],
        },
    )
    return results, stats


def _generate_erce_placeholder() -> List[Dict[str, Any]]:
    """ERCE placeholder fallback."""
    return [
        {"clause_pair_id": 1, "risk_category": "MODERATE", "pattern_ref": None, "success_probability": None, "confidence": 0.85},
        {"clause_pair_id": 2, "risk_category": "HIGH", "pattern_ref": "INDEMNIFICATION_UNLIMITED", "success_probability": 0.65, "confidence": 0.78},
        {"clause_pair_id": 3, "risk_category": "ADMIN", "pattern_ref": None, "success_probability": None, "confidence": 0.92}
    ]


# ============================================================================
# BIRL: BUSINESS IMPACT & RISK LANGUAGE (REAL)
# ============================================================================

BIRL_SYSTEM_PROMPT = """You are a contract analysis expert. Generate a concise business impact narrative for a clause change.

CONSTRAINTS:
- 2-4 sentences maximum
- Focus on business/financial impact
- Do not invent clause numbers or terms not provided
- Do not mention specific dollar amounts unless they appear in the provided text
- Do not mention specific dates unless they appear in the provided text
- Use plain business language
- Do not provide legal advice or recommend legal actions
- Map to dimensions: MARGIN, SCHEDULE, QUALITY, CASH_FLOW, COMPLIANCE, ADMIN

OUTPUT FORMAT:
Narrative: [2-4 sentence impact description]
Dimensions: [comma-separated list of impacted dimensions]"""

# Legal advice phrases to detect and reject
LEGAL_ADVICE_PHRASES = [
    "you should consult",
    "seek legal advice",
    "recommend an attorney",
    "legal counsel",
    "not legal advice",
    "consult with a lawyer",
    "legal professional",
    "this is not advice",
    "disclaimer",
]


def _extract_dimensions(text: str) -> List[str]:
    """Extract impact dimensions from text via keyword scan."""
    text_lower = text.lower()
    dimensions = []

    dimension_keywords = {
        "MARGIN": ["margin", "profit", "cost", "price", "fee", "payment", "revenue"],
        "SCHEDULE": ["timeline", "deadline", "delivery", "schedule", "delay", "time"],
        "QUALITY": ["quality", "standard", "specification", "performance", "defect"],
        "CASH_FLOW": ["cash", "payment term", "net 30", "net 60", "invoice", "receivable"],
        "COMPLIANCE": ["compliance", "regulatory", "law", "regulation", "legal", "audit"],
        "ADMIN": ["administrative", "notice", "amendment", "general"]
    }

    for dim, keywords in dimension_keywords.items():
        if any(kw in text_lower for kw in keywords):
            dimensions.append(dim)

    return dimensions if dimensions else ["ADMIN"]


def _extract_clause_numbers_from_text(text: str) -> set:
    """Extract clause/section numbers mentioned in text."""
    import re
    # Match patterns like: Section 1, Clause 2.3, Article 4, §5
    patterns = [
        r'(?:section|clause|article|§)\s*(\d+(?:\.\d+)*)',
        r'(?:section|clause|article)\s+([a-z])',
    ]
    numbers = set()
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        numbers.update(matches)
    return numbers


def _extract_dollar_amounts_from_text(text: str) -> set:
    """Extract dollar amounts mentioned in text."""
    import re
    # Match patterns like: $100, $1,000, $1.5M, $2 million
    # Use word boundary to avoid partial matches like "$500 m" from "$500 monthly"
    pattern = r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand|M|B|K)\b)?'
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Normalize by stripping whitespace
    return set(m.strip() for m in matches)


def _extract_dates_from_text(text: str) -> set:
    """Extract specific dates mentioned in text."""
    import re
    # Match patterns like: January 1, 2024; 01/01/2024; 2024-01-01
    patterns = [
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
    ]
    dates = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.update(m.lower() for m in matches)
    return dates


def _validate_narrative_hallucination(
    narrative: str,
    input_text: str,
    request_id: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate narrative for hallucinations.

    Phase 5 Step 4: Hallucination shield.

    Checks:
    1. Clause numbers in narrative must exist in input
    2. Dollar amounts in narrative must exist in input
    3. Dates in narrative must exist in input
    4. No legal advice phrases

    Args:
        narrative: Generated narrative text
        input_text: Combined input text (v1 + v2 clauses)
        request_id: For logging

    Returns:
        Tuple of (is_valid, rejection_reason)
    """
    narrative_lower = narrative.lower()

    # Check for legal advice phrases
    for phrase in LEGAL_ADVICE_PHRASES:
        if phrase in narrative_lower:
            return False, f"legal_advice_phrase:{phrase}"

    # Extract entities from input
    input_clause_nums = _extract_clause_numbers_from_text(input_text)
    input_dollars = _extract_dollar_amounts_from_text(input_text)
    input_dates = _extract_dates_from_text(input_text)

    # Extract entities from narrative
    narrative_clause_nums = _extract_clause_numbers_from_text(narrative)
    narrative_dollars = _extract_dollar_amounts_from_text(narrative)
    narrative_dates = _extract_dates_from_text(narrative)

    # Check for hallucinated clause numbers
    hallucinated_clauses = narrative_clause_nums - input_clause_nums
    if hallucinated_clauses:
        return False, f"hallucinated_clause_number:{list(hallucinated_clauses)[0]}"

    # Check for hallucinated dollar amounts
    hallucinated_dollars = narrative_dollars - input_dollars
    if hallucinated_dollars:
        return False, f"hallucinated_dollar_amount:{list(hallucinated_dollars)[0]}"

    # Check for hallucinated dates
    hallucinated_dates = narrative_dates - input_dates
    if hallucinated_dates:
        return False, f"hallucinated_date:{list(hallucinated_dates)[0]}"

    return True, None


def _truncate_to_sentences(text: str, max_sentences: int = 4) -> str:
    """
    Truncate text to maximum number of sentences.

    Args:
        text: Text to truncate
        max_sentences: Maximum sentences to keep (default 4)

    Returns:
        Truncated text
    """
    import re
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text.strip()
    return ' '.join(sentences[:max_sentences])


def _count_sentences(text: str) -> int:
    """Count sentences in text."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return len([s for s in sentences if s.strip()])


def run_birl_real(
    erce_results: List[Dict[str, Any]],
    sae_matches: List[Dict[str, Any]],
    v1_clauses: List[Dict[str, Any]],
    v2_clauses: List[Dict[str, Any]],
    request_id: str
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run real BIRL with Claude.

    Phase 5 Step 4: Respects birl_intelligence_active flag.
    - When False: Returns placeholder behavior (legacy)
    - When True: Uses Claude with hallucination shields

    Returns:
        Tuple of (narratives, stats)
    """
    stats = {
        "narratives_count": 0,
        "failures_count": 0,
        "hallucination_rejections": 0,
        "truncations": 0,
        "low_value_count": 0,
    }

    # Check Phase 5 feature flag
    birl_active = PHASE5_AVAILABLE and is_flag_enabled("birl_intelligence_active")

    if not birl_active:
        # Flag disabled - use placeholder behavior
        logger.info(
            "BIRL using placeholder (flag disabled)",
            extra={
                "agent_role": "cip-reasoning",
                "stage": "BIRL",
                "request_id": request_id,
                "birl_active": False,
            },
        )
        return _generate_birl_placeholder(), {"narratives_count": 3, "failures_count": 0}

    # Phase 5 BIRL with Claude
    logger.info(
        "BIRL starting with Claude narratives",
        extra={
            "agent_role": "cip-reasoning",
            "stage": "BIRL",
            "request_id": request_id,
            "birl_active": True,
            "erce_results_count": len(erce_results),
            "sae_matches_count": len(sae_matches),
        },
    )

    if not call_claude_safe:
        logger.warning(
            "BIRL call_claude_safe unavailable, falling back to placeholder",
            extra={
                "agent_role": "cip-reasoning",
                "stage": "BIRL",
                "request_id": request_id,
            },
        )
        return _generate_birl_placeholder(), {"narratives_count": 3, "failures_count": 0}

    # Get max narratives cap from config
    max_narratives = get_config("birl_max_narratives", 5)

    # Build clause lookup
    v1_lookup = {c.get('id'): c for c in v1_clauses}
    v2_lookup = {c.get('id'): c for c in v2_clauses}

    narratives = []

    # Process up to max_narratives pairs
    pairs_to_process = list(zip(erce_results, sae_matches))[:max_narratives]

    for idx, (erce, sae) in enumerate(pairs_to_process):
        v1_id = sae.get('v1_clause_id')
        v2_id = sae.get('v2_clause_id')

        v1_clause = v1_lookup.get(v1_id, {})
        v2_clause = v2_lookup.get(v2_id, {})

        v1_title = v1_clause.get('title', 'Unknown clause')
        v2_title = v2_clause.get('title', 'Unknown clause')
        v1_text = v1_clause.get('text', '')[:500]  # Limit context
        v2_text = v2_clause.get('text', '')[:500]
        risk_category = erce.get('risk_category', 'ADMIN')

        # Combined input text for hallucination validation
        combined_input = f"{v1_title} {v1_text} {v2_title} {v2_text}"

        # Prepare prompt
        user_message = f"""Analyze this clause change:

V1 Clause: {v1_title}
V1 Text (excerpt): {v1_text}

V2 Clause: {v2_title}
V2 Text (excerpt): {v2_text}

Risk Category: {risk_category}

Provide a 2-4 sentence business impact narrative."""

        # Call Claude
        try:
            result = call_claude_safe(
                payload={
                    'system': BIRL_SYSTEM_PROMPT,
                    'messages': [{'role': 'user', 'content': user_message}],
                    'max_tokens': BIRL_MAX_TOKENS
                },
                purpose="compare",
                contract_id=None
            )

            if result.success:
                response_text = result.data.get('response', '')

                # Parse response
                narrative = response_text.strip()
                if "Narrative:" in narrative:
                    narrative = narrative.split("Narrative:")[-1].split("Dimensions:")[0].strip()

                # Hallucination shield validation
                is_valid, rejection_reason = _validate_narrative_hallucination(
                    narrative, combined_input, request_id
                )

                if not is_valid:
                    logger.warning(
                        "BIRL narrative rejected by hallucination shield",
                        extra={
                            "agent_role": "cip-reasoning",
                            "stage": "BIRL",
                            "request_id": request_id,
                            "clause_pair_id": idx + 1,
                            "rejection_reason": rejection_reason,
                        },
                    )
                    stats["hallucination_rejections"] += 1
                    narratives.append({
                        "clause_pair_id": idx + 1,
                        "narrative": "Impact analysis unavailable.",
                        "impact_dimensions": ["ADMIN"],
                        "token_count": 0
                    })
                    stats["failures_count"] += 1
                    continue

                # Truncate to 4 sentences max
                sentence_count = _count_sentences(narrative)
                if sentence_count > 4:
                    narrative = _truncate_to_sentences(narrative, 4)
                    stats["truncations"] += 1

                # Mark low-value if < 2 sentences
                if sentence_count < 2:
                    stats["low_value_count"] += 1

                # Extract dimensions
                dimensions = _extract_dimensions(f"{v1_text} {v2_text} {narrative}")

                narratives.append({
                    "clause_pair_id": idx + 1,
                    "narrative": narrative[:500],  # Cap length
                    "impact_dimensions": dimensions,
                    "token_count": len(narrative.split())
                })
                stats["narratives_count"] += 1
            else:
                # Fallback on failure
                logger.warning(
                    "BIRL Claude call failed",
                    extra={
                        "agent_role": "cip-reasoning",
                        "stage": "BIRL",
                        "request_id": request_id,
                        "clause_pair_id": idx + 1,
                    },
                )
                narratives.append({
                    "clause_pair_id": idx + 1,
                    "narrative": "Impact analysis unavailable.",
                    "impact_dimensions": ["ADMIN"],
                    "token_count": 0
                })
                stats["failures_count"] += 1

        except Exception as e:
            logger.error(
                "BIRL exception",
                extra={
                    "agent_role": "cip-reasoning",
                    "stage": "BIRL",
                    "request_id": request_id,
                    "clause_pair_id": idx + 1,
                    "error": str(e),
                },
            )
            narratives.append({
                "clause_pair_id": idx + 1,
                "narrative": "Impact analysis unavailable.",
                "impact_dimensions": ["ADMIN"],
                "token_count": 0
            })
            stats["failures_count"] += 1

    logger.info(
        "BIRL complete",
        extra={
            "agent_role": "cip-reasoning",
            "stage": "BIRL",
            "request_id": request_id,
            "narratives_count": stats["narratives_count"],
            "failures_count": stats["failures_count"],
            "hallucination_rejections": stats["hallucination_rejections"],
            "truncations": stats["truncations"],
            "low_value_count": stats["low_value_count"],
        },
    )
    return narratives, stats


def _generate_birl_placeholder() -> List[Dict[str, Any]]:
    """BIRL placeholder fallback."""
    return [
        {"clause_pair_id": 1, "narrative": "No material business impact detected.", "impact_dimensions": ["MARGIN"], "token_count": 12},
        {"clause_pair_id": 2, "narrative": "Payment term extension may impact quarterly cash flow projections.", "impact_dimensions": ["MARGIN", "CASH_FLOW"], "token_count": 24},
        {"clause_pair_id": 3, "narrative": "Administrative clause change with minimal operational impact.", "impact_dimensions": ["ADMIN"], "token_count": 18}
    ]


# ============================================================================
# FAR: FLOWDOWN ANALYSIS & REQUIREMENTS (RULE-BASED)
# ============================================================================

# Flowdown-critical clause categories that require strict compliance
FLOWDOWN_CRITICAL_CATEGORIES = [
    "indemnification",
    "liability",
    "insurance",
    "termination",
    "ip_rights",
    "confidentiality",
    "warranty",
    "compliance",
    "audit",
    "subcontracting",
]

# Keywords indicating mandatory requirements in upstream
UPSTREAM_MANDATORY_KEYWORDS = [
    "shall",
    "must",
    "required",
    "mandatory",
    "will",
    "obligated",
]

# Keywords indicating weakened/optional in downstream
DOWNSTREAM_WEAK_KEYWORDS = [
    "may",
    "optional",
    "reasonable efforts",
    "best efforts",
    "commercially reasonable",
    "endeavor",
    "attempt",
]

# Conflict detection pairs (term1 in v1, term2 in v2 = CONFLICT)
CONFLICT_TERM_PAIRS = [
    ("unlimited", "limited"),
    ("perpetual", "term"),
    ("exclusive", "non-exclusive"),
    ("irrevocable", "revocable"),
    ("worldwide", "territorial"),
    ("unconditional", "conditional"),
]


def _check_contract_relationships(contract_id: int, request_id: str) -> List[Dict[str, Any]]:
    """
    Check if contract has relationships in DB.

    Phase 5 Step 5: Uses agent_role="far" logging.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check parent_id and relationship_type in contracts table
        cursor.execute("""
            SELECT id, parent_id, relationship_type
            FROM contracts
            WHERE id = ? OR parent_id = ?
        """, (contract_id, contract_id))

        rows = cursor.fetchall()
        conn.close()

        relationships = []
        for row in rows:
            if row[1]:  # Has parent
                relationships.append({
                    'contract_id': row[0],
                    'parent_id': row[1],
                    'type': row[2] or 'unknown'
                })

        logger.debug(
            "FAR relationship check",
            extra={
                "agent_role": "far",
                "request_id": request_id,
                "contract_id": contract_id,
                "relationships_found": len(relationships),
            },
        )
        return relationships
    except Exception as e:
        logger.warning(
            "FAR relationship check failed",
            extra={
                "agent_role": "far",
                "request_id": request_id,
                "contract_id": contract_id,
                "error": str(e),
            },
        )
        return []


def _classify_gap(v1_text: str, v2_text: str, section: str, request_id: str) -> Tuple[str, str, str]:
    """
    Classify gap type and severity based on flowdown rules.

    Phase 5 Step 5: Enhanced rule-based classification.

    Gap Types:
    - MISSING: Present in upstream, absent in downstream
    - WEAKER: Downstream weakens mandatory upstream requirement
    - CONFLICT: Direct contradiction between versions

    Returns:
        (gap_type, severity, recommendation)
    """
    v1_lower = v1_text.lower() if v1_text else ""
    v2_lower = v2_text.lower() if v2_text else ""

    # MISSING: present in upstream, absent in downstream
    if v1_lower and not v2_lower:
        return "MISSING", "HIGH", f"Section {section} is required in upstream but missing downstream. Add equivalent clause."

    # CONFLICT: directly contradictory terms
    for term1, term2 in CONFLICT_TERM_PAIRS:
        if term1 in v1_lower and term2 in v2_lower:
            return "CONFLICT", "CRITICAL", f"Section {section} has conflicting terms: upstream uses '{term1}' but downstream uses '{term2}'. Align terminology."
        if term2 in v1_lower and term1 in v2_lower:
            return "CONFLICT", "CRITICAL", f"Section {section} has conflicting terms: upstream uses '{term2}' but downstream uses '{term1}'. Align terminology."

    # WEAKER: downstream weakens upstream requirement
    v1_mandatory = any(kw in v1_lower for kw in UPSTREAM_MANDATORY_KEYWORDS)
    v2_weakened = any(kw in v2_lower for kw in DOWNSTREAM_WEAK_KEYWORDS)

    if v1_mandatory and v2_weakened:
        return "WEAKER", "MODERATE", f"Section {section} uses weaker language downstream. Consider strengthening to match upstream obligations."

    # Check for critical category with missing mandatory language
    section_lower = section.lower()
    is_critical_category = any(cat in section_lower or cat in v1_lower for cat in FLOWDOWN_CRITICAL_CATEGORIES)

    if is_critical_category and v1_mandatory and not v2_weakened:
        # Check if downstream also has mandatory language
        v2_mandatory = any(kw in v2_lower for kw in UPSTREAM_MANDATORY_KEYWORDS)
        if not v2_mandatory:
            return "WEAKER", "HIGH", f"Section {section} is a critical flowdown category but downstream lacks mandatory language."

    return "ALIGNED", "ADMIN", ""


def _extract_clause_category(clause: Dict[str, Any]) -> str:
    """Extract category from clause for flowdown analysis."""
    title_lower = clause.get('title', '').lower()
    text_lower = clause.get('text', '')[:500].lower()
    category = clause.get('category', '').lower()

    # Check explicit category first
    if category:
        return category

    # Infer from title/text
    for cat in FLOWDOWN_CRITICAL_CATEGORIES:
        if cat in title_lower or cat in text_lower:
            return cat

    return "general"


def run_far_real(
    v1_contract_id: int,
    v2_contract_id: int,
    v1_clauses: List[Dict[str, Any]],
    v2_clauses: List[Dict[str, Any]],
    request_id: str
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run real FAR with rule-based flowdown logic.

    Phase 5 Step 5: Respects far_intelligence_active flag.
    - When False: Returns empty (placeholder behavior)
    - When True: Rule-based flowdown gap analysis

    Gap Types Detected:
    - MISSING: Upstream clause not present in downstream
    - WEAKER: Downstream weakens mandatory upstream requirement
    - CONFLICT: Direct contradiction between upstream/downstream terms

    Note: FAR is NOT used for TRUST per frozen spec.

    Returns:
        Tuple of (gaps, stats)
    """
    stats = {
        "gaps_count": 0,
        "critical_count": 0,
        "high_count": 0,
        "moderate_count": 0,
        "missing_count": 0,
        "weaker_count": 0,
        "conflict_count": 0,
        "clauses_analyzed": 0,
    }

    # Check Phase 5 feature flag
    far_active = PHASE5_AVAILABLE and is_flag_enabled("far_intelligence_active")

    if not far_active:
        # Flag disabled - use placeholder behavior
        logger.info(
            "FAR using placeholder (flag disabled)",
            extra={
                "agent_role": "far",
                "request_id": request_id,
                "far_active": False,
            },
        )
        return _generate_far_placeholder(), {"gaps_count": 0, "critical_count": 0, "high_count": 0}

    # Phase 5 FAR with rule-based analysis
    logger.info(
        "FAR starting with rule-based flowdown analysis",
        extra={
            "agent_role": "far",
            "request_id": request_id,
            "far_active": True,
            "v1_clause_count": len(v1_clauses),
            "v2_clause_count": len(v2_clauses),
        },
    )

    # Check if relationships exist (for context, not required)
    v1_rels = _check_contract_relationships(v1_contract_id, request_id)
    v2_rels = _check_contract_relationships(v2_contract_id, request_id)

    has_relationships = bool(v1_rels or v2_rels)

    if not has_relationships:
        logger.info(
            "FAR no parent/child relationships found, analyzing as standalone comparison",
            extra={
                "agent_role": "far",
                "request_id": request_id,
            },
        )

    gaps = []

    # Build clause lookup by section number for comparison
    v1_by_section = {}
    for c in v1_clauses:
        section = c.get('section_number', '')
        if section:
            v1_by_section[section] = c

    v2_by_section = {}
    for c in v2_clauses:
        section = c.get('section_number', '')
        if section:
            v2_by_section[section] = c

    # Analyze each upstream clause for flowdown compliance
    for section, v1_clause in v1_by_section.items():
        v2_clause = v2_by_section.get(section)
        stats["clauses_analyzed"] += 1

        v1_text = v1_clause.get('text', '')
        v1_title = v1_clause.get('title', section)
        v1_category = _extract_clause_category(v1_clause)

        if not v2_clause:
            # MISSING: clause exists in upstream but not downstream
            # Only flag as gap if it's a critical category or has mandatory language
            is_critical = v1_category in FLOWDOWN_CRITICAL_CATEGORIES
            has_mandatory = any(kw in v1_text.lower() for kw in UPSTREAM_MANDATORY_KEYWORDS)

            if is_critical or has_mandatory:
                gap = {
                    "gap_type": "MISSING",
                    "severity": "HIGH" if is_critical else "MODERATE",
                    "upstream_clause": v1_title,
                    "upstream_section": section,
                    "downstream_clause": None,
                    "downstream_section": None,
                    "category": v1_category,
                    "recommendation": f"Add clause {section} ({v1_title}) to downstream contract. This is a {'critical flowdown requirement' if is_critical else 'mandatory upstream clause'}."
                }
                gaps.append(gap)
                stats["gaps_count"] += 1
                stats["missing_count"] += 1
                if gap["severity"] == "HIGH":
                    stats["high_count"] += 1
                else:
                    stats["moderate_count"] += 1

                logger.debug(
                    "FAR gap detected: MISSING",
                    extra={
                        "agent_role": "far",
                        "request_id": request_id,
                        "section": section,
                        "category": v1_category,
                        "severity": gap["severity"],
                    },
                )
        else:
            # Compare content
            v2_text = v2_clause.get('text', '')
            v2_title = v2_clause.get('title', section)

            gap_type, severity, recommendation = _classify_gap(v1_text, v2_text, section, request_id)

            if gap_type != "ALIGNED":
                gap = {
                    "gap_type": gap_type,
                    "severity": severity,
                    "upstream_clause": v1_title,
                    "upstream_section": section,
                    "downstream_clause": v2_title,
                    "downstream_section": section,
                    "category": v1_category,
                    "recommendation": recommendation
                }
                gaps.append(gap)
                stats["gaps_count"] += 1

                if gap_type == "CONFLICT":
                    stats["conflict_count"] += 1
                elif gap_type == "WEAKER":
                    stats["weaker_count"] += 1
                elif gap_type == "MISSING":
                    stats["missing_count"] += 1

                if severity == "CRITICAL":
                    stats["critical_count"] += 1
                elif severity == "HIGH":
                    stats["high_count"] += 1
                else:
                    stats["moderate_count"] += 1

                logger.debug(
                    f"FAR gap detected: {gap_type}",
                    extra={
                        "agent_role": "far",
                        "request_id": request_id,
                        "section": section,
                        "gap_type": gap_type,
                        "severity": severity,
                    },
                )

    logger.info(
        "FAR complete",
        extra={
            "agent_role": "far",
            "request_id": request_id,
            "gaps_count": stats["gaps_count"],
            "critical_count": stats["critical_count"],
            "high_count": stats["high_count"],
            "moderate_count": stats["moderate_count"],
            "missing_count": stats["missing_count"],
            "weaker_count": stats["weaker_count"],
            "conflict_count": stats["conflict_count"],
            "clauses_analyzed": stats["clauses_analyzed"],
        },
    )
    return gaps, stats


def _generate_far_placeholder() -> List[Dict[str, Any]]:
    """FAR placeholder fallback."""
    return []


# ============================================================================
# CLAUSE RETRIEVAL HELPER
# ============================================================================

def get_clauses_for_contract(contract_id: int) -> List[Dict[str, Any]]:
    """Retrieve clauses for a contract from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, contract_id, section_number, title, text, category, risk_level, pattern_id
            FROM clauses
            WHERE contract_id = ?
            ORDER BY section_number
        """, (contract_id,))

        rows = cursor.fetchall()
        conn.close()

        clauses = []
        for row in rows:
            clauses.append({
                'id': row[0],
                'contract_id': row[1],
                'section_number': row[2],
                'title': row[3],
                'text': row[4],
                'category': row[5],
                'risk_level': row[6],
                'pattern_id': row[7]
            })

        return clauses
    except Exception as e:
        logger.error(f"Failed to get clauses for contract {contract_id}: {e}")
        return []


# ============================================================================
# COMPARE V3 ORCHESTRATOR (PHASE 5 STEP 6)
# ============================================================================

# Stage timeout configuration (seconds)
ORCHESTRATOR_TIMEOUTS = {
    "global": 120,  # Global hard timeout
    "SAE": 60,      # Semantic alignment
    "ERCE": 30,     # Risk classification
    "BIRL": 45,     # Business impact narratives
    "FAR": 15,      # Flowdown analysis
}

# Agent role mapping per stage
STAGE_AGENT_ROLES = {
    "SAE": "cip-severity",
    "ERCE": "cip-severity",
    "BIRL": "cip-reasoning",
    "FAR": "far",
}


def _execute_stage_with_timeout(
    stage_name: str,
    stage_func: callable,
    stage_args: tuple,
    timeout_seconds: int,
    request_id: str
) -> Tuple[Any, Dict[str, Any], str, Optional[str]]:
    """
    Execute a pipeline stage with timeout and error handling.

    Args:
        stage_name: Name of the stage (SAE, ERCE, BIRL, FAR)
        stage_func: Function to execute
        stage_args: Arguments for the function
        timeout_seconds: Timeout in seconds
        request_id: Request ID for logging

    Returns:
        Tuple of (result, stats, status, error_key)
        - result: Stage output or placeholder
        - stats: Stage statistics
        - status: "success" or "failure"
        - error_key: Error key if failed, None otherwise
    """
    import time
    import concurrent.futures

    agent_role = STAGE_AGENT_ROLES.get(stage_name, "unknown")
    start_time = time.time()

    try:
        # Execute with timeout using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(stage_func, *stage_args)
            try:
                result, stats = future.result(timeout=timeout_seconds)
                duration_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    f"Orchestrator stage complete: {stage_name}",
                    extra={
                        "request_id": request_id,
                        "orchestrator_stage": stage_name,
                        "agent_role": agent_role,
                        "duration_ms": duration_ms,
                        "status": "success",
                        "error_key": None,
                    },
                )

                return result, stats, "success", None

            except concurrent.futures.TimeoutError:
                duration_ms = int((time.time() - start_time) * 1000)
                error_key = f"{stage_name.lower()}.timeout"

                logger.warning(
                    f"Orchestrator stage timeout: {stage_name}",
                    extra={
                        "request_id": request_id,
                        "orchestrator_stage": stage_name,
                        "agent_role": agent_role,
                        "duration_ms": duration_ms,
                        "status": "failure",
                        "error_key": error_key,
                        "timeout_seconds": timeout_seconds,
                    },
                )

                return None, {}, "failure", error_key

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_key = f"{stage_name.lower()}.exception"

        logger.error(
            f"Orchestrator stage exception: {stage_name}",
            extra={
                "request_id": request_id,
                "orchestrator_stage": stage_name,
                "agent_role": agent_role,
                "duration_ms": duration_ms,
                "status": "failure",
                "error_key": error_key,
                "error_detail": str(e),
            },
        )

        return None, {}, "failure", error_key


def run_compare_v3_orchestrator(
    v1_text: str,
    v2_text: str,
    v1_contract_id: Optional[int] = None,
    v2_contract_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Phase 5 Step 6+7: Unified Compare v3 Orchestrator with Observability.

    Executes SAE → ERCE → BIRL → FAR in sequence with:
    - Per-stage timeout thresholds
    - Per-stage duration tracking in _meta.stats
    - Graceful degradation (no cascade failures)
    - Unified logging with orchestrator_stage, agent_role, duration_ms
    - Phase 5 Step 7: Full observability via _meta.monitor

    Feature Flags Respected:
    - sae_intelligence_active
    - erce_intelligence_active
    - birl_intelligence_active
    - far_intelligence_active

    Args:
        v1_text: First contract version text
        v2_text: Second contract version text
        v1_contract_id: Optional contract ID for v1
        v2_contract_id: Optional contract ID for v2

    Returns:
        Dict with all pipeline outputs, _meta, and _meta.monitor
    """
    import time

    request_id = str(uuid.uuid4())
    orchestrator_start = time.time()
    orchestrator_start_ms = int(orchestrator_start * 1000)

    # Phase 5 Step 7: Initialize monitor metrics
    metrics = MonitorMetrics(request_id)
    metrics.total_start_ms = orchestrator_start_ms

    # Track stage statuses for _meta.pipeline_status
    stage_statuses = {}
    stage_durations = {}
    pipeline_errors = []

    # Monitor: ORCH stage_start
    monitor_event(
        metrics=metrics,
        agent_role="orchestrator",
        stage="ORCH",
        event_type="stage_start",
        duration_ms=0,
        status_code="OK"
    )

    logger.info(
        "Orchestrator starting pipeline",
        extra={
            "request_id": request_id,
            "orchestrator_stage": "INIT",
            "agent_role": "orchestrator",
            "duration_ms": 0,
            "status": "success",
            "error_key": None,
            "v1_contract_id": v1_contract_id,
            "v2_contract_id": v2_contract_id,
        },
    )

    # =========================================================================
    # CLAUSE RETRIEVAL
    # =========================================================================
    v1_clauses = []
    v2_clauses = []

    if v1_contract_id:
        v1_clauses = get_clauses_for_contract(v1_contract_id)
    if v2_contract_id:
        v2_clauses = get_clauses_for_contract(v2_contract_id)

    # If no clauses from DB, create synthetic clauses from text
    if not v1_clauses and v1_text:
        v1_clauses = [{'id': 1, 'text': v1_text[:2000], 'title': 'Full Contract', 'section_number': '1'}]
    if not v2_clauses and v2_text:
        v2_clauses = [{'id': 1, 'text': v2_text[:2000], 'title': 'Full Contract', 'section_number': '1'}]

    # =========================================================================
    # STAGE 1: SAE - Semantic Alignment Engine
    # =========================================================================
    # Monitor: SAE stage_start
    monitor_event(
        metrics=metrics,
        agent_role="cip-severity",
        stage="SAE",
        event_type="stage_start",
        status_code="OK"
    )

    sae_start = time.time()
    sae_result, sae_stats, sae_status, sae_error = _execute_stage_with_timeout(
        stage_name="SAE",
        stage_func=run_sae_real,
        stage_args=(v1_clauses, v2_clauses, v1_contract_id or 0, v2_contract_id or 0, request_id),
        timeout_seconds=ORCHESTRATOR_TIMEOUTS["SAE"],
        request_id=request_id
    )

    sae_duration_ms = int((time.time() - sae_start) * 1000)
    stage_durations["SAE"] = sae_duration_ms
    stage_statuses["SAE"] = sae_status
    metrics.record_stage_latency("SAE", sae_duration_ms)

    if sae_status == "failure":
        sae_matches = _generate_sae_placeholder()
        sae_stats = {"matched_count": 3, "unmatched_v1": 0, "unmatched_v2": 0, "status": "PLACEHOLDER"}
        pipeline_errors.append("SAE")
        metrics.record_fallback()
        metrics.record_error("SAE", sae_error or "sae.unknown", "Stage failed")
        # Monitor: SAE stage_error
        monitor_event(
            metrics=metrics,
            agent_role="cip-severity",
            stage="SAE",
            event_type="stage_error",
            duration_ms=sae_duration_ms,
            status_code="FAIL",
            error_detail=sae_error
        )
    else:
        sae_matches = sae_result
        sae_stats["status"] = "REAL"
        # Track cache hits/misses from SAE stats
        if sae_stats.get("cache_hits"):
            for _ in range(sae_stats["cache_hits"]):
                metrics.record_cache_hit()
        if sae_stats.get("cache_misses"):
            for _ in range(sae_stats["cache_misses"]):
                metrics.record_cache_miss()
        # Monitor: SAE stage_end
        payload_ref = compute_payload_ref(sae_matches)
        monitor_event(
            metrics=metrics,
            agent_role="cip-severity",
            stage="SAE",
            event_type="stage_end",
            duration_ms=sae_duration_ms,
            payload_ref=payload_ref,
            status_code="OK"
        )

    # =========================================================================
    # STAGE 2: ERCE - Enterprise Risk Classification Engine
    # =========================================================================
    # Monitor: ERCE stage_start
    monitor_event(
        metrics=metrics,
        agent_role="cip-severity",
        stage="ERCE",
        event_type="stage_start",
        status_code="OK"
    )

    erce_start = time.time()
    erce_result, erce_stats, erce_status, erce_error = _execute_stage_with_timeout(
        stage_name="ERCE",
        stage_func=run_erce_real,
        stage_args=(sae_matches, v1_clauses, v2_clauses, request_id),
        timeout_seconds=ORCHESTRATOR_TIMEOUTS["ERCE"],
        request_id=request_id
    )

    erce_duration_ms = int((time.time() - erce_start) * 1000)
    stage_durations["ERCE"] = erce_duration_ms
    stage_statuses["ERCE"] = erce_status
    metrics.record_stage_latency("ERCE", erce_duration_ms)

    if erce_status == "failure":
        erce_results = _generate_erce_placeholder()
        erce_stats = {"risk_count": 3, "high_count": 1, "critical_count": 0, "status": "PLACEHOLDER"}
        pipeline_errors.append("ERCE")
        metrics.record_fallback()
        metrics.record_error("ERCE", erce_error or "erce.unknown", "Stage failed")
        # Monitor: ERCE stage_error
        monitor_event(
            metrics=metrics,
            agent_role="cip-severity",
            stage="ERCE",
            event_type="stage_error",
            duration_ms=erce_duration_ms,
            status_code="FAIL",
            error_detail=erce_error
        )
    else:
        erce_results = erce_result
        erce_stats["status"] = "REAL"
        # Monitor: ERCE stage_end
        payload_ref = compute_payload_ref(erce_results)
        monitor_event(
            metrics=metrics,
            agent_role="cip-severity",
            stage="ERCE",
            event_type="stage_end",
            duration_ms=erce_duration_ms,
            payload_ref=payload_ref,
            status_code="OK"
        )

    # =========================================================================
    # STAGE 3: BIRL - Business Impact & Risk Language
    # =========================================================================
    # Monitor: BIRL stage_start
    monitor_event(
        metrics=metrics,
        agent_role="cip-reasoning",
        stage="BIRL",
        event_type="stage_start",
        status_code="OK"
    )

    birl_start = time.time()
    birl_result, birl_stats, birl_status, birl_error = _execute_stage_with_timeout(
        stage_name="BIRL",
        stage_func=run_birl_real,
        stage_args=(erce_results, sae_matches, v1_clauses, v2_clauses, request_id),
        timeout_seconds=ORCHESTRATOR_TIMEOUTS["BIRL"],
        request_id=request_id
    )

    birl_duration_ms = int((time.time() - birl_start) * 1000)
    stage_durations["BIRL"] = birl_duration_ms
    stage_statuses["BIRL"] = birl_status
    metrics.record_stage_latency("BIRL", birl_duration_ms)

    if birl_status == "failure":
        birl_narratives = _generate_birl_placeholder()
        birl_stats = {"narratives_count": 3, "failures_count": 0, "status": "PLACEHOLDER"}
        pipeline_errors.append("BIRL")
        metrics.record_fallback()
        metrics.record_error("BIRL", birl_error or "birl.unknown", "Stage failed")
        # Monitor: BIRL stage_error
        monitor_event(
            metrics=metrics,
            agent_role="cip-reasoning",
            stage="BIRL",
            event_type="stage_error",
            duration_ms=birl_duration_ms,
            status_code="FAIL",
            error_detail=birl_error
        )
    else:
        birl_narratives = birl_result
        birl_stats["status"] = "REAL"
        # Monitor: BIRL stage_end
        payload_ref = compute_payload_ref(birl_narratives)
        monitor_event(
            metrics=metrics,
            agent_role="cip-reasoning",
            stage="BIRL",
            event_type="stage_end",
            duration_ms=birl_duration_ms,
            payload_ref=payload_ref,
            status_code="OK"
        )

    # =========================================================================
    # STAGE 4: FAR - Flowdown Analysis & Requirements
    # =========================================================================
    # Monitor: FAR stage_start
    monitor_event(
        metrics=metrics,
        agent_role="far",
        stage="FAR",
        event_type="stage_start",
        status_code="OK"
    )

    far_start = time.time()
    far_result, far_stats, far_status, far_error = _execute_stage_with_timeout(
        stage_name="FAR",
        stage_func=run_far_real,
        stage_args=(v1_contract_id or 0, v2_contract_id or 0, v1_clauses, v2_clauses, request_id),
        timeout_seconds=ORCHESTRATOR_TIMEOUTS["FAR"],
        request_id=request_id
    )

    far_duration_ms = int((time.time() - far_start) * 1000)
    stage_durations["FAR"] = far_duration_ms
    stage_statuses["FAR"] = far_status
    metrics.record_stage_latency("FAR", far_duration_ms)

    if far_status == "failure":
        flowdown_gaps = _generate_far_placeholder()
        far_stats = {"gaps_count": 0, "critical_count": 0, "high_count": 0, "status": "PLACEHOLDER"}
        pipeline_errors.append("FAR")
        metrics.record_fallback()
        metrics.record_error("FAR", far_error or "far.unknown", "Stage failed")
        # Monitor: FAR stage_error
        monitor_event(
            metrics=metrics,
            agent_role="far",
            stage="FAR",
            event_type="stage_error",
            duration_ms=far_duration_ms,
            status_code="FAIL",
            error_detail=far_error
        )
    else:
        flowdown_gaps = far_result
        far_stats["status"] = "REAL"
        # Monitor: FAR stage_end
        payload_ref = compute_payload_ref(flowdown_gaps)
        monitor_event(
            metrics=metrics,
            agent_role="far",
            stage="FAR",
            event_type="stage_end",
            duration_ms=far_duration_ms,
            payload_ref=payload_ref,
            status_code="OK"
        )

    # =========================================================================
    # BUILD UNIFIED RESULT
    # =========================================================================
    total_duration_ms = int((time.time() - orchestrator_start) * 1000)
    metrics.total_end_ms = int(time.time() * 1000)

    # Record stages skipped (those that used fallback due to flag being off, not error)
    # This is distinct from failures - it's when flag is OFF
    for stage in ["SAE", "ERCE", "BIRL", "FAR"]:
        flag_name = f"{stage.lower()}_intelligence_active"
        if not is_flag_enabled(flag_name) and stage not in pipeline_errors:
            metrics.record_stage_skipped()

    # Determine overall pipeline status
    if not pipeline_errors:
        pipeline_status = "REAL"
        orch_status_code = "OK"
    elif len(pipeline_errors) == 4:
        pipeline_status = "PLACEHOLDER"
        orch_status_code = "PARTIAL"
    else:
        pipeline_status = f"PARTIAL:{','.join(pipeline_errors)}"
        orch_status_code = "PARTIAL"

    # Check which intelligence flags are active
    intelligence_flags = {
        "sae_intelligence_active": is_flag_enabled("sae_intelligence_active"),
        "erce_intelligence_active": is_flag_enabled("erce_intelligence_active"),
        "birl_intelligence_active": is_flag_enabled("birl_intelligence_active"),
        "far_intelligence_active": is_flag_enabled("far_intelligence_active"),
    }

    # Intelligence is active if any flag is enabled AND no errors
    any_intelligence = any(intelligence_flags.values())
    intelligence_active = any_intelligence and len(pipeline_errors) < 4

    # Monitor: ORCH stage_end
    monitor_event(
        metrics=metrics,
        agent_role="orchestrator",
        stage="ORCH",
        event_type="stage_end",
        duration_ms=total_duration_ms,
        status_code=orch_status_code
    )

    logger.info(
        "Orchestrator pipeline complete",
        extra={
            "request_id": request_id,
            "orchestrator_stage": "COMPLETE",
            "agent_role": "orchestrator",
            "duration_ms": total_duration_ms,
            "status": "success" if not pipeline_errors else "partial",
            "error_key": None,
            "pipeline_status": pipeline_status,
            "stages_succeeded": 4 - len(pipeline_errors),
            "stages_failed": len(pipeline_errors),
        },
    )

    return {
        "sae_matches": sae_matches,
        "erce_results": erce_results,
        "birl_narratives": birl_narratives,
        "flowdown_gaps": flowdown_gaps,
        "_meta": {
            "engine_version": "5.7",
            "intelligence_active": intelligence_active,
            "intelligence_flags": intelligence_flags,
            "pipeline_status": pipeline_status,
            "request_id": request_id,
            "generated_at": datetime.now().isoformat(),
            "total_duration_ms": total_duration_ms,
            "stage_statuses": stage_statuses,
            "stage_durations_ms": stage_durations,
            "stats": {
                "sae": sae_stats,
                "erce": erce_stats,
                "birl": birl_stats,
                "far": far_stats
            },
            "monitor": metrics.to_meta_monitor()
        }
    }


# ============================================================================
# COMPARE V3 ORCHESTRATOR (PHASE 4F - LEGACY)
# ============================================================================

def run_compare_v3(
    v1_text: str,
    v2_text: str,
    v1_contract_id: Optional[int] = None,
    v2_contract_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Phase 4F Compare v3 pipeline with real intelligence.

    PIPELINE ORDER:
    1. SAE - Semantic clause alignment (embeddings)
    2. ERCE - Risk classification (pattern library)
    3. BIRL - Business impact narratives (Claude)
    4. FAR - Flowdown gap analysis (rule-based)

    Args:
        v1_text: First contract version text
        v2_text: Second contract version text
        v1_contract_id: Optional contract ID for v1
        v2_contract_id: Optional contract ID for v2

    Returns:
        Dict with all pipeline outputs
    """
    request_id = str(uuid.uuid4())
    intelligence_active = True
    pipeline_errors = []

    # Get clauses from database if contract IDs provided
    v1_clauses = []
    v2_clauses = []

    if v1_contract_id:
        v1_clauses = get_clauses_for_contract(v1_contract_id)
    if v2_contract_id:
        v2_clauses = get_clauses_for_contract(v2_contract_id)

    # If no clauses from DB, create synthetic clauses from text
    if not v1_clauses and v1_text:
        v1_clauses = [{'id': 1, 'text': v1_text[:2000], 'title': 'Full Contract', 'section_number': '1'}]
    if not v2_clauses and v2_text:
        v2_clauses = [{'id': 1, 'text': v2_text[:2000], 'title': 'Full Contract', 'section_number': '1'}]

    # =========================================================================
    # 1. SAE - Semantic Alignment
    # =========================================================================
    try:
        sae_matches, sae_stats = run_sae_real(
            v1_clauses, v2_clauses,
            v1_contract_id or 0, v2_contract_id or 0,
            request_id
        )
        logger.info(f"[{request_id}] SAE complete", extra={
            "request_id": request_id,
            "matched_count": sae_stats.get("matched_count", 0),
            "unmatched_v1": sae_stats.get("unmatched_v1", 0),
            "unmatched_v2": sae_stats.get("unmatched_v2", 0)
        })
    except Exception as e:
        logger.error(f"[{request_id}] SAE failed: {e}")
        sae_matches = _generate_sae_placeholder()
        sae_stats = {"matched_count": 3, "unmatched_v1": 0, "unmatched_v2": 0}
        pipeline_errors.append("SAE")
        intelligence_active = False

    # =========================================================================
    # 2. ERCE - Risk Classification
    # =========================================================================
    try:
        erce_results, erce_stats = run_erce_real(sae_matches, v1_clauses, v2_clauses, request_id)
        logger.info(f"[{request_id}] ERCE complete", extra={
            "request_id": request_id,
            "risk_count": erce_stats.get("risk_count", 0),
            "high_count": erce_stats.get("high_count", 0),
            "critical_count": erce_stats.get("critical_count", 0)
        })
    except Exception as e:
        logger.error(f"[{request_id}] ERCE failed: {e}")
        erce_results = _generate_erce_placeholder()
        erce_stats = {"risk_count": 3, "high_count": 1, "critical_count": 0}
        pipeline_errors.append("ERCE")
        intelligence_active = False

    # =========================================================================
    # 3. BIRL - Business Impact Narratives
    # =========================================================================
    try:
        birl_narratives, birl_stats = run_birl_real(
            erce_results, sae_matches, v1_clauses, v2_clauses, request_id
        )
        logger.info(f"[{request_id}] BIRL complete", extra={
            "request_id": request_id,
            "narratives_count": birl_stats.get("narratives_count", 0),
            "failures_count": birl_stats.get("failures_count", 0)
        })
    except Exception as e:
        logger.error(f"[{request_id}] BIRL failed: {e}")
        birl_narratives = _generate_birl_placeholder()
        birl_stats = {"narratives_count": 3, "failures_count": 0}
        pipeline_errors.append("BIRL")
        intelligence_active = False

    # =========================================================================
    # 4. FAR - Flowdown Gap Analysis
    # =========================================================================
    try:
        flowdown_gaps, far_stats = run_far_real(
            v1_contract_id or 0, v2_contract_id or 0,
            v1_clauses, v2_clauses, request_id
        )
        logger.info(f"[{request_id}] FAR complete", extra={
            "request_id": request_id,
            "gaps_count": far_stats.get("gaps_count", 0),
            "critical_count": far_stats.get("critical_count", 0),
            "high_count": far_stats.get("high_count", 0)
        })
    except Exception as e:
        logger.error(f"[{request_id}] FAR failed: {e}")
        flowdown_gaps = _generate_far_placeholder()
        far_stats = {"gaps_count": 0, "critical_count": 0, "high_count": 0}
        pipeline_errors.append("FAR")

    # =========================================================================
    # Build Result
    # =========================================================================
    return {
        "sae_matches": sae_matches,
        "erce_results": erce_results,
        "birl_narratives": birl_narratives,
        "flowdown_gaps": flowdown_gaps,
        "_meta": {
            "engine_version": "4F",
            "intelligence_active": intelligence_active,
            "pipeline_status": "REAL" if not pipeline_errors else f"PARTIAL:{','.join(pipeline_errors)}",
            "request_id": request_id,
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "sae": sae_stats,
                "erce": erce_stats,
                "birl": birl_stats,
                "far": far_stats
            }
        }
    }


def create_comparison_snapshot(
    v1_snapshot_id: int,
    v2_snapshot_id: int,
    v1_text: str,
    v2_text: str
) -> ComparisonSnapshot:
    """
    Create a full ComparisonSnapshot from Compare v3 pipeline.

    Phase 4F: Uses real intelligence with fallbacks.
    """
    # Run the pipeline
    raw_results = run_compare_v3(v1_text, v2_text)

    # Convert to typed dataclasses
    sae_matches = [ClauseMatch(**m) for m in raw_results["sae_matches"]]
    erce_results = [RiskDelta(**r) for r in raw_results["erce_results"]]
    birl_narratives = [BusinessImpact(**n) for n in raw_results["birl_narratives"]]
    flowdown_gaps = [FlowdownGap(**g) for g in raw_results["flowdown_gaps"]]

    # Create snapshot
    snapshot = ComparisonSnapshot(
        id=int(uuid.uuid4().int % 100000),
        v1_snapshot_id=v1_snapshot_id,
        v2_snapshot_id=v2_snapshot_id,
        created_at=datetime.now(),
        sae_matches=sae_matches,
        erce_results=erce_results,
        birl_narratives=birl_narratives,
        flowdown_gaps=flowdown_gaps,
    )

    return snapshot


# ============================================================================
# API-READY FUNCTION
# ============================================================================

def compare_v3_api(
    v1_text: str,
    v2_text: str,
    v1_contract_id: Optional[int] = None,
    v2_contract_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    API-ready Compare v3 function.

    Returns the standard response shape for frontend consumption.
    """
    try:
        result = run_compare_v3(v1_text, v2_text, v1_contract_id, v2_contract_id)

        return {
            "success": True,
            "data": result,
            "engine_version": result.get("_meta", {}).get("engine_version", "4F"),
            "intelligence_active": result.get("_meta", {}).get("intelligence_active", True)
        }

    except Exception as e:
        logger.error(f"compare_v3_api error: {e}")
        return {
            "success": False,
            "error_category": "compare",
            "error_message_key": "compare.internal_failure",
            "error_detail": str(e),
            "retry_allowed": False
        }
