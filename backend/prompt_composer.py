"""
Prompt Composer Module v1.1 (v1.3 Pattern Library Integration)
Assembles Claude prompts with selected pattern cards from deck_v3_phase3.json

Implements Gate 4 (Pattern Hand) from CIP ARCHITECTURE:
1. Mandatory patterns (dealbreakers for position)
2. Category-filtered patterns (by contract type)
3. Stage-filtered patterns (MNDA, NDA, COMMERCIAL, EXECUTED)
4. Status-filtered patterns (CONFIRMED, RESEARCH_NEEDED, etc.)
5. Ranked by success rate for position/leverage

v1.1 Changes:
    - Stage filtering: Excludes patterns with stage_restrictions matching current stage
    - Status filtering: Only CONFIRMED patterns by default (option to include others)
    - Escalation tracking: Flags patterns requiring CEO, LEGAL, or INSURANCE approval
    - Dealbreaker detection: Immediate flagging of DEALBREAKER status patterns

Integration:
    - Called by api.py /api/analyze endpoint
    - Composes system prompt passed to orchestrator.analyze_contract()
    - Saves prompts to contracts.db prompts table for audit trail

Configuration (from config.py):
    - PATTERN_DECK_PATH: Path to deck_v3_phase3.json
    - MAX_PATTERNS_PER_PROMPT: Default 15
    - PATTERN_TOKEN_CEILING: Default 1500
    - CONTRACT_CATEGORY_MAP: CIP contract_type to deck category mapping
    - CONTRACT_STAGES: Valid contract stages
    - PATTERN_STATUSES: Valid pattern statuses
    - ESCALATION_TYPES: Valid escalation types
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Use CIP logging convention
logger = logging.getLogger(__name__)


class PromptComposer:
    """Composes prompts with pattern card selection (v1.1 - v1.3 Pattern Library)."""

    def __init__(self, config: Dict):
        """
        Initialize composer with configuration.

        Args:
            config: Dict containing PATTERN_DECK_PATH, MAX_PATTERNS_PER_PROMPT,
                   PATTERN_TOKEN_CEILING, CONTRACT_CATEGORY_MAP, DB_PATH,
                   CONTRACT_STAGES, PATTERN_STATUSES, ESCALATION_TYPES
        """
        self.deck_path = config.get('PATTERN_DECK_PATH')
        self.max_patterns = config.get('MAX_PATTERNS_PER_PROMPT', 15)
        self.token_ceiling = config.get('PATTERN_TOKEN_CEILING', 1500)
        self.avg_tokens_per_card = config.get('PATTERN_COMPACT_AVG_TOKENS', 70)
        self.category_map = config.get('CONTRACT_CATEGORY_MAP', {})
        self.db_path = config.get('DB_PATH')

        # v1.3 additions
        self.valid_stages = config.get('CONTRACT_STAGES', ['MNDA', 'NDA', 'COMMERCIAL', 'EXECUTED'])
        self.valid_statuses = config.get('PATTERN_STATUSES', ['CONFIRMED', 'RESEARCH_NEEDED', 'DEALBREAKER', 'LEGAL_REVIEW'])
        self.valid_escalations = config.get('ESCALATION_TYPES', ['CEO', 'LEGAL', 'INSURANCE'])

        self.deck = self._load_deck()
        self.deck_version = self.deck.get('metadata', {}).get('deck_version', 'unknown')
        self.pattern_library_version = self.deck.get('metadata', {}).get('pattern_library_version', 'unknown')

    def _load_deck(self) -> Dict:
        """Load pattern deck from JSON file."""
        try:
            with open(self.deck_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load pattern deck: {e}")

    def select_patterns(
        self,
        contract_type: str,
        position: str,
        leverage: str,
        contract_stage: str = 'COMMERCIAL',
        include_research_needed: bool = False,
        contract_text: Optional[str] = None
    ) -> Tuple[List[Dict], Dict]:
        """
        Select relevant patterns using 5-stage filter (v1.1 - v1.3 Pattern Library).

        Stage 1: Status filter (CONFIRMED only by default, optionally include RESEARCH_NEEDED)
        Stage 2: Stage filter (exclude patterns restricted for current stage)
        Stage 3: Mandatory patterns (combined_triggers for dealbreakers)
        Stage 4: Category filter (contract_categories match)
        Stage 5: Rank by success rate for position/leverage

        Args:
            contract_type: CIP contract type (MSA, SOW, NDA, etc.)
            position: User position (customer, vendor, integrator, channel, reseller)
            leverage: Negotiation leverage (strong, balanced, weak)
            contract_stage: Current stage (MNDA, NDA, COMMERCIAL, EXECUTED)
            include_research_needed: Whether to include RESEARCH_NEEDED patterns
            contract_text: Optional contract text for keyword matching

        Returns:
            Tuple of (selected_cards, filter_metadata)
            - selected_cards: List of selected pattern cards, sorted by relevance
            - filter_metadata: Dict with filtering stats and escalations
        """
        # Map CIP contract_type to deck category
        category = self._map_category(contract_type)
        contract_stage = contract_stage.upper() if contract_stage else 'COMMERCIAL'

        cards = self.deck.get('cards', {})

        # Track filtering metadata
        filter_meta = {
            'total_cards': len(cards),
            'status_filtered': 0,
            'stage_filtered': 0,
            'category_matched': 0,
            'escalations_triggered': [],
            'dealbreakers_flagged': [],
            'applied_filters': {
                'status': ['CONFIRMED'] + (['RESEARCH_NEEDED'] if include_research_needed else []),
                'stage': contract_stage,
                'category': category,
                'position': position
            }
        }

        # Stage 1: Status filter
        status_passed = {}
        allowed_statuses = ['CONFIRMED']
        if include_research_needed:
            allowed_statuses.append('RESEARCH_NEEDED')

        for card_id, card in cards.items():
            card_status = card.get('v1_3_status', 'NOT_REVIEWED')

            # Always flag DEALBREAKER patterns
            if card_status == 'DEALBREAKER':
                filter_meta['dealbreakers_flagged'].append({
                    'id': card.get('id', card_id),
                    'name': card.get('name', 'Unknown'),
                    'user_notes': card.get('v1_3_user_notes')
                })
                continue

            # Check if status is allowed
            if card_status in allowed_statuses:
                status_passed[card_id] = card
            else:
                filter_meta['status_filtered'] += 1

        # Stage 2: Stage filter (exclude patterns with restrictions for current stage)
        stage_passed = {}
        for card_id, card in status_passed.items():
            stage_restrictions = card.get('stage_restrictions', [])

            # If current stage is in restrictions, exclude the pattern
            if contract_stage in stage_restrictions:
                filter_meta['stage_filtered'] += 1
                logger.debug(f"Pattern {card_id} excluded: stage restriction {contract_stage}")
                continue

            stage_passed[card_id] = card

            # Track escalations
            escalations = card.get('escalation', [])
            if escalations:
                filter_meta['escalations_triggered'].append({
                    'id': card.get('id', card_id),
                    'name': card.get('name', 'Unknown'),
                    'escalation_types': escalations,
                    'user_notes': card.get('v1_3_user_notes')
                })

        # Stage 3: Mandatory patterns (have combined_triggers - dealbreaker detection)
        mandatory = []
        for card_id, card in stage_passed.items():
            if card.get('combined_triggers'):
                mandatory.append(card)

        # Stage 4: Category filter
        category_matched = []
        for card_id, card in stage_passed.items():
            card_categories = card.get('contract_categories', [])
            if category in card_categories:
                # Also check position match
                card_positions = card.get('positions', [])
                if not card_positions or position in card_positions:
                    if card not in mandatory:
                        category_matched.append(card)
                        filter_meta['category_matched'] += 1

        # Stage 5: Rank by success rate
        def get_success_rate(card: Dict) -> float:
            rates = card.get('success_rates', {})
            # Try position_leverage specific rate first
            key = f"{position}_{leverage}"
            if key in rates:
                return rates[key]
            # Fall back to any_leverage
            fallback_key = f"any_{leverage}"
            if fallback_key in rates:
                return rates[fallback_key]
            # Default
            return card.get('confidence_score', 0.5)

        # Sort category-matched by success rate descending
        category_matched.sort(key=get_success_rate, reverse=True)

        # Combine: mandatory first, then ranked category matches
        selected = mandatory.copy()

        # Add category matches up to limit
        remaining_slots = self.max_patterns - len(selected)
        for card in category_matched[:remaining_slots]:
            if card not in selected:
                selected.append(card)

        # Enforce both max_patterns and token ceiling
        if len(selected) > self.max_patterns:
            selected = selected[:self.max_patterns]

        selected = self._enforce_token_limit(selected)

        logger.info(f"Pattern selection: {len(selected)} cards "
                   f"(stage={contract_stage}, status_filtered={filter_meta['status_filtered']}, "
                   f"stage_filtered={filter_meta['stage_filtered']}, "
                   f"escalations={len(filter_meta['escalations_triggered'])}, "
                   f"dealbreakers={len(filter_meta['dealbreakers_flagged'])})")

        return selected, filter_meta

    def _map_category(self, contract_type: str) -> str:
        """Map CIP contract_type to deck category letter."""
        # Normalize input
        ct = contract_type.upper().strip()

        # Direct mapping from config
        if ct in self.category_map:
            return self.category_map[ct]

        # Fallback heuristics
        if 'MSA' in ct or 'MASTER' in ct:
            return 'A'
        if 'MOU' in ct or 'LOI' in ct or 'INTENT' in ct:
            return 'B'
        if 'NDA' in ct or 'CONFIDENTIAL' in ct:
            return 'C'
        if 'SERVICE' in ct or 'SOW' in ct:
            return 'D'
        if 'PROJECT' in ct or 'DESIGN' in ct or 'BUILD' in ct:
            return 'E'
        if 'CHANNEL' in ct or 'RESELLER' in ct or 'PARTNER' in ct:
            return 'F'
        if 'BROKER' in ct or 'FACILITATOR' in ct:
            return 'G'

        # Default to MSA category
        return 'A'

    def _enforce_token_limit(self, cards: List[Dict]) -> List[Dict]:
        """Trim card list to stay within token ceiling."""
        estimated_tokens = len(cards) * self.avg_tokens_per_card

        while estimated_tokens > self.token_ceiling and len(cards) > 1:
            cards.pop()  # Remove lowest priority (last in list)
            estimated_tokens = len(cards) * self.avg_tokens_per_card

        return cards

    def card_to_prompt(self, card: Dict, position: str, leverage: str) -> str:
        """
        Convert storage card to compact prompt format (~70 tokens).

        Args:
            card: Full pattern card from deck
            position: User position
            leverage: Negotiation leverage

        Returns:
            Compact string representation for prompt injection
        """
        # Get position-specific success rate
        rates = card.get('success_rates', {})
        key = f"{position}_{leverage}"
        fallback_key = f"any_{leverage}"
        success = rates.get(key, rates.get(fallback_key, 0.5))

        # Get first talking point
        talking_points = card.get('talking_points', [])
        talking_point = talking_points[0] if talking_points else "N/A"

        # Get acceptable fallback
        fallbacks = card.get('fallbacks', {})
        fallback = fallbacks.get('acceptable', 'N/A')

        return f"""[{card['id']}] {card['name']}
Problem: {card['problem']}
Revision: {card['revision']}
Success: {int(success*100)}% ({leverage})
Fallback: {fallback}
Talking Point: {talking_point}"""

    def compose_prompt(
        self,
        contract_id: int,
        contract_type: str,
        position: str,
        leverage: str,
        contract_text: str,
        contract_stage: str = 'COMMERCIAL',
        include_research_needed: bool = False,
        base_system_prompt: str = ""
    ) -> Tuple[str, Dict]:
        """
        Compose full prompt with selected patterns (v1.1 - v1.3 Pattern Library).

        Args:
            contract_id: Database ID of contract
            contract_type: CIP contract type
            position: User position
            leverage: Negotiation leverage
            contract_text: Full contract text
            contract_stage: Current stage (MNDA, NDA, COMMERCIAL, EXECUTED)
            include_research_needed: Whether to include RESEARCH_NEEDED patterns
            base_system_prompt: Optional base system prompt to extend

        Returns:
            Tuple of (assembled_prompt, metadata_dict)
        """
        # Select patterns with v1.3 filtering
        selected, filter_meta = self.select_patterns(
            contract_type, position, leverage,
            contract_stage=contract_stage,
            include_research_needed=include_research_needed,
            contract_text=contract_text
        )

        # Build pattern section
        pattern_section = self._build_pattern_section(selected, position, leverage, filter_meta)

        # Assemble full prompt
        assembled = self._assemble_prompt(
            base_system_prompt,
            pattern_section,
            contract_type,
            position,
            leverage,
            contract_stage,
            filter_meta
        )

        # Calculate token estimate
        token_count = len(assembled) // 4  # Rough estimate

        # Build metadata with v1.3 additions
        metadata = {
            'contract_id': contract_id,
            'position': position,
            'leverage': leverage,
            'category': self._map_category(contract_type),
            'contract_stage': contract_stage,
            'selected_patterns': [c['id'] for c in selected],
            'pattern_count': len(selected),
            'token_count': token_count,
            'deck_version': self.deck_version,
            'pattern_library_version': self.pattern_library_version,
            # v1.3 filter metadata
            'escalations_triggered': filter_meta.get('escalations_triggered', []),
            'dealbreakers_flagged': filter_meta.get('dealbreakers_flagged', []),
            'status_filter_applied': json.dumps(filter_meta.get('applied_filters', {}).get('status', [])),
            'stage_filter_applied': contract_stage
        }

        # Save to database
        prompt_id = self._save_prompt(metadata, assembled)
        metadata['prompt_id'] = prompt_id

        return assembled, metadata

    def _build_pattern_section(
        self,
        cards: List[Dict],
        position: str,
        leverage: str,
        filter_meta: Optional[Dict] = None
    ) -> str:
        """Build the pattern cards section of the prompt (v1.1)."""
        if not cards:
            return ""

        lines = [
            "## APPLICABLE PATTERN CARDS",
            f"Position: {position.title()} | Leverage: {leverage.title()}",
            f"Patterns: {len(cards)} selected from deck v{self.deck_version} (Pattern Library v{self.pattern_library_version})",
            ""
        ]

        # Add escalation warnings if any
        if filter_meta and filter_meta.get('escalations_triggered'):
            lines.append("### ESCALATION REQUIRED")
            for esc in filter_meta['escalations_triggered']:
                esc_types = ', '.join(esc['escalation_types'])
                lines.append(f"- [{esc['id']}] {esc['name']}: Requires {esc_types} approval")
            lines.append("")

        # Add dealbreaker warnings if any
        if filter_meta and filter_meta.get('dealbreakers_flagged'):
            lines.append("### DEALBREAKER ALERT")
            for db in filter_meta['dealbreakers_flagged']:
                lines.append(f"- [{db['id']}] {db['name']}: {db.get('user_notes', 'No notes')}")
            lines.append("")

        for card in cards:
            lines.append(self.card_to_prompt(card, position, leverage))
            lines.append("")  # Blank line between cards

        return "\n".join(lines)

    def _assemble_prompt(
        self,
        base_prompt: str,
        pattern_section: str,
        contract_type: str,
        position: str,
        leverage: str,
        contract_stage: str = 'COMMERCIAL',
        filter_meta: Optional[Dict] = None
    ) -> str:
        """Assemble the complete prompt (v1.1)."""
        context_header = f"""## CONTRACT ANALYSIS CONTEXT
Contract Type: {contract_type}
Position: {position.title()}
Leverage: {leverage.title()}
Contract Stage: {contract_stage}
Analysis Mode: Pattern-guided risk assessment (v1.3 Pattern Library)

"""

        # Build escalation summary if any
        escalation_summary = ""
        if filter_meta and filter_meta.get('escalations_triggered'):
            esc_types = set()
            for esc in filter_meta['escalations_triggered']:
                esc_types.update(esc['escalation_types'])
            escalation_summary = f"ESCALATIONS REQUIRED: {', '.join(sorted(esc_types))}\n\n"

        # Build dealbreaker warning if any
        dealbreaker_warning = ""
        if filter_meta and filter_meta.get('dealbreakers_flagged'):
            db_names = [db['name'] for db in filter_meta['dealbreakers_flagged']]
            dealbreaker_warning = f"DEALBREAKER PATTERNS DETECTED: {', '.join(db_names)}\n\n"

        instructions = """## INSTRUCTIONS
1. Analyze the contract using the applicable pattern cards below
2. For each triggered pattern, assess current contract language
3. Recommend revisions using the pattern's revision language
4. Include success probability and fallback positions
5. Flag any DEALBREAKER combinations immediately
6. Note any patterns requiring escalation (CEO, LEGAL, INSURANCE)

"""

        # Combine all sections
        sections = [base_prompt] if base_prompt else []
        if dealbreaker_warning:
            sections.append(dealbreaker_warning)
        if escalation_summary:
            sections.append(escalation_summary)
        sections.extend([context_header, pattern_section, instructions])

        return "\n".join(sections)

    def _save_prompt(self, metadata: Dict, assembled_prompt: str) -> Optional[int]:
        """Save composed prompt to database for audit trail (v1.1)."""
        if not self.db_path:
            logger.debug("No DB path configured, skipping prompt save")
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO prompts (
                    contract_id, position, leverage, category,
                    selected_patterns, assembled_prompt, token_count,
                    created_at, version,
                    contract_stage, escalations_triggered, status_filter_applied,
                    stage_filter_applied, dealbreakers_flagged
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata['contract_id'],
                metadata['position'],
                metadata['leverage'],
                metadata['category'],
                json.dumps(metadata['selected_patterns']),
                assembled_prompt,
                metadata['token_count'],
                datetime.now().isoformat(),
                metadata['deck_version'],
                # v1.3 columns
                metadata.get('contract_stage', 'COMMERCIAL'),
                json.dumps(metadata.get('escalations_triggered', [])),
                metadata.get('status_filter_applied', '["CONFIRMED"]'),
                metadata.get('stage_filter_applied', 'COMMERCIAL'),
                json.dumps(metadata.get('dealbreakers_flagged', []))
            ))

            prompt_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.debug(f"Saved prompt ID {prompt_id} to database (v1.1 with stage/escalation tracking)")
            return prompt_id

        except Exception as e:
            logger.warning(f"Failed to save prompt to database: {e}")
            return None

    def get_pattern_hand_display(
        self,
        contract_type: str,
        position: str,
        leverage: str,
        contract_stage: str = 'COMMERCIAL',
        include_research_needed: bool = False
    ) -> Dict:
        """
        Get pattern selection for UI display (Gate 4 approval) - v1.1.

        Returns dict with cards and filter metadata for Streamlit display.
        """
        selected, filter_meta = self.select_patterns(
            contract_type, position, leverage,
            contract_stage=contract_stage,
            include_research_needed=include_research_needed
        )

        display_cards = []
        for card in selected:
            rates = card.get('success_rates', {})
            key = f"{position}_{leverage}"
            fallback_key = f"any_{leverage}"
            success = rates.get(key, rates.get(fallback_key, 0.5))

            display_cards.append({
                'id': card['id'],
                'name': card['name'],
                'category': card.get('category', 'unknown'),
                'problem': card['problem'],
                'success_rate': int(success * 100),
                'is_mandatory': bool(card.get('combined_triggers')),
                'fallback': card.get('fallbacks', {}).get('acceptable', 'N/A'),
                # v1.3 additions
                'v1_3_status': card.get('v1_3_status', 'NOT_REVIEWED'),
                'user_notes': card.get('v1_3_user_notes'),
                'escalation': card.get('escalation', []),
                'stage_restrictions': card.get('stage_restrictions', [])
            })

        return {
            'cards': display_cards,
            'filter_meta': filter_meta,
            'deck_version': self.deck_version,
            'pattern_library_version': self.pattern_library_version
        }


def create_composer(config: Dict) -> PromptComposer:
    """Factory function to create PromptComposer instance."""
    return PromptComposer(config)


# Standalone test
if __name__ == "__main__":
    # Test configuration (v1.1 - v1.3 Pattern Library)
    test_config = {
        'PATTERN_DECK_PATH': 'C:/Users/jrudy/CCE/memory/patterns/deck_v3_phase3.json',
        'MAX_PATTERNS_PER_PROMPT': 15,
        'PATTERN_TOKEN_CEILING': 1500,
        'PATTERN_COMPACT_AVG_TOKENS': 70,
        'CONTRACT_CATEGORY_MAP': {
            'MSA': 'A',
            'SOW': 'D',
            'NDA': 'C',
            'MOU': 'B',
            'LOI': 'B',
            'CHANNEL': 'F',
            'RESELLER': 'F',
            'BROKER': 'G'
        },
        'CONTRACT_STAGES': ['MNDA', 'NDA', 'COMMERCIAL', 'EXECUTED'],
        'PATTERN_STATUSES': ['CONFIRMED', 'RESEARCH_NEEDED', 'DEALBREAKER', 'LEGAL_REVIEW'],
        'ESCALATION_TYPES': ['CEO', 'LEGAL', 'INSURANCE'],
        'DB_PATH': None  # Skip DB for test
    }

    composer = PromptComposer(test_config)

    print("=" * 60)
    print("PROMPT COMPOSER v1.1 TEST (v1.3 Pattern Library)")
    print("=" * 60)
    print(f"Deck Version: {composer.deck_version}")
    print(f"Pattern Library: v{composer.pattern_library_version}")
    print()

    # Test pattern selection with stage filtering
    print("=== Pattern Selection Test ===")
    print("Contract: MSA | Position: customer | Leverage: balanced | Stage: COMMERCIAL")
    print()

    selected, filter_meta = composer.select_patterns('MSA', 'customer', 'balanced', 'COMMERCIAL')
    print(f"Selected {len(selected)} patterns:")
    for card in selected[:5]:
        status = card.get('v1_3_status', 'N/A')
        esc = card.get('escalation', [])
        esc_str = f" [{', '.join(esc)}]" if esc else ""
        print(f"  [{card['id']}] {card['name']} ({status}){esc_str}")

    print()
    print("=== Filter Metadata ===")
    print(f"  Status filtered: {filter_meta['status_filtered']}")
    print(f"  Stage filtered: {filter_meta['stage_filtered']}")
    print(f"  Escalations: {len(filter_meta['escalations_triggered'])}")
    print(f"  Dealbreakers: {len(filter_meta['dealbreakers_flagged'])}")

    if filter_meta['escalations_triggered']:
        print("\n  Escalation Details:")
        for esc in filter_meta['escalations_triggered']:
            print(f"    - [{esc['id']}] {esc['name']}: {', '.join(esc['escalation_types'])}")

    if filter_meta['dealbreakers_flagged']:
        print("\n  Dealbreaker Details:")
        for db in filter_meta['dealbreakers_flagged']:
            print(f"    - [{db['id']}] {db['name']}")

    print()
    print("=== Stage Filter Test (NDA stage) ===")
    selected_nda, filter_meta_nda = composer.select_patterns('MSA', 'customer', 'balanced', 'NDA')
    print(f"Selected {len(selected_nda)} patterns (stage=NDA)")
    print(f"Stage filtered: {filter_meta_nda['stage_filtered']} patterns excluded")

    print()
    print("=== Display Format (for UI) ===")
    display = composer.get_pattern_hand_display('MSA', 'customer', 'balanced', 'COMMERCIAL')
    print(f"Cards: {len(display['cards'])}")
    print(f"Deck: v{display['deck_version']}, Pattern Library: v{display['pattern_library_version']}")
    for d in display['cards'][:3]:
        esc_str = f" [{', '.join(d['escalation'])}]" if d['escalation'] else ""
        print(f"  {d['id']}: {d['name']} ({d['success_rate']}%, {d['v1_3_status']}){esc_str}")

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
