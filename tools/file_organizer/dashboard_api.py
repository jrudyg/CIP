"""
Dashboard API - Flask Backend
REST API for file organizer web dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DASHBOARD_HOST, DASHBOARD_PORT, ARCHIVE_ROOT, DEBUG_MODE, validate_config
from database import (
    init_database, get_statistics, get_latest_scan,
    get_pending_duplicate_groups, approve_duplicate_group,
    unapprove_duplicate_group, get_archive_sessions, get_connection
)
from logger import setup_logger
from file_ops import validate_path_safety

# Initialize
app = Flask(__name__, static_folder='dashboard', static_url_path='')

# Restrict CORS to localhost only (Phase 2 security fix)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Rate limiting (Phase 2 security fix)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://"  # Use in-memory storage for simplicity
)

logger = setup_logger('dashboard_api')

@app.route('/')
def index():
    """Serve dashboard HTML"""
    return send_from_directory('dashboard', 'index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0'})

@app.route('/api/summary')
def get_summary():
    """
    Get overview statistics

    Returns:
        JSON with total files, duplicates, savings, etc.
    """
    try:
        stats = get_statistics()
        latest_scan = get_latest_scan()

        response = {
            'stats': stats,
            'latest_scan': latest_scan,
            'status': 'success'
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/duplicates')
def get_duplicates():
    """
    Get duplicate groups pending review

    Query params:
        limit: Maximum number of groups to return (default: 100)

    Returns:
        JSON array of duplicate groups
    """
    try:
        limit = request.args.get('limit', 100, type=int)

        # Validate limit bounds
        MAX_LIMIT = 1000
        MIN_LIMIT = 1
        if limit < MIN_LIMIT or limit > MAX_LIMIT:
            return jsonify({
                'status': 'error',
                'message': f'Limit must be between {MIN_LIMIT} and {MAX_LIMIT}'
            }), 400

        groups = get_pending_duplicate_groups(limit=limit)

        # Calculate total potential savings
        total_savings = sum(
            (g['total_size'] * (g['file_count'] - 1))
            for g in groups
        )

        response = {
            'groups': groups,
            'total_groups': len(groups),
            'total_savings_bytes': total_savings,
            'total_savings_mb': round(total_savings / (1024**2), 2),
            'status': 'success'
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error getting duplicates: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/duplicates/<int:group_id>/approve', methods=['POST'])
def approve_duplicate(group_id):
    """
    Approve a duplicate group for deletion

    Args:
        group_id: Duplicate group ID

    Body:
        {
            "keep_file": "path/to/file/to/keep"  // optional
        }

    Returns:
        JSON success/error response
    """
    try:
        data = request.get_json() or {}
        keep_file = data.get('keep_file')

        # Validate group_id is positive
        if group_id < 1:
            return jsonify({'status': 'error', 'message': 'Invalid group ID'}), 400

        # Get group members to validate paths
        with get_connection() as conn:
            members = conn.execute("""
                SELECT file_path FROM duplicate_members WHERE group_id = ?
            """, (group_id,)).fetchall()

            if not members:
                return jsonify({'status': 'error', 'message': f'Group {group_id} not found'}), 404

            # Validate all file paths are safe
            for member in members:
                file_path = Path(member['file_path'])
                if not validate_path_safety(file_path, ARCHIVE_ROOT.parent):
                    logger.warning(f"Unsafe path detected in group {group_id}: {file_path}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid file path detected in group'
                    }), 403

        # Validate keep_file if specified
        if keep_file:
            keep_path = Path(keep_file)
            if not validate_path_safety(keep_path, ARCHIVE_ROOT.parent):
                return jsonify({'status': 'error', 'message': 'Invalid keep_file path'}), 403
            # TODO: Update representative file if specified
            return jsonify({
                'status': 'error',
                'message': 'keep_file parameter not yet supported'
            }), 400

        # Approve group
        success = approve_duplicate_group(group_id)

        if success:
            logger.info(f"Approved duplicate group {group_id}")
            return jsonify({
                'status': 'success',
                'message': f'Group {group_id} approved for deletion',
                'group_id': group_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to approve group {group_id}'
            }), 500

    except Exception as e:
        logger.error(f"Error approving duplicate {group_id}: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/duplicates/<int:group_id>/unapprove', methods=['POST'])
def unapprove_duplicate(group_id):
    """
    Un-approve a duplicate group (revert to pending status)

    Args:
        group_id: Duplicate group ID

    Returns:
        JSON success/error response
    """
    try:
        # Validate group_id is positive
        if group_id < 1:
            return jsonify({'status': 'error', 'message': 'Invalid group ID'}), 400

        # Unapprove group
        success = unapprove_duplicate_group(group_id)

        if success:
            logger.info(f"Un-approved duplicate group {group_id}")
            return jsonify({
                'status': 'success',
                'message': f'Group {group_id} reverted to pending status',
                'group_id': group_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Group {group_id} not found or not approved'
            }), 404

    except Exception as e:
        logger.error(f"Error un-approving duplicate {group_id}: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/duplicates/bulk-approve', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter limit for bulk operations
def bulk_approve_duplicates():
    """
    Approve multiple duplicate groups at once

    Body:
        {
            "group_ids": [1, 2, 3, ...],
            "action": "approve" | "ignore"
        }

    Returns:
        JSON with results
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON body provided'}), 400

        group_ids = data.get('group_ids', [])
        action = data.get('action', 'approve')

        # Validate group_ids is a list
        if not isinstance(group_ids, list):
            return jsonify({'status': 'error', 'message': 'group_ids must be an array'}), 400

        if not group_ids:
            return jsonify({
                'status': 'error',
                'message': 'No group IDs provided'
            }), 400

        # Validate each ID is a positive integer
        for gid in group_ids:
            if not isinstance(gid, int) or gid < 1:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid group ID: {gid}. Must be positive integer.'
                }), 400

        # Validate action
        if action not in ['approve', 'ignore']:
            return jsonify({
                'status': 'error',
                'message': f'Invalid action: {action}. Must be "approve" or "ignore".'
            }), 400

        # Validate all file paths before processing
        with get_connection() as conn:
            for group_id in group_ids:
                members = conn.execute("""
                    SELECT file_path FROM duplicate_members WHERE group_id = ?
                """, (group_id,)).fetchall()

                if not members:
                    return jsonify({
                        'status': 'error',
                        'message': f'Group {group_id} not found'
                    }), 404

                # Validate paths
                for member in members:
                    file_path = Path(member['file_path'])
                    if not validate_path_safety(file_path, ARCHIVE_ROOT.parent):
                        logger.warning(f"Unsafe path in group {group_id}: {file_path}")
                        return jsonify({
                            'status': 'error',
                            'message': f'Invalid file path in group {group_id}'
                        }), 403

        # Use atomic transaction for all approvals
        approved = 0
        failed = 0

        if action == 'ignore':
            return jsonify({
                'status': 'error',
                'message': 'Ignore action not yet implemented'
            }), 501

        # Perform all approvals in a single transaction
        with get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")

                for group_id in group_ids:
                    try:
                        # Inline approval to use same transaction
                        cursor = conn.execute("""
                            UPDATE duplicate_groups
                            SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP
                            WHERE id = ? AND status = 'pending'
                        """, (group_id,))

                        if cursor.rowcount > 0:
                            approved += 1
                        else:
                            failed += 1
                            logger.warning(f"Group {group_id} not found or already processed")

                    except Exception as e:
                        logger.error(f"Error processing group {group_id}: {e}", exc_info=True)
                        # Rollback entire transaction on any error
                        conn.execute("ROLLBACK")
                        return jsonify({
                            'status': 'error',
                            'message': f'Transaction failed at group {group_id}: {str(e)}',
                            'approved': 0,
                            'failed': len(group_ids)
                        }), 500

                # Commit all changes atomically
                conn.execute("COMMIT")
                logger.info(f"Bulk approve: {approved} succeeded, {failed} not pending")

                return jsonify({
                    'status': 'success',
                    'approved': approved,
                    'failed': failed,
                    'total': len(group_ids)
                })

            except Exception as e:
                logger.error(f"Transaction error in bulk approve: {e}", exc_info=True)
                try:
                    conn.execute("ROLLBACK")
                except:
                    pass
                raise

    except Exception as e:
        logger.error(f"Error in bulk approve: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/archives')
def get_archives_api():
    """
    Get archive sessions

    Query params:
        limit: Maximum number of sessions (default: 50)

    Returns:
        JSON array of archive sessions
    """
    try:
        limit = request.args.get('limit', 50, type=int)

        # Validate limit bounds
        MAX_LIMIT = 1000
        MIN_LIMIT = 1
        if limit < MIN_LIMIT or limit > MAX_LIMIT:
            return jsonify({
                'status': 'error',
                'message': f'Limit must be between {MIN_LIMIT} and {MAX_LIMIT}'
            }), 400

        sessions = get_archive_sessions(limit=limit)

        response = {
            'sessions': sessions,
            'total_sessions': len(sessions),
            'status': 'success'
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error getting archives: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/scan/status')
def scan_status():
    """
    Get status of current/latest scan

    Returns:
        JSON with scan status
    """
    try:
        latest_scan = get_latest_scan()

        if latest_scan:
            return jsonify({
                'status': 'success',
                'scan': latest_scan,
                'has_scan': True
            })
        else:
            return jsonify({
                'status': 'success',
                'has_scan': False,
                'message': 'No scans found'
            })

    except Exception as e:
        logger.error(f"Error getting scan status: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/execute', methods=['POST'])
def execute_operations():
    """
    Execute approved operations (archive/delete)

    Body:
        {
            "dry_run": true | false,
            "group_ids": [1, 2, 3, ...]  // optional, defaults to all approved
        }

    Returns:
        JSON with execution results
    """
    try:
        data = request.get_json() or {}
        dry_run = data.get('dry_run', True)
        group_ids = data.get('group_ids')

        # TODO: Implement execution engine
        logger.warning("Execute operations not yet implemented")

        return jsonify({
            'status': 'error',
            'message': 'Execution not yet implemented - coming soon!',
            'dry_run': dry_run
        }), 501  # Not Implemented

    except Exception as e:
        logger.error(f"Error executing operations: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

def run_dashboard(host: str = DASHBOARD_HOST, port: int = DASHBOARD_PORT, debug: bool = DEBUG_MODE):
    """
    Run dashboard server

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode (defaults to DEBUG_MODE from config)
    """
    # Validate configuration first (Phase 2 security fix)
    try:
        validate_config()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Initialize database
    init_database()

    logger.info(f"Starting File Organizer Dashboard on http://{host}:{port}")
    logger.info(f"Debug mode: {'ENABLED' if debug else 'DISABLED'}")
    logger.info("Press Ctrl+C to stop")

    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_dashboard()  # Uses DEBUG_MODE from config, controlled by environment
