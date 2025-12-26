#!/usr/bin/env python3
"""
Pattern Matcher (DEPRECATED)
Matches contract changes to negotiation patterns from library

DEPRECATION NOTICE (2025-11-27):
    This module uses the legacy prefix-based pattern format (e.g., LOL-1, TER-2).
    It has been superseded by prompt_composer.py which uses the new hierarchical
    pattern deck format (e.g., 2.1.1, 3.7.2) from deck_v2_phase2.json.

    For new development, use:
        from prompt_composer import PromptComposer, create_composer
        from config import get_prompt_composer_config

    This module is retained for backward compatibility with comparison tools
    but should not be used for new analysis workflows.

See Also:
    - prompt_composer.py: New pattern selection and prompt composition
    - CCE/memory/patterns/deck_v2_phase2.json: 59-pattern deck (v2.0)
    - config.py: get_prompt_composer_config() for new pattern settings
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from difflib import SequenceMatcher


class PatternMatcher:
    """Match contract changes to negotiation patterns"""

    def __init__(self, patterns_json_path: Optional[Union[str, Path]] = None):
        """Load patterns from JSON file"""
        if patterns_json_path is None:
            patterns_json_path = Path(__file__).parent / 'data' / 'patterns.json'

        with open(patterns_json_path, 'r', encoding='utf-8') as f:
            self.patterns = json.load(f)

        print(f"[INIT] Loaded {len(self.patterns)} patterns for matching")

    def match_changes(self, changes: List[Dict], context: Dict) -> List[Dict]:
        """
        Match patterns to changes

        Args:
            changes: List of change dicts from comparison
            context: Position, leverage, contract type

        Returns:
            Changes enhanced with pattern_matches array
        """
        matched_count = 0

        for change in changes:
            # Stage 1: Keyword filtering
            candidates = self.keyword_filter(change)

            if not candidates:
                continue

            # Stage 2: Semantic ranking
            ranked = self.semantic_rank(candidates, change)

            # Stage 3: Context filtering
            relevant = self.context_filter(ranked, context)

            if relevant:
                # Add matches to change
                change['pattern_matches'] = relevant[:3]  # Top 3 matches
                matched_count += 1

        print(f"[MATCH] {matched_count}/{len(changes)} changes matched to patterns")
        return changes

    def keyword_filter(self, change: Dict) -> List[Dict]:
        """
        Stage 1: Fast keyword matching
        Returns patterns that share keywords with the change
        """
        # Extract keywords from change
        change_text = (
            change.get('section_title', '') + ' ' +
            change.get('reasoning', '') + ' ' +
            change.get('business_impact', '')
        ).lower()

        change_keywords = set(re.findall(r'\b[a-z]{4,}\b', change_text))

        # Find patterns with keyword overlap
        candidates = []
        for pattern in self.patterns:
            pattern_keywords = set(pattern.get('keywords', []))

            # Calculate overlap
            overlap = change_keywords & pattern_keywords
            if len(overlap) >= 2:  # At least 2 keywords in common
                candidates.append({
                    'pattern': pattern,
                    'keyword_score': len(overlap) / max(len(pattern_keywords), 1)
                })

        # Sort by keyword score
        candidates.sort(key=lambda x: x['keyword_score'], reverse=True)

        return [c['pattern'] for c in candidates[:10]]  # Top 10

    def semantic_rank(self, candidates: List[Dict], change: Dict) -> List[Dict]:
        """
        Stage 2: Semantic similarity scoring
        Ranks candidates by text similarity to change
        """
        change_text = (
            change.get('section_title', '') + ' ' +
            change.get('reasoning', '')
        ).lower()

        ranked: List[Dict[str, Any]] = []
        for pattern in candidates:
            pattern_text = (
                pattern.get('name', '') + ' ' +
                pattern.get('problem', '')
            ).lower()

            # Calculate similarity
            similarity: float = SequenceMatcher(None, change_text, pattern_text).ratio()

            ranked.append({
                'pattern': pattern,
                'similarity': similarity
            })

        # Sort by similarity
        ranked.sort(key=lambda x: float(x['similarity']), reverse=True)

        return [r['pattern'] for r in ranked[:5]]  # Top 5

    def context_filter(self, candidates: List[Dict], context: Dict) -> List[Dict]:
        """
        Stage 3: Filter by position/leverage context
        Adjusts success rates based on context
        """
        position = context.get('position', 'Unknown')
        leverage = context.get('leverage', 'Unknown')

        relevant = []
        for pattern in candidates:
            # Check if pattern applies to this position/leverage
            pattern_position = pattern.get('position', 'Any')
            pattern_leverage = pattern.get('leverage', 'Any')

            # Match logic
            position_match = (
                pattern_position == 'Any' or
                position == 'Unknown' or
                pattern_position.lower() in position.lower()
            )

            leverage_match = (
                pattern_leverage == 'Any' or
                leverage == 'Unknown' or
                pattern_leverage.lower() in leverage.lower()
            )

            if position_match and leverage_match:
                # Add with adjusted success rate
                pattern_match = {
                    'pattern_name': pattern.get('name', ''),
                    'pattern_category': pattern.get('category', ''),
                    'predicted_success_rate': pattern.get('success_rate', 0.0),
                    'revision_template': pattern.get('revision', ''),
                    'business_context': pattern.get('business_context', ''),
                    'strategic_note': pattern.get('strategic_note', ''),
                    'match_confidence': 0.8  # Fixed for now, could be calculated
                }

                relevant.append(pattern_match)

        return relevant

    def adjust_success_rate(self, base_rate: float, context: Dict) -> float:
        """
        Stage 4: Bayesian adjustment for context
        Adjusts success rate based on leverage and other factors
        """
        # Simple adjustment for now
        leverage = context.get('leverage', 'Moderate')

        multiplier = 1.0
        if leverage == 'Strong':
            multiplier = 1.15
        elif leverage == 'Weak':
            multiplier = 0.85

        return min(base_rate * multiplier, 1.0)


if __name__ == "__main__":
    # Test pattern matcher
    matcher = PatternMatcher()

    # Sample change
    test_change = {
        'section_title': 'Termination for Convenience',
        'reasoning': 'Company can terminate unilaterally with 15 day notice',
        'impact': 'HIGH_PRIORITY'
    }

    context = {
        'position': 'Service Provider',
        'leverage': 'Moderate'
    }

    # Match
    changes = matcher.match_changes([test_change], context)

    print(f"\n{'='*60}")
    print("PATTERN MATCHING TEST")
    print(f"{'='*60}")

    if changes[0].get('pattern_matches'):
        print(f"\nMatches found: {len(changes[0]['pattern_matches'])}")
        for match in changes[0]['pattern_matches']:
            print(f"\n- {match['pattern_name']}")
            print(f"  Category: {match['pattern_category']}")
            print(f"  Success: {match['predicted_success_rate']:.0%}")
            print(f"  Template: {match['revision_template'][:100]}...")
    else:
        print("\nNo matches found")
