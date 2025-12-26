#!/usr/bin/env python
"""
CIP Monitor - Real-time monitoring for Contract Intelligence Platform

Usage:
    python cip_monitor.py [--log-level LEVEL] [--refresh N] [--no-color] [--tail-only]
    python cip_monitor.py health
    python cip_monitor.py logs [--file FILE] [--lines N]
    python cip_monitor.py errors
"""

import argparse
import sys
import time
import threading
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import requests
from colorama import init, Fore, Back, Style

from config import (
    API_BASE_URL, HEALTH_ENDPOINT, CONTRACTS_DB, REPORTS_DB,
    LOG_FILES, COLORS, DEFAULT_LOG_LINES, DEFAULT_REFRESH_INTERVAL,
    HEALTH_CHECK_TIMEOUT,
)
from log_parser import LogParser, LogLevel, LogEntry, LogTailer

# Initialize colorama for Windows
init()


class HealthMonitor:
    """Monitor backend health."""

    def __init__(self, endpoint: str = HEALTH_ENDPOINT):
        self.endpoint = endpoint
        self.last_check = None
        self.last_status = None

    def check(self) -> dict:
        """Check backend health."""
        try:
            resp = requests.get(self.endpoint, timeout=HEALTH_CHECK_TIMEOUT)
            self.last_check = datetime.now()

            if resp.ok:
                self.last_status = resp.json()
                self.last_status['_ok'] = True
            else:
                self.last_status = {'_ok': False, 'error': f'HTTP {resp.status_code}'}

        except requests.exceptions.ConnectionError:
            self.last_status = {'_ok': False, 'error': 'Connection refused'}
        except requests.exceptions.Timeout:
            self.last_status = {'_ok': False, 'error': 'Timeout'}
        except Exception as e:
            self.last_status = {'_ok': False, 'error': str(e)}

        return self.last_status


class DatabaseStats:
    """Get database statistics."""

    @staticmethod
    def get_stats() -> dict:
        """Get database statistics."""
        stats = {
            'contracts_db': {'exists': False, 'size': 0, 'contracts': 0},
            'reports_db': {'exists': False, 'size': 0},
        }

        # Contracts DB
        if CONTRACTS_DB.exists():
            stats['contracts_db']['exists'] = True
            stats['contracts_db']['size'] = CONTRACTS_DB.stat().st_size

            try:
                conn = sqlite3.connect(str(CONTRACTS_DB))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM contracts")
                stats['contracts_db']['contracts'] = cursor.fetchone()[0]
                conn.close()
            except:
                pass

        # Reports DB
        if REPORTS_DB.exists():
            stats['reports_db']['exists'] = True
            stats['reports_db']['size'] = REPORTS_DB.stat().st_size

        return stats


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    """Print a header."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}\n")


def print_status(label: str, ok: bool, detail: str = ""):
    """Print a status line."""
    status = f"{Fore.GREEN}OK{Style.RESET_ALL}" if ok else f"{Fore.RED}FAIL{Style.RESET_ALL}"
    detail_str = f" ({detail})" if detail else ""
    print(f"  {label:20} [{status}]{detail_str}")


def format_bytes(size: int) -> str:
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def cmd_health(args):
    """Check system health."""
    print_header("CIP System Health Check")

    # Backend health
    print(f"{Fore.YELLOW}Backend API:{Style.RESET_ALL}")
    monitor = HealthMonitor()
    status = monitor.check()

    print_status("API Status", status.get('_ok', False),
                 status.get('status', status.get('error', '')))

    if status.get('_ok'):
        print_status("Orchestrator", status.get('orchestrator', False))
        print_status("API Key", status.get('api_key_configured', False))

        db_status = status.get('database', {})
        print_status("Contracts DB", db_status.get('contracts', False))
        print_status("Reports DB", db_status.get('reports', False))

    # Database stats
    print(f"\n{Fore.YELLOW}Database Statistics:{Style.RESET_ALL}")
    db_stats = DatabaseStats.get_stats()

    contracts = db_stats['contracts_db']
    print_status("contracts.db", contracts['exists'],
                 f"{format_bytes(contracts['size'])}, {contracts['contracts']} contracts")

    reports = db_stats['reports_db']
    print_status("reports.db", reports['exists'],
                 f"{format_bytes(reports['size'])}")

    # Log files
    print(f"\n{Fore.YELLOW}Log Files:{Style.RESET_ALL}")
    for name, path in LOG_FILES.items():
        exists = path.exists()
        size = format_bytes(path.stat().st_size) if exists else "N/A"
        print_status(f"{name}.log", exists, size)

    print()


def cmd_logs(args):
    """View log files."""
    log_name = args.file or "cip"
    log_path = LOG_FILES.get(log_name)

    if not log_path:
        print(f"{Fore.RED}Unknown log file: {log_name}{Style.RESET_ALL}")
        print(f"Available: {', '.join(LOG_FILES.keys())}")
        return

    if not log_path.exists():
        print(f"{Fore.RED}Log file not found: {log_path}{Style.RESET_ALL}")
        return

    parser = LogParser()
    min_level = LogLevel.from_string(args.level)
    entries = parser.parse_file(log_path, limit=args.lines, min_level=min_level)

    print_header(f"Log: {log_name}.log ({len(entries)} entries)")

    for entry in entries:
        print(entry.colored(use_color=not args.no_color))

    print()


def cmd_errors(args):
    """View recent errors."""
    print_header("Recent Errors")

    parser = LogParser()
    error_log = LOG_FILES.get("error")

    if error_log and error_log.exists():
        entries = parser.parse_file(error_log, limit=args.lines, min_level=LogLevel.ERROR)

        if entries:
            for entry in entries:
                print(entry.colored(use_color=not args.no_color))
        else:
            print(f"{Fore.GREEN}No recent errors!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Error log not found{Style.RESET_ALL}")

    print()


def cmd_tail(args):
    """Tail log files in real-time."""
    log_name = args.file or "cip"
    log_path = LOG_FILES.get(log_name)

    if not log_path:
        print(f"{Fore.RED}Unknown log file: {log_name}{Style.RESET_ALL}")
        return

    print_header(f"Tailing: {log_name}.log (Ctrl+C to stop)")

    parser = LogParser()
    min_level = LogLevel.from_string(args.level)

    def on_entry(entry: LogEntry):
        print(entry.colored(use_color=not args.no_color))

    tailer = parser.tail_file(log_path, on_entry, min_level)
    tailer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopped{Style.RESET_ALL}")
        tailer.stop()


def cmd_dashboard(args):
    """Show monitoring dashboard."""
    print_header("CIP Monitor Dashboard")
    print(f"{Fore.YELLOW}Press Ctrl+C to exit{Style.RESET_ALL}\n")

    monitor = HealthMonitor()
    parser = LogParser()

    try:
        while True:
            clear_screen()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.CYAN}{Style.BRIGHT}CIP Monitor{Style.RESET_ALL}  {Fore.WHITE}{now}{Style.RESET_ALL}\n")

            # Health status
            status = monitor.check()
            api_ok = status.get('_ok', False)
            api_status = f"{Fore.GREEN}ONLINE{Style.RESET_ALL}" if api_ok else f"{Fore.RED}OFFLINE{Style.RESET_ALL}"
            print(f"  API: {api_status}")

            if api_ok:
                db = status.get('database', {})
                db_ok = db.get('contracts', False) and db.get('reports', False)
                db_status = f"{Fore.GREEN}OK{Style.RESET_ALL}" if db_ok else f"{Fore.RED}ERROR{Style.RESET_ALL}"
                print(f"  DB:  {db_status}")

            # Database stats
            db_stats = DatabaseStats.get_stats()
            contracts = db_stats['contracts_db']['contracts']
            print(f"  Contracts: {contracts}")

            # Recent errors
            print(f"\n{Fore.YELLOW}Recent Errors:{Style.RESET_ALL}")
            error_log = LOG_FILES.get("error")
            if error_log and error_log.exists():
                entries = parser.parse_file(error_log, limit=5, min_level=LogLevel.ERROR)
                if entries:
                    for entry in entries[-5:]:
                        ts = entry.timestamp.strftime("%H:%M:%S")
                        msg = entry.message[:60] + "..." if len(entry.message) > 60 else entry.message
                        print(f"  {Fore.RED}{ts}{Style.RESET_ALL} {msg}")
                else:
                    print(f"  {Fore.GREEN}No recent errors{Style.RESET_ALL}")

            # Recent activity
            print(f"\n{Fore.YELLOW}Recent Activity:{Style.RESET_ALL}")
            cip_log = LOG_FILES.get("cip")
            if cip_log and cip_log.exists():
                entries = parser.parse_file(cip_log, limit=10, min_level=LogLevel.INFO)
                for entry in entries[-5:]:
                    ts = entry.timestamp.strftime("%H:%M:%S")
                    level_color = {
                        LogLevel.INFO: Fore.GREEN,
                        LogLevel.WARNING: Fore.YELLOW,
                        LogLevel.ERROR: Fore.RED,
                    }.get(entry.level, Fore.WHITE)
                    msg = entry.message[:60] + "..." if len(entry.message) > 60 else entry.message
                    print(f"  {Fore.WHITE}{ts}{Style.RESET_ALL} {level_color}{entry.level.value:8}{Style.RESET_ALL} {msg}")

            print(f"\n{Fore.WHITE}Refreshing in {args.refresh}s... (Ctrl+C to exit){Style.RESET_ALL}")
            time.sleep(args.refresh)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopped{Style.RESET_ALL}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CIP Monitor - Real-time monitoring for Contract Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Health command
    health_parser = subparsers.add_parser("health", help="Check system health")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View log files")
    logs_parser.add_argument(
        "--file", "-f", choices=list(LOG_FILES.keys()),
        default="cip", help="Log file to view (default: cip)"
    )
    logs_parser.add_argument(
        "--lines", "-n", type=int, default=DEFAULT_LOG_LINES,
        help=f"Number of lines (default: {DEFAULT_LOG_LINES})"
    )
    logs_parser.add_argument(
        "--level", "-l", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO", help="Minimum log level (default: INFO)"
    )

    # Errors command
    errors_parser = subparsers.add_parser("errors", help="View recent errors")
    errors_parser.add_argument(
        "--lines", "-n", type=int, default=20,
        help="Number of errors (default: 20)"
    )

    # Tail command
    tail_parser = subparsers.add_parser("tail", help="Tail log files in real-time")
    tail_parser.add_argument(
        "--file", "-f", choices=list(LOG_FILES.keys()),
        default="cip", help="Log file to tail (default: cip)"
    )
    tail_parser.add_argument(
        "--level", "-l", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO", help="Minimum log level (default: INFO)"
    )

    # Dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Show monitoring dashboard")
    dash_parser.add_argument(
        "--refresh", "-r", type=int, default=DEFAULT_REFRESH_INTERVAL,
        help=f"Refresh interval in seconds (default: {DEFAULT_REFRESH_INTERVAL})"
    )

    args = parser.parse_args()

    # Default to health if no command
    if not args.command:
        args.command = "health"
        cmd_health(args)
        return

    # Dispatch command
    commands = {
        "health": cmd_health,
        "logs": cmd_logs,
        "errors": cmd_errors,
        "tail": cmd_tail,
        "dashboard": cmd_dashboard,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
