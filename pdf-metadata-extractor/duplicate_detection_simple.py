import json
import re
from pathlib import Path
from collections import defaultdict

json_path = list(Path("outputs/full_portfolio/exports").glob("metadata_export_*.json"))[0]
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['pdfs']

print("\n" + "="*80)
print("PHASE 3: DUPLICATE DETECTION ANALYSIS")
print("="*80)

# Group by base filename
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
    
    basename = re.sub(r'\s+\d{1,2}\.\d{1,2}\.\d{2,4}$', '', basename)
    basename = re.sub(r'\s+\d{4}-\d{2}-\d{2}$', '', basename)
    basename = re.sub(r'\s+\d+$', '', basename)
    basename = basename.strip()
    
    contracts[basename].append(result)

duplicates = {k: v for k, v in contracts.items() if len(v) > 1}

print(f"\nTotal unique contract names (normalized): {len(contracts)}")
print(f"Contracts with multiple versions: {len(duplicates)}")
print(f"Total files: {sum(len(v) for v in contracts.values())}")
print(f"Duplicate files: {sum(len(v) for v in duplicates.values())}")

print(f"\n" + "="*80)
print("TOP 15 DUPLICATE GROUPS")
print("="*80)

sorted_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
for i, (basename, versions) in enumerate(sorted_dupes[:15], 1):
    print(f"\n{i}. {basename[:70]} ({len(versions)} versions)")
    for v in versions:
        filename = Path(v['document_metadata']['filename']).name
        status = v['execution_status']
        sig_count = v['total_signature_fields']
        print(f"   [{status:18s}] sigs:{sig_count} - {filename[:55]}")

# Export
duplicate_report = []
for basename, versions in sorted_dupes:
    duplicate_report.append({
        'normalized_name': basename,
        'version_count': len(versions),
        'versions': [{
            'filename': v['document_metadata']['filename'],
            'execution_status': v['execution_status'],
            'has_signatures': v['has_digital_signatures'],
            'confidence': v['execution_confidence']
        } for v in versions]
    })

with open('outputs/full_portfolio/duplicate_contracts.json', 'w', encoding='utf-8') as f:
    json.dump(duplicate_report, f, indent=2)

print(f"\n\nDuplicate analysis exported to: outputs/full_portfolio/duplicate_contracts.json")
