#!/usr/bin/env python3
"""
Test script for Phase 7A: Report Generation Integration
Tests Task 1 (Report Generation UI) and Task 2 (Redline Export)
"""

import requests
import sqlite3
import os
import json
from datetime import datetime

API_BASE = "http://localhost:5000/api"
OUTPUT_DIR = r"C:\Users\jrudy\CIP\outputs"

def get_test_contract():
    """Get a test contract from the database"""
    conn = sqlite3.connect(r'C:\Users\jrudy\CIP\data\contracts.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM contracts LIMIT 1")
    contract = cursor.fetchone()
    conn.close()

    if not contract:
        print("[X] No contracts found in database")
        return None

    return dict(contract)

def test_task_1_risk_review():
    """Test Task 1: Risk Review Report Generation"""
    print("\n" + "="*60)
    print("TASK 1: Testing Risk Review Report Generation")
    print("="*60)

    contract = get_test_contract()
    if not contract:
        return False

    print(f"[OK] Using contract: {contract['title']} (ID: {contract['id']})")

    # Prepare request
    payload = {
        "contract_id": contract['id'],
        "report_type": "risk_review",
        "parameters": {
            "our_entity": contract.get('our_entity', 'Our Company'),
            "counterparty": contract.get('counterparty', 'Counterparty'),
            "position": contract.get('position', 'Party A'),
            "include_sections": ["executive_summary", "heat_map", "clause_analysis"]
        }
    }

    print(f"[OK] Request payload prepared")
    print(f"  - Report Type: {payload['report_type']}")
    print(f"  - Contract ID: {payload['contract_id']}")

    # Call API
    try:
        print(f"\n--> Calling POST {API_BASE}/reports/generate...")
        response = requests.post(
            f"{API_BASE}/reports/generate",
            json=payload,
            timeout=60
        )

        print(f"  Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"[X] API call failed: {response.text}")
            return False

        data = response.json()
        print(f"[OK] Report generated successfully")
        print(f"  - Report ID: {data.get('report_id')}")
        print(f"  - Filename: {data.get('filename')}")

        # Test download
        report_id = data.get('report_id')
        if report_id:
            print(f"\n--> Testing download for report {report_id}...")
            download_response = requests.get(
                f"{API_BASE}/reports/{report_id}/download",
                timeout=30
            )

            if download_response.status_code == 200:
                print(f"[OK] Download successful ({len(download_response.content)} bytes)")

                # Save to verify
                test_file = f"{OUTPUT_DIR}/test_risk_review_{report_id}.docx"
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                with open(test_file, 'wb') as f:
                    f.write(download_response.content)
                print(f"[OK] File saved: {test_file}")

                return True
            else:
                print(f"[X] Download failed: {download_response.status_code}")
                return False

    except requests.exceptions.Timeout:
        print("[X] Request timed out")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_task_1_redline():
    """Test Task 1: Redline Report Generation"""
    print("\n" + "="*60)
    print("TASK 1: Testing Redline Report Generation")
    print("="*60)

    contract = get_test_contract()
    if not contract:
        return False

    print(f"[OK] Using contract: {contract['title']} (ID: {contract['id']})")

    # Prepare request
    payload = {
        "contract_id": contract['id'],
        "report_type": "redline",
        "parameters": {
            "our_entity": contract.get('our_entity', 'Our Company'),
            "counterparty": contract.get('counterparty', 'Counterparty'),
            "position": contract.get('position', 'Party A')
        }
    }

    print(f"[OK] Request payload prepared")

    # Call API
    try:
        print(f"\n--> Calling POST {API_BASE}/reports/generate...")
        response = requests.post(
            f"{API_BASE}/reports/generate",
            json=payload,
            timeout=60
        )

        print(f"  Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"[X] API call failed: {response.text}")
            return False

        data = response.json()
        print(f"[OK] Report generated successfully")
        print(f"  - Report ID: {data.get('report_id')}")
        print(f"  - Filename: {data.get('filename')}")

        return True

    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_task_1_comparison():
    """Test Task 1: Comparison Report Generation"""
    print("\n" + "="*60)
    print("TASK 1: Testing Comparison Report Generation")
    print("="*60)

    contract = get_test_contract()
    if not contract:
        return False

    print(f"[OK] Using contract: {contract['title']} (ID: {contract['id']})")

    # Prepare request
    payload = {
        "contract_id": contract['id'],
        "report_type": "comparison",
        "parameters": {
            "our_entity": contract.get('our_entity', 'Our Company'),
            "counterparty": contract.get('counterparty', 'Counterparty'),
            "position": contract.get('position', 'Party A'),
            "v1_label": "Version 1",
            "v2_label": "Version 2"
        }
    }

    print(f"[OK] Request payload prepared")

    # Call API
    try:
        print(f"\n--> Calling POST {API_BASE}/reports/generate...")
        response = requests.post(
            f"{API_BASE}/reports/generate",
            json=payload,
            timeout=60
        )

        print(f"  Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"[X] API call failed: {response.text}")
            return False

        data = response.json()
        print(f"[OK] Report generated successfully")
        print(f"  - Report ID: {data.get('report_id')}")
        print(f"  - Filename: {data.get('filename')}")

        return True

    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_task_2_redline_export():
    """Test Task 2: Redline Review Export Integration"""
    print("\n" + "="*60)
    print("TASK 2: Testing Redline Review Export")
    print("="*60)

    contract = get_test_contract()
    if not contract:
        return False

    print(f"[OK] Using contract: {contract['title']} (ID: {contract['id']})")

    # Simulate approved clauses from Redline Review page
    approved_clauses = [
        {
            "clause_type": "Indemnification",
            "section_number": "8.1",
            "current_text": "Provider shall indemnify Client...",
            "revised_text": "Provider shall indemnify Client for direct damages only...",
            "rationale": "Limits scope to direct damages",
            "priority": "dealbreaker"
        }
    ]

    payload = {
        "contract_id": contract['id'],
        "report_type": "redline",
        "parameters": {
            "our_entity": contract.get('our_entity', 'Our Company'),
            "counterparty": contract.get('counterparty', 'Counterparty'),
            "position": contract.get('position', 'Party A'),
            "leverage": "balanced",
            "approved_clauses": approved_clauses,
            "decisions": {"8.1": "approved"},
            "modifications": {}
        }
    }

    print(f"[OK] Request payload prepared with {len(approved_clauses)} approved clause(s)")

    # Call API
    try:
        print(f"\n--> Calling POST {API_BASE}/reports/generate...")
        response = requests.post(
            f"{API_BASE}/reports/generate",
            json=payload,
            timeout=60
        )

        print(f"  Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"[X] API call failed: {response.text}")
            return False

        data = response.json()
        print(f"[OK] Redline report generated successfully")
        print(f"  - Report ID: {data.get('report_id')}")
        print(f"  - Filename: {data.get('filename')}")

        # Test download
        report_id = data.get('report_id')
        if report_id:
            print(f"\n--> Testing download for report {report_id}...")
            download_response = requests.get(
                f"{API_BASE}/reports/{report_id}/download",
                timeout=30
            )

            if download_response.status_code == 200:
                print(f"[OK] Download successful ({len(download_response.content)} bytes)")

                # Save to verify
                test_file = f"{OUTPUT_DIR}/test_redline_export_{report_id}.docx"
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                with open(test_file, 'wb') as f:
                    f.write(download_response.content)
                print(f"[OK] File saved: {test_file}")

                return True
            else:
                print(f"[X] Download failed: {download_response.status_code}")
                return False

    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 7A INTEGRATION TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = {
        "Task 1 - Risk Review": test_task_1_risk_review(),
        "Task 1 - Redline": test_task_1_redline(),
        "Task 1 - Comparison": test_task_1_comparison(),
        "Task 2 - Redline Export": test_task_2_redline_export()
    }

    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[X] FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return 0
    else:
        print("\n[WARNING]  SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit(main())
