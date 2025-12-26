"""
Test script for the /api/compare endpoint
"""

import sys
sys.path.insert(0, 'backend')

import api

print("\n" + "="*60)
print("CIP API ENDPOINTS VERIFICATION")
print("="*60)

endpoints = []
for rule in api.app.url_map.iter_rules():
    if rule.endpoint != 'static':
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        endpoints.append((rule.rule, methods, rule.endpoint))

# Sort by path
endpoints.sort()

print("\nRegistered Endpoints:")
print("-" * 60)
for path, methods, endpoint in endpoints:
    print(f"{methods:15} {path:30} ({endpoint})")

print("\n" + "="*60)
print(f"Total API Endpoints: {len(endpoints)}")
print("="*60)

# Verify compare endpoint exists
compare_found = any('/api/compare' in path for path, _, _ in endpoints)
if compare_found:
    print("\n✓ /api/compare endpoint successfully registered")
else:
    print("\n✗ /api/compare endpoint NOT found")

print("\nEndpoint Summary:")
print("-" * 60)
api_endpoints = [e for e in endpoints if e[0].startswith('/api/')]
for path, methods, endpoint in api_endpoints:
    print(f"  {path}")

print(f"\nTotal /api/ endpoints: {len(api_endpoints)}")
