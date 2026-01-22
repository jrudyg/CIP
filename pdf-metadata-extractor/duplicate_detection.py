import json
import re
from pathlib import Path
from collections import defaultdict

# Load results
json_path = list(Path("outputs/full_portfolio/exports").glob("metadata_export_*.json"))[0]
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['pdfs']

print(f"\n{'='*80}")
print("PHASE 3: DUPLICATE DETECTION ANALYSIS")
print(f"{'='*80}")

# Group by base filename (removing signed/unsigned/executed suffixes)
contracts = defaultdict(list)

for result in results:
    filename = result['document_metadata']['filename']
    basename = Path(filename).stem.lower()
    
    # Remove common suffixes
    for suffix in [' - signed', ' signed', ' - executed', ' executed', 
                   ' unsigned', ' - unsigned', ' - draft', ' draft',
                   ' - for execution', ' for execution', ' final',
                   ' - final', 'fully executed', '- fully executed']:
        basename = basename.replace(suffix, '')
    
    # Remove trailing numbers and dates
    basename = re.sub(r'\s+\d{1,2}\.\d{1,2}\.\d{2,4}$', '', basename)
    basename = re.sub(r'\s+\d{4}-\d{2}-\d{2}$', '', basename)
    basename = re.sub(r'\s+\d+$', '', basename)
    basename = basename.strip()
    
    contracts[basename].append(result)

# Find duplicates
duplicates = {k: v for k, v in contracts.items() if len(v) > 1}

print(f"\nTotal unique contract names (normalized): {len(contracts)}")
print(f"Contracts with multiple versions: {len(duplicates)}")
print(f"Total files: {sum(len(v) for v in contracts.values())}")
print(f"Duplicate files: {sum(len(v) for v in duplicates.values())}")

# Analyze duplicate patterns
print(f"\n{'='*80}")
print("DUPLICATE PATTERNS")
print(f"{'='*80}")

signed_unsigned_pairs = 0
execution_status_mismatch = 0
duplicate_triads = []

for basename, versions in duplicates.items():
    if len(versions) > 2:
        duplicate_triads.append((basename, versions))
    
    # Check for signed/unsigned pairs
    filenames = [v['document_metadata']['filename'].lower() for v in versions]
    has_signed = any('signed' in f or 'executed' in f for f in filenames)
    has_unsigned = any('unsigned' in f or 'draft' in f for f in filenames)
    
    if has_signed and has_unsigned:
        signed_unsigned_pairs += 1
    
    # Check for execution status mismatch
    statuses = set(v['execution_status'] for v in versions)
    if len(statuses) > 1:
        execution_status_mismatch += 1

print(f"Signed/Unsigned pairs: {signed_unsigned_pairs}")
print(f"Contracts with >=3 versions: {len(duplicate_triads)}")
print(f"Execution status mismatches: {execution_status_mismatch}")

# Show top 10 duplicate groups
print(f"\n{'='*80}")
print("TOP 10 DUPLICATE GROUPS")
print(f"{'='*80}")

sorted_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
for i, (basename, versions) in enumerate(sorted_dupes[:10], 1):
    print(f"\n{i}. {basename[:70]} ({len(versions)} versions)")
    for v in versions:
        filename = Path(v['document_metadata']['filename']).name
        status = v['execution_status']
        has_sig = "Y" if v['has_digital_signatures'] else "✗"
        print(f"   [{status:18s}] {has_sig} {filename[:60]}")

# Export duplicates
duplicate_report = []
for basename, versions in sorted_dupes:
    duplicate_report.append({
        'normalized_name': basename,
        'version_count': len(versions),
        'versions': [{
            'filename': v['document_metadata']['filename'],
            'file_path': v['document_metadata']['file_path'],
            'execution_status': v['execution_status'],
            'has_signatures': v['has_digital_signatures'],
            'confidence': v['execution_confidence'],
            'file_size': v['document_metadata']['file_size']
        } for v in versions]
    })

with open('outputs/full_portfolio/duplicate_contracts.json', 'w', encoding='utf-8') as f:
    json.dump(duplicate_report, f, indent=2)

print(f"\n\nDuplicate analysis exported to: outputs/full_portfolio/duplicate_contracts.json")
