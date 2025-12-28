"""
CIP QA/QC API Blueprint

Flask API endpoints for the QA/QC system.
Follows existing health_api.py patterns.

Endpoints:
- GET  /api/qa/report         - Full QA report with all checks
- GET  /api/qa/dashboard      - Summary for dashboard widget
- GET  /api/contracts/<id>/qa - QA checks for specific contract
- POST /api/qa/run            - Trigger on-demand QA run
- POST /api/qa/fix/orphans    - Auto-fix orphaned records
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify

from qa_checks import (
    QACheckEngine,
    run_qa_checks,
    get_qa_dashboard_summary,
    fix_orphaned_records,
    CATEGORY_WEIGHTS
)

# Create blueprint
qa_bp = Blueprint('qa', __name__)

# Configuration
CIP_ROOT = Path(r"C:\Users\jrudy\CIP")
CONTRACTS_DB = CIP_ROOT / "data" / "contracts.db"


@qa_bp.route('/api/qa/report', methods=['GET'])
def get_qa_report():
    """
    Get full QA report with all checks.

    Query params:
    - category: Filter by category (data_quality, analysis_quality, process_quality, system_integrity)
    - severity: Filter results by severity (critical, high, medium, low)
    - contract_id: Check specific contract only

    Returns complete QA report with scores, checks, and recommendations.
    """
    try:
        category = request.args.get('category')
        severity = request.args.get('severity')
        contract_id = request.args.get('contract_id', type=int)

        # Validate category if provided
        if category and category not in CATEGORY_WEIGHTS:
            return jsonify({
                'error': f"Invalid category. Must be one of: {list(CATEGORY_WEIGHTS.keys())}"
            }), 400

        # Run checks
        report = run_qa_checks(contract_id=contract_id, category=category)

        # Convert to dict
        result = report.to_dict()

        # Filter by severity if requested
        if severity:
            result['checks'] = [c for c in result['checks'] if c['severity'] == severity]
            result['critical_issues'] = [c for c in result['critical_issues'] if c['severity'] == severity]

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@qa_bp.route('/api/qa/dashboard', methods=['GET'])
def get_qa_dashboard():
    """
    Get QA summary for dashboard widget.

    Returns compact summary with overall score, grade, and category status.
    """
    try:
        summary = get_qa_dashboard_summary()
        return jsonify(summary)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@qa_bp.route('/api/contracts/<int:contract_id>/qa', methods=['GET'])
def get_contract_qa(contract_id: int):
    """
    Get QA checks for a specific contract.

    Returns all applicable QA checks for the given contract.
    """
    try:
        # Verify contract exists
        conn = sqlite3.connect(str(CONTRACTS_DB))
        conn.row_factory = sqlite3.Row
        contract = conn.execute(
            "SELECT id, title FROM contracts WHERE id = ?", (contract_id,)
        ).fetchone()
        conn.close()

        if not contract:
            return jsonify({'error': f"Contract {contract_id} not found"}), 404

        # Run checks for this contract
        report = run_qa_checks(contract_id=contract_id)

        # Filter to only checks that affect this contract
        relevant_checks = [
            c for c in report.checks
            if contract_id in c.affected_ids or c.affected_count == 0
        ]

        return jsonify({
            'contract_id': contract_id,
            'contract_title': contract['title'],
            'overall_score': report.overall_score,
            'grade': report.grade,
            'grade_color': report.grade_color,
            'checks': [c.to_dict() for c in relevant_checks],
            'issues': [c.to_dict() for c in relevant_checks if not c.passed],
            'recommendations': [c.recommendation for c in relevant_checks if c.recommendation]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@qa_bp.route('/api/qa/run', methods=['POST'])
def run_qa():
    """
    Trigger on-demand QA run.

    Request body (optional):
    {
        "categories": ["data_quality", "system_integrity"],  // Run specific categories
        "contract_id": 123  // Check specific contract
    }

    Returns the full QA report.
    """
    try:
        data = request.get_json() or {}
        categories = data.get('categories', [])
        contract_id = data.get('contract_id')

        # Validate categories
        if categories:
            invalid = [c for c in categories if c not in CATEGORY_WEIGHTS]
            if invalid:
                return jsonify({
                    'error': f"Invalid categories: {invalid}. Valid: {list(CATEGORY_WEIGHTS.keys())}"
                }), 400

        # Run checks
        engine = QACheckEngine()

        if categories:
            # Run only specified categories
            for category in categories:
                engine.run_category_checks(category, contract_id)
            report = engine._generate_report()
        else:
            # Run all checks
            report = engine.run_all_checks(contract_id)

        # Log the QA run to audit log
        try:
            conn = sqlite3.connect(str(CONTRACTS_DB))
            conn.execute("""
                INSERT INTO audit_log (action, contract_id, user, details)
                VALUES (?, ?, ?, ?)
            """, (
                'qa_check_run',
                contract_id,
                'system',
                f'{{"score": {report.overall_score}, "grade": "{report.grade}", "passed": {report.passed_checks}, "failed": {report.failed_checks}}}'
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass  # Don't fail if audit logging fails

        return jsonify({
            'status': 'completed',
            'report': report.to_dict()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@qa_bp.route('/api/qa/fix/orphans', methods=['POST'])
def fix_orphans():
    """
    Auto-fix orphaned records by deleting them.

    Request body (optional):
    {
        "confirm": true  // Required to actually delete
    }

    Without confirm=true, returns preview of what would be deleted.
    With confirm=true, deletes orphaned records and returns counts.
    """
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)

        if not confirm:
            # Preview mode - show what would be deleted
            engine = QACheckEngine()

            # Run only orphan checks
            ra_result = engine.check_orphaned_risk_assessments()
            cl_result = engine.check_orphaned_clauses()
            sn_result = engine.check_orphaned_snapshots()

            return jsonify({
                'preview': True,
                'would_delete': {
                    'risk_assessments': ra_result.affected_count,
                    'clauses': cl_result.affected_count,
                    'snapshots': sn_result.details.get('analysis_orphans', 0)
                },
                'message': 'Set confirm=true to delete these records'
            })

        # Actually delete orphans
        deleted = fix_orphaned_records()

        # Log to audit
        try:
            conn = sqlite3.connect(str(CONTRACTS_DB))
            conn.execute("""
                INSERT INTO audit_log (action, user, details)
                VALUES (?, ?, ?)
            """, (
                'qa_fix_orphans',
                'system',
                str(deleted)
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return jsonify({
            'status': 'completed',
            'deleted': deleted,
            'message': f"Deleted {sum(deleted.values())} orphaned records"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@qa_bp.route('/api/qa/checks', methods=['GET'])
def list_checks():
    """
    List all available QA checks with their metadata.
    """
    checks = [
        # Data Quality
        {'id': 'metadata_completeness', 'name': 'Metadata Completeness', 'category': 'data_quality', 'severity': 'high'},
        {'id': 'duplicate_detection', 'name': 'Duplicate Detection', 'category': 'data_quality', 'severity': 'medium'},
        {'id': 'validation_rules', 'name': 'Validation Rules', 'category': 'data_quality', 'severity': 'high'},

        # Analysis Quality
        {'id': 'missing_risk_assessment', 'name': 'Missing Risk Assessment', 'category': 'analysis_quality', 'severity': 'critical'},
        {'id': 'low_confidence', 'name': 'Low Confidence Scores', 'category': 'analysis_quality', 'severity': 'high'},
        {'id': 'stale_analysis', 'name': 'Stale Analysis', 'category': 'analysis_quality', 'severity': 'medium'},
        {'id': 'clause_consistency', 'name': 'Clause Consistency', 'category': 'analysis_quality', 'severity': 'medium'},

        # Process Quality
        {'id': 'invalid_workflow_stage', 'name': 'Invalid Workflow Stage', 'category': 'process_quality', 'severity': 'high'},
        {'id': 'stale_intake', 'name': 'Stale Intake', 'category': 'process_quality', 'severity': 'medium'},
        {'id': 'audit_completeness', 'name': 'Audit Completeness', 'category': 'process_quality', 'severity': 'low'},

        # System Integrity
        {'id': 'orphaned_risk_assessments', 'name': 'Orphaned Risk Assessments', 'category': 'system_integrity', 'severity': 'critical'},
        {'id': 'orphaned_clauses', 'name': 'Orphaned Clauses', 'category': 'system_integrity', 'severity': 'critical'},
        {'id': 'orphaned_snapshots', 'name': 'Orphaned Snapshots', 'category': 'system_integrity', 'severity': 'high'},
        {'id': 'invalid_parent_references', 'name': 'Invalid Parent References', 'category': 'system_integrity', 'severity': 'high'},
        {'id': 'circular_relationships', 'name': 'Circular Relationships', 'category': 'system_integrity', 'severity': 'medium'},
    ]

    return jsonify({
        'total': len(checks),
        'categories': list(CATEGORY_WEIGHTS.keys()),
        'checks': checks
    })


# Register function for api.py
def register_qa(app):
    """Register QA blueprint with Flask app."""
    app.register_blueprint(qa_bp)
    return qa_bp
