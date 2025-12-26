#!/usr/bin/env python3
"""
Redline Analyzer
Analyzes single contract and generates minimal revision suggestions with visual redlines
"""

import anthropic
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import json

# Import config
try:
    from config import ANTHROPIC_API_KEY, DEFAULT_MODEL
except ImportError:
    print("[WARN] config.py not found, falling back to environment variables")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    DEFAULT_MODEL = "claude-sonnet-4-20250514"


class RevisionValidator:
    """Validates that revisions follow minimal revision principle"""

    @staticmethod
    def calculate_change_metrics(original: str, revised: str) -> Dict:
        """
        Calculate change metrics for minimal revision validation

        Returns:
            {
                'change_ratio': float (0.0-1.0),
                'word_retention': float (0.0-1.0),
                'char_change_ratio': float (0.0-1.0),
                'is_minimal': bool
            }
        """
        # Tokenize into words
        original_words = set(original.lower().split())
        revised_words = set(revised.lower().split())

        # Word retention rate
        retained_words = original_words & revised_words
        word_retention = len(retained_words) / len(original_words) if original_words else 0.0

        # Character-level change ratio
        matcher = SequenceMatcher(None, original, revised)
        char_change_ratio = 1.0 - matcher.ratio()

        # Overall change ratio (based on edit distance)
        change_ratio = char_change_ratio

        # Minimal revision check: <40% change AND >60% word retention
        is_minimal = change_ratio < 0.40 and word_retention > 0.60

        return {
            'change_ratio': change_ratio,
            'word_retention': word_retention,
            'char_change_ratio': char_change_ratio,
            'is_minimal': is_minimal
        }

    @staticmethod
    def generate_html_redline(original: str, revised: str) -> str:
        """
        Generate HTML redline showing deletions and insertions

        Deletions: <span style="color:red;text-decoration:line-through;">text</span>
        Insertions: <span style="color:green;font-weight:bold;">text</span>
        """
        # Use SequenceMatcher to find differences
        matcher = SequenceMatcher(None, original, revised)

        html_parts = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged text
                html_parts.append(original[i1:i2])
            elif tag == 'delete':
                # Deleted text (red strikethrough)
                deleted = original[i1:i2]
                html_parts.append(f'<span style="color:red;text-decoration:line-through;">{deleted}</span>')
            elif tag == 'insert':
                # Inserted text (green bold)
                inserted = revised[j1:j2]
                html_parts.append(f'<span style="color:green;font-weight:bold;">{inserted}</span>')
            elif tag == 'replace':
                # Replaced text (deletion + insertion)
                deleted = original[i1:i2]
                inserted = revised[j1:j2]
                html_parts.append(f'<span style="color:red;text-decoration:line-through;">{deleted}</span>')
                html_parts.append(f'<span style="color:green;font-weight:bold;">{inserted}</span>')

        return ''.join(html_parts)


class RedlineAnalyzer:
    """Analyze single contract and generate suggested redlines"""

    REDLINE_GENERATION_PROMPT = """You are a contract negotiation expert. Analyze this contract clause and suggest a MINIMAL revision that addresses risks while preserving as much original language as possible.

CRITICAL CONSTRAINTS:
- Change <40% of the text
- Retain >60% of the original words
- Make only necessary changes
- Preserve structure and formatting
- Focus on high-impact modifications

CONTRACT CONTEXT:
Position: {position}
Leverage: {leverage}
Contract Type: {contract_type}

CLAUSE TO ANALYZE:
Section: {section_title}
Text: {clause_text}

PATTERN LIBRARY MATCHES:
{pattern_matches}

INSTRUCTIONS:
1. Identify the primary risk in this clause
2. Suggest a MINIMAL revision that addresses the risk
3. Ensure your revision changes <40% of the original text
4. Ensure your revision retains >60% of the original words
5. Return ONLY the revised clause text (no explanations)

REVISED CLAUSE:"""

    CLAUSE_ANALYSIS_PROMPT = """You are a contract analysis expert. Break down this contract into analyzable clauses.

CONTRACT TEXT:
{contract_text}

INSTRUCTIONS:
Return a JSON array of clauses with this structure:
[
  {{
    "section_number": "1.1",
    "section_title": "Definitions",
    "clause_text": "The full text of the clause...",
    "risk_level": "LOW|MEDIUM|HIGH",
    "risk_summary": "Brief description of risk"
  }}
]

Return ONLY valid JSON, no explanations."""

    def __init__(self, patterns_json_path: Optional[str] = None):
        """Initialize analyzer with pattern library"""
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = DEFAULT_MODEL

        # Load pattern library
        if patterns_json_path is None:
            patterns_json_path = Path(__file__).parent / 'data' / 'patterns.json'

        with open(patterns_json_path, 'r', encoding='utf-8') as f:
            self.patterns = json.load(f)

        print(f"[INIT] RedlineAnalyzer loaded with {len(self.patterns)} patterns")

    def analyze_document(self, contract_text: str, context: Dict) -> List[Dict]:
        """
        Main pipeline: Analyze document and generate redline suggestions

        Args:
            contract_text: Full contract text
            context: {position, leverage, contract_type}

        Returns:
            List of clause dictionaries with redline suggestions
        """
        print("[STEP 1] Parsing contract into clauses...")
        clauses = self.parse_into_clauses(contract_text)
        print(f"[STEP 1] Found {len(clauses)} clauses")

        print("[STEP 2] Analyzing each clause and generating redlines...")
        results = []

        for idx, clause in enumerate(clauses, 1):
            print(f"[STEP 2] Analyzing clause {idx}/{len(clauses)}: {clause.get('section_title', 'Unknown')}")

            # Match patterns
            pattern_matches = self.match_patterns(clause, context)

            # Generate minimal revision
            if clause.get('risk_level') in ['MEDIUM', 'HIGH']:
                revision_result = self.generate_minimal_revision(clause, context, pattern_matches)

                if revision_result:
                    clause.update(revision_result)

            results.append(clause)

        print(f"[COMPLETE] Generated {sum(1 for c in results if c.get('suggested_revision'))} redline suggestions")
        return results

    def parse_into_clauses(self, contract_text: str) -> List[Dict]:
        """Parse contract into individual clauses using Claude"""

        prompt = self.CLAUSE_ANALYSIS_PROMPT.format(contract_text=contract_text[:15000])

        try:
            print(f"[DEBUG] About to call Claude API for clause parsing")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Prompt length: {len(prompt)}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            print(f"[DEBUG] Response received, type: {type(response)}")
            print(f"[DEBUG] Response has content: {hasattr(response, 'content')}")

            if hasattr(response, 'content') and len(response.content) > 0:
                response_text = response.content[0].text.strip()
            else:
                print(f"[ERROR] Response structure unexpected: {response}")
                return self.fallback_clause_parser(contract_text)

            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                clauses = json.loads(json_match.group(0))
                return clauses
            else:
                print("[WARN] No JSON found in Claude response, using fallback parser")
                return self.fallback_clause_parser(contract_text)

        except Exception as e:
            import traceback
            print(f"[ERROR] Clause parsing failed: {e}")
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()
            return self.fallback_clause_parser(contract_text)

    def fallback_clause_parser(self, contract_text: str) -> List[Dict]:
        """Simple fallback parser if Claude parsing fails"""
        # Split by common section patterns
        sections = re.split(r'\n\s*(\d+\.[\d\.]*\s+[A-Z][^\n]+)', contract_text)

        clauses = []
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                title = sections[i].strip()
                text = sections[i + 1].strip()

                clauses.append({
                    'section_number': re.match(r'(\d+\.[\d\.]*)', title).group(1) if re.match(r'(\d+\.[\d\.]*)', title) else str(i),
                    'section_title': title,
                    'clause_text': text,
                    'risk_level': 'MEDIUM',
                    'risk_summary': 'Requires review'
                })

        return clauses if clauses else [{'section_number': '1', 'section_title': 'Full Contract', 'clause_text': contract_text, 'risk_level': 'MEDIUM', 'risk_summary': 'Full document review'}]

    def match_patterns(self, clause: Dict, context: Dict) -> List[Dict]:
        """Match clause against pattern library"""
        clause_text = (
            clause.get('section_title', '') + ' ' +
            clause.get('clause_text', '') + ' ' +
            clause.get('risk_summary', '')
        ).lower()

        # Extract keywords from clause
        clause_keywords = set(re.findall(r'\b[a-z]{4,}\b', clause_text))

        # Find matching patterns
        matches = []
        for pattern in self.patterns:
            pattern_keywords = set(pattern.get('keywords', []))
            overlap = clause_keywords & pattern_keywords

            if len(overlap) >= 1:  # At least 1 keyword match
                # Calculate similarity
                pattern_text = (pattern.get('name', '') + ' ' + pattern.get('problem', '')).lower()
                similarity = SequenceMatcher(None, clause_text, pattern_text).ratio()

                # Check context match
                position_match = self.check_context_match(pattern, context)

                if position_match and similarity > 0.1:
                    matches.append({
                        'pattern_name': pattern.get('name', ''),
                        'pattern_category': pattern.get('category', ''),
                        'success_rate': pattern.get('success_rate', 0.0),
                        'revision_template': pattern.get('revision', ''),
                        'business_context': pattern.get('business_context', ''),
                        'similarity': similarity
                    })

        # Return top 3 matches
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:3]

    def check_context_match(self, pattern: Dict, context: Dict) -> bool:
        """Check if pattern matches position/leverage context"""
        pattern_position = pattern.get('position', 'Any')
        pattern_leverage = pattern.get('leverage', 'Any')

        position = context.get('position', 'Unknown')
        leverage = context.get('leverage', 'Unknown')

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

        return position_match and leverage_match

    def generate_minimal_revision(self, clause: Dict, context: Dict, pattern_matches: List[Dict]) -> Optional[Dict]:
        """
        Generate minimal revision for clause using Claude

        Returns:
            {
                'suggested_revision': str,
                'html_redline': str,
                'change_metrics': dict,
                'pattern_applied': str,
                'revision_rationale': str
            }
        """
        # Format pattern matches for prompt
        pattern_text = ""
        if pattern_matches:
            pattern_text = "\n".join([
                f"- {p['pattern_name']} (Success: {p['success_rate']:.0%})\n  Template: {p['revision_template'][:200]}"
                for p in pattern_matches
            ])
        else:
            pattern_text = "No specific patterns matched. Use general contract negotiation principles."

        prompt = self.REDLINE_GENERATION_PROMPT.format(
            position=context.get('position', 'Unknown'),
            leverage=context.get('leverage', 'Unknown'),
            contract_type=context.get('contract_type', 'Unknown'),
            section_title=clause.get('section_title', 'Unknown'),
            clause_text=clause.get('clause_text', ''),
            pattern_matches=pattern_text
        )

        try:
            print(f"[DEBUG] Generating revision for clause: {clause.get('section_title', 'Unknown')}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            print(f"[DEBUG] Revision response received, type: {type(response)}")

            if hasattr(response, 'content') and len(response.content) > 0:
                suggested_revision = response.content[0].text.strip()
            else:
                print(f"[ERROR] Invalid response structure for revision")
                return None

            original_text = clause.get('clause_text', '')

            # Validate minimality
            metrics = RevisionValidator.calculate_change_metrics(original_text, suggested_revision)

            if not metrics['is_minimal']:
                print(f"[WARN] Revision not minimal (change: {metrics['change_ratio']:.1%}, retention: {metrics['word_retention']:.1%})")
                # Try to use pattern template directly for more minimal change
                if pattern_matches and pattern_matches[0].get('revision_template'):
                    suggested_revision = self.apply_pattern_minimally(original_text, pattern_matches[0])
                    metrics = RevisionValidator.calculate_change_metrics(original_text, suggested_revision)

            # Generate HTML redline
            html_redline = RevisionValidator.generate_html_redline(original_text, suggested_revision)

            return {
                'suggested_revision': suggested_revision,
                'html_redline': html_redline,
                'change_metrics': metrics,
                'pattern_applied': pattern_matches[0]['pattern_name'] if pattern_matches else 'General Review',
                'revision_rationale': clause.get('risk_summary', 'Risk mitigation'),
                'status': 'pending'  # ✏️ pending, ✅ approved, ❌ rejected, ⏭️ skipped
            }

        except Exception as e:
            import traceback
            print(f"[ERROR] Revision generation failed: {e}")
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()
            return None

    def apply_pattern_minimally(self, original_text: str, pattern: Dict) -> str:
        """Apply pattern template to original text with minimal changes"""
        template = pattern.get('revision_template', '')

        # Simple strategy: Try to inject pattern language into original text
        # This is a fallback - Claude should do better

        # For now, just return the template (Claude version is better)
        return template if template else original_text


if __name__ == "__main__":
    # Test RedlineAnalyzer
    analyzer = RedlineAnalyzer()

    # Sample contract clause
    test_contract = """
1. TERMINATION FOR CONVENIENCE

Company may terminate this Agreement at any time, for any reason or no reason, upon fifteen (15) days' written notice to Vendor. Upon termination, Vendor shall immediately cease all work and return all Company materials. No fees shall be owed for work not completed as of the termination date.

2. LIMITATION OF LIABILITY

IN NO EVENT SHALL COMPANY BE LIABLE TO VENDOR FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF OR RELATED TO THIS AGREEMENT, REGARDLESS OF THE FORM OF ACTION AND WHETHER OR NOT COMPANY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. COMPANY'S TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID BY COMPANY IN THE THREE (3) MONTHS PRECEDING THE CLAIM.
"""

    context = {
        'position': 'Vendor',
        'leverage': 'Moderate',
        'contract_type': 'Services Agreement'
    }

    print(f"\n{'='*70}")
    print("REDLINE ANALYZER TEST")
    print(f"{'='*70}\n")

    results = analyzer.analyze_document(test_contract, context)

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}\n")

    for clause in results:
        print(f"\nSection: {clause.get('section_title', 'Unknown')}")
        print(f"Risk: {clause.get('risk_level', 'Unknown')}")

        if clause.get('suggested_revision'):
            print(f"\nPattern Applied: {clause.get('pattern_applied', 'None')}")
            metrics = clause.get('change_metrics', {})
            print(f"Change Ratio: {metrics.get('change_ratio', 0):.1%}")
            print(f"Word Retention: {metrics.get('word_retention', 0):.1%}")
            print(f"Is Minimal: {metrics.get('is_minimal', False)}")
            print(f"\nHTML Redline Preview:")
            print(clause.get('html_redline', 'None')[:300] + "...")
        else:
            print("No revision suggested")

        print(f"\n{'-'*70}")
