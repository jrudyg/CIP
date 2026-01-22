import json
from collections import Counter
from pathlib import Path

# Load full portfolio results
json_path = list(Path("outputs/full_portfolio/exports").glob("metadata_export_*.json"))[0]
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['pdfs']
metadata = data['metadata']

print(f"\n{'='*80}")
print("PHASE 2: FULL PORTFOLIO EXTRACTION RESULTS")
print(f"{'='*80}")
print(f"Total contracts processed: {len(results)}")
print(f"Extraction date: {metadata['generated']}")

# 1. Execution Status Breakdown
print(f"\n{'='*80}")
print("1. EXECUTION STATUS DISTRIBUTION")
print(f"{'='*80}")
statuses = Counter(r['execution_status'] for r in results)
for status, count in statuses.most_common():
    pct = (count / len(results)) * 100
    print(f"{status:25s}: {count:3d} ({pct:5.1f}%)")

# 2. Confidence Metrics
print(f"\n{'='*80}")
print("2. CONFIDENCE METRICS")
print(f"{'='*80}")
confidences = [r['execution_confidence'] for r in results]
avg_conf = sum(confidences) / len(confidences)
high_conf = sum(1 for c in confidences if c >= 70)
low_conf = sum(1 for c in confidences if c < 60)
print(f"Average confidence: {avg_conf:.1f}%")
print(f"High confidence (>=70%): {high_conf}/{len(results)} ({high_conf/len(results)*100:.1f}%)")
print(f"Low confidence (<60%): {low_conf}/{len(results)} ({low_conf/len(results)*100:.1f}%)")

# 3. Signature Detection
print(f"\n{'='*80}")
print("3. SIGNATURE DETECTION")
print(f"{'='*80}")
has_sigs = sum(1 for r in results if r['has_digital_signatures'])
total_sig_fields = sum(r['total_signature_fields'] for r in results)
signed_sig_fields = sum(r['signed_signature_fields'] for r in results)
print(f"Files with digital signatures: {has_sigs}/{len(results)} ({has_sigs/len(results)*100:.1f}%)")
print(f"Total signature fields: {total_sig_fields}")
print(f"Signed signature fields: {signed_sig_fields}")
if total_sig_fields > 0:
    print(f"Signature completion rate: {signed_sig_fields/total_sig_fields*100:.1f}%")

# 4. Priority Contracts (Unsigned/Unknown)
print(f"\n{'='*80}")
print("4. PRIORITY CONTRACTS (Need Attention)")
print(f"{'='*80}")
unsigned = [r for r in results if r['execution_status'] in ['unsigned', 'unknown']]
low_confidence = [r for r in results if r['execution_confidence'] < 60]
print(f"Unsigned/Unknown status: {len(unsigned)} contracts")
print(f"Low confidence (<60%): {len(low_confidence)} contracts")

print(f"\nTop 10 Unsigned/Unknown contracts:")
for i, r in enumerate(unsigned[:10], 1):
    filename = r['document_metadata']['filename']
    status = r['execution_status']
    conf = r['execution_confidence']
    print(f"{i:2d}. [{status:8s}] {conf:2d}% - {filename[:65]}")

# 5. Metadata Summary
print(f"\n{'='*80}")
print("5. SUMMARY FROM METADATA")
print(f"{'='*80}")
print(f"Total PDFs: {metadata['total_pdfs']}")
print(f"Total signatures: {metadata['total_signatures']}")
print(f"Executed contracts: {metadata['executed_contracts']}")
print(f"Average confidence: {metadata['average_confidence']:.1f}%")

# Export priority list
priority_list = {
    'unsigned_unknown': [r['document_metadata']['filename'] for r in unsigned],
    'low_confidence': [r['document_metadata']['filename'] for r in low_confidence]
}

Path('outputs/full_portfolio').mkdir(parents=True, exist_ok=True)
with open('outputs/full_portfolio/priority_contracts.json', 'w', encoding='utf-8') as f:
    json.dump(priority_list, f, indent=2)

print(f"\nPriority contracts exported to: outputs/full_portfolio/priority_contracts.json")
