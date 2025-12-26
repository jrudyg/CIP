"""
CIP Dashboard API Endpoints

Provides aggregated data for dashboard displays:
- /api/dashboard/alerts - Contracts requiring attention
- /api/dashboard/stats - Portfolio statistics
- /api/dashboard/trends - Historical trends

Optimized for the indexes created by optimize_db_indexes.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

from flask import Blueprint, request, jsonify

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# Configuration
CIP_ROOT = Path(r"C:\Users\jrudy\CIP")
CONTRACTS_DB = CIP_ROOT / "data" / "contracts.db"


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(CONTRACTS_DB))
    conn.row_factory = sqlite3.Row
    return conn


@dashboard_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get contracts requiring attention.

    Returns:
        {
            summary: {expiring_30d, expiring_60d, expiring_90d, pending_review, high_risk_active},
            action_items: [{id, title, counterparty, days_to_expiry, risk_level, status, urgency}...]
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().date()
    d30 = (today + timedelta(days=30)).isoformat()
    d60 = (today + timedelta(days=60)).isoformat()
    d90 = (today + timedelta(days=90)).isoformat()
    today_str = today.isoformat()

    # Base filter: non-archived contracts
    base_where = "(archived = 0 OR archived IS NULL)"

    # Summary counts
    summary = {}

    # Expiring in 30 days
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND expiration_date BETWEEN ? AND ?
        AND status NOT IN ('expired', 'terminated', 'archived')
    """, (today_str, d30))
    summary['expiring_30d'] = cursor.fetchone()[0]

    # Expiring in 60 days
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND expiration_date BETWEEN ? AND ?
        AND status NOT IN ('expired', 'terminated', 'archived')
    """, (today_str, d60))
    summary['expiring_60d'] = cursor.fetchone()[0]

    # Expiring in 90 days
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND expiration_date BETWEEN ? AND ?
        AND status NOT IN ('expired', 'terminated', 'archived')
    """, (today_str, d90))
    summary['expiring_90d'] = cursor.fetchone()[0]

    # Pending review (intake, review, uploaded status)
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND status IN ('intake', 'review', 'uploaded', 'pending_review')
    """)
    summary['pending_review'] = cursor.fetchone()[0]

    # High risk active contracts
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND risk_level IN ('CRITICAL', 'HIGH')
        AND status IN ('active', 'negotiating', 'review')
    """)
    summary['high_risk_active'] = cursor.fetchone()[0]

    # Negotiating contracts
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND status = 'negotiating'
    """)
    summary['negotiating'] = cursor.fetchone()[0]

    # Recently expired (last 30 days)
    d30_ago = (today - timedelta(days=30)).isoformat()
    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND expiration_date BETWEEN ? AND ?
    """, (d30_ago, today_str))
    summary['recently_expired'] = cursor.fetchone()[0]

    # Action items - contracts needing attention
    cursor.execute(f"""
        SELECT
            id, title, counterparty, expiration_date, risk_level, status, contract_value
        FROM contracts
        WHERE {base_where}
        AND (
            (expiration_date BETWEEN ? AND ? AND status NOT IN ('expired', 'terminated'))
            OR (risk_level IN ('CRITICAL', 'HIGH') AND status IN ('active', 'negotiating', 'review'))
            OR status IN ('intake', 'review', 'pending_review')
        )
        ORDER BY
            CASE
                WHEN risk_level = 'CRITICAL' THEN 1
                WHEN risk_level = 'HIGH' THEN 2
                WHEN expiration_date < ? THEN 3
                ELSE 4
            END,
            expiration_date ASC
        LIMIT 20
    """, (today_str, d90, d30))

    action_items = []
    for row in cursor.fetchall():
        item = dict(row)

        # Calculate days to expiry
        if item['expiration_date']:
            try:
                exp_date = datetime.strptime(item['expiration_date'], '%Y-%m-%d').date()
                item['days_to_expiry'] = (exp_date - today).days
            except:
                item['days_to_expiry'] = None
        else:
            item['days_to_expiry'] = None

        # Determine urgency level
        urgency = 'low'
        if item['risk_level'] == 'CRITICAL':
            urgency = 'critical'
        elif item['risk_level'] == 'HIGH':
            urgency = 'high'
        elif item['days_to_expiry'] is not None:
            if item['days_to_expiry'] <= 30:
                urgency = 'high'
            elif item['days_to_expiry'] <= 60:
                urgency = 'medium'

        item['urgency'] = urgency
        action_items.append(item)

    conn.close()

    return jsonify({
        'summary': summary,
        'action_items': action_items,
        'generated_at': datetime.now().isoformat()
    })


@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get portfolio statistics.

    Returns:
        {
            totals: {contracts, value, active, expired},
            by_status: {status: count},
            by_type: {type: count},
            by_risk: {level: count},
            value_by_status: {status: value}
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    base_where = "(archived = 0 OR archived IS NULL)"

    stats = {
        'totals': {},
        'by_status': {},
        'by_type': {},
        'by_risk': {},
        'value_by_status': {}
    }

    # Total counts
    cursor.execute(f"SELECT COUNT(*) FROM contracts WHERE {base_where}")
    stats['totals']['contracts'] = cursor.fetchone()[0]

    cursor.execute(f"SELECT COALESCE(SUM(contract_value), 0) FROM contracts WHERE {base_where}")
    stats['totals']['value'] = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM contracts WHERE {base_where} AND status = 'active'")
    stats['totals']['active'] = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM contracts WHERE {base_where} AND status = 'expired'")
    stats['totals']['expired'] = cursor.fetchone()[0]

    # By status
    cursor.execute(f"""
        SELECT status, COUNT(*) as count
        FROM contracts
        WHERE {base_where} AND status IS NOT NULL
        GROUP BY status
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        stats['by_status'][row['status']] = row['count']

    # By contract type
    cursor.execute(f"""
        SELECT contract_type, COUNT(*) as count
        FROM contracts
        WHERE {base_where} AND contract_type IS NOT NULL
        GROUP BY contract_type
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        stats['by_type'][row['contract_type']] = row['count']

    # By risk level
    cursor.execute(f"""
        SELECT risk_level, COUNT(*) as count
        FROM contracts
        WHERE {base_where} AND risk_level IS NOT NULL
        GROUP BY risk_level
        ORDER BY
            CASE risk_level
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END
    """)
    for row in cursor.fetchall():
        stats['by_risk'][row['risk_level']] = row['count']

    # Value by status
    cursor.execute(f"""
        SELECT status, COALESCE(SUM(contract_value), 0) as total_value
        FROM contracts
        WHERE {base_where} AND status IS NOT NULL
        GROUP BY status
        ORDER BY total_value DESC
    """)
    for row in cursor.fetchall():
        stats['value_by_status'][row['status']] = row['total_value']

    conn.close()

    return jsonify({
        **stats,
        'generated_at': datetime.now().isoformat()
    })


@dashboard_bp.route('/trends', methods=['GET'])
def get_trends():
    """
    Get historical trends.

    Query params:
        - months: Number of months to look back (default: 6, max: 24)

    Returns:
        {
            uploads_by_month: [{month, count}],
            expirations_by_month: [{month, count}],
            risk_distribution_trend: [{month, critical, high, medium, low}]
        }
    """
    months = min(int(request.args.get('months', 6)), 24)

    conn = get_db_connection()
    cursor = conn.cursor()

    base_where = "(archived = 0 OR archived IS NULL)"

    # Calculate date range
    today = datetime.now().date()
    start_date = (today - timedelta(days=months * 30)).isoformat()

    trends = {
        'uploads_by_month': [],
        'expirations_by_month': [],
    }

    # Uploads by month
    cursor.execute(f"""
        SELECT
            strftime('%Y-%m', upload_date) as month,
            COUNT(*) as count
        FROM contracts
        WHERE {base_where} AND upload_date >= ?
        GROUP BY month
        ORDER BY month
    """, (start_date,))
    for row in cursor.fetchall():
        if row['month']:
            trends['uploads_by_month'].append({
                'month': row['month'],
                'count': row['count']
            })

    # Expirations by month (next 12 months)
    future_date = (today + timedelta(days=365)).isoformat()
    cursor.execute(f"""
        SELECT
            strftime('%Y-%m', expiration_date) as month,
            COUNT(*) as count
        FROM contracts
        WHERE {base_where}
        AND expiration_date BETWEEN ? AND ?
        AND status NOT IN ('expired', 'terminated')
        GROUP BY month
        ORDER BY month
    """, (today.isoformat(), future_date))
    for row in cursor.fetchall():
        if row['month']:
            trends['expirations_by_month'].append({
                'month': row['month'],
                'count': row['count']
            })

    conn.close()

    return jsonify({
        **trends,
        'period_months': months,
        'generated_at': datetime.now().isoformat()
    })


@dashboard_bp.route('/summary', methods=['GET'])
def get_summary():
    """
    Get a quick summary for dashboard header.

    Returns compact metrics for immediate display.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().date()
    d30 = (today + timedelta(days=30)).isoformat()
    base_where = "(archived = 0 OR archived IS NULL)"

    # Quick stats
    cursor.execute(f"SELECT COUNT(*) FROM contracts WHERE {base_where}")
    total = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM contracts WHERE {base_where} AND status = 'active'")
    active = cursor.fetchone()[0]

    cursor.execute(f"SELECT COALESCE(SUM(contract_value), 0) FROM contracts WHERE {base_where}")
    value = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND expiration_date BETWEEN ? AND ?
        AND status NOT IN ('expired', 'terminated')
    """, (today.isoformat(), d30))
    expiring_soon = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND risk_level IN ('CRITICAL', 'HIGH')
        AND status NOT IN ('expired', 'terminated', 'archived')
    """)
    high_risk = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(*) FROM contracts
        WHERE {base_where}
        AND status IN ('intake', 'review', 'negotiating')
    """)
    needs_attention = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        'total_contracts': total,
        'active_contracts': active,
        'total_value': value,
        'expiring_30d': expiring_soon,
        'high_risk': high_risk,
        'needs_attention': needs_attention,
        'generated_at': datetime.now().isoformat()
    })


def register_dashboard(app):
    """Register dashboard blueprint with Flask app."""
    app.register_blueprint(dashboard_bp)
    return dashboard_bp
