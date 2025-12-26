"""
CIP System Health Check
Validates all system components and configurations
"""

import sys
from pathlib import Path
import sqlite3
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import (
        ANTHROPIC_API_KEY,
        DEFAULT_MODEL,
        CONTRACTS_DB,
        REPORTS_DB,
        UPLOAD_DIRECTORY,
        API_HOST,
        API_PORT
    )
    config_loaded = True
except ImportError as e:
    print(f"[ERROR] Could not load config: {e}")
    config_loaded = False

def check_mark(passed: bool) -> str:
    """Return checkmark or X"""
    return "[OK]  " if passed else "[FAIL]"

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 8
    print(f"{check_mark(passed)} Python {version.major}.{version.minor}.{version.micro}")
    return passed

def check_config():
    """Check configuration"""
    if not config_loaded:
        print("[FAIL] Configuration file")
        return False

    checks = [
        ("Anthropic API key configured", bool(ANTHROPIC_API_KEY)),
        ("Default model set", bool(DEFAULT_MODEL)),
        ("API host configured", bool(API_HOST)),
        ("API port configured", bool(API_PORT)),
    ]

    all_passed = True
    for name, passed in checks:
        print(f"{check_mark(passed)} {name}")
        if not passed:
            all_passed = False

    return all_passed

def check_directories():
    """Check required directories exist"""
    base_dir = Path(__file__).parent.parent

    required_dirs = [
        ("Data directory", base_dir / "data"),
        ("Uploads directory", UPLOAD_DIRECTORY if config_loaded else None),
        ("Logs directory", base_dir / "logs"),
        ("Backups directory", base_dir / "backups"),
        ("Frontend directory", base_dir / "frontend"),
        ("Backend directory", base_dir / "backend"),
        ("Docs directory", base_dir / "docs"),
    ]

    all_passed = True
    for name, path in required_dirs:
        if path is None:
            print(f"[SKIP] {name}")
            continue

        passed = path.exists() and path.is_dir()
        print(f"{check_mark(passed)} {name}: {path}")
        if not passed:
            all_passed = False

    return all_passed

def check_databases():
    """Check database files and integrity"""
    if not config_loaded:
        print("[SKIP] Database checks (config not loaded)")
        return False

    databases = [
        ("Contracts database", CONTRACTS_DB),
        ("Reports database", REPORTS_DB),
    ]

    all_passed = True
    for name, db_path in databases:
        if not db_path.exists():
            print(f"[FAIL] {name} not found: {db_path}")
            all_passed = False
            continue

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            if result == "ok":
                # Get size
                size_kb = db_path.stat().st_size / 1024
                print(f"[OK]   {name}: {size_kb:.1f} KB (integrity OK)")
            else:
                print(f"[FAIL] {name}: integrity check failed")
                all_passed = False

            conn.close()

        except Exception as e:
            print(f"[FAIL] {name}: {str(e)}")
            all_passed = False

    return all_passed

def check_required_files():
    """Check required files exist"""
    base_dir = Path(__file__).parent.parent

    required_files = [
        ("API script", base_dir / "backend" / "api.py"),
        ("Orchestrator", base_dir / "backend" / "orchestrator.py"),
        ("Config", base_dir / "backend" / "config.py"),
        ("Logger config", base_dir / "backend" / "logger_config.py"),
        ("UI components", base_dir / "frontend" / "ui_components.py"),
        ("Error handler", base_dir / "frontend" / "error_handler.py"),
        ("Progress indicators", base_dir / "frontend" / "progress_indicators.py"),
        (".gitignore", base_dir / ".gitignore"),
        ("Requirements", base_dir / "requirements.txt"),
    ]

    all_passed = True
    for name, file_path in required_files:
        passed = file_path.exists() and file_path.is_file()
        print(f"{check_mark(passed)} {name}: {file_path.name}")
        if not passed:
            all_passed = False

    return all_passed

def check_api_server():
    """Check if API server is running"""
    if not config_loaded:
        print("[SKIP] API server check (config not loaded)")
        return False

    try:
        url = f"http://{API_HOST}:{API_PORT}/health"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"[OK]   API server running at {API_HOST}:{API_PORT}")
            print(f"       Status: {data.get('status')}")
            print(f"       Orchestrator: {data.get('orchestrator')}")
            return True
        else:
            print(f"[FAIL] API server responded with status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"[WARN] API server not running at {API_HOST}:{API_PORT}")
        print(f"       Run: python backend/api.py")
        return False

    except Exception as e:
        print(f"[ERROR] API server check failed: {e}")
        return False

def check_logs():
    """Check log files"""
    log_dir = Path(__file__).parent.parent / "logs"

    if not log_dir.exists():
        print("[WARN] Logs directory not found")
        return False

    log_files = list(log_dir.glob("*.log"))

    if not log_files:
        print("[INFO] No log files found (normal for fresh install)")
        return True

    print(f"[OK]   Found {len(log_files)} log file(s):")
    for log_file in log_files:
        size_kb = log_file.stat().st_size / 1024
        print(f"       - {log_file.name}: {size_kb:.1f} KB")

    return True

def check_database_tables():
    """Check database tables exist"""
    if not config_loaded or not CONTRACTS_DB.exists():
        print("[SKIP] Database table checks")
        return False

    required_tables = [
        'contracts', 'clauses', 'risk_assessments',
        'analysis_snapshots', 'comparison_snapshots',
        'redline_snapshots', 'contract_relationships', 'audit_log'
    ]

    try:
        conn = sqlite3.connect(str(CONTRACTS_DB))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        all_passed = True
        for table in required_tables:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"[OK]   Table '{table}': {count} records")
            else:
                print(f"[FAIL] Table '{table}' not found")
                all_passed = False

        conn.close()
        return all_passed

    except Exception as e:
        print(f"[ERROR] Table check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("CIP System Health Check")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    print("1. Python Environment")
    print("-" * 70)
    results['python'] = check_python_version()
    print()

    print("2. Configuration")
    print("-" * 70)
    results['config'] = check_config()
    print()

    print("3. Directories")
    print("-" * 70)
    results['directories'] = check_directories()
    print()

    print("4. Required Files")
    print("-" * 70)
    results['files'] = check_required_files()
    print()

    print("5. Databases")
    print("-" * 70)
    results['databases'] = check_databases()
    print()

    print("6. Database Tables")
    print("-" * 70)
    results['tables'] = check_database_tables()
    print()

    print("7. Log Files")
    print("-" * 70)
    results['logs'] = check_logs()
    print()

    print("8. API Server")
    print("-" * 70)
    results['api'] = check_api_server()
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {check.title():20} {status}")

    print()
    print(f"Overall: {passed}/{total} checks passed")

    if passed == total:
        print("\nStatus: All systems operational")
        sys.exit(0)
    elif passed >= total * 0.75:
        print("\nStatus: System operational with warnings")
        sys.exit(0)
    else:
        print("\nStatus: Critical issues detected")
        sys.exit(1)
