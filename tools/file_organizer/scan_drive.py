"""
Drive Scanner
Analyzes directory index, calculates hashes, detects duplicates and similar files
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

from config import GDRIVE_INDEX, MIN_FILE_SIZE_FOR_HASH, ARCHIVE_ROOT
from file_ops import (
    FileInfo, load_directory_index, calculate_file_hash, should_hash_file,
    find_duplicates_by_size, find_duplicates_by_hash, find_similar_files
)
from database import (
    init_database, log_scan_result, add_duplicate_group, log_operation
)

def scan_drive(index_path: Path, calculate_hashes: bool = True, limit: int = None) -> Dict:
    """
    Scan drive using existing directory index.

    Args:
        index_path: Path to directory_index.json
        calculate_hashes: Whether to calculate file hashes
        limit: Limit number of files to process (for testing)

    Returns:
        Dictionary with scan results
    """
    print(f"\n{'=' * 70}")
    print(f"  File Organizer - Drive Scan")
    print(f"{'=' * 70}\n")

    start_time = time.time()

    # Initialize database
    init_database()

    # Load directory index
    print(f"Loading directory index: {index_path}")
    all_files = load_directory_index(index_path)

    if limit:
        all_files = all_files[:limit]
        print(f"  Limited to {limit} files for testing")

    print(f"  Loaded {len(all_files):,} files")

    total_size = sum(f.size_bytes for f in all_files)
    print(f"  Total size: {total_size / (1024**3):.2f} GB")

    # Categorize files
    print(f"\nCategorizing files...")
    categorized = defaultdict(list)
    uncategorized = []

    for file_info in all_files:
        if file_info.category:
            categorized[file_info.category.name].append(file_info)
        else:
            uncategorized.append(file_info)

    print(f"  Categorized: {len(all_files) - len(uncategorized):,} files")
    print(f"  Uncategorized: {len(uncategorized):,} files")

    # Show category breakdown
    print(f"\n  Category Breakdown:")
    for cat_name, files in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        cat_size = sum(f.size_bytes for f in files)
        print(f"    {cat_name}: {len(files):,} files ({cat_size / (1024**2):.1f} MB)")

    # Find potential duplicates by size (cheap pre-filter)
    print(f"\nFinding potential duplicates...")
    size_groups = find_duplicates_by_size(all_files)
    print(f"  Found {len(size_groups):,} size groups with potential duplicates")

    # Calculate hashes for potential duplicates
    duplicate_groups = {}
    if calculate_hashes:
        print(f"\nCalculating hashes for duplicate detection...")

        # Flatten size groups and filter by criteria
        files_to_hash = []
        for size, files in size_groups.items():
            for file_info in files:
                if should_hash_file(file_info):
                    files_to_hash.append(file_info)

        print(f"  Files to hash: {len(files_to_hash):,}")

        # Calculate hashes with progress
        hashed_count = 0
        for i, file_info in enumerate(files_to_hash):
            if i % 100 == 0 and i > 0:
                print(f"    Progress: {i}/{len(files_to_hash)} ({i/len(files_to_hash)*100:.1f}%)")

            try:
                file_info.hash = calculate_file_hash(file_info.path)
                if file_info.hash:
                    hashed_count += 1
            except Exception as e:
                print(f"    Error hashing {file_info.path}: {e}")

        print(f"  Successfully hashed: {hashed_count:,} files")

        # Find exact duplicates by hash
        files_with_hashes = [f for f in files_to_hash if f.hash]
        duplicate_groups = find_duplicates_by_hash(files_with_hashes)

        print(f"  Found {len(duplicate_groups):,} duplicate groups")

        # Calculate potential savings
        total_savings = 0
        for hash_val, files in duplicate_groups.items():
            # Savings = total size - size of one file to keep
            group_size = files[0].size_bytes  # all same size
            savings = group_size * (len(files) - 1)
            total_savings += savings

        print(f"  Potential savings: {total_savings / (1024**2):.1f} MB")

        # Add duplicate groups to database
        print(f"\nSaving duplicate groups to database...")
        for hash_val, files in duplicate_groups.items():
            # Sort by modification date (keep newest)
            files_sorted = sorted(files, key=lambda f: f.modified_date, reverse=True)
            representative = files_sorted[0].path  # Keep newest

            # Prepare file data
            file_data = []
            for f in files_sorted:
                file_data.append({
                    'path': str(f.path),
                    'size': f.size_bytes,
                    'modified_date': f.modified_date.isoformat()
                })

            add_duplicate_group(hash_val, file_data, str(representative))

        print(f"  Saved {len(duplicate_groups):,} groups")

    # Find similar files (fuzzy matching)
    print(f"\nFinding similar files...")
    similar_groups = find_similar_files(all_files, threshold=0.85)
    print(f"  Found {len(similar_groups):,} similar file groups")

    # Show top similar groups
    if similar_groups:
        print(f"\n  Top 5 Similar Groups:")
        for i, group in enumerate(sorted(similar_groups, key=lambda g: g.total_size(), reverse=True)[:5]):
            print(f"    {i+1}. '{group.common_base}...' - {len(group.files)} files ({group.total_size() / (1024**2):.1f} MB)")

    # Calculate scan duration
    scan_duration = time.time() - start_time

    # Log scan result
    potential_savings = sum(
        f.size_bytes * (len(files) - 1)
        for files in duplicate_groups.values()
        if files
    )

    scan_id = log_scan_result(
        drive_path=str(index_path.parent),
        total_files=len(all_files),
        total_size=total_size,
        duplicate_groups=len(duplicate_groups),
        similar_groups=len(similar_groups),
        potential_savings=potential_savings,
        scan_duration=scan_duration,
        notes=f"Scan of {index_path.name}"
    )

    # Prepare results
    results = {
        'scan_id': scan_id,
        'scan_date': datetime.now().isoformat(),
        'index_path': str(index_path),
        'total_files': len(all_files),
        'total_size': total_size,
        'total_size_gb': round(total_size / (1024**3), 2),
        'categorized_files': len(all_files) - len(uncategorized),
        'uncategorized_files': len(uncategorized),
        'category_breakdown': {
            cat: len(files) for cat, files in categorized.items()
        },
        'duplicate_groups': len(duplicate_groups),
        'potential_savings_bytes': potential_savings,
        'potential_savings_mb': round(potential_savings / (1024**2), 1),
        'similar_groups': len(similar_groups),
        'scan_duration_seconds': round(scan_duration, 2)
    }

    # Save results to JSON
    output_dir = Path(__file__).parent
    output_file = output_dir / f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"  Scan Complete!")
    print(f"{'=' * 70}")
    print(f"  Duration: {scan_duration:.1f} seconds")
    print(f"  Results saved to: {output_file.name}")
    print(f"\n  Summary:")
    print(f"    Total files scanned: {results['total_files']:,}")
    print(f"    Total size: {results['total_size_gb']:.2f} GB")
    print(f"    Duplicate groups found: {results['duplicate_groups']:,}")
    print(f"    Potential space savings: {results['potential_savings_mb']:.1f} MB")
    print(f"    Similar file groups: {results['similar_groups']:,}")
    print(f"\n  Next steps:")
    print(f"    1. Review duplicate groups in database")
    print(f"    2. Use dashboard to approve deletions")
    print(f"    3. Execute approved operations")
    print(f"{'=' * 70}\n")

    return results

def generate_summary_report(results: Dict) -> str:
    """
    Generate human-readable summary report.

    Args:
        results: Scan results dictionary

    Returns:
        Formatted report string
    """
    report = f"""
================================================================================
  FILE ORGANIZER SCAN REPORT
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

SCAN OVERVIEW
-------------
Drive/Index:        {results['index_path']}
Scan Date:          {results['scan_date']}
Duration:           {results['scan_duration_seconds']} seconds

FILE STATISTICS
---------------
Total Files:        {results['total_files']:,}
Total Size:         {results['total_size_gb']} GB
Categorized:        {results['categorized_files']:,}
Uncategorized:      {results['uncategorized_files']:,}

CATEGORY BREAKDOWN
------------------
"""

    for category, count in sorted(results['category_breakdown'].items(), key=lambda x: x[1], reverse=True):
        report += f"{category:<30} {count:>10,} files\n"

    report += f"""
DUPLICATE ANALYSIS
------------------
Duplicate Groups:   {results['duplicate_groups']:,}
Potential Savings:  {results['potential_savings_mb']:.1f} MB

SIMILAR FILES
-------------
Similar Groups:     {results['similar_groups']:,}

RECOMMENDATIONS
---------------
1. Review duplicate groups - {results['duplicate_groups']} groups found
2. Potential space savings: {results['potential_savings_mb']:.1f} MB
3. Check similar files for consolidation opportunities

================================================================================
"""

    return report

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scan drive for duplicates and organize files')
    parser.add_argument('--index', type=str, default=str(GDRIVE_INDEX),
                        help='Path to directory_index.json')
    parser.add_argument('--no-hash', action='store_true',
                        help='Skip hash calculation (faster, size-only detection)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of files to process (for testing)')
    parser.add_argument('--report', action='store_true',
                        help='Generate summary report')

    args = parser.parse_args()

    # Run scan
    results = scan_drive(
        index_path=Path(args.index),
        calculate_hashes=not args.no_hash,
        limit=args.limit
    )

    # Generate report if requested
    if args.report:
        report = generate_summary_report(results)
        report_file = Path(__file__).parent / f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\nDetailed report saved to: {report_file.name}")
        print(report)
