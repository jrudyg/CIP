"""
CIP Contract Health Score API

Calculates a 0-100 health score for each contract based on:
- Expiration Urgency (40 pts) - How soon contract expires
- Risk Level (30 pts) - CRITICAL/HIGH/MEDIUM/LOW rating
- Metadata Completeness (20 pts) - How complete the contract record is
- Review Recency (10 pts) - How recently the contract was reviewed

Endpoints:
- /api/contracts/health - Get health scores for all contracts
- /api/contracts/<id>/health - Get health score for single contract
- /api/dashboard/health - Get aggregated health summary
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from flask import Blueprint, request, jsonify

# Create blueprint
health_bp = Blueprint('health', __name__)

# Configuration
CIP_ROOT = Path(r"C:\Users\jrudy\CIP")
CONTRACTS_DB = CIP_ROOT / "data" / "contracts.db"

# Health score configuration
HEALTH_CONFIG = {
    # Expiration urgency scoring (40 points max)
    'expiration': {
        'weight': 40,
        'thresholds': [
            (0, 0),       # Already expired = 0 points
            (30, 10),     # Within 30 days = 10 points
            (60, 20),     # Within 60 days = 20 points
            (90, 30),     # Within 90 days = 30 points
            (180, 35),    # Within 180 days = 35 points
            (365, 38),    # Within 1 year = 38 points
            (None, 40),   # More than 1 year = 40 points
        ]
    },
    # Risk level scoring (30 points max)
    'risk': {
        'weight': 30,
        'scores': {
            'LOW': 30,
            'MEDIUM': 20,
            'HIGH': 10,
            'CRITICAL': 0,
            None: 15,  # Unknown risk
        }
    },
    # Metadata completeness scoring (20 points max)
    'metadata': {
        'weight': 20,
        'fields': [
            ('title', 2),
            ('counterparty', 3),
            ('contract_type', 2),
            ('status', 2),
            ('effective_date', 2),
            ('expiration_date', 3),
            ('contract_value', 3),
            ('purpose', 2),
            ('filename', 1),
        ]
    },
    # Review recency scoring (10 points max)
    'review': {
        'weight': 10,
        'thresholds': [
            (7, 10),      # Reviewed within 7 days = 10 points
            (30, 8),      # Within 30 days = 8 points
            (90, 5),      # Within 90 days = 5 points
            (180, 3),     # Within 180 days = 3 points
            (365, 1),     # Within 1 year = 1 point
            (None, 0),    # Over 1 year = 0 points
        ]
    }
}

# Health grade thresholds
HEALTH_GRADES = {
    'A': {'min': 90, 'color': '#22C55E', 'label': 'Excellent'},
    'B': {'min': 75, 'color': '#84CC16', 'label': 'Good'},
    'C': {'min': 60, 'color': '#EAB308', 'label': 'Fair'},
    'D': {'min': 40, 'color': '#F97316', 'label': 'Poor'},
    'F': {'min': 0, 'color': '#EF4444', 'label': 'Critical'},
}


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(CONTRACTS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def calculate_expiration_score(expiration_date: Optional[str]) -> Tuple[int, str]:
    """
    Calculate expiration urgency score.

    Returns:
        Tuple of (score, reason)
    """
    if not expiration_date:
        return (20, "No expiration date set")  # Neutral score

    try:
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_until = (exp_date - today).days

        if days_until < 0:
            return (0, f"Expired {abs(days_until)} days ago")

        thresholds = HEALTH_CONFIG['expiration']['thresholds']
        for threshold_days, score in thresholds:
            if threshold_days is None or days_until <= threshold_days:
                if threshold_days is None:
                    return (score, f"Expires in {days_until} days (healthy)")
                return (score, f"Expires in {days_until} days")

        return (40, f"Expires in {days_until} days")
    except (ValueError, TypeError):
        return (20, "Invalid expiration date")


def calculate_risk_score(risk_level: Optional[str]) -> Tuple[int, str]:
    """
    Calculate risk level score.

    Returns:
        Tuple of (score, reason)
    """
    scores = HEALTH_CONFIG['risk']['scores']
    risk_upper = risk_level.upper() if risk_level else None

    score = scores.get(risk_upper, scores[None])

    if risk_upper == 'CRITICAL':
        reason = "Critical risk level"
    elif risk_upper == 'HIGH':
        reason = "High risk level"
    elif risk_upper == 'MEDIUM':
        reason = "Medium risk level"
    elif risk_upper == 'LOW':
        reason = "Low risk level"
    else:
        reason = "Risk level not assessed"

    return (score, reason)


def calculate_metadata_score(contract: Dict) -> Tuple[int, str, List[str]]:
    """
    Calculate metadata completeness score.

    Returns:
        Tuple of (score, reason, missing_fields)
    """
    fields = HEALTH_CONFIG['metadata']['fields']
    total_possible = sum(weight for _, weight in fields)
    earned = 0
    missing = []

    for field, weight in fields:
        value = contract.get(field)
        if value is not None and str(value).strip():
            earned += weight
        else:
            missing.append(field)

    # Scale to 20 points max
    score = int((earned / total_possible) * HEALTH_CONFIG['metadata']['weight'])

    if not missing:
        reason = "All metadata fields complete"
    elif len(missing) <= 2:
        reason = f"Missing: {', '.join(missing)}"
    else:
        reason = f"Missing {len(missing)} fields"

    return (score, reason, missing)


def calculate_review_score(updated_at: Optional[str]) -> Tuple[int, str]:
    """
    Calculate review recency score.

    Returns:
        Tuple of (score, reason)
    """
    if not updated_at:
        return (0, "Never reviewed")

    try:
        # Handle various datetime formats
        if 'T' in updated_at:
            update_date = datetime.fromisoformat(updated_at.replace('Z', '')).date()
        else:
            update_date = datetime.strptime(updated_at[:10], '%Y-%m-%d').date()

        today = datetime.now().date()
        days_since = (today - update_date).days

        thresholds = HEALTH_CONFIG['review']['thresholds']
        for threshold_days, score in thresholds:
            if threshold_days is None or days_since <= threshold_days:
                if days_since == 0:
                    return (score, "Updated today")
                elif days_since == 1:
                    return (score, "Updated yesterday")
                else:
                    return (score, f"Updated {days_since} days ago")

        return (0, f"Last updated {days_since} days ago")
    except (ValueError, TypeError):
        return (0, "Invalid update date")


def calculate_health_score(contract: Dict) -> Dict[str, Any]:
    """
    Calculate complete health score for a contract.

    Returns:
        Dict with total score, grade, and component breakdown
    """
    # Calculate component scores
    exp_score, exp_reason = calculate_expiration_score(contract.get('expiration_date'))
    risk_score, risk_reason = calculate_risk_score(contract.get('risk_level'))
    meta_score, meta_reason, missing_fields = calculate_metadata_score(contract)
    review_score, review_reason = calculate_review_score(contract.get('updated_at'))

    # Calculate total
    total_score = exp_score + risk_score + meta_score + review_score

    # Determine grade
    grade = 'F'
    for g, info in HEALTH_GRADES.items():
        if total_score >= info['min']:
            grade = g
            break

    grade_info = HEALTH_GRADES[grade]

    return {
        'contract_id': contract.get('id'),
        'total_score': total_score,
        'grade': grade,
        'grade_label': grade_info['label'],
        'grade_color': grade_info['color'],
        'components': {
            'expiration': {
                'score': exp_score,
                'max': HEALTH_CONFIG['expiration']['weight'],
                'reason': exp_reason
            },
            'risk': {
                'score': risk_score,
                'max': HEALTH_CONFIG['risk']['weight'],
                'reason': risk_reason
            },
            'metadata': {
                'score': meta_score,
                'max': HEALTH_CONFIG['metadata']['weight'],
                'reason': meta_reason,
                'missing_fields': missing_fields
            },
            'review': {
                'score': review_score,
                'max': HEALTH_CONFIG['review']['weight'],
                'reason': review_reason
            }
        }
    }


@health_bp.route('/api/contracts/health', methods=['GET'])
def get_all_health_scores():
    """
    Get health scores for all contracts.

    Query params:
        - min_score: Filter to contracts with score >= value
        - max_score: Filter to contracts with score <= value
        - grade: Filter by grade (A, B, C, D, F)
        - status: Filter by contract status
        - sort: Sort by 'score' (default), 'expiration', 'risk'
        - order: 'asc' or 'desc' (default)
        - limit: Max results (default 100)
        - include_archived: Include archived contracts (default false)

    Returns:
        {contracts: [{id, title, counterparty, health_score, grade, ...}], summary: {...}}
    """
    # Parse parameters
    min_score = request.args.get('min_score', type=int)
    max_score = request.args.get('max_score', type=int)
    grade_filter = request.args.get('grade', '').upper()
    status_filter = request.args.get('status')
    sort_by = request.args.get('sort', 'score')
    order = request.args.get('order', 'desc').lower()
    limit = min(request.args.get('limit', 100, type=int), 500)
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query
    base_where = "(archived = 0 OR archived IS NULL)" if not include_archived else "1=1"
    params = []

    if status_filter:
        base_where += " AND status = ?"
        params.append(status_filter)

    cursor.execute(f"""
        SELECT id, title, counterparty, contract_type, status,
               risk_level, expiration_date, contract_value, updated_at
        FROM contracts
        WHERE {base_where}
    """, params)

    contracts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Calculate health scores
    results = []
    for contract in contracts:
        health = calculate_health_score(contract)

        # Apply score filters
        if min_score and health['total_score'] < min_score:
            continue
        if max_score and health['total_score'] > max_score:
            continue
        if grade_filter and health['grade'] != grade_filter:
            continue

        results.append({
            'id': contract['id'],
            'title': contract['title'],
            'counterparty': contract['counterparty'],
            'contract_type': contract['contract_type'],
            'status': contract['status'],
            'risk_level': contract['risk_level'],
            'expiration_date': contract['expiration_date'],
            'health_score': health['total_score'],
            'grade': health['grade'],
            'grade_label': health['grade_label'],
            'grade_color': health['grade_color'],
            'components': health['components']
        })

    # Sort results
    if sort_by == 'score':
        results.sort(key=lambda x: x['health_score'], reverse=(order == 'desc'))
    elif sort_by == 'expiration':
        results.sort(key=lambda x: x['expiration_date'] or '9999-12-31', reverse=(order == 'desc'))
    elif sort_by == 'risk':
        risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, None: 4}
        results.sort(key=lambda x: risk_order.get(x['risk_level'], 4), reverse=(order == 'desc'))

    # Apply limit
    results = results[:limit]

    # Calculate summary
    if results:
        scores = [r['health_score'] for r in results]
        grade_counts = {}
        for r in results:
            grade_counts[r['grade']] = grade_counts.get(r['grade'], 0) + 1

        summary = {
            'total_contracts': len(results),
            'average_score': round(sum(scores) / len(scores), 1),
            'min_score': min(scores),
            'max_score': max(scores),
            'by_grade': grade_counts
        }
    else:
        summary = {
            'total_contracts': 0,
            'average_score': 0,
            'min_score': 0,
            'max_score': 0,
            'by_grade': {}
        }

    return jsonify({
        'contracts': results,
        'summary': summary,
        'generated_at': datetime.now().isoformat()
    })


@health_bp.route('/api/contracts/<int:contract_id>/health', methods=['GET'])
def get_contract_health(contract_id: int):
    """
    Get detailed health score for a single contract.

    Returns:
        Full health breakdown with recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM contracts WHERE id = ?
    """, (contract_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Contract not found'}), 404

    contract = dict(row)
    health = calculate_health_score(contract)

    # Generate recommendations
    recommendations = []

    # Expiration recommendations
    exp_score = health['components']['expiration']['score']
    if exp_score < 20:
        recommendations.append({
            'priority': 'high',
            'category': 'expiration',
            'action': 'Review expiring contract immediately',
            'impact': '+20 points potential'
        })

    # Risk recommendations
    risk_score = health['components']['risk']['score']
    if risk_score < 20:
        recommendations.append({
            'priority': 'high' if risk_score == 0 else 'medium',
            'category': 'risk',
            'action': 'Address high-risk issues identified in risk assessment',
            'impact': '+10-20 points potential'
        })

    # Metadata recommendations
    missing = health['components']['metadata'].get('missing_fields', [])
    if missing:
        recommendations.append({
            'priority': 'medium',
            'category': 'metadata',
            'action': f'Complete missing fields: {", ".join(missing[:3])}',
            'impact': f'+{len(missing) * 2} points potential'
        })

    # Review recommendations
    review_score = health['components']['review']['score']
    if review_score < 5:
        recommendations.append({
            'priority': 'low',
            'category': 'review',
            'action': 'Schedule periodic contract review',
            'impact': '+5-10 points potential'
        })

    return jsonify({
        'contract': {
            'id': contract['id'],
            'title': contract['title'],
            'counterparty': contract.get('counterparty'),
            'status': contract.get('status'),
            'risk_level': contract.get('risk_level'),
            'expiration_date': contract.get('expiration_date')
        },
        'health': health,
        'recommendations': recommendations,
        'generated_at': datetime.now().isoformat()
    })


@health_bp.route('/api/dashboard/health', methods=['GET'])
def get_health_dashboard():
    """
    Get aggregated health metrics for dashboard.

    Returns:
        Portfolio-wide health summary with trends and alerts
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    base_where = "(archived = 0 OR archived IS NULL)"

    cursor.execute(f"""
        SELECT id, title, counterparty, contract_type, status,
               risk_level, expiration_date, contract_value, updated_at
        FROM contracts
        WHERE {base_where}
    """)

    contracts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not contracts:
        return jsonify({
            'portfolio_score': 0,
            'portfolio_grade': 'N/A',
            'total_contracts': 0,
            'by_grade': {},
            'alerts': [],
            'generated_at': datetime.now().isoformat()
        })

    # Calculate all health scores
    health_data = []
    for contract in contracts:
        health = calculate_health_score(contract)
        health_data.append({
            'contract': contract,
            'health': health
        })

    # Calculate portfolio metrics
    scores = [h['health']['total_score'] for h in health_data]
    avg_score = sum(scores) / len(scores)

    # Determine portfolio grade
    portfolio_grade = 'F'
    for g, info in HEALTH_GRADES.items():
        if avg_score >= info['min']:
            portfolio_grade = g
            break

    # Count by grade
    grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for h in health_data:
        grade_counts[h['health']['grade']] = grade_counts.get(h['health']['grade'], 0) + 1

    # Identify critical alerts (score < 40)
    alerts = []
    for h in health_data:
        if h['health']['total_score'] < 40:
            alerts.append({
                'contract_id': h['contract']['id'],
                'title': h['contract']['title'],
                'score': h['health']['total_score'],
                'grade': h['health']['grade'],
                'primary_issue': get_primary_issue(h['health'])
            })

    # Sort alerts by score (lowest first)
    alerts.sort(key=lambda x: x['score'])
    alerts = alerts[:10]  # Top 10 most critical

    # Component averages
    component_avgs = {
        'expiration': sum(h['health']['components']['expiration']['score'] for h in health_data) / len(health_data),
        'risk': sum(h['health']['components']['risk']['score'] for h in health_data) / len(health_data),
        'metadata': sum(h['health']['components']['metadata']['score'] for h in health_data) / len(health_data),
        'review': sum(h['health']['components']['review']['score'] for h in health_data) / len(health_data),
    }

    return jsonify({
        'portfolio_score': round(avg_score, 1),
        'portfolio_grade': portfolio_grade,
        'portfolio_grade_label': HEALTH_GRADES[portfolio_grade]['label'],
        'portfolio_grade_color': HEALTH_GRADES[portfolio_grade]['color'],
        'total_contracts': len(contracts),
        'by_grade': grade_counts,
        'component_averages': {k: round(v, 1) for k, v in component_avgs.items()},
        'critical_alerts': alerts,
        'score_distribution': {
            'excellent': len([s for s in scores if s >= 90]),
            'good': len([s for s in scores if 75 <= s < 90]),
            'fair': len([s for s in scores if 60 <= s < 75]),
            'poor': len([s for s in scores if 40 <= s < 60]),
            'critical': len([s for s in scores if s < 40]),
        },
        'generated_at': datetime.now().isoformat()
    })


def get_primary_issue(health: Dict) -> str:
    """Identify the primary issue affecting health score."""
    components = health['components']

    # Find lowest scoring component (relative to max)
    ratios = []
    for name, data in components.items():
        ratio = data['score'] / data['max'] if data['max'] > 0 else 0
        ratios.append((name, ratio, data['reason']))

    ratios.sort(key=lambda x: x[1])
    worst = ratios[0]

    return worst[2]  # Return the reason


def register_health(app):
    """Register health blueprint with Flask app."""
    app.register_blueprint(health_bp)
    return health_bp
