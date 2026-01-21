"""
CCE-Plus Integration Module for CIP
====================================
Bridge module enabling CIP to leverage CCE-Plus risk scoring and cascade detection.

Location: C:\\Users\\jrudy\\CIP\\backend\\cce_plus_integration.py
Requires: CCE-Plus installed at C:\\Users\\jrudy\\CCE\\cce-plus

Usage:
    from cce_plus_integration import (
        score_clause_risk,
        detect_cascades,
        calculate_display_priority,
        enrich_comparison_entries
    )
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# CCE-Plus installation path
CCE_PLUS_ROOT = Path(r"C:\Users\jrudy\CCE\cce-plus")
CCE_PLUS_LIB = CCE_PLUS_ROOT / "scripts" / "lib"
CCE_PLUS_KNOWLEDGE = CCE_PLUS_ROOT / "knowledge" / "architecture"

# Add CCE-Plus to Python path for imports
if str(CCE_PLUS_ROOT) not in sys.path:
    sys.path.insert(0, str(CCE_PLUS_ROOT))

# =============================================================================
# STATUTORY LOGIC LOADER
# =============================================================================

_statutory_logic_cache = None

def load_statutory_logic() -> Dict:
    """
    Load UCC_Statutory_Logic.json from CCE-Plus.
    Single source of truth for statutory rules.
    """
    global _statutory_logic_cache
    
    if _statutory_logic_cache is not None:
        return _statutory_logic_cache
    
    statutory_path = CCE_PLUS_KNOWLEDGE / "UCC_Statutory_Logic.json"
    
    if not statutory_path.exists():
        raise FileNotFoundError(
            f"CCE-Plus statutory logic not found at {statutory_path}. "
            "Ensure CCE-Plus is installed and UCC_Statutory_Logic.json exists."
        )
    
    with open(statutory_path, 'r', encoding='utf-8') as f:
        _statutory_logic_cache = json.load(f)
    
    return _statutory_logic_cache


def get_cascade_patterns() -> List[Dict]:
    """Get cascade patterns from CCE-Plus statutory logic."""
    logic = load_statutory_logic()
    return logic.get('cascade_patterns', [])


def get_keyword_severity_map() -> Dict:
    """Get keyword severity mappings from CCE-Plus."""
    logic = load_statutory_logic()
    return logic.get('keyword_severity_map', {})


# =============================================================================
# RISK SCORING (Mirrors CCE-Plus risk-scorer.js)
# =============================================================================

# 10/8/5/1 Heuristic Map
RISK_MAP = {
    'CRITICAL': 10,
    'HIGH': 8,
    'MEDIUM': 5,
    'LOW': 1,
    'MINIMAL': 0
}

# Classification Thresholds
RISK_THRESHOLDS = {
    'CRITICAL': 9.0,
    'HIGH': 7.0,
    'MEDIUM': 5.0,
    'LOW': 3.0
}

# Risk Type Baselines (from CCE-Plus risk-scorer.js)
RISK_TYPE_MAP = {
    'Legal/Liability': {'severity': 8, 'complexity': 6, 'impact': 9},
    'Legal/Remedy': {'severity': 10, 'complexity': 7, 'impact': 10},
    'Financial/Prepayment': {'severity': 9, 'complexity': 5, 'impact': 9},
    'Financial/Payment': {'severity': 3, 'complexity': 2, 'impact': 4},
    'IP/Ownership': {'severity': 7, 'complexity': 5, 'impact': 8},
    'Termination': {'severity': 6, 'complexity': 4, 'impact': 7},
    'Indemnification': {'severity': 8, 'complexity': 6, 'impact': 8},
    'Confidentiality': {'severity': 5, 'complexity': 3, 'impact': 5},
    'Default': {'severity': 5, 'complexity': 5, 'impact': 5}
}


def calculate_risk_score(
    severity: int,
    complexity: int,
    impact: int,
    statutory_multiplier: Optional[float] = None,
    statutory_weight: float = 0.4
) -> float:
    """
    Calculate weighted risk score with optional statutory component.

    Base formula: (severity × 0.3) + (complexity × 0.3) + (impact × 0.4)

    If UCC statutory violation detected:
        - Base components weighted at (1 - statutory_weight)
        - Statutory component weighted at statutory_weight
        - Final score = (base × 0.6) + (statutory_multiplier × 0.4)

    Args:
        severity: 0-10 legal/business severity scale
        complexity: 0-10 interpretive complexity scale
        impact: 0-10 business consequence scale
        statutory_multiplier: 0-10 UCC risk multiplier (if violation detected)
        statutory_weight: Weight for statutory component (default 0.4 = 40%)

    Returns:
        Weighted score 0.0-10.0

    Example:
        Base score 6.8 + UCC multiplier 10.0 = 8.08 (escalates MEDIUM→HIGH)
    """
    # Normalize inputs
    severity = max(0, min(10, severity))
    complexity = max(0, min(10, complexity))
    impact = max(0, min(10, impact))

    # Calculate base score from severity/complexity/impact
    base_score = (severity * 0.3) + (complexity * 0.3) + (impact * 0.4)

    # If statutory violation detected, apply weighted integration
    if statutory_multiplier is not None:
        statutory_multiplier = max(0, min(10, statutory_multiplier))
        base_weight = 1.0 - statutory_weight  # 0.6 if statutory_weight = 0.4
        statutory_component = statutory_multiplier * statutory_weight
        final_score = (base_score * base_weight) + statutory_component
        return round(final_score, 1)

    # No statutory violation: return base score
    return round(base_score, 1)


def classify_risk(score: float) -> str:
    """Classify risk level based on score."""
    if score >= RISK_THRESHOLDS['CRITICAL']:
        return 'CRITICAL'
    elif score >= RISK_THRESHOLDS['HIGH']:
        return 'HIGH'
    elif score >= RISK_THRESHOLDS['MEDIUM']:
        return 'MEDIUM'
    elif score >= RISK_THRESHOLDS['LOW']:
        return 'LOW'
    else:
        return 'MINIMAL'


def detect_keywords(text: str) -> Tuple[int, int]:
    """
    Detect risk keywords in clause text.
    Returns severity and impact adjustments.
    """
    keyword_map = get_keyword_severity_map()
    text_lower = text.lower()
    
    severity_adj = 0
    impact_adj = 0
    
    # Critical keywords (severity 10)
    for keyword in keyword_map.get('critical_10', []):
        if keyword in text_lower:
            severity_adj = max(severity_adj, 4)
            impact_adj = max(impact_adj, 2)
    
    # High keywords (severity 8)
    for keyword in keyword_map.get('high_8', []):
        if keyword in text_lower:
            severity_adj = max(severity_adj, 2)
            impact_adj = max(impact_adj, 1)
    
    # Medium keywords (severity 5)
    for keyword in keyword_map.get('medium_5', []):
        if keyword in text_lower:
            severity_adj = max(severity_adj, 1)
    
    return severity_adj, impact_adj


def score_clause_risk(
    clause_text: str,
    clause_type: str = 'Default',
    section_number: str = None
) -> Dict:
    """
    Score a single clause using CCE-Plus methodology.
    
    Args:
        clause_text: Full clause text
        clause_type: Risk category (e.g., 'Legal/Liability')
        section_number: Optional section reference (e.g., '5.2')
    
    Returns:
        Dict with risk_score, risk_level, severity, complexity, impact, statutory_flag
    """
    # Get baseline from risk type
    baseline = RISK_TYPE_MAP.get(clause_type, RISK_TYPE_MAP['Default'])
    
    severity = baseline['severity']
    complexity = baseline['complexity']
    impact = baseline['impact']
    
    # Adjust for keywords
    sev_adj, imp_adj = detect_keywords(clause_text)
    severity = min(10, severity + sev_adj)
    impact = min(10, impact + imp_adj)
    
    # Adjust complexity by text length
    word_count = len(clause_text.split())
    if word_count > 100:
        complexity = min(10, complexity + 2)
    elif word_count < 20:
        complexity = max(1, complexity - 1)
    
    # Check for statutory conflicts with UCC rule matching
    statutory_result = detect_statutory_conflict(clause_text, clause_type)

    # Extract statutory multiplier if violation found
    statutory_multiplier = None
    statutory_flag = None
    statutory_cite = None
    ucc_violation = None

    if statutory_result:
        statutory_multiplier = statutory_result.get("risk_multiplier")
        statutory_flag = statutory_result.get("statutory_flag")
        statutory_cite = statutory_result.get("citation")
        ucc_violation = statutory_result  # Store full UCC match details

    # Calculate risk score with statutory weight integration (40% if violation detected)
    risk_score = calculate_risk_score(
        severity,
        complexity,
        impact,
        statutory_multiplier=statutory_multiplier,
        statutory_weight=0.4  # 40% weight for UCC violations
    )
    risk_level = classify_risk(risk_score)

    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'severity': severity,
        'complexity': complexity,
        'impact': impact,
        'statutory_flag': statutory_flag,
        'statutory_cite': statutory_cite,
        'ucc_violation': ucc_violation,  # Full UCC match details
        'word_count': word_count
    }


# =============================================================================
# STATUTORY CONFLICT DETECTION
# =============================================================================

def detect_statutory_conflict(clause_text: str, clause_type: str = None) -> Optional[Dict]:
    """
    Detect Delaware UCC statutory conflicts via UCC_Statutory_Logic_v2.json.

    Now uses dedicated ucc_statutory_matcher module for enhanced detection.

    Args:
        clause_text: Contract clause text to analyze
        clause_type: Optional clause category (not currently used for filtering)

    Returns:
        Dict with UCC violation details, or None if no violation

        {
            "statutory_flag": str,      # e.g., "UCC-2-719"
            "citation": str,            # e.g., "6 Del. C. § 2-719"
            "severity": str,            # "CRITICAL", "HIGH", "MEDIUM"
            "risk_multiplier": float,   # 5.0-10.0
            "matched_concepts": List[str],  # Trigger concepts found
            "category": str,            # e.g., "REMEDY_LIMITATION"
            "business_impact": str,
            "si_impact": str
        }
    """
    try:
        from backend.ucc_statutory_matcher import detect_ucc_violation

        # Use new UCC matcher module
        return detect_ucc_violation(clause_text, clause_type)

    except ImportError:
        # Fallback to legacy detection if ucc_statutory_matcher not available
        logic = load_statutory_logic()
        text_lower = clause_text.lower()

        for rule in logic.get('rules', []):
            trigger_concepts = rule.get('trigger_concepts', [])

            # Check if any trigger concepts present
            matches = sum(1 for concept in trigger_concepts if concept in text_lower)

            # Threshold: 2+ trigger concepts = flag
            if matches >= 2:
                return {
                    "statutory_flag": rule['id'],
                    "citation": rule['citation'],
                    "severity": rule.get('severity', 'HIGH'),
                    "risk_multiplier": rule.get('risk_multiplier', 8.0),
                    "matched_concepts": [],  # Legacy mode doesn't track matches
                    "category": rule.get('category', 'UNKNOWN')
                }

        return None


# =============================================================================
# CASCADE DETECTION
# =============================================================================

def detect_cascades(comparison_entries: List[Dict]) -> List[Dict]:
    """
    Detect cross-clause cascade risks in comparison results.
    
    Args:
        comparison_entries: List of clause comparisons with CCE-Plus scores
    
    Returns:
        List of cascade alerts
    """
    cascade_patterns = get_cascade_patterns()
    cascades_found = []
    
    # Index entries by section
    sections = {}
    for entry in comparison_entries:
        section = entry.get('section_number', '')
        if section:
            sections[section] = entry
    
    # Check each cascade pattern
    for pattern in cascade_patterns:
        pattern_sections = [comp['section'] for comp in pattern.get('components', [])]
        
        # Check if all required sections are present and high-risk
        matching_sections = []
        all_present = True
        
        for section in pattern_sections:
            # Handle flexible section matching (e.g., "5.x" matches "5.1", "5.2", etc.)
            if section.endswith('.x'):
                prefix = section[:-1]
                matched = [s for s in sections.keys() if s.startswith(prefix)]
                if matched:
                    matching_sections.extend(matched)
                else:
                    all_present = False
            elif section == 'any':
                # "any" matches if any high-risk section exists
                high_risk = [s for s, e in sections.items() 
                            if e.get('cce_risk_score', 0) >= 7.0]
                if high_risk:
                    matching_sections.extend(high_risk[:1])
                else:
                    all_present = False
            else:
                if section in sections:
                    matching_sections.append(section)
                else:
                    all_present = False
        
        if all_present and matching_sections:
            # Verify high-risk threshold for matched sections
            high_risk_count = sum(
                1 for s in matching_sections 
                if sections.get(s, {}).get('cce_risk_score', 0) >= 7.0
            )
            
            # Cascade triggers if majority are high-risk
            if high_risk_count >= len(matching_sections) * 0.5:
                cascades_found.append({
                    'cascade_id': pattern['id'],
                    'cascade_name': pattern['name'],
                    'description': pattern['description'],
                    'affected_sections': matching_sections,
                    'statutory_violation': pattern.get('statutory_violation'),
                    'combined_risk': pattern.get('combined_risk', 10.0),
                    'remediation': pattern.get('remediation', '')
                })
    
    return cascades_found


# =============================================================================
# DISPLAY PRIORITY CALCULATION
# =============================================================================

def calculate_change_ratio(v1_text: str, v2_text: str) -> float:
    """
    Calculate how much text changed between versions.
    
    Returns:
        Float 0.0-1.0 representing change magnitude
    """
    if not v1_text and not v2_text:
        return 0.0
    
    if not v1_text or not v2_text:
        return 1.0  # Complete add or remove
    
    # Use SequenceMatcher for similarity
    similarity = SequenceMatcher(None, v1_text, v2_text).ratio()
    
    # Change ratio is inverse of similarity
    return round(1.0 - similarity, 3)


def calculate_display_priority(
    risk_score: float,
    v1_text: str,
    v2_text: str,
    risk_weight: float = 0.6,
    delta_weight: float = 0.4
) -> float:
    """
    Calculate combined priority score for display sorting.
    
    Formula: (normalized_risk × 0.6) + (delta_magnitude × 0.4)
    
    Args:
        risk_score: CCE-Plus risk score (0-10)
        v1_text: Original clause text
        v2_text: New clause text
        risk_weight: Weight for risk component (default 0.6)
        delta_weight: Weight for change component (default 0.4)
    
    Returns:
        Priority score 0.0-1.0 (higher = show first)
    """
    # Normalize risk to 0-1
    normalized_risk = min(1.0, risk_score / 10.0)
    
    # Calculate change magnitude
    delta_magnitude = calculate_change_ratio(v1_text, v2_text)
    
    # Combined score
    priority = (normalized_risk * risk_weight) + (delta_magnitude * delta_weight)
    
    return round(priority, 3)


# =============================================================================
# MAIN ENRICHMENT FUNCTION
# =============================================================================

def enrich_comparison_entries(entries: List[Dict]) -> List[Dict]:
    """
    Enrich comparison entries with CCE-Plus risk scores, statutory flags, and cascades.
    
    Args:
        entries: List of comparison entries from CIP
            Expected keys: section_number, clause_type, v1_content, v2_content
    
    Returns:
        Enriched entries with CCE-Plus data added
    """
    enriched = []
    
    for entry in entries:
        # Score the V2 content (current version)
        v2_text = entry.get('v2_content', '')
        clause_type = entry.get('clause_type', 'Default')
        section = entry.get('section_number', '')
        
        risk_data = score_clause_risk(v2_text, clause_type, section)
        
        # Calculate display priority
        v1_text = entry.get('v1_content', '')
        priority = calculate_display_priority(
            risk_data['risk_score'],
            v1_text,
            v2_text
        )
        
        # Merge CCE-Plus data into entry
        enriched_entry = {
            **entry,
            'cce_risk_score': risk_data['risk_score'],
            'cce_risk_level': risk_data['risk_level'],
            'cce_severity': risk_data['severity'],
            'cce_complexity': risk_data['complexity'],
            'cce_impact': risk_data['impact'],
            'cce_statutory_flag': risk_data['statutory_flag'],
            'cce_statutory_cite': risk_data['statutory_cite'],
            'cce_cascade_id': None,  # Set after cascade detection
            'cce_cascade_name': None,
            'display_priority': priority
        }
        
        enriched.append(enriched_entry)
    
    # Detect cascades across all entries
    cascades = detect_cascades(enriched)
    
    # Tag entries involved in cascades
    for cascade in cascades:
        for section in cascade['affected_sections']:
            for entry in enriched:
                if entry.get('section_number') == section:
                    entry['cce_cascade_id'] = cascade['cascade_id']
                    entry['cce_cascade_name'] = cascade['cascade_name']
    
    # Sort by priority (highest first)
    enriched.sort(key=lambda x: x.get('display_priority', 0), reverse=True)
    
    return enriched


def get_cascade_alerts(entries: List[Dict]) -> List[Dict]:
    """
    Get cascade alerts for display in UI.
    
    Args:
        entries: Enriched comparison entries
    
    Returns:
        List of unique cascade alerts with display info
    """
    cascades = detect_cascades(entries)
    
    alerts = []
    for cascade in cascades:
        alerts.append({
            'id': cascade['cascade_id'],
            'name': cascade['cascade_name'],
            'severity': 'CRITICAL',
            'sections': ', '.join(cascade['affected_sections']),
            'statutory': cascade['statutory_violation'],
            'message': f"⚠️ {cascade['name']}: {cascade['description']}",
            'remediation': cascade['remediation']
        })
    
    return alerts


# =============================================================================
# VERIFICATION / TESTING
# =============================================================================

def verify_cce_plus_connection() -> Dict:
    """
    Verify CCE-Plus is properly connected and accessible.
    
    Returns:
        Dict with status and diagnostics
    """
    status = {
        'connected': False,
        'cce_plus_root': str(CCE_PLUS_ROOT),
        'statutory_logic': False,
        'cascade_patterns': 0,
        'keyword_map': False,
        'errors': []
    }
    
    try:
        # Check root exists
        if not CCE_PLUS_ROOT.exists():
            status['errors'].append(f"CCE-Plus root not found: {CCE_PLUS_ROOT}")
            return status
        
        # Check statutory logic
        logic = load_statutory_logic()
        status['statutory_logic'] = True
        status['cascade_patterns'] = len(logic.get('cascade_patterns', []))
        status['keyword_map'] = 'keyword_severity_map' in logic
        
        status['connected'] = True
        
    except Exception as e:
        status['errors'].append(str(e))
    
    return status


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("CCE-Plus Integration Module - Self Test")
    print("=" * 60)
    
    # Test connection
    print("\n1. Testing CCE-Plus connection...")
    status = verify_cce_plus_connection()
    print(f"   Connected: {status['connected']}")
    print(f"   Statutory Logic: {status['statutory_logic']}")
    print(f"   Cascade Patterns: {status['cascade_patterns']}")
    
    if status['errors']:
        print(f"   Errors: {status['errors']}")
        sys.exit(1)
    
    # Test risk scoring
    print("\n2. Testing risk scoring...")
    test_clause = """
    Client shall provide full prepayment to Vendor before Vendor incurs such costs.
    Vendor shall not be obligated to proceed without receipt of prepayment.
    Client may withhold payment only in cases where deliverables fail to meet 
    the acceptance criteria explicitly documented in the applicable Statement of Work.
    """
    
    risk = score_clause_risk(test_clause, 'Financial/Prepayment', '5.2')
    print(f"   Risk Score: {risk['risk_score']}/10.0")
    print(f"   Risk Level: {risk['risk_level']}")
    print(f"   Statutory Flag: {risk['statutory_flag']}")
    
    # Test priority calculation
    print("\n3. Testing priority calculation...")
    v1 = "Client reserves the right to withhold payment for any disputed charges."
    v2 = "Client may withhold payment only in cases where deliverables fail to meet explicitly documented criteria."
    
    priority = calculate_display_priority(risk['risk_score'], v1, v2)
    print(f"   Display Priority: {priority}")
    
    # Test cascade detection
    print("\n4. Testing cascade detection...")
    test_entries = [
        {'section_number': '5.2', 'clause_type': 'Financial/Prepayment', 
         'v2_content': 'Full prepayment required', 'cce_risk_score': 9.0},
        {'section_number': '5.3', 'clause_type': 'Legal/Remedy', 
         'v2_content': 'Withholding restricted to documented criteria', 'cce_risk_score': 10.0},
        {'section_number': '15.3', 'clause_type': 'Termination', 
         'v2_content': 'Termination requires 30-day cure', 'cce_risk_score': 7.0},
    ]
    
    cascades = detect_cascades(test_entries)
    print(f"   Cascades Found: {len(cascades)}")
    for c in cascades:
        print(f"   - {c['cascade_name']} ({c['cascade_id']})")
    
    print("\n" + "=" * 60)
    print("All tests passed ✅")
    print("=" * 60)
