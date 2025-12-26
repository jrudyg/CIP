import json

with open('C:/Users/jrudy/CIP/data/reports/comparison_44_45_20251123_200436.json') as f:
    data = json.load(f)

print("=== TOP LEVEL FIELDS ===")
print("claude_enhanced:", data.get('claude_enhanced'))
print("total_changes:", data.get('total_changes'))
print("Has executive_summary_enhanced:", 'executive_summary_enhanced' in data)

print("\n=== EXECUTIVE SUMMARY ===")
exec_sum = data.get('executive_summary_enhanced', {})
print("Keys:", list(exec_sum.keys()) if exec_sum else 'NONE')

print("\n=== FIRST CHANGE ===")
if data.get('changes'):
    change = data['changes'][0]
    print("All keys:", list(change.keys()))
    print("Has v1_content:", 'v1_content' in change)
    print("Has v2_content:", 'v2_content' in change)
    print("Has reasoning:", 'reasoning' in change)
    print("Has risk_factors:", 'risk_factors' in change)
    print("Impact:", change.get('impact'))
