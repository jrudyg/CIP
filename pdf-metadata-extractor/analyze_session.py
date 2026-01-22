import json
from collections import Counter

# Load session state
with open('session_state.json', 'r', encoding='utf-8') as f:
    session = json.load(f)

files = session['files_processed']
print(f"\n=== PHASE 1 PILOT RESULTS ===")
print(f"Total files processed: {len(files)}")
print(f"Last run: {session['last_run']}")

# Extract execution statuses
statuses = []
confidences = []
has_sigs = []
times = []

for filename, data in files.items():
    result = data['extraction_result']
    statuses.append(result['execution_status'])
    confidences.append(result['execution_confidence'])
    has_sigs.append(result['has_digital_signatures'])
    times.append(data['processing_time_seconds'])

# Execution status distribution
print(f"\n=== EXECUTION STATUS DISTRIBUTION ===")
status_counts = Counter(statuses)
for status, count in status_counts.most_common():
    pct = (count / len(files)) * 100
    print(f"{status:25s}: {count:2d} ({pct:5.1f}%)")

# Signature detection
sig_count = sum(has_sigs)
print(f"\n=== SIGNATURE DETECTION ===")
print(f"Files with digital signatures: {sig_count}/{len(files)} ({sig_count/len(files)*100:.1f}%)")

# Confidence scores
avg_conf = sum(confidences) / len(confidences)
high_conf = sum(1 for c in confidences if c >= 70)
print(f"\n=== CONFIDENCE METRICS ===")
print(f"Average confidence: {avg_conf:.1f}%")
print(f"High confidence (>=70%): {high_conf}/{len(files)} ({high_conf/len(files)*100:.1f}%)")

# Performance
total_time = sum(times)
avg_time = total_time / len(times)
print(f"\n=== PERFORMANCE ===")
print(f"Total processing time: {total_time:.2f} seconds")
print(f"Average time per file: {avg_time:.2f} seconds")
print(f"Max time per file: {max(times):.2f} seconds")

# Files with "signed" keyword
print(f"\n=== SIGNED KEYWORD FILES ===")
signed_keyword_files = [f for f in files.keys() if 'signed' in f.lower()]
print(f"Files with 'signed' in name: {len(signed_keyword_files)}")
for f in signed_keyword_files:
    result = files[f]['extraction_result']
    has_sig = "✓" if result['has_digital_signatures'] else "✗"
    print(f"  {has_sig} {f[:60]}")

# Unsigned keyword files
print(f"\n=== UNSIGNED KEYWORD FILES ===")
unsigned_keyword_files = [f for f in files.keys() if 'unsigned' in f.lower()]
print(f"Files with 'unsigned' in name: {len(unsigned_keyword_files)}")
for f in unsigned_keyword_files:
    result = files[f]['extraction_result']
    status = result['execution_status']
    print(f"  [{status}] {f[:60]}")

