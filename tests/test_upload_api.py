"""
Test Upload API Endpoint
Automated test for contract upload with metadata extraction
"""

import requests
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:5000"
TEST_FILE = "tools/comparison/test-output/test_v1.docx"
DB_PATH = "data/contracts.db"

def test_upload():
    """Test contract upload via API"""

    print("=" * 80)
    print("CIP UPLOAD API TEST")
    print("=" * 80)
    print()

    # Step 1: Verify test file exists
    print("Step 1: Verify test file exists")
    test_file_path = Path(TEST_FILE)
    if not test_file_path.exists():
        print(f"❌ Test file not found: {TEST_FILE}")
        return False

    file_size = test_file_path.stat().st_size
    print(f"[OK] Test file found: {TEST_FILE}")
    print(f"   Size: {file_size:,} bytes")
    print()

    # Step 2: Prepare upload request
    print("Step 2: Prepare upload request")

    with open(test_file_path, 'rb') as f:
        files = {
            'file': (test_file_path.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }

        # Optional metadata (backend will extract if not provided)
        data = {
            'contract_type': 'Service Agreement',
            'position': 'vendor',
            'leverage': 'moderate',
            'narrative': 'API test upload - automated testing'
        }

        print(f"   File: {test_file_path.name}")
        print(f"   Type: {data['contract_type']}")
        print(f"   Position: {data['position']}")
        print()

        # Step 3: Upload to API
        print("Step 3: Upload to API")
        print(f"   Endpoint: {API_BASE_URL}/api/upload")
        print("   Uploading... (this may take 30-60 seconds)")

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/upload",
                files=files,
                data=data,
                timeout=120
            )

            print(f"   Status Code: {response.status_code}")

            if response.status_code not in [200, 201]:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

            result = response.json()
            print(f"✅ Upload successful!")
            print()

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            return False

    # Step 4: Verify response data
    print("Step 4: Verify response data")
    print(f"   Contract ID: {result.get('contract_id')}")
    print(f"   Filename: {result.get('filename')}")
    print(f"   Upload Date: {result.get('upload_date')}")

    if 'detected_metadata' in result:
        print()
        print("   Metadata Extraction:")
        metadata = result['detected_metadata']
        print(f"      Type: {metadata.get('type')}")
        print(f"      Parties: {metadata.get('parties')}")
        print(f"      Perspective: {metadata.get('perspective')}")
        print(f"      Confidence: {metadata.get('confidence', 0):.0%}")

    if 'suggested_context' in result:
        print()
        print("   Business Context:")
        context = result['suggested_context']
        print(f"      Position: {context.get('position')}")
        print(f"      Leverage: {context.get('leverage')}")
        print(f"      Narrative: {context.get('narrative', '')[:60]}...")

    print()

    contract_id = result.get('contract_id')
    if not contract_id:
        print("❌ No contract_id in response")
        return False

    # Step 5: Verify database entry
    print("Step 5: Verify database entry")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, filename, contract_type, position, leverage, upload_date, file_path FROM contracts WHERE id = ?",
            (contract_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            print(f"❌ Contract ID {contract_id} not found in database")
            return False

        print(f"✅ Database entry verified")
        print(f"   ID: {row[0]}")
        print(f"   Filename: {row[1]}")
        print(f"   Type: {row[2]}")
        print(f"   Position: {row[3]}")
        print(f"   Leverage: {row[4]}")
        print(f"   Upload Date: {row[5]}")
        print(f"   File Path: {row[6]}")
        print()

        file_path = row[6]

    except Exception as e:
        print(f"❌ Database verification failed: {str(e)}")
        return False

    # Step 6: Verify file saved in uploads/
    print("Step 6: Verify file saved in uploads/")

    if file_path:
        uploaded_file = Path(file_path)
        if uploaded_file.exists():
            uploaded_size = uploaded_file.stat().st_size
            print(f"✅ File saved in uploads/")
            print(f"   Path: {file_path}")
            print(f"   Size: {uploaded_size:,} bytes")
        else:
            print(f"❌ File not found: {file_path}")
            return False
    else:
        print(f"❌ No file path in database")
        return False

    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Open browser to: http://localhost:8501")
    print("2. Navigate to '📤 Upload' page")
    print(f"3. You should see contract ID {contract_id} in the system")
    print("4. Try uploading another contract through the UI")
    print()

    return True

if __name__ == "__main__":
    success = test_upload()
    exit(0 if success else 1)
