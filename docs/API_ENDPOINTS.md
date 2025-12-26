# CIP API Endpoints Reference

**Base URL:** `http://127.0.0.1:5000`

---

## Health Check

### GET /health
Check API and orchestrator status

**Response:**
```json
{
  "status": "healthy",
  "service": "CIP API",
  "timestamp": "2025-11-22T14:30:00",
  "orchestrator": true,
  "api_key_configured": true,
  "database": {
    "contracts": true,
    "reports": true
  }
}
```

---

## Contract Management

### POST /api/upload
Upload a new contract for analysis

**Request (multipart/form-data):**
- `file`: Contract file (PDF, DOCX, TXT)
- `contract_type`: Type of contract (optional)
- `parties`: Parties involved (optional)
- `position`: Our position (vendor, customer, landlord, tenant, etc.)
- `leverage`: Leverage level (strong, moderate, balanced, weak)
- `narrative`: Specific concerns and priorities

**Response:**
```json
{
  "contract_id": 1,
  "filename": "service_agreement.docx",
  "file_path": "/data/uploads/20251122_143000_service_agreement.docx",
  "upload_date": "2025-11-22T14:30:00"
}
```

**Status Codes:**
- `201`: Contract uploaded successfully
- `400`: Invalid file type or missing required fields
- `500`: Server error

---

### GET /api/contracts
List all uploaded contracts

**Query Parameters:**
- `limit`: Maximum number of contracts to return (default: 100)
- `offset`: Number of contracts to skip (default: 0)

**Response:**
```json
{
  "contracts": [
    {
      "id": 1,
      "filename": "service_agreement.docx",
      "contract_type": "Service Agreement",
      "position": "vendor",
      "leverage": "moderate",
      "upload_date": "2025-11-22T14:30:00",
      "status": "analyzed"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

---

### GET /api/contract/{contract_id}
Get details of a specific contract

**URL Parameters:**
- `contract_id`: Contract ID (integer)

**Response:**
```json
{
  "id": 1,
  "filename": "service_agreement.docx",
  "file_path": "/data/uploads/20251122_143000_service_agreement.docx",
  "contract_type": "Service Agreement",
  "parties": "Company A, Company B",
  "position": "vendor",
  "leverage": "moderate",
  "narrative": "Focus on liability and IP provisions",
  "upload_date": "2025-11-22T14:30:00",
  "status": "analyzed"
}
```

**Status Codes:**
- `200`: Success
- `404`: Contract not found

---

## Analysis

### POST /api/analyze
Trigger AI-powered contract analysis

**Request (JSON):**

**Option 1: Analyze uploaded contract**
```json
{
  "contract_id": 1
}
```

**Option 2: Analyze file directly**
```json
{
  "file_path": "/path/to/contract.pdf",
  "position": "vendor",
  "leverage": "moderate",
  "narrative": "Specific concerns...",
  "contract_type": "Service Agreement",
  "parties": "Company A, Company B"
}
```

**Response:**
```json
{
  "status": "completed",
  "analysis": {
    "contract_id": 1,
    "overall_risk": "MEDIUM",
    "confidence_score": 0.92,
    "analysis_date": "2025-11-22T14:35:00",
    "dealbreakers": [
      {
        "section_number": "5.2",
        "section_title": "Unlimited Liability",
        "risk_level": "DEALBREAKER",
        "category": "liability",
        "finding": "Unlimited liability exposure without cap",
        "recommendation": "Negotiate liability cap at 12 months fees",
        "confidence": 1.0,
        "pattern_id": "unlimited-liability-001"
      }
    ],
    "critical_items": [...],
    "important_items": [...],
    "standard_items": [...],
    "context": {
      "position": "vendor",
      "leverage": "moderate",
      "narrative": "Focus on liability and IP provisions",
      "contract_type": "Service Agreement",
      "parties": "Company A, Company B"
    }
  }
}
```

**Status Codes:**
- `200`: Analysis completed
- `400`: Missing required parameters
- `404`: Contract not found
- `500`: Analysis failed

---

### GET /api/assessment/{contract_id}
Retrieve existing risk assessment

**URL Parameters:**
- `contract_id`: Contract ID (integer)

**Response:**
```json
{
  "contract_id": 1,
  "assessment": {
    "overall_risk": "MEDIUM",
    "confidence_score": 0.92,
    "dealbreakers": [...],
    "critical_items": [...],
    "important_items": [...],
    "standard_items": [...]
  },
  "contract": {
    "filename": "service_agreement.docx",
    "contract_type": "Service Agreement"
  }
}
```

**Status Codes:**
- `200`: Success
- `404`: No assessment found for contract

---

## Comparison (NEW)

### POST /api/compare
Compare two contract versions

**Request (JSON):**
```json
{
  "v1_contract_id": 1,
  "v2_contract_id": 2,
  "include_recommendations": true
}
```

**Parameters:**
- `v1_contract_id`: ID of first contract version (required)
- `v2_contract_id`: ID of second contract version (required)
- `include_recommendations`: Include recommendations in report (optional, default: true)

**Response:**
```json
{
  "status": "completed",
  "comparison_id": 1,
  "report_path": "/data/reports/comparison_report_1_2_20251122_143500.docx",
  "json_path": "/data/reports/comparison_1_2_20251122_143500.json",
  "executive_summary": "Comparison identified 12 substantive changes including 2 CRITICAL items requiring immediate attention",
  "total_changes": 12,
  "impact_breakdown": {
    "CRITICAL": 2,
    "HIGH_PRIORITY": 4,
    "IMPORTANT": 3,
    "OPERATIONAL": 2,
    "ADMINISTRATIVE": 1
  },
  "v1_contract": {
    "id": 1,
    "filename": "service_agreement_v1.docx"
  },
  "v2_contract": {
    "id": 2,
    "filename": "service_agreement_v2.docx"
  }
}
```

**Features:**
- Extracts sections from both contract versions
- Matches corresponding sections using content similarity
- Detects substantive changes (ignores formatting/minor differences)
- Classifies changes by impact level (CRITICAL, HIGH_PRIORITY, IMPORTANT, OPERATIONAL, ADMINISTRATIVE)
- Generates professional .docx report with:
  - Executive summary
  - Detailed 5-column comparison table
  - Redlines (deletions in red, additions in green)
  - Business impact narratives
  - Recommendations (if enabled)
- Stores comparison metadata in reports database

**Status Codes:**
- `200`: Comparison completed successfully
- `400`: Invalid parameters or same contract IDs
- `404`: One or both contracts not found
- `500`: Comparison failed

**Important Notes:**
- Both contracts must be in .docx format
- Comparison uses tools from `tools/comparison/scripts/`
- Report includes 5-column table: # | Section/Recommendation | V1 Clause | V2 Clause | Business Impact
- JSON results stored for programmatic access
- DOCX report generated for stakeholder review

---

## Statistics

### GET /api/statistics
Get platform statistics

**Response:**
```json
{
  "contracts": {
    "total": 25,
    "active": 20,
    "archived": 5
  },
  "assessments": {
    "total": 22,
    "high_risk": 3,
    "medium_risk": 12,
    "low_risk": 7
  },
  "comparisons": {
    "total": 5
  },
  "recent_activity": [...]
}
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "status_code": 400
}
```

**Common Status Codes:**
- `400`: Bad Request - Invalid parameters
- `404`: Not Found - Resource doesn't exist
- `500`: Internal Server Error - Server-side error
- `503`: Service Unavailable - Orchestrator not initialized

---

## Integration Examples

### Python (requests)
```python
import requests

# Upload contract
with open('contract.docx', 'rb') as f:
    files = {'file': f}
    data = {
        'position': 'vendor',
        'leverage': 'moderate',
        'narrative': 'Focus on liability'
    }
    response = requests.post('http://127.0.0.1:5000/api/upload', files=files, data=data)
    contract_id = response.json()['contract_id']

# Analyze
response = requests.post('http://127.0.0.1:5000/api/analyze', json={'contract_id': contract_id})
analysis = response.json()['analysis']

# Compare two versions
response = requests.post('http://127.0.0.1:5000/api/compare', json={
    'v1_contract_id': 1,
    'v2_contract_id': 2,
    'include_recommendations': True
})
comparison = response.json()
```

### JavaScript (fetch)
```javascript
// Upload contract
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('position', 'vendor');
formData.append('leverage', 'moderate');

const uploadResponse = await fetch('http://127.0.0.1:5000/api/upload', {
  method: 'POST',
  body: formData
});
const { contract_id } = await uploadResponse.json();

// Analyze
const analyzeResponse = await fetch('http://127.0.0.1:5000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ contract_id })
});
const { analysis } = await analyzeResponse.json();

// Compare
const compareResponse = await fetch('http://127.0.0.1:5000/api/compare', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    v1_contract_id: 1,
    v2_contract_id: 2,
    include_recommendations: true
  })
});
const comparison = await compareResponse.json();
```

---

## CORS Configuration

CORS is enabled for:
- **Origins:** `http://localhost:8501`, `http://127.0.0.1:8501` (Streamlit)
- **Methods:** GET, POST, PUT, DELETE, OPTIONS
- **Headers:** Content-Type, Authorization

---

## Rate Limiting

Currently no rate limiting implemented. Consider adding for production deployment.

---

## Authentication

Currently no authentication required. Add authentication middleware for production use.

---

**Last Updated:** 2025-11-22
**API Version:** 1.1
**Total Endpoints:** 8 (1 NEW: /api/compare)
