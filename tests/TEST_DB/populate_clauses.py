"""
Populate Test Database with EPC Clause Data
Creates realistic clause data for 20 contracts including:
- Full clause text from EPC clause library
- Risk assessments with structured findings
- Redline snapshots with revision suggestions
- Analysis snapshots with clause lists
"""

import sqlite3
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

from epc_clause_library import EPC_CLAUSE_LIBRARY, get_all_categories

# =============================================================================
# CONFIGURATION
# =============================================================================

NUM_CONTRACTS_TO_ENHANCE = 20
CLAUSES_PER_CONTRACT = (8, 12)  # min, max

# Risk variant weights: favorable, balanced, unfavorable, dealbreaker
RISK_WEIGHTS = {
    'favorable': 0.15,
    'balanced': 0.40,
    'unfavorable': 0.35,
    'dealbreaker': 0.10
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def select_contracts(cursor, num_contracts):
    """Select contracts for enhancement with diverse characteristics."""

    contracts = []

    # Get negotiating contracts (need redlines)
    cursor.execute("""
        SELECT id, contract_type, status, risk_level, contract_value
        FROM contracts
        WHERE status = 'negotiating'
        LIMIT 5
    """)
    contracts.extend(cursor.fetchall())

    # Get reviewing/analyzing contracts (need risk assessment)
    cursor.execute("""
        SELECT id, contract_type, status, risk_level, contract_value
        FROM contracts
        WHERE status IN ('review', 'analyzing', 'in_progress')
        AND id NOT IN ({})
        LIMIT 5
    """.format(','.join(str(c[0]) for c in contracts) if contracts else '0'))
    contracts.extend(cursor.fetchall())

    # Get high-value active contracts
    cursor.execute("""
        SELECT id, contract_type, status, risk_level, contract_value
        FROM contracts
        WHERE status = 'active'
        AND contract_value > 100000
        AND id NOT IN ({})
        LIMIT 5
    """.format(','.join(str(c[0]) for c in contracts) if contracts else '0'))
    contracts.extend(cursor.fetchall())

    # Get diverse contract types
    cursor.execute("""
        SELECT id, contract_type, status, risk_level, contract_value
        FROM contracts
        WHERE contract_type IN ('MSA', 'SOW', 'NDA', 'LICENSE', 'LEASE')
        AND id NOT IN ({})
        LIMIT 5
    """.format(','.join(str(c[0]) for c in contracts) if contracts else '0'))
    contracts.extend(cursor.fetchall())

    # Fill remaining with random contracts
    if len(contracts) < num_contracts:
        existing_ids = [c[0] for c in contracts]
        cursor.execute("""
            SELECT id, contract_type, status, risk_level, contract_value
            FROM contracts
            WHERE id NOT IN ({})
            LIMIT {}
        """.format(','.join(str(id) for id in existing_ids) if existing_ids else '0',
                   num_contracts - len(contracts)))
        contracts.extend(cursor.fetchall())

    return contracts[:num_contracts]


def generate_clause_set(contract_id, contract_type, target_risk_level):
    """Generate a set of clauses for a contract."""

    categories = get_all_categories()
    num_clauses = random.randint(*CLAUSES_PER_CONTRACT)

    # Select categories - prioritize certain ones based on contract type
    priority_categories = {
        'MSA': ['payment', 'limitation_of_liability', 'indemnification', 'termination', 'warranties'],
        'SOW': ['payment', 'change_orders', 'schedule_delays', 'warranties', 'termination'],
        'NDA': ['confidentiality', 'termination', 'governing_law', 'dispute_resolution'],
        'LICENSE': ['intellectual_property', 'payment', 'warranties', 'limitation_of_liability'],
        'LEASE': ['payment', 'termination', 'insurance', 'assignment'],
    }

    # Start with priority categories for this contract type
    selected_categories = priority_categories.get(contract_type, [])[:4]

    # Add remaining random categories
    remaining = [c for c in categories if c not in selected_categories]
    random.shuffle(remaining)
    selected_categories.extend(remaining[:num_clauses - len(selected_categories)])

    # Generate clauses
    clauses = []
    risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0, 'DEALBREAKER': 0}

    for i, category in enumerate(selected_categories[:num_clauses]):
        # Determine risk variant based on weights and target risk
        if target_risk_level in ['DEALBREAKER', 'CRITICAL'] and i < 2:
            # High-risk contracts should have some high-risk clauses
            variants = ['unfavorable', 'dealbreaker']
            weights = [0.7, 0.3]
        elif target_risk_level == 'LOW' and i < 3:
            variants = ['favorable', 'balanced']
            weights = [0.5, 0.5]
        else:
            variants = list(RISK_WEIGHTS.keys())
            weights = list(RISK_WEIGHTS.values())

        variant = random.choices(variants, weights=weights)[0]

        clause_data = EPC_CLAUSE_LIBRARY.get(category, {}).get(variant)
        if not clause_data:
            continue

        clause = {
            'contract_id': contract_id,
            'section_number': f"{i+1}.0",
            'title': clause_data.get('title', category.replace('_', ' ').title()),
            'text': clause_data['text'].strip(),
            'category': category,
            'risk_level': clause_data['risk_level'],
            'pattern_id': clause_data.get('pattern_id', f'PAT-{category[:3].upper()}-{random.randint(100,999)}'),
            'finding': clause_data.get('finding'),
            'recommendation': clause_data.get('recommendation'),
            'redline': clause_data.get('redline'),
            'escalation': clause_data.get('escalation'),
            'variant': variant
        }
        clauses.append(clause)
        risk_counts[clause['risk_level']] += 1

    return clauses, risk_counts


def create_risk_assessment(contract_id, clauses, risk_counts):
    """Create a structured risk assessment from clauses."""

    # Categorize clauses by risk level
    critical_items = []
    important_items = []
    standard_items = []
    dealbreakers = []

    for clause in clauses:
        item = {
            'section_number': clause['section_number'],
            'section_title': clause['title'],
            'risk_level': clause['risk_level'],
            'category': clause['category'],
            'finding': clause.get('finding') or f"Review required for {clause['category']}",
            'recommendation': clause.get('recommendation') or "Standard review recommended",
            'confidence': round(random.uniform(0.85, 0.98), 2),
            'pattern_id': clause['pattern_id'],
            'clause_text': clause['text'][:500] + '...' if len(clause['text']) > 500 else clause['text']
        }

        if clause.get('redline'):
            item['redline_suggestion'] = f"~~{clause['redline']['current_text'][:100]}~~ `{clause['redline']['suggested_text'][:100]}`"

        if clause.get('escalation'):
            item['escalation'] = clause['escalation']

        if clause['risk_level'] == 'DEALBREAKER':
            dealbreakers.append(item)
        elif clause['risk_level'] == 'CRITICAL':
            critical_items.append(item)
        elif clause['risk_level'] in ['HIGH', 'MEDIUM']:
            important_items.append(item)
        else:
            standard_items.append(item)

    # Determine overall risk
    if dealbreakers:
        overall_risk = 'DEALBREAKER'
    elif critical_items:
        overall_risk = 'CRITICAL'
    elif len([c for c in clauses if c['risk_level'] == 'HIGH']) >= 2:
        overall_risk = 'HIGH'
    elif len([c for c in clauses if c['risk_level'] in ['HIGH', 'MEDIUM']]) >= 3:
        overall_risk = 'MEDIUM'
    else:
        overall_risk = 'LOW'

    assessment = {
        'contract_id': contract_id,
        'overall_risk': overall_risk,
        'critical_items': critical_items,
        'important_items': important_items,
        'standard_items': standard_items,
        'dealbreakers': dealbreakers,
        'confidence_score': round(random.uniform(0.85, 0.95), 2),
        'risk_counts': risk_counts,
        'categories_analyzed': len(clauses),
        'analysis_version': '2.0-EPC'
    }

    return assessment


def create_redline_snapshot(contract_id, clauses, overall_risk):
    """Create a redline snapshot for contracts in negotiation."""

    redline_clauses = []

    for i, clause in enumerate(clauses):
        redline_data = clause.get('redline')

        # Create RedlineClause structure
        rc = {
            'clause_id': i,
            'section_number': clause['section_number'],
            'title': clause['title'],
            'risk_category': clause['category'],
            'current_text': clause['text'],
            'suggested_text': redline_data['suggested_text'] if redline_data else clause['text'],
            'rationale': redline_data['rationale'] if redline_data else 'No changes recommended',
            'pattern_ref': clause['pattern_id'],
            'confidence': round(random.uniform(0.85, 0.95), 2),
            'status': 'suggested' if redline_data else 'accepted',
            'user_notes': None,
            'success_probability': redline_data['success_probability'] if redline_data else None,
            'leverage_context': redline_data['leverage_context'] if redline_data else None,
            'flowdown_impact': None,
            'dealbreaker_flag': clause['risk_level'] == 'DEALBREAKER',
            'risk_priority': clause['risk_level'] if clause['risk_level'] in ['CRITICAL', 'HIGH'] else 'MODERATE'
        }
        redline_clauses.append(rc)

    # Calculate risk after potential changes
    risk_after = overall_risk
    suggested_count = len([rc for rc in redline_clauses if rc['status'] == 'suggested'])
    if suggested_count > 0 and overall_risk in ['CRITICAL', 'HIGH']:
        risk_after = 'MEDIUM' if overall_risk == 'HIGH' else 'HIGH'

    snapshot = {
        'contract_id': contract_id,
        'base_version_contract_id': contract_id,
        'source_mode': 'single',
        'created_at': datetime.now().isoformat(),
        'overall_risk_before': overall_risk,
        'overall_risk_after': risk_after,
        'clauses': redline_clauses,
        'status': 'draft',
        'contract_position': random.choice(['upstream', 'downstream', 'teaming', 'other']),
        'dealbreakers_detected': len([c for c in clauses if c['risk_level'] == 'DEALBREAKER'])
    }

    return snapshot


def create_analysis_snapshot(contract_id, clauses, overall_risk):
    """Create an analysis snapshot."""

    clause_list = []
    categories = []

    for clause in clauses:
        clause_list.append({
            'section_number': clause['section_number'],
            'title': clause['title'],
            'text': clause['text'][:500] + '...' if len(clause['text']) > 500 else clause['text'],
            'category': clause['category'],
            'risk_level': clause['risk_level']
        })
        if clause['category'] not in categories:
            categories.append(clause['category'])

    return {
        'contract_id': contract_id,
        'created_at': datetime.now().isoformat(),
        'overall_risk': overall_risk,
        'categories': categories,
        'clauses': clause_list
    }


# =============================================================================
# MAIN POPULATION FUNCTION
# =============================================================================

def populate_database(db_path):
    """Populate the database with EPC clause data."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*70)
    print("POPULATING TEST DATABASE WITH EPC CLAUSE DATA")
    print("="*70)

    # Select contracts to enhance
    print(f"\n[1] Selecting {NUM_CONTRACTS_TO_ENHANCE} contracts...")
    contracts = select_contracts(cursor, NUM_CONTRACTS_TO_ENHANCE)
    print(f"  Selected {len(contracts)} contracts")

    for c in contracts:
        print(f"    ID {c[0]}: {c[1]} ({c[2]}) - Risk: {c[3]}")

    # Process each contract
    print(f"\n[2] Generating clause data...")

    stats = {
        'clauses_created': 0,
        'risk_assessments_updated': 0,
        'redline_snapshots_created': 0,
        'analysis_snapshots_updated': 0
    }

    for contract in contracts:
        contract_id, contract_type, status, target_risk, value = contract

        print(f"\n  Processing contract {contract_id} ({contract_type})...")

        # Generate clauses
        clauses, risk_counts = generate_clause_set(contract_id, contract_type, target_risk)
        print(f"    Generated {len(clauses)} clauses")

        # Delete existing clauses for this contract
        cursor.execute("DELETE FROM clauses WHERE contract_id = ?", (contract_id,))

        # Insert new clauses
        for clause in clauses:
            cursor.execute("""
                INSERT INTO clauses (contract_id, section_number, title, text, category, risk_level, pattern_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                clause['contract_id'],
                clause['section_number'],
                clause['title'],
                clause['text'],
                clause['category'],
                clause['risk_level'],
                clause['pattern_id']
            ))
            stats['clauses_created'] += 1

        # Create risk assessment
        assessment = create_risk_assessment(contract_id, clauses, risk_counts)

        # Update risk_assessments table
        cursor.execute("""
            UPDATE risk_assessments
            SET overall_risk = ?,
                critical_items = ?,
                dealbreakers = ?,
                confidence_score = ?,
                analysis_json = ?,
                assessment_date = ?
            WHERE contract_id = ?
        """, (
            assessment['overall_risk'],
            json.dumps([item['section_title'] for item in assessment['critical_items']]),
            json.dumps([item['section_title'] for item in assessment['dealbreakers']]),
            assessment['confidence_score'],
            json.dumps(assessment),
            datetime.now().isoformat(),
            contract_id
        ))
        stats['risk_assessments_updated'] += 1

        # Update contract risk level
        cursor.execute("""
            UPDATE contracts SET risk_level = ? WHERE id = ?
        """, (assessment['overall_risk'], contract_id))

        # Create redline snapshot for negotiating contracts
        if status in ['negotiating', 'review', 'in_progress']:
            snapshot = create_redline_snapshot(contract_id, clauses, assessment['overall_risk'])

            # Check if redline snapshot exists
            cursor.execute("SELECT redline_id FROM redline_snapshots WHERE contract_id = ?", (contract_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE redline_snapshots
                    SET clauses_json = ?,
                        overall_risk_before = ?,
                        overall_risk_after = ?,
                        status = ?,
                        contract_position = ?,
                        dealbreakers_detected = ?,
                        created_at = ?
                    WHERE contract_id = ?
                """, (
                    json.dumps(snapshot['clauses']),
                    snapshot['overall_risk_before'],
                    snapshot['overall_risk_after'],
                    snapshot['status'],
                    snapshot['contract_position'],
                    snapshot['dealbreakers_detected'],
                    snapshot['created_at'],
                    contract_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO redline_snapshots
                    (contract_id, base_version_contract_id, source_mode, created_at,
                     overall_risk_before, overall_risk_after, clauses_json, status,
                     contract_position, dealbreakers_detected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot['contract_id'],
                    snapshot['base_version_contract_id'],
                    snapshot['source_mode'],
                    snapshot['created_at'],
                    snapshot['overall_risk_before'],
                    snapshot['overall_risk_after'],
                    json.dumps(snapshot['clauses']),
                    snapshot['status'],
                    snapshot['contract_position'],
                    snapshot['dealbreakers_detected']
                ))
            stats['redline_snapshots_created'] += 1

            # Also create individual redlines
            for rc in snapshot['clauses']:
                if rc['status'] == 'suggested' and rc['current_text'] != rc['suggested_text']:
                    cursor.execute("""
                        INSERT OR REPLACE INTO redlines
                        (contract_id, section_number, original_text, revised_text,
                         rationale, success_probability, pattern_id, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        contract_id,
                        rc['section_number'],
                        rc['current_text'][:1000],
                        rc['suggested_text'][:1000],
                        rc['rationale'],
                        rc['success_probability'],
                        rc['pattern_ref'],
                        'proposed'
                    ))

        # Update analysis snapshot
        analysis = create_analysis_snapshot(contract_id, clauses, assessment['overall_risk'])

        cursor.execute("""
            UPDATE analysis_snapshots
            SET overall_risk = ?,
                categories = ?,
                clauses = ?,
                created_at = ?
            WHERE contract_id = ?
        """, (
            analysis['overall_risk'],
            json.dumps(analysis['categories']),
            json.dumps(analysis['clauses']),
            analysis['created_at'],
            contract_id
        ))
        stats['analysis_snapshots_updated'] += 1

    conn.commit()

    # Print summary
    print("\n" + "="*70)
    print("POPULATION SUMMARY")
    print("="*70)
    print(f"  Contracts enhanced: {len(contracts)}")
    print(f"  Clauses created: {stats['clauses_created']}")
    print(f"  Risk assessments updated: {stats['risk_assessments_updated']}")
    print(f"  Redline snapshots created: {stats['redline_snapshots_created']}")
    print(f"  Analysis snapshots updated: {stats['analysis_snapshots_updated']}")

    # Verify data
    print("\n" + "-"*70)
    print("VERIFICATION")
    print("-"*70)

    cursor.execute("""
        SELECT c.id, c.contract_type, c.status, c.risk_level, COUNT(cl.id) as clause_count
        FROM contracts c
        LEFT JOIN clauses cl ON c.id = cl.contract_id
        WHERE c.id IN ({})
        GROUP BY c.id
    """.format(','.join(str(c[0]) for c in contracts)))

    print("\n  Enhanced contracts:")
    for row in cursor.fetchall():
        print(f"    ID {row[0]}: {row[1]} ({row[2]}) - Risk: {row[3]}, Clauses: {row[4]}")

    # Check redline snapshots
    cursor.execute("""
        SELECT contract_id, overall_risk_before, overall_risk_after, dealbreakers_detected,
               LENGTH(clauses_json) as json_size
        FROM redline_snapshots
        WHERE contract_id IN ({})
    """.format(','.join(str(c[0]) for c in contracts)))

    redline_data = cursor.fetchall()
    if redline_data:
        print("\n  Redline snapshots:")
        for row in redline_data:
            print(f"    Contract {row[0]}: {row[1]} -> {row[2]}, Dealbreakers: {row[3]}, JSON: {row[4]} bytes")

    conn.close()
    print("\n" + "="*70)
    print("Database population complete!")
    print("="*70)


def main():
    db_path = Path("C:/Users/jrudy/CIP/tests/TEST_DB/test_contracts.db")

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return

    populate_database(str(db_path))

    # Copy to active locations
    print("\n\nCopying updated database to active locations...")
    import shutil
    active_paths = [
        Path("C:/Users/jrudy/CIP/data/contracts.db"),
        Path("C:/Users/jrudy/CIP/backend/contracts.db"),
    ]
    for active_path in active_paths:
        if active_path.parent.exists():
            shutil.copy(db_path, active_path)
            print(f"  Copied to: {active_path}")


if __name__ == "__main__":
    main()
