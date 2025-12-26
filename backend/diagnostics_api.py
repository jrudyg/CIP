"""
CIP Diagnostics API Endpoints

Provides endpoints for system monitoring and debugging:
- /api/diagnostics/logs - View log files
- /api/diagnostics/api-history - Recent API call history
- /api/diagnostics/db-stats - Database statistics
- /api/diagnostics/system-resources - CPU/Memory/Disk usage
"""

import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import psutil
from flask import Blueprint, request, jsonify

# Create blueprint
diagnostics_bp = Blueprint('diagnostics', __name__, url_prefix='/api/diagnostics')

# Configuration
CIP_ROOT = Path(r"C:\Users\jrudy\CIP")
LOG_DIR = CIP_ROOT / "logs"
DATA_DIR = CIP_ROOT / "data"
CONTRACTS_DB = DATA_DIR / "contracts.db"
REPORTS_DB = DATA_DIR / "reports.db"

LOG_FILES = {
    "cip": LOG_DIR / "cip.log",
    "error": LOG_DIR / "error.log",
    "api": LOG_DIR / "api.log",
}

# Log parsing pattern
LOG_PATTERN = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?) - '  # timestamp
    r'(\S+) - '                                               # logger name
    r'(DEBUG|INFO|WARNING|ERROR|CRITICAL) - '                 # level
    r'(?:\[(\S+):(\d+)\] - )?'                                # optional file:line
    r'(.+)'                                                   # message
)

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def parse_log_line(line: str) -> Optional[Dict]:
    """Parse a single log line."""
    line = line.strip()
    if not line:
        return None

    match = LOG_PATTERN.match(line)
    if not match:
        return {
            "timestamp": datetime.now().isoformat(),
            "logger": "unknown",
            "level": "INFO",
            "message": line,
        }

    groups = match.groups()
    return {
        "timestamp": groups[0],
        "logger": groups[1],
        "level": groups[2],
        "file": groups[3],
        "line": int(groups[4]) if groups[4] else None,
        "message": groups[5],
    }


def parse_log_file(filepath: Path, limit: int = 100, min_level: str = "INFO") -> List[Dict]:
    """Parse last N lines from a log file."""
    entries = []
    min_level_idx = LOG_LEVELS.index(min_level) if min_level in LOG_LEVELS else 1

    if not filepath.exists():
        return entries

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                entry = parse_log_line(line)
                if entry:
                    level_idx = LOG_LEVELS.index(entry["level"]) if entry["level"] in LOG_LEVELS else 1
                    if level_idx >= min_level_idx:
                        entries.append(entry)
    except Exception as e:
        entries.append({
            "timestamp": datetime.now().isoformat(),
            "logger": "diagnostics",
            "level": "ERROR",
            "message": f"Error reading log: {e}",
        })

    return entries


@diagnostics_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    Get log entries from specified log file.

    Query params:
        - file: cip|error|api (default: cip)
        - level: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
        - limit: 1-1000 (default: 100)

    Returns:
        {entries: [...], total: int, file: str}
    """
    log_name = request.args.get('file', 'cip')
    level = request.args.get('level', 'INFO').upper()
    limit = min(max(int(request.args.get('limit', 100)), 1), 1000)

    log_path = LOG_FILES.get(log_name)
    if not log_path:
        return jsonify({
            'error': f'Unknown log file: {log_name}',
            'available': list(LOG_FILES.keys())
        }), 400

    entries = parse_log_file(log_path, limit=limit, min_level=level)

    return jsonify({
        'entries': entries,
        'total': len(entries),
        'file': log_name,
        'level': level,
    })


@diagnostics_bp.route('/api-history', methods=['GET'])
def get_api_history():
    """
    Get recent API call history from api.log.

    Query params:
        - limit: 1-100 (default: 50)

    Returns:
        {calls: [...], total: int}
    """
    limit = min(max(int(request.args.get('limit', 50)), 1), 100)

    api_log = LOG_FILES.get("api")
    if not api_log or not api_log.exists():
        return jsonify({'calls': [], 'total': 0, 'note': 'API log not found'})

    # Parse API log for request/response patterns
    calls = []
    request_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?(GET|POST|PUT|DELETE)\s+(/\S+).*?(\d{3})?')

    try:
        with open(api_log, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()[-limit*2:]  # Read more lines to find matches
            for line in lines:
                match = request_pattern.search(line)
                if match:
                    calls.append({
                        'timestamp': match.group(1),
                        'method': match.group(2),
                        'endpoint': match.group(3),
                        'status': int(match.group(4)) if match.group(4) else None,
                    })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'calls': calls[-limit:],
        'total': len(calls[-limit:]),
    })


@diagnostics_bp.route('/db-stats', methods=['GET'])
def get_db_stats():
    """
    Get database statistics.

    Returns:
        {
            contracts_db: {exists, size_bytes, tables: {name: row_count}},
            reports_db: {exists, size_bytes, tables: {name: row_count}}
        }
    """
    stats = {}

    for db_name, db_path in [('contracts_db', CONTRACTS_DB), ('reports_db', REPORTS_DB)]:
        db_stats = {
            'exists': db_path.exists(),
            'size_bytes': 0,
            'size_human': '0 B',
            'tables': {},
        }

        if db_path.exists():
            db_stats['size_bytes'] = db_path.stat().st_size
            db_stats['size_human'] = format_bytes(db_stats['size_bytes'])

            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]

                # Get row count for each table
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        db_stats['tables'][table] = cursor.fetchone()[0]
                    except:
                        db_stats['tables'][table] = -1

                conn.close()
            except Exception as e:
                db_stats['error'] = str(e)

        stats[db_name] = db_stats

    return jsonify(stats)


@diagnostics_bp.route('/system-resources', methods=['GET'])
def get_system_resources():
    """
    Get system resource usage.

    Returns:
        {
            cpu_percent, memory_percent, memory_used_gb,
            disk_percent, disk_free_gb,
            process: {pid, cpu_percent, memory_mb}
        }
    """
    # System-wide stats
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('C:/')

    # Current process stats
    process = psutil.Process(os.getpid())
    proc_memory = process.memory_info()

    return jsonify({
        'cpu_percent': cpu,
        'memory_percent': memory.percent,
        'memory_used_gb': round(memory.used / (1024**3), 2),
        'memory_total_gb': round(memory.total / (1024**3), 2),
        'disk_percent': disk.percent,
        'disk_free_gb': round(disk.free / (1024**3), 2),
        'disk_total_gb': round(disk.total / (1024**3), 2),
        'process': {
            'pid': process.pid,
            'cpu_percent': process.cpu_percent(),
            'memory_mb': round(proc_memory.rss / (1024**2), 2),
        },
        'timestamp': datetime.now().isoformat(),
    })


def format_bytes(size: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def register_diagnostics(app):
    """Register diagnostics blueprint with Flask app."""
    app.register_blueprint(diagnostics_bp)
    return diagnostics_bp
