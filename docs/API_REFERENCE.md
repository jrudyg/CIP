# CIP Backend API Reference

## Base URL
```
http://127.0.0.1:5000
```

## Authentication
Currently no authentication required (development mode).

---

## Endpoints

### Health Check

#### `GET /health`
Check API health and service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "CIP API",
  "timestamp": "2025-11-22T18:30:00",
  "orchestrator": true,
  "api_key_configured": true,
  "database": {
    "contracts": true,
    "reports": true
  }
}
```

---

### Contract Upload

#### `POST /api/upload`
Upload and analyze a contract file with automatic metadata extraction.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (PDF, DOCX, or TXT)

**Response (201 Created):**
```json
{
  "contract_id": 123,
  "detected_metadata": {
    "type": "MSA",
    "parties": ["Company A", "Company B"],
    "perspective": "Customer",
    "dates": {
      "effective_date": "2024-01-01",
      "expiration_date": "2025-01-01"
    },
    "amounts": {
      "total_value": "$500,000",
      "payment_terms": "Net 30"
    },
    "jurisdiction": "Delaware",
    "confidence": 0.92
  },
  "suggested_context": {
    "position": "customer",
    "leverage": "Strong",
    "narrative": "Standard MSA with favorable terms...",
    "confidence": 0.88
  },
  "version_info": {
    "is_new_version": false,
    "parent_contract_id": null,
    "suggested_version_number": 1,
    "is_duplicate": false
  }
}
```

**Errors:**
- `400` - No file provided or invalid file type
- `503` - Upload service not available

---

### Confirm Metadata

#### `POST /api/upload/confirm-metadata`
Confirm user-edited metadata for uploaded contract.

**Request:**
```json
{
  "contract_id": 123,
  "metadata": {
    "type": "MSA",
    "parties": ["Company A", "Company B"],
    "perspective": "Customer",
    "dates": {
      "effective_date": "2024-01-01",
      "expiration_date": "2025-01-01"
    },
    "amounts": {
      "total_value": "$500,000",
      "payment_terms": "Net 30"
    },
    "jurisdiction": "Delaware"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "contract_id": 123
}
```

---

### Confirm Context

#### `POST /api/upload/confirm-context`
Confirm business context and finalize contract upload.

**Request:**
```json
{
  "contract_id": 123,
  "context": {
    "position": "customer",
    "leverage": "Strong",
    "narrative": "Standard MSA with favorable terms..."
  },
  "link_as_version": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "contract_id": 123,
  "ready_for_analysis": true
}
```

---

### List Contracts

#### `GET /api/contracts`
Retrieve list of uploaded contracts.

**Query Parameters:**
- `limit` (optional): Max number of contracts (default: 100)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (active, analyzed, archived)

**Response (200 OK):**
```json
{
  "contracts": [
    {
      "id": 123,
      "filename": "MSA_Acme_Corp.pdf",
      "upload_date": "2024-11-22T10:30:00",
      "contract_type": "MSA",
      "status": "analyzed",
      "parties": ["Company A", "Company B"]
    }
  ],
  "total": 20,
  "limit": 100,
  "offset": 0
}
```

---

### Get Contract Details

#### `GET /api/contracts/<contract_id>`
Get detailed information about a specific contract.

**Response (200 OK):**
```json
{
  "id": 123,
  "filename": "MSA_Acme_Corp.pdf",
  "file_path": "/uploads/20241122_103000_MSA_Acme_Corp.pdf",
  "upload_date": "2024-11-22T10:30:00",
  "contract_type": "MSA",
  "parties": ["Company A", "Company B"],
  "effective_date": "2024-01-01",
  "status": "analyzed",
  "position": "customer",
  "leverage": "Strong",
  "narrative": "Standard MSA...",
  "metadata_json": {...}
}
```

**Errors:**
- `404` - Contract not found

---

### Analyze Contract

#### `POST /api/analyze`
Perform AI-powered risk analysis on a contract.

**Request:**
```json
{
  "contract_id": 123
}
```

**Response (200 OK):**
```json
{
  "analysis": {
    "overall_risk": "MEDIUM",
    "confidence_score": 0.89,
    "dealbreakers": [],
    "critical_items": [
      {
        "section_number": "8.2",
        "section_title": "Liability Cap",
        "category": "liability",
        "finding": "Liability cap may be insufficient...",
        "recommendation": "Negotiate higher cap...",
        "confidence": 0.92,
        "risk_level": "CRITICAL"
      }
    ],
    "important_items": [...],
    "standard_items": [...],
    "context": {
      "position": "customer",
      "leverage": "Strong",
      "contract_type": "MSA",
      "narrative": "..."
    }
  }
}
```

**Processing Time:** 30-60 seconds (AI analysis)

**Errors:**
- `404` - Contract not found
- `400` - Invalid contract_id
- `503` - Analysis service not available

---

### Get Assessment

#### `GET /api/assessment/<contract_id>`
Retrieve existing risk assessment for a contract.

**Response (200 OK):**
```json
{
  "assessment": {
    "overall_risk": "MEDIUM",
    "confidence_score": 0.89,
    "analysis_date": "2024-11-22T10:35:00",
    "dealbreakers": [],
    "critical_items": [...],
    "important_items": [...],
    "standard_items": [...]
  }
}
```

**Errors:**
- `404` - No assessment found for this contract

---

### Delete Contract

#### `DELETE /api/contracts/<contract_id>`
Delete a contract and all associated data.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Contract deleted successfully"
}
```

**Errors:**
- `404` - Contract not found

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "status_code": 400
}
```

### Common Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limiting

Currently no rate limiting (development mode).

---

## Logging

All API requests are logged to:
- `logs/api.log` - All API activity
- `logs/cip.log` - General application logs
- `logs/error.log` - Errors only

Log files rotate at 10MB with 5-10 backups retained.
