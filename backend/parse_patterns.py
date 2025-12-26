#!/usr/bin/env python3
"""
Pattern Library Parser
Extracts negotiation patterns from markdown into structured JSON
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional


class PatternParser:
    """Parse pattern library markdown file"""

    def __init__(self, md_file_path: str):
        self.md_file_path = Path(md_file_path)
        with open(self.md_file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

        self.patterns: List[Dict] = []
        self.current_category = None

    def parse(self) -> List[Dict]:
        """Extract all patterns from markdown"""

        # Split into sections by ## headers (category level)
        sections = re.split(r'^## (.+)$', self.content, flags=re.MULTILINE)

        for i in range(1, len(sections), 2):
            category_name = sections[i].strip()
            category_content = sections[i + 1] if i + 1 < len(sections) else ""

            # Skip meta sections
            if any(skip in category_name.upper() for skip in [
                'APPLICATION NOTES', 'SUCCESS RATE CALIBRATION',
                'ENHANCED DEALBREAKER', 'STRATEGIC POSITIONING'
            ]):
                continue

            # Extract patterns from this category
            self.parse_category(category_name, category_content)

        print(f"[INFO] Extracted {len(self.patterns)} patterns from {self.md_file_path.name}")
        return self.patterns

    def parse_category(self, category_name: str, content: str):
        """Parse all patterns within a category"""

        # Split by ### headers (pattern level)
        pattern_sections = re.split(r'^### (.+)$', content, flags=re.MULTILINE)

        for i in range(1, len(pattern_sections), 2):
            pattern_name = pattern_sections[i].strip()
            pattern_content = pattern_sections[i + 1] if i + 1 < len(pattern_sections) else ""

            pattern = self.parse_pattern(category_name, pattern_name, pattern_content)
            if pattern:
                self.patterns.append(pattern)

    def parse_pattern(self, category: str, name: str, content: str) -> Optional[Dict]:
        """Extract structured data from a single pattern"""

        pattern = {
            'category': category,
            'name': name,
            'problem': '',
            'position': '',
            'leverage': '',
            'revision': '',
            'success_rate': 0.0,
            'success_rate_text': '',
            'business_context': '',
            'strategic_note': '',
            'keywords': set(),
        }

        # Extract problem
        problem_match = re.search(r'\*\*Original Problem:\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
        if problem_match:
            pattern['problem'] = problem_match.group(1).strip()

        # Extract when clause (for protective patterns)
        when_match = re.search(r'\*\*When:\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
        if when_match:
            pattern['problem'] = when_match.group(1).strip()
            pattern['position'] = 'Any'
            pattern['leverage'] = 'Protective'

        # Extract position/leverage
        pos_lev_match = re.search(r'\*\*Position/Leverage:\*\*\s*(.+?)(?=\n|\Z)', content)
        if pos_lev_match:
            pos_lev = pos_lev_match.group(1).strip()
            parts = pos_lev.split('/')
            if len(parts) >= 2:
                pattern['position'] = parts[0].strip()
                pattern['leverage'] = parts[1].strip()

        # Extract revision (handles both Revision: and Add:)
        revision_match = re.search(r'\*\*(?:Revision|Add):\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
        if revision_match:
            revision = revision_match.group(1).strip()
            # Clean up markdown formatting
            revision = re.sub(r'~~(.+?)~~', r'\1 [DELETE]', revision)  # Strikethrough
            revision = re.sub(r'`([^`]+)`', r'\1', revision)  # Backticks
            pattern['revision'] = revision

        # Extract success rate
        success_match = re.search(r'\*\*Success Rate:\*\*\s*(.+?)(?=\n|\Z)', content)
        if success_match:
            success_text = success_match.group(1).strip()
            pattern['success_rate_text'] = success_text

            # Extract numeric success rate (first percentage found)
            percent_match = re.search(r'(\d+)%', success_text)
            if percent_match:
                pattern['success_rate'] = int(percent_match.group(1)) / 100.0

        # Extract business context
        context_match = re.search(r'\*\*Business Context:\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
        if context_match:
            pattern['business_context'] = context_match.group(1).strip()

        # Extract strategic note
        strategic_match = re.search(r'\*\*Strategic Note:\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
        if strategic_match:
            pattern['strategic_note'] = strategic_match.group(1).strip()

        # Extract note
        note_match = re.search(r'\*\*Note:\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
        if note_match:
            pattern['strategic_note'] = str(pattern['strategic_note']) + ' ' + note_match.group(1).strip()

        # Generate keywords for matching
        pattern['keywords'] = self.extract_keywords(pattern)

        return pattern

    def extract_keywords(self, pattern: Dict) -> List[str]:
        """Generate keywords for fast pattern matching"""
        keywords = set()

        # From category
        keywords.add(pattern['category'].lower())

        # From name
        for word in pattern['name'].lower().split():
            if len(word) > 3:
                keywords.add(word)

        # From problem
        problem_words = re.findall(r'\b[a-z]{4,}\b', pattern['problem'].lower())
        keywords.update(problem_words[:10])  # Top 10 words

        # Key legal terms
        legal_terms = [
            'liability', 'indemnification', 'termination', 'payment',
            'assignment', 'exclusivity', 'confidentiality', 'warranty',
            'limitation', 'damages', 'breach', 'notice', 'cure',
            'mutual', 'sole', 'discretion', 'reasonable', 'fees'
        ]
        for term in legal_terms:
            if term in pattern['problem'].lower() or term in pattern['revision'].lower():
                keywords.add(term)

        return list(keywords)

    def save_json(self, output_path: str):
        """Save patterns to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert sets to lists for JSON serialization
        patterns_json = []
        for p in self.patterns:
            pattern_copy = p.copy()
            pattern_copy['keywords'] = list(pattern_copy['keywords']) if isinstance(pattern_copy['keywords'], set) else pattern_copy['keywords']
            patterns_json.append(pattern_copy)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(patterns_json, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] {len(patterns_json)} patterns to {output_file}")


if __name__ == "__main__":
    # Parse pattern library
    parser = PatternParser('C:/Users/jrudy/CIP/knowledge/02_CLAUSE_PATTERN_LIBRARY_v1.2.md')
    patterns = parser.parse()

    # Display statistics
    print(f"\n{'='*60}")
    print(f"PATTERN LIBRARY STATISTICS")
    print(f"{'='*60}")
    print(f"Total Patterns: {len(patterns)}")

    # Count by category
    categories: Dict[str, int] = {}
    for p in patterns:
        cat = p['category']
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nBy Category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Average success rate
    avg_success = sum(p['success_rate'] for p in patterns) / len(patterns) if patterns else 0
    print(f"\nAverage Success Rate: {avg_success:.1%}")

    # Save to JSON
    parser.save_json('C:/Users/jrudy/CIP/backend/data/patterns.json')

    print(f"\n{'='*60}")
    print(f"SAMPLE PATTERNS")
    print(f"{'='*60}")
    for pattern in patterns[:3]:
        print(f"\nPattern: {pattern['name']}")
        print(f"Category: {pattern['category']}")
        print(f"Success Rate: {pattern['success_rate']:.0%}")
        print(f"Keywords: {', '.join(pattern['keywords'][:5])}")
