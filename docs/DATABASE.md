# CIP Database Schema

## Overview

CIP uses SQLite databases for contract storage and analysis.

**Database Files:**
- `data/contracts.db` - Main contract database
- `data/reports.db` - Generated reports

---

## contracts.db Schema

### Table: `contracts`

Primary table storing uploaded contracts.

```sql
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    contract_type TEXT,
    parties TEXT,                  -- JSON array
    effective_date DATE,
    term_months INTEGER,
    status TEXT DEFAULT 'active',
    version_number INTEGER DEFAULT 1,
    position TEXT,
    leverage TEXT,
    narrative TEXT,
    metadata_json TEXT,            -- JSON object
    parent_contract_id INTEGER,
    is_latest_version INTEGER DEFAULT 1,
    version_notes TEXT,
    auto_detected_metadata TEXT,   -- JSON object
    metadata_confirmed INTEGER DEFAULT 0,
    content_hash TEXT,
    ai_suggested_context TEXT      -- JSON object
);
```

**Key Fields:**
- `id`: Unique contract identifier
- `filename`: Original uploaded filename
- `file_path`: Server file path
- `contract_type`: MSA, NDA, SOW, etc.
- `parties`: JSON array of party names
- `status`: active, analyzed, archived
- `position`: customer, vendor, buyer, seller
- `leverage`: Strong, Moderate, Weak
- `content_hash`: MD5 hash for duplicate detection

---

### Table: `metadata`

Extracted and confirmed contract metadata.

```sql
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    type TEXT,
    parties TEXT,                  -- JSON array
    perspective TEXT,
    effective_date TEXT,
    expiration_date TEXT,
    total_value TEXT,
    payment_terms TEXT,
    jurisdiction TEXT,
    confidence REAL,
    FOREIGN KEY (contract_id) REFERENCES contracts (id)
);
```

---

### Table: `context`

Business context for contracts.

```sql
CREATE TABLE context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    position TEXT,
    leverage TEXT,
    narrative TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts (id)
);
```

---

### Table: `assessments`

Risk assessment results from AI analysis.

```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    analysis_date TEXT NOT NULL,
    overall_risk TEXT,             -- HIGH, MEDIUM, LOW
    confidence_score REAL,
    analysis_json TEXT,            -- Full analysis in JSON
    FOREIGN KEY (contract_id) REFERENCES contracts (id)
);
```

**analysis_json Structure:**
```json
{
  "overall_risk": "MEDIUM",
  "confidence_score": 0.89,
  "dealbreakers": [...],
  "critical_items": [...],
  "important_items": [...],
  "standard_items": [...],
  "context": {...}
}
```

---

### Table: `clauses`

Individual contract clauses extracted during analysis.

```sql
CREATE TABLE clauses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    section_number TEXT,
    title TEXT,
    text TEXT NOT NULL,
    category TEXT,
    risk_level TEXT,
    pattern_id TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
```

---

### Table: `risk_assessments`

Detailed risk assessment data.

```sql
CREATE TABLE risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_risk TEXT,
    critical_items TEXT,           -- JSON array
    dealbreakers TEXT,             -- JSON array
    confidence_score REAL,
    analysis_json TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
```

---

### Table: `negotiations`

Negotiation strategies and talking points.

```sql
CREATE TABLE negotiations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    strategy TEXT,
    leverage TEXT,
    position TEXT,
    key_points TEXT,              -- JSON array
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
```

---

## Indexes

Recommended indexes for performance:

```sql
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_type ON contracts(contract_type);
CREATE INDEX idx_contracts_upload_date ON contracts(upload_date);
CREATE INDEX idx_metadata_contract_id ON metadata(contract_id);
CREATE INDEX idx_assessments_contract_id ON assessments(contract_id);
CREATE INDEX idx_clauses_contract_id ON clauses(contract_id);
```

---

## Relationships

```
contracts (1) ----< (N) metadata
contracts (1) ----< (N) context
contracts (1) ----< (N) assessments
contracts (1) ----< (N) clauses
contracts (1) ----< (N) risk_assessments
contracts (1) ----< (N) negotiations
contracts (1) ----< (N) contracts (parent-child versioning)
```

---

## Data Types

### JSON Fields

Several fields store JSON data:

**parties** (string array):
```json
["Company A", "Company B", "Company C"]
```

**metadata_json** (object):
```json
{
  "uploaded": true,
  "auto_detected": true,
  "source": "AI extraction",
  "custom_field_1": "value"
}
```

**analysis_json** (complex object):
```json
{
  "overall_risk": "MEDIUM",
  "dealbreakers": [{...}],
  "critical_items": [{...}],
  "important_items": [{...}],
  "standard_items": [{...}]
}
```

---

## Sample Queries

### Get all active contracts
```sql
SELECT id, filename, contract_type, upload_date
FROM contracts
WHERE status = 'active'
ORDER BY upload_date DESC;
```

### Get contracts with high risk
```sql
SELECT c.id, c.filename, a.overall_risk, a.confidence_score
FROM contracts c
JOIN assessments a ON c.id = a.contract_id
WHERE a.overall_risk = 'HIGH'
ORDER BY a.confidence_score DESC;
```

### Get all versions of a contract
```sql
SELECT id, version_number, filename, upload_date
FROM contracts
WHERE parent_contract_id = 123 OR id = 123
ORDER BY version_number;
```

### Get contracts expiring soon
```sql
SELECT id, filename, effective_date, term_months
FROM contracts
WHERE DATE(effective_date, '+' || term_months || ' months')
      BETWEEN DATE('now') AND DATE('now', '+90 days')
ORDER BY effective_date;
```

---

## Maintenance

### Vacuum database (reclaim space)
```sql
VACUUM;
```

### Analyze query performance
```sql
ANALYZE;
```

### Check database integrity
```sql
PRAGMA integrity_check;
```

---

## Backup Recommendations

1. **Daily backups** of `data/contracts.db`
2. **Before migrations** - backup before schema changes
3. **After bulk operations** - backup after imports/deletions
4. **Retention**: Keep 30 days of backups

**Backup command:**
```bash
sqlite3 data/contracts.db ".backup data/contracts_backup_$(date +%Y%m%d).db"
```
