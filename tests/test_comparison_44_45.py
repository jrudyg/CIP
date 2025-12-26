"""Test comparison of contracts 44 vs 45 with Claude enhancement"""
import requests
import json
import time

API_BASE_URL = "http://127.0.0.1:5000"

print("=" * 70)
print("TESTING CONTRACT COMPARISON: 44 vs 45")
print("=" * 70)

# Start timing
start_time = time.time()

print("\n[1] Sending comparison request...")
response = requests.post(
    f"{API_BASE_URL}/api/compare",
    json={
        'v1_contract_id': 44,
        'v2_contract_id': 45,
        'include_recommendations': True
    },
    timeout=600  # 10 minute timeout
)

elapsed = time.time() - start_time
print(f"[2] Response received in {elapsed:.1f} seconds")
print(f"[3] Status code: {response.status_code}")

if response.status_code == 200:
    result = response.json()

    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)

    print(f"\n✓ Total Changes: {result.get('total_changes', 0)}")
    print(f"✓ Claude Enhanced: {result.get('claude_enhanced', False)}")

    if result.get('claude_enhanced'):
        print("\n[SUCCESS] Claude enhancement worked!")

        # Show impact breakdown
        impact = result.get('impact_breakdown', {})
        print("\nImpact Breakdown:")
        for level, count in impact.items():
            print(f"  - {level}: {count}")

        # Show executive summary if present
        if result.get('executive_summary_enhanced'):
            summary = result['executive_summary_enhanced']
            print("\nExecutive Summary:")
            print(f"  - Critical: {summary.get('critical_count', 0)}")
            print(f"  - High Priority: {summary.get('high_priority_count', 0)}")
            print(f"  - Important: {summary.get('important_count', 0)}")

            if summary.get('key_patterns'):
                print("\nKey Patterns Detected:")
                for pattern in summary['key_patterns']:
                    print(f"  • {pattern}")
    else:
        error = result.get('enhancement_error', 'Unknown')
        print(f"\n[WARNING] Claude enhancement failed: {error}")
        print("Falling back to Python-only comparison")

    print("\n" + "=" * 70)
    print("DETAILED RESULTS")
    print("=" * 70)

    # Show first few changes
    changes = result.get('changes', [])
    print(f"\nShowing first 3 of {len(changes)} changes:\n")

    for i, change in enumerate(changes[:3], 1):
        print(f"\n[Change {i}]")
        print(f"  Section: {change.get('section_title', 'Unknown')}")
        print(f"  Impact: {change.get('impact', 'N/A')}")
        if change.get('reasoning'):
            print(f"  Reasoning: {change['reasoning'][:150]}...")

    print("\n" + "=" * 70)
    print(f"TEST COMPLETE - Time: {elapsed:.1f}s")
    print("=" * 70)

else:
    print(f"\n[ERROR] API returned status {response.status_code}")
    print(f"Response: {response.text}")
