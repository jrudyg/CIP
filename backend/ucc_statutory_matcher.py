"""
UCC Statutory Matcher Module
Integrated statutory conflict detection for CIP contract analysis.

This module loads UCC statutory rules from UCC_Statutory_Logic_v2.json and
matches contract clause text against trigger concepts to identify statutory
violations.

Created: 2026-01-18
Version: 1.0
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class UCCRule:
    """UCC statutory rule with trigger concepts and risk assessment."""
    rule_id: str
    title: str
    citation: str
    category: str
    trigger_concepts: List[str]
    severity: str
    risk_multiplier: float
    business_impact: str
    si_impact: str


@dataclass
class UCCMatch:
    """UCC statutory violation match result."""
    rule_id: str
    category: str
    severity: str
    risk_multiplier: float
    matched_concepts: List[str]
    citation: str
    business_impact: str
    si_impact: str


def load_ucc_rules(json_path: str = None) -> List[UCCRule]:
    """Load UCC statutory rules from JSON file.

    Args:
        json_path: Path to UCC_Statutory_Logic_v2.json file.
                  Defaults to CIP/00 download/UCC_Statutory_Logic_v2.json

    Returns:
        List of UCCRule dataclass objects

    Raises:
        FileNotFoundError: If JSON file not found
        json.JSONDecodeError: If JSON is malformed
    """
    if json_path is None:
        # Default path relative to CIP root
        cip_root = Path(__file__).resolve().parents[1]
        json_path = cip_root / "00 download" / "UCC_Statutory_Logic_v2.json"

    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"UCC rules file not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rules = []
    for rule_data in data.get("rules", []):
        rule = UCCRule(
            rule_id=rule_data["id"],
            title=rule_data["title"],
            citation=rule_data["citation"],
            category=rule_data["category"],
            trigger_concepts=rule_data["trigger_concepts"],
            severity=rule_data["severity"],
            risk_multiplier=float(rule_data["risk_multiplier"]),
            business_impact=rule_data.get("business_impact", ""),
            si_impact=rule_data.get("si_impact", "")
        )
        rules.append(rule)

    return rules


def match_ucc_violations(
    clause_text: str,
    clause_type: str,
    ucc_rules: List[UCCRule]
) -> Optional[UCCMatch]:
    """Match clause text against UCC statutory rules.

    Uses case-insensitive keyword matching to detect statutory violations.
    Returns the highest-severity match if multiple rules trigger.

    Args:
        clause_text: The contract clause text to analyze
        clause_type: The clause category (e.g., "REMEDY_LIMITATION", "WARRANTY")
        ucc_rules: List of UCCRule objects to match against

    Returns:
        UCCMatch object if violation detected, None otherwise
    """
    if not clause_text or not ucc_rules:
        return None

    # Normalize clause text for matching
    clause_text_lower = clause_text.lower()

    # Track all matches (may have multiple)
    matches = []

    for rule in ucc_rules:
        # Check if any trigger concepts match
        matched_concepts = []

        for concept in rule.trigger_concepts:
            concept_lower = concept.lower()

            # Word-boundary matching to avoid false positives
            # "rate" should not match "cooperate", "govern" should not match "government"
            import re
            # Build regex pattern with word boundaries
            pattern = r'\b' + re.escape(concept_lower) + r'\b'

            if re.search(pattern, clause_text_lower):
                matched_concepts.append(concept)

        # If any concepts matched, record this rule as a match
        if matched_concepts:
            match = UCCMatch(
                rule_id=rule.rule_id,
                category=rule.category,
                severity=rule.severity,
                risk_multiplier=rule.risk_multiplier,
                matched_concepts=matched_concepts,
                citation=rule.citation,
                business_impact=rule.business_impact,
                si_impact=rule.si_impact
            )
            matches.append(match)

    if not matches:
        return None

    # Return highest-severity match (by risk_multiplier)
    highest_match = max(matches, key=lambda m: m.risk_multiplier)
    return highest_match


def classify_ucc_severity(risk_multiplier: float) -> str:
    """Map UCC risk_multiplier to severity level.

    Args:
        risk_multiplier: Risk multiplier value (typically 5.0-10.0)

    Returns:
        Severity level: "CRITICAL", "HIGH", or "MEDIUM"
    """
    if risk_multiplier >= 9.5:
        return "CRITICAL"
    elif risk_multiplier >= 8.0:
        return "HIGH"
    elif risk_multiplier >= 5.0:
        return "MEDIUM"
    else:
        return "LOW"


# Module-level cache for UCC rules (loaded once)
_UCC_RULES_CACHE: Optional[List[UCCRule]] = None


def get_ucc_rules() -> List[UCCRule]:
    """Get UCC rules with caching.

    Loads rules from JSON on first call, then returns cached version.

    Returns:
        List of UCCRule objects
    """
    global _UCC_RULES_CACHE

    if _UCC_RULES_CACHE is None:
        _UCC_RULES_CACHE = load_ucc_rules()

    return _UCC_RULES_CACHE


def detect_ucc_violation(clause_text: str, clause_type: str = None) -> Optional[Dict[str, Any]]:
    """High-level UCC violation detection function.

    This is the primary entry point for UCC statutory detection.

    Args:
        clause_text: Contract clause text to analyze
        clause_type: Optional clause category for filtering

    Returns:
        Dictionary with UCC violation details, or None if no violation

    Example return:
        {
            "statutory_flag": "UCC-2-719",
            "citation": "6 Del. C. § 2-719",
            "severity": "CRITICAL",
            "risk_multiplier": 10.0,
            "matched_concepts": ["sole remedy", "exclusive remedy"],
            "business_impact": "Client loses all self-help remedies...",
            "si_impact": "If vendor equipment fails..."
        }
    """
    rules = get_ucc_rules()
    match = match_ucc_violations(clause_text, clause_type, rules)

    if match:
        return {
            "statutory_flag": match.rule_id,
            "citation": match.citation,
            "severity": match.severity,
            "risk_multiplier": match.risk_multiplier,
            "matched_concepts": match.matched_concepts,
            "category": match.category,
            "business_impact": match.business_impact,
            "si_impact": match.si_impact
        }

    return None


# Export public API
__all__ = [
    'UCCRule',
    'UCCMatch',
    'load_ucc_rules',
    'match_ucc_violations',
    'classify_ucc_severity',
    'get_ucc_rules',
    'detect_ucc_violation'
]
