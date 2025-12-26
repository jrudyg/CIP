"""
Pattern Library Cache for Phase 5 ERCE (Enterprise Risk Classification Engine)
Stores risk classification patterns for efficient pattern matching.

Phase 5 Step 1: Schema and metrics only.
Pattern matching activation happens in Step 3.
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from phase5_flags import is_flag_enabled, get_config


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RiskPattern:
    """Risk classification pattern definition"""
    pattern_id: str
    pattern_name: str
    risk_category: str  # "ADMIN", "MODERATE", "HIGH", "CRITICAL"
    pattern_type: str   # "regex", "keyword", "semantic"
    pattern_value: str  # Regex string or keyword list JSON
    success_probability: Optional[float]  # Historical success rate
    description: str
    priority: int  # Higher = checked first
    enabled: bool
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskPattern":
        return cls(**data)


# ============================================================================
# DEFAULT PATTERN LIBRARY
# ============================================================================

DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {
        "pattern_id": "INDEM_UNLIMITED_001",
        "pattern_name": "Unlimited Indemnification",
        "risk_category": "CRITICAL",
        "pattern_type": "regex",
        "pattern_value": r"(?i)(unlimited|uncapped)\s+(indemnif|liability)",
        "success_probability": 0.35,
        "description": "Detects unlimited or uncapped indemnification clauses",
        "priority": 100,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "INDEM_CONSEQUENTIAL_002",
        "pattern_name": "Consequential Damages Included",
        "risk_category": "HIGH",
        "pattern_type": "regex",
        "pattern_value": r"(?i)consequential\s+damages?\s+(included|not\s+excluded)",
        "success_probability": 0.55,
        "description": "Detects inclusion of consequential damages",
        "priority": 90,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "TERM_AUTO_RENEW_003",
        "pattern_name": "Auto-Renewal Clause",
        "risk_category": "MODERATE",
        "pattern_type": "regex",
        "pattern_value": r"(?i)(auto|automatic)\s*(renew|extend)",
        "success_probability": 0.75,
        "description": "Detects automatic renewal terms",
        "priority": 60,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "PAY_NET_EXTENDED_004",
        "pattern_name": "Extended Payment Terms",
        "risk_category": "MODERATE",
        "pattern_type": "regex",
        "pattern_value": r"(?i)net\s*(60|90|120)",
        "success_probability": 0.70,
        "description": "Detects extended payment terms (Net 60+)",
        "priority": 50,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "IP_ASSIGN_005",
        "pattern_name": "IP Assignment",
        "risk_category": "HIGH",
        "pattern_type": "regex",
        "pattern_value": r"(?i)(assign|transfer)\s+(all|any)?\s*(intellectual property|ip|patent|copyright)",
        "success_probability": 0.60,
        "description": "Detects broad IP assignment clauses",
        "priority": 85,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "NONCOMP_BROAD_006",
        "pattern_name": "Broad Non-Compete",
        "risk_category": "HIGH",
        "pattern_type": "regex",
        "pattern_value": r"(?i)non-?compete\s+.{0,50}(worldwide|global|unlimited)",
        "success_probability": 0.45,
        "description": "Detects overly broad non-compete clauses",
        "priority": 80,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "AUDIT_RIGHTS_007",
        "pattern_name": "Audit Rights",
        "risk_category": "ADMIN",
        "pattern_type": "regex",
        "pattern_value": r"(?i)audit\s+(right|access)",
        "success_probability": 0.85,
        "description": "Detects audit rights provisions",
        "priority": 30,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
    {
        "pattern_id": "NOTICE_PERIOD_008",
        "pattern_name": "Notice Period Change",
        "risk_category": "ADMIN",
        "pattern_type": "regex",
        "pattern_value": r"(?i)notice\s+.{0,20}(day|week|month)",
        "success_probability": 0.90,
        "description": "Detects notice period provisions",
        "priority": 20,
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    },
]


# ============================================================================
# PATTERN CACHE CLASS
# ============================================================================

class PatternCache:
    """
    JSON-based cache for ERCE risk classification patterns.

    Phase 5 Step 1: Structure and metrics only.
    Pattern matching activation happens in Step 3.
    """

    def __init__(self, cache_path: Optional[str] = None):
        """
        Initialize pattern cache.

        Args:
            cache_path: Path to JSON cache file (defaults to data/pattern_library.json)
        """
        if cache_path is None:
            cache_path = os.path.join(
                os.path.dirname(__file__),
                "data",
                "pattern_library.json"
            )

        self.cache_path = os.path.abspath(cache_path)

        # In-memory compiled patterns (for performance)
        self._compiled_patterns: Dict[str, re.Pattern] = {}

        # Metrics counters (in-memory) - must be initialized before _init_cache
        self._metrics = {
            "pattern_matches": 0,
            "pattern_misses": 0,
            "cache_loads": 0,
            "cache_writes": 0,
            "errors": 0,
        }

        # Initialize directory and cache file
        self._ensure_directory()
        self._init_cache()

    def _ensure_directory(self) -> None:
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    def _init_cache(self) -> None:
        """Initialize cache file with default patterns if not exists"""
        if not os.path.exists(self.cache_path):
            self._write_cache({
                "schema_version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "patterns": DEFAULT_PATTERNS
            })

    def _read_cache(self) -> Dict[str, Any]:
        """Read cache from JSON file"""
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._metrics["cache_loads"] += 1
                return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self._metrics["errors"] += 1
            return {
                "schema_version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "patterns": DEFAULT_PATTERNS
            }

    def _write_cache(self, data: Dict[str, Any]) -> bool:
        """Write cache to JSON file"""
        try:
            data["updated_at"] = datetime.now().isoformat()
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._metrics["cache_writes"] += 1
            return True
        except (IOError, json.JSONDecodeError) as e:
            self._metrics["errors"] += 1
            return False

    def get_all_patterns(self) -> List[RiskPattern]:
        """
        Get all patterns from cache.

        Returns:
            List of RiskPattern objects, sorted by priority (highest first)

        Note: Returns patterns regardless of feature flag (read-only operation).
        """
        data = self._read_cache()
        patterns = [RiskPattern.from_dict(p) for p in data.get("patterns", [])]
        return sorted(patterns, key=lambda p: p.priority, reverse=True)

    def get_enabled_patterns(self) -> List[RiskPattern]:
        """
        Get only enabled patterns from cache.

        Returns:
            List of enabled RiskPattern objects, sorted by priority
        """
        all_patterns = self.get_all_patterns()
        return [p for p in all_patterns if p.enabled]

    def get_patterns_by_category(self, category: str) -> List[RiskPattern]:
        """
        Get patterns filtered by risk category.

        Args:
            category: Risk category ("ADMIN", "MODERATE", "HIGH", "CRITICAL")

        Returns:
            List of matching RiskPattern objects
        """
        all_patterns = self.get_enabled_patterns()
        return [p for p in all_patterns if p.risk_category == category]

    def get_pattern_by_id(self, pattern_id: str) -> Optional[RiskPattern]:
        """
        Get specific pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            RiskPattern or None if not found
        """
        all_patterns = self.get_all_patterns()
        for p in all_patterns:
            if p.pattern_id == pattern_id:
                return p
        return None

    def add_pattern(self, pattern: RiskPattern) -> bool:
        """
        Add new pattern to cache.

        Args:
            pattern: RiskPattern to add

        Returns:
            True if added successfully

        Note: Only writes if pattern_cache_active flag is True.
        """
        if not is_flag_enabled("pattern_cache_active"):
            return False

        data = self._read_cache()
        patterns = data.get("patterns", [])

        # Check for duplicate
        for p in patterns:
            if p.get("pattern_id") == pattern.pattern_id:
                return False  # Already exists

        patterns.append(pattern.to_dict())
        data["patterns"] = patterns
        return self._write_cache(data)

    def update_pattern(self, pattern: RiskPattern) -> bool:
        """
        Update existing pattern in cache.

        Args:
            pattern: RiskPattern with updated values

        Returns:
            True if updated successfully

        Note: Only writes if pattern_cache_active flag is True.
        """
        if not is_flag_enabled("pattern_cache_active"):
            return False

        data = self._read_cache()
        patterns = data.get("patterns", [])

        for i, p in enumerate(patterns):
            if p.get("pattern_id") == pattern.pattern_id:
                pattern_dict = pattern.to_dict()
                pattern_dict["updated_at"] = datetime.now().isoformat()
                patterns[i] = pattern_dict
                data["patterns"] = patterns
                return self._write_cache(data)

        return False  # Not found

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete pattern from cache.

        Args:
            pattern_id: Pattern identifier to delete

        Returns:
            True if deleted successfully

        Note: Only writes if pattern_cache_active flag is True.
        """
        if not is_flag_enabled("pattern_cache_active"):
            return False

        data = self._read_cache()
        patterns = data.get("patterns", [])

        original_count = len(patterns)
        patterns = [p for p in patterns if p.get("pattern_id") != pattern_id]

        if len(patterns) < original_count:
            data["patterns"] = patterns
            return self._write_cache(data)

        return False  # Not found

    def compile_pattern(self, pattern: RiskPattern) -> Optional[re.Pattern]:
        """
        Compile regex pattern for efficient matching.

        Args:
            pattern: RiskPattern to compile

        Returns:
            Compiled regex or None if invalid/non-regex pattern
        """
        if pattern.pattern_type != "regex":
            return None

        if pattern.pattern_id in self._compiled_patterns:
            return self._compiled_patterns[pattern.pattern_id]

        try:
            compiled = re.compile(pattern.pattern_value)
            self._compiled_patterns[pattern.pattern_id] = compiled
            return compiled
        except re.error:
            self._metrics["errors"] += 1
            return None

    def match_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Match text against all enabled patterns.

        Args:
            text: Text to match against patterns

        Returns:
            List of matching pattern results

        Note: Only performs matching if pattern_cache_active flag is True.
              Otherwise returns empty list.
        """
        if not is_flag_enabled("pattern_cache_active"):
            return []

        matches = []
        patterns = self.get_enabled_patterns()

        for pattern in patterns:
            if pattern.pattern_type == "regex":
                compiled = self.compile_pattern(pattern)
                if compiled:
                    match = compiled.search(text)
                    if match:
                        self._metrics["pattern_matches"] += 1
                        matches.append({
                            "pattern_id": pattern.pattern_id,
                            "pattern_name": pattern.pattern_name,
                            "risk_category": pattern.risk_category,
                            "success_probability": pattern.success_probability,
                            "match_text": match.group(),
                            "match_start": match.start(),
                            "match_end": match.end(),
                        })
                    else:
                        self._metrics["pattern_misses"] += 1

            elif pattern.pattern_type == "keyword":
                keywords = json.loads(pattern.pattern_value)
                text_lower = text.lower()
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        self._metrics["pattern_matches"] += 1
                        matches.append({
                            "pattern_id": pattern.pattern_id,
                            "pattern_name": pattern.pattern_name,
                            "risk_category": pattern.risk_category,
                            "success_probability": pattern.success_probability,
                            "match_text": keyword,
                            "match_start": None,
                            "match_end": None,
                        })
                        break
                else:
                    self._metrics["pattern_misses"] += 1

        return matches

    def reset_cache(self) -> bool:
        """
        Reset cache to default patterns.

        Returns:
            True if reset successfully
        """
        self._compiled_patterns.clear()
        return self._write_cache({
            "schema_version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "patterns": DEFAULT_PATTERNS
        })

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics and metrics
        """
        data = self._read_cache()
        patterns = data.get("patterns", [])

        # Count by category
        category_counts = {}
        for p in patterns:
            cat = p.get("risk_category", "UNKNOWN")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Count by type
        type_counts = {}
        for p in patterns:
            ptype = p.get("pattern_type", "unknown")
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        enabled_count = sum(1 for p in patterns if p.get("enabled", False))

        return {
            "total_patterns": len(patterns),
            "enabled_patterns": enabled_count,
            "disabled_patterns": len(patterns) - enabled_count,
            "category_counts": category_counts,
            "type_counts": type_counts,
            "compiled_patterns": len(self._compiled_patterns),
            "metrics": self._metrics.copy(),
            "schema_version": data.get("schema_version", "unknown"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "ttl_hours": get_config("pattern_cache_ttl_hours", 24),
            "flag_enabled": is_flag_enabled("pattern_cache_active"),
            "cache_path": self.cache_path,
        }

    def get_metrics(self) -> Dict[str, int]:
        """
        Get cache metrics counters.

        Returns:
            Dictionary with pattern_matches, pattern_misses, cache_loads, cache_writes, errors
        """
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset metrics counters to zero"""
        self._metrics = {
            "pattern_matches": 0,
            "pattern_misses": 0,
            "cache_loads": 0,
            "cache_writes": 0,
            "errors": 0,
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_pattern_cache: Optional[PatternCache] = None


def get_pattern_cache() -> PatternCache:
    """
    Get global pattern cache instance.

    Returns:
        PatternCache singleton
    """
    global _pattern_cache
    if _pattern_cache is None:
        _pattern_cache = PatternCache()
    return _pattern_cache


# ============================================================================
# PUBLIC API FUNCTIONS (Step 1 - No call sites yet)
# ============================================================================

@dataclass
class PatternLibrary:
    """Pattern library container for ERCE"""
    patterns: List[RiskPattern]
    schema_version: str
    loaded_from: str
    loaded_at: datetime

    def get_by_category(self, category: str) -> List[RiskPattern]:
        """Get patterns by risk category"""
        return [p for p in self.patterns if p.risk_category == category]

    def get_enabled(self) -> List[RiskPattern]:
        """Get only enabled patterns"""
        return [p for p in self.patterns if p.enabled]


def load_pattern_library(path: str = "data/pattern_library.json") -> PatternLibrary:
    """
    Load pattern library from file.

    Phase 5 Step 1: Loads patterns but matching is disabled until flag is True.

    Args:
        path: Path to pattern library JSON file (relative to backend dir)

    Returns:
        PatternLibrary with loaded patterns
    """
    # Resolve path relative to backend directory
    if not os.path.isabs(path):
        base_dir = os.path.dirname(__file__)
        full_path = os.path.join(base_dir, path)
    else:
        full_path = path

    # Use PatternCache to load (handles defaults if file missing)
    cache = PatternCache(cache_path=full_path)
    patterns = cache.get_all_patterns()

    return PatternLibrary(
        patterns=patterns,
        schema_version="1.0.0",
        loaded_from=full_path,
        loaded_at=datetime.now(),
    )


# ============================================================================
# STEP 3: ERCE INTELLIGENCE HELPERS
# ============================================================================

# Severity ordering for pattern selection
SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "ADMIN": 1}


@dataclass
class ERCEMatchResult:
    """Result from ERCE pattern matching operation"""
    pattern_id: Optional[str]
    pattern_name: Optional[str]
    risk_category: str
    success_probability: Optional[float]
    confidence: float
    matched_patterns_count: int
    keyword_density: float


def match_patterns_for_erce(
    text: str,
    patterns: List[RiskPattern]
) -> List[Dict[str, Any]]:
    """
    Match text against patterns for ERCE classification.

    Phase 5 Step 3: Real pattern matching for ERCE.
    Does NOT require erce_intelligence_active flag - that's checked in engine.

    Args:
        text: Combined clause text to analyze
        patterns: List of RiskPattern objects to match against

    Returns:
        List of matched patterns with match details
    """
    if not text or not patterns:
        return []

    matches = []
    text_lower = text.lower()

    for pattern in patterns:
        if not pattern.enabled:
            continue

        if pattern.pattern_type == "regex":
            try:
                compiled = re.compile(pattern.pattern_value)
                match = compiled.search(text)
                if match:
                    matches.append({
                        "pattern_id": pattern.pattern_id,
                        "pattern_name": pattern.pattern_name,
                        "risk_category": pattern.risk_category,
                        "success_probability": pattern.success_probability,
                        "match_text": match.group(),
                        "match_type": "regex",
                        "priority": pattern.priority,
                    })
            except re.error:
                continue

        elif pattern.pattern_type == "keyword":
            try:
                keywords = json.loads(pattern.pattern_value)
                matched_keywords = [kw for kw in keywords if kw.lower() in text_lower]
                if matched_keywords:
                    matches.append({
                        "pattern_id": pattern.pattern_id,
                        "pattern_name": pattern.pattern_name,
                        "risk_category": pattern.risk_category,
                        "success_probability": pattern.success_probability,
                        "match_text": matched_keywords[0],
                        "match_type": "keyword",
                        "priority": pattern.priority,
                    })
            except (json.JSONDecodeError, TypeError):
                continue

    return matches


def compute_keyword_density(text: str, matched_patterns: List[Dict[str, Any]]) -> float:
    """
    Compute keyword density score for confidence calculation.

    Higher density = more pattern matches per unit of text = higher confidence.

    Args:
        text: The analyzed text
        matched_patterns: List of matched pattern results

    Returns:
        Keyword density score in [0.0, 1.0]
    """
    if not text or not matched_patterns:
        return 0.0

    # Count total match characters
    total_match_chars = sum(
        len(m.get("match_text", ""))
        for m in matched_patterns
    )

    # Density = match chars / text length, capped at 1.0
    text_len = len(text)
    if text_len == 0:
        return 0.0

    raw_density = total_match_chars / text_len
    # Scale to make typical matches yield 0.6-0.9 confidence
    scaled_density = min(1.0, raw_density * 10)

    return scaled_density


def classify_erce_risk(
    matched_patterns: List[Dict[str, Any]],
    text: str
) -> ERCEMatchResult:
    """
    Classify risk based on matched patterns.

    Phase 5 Step 3: Real ERCE classification logic.

    Priority rules:
    - CRITICAL > HIGH > MODERATE > ADMIN
    - If multiple patterns match, use highest severity
    - Confidence increases with more pattern matches

    Args:
        matched_patterns: List of matched pattern dictionaries
        text: Original text (for density calculation)

    Returns:
        ERCEMatchResult with classification
    """
    if not matched_patterns:
        # No patterns matched - default to ADMIN with low confidence
        return ERCEMatchResult(
            pattern_id=None,
            pattern_name=None,
            risk_category="ADMIN",
            success_probability=None,
            confidence=round(0.30 + (0.29 * (len(text) / 1000 if text else 0)), 2),  # 0.30-0.59
            matched_patterns_count=0,
            keyword_density=0.0,
        )

    # Find highest severity pattern
    best_pattern = None
    best_severity = 0

    for pattern in matched_patterns:
        cat = pattern.get("risk_category", "ADMIN").upper()
        sev = SEVERITY_ORDER.get(cat, 1)
        if sev > best_severity:
            best_severity = sev
            best_pattern = pattern

    # Calculate confidence based on:
    # 1. Number of patterns matched (more = higher confidence)
    # 2. Keyword density
    keyword_density = compute_keyword_density(text, matched_patterns)
    pattern_count = len(matched_patterns)

    # Base confidence from pattern count: 0.60 + 0.05 per additional match, max 0.95
    base_confidence = min(0.95, 0.60 + (pattern_count - 1) * 0.05)

    # Adjust by keyword density: +/- 0.1
    density_adjustment = (keyword_density - 0.5) * 0.2  # -0.1 to +0.1
    final_confidence = max(0.60, min(0.95, base_confidence + density_adjustment))

    return ERCEMatchResult(
        pattern_id=best_pattern.get("pattern_id") if best_pattern else None,
        pattern_name=best_pattern.get("pattern_name") if best_pattern else None,
        risk_category=best_pattern.get("risk_category", "ADMIN").upper() if best_pattern else "ADMIN",
        success_probability=best_pattern.get("success_probability") if best_pattern else None,
        confidence=round(final_confidence, 2),
        matched_patterns_count=pattern_count,
        keyword_density=round(keyword_density, 3),
    )


def get_erce_patterns() -> List[RiskPattern]:
    """
    Get patterns for ERCE from global cache.

    Returns:
        List of enabled RiskPattern objects sorted by priority
    """
    cache = get_pattern_cache()
    return cache.get_enabled_patterns()
