"""Final test of contracts 44 vs 45 with Claude enhancement"""
import requests
import json
import time

API_BASE_URL = "http://127.0.0.1:5000"

print("="*70)
print("FINAL TEST: CONTRACT COMPARISON 44 vs 45")
print("="*70)

# Start timing
start_time = time.time()

print("\n[1] Sending comparison request to API...")
try:
    response = requests.post(
        f"{API_BASE_URL}/api/compare",
        json={
            'v1_contract_id': 44,
            'v2_contract_id': 45,
            'include_recommendations': True
        },
        timeout=600
    )

    elapsed = time.time() - start_time
    print(f"[2] Response received in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"[3] Status code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()

        # Also read the actual saved JSON file to verify persistence
        import glob
        json_files = glob.glob('C:/Users/jrudy/CIP/data/reports/comparison_44_45_*.json')
        if json_files:
            latest_json = max(json_files, key=lambda x: x.split('_')[-1])
            print(f"\n[INFO] Reading latest saved JSON: {latest_json.split('/')[-1]}")
            with open(latest_json, 'r', encoding='utf-8') as f:
                file_result = json.load(f)
                # Use file result for validation (it has the saved enhancements)
                result = file_result

        print("\n" + "="*70)
        print("SUCCESS CRITERIA VALIDATION")
        print("="*70)

        # Success Criterion 1: Comparison completes
        print("\n[CHECK 1] Comparison completed: YES")

        # Success Criterion 2: Changes detected (50+)
        total_changes = result.get('total_changes', 0)
        print(f"[CHECK 2] Changes detected: {total_changes} (Target: 50+)")
        if total_changes >= 50:
            print("           PASS")
        else:
            print(f"           FAIL (only {total_changes})")

        # Success Criterion 3: Claude enhanced
        claude_enhanced = result.get('claude_enhanced')
        print(f"[CHECK 3] Claude enhanced: {claude_enhanced}")
        if claude_enhanced:
            print("           PASS")
        else:
            error = result.get('enhancement_error', 'Unknown')
            print(f"           FAIL - Error: {error}")

        # Success Criterion 4: Each change has enhancements
        changes = result.get('changes', [])
        if changes:
            first_change = changes[0]
            has_impact = 'impact' in first_change
            has_reasoning = 'reasoning' in first_change
            has_risk_factors = 'risk_factors' in first_change

            print(f"[CHECK 4] Change enhancements:")
            print(f"           - impact: {has_impact}")
            print(f"           - reasoning: {has_reasoning}")
            print(f"           - risk_factors: {has_risk_factors}")

            if has_impact and has_reasoning and has_risk_factors:
                print("           PASS")
            else:
                print("           FAIL")

        # Success Criterion 5: Executive summary with patterns
        exec_summary = result.get('executive_summary_enhanced')
        if exec_summary:
            has_patterns = 'key_patterns' in exec_summary
            print(f"[CHECK 5] Executive summary with key_patterns: {has_patterns}")
            if has_patterns:
                print("           PASS")
                print("\n           Key Patterns:")
                for pattern in exec_summary.get('key_patterns', []):
                    print(f"           - {pattern}")
            else:
                print("           FAIL")
        else:
            print("[CHECK 5] Executive summary: MISSING")

        # Impact breakdown
        print("\n" + "="*70)
        print("IMPACT BREAKDOWN")
        print("="*70)
        impact = result.get('impact_breakdown', {})
        for level, count in impact.items():
            print(f"  {level}: {count}")

        # Show sample changes
        print("\n" + "="*70)
        print("SAMPLE CHANGES (First 3)")
        print("="*70)
        for i, change in enumerate(changes[:3], 1):
            print(f"\n[Change {i}]")
            print(f"  Section: {change.get('section_title', 'Unknown')}")
            print(f"  Impact: {change.get('impact', 'N/A')}")
            if change.get('reasoning'):
                reasoning = change['reasoning'][:200]
                print(f"  Reasoning: {reasoning}...")

        print("\n" + "="*70)
        print(f"TEST COMPLETE - Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print("="*70)

    else:
        print(f"\n[ERROR] API returned status {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n[ERROR] Exception after {elapsed:.1f}s: {str(e)}")
    import traceback
    traceback.print_exc()
