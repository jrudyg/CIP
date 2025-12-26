# CIP Database Schema Update v2.0

**Date:** 2024-12-18
**Status:** BREAKING CHANGE
**Database:** `C:\Users\jrudy\CIP\data\contracts.db`
**Backup:** `contracts.db.backup_20251218_164723`

---

## Executive Summary

The CIP database schema has been cleaned and optimized. **All data has been cleared** for a fresh start. The schema was reduced from 14 tables to 8 tables, and 2 redundant columns were removed from the `contracts` table.

**Impact:** All roles must update any hardcoded references to removed tables/columns.

---

## What Changed

### Tables Removed (6)

| Removed Table | Replacement | Reason |
|---------------|-------------|--------|
| `redlines` | `redline_snapshots` | Snapshot-based architecture |
| `comparisons` | `comparison_snapshots` | Snapshot-based architecture |
| `contract_versions` | `contract_relationships` | Unified relationship tracking |
| `negotiations` | None | Never populated (deprecated) |
| `risk_reports` | `risk_assessments` | Consolidated risk data |
| `related_documents` | None | Never used (deprecated) |

### Columns Removed from `contracts` (2)

| Removed Column | Use Instead | Reason |
|----------------|-------------|--------|
| `purpose` | `contract_purpose` | Duplicate field |
| `end_date` | `expiration_date` | Duplicate field |

### Bug Fixed

| File | Line | Change |
|------|------|--------|
| `frontend/pages/1_Home.py` | 86 | `end_date` -> `expiration_date` |

---

## Current Schema (8 Tables)

```
TABLE                    ROWS    PURPOSE
─────────────────────────────────────────────────────────────
contracts                0       Core contract records (33 columns)
clauses                  0       Extracted contract clauses
risk_assessments         0       AI risk analysis results
analysis_snapshots       0       Point-in-time analysis captures
comparison_snapshots     0       Version comparison results
redline_snapshots        0       Revision suggestions with decisions
contract_relationships   0       Parent/child/version links
audit_log                0       Change tracking (future use)
```

---

## Data Model

```
                    ┌─────────────────────┐
                    │     contracts       │
                    │  (central entity)   │
                    └──────────┬──────────┘
                               │
       ┌───────────┬───────────┼───────────┬───────────┐
       │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ clauses  │ │  risk_   │ │analysis_ │ │redline_  │ │contract_ │
│          │ │assess-   │ │snapshots │ │snapshots │ │relation- │
│          │ │ments     │ │          │ │          │ │ships     │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ comparison_snapshots│
                    │  (links 2 analyses) │
                    └─────────────────────┘
```

---

## Role-Specific Guidance

### ORCHESTRATOR

**Key Changes:**
- All point-in-time data now uses snapshot tables
- `analysis_snapshots` stores full analysis as JSON in `clauses` field
- `redline_snapshots` stores clause-level suggestions in `clauses_json` field
- `comparison_snapshots` links two analysis snapshots via foreign keys

**API Patterns:**
```python
# Save analysis snapshot
INSERT INTO analysis_snapshots (contract_id, created_at, overall_risk, categories, clauses)
VALUES (?, datetime('now'), ?, ?, ?)

# Save redline snapshot
INSERT INTO redline_snapshots (contract_id, base_version_contract_id, source_mode,
                               created_at, overall_risk_before, clauses_json, status)
VALUES (?, ?, ?, datetime('now'), ?, ?, 'draft')
```

---

### AGENTS

**Read/Write Permissions:**
| Table | Read | Write |
|-------|------|-------|
| `contracts` | Yes | Yes |
| `clauses` | Yes | Yes |
| `risk_assessments` | Yes | Yes |
| `analysis_snapshots` | Yes | Yes |
| `redline_snapshots` | Yes | Yes |
| `comparison_snapshots` | Yes | Yes |
| `contract_relationships` | Yes | Yes |
| `audit_log` | Yes | No (system only) |

**Column Name Updates:**
```python
# WRONG - These columns no longer exist
contract.get('purpose')      # REMOVED
contract.get('end_date')     # REMOVED

# CORRECT - Use these instead
contract.get('contract_purpose')   # Use this
contract.get('expiration_date')    # Use this
```

**Required Fields for Contract Insert:**
```python
required_fields = ['filename']  # Minimum required

recommended_fields = [
    'filename', 'title', 'counterparty', 'contract_type',
    'status', 'effective_date', 'expiration_date', 'contract_purpose'
]
```

---

### DEBUGGERS

**Common Issues to Check:**

1. **Old Column References:**
   ```sql
   -- These will fail:
   SELECT purpose FROM contracts;        -- Column removed
   SELECT end_date FROM contracts;       -- Column removed

   -- Use instead:
   SELECT contract_purpose FROM contracts;
   SELECT expiration_date FROM contracts;
   ```

2. **Old Table References:**
   ```sql
   -- These tables no longer exist:
   SELECT * FROM redlines;           -- Use redline_snapshots
   SELECT * FROM comparisons;        -- Use comparison_snapshots
   SELECT * FROM negotiations;       -- Deprecated
   SELECT * FROM risk_reports;       -- Use risk_assessments
   SELECT * FROM contract_versions;  -- Use contract_relationships
   SELECT * FROM related_documents;  -- Deprecated
   ```

3. **Schema Verification:**
   ```sql
   -- Check current tables
   SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

   -- Check contracts columns
   PRAGMA table_info(contracts);

   -- Verify removed columns are gone
   -- 'purpose' and 'end_date' should NOT appear
   ```

**Backup Location:**
```
C:\Users\jrudy\CIP\data\contracts.db.backup_20251218_164723
```

---

### TESTERS

**Initial State:**
- All 8 tables exist but are empty (0 rows each)
- Auto-increment counters reset to 0
- Schema is clean with no orphaned data

**Test Sequence:**
1. **Contract Upload** - Test file upload creates contract record
2. **Clause Extraction** - Verify clauses link to contract_id
3. **Risk Analysis** - Check risk_assessments and analysis_snapshots
4. **Redline Generation** - Verify redline_snapshots created
5. **Version Comparison** - Test comparison_snapshots with two contracts

**Validation Queries:**
```sql
-- Verify schema version (8 tables expected)
SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';
-- Expected: 8

-- Verify contracts has 33 columns
SELECT COUNT(*) FROM pragma_table_info('contracts');
-- Expected: 33

-- Verify removed columns are gone
SELECT COUNT(*) FROM pragma_table_info('contracts')
WHERE name IN ('purpose', 'end_date');
-- Expected: 0
```

---

### CODERS

**Breaking Changes:**

1. **Column Renames:**
   ```python
   # Before
   cursor.execute("SELECT purpose, end_date FROM contracts")

   # After
   cursor.execute("SELECT contract_purpose, expiration_date FROM contracts")
   ```

2. **Removed Tables:**
   ```python
   # These will raise errors - tables don't exist:
   cursor.execute("SELECT * FROM redlines")
   cursor.execute("SELECT * FROM negotiations")
   cursor.execute("SELECT * FROM comparisons")

   # Use replacement tables instead
   ```

3. **Model Updates:**
   ```python
   # Update any dataclasses/models
   @dataclass
   class Contract:
       # Remove these:
       # purpose: str          # REMOVED
       # end_date: str         # REMOVED

       # Keep these:
       contract_purpose: str   # Use this
       expiration_date: str    # Use this
   ```

**SQL Best Practices:**
```python
# Always use parameterized queries
cursor.execute("""
    INSERT INTO contracts (filename, title, contract_purpose, expiration_date)
    VALUES (?, ?, ?, ?)
""", (filename, title, purpose, exp_date))

# Use column lists explicitly (don't rely on column order)
cursor.execute("""
    SELECT id, title, counterparty, contract_purpose, expiration_date
    FROM contracts
    WHERE id = ?
""", (contract_id,))
```

---

## Contracts Table Schema (33 Columns)

```sql
CREATE TABLE contracts (
    id                    INTEGER PRIMARY KEY,
    filename              TEXT NOT NULL,
    filepath              TEXT,
    title                 TEXT,
    counterparty          TEXT,
    contract_type         TEXT,
    contract_role         TEXT,
    status                TEXT DEFAULT 'intake',
    effective_date        TEXT,
    expiration_date       TEXT,           -- Use this (not end_date)
    renewal_date          TEXT,
    contract_value        REAL,
    parent_id             INTEGER,
    relationship_type     TEXT,
    version_number        INTEGER DEFAULT 1,
    is_latest_version     INTEGER DEFAULT 1,
    last_amended_date     TEXT,
    risk_level            TEXT,
    metadata_verified     INTEGER DEFAULT 0,
    parsed_metadata       TEXT,
    position              TEXT,
    leverage              TEXT,
    narrative             TEXT,
    parties               TEXT,
    metadata_json         TEXT,
    upload_date           TEXT,
    created_at            TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at            TEXT DEFAULT CURRENT_TIMESTAMP,
    archived              INTEGER DEFAULT 0,
    contract_purpose      TEXT,           -- Use this (not purpose)
    our_entity            TEXT,
    party_relationship    TEXT,
    display_id            TEXT
);
```

---

## Migration Checklist

- [x] Backup created: `contracts.db.backup_20251218_164723`
- [x] Tables dropped: 6 unused tables
- [x] Columns dropped: `purpose`, `end_date`
- [x] Bug fixed: `1_Home.py` column reference
- [x] Data cleared: All tables empty
- [x] Schema verified: 8 tables, 33 columns in contracts

---

## Questions?

If you encounter issues related to this schema update, check:
1. Are you using the correct column names?
2. Are you referencing tables that still exist?
3. Did you clear any cached schema information?

**Backup restoration (if needed):**
```python
import shutil
shutil.copy('contracts.db.backup_20251218_164723', 'contracts.db')
```
