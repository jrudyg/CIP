"""
File Organizer - Main CLI Entry Point
Provides command-line interface for all file organization operations
"""

import argparse
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import GDRIVE_INDEX, ONEDRIVE_INDEX, DASHBOARD_HOST, DASHBOARD_PORT
from database import init_database, get_statistics, get_latest_scan, get_archive_sessions

def cmd_scan(args):
    """Run drive scan"""
    from scan_drive import scan_drive

    index_path = Path(args.index) if args.index else GDRIVE_INDEX

    print(f"Scanning: {index_path}")

    results = scan_drive(
        index_path=index_path,
        calculate_hashes=not args.no_hash,
        limit=args.limit
    )

    if args.report:
        from scan_drive import generate_summary_report
        report = generate_summary_report(results)
        print(report)

    return 0

def cmd_stats(args):
    """Show database statistics"""
    stats = get_statistics()

    print("\n" + "=" * 70)
    print("  File Organizer Statistics")
    print("=" * 70)
    print(f"\nDatabase Operations:")
    print(f"  Total operations logged:     {stats['total_operations']:,}")
    print(f"\nDuplicate Detection:")
    print(f"  Pending duplicate groups:    {stats['pending_duplicates']:,}")
    print(f"  Potential savings:           {stats['potential_savings_bytes'] / (1024**2):.1f} MB")
    print(f"\nArchive Management:")
    print(f"  Active archive sessions:     {stats['active_archives']:,}")

    # Get latest scan
    latest_scan = get_latest_scan()
    if latest_scan:
        print(f"\nLatest Scan:")
        print(f"  Date:                        {latest_scan['scan_date']}")
        print(f"  Files scanned:               {latest_scan['total_files']:,}")
        print(f"  Total size:                  {latest_scan['total_size'] / (1024**3):.2f} GB")
        print(f"  Duplicate groups found:      {latest_scan['duplicate_groups']:,}")
        print(f"  Similar groups found:        {latest_scan['similar_groups']:,}")

    print("=" * 70 + "\n")
    return 0

def cmd_dashboard(args):
    """Start web dashboard"""
    from dashboard_api import run_dashboard

    print(f"\nStarting File Organizer Dashboard...")
    print(f"Dashboard URL: http://{DASHBOARD_HOST}:{args.port}")
    print(f"\nOpen your browser and navigate to the URL above")
    print(f"Press Ctrl+C to stop the server\n")

    try:
        run_dashboard(host=DASHBOARD_HOST, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nDashboard stopped")
        return 0
    except Exception as e:
        print(f"\nError starting dashboard: {e}")
        return 1

def cmd_duplicates(args):
    """List duplicate groups"""
    from database import get_pending_duplicate_groups

    groups = get_pending_duplicate_groups(limit=args.limit)

    print(f"\n{'=' * 70}")
    print(f"  Duplicate Groups ({len(groups)} pending review)")
    print(f"{'=' * 70}\n")

    for i, group in enumerate(groups[:args.limit], 1):
        print(f"{i}. Hash: {group['hash'][:16]}...")
        print(f"   Files: {group['file_count']}")
        print(f"   Size: {group['total_size'] / (1024**2):.1f} MB per file")
        print(f"   Total: {(group['total_size'] * group['file_count']) / (1024**2):.1f} MB")
        print(f"   Savings: {(group['total_size'] * (group['file_count'] - 1)) / (1024**2):.1f} MB")
        print(f"   Keep: {group['representative_file']}")
        print(f"   Members:")
        for member in group['members']:
            marker = " (KEEP)" if member['keep'] else " (DELETE)"
            print(f"     - {member['file_path']}{marker}")
        print()

    return 0

def cmd_archives(args):
    """List archive sessions"""
    sessions = get_archive_sessions(limit=args.limit)

    print(f"\n{'=' * 70}")
    print(f"  Archive Sessions ({len(sessions)} found)")
    print(f"{'=' * 70}\n")

    for session in sessions:
        print(f"Session: {session['session_id']}")
        print(f"  Created:   {session['created_at']}")
        print(f"  Files:     {session['file_count']:,}")
        print(f"  Size:      {session['total_size'] / (1024**2):.1f} MB")
        print(f"  Status:    {session['status']}")
        print(f"  Location:  {session['archive_path']}")
        if session['notes']:
            print(f"  Notes:     {session['notes']}")
        print()

    return 0

def cmd_init(args):
    """Initialize database"""
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='File Organizer - Manage and cleanup duplicate files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full scan
  python main.py scan

  # Scan with test limit
  python main.py scan --limit 1000

  # Show statistics
  python main.py stats

  # List duplicate groups
  python main.py duplicates --limit 10

  # List archive sessions
  python main.py archives

  # Start dashboard
  python main.py dashboard
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan drive for duplicates')
    scan_parser.add_argument('--index', type=str, help='Path to directory_index.json')
    scan_parser.add_argument('--no-hash', action='store_true', help='Skip hash calculation')
    scan_parser.add_argument('--limit', type=int, help='Limit number of files')
    scan_parser.add_argument('--report', action='store_true', help='Generate summary report')
    scan_parser.set_defaults(func=cmd_scan)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)

    # Duplicates command
    dup_parser = subparsers.add_parser('duplicates', help='List duplicate groups')
    dup_parser.add_argument('--limit', type=int, default=20, help='Number of groups to show')
    dup_parser.set_defaults(func=cmd_duplicates)

    # Archives command
    arch_parser = subparsers.add_parser('archives', help='List archive sessions')
    arch_parser.add_argument('--limit', type=int, default=50, help='Number of sessions to show')
    arch_parser.set_defaults(func=cmd_archives)

    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Start web dashboard')
    dash_parser.add_argument('--port', type=int, default=DASHBOARD_PORT, help='Port number')
    dash_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    dash_parser.set_defaults(func=cmd_dashboard)

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')
    init_parser.set_defaults(func=cmd_init)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
