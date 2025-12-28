# CIP Backend - Product Requirements Document
**Version:** 0.1 DRAFT  
**Created:** December 27, 2025  
**Status:** Awaiting User Review  
**Purpose:** Define "correct" backend state for CC validation

---

## 1. SYSTEM OVERVIEW

### 1.1 What CIP Does
Contract Intelligence Platform analyzes, compares, and manages contract risk.

### 1.2 Backend Components
| Component | Technology | Location |
|-----------|------------|----------|
| API Server | Flask | backend/api.py |
| Orchestrator | Python + Claude API | backend/orchestrator.py |
| Database | SQLite | data/contracts.db |
| Cache DBs | SQLite | data/clause_embeddings.db, data/comparison_snapshots.db |
| File Storage | Filesystem | data/reports/, uploads/ |

### 1.3 Core User Flows
```
UPLOAD    → Store contract → Hash content → Return ID
ANALYZE   → Extract clauses → Score risk → Store results
COMPARE   → Match V1↔V2 clauses → Generate redlines → Store/cache
RETRIEVE  → Return cached results if valid → Else re-run
DELETE    → Remove contract → Cascade to related records
```

---

## 2. DATABASE REQUIREMENTS

### 2.1 Tables

| Table | Purpose | Required Columns |
|-------|---------|------------------|
| contracts | Source documents | id, filename, filepath, content_hash, created_at, updated_at, last_analyzed_at |
| clauses | Extracted clause text | id, contract_id (FK), section_number, title, text, category, risk_level |
| risk_assessments | Analysis results | id, contract_id (FK), assessment_date, overall_risk, confidence_score, analysis_json |
| analysis_snapshots | Cached analysis | snapshot_id, contract_id (FK), source_hash, created_at, overall_risk, clauses |
| comparison_snapshots | Cached comparisons | id, v1_contract_id (FK), v2_contract_id (FK), comparison_hash, result_json, created_at |
| redline_snapshots | Cached redlines | id, contract_id (FK), created_at, redlines_json |

### 2.2 Integrity Rules

| Rule | Requirement | Enforcement |
|------|-------------|-------------|
| FK Enforcement | ON for all connections | PRAGMA foreign_keys = ON |
| Cascade Deletes | Contract deletion removes related records | ON DELETE CASCADE |
| No Orphans | Every child record has valid parent | FK constraint |
| Content Hash | Every contract has SHA-256 hash | NOT NULL after upload |
| Timestamps | created_at on insert, updated_at on modify | Trigger or application |

### 2.3 Integrity Thresholds

| Metric | Target | Current (Report 2) |
|--------|--------|-------------------|
| Orphaned records | 0 | 24 |
| FK enforcement | ON | OFF |
| Null content_hash | 0 | N/A (column missing) |
| Integrity score | ≥95% | 62% |

---

## 3. API REQUIREMENTS

### 3.1 Endpoints

| Endpoint | Method | Function | Idempotent |
|----------|--------|----------|------------|
| /api/contracts | GET | List all contracts | Yes |
| /api/contract/{id} | GET | Get contract + clauses + assessments | Yes |
| /api/contract/{id} | DELETE | Delete contract + cascade | Yes |
| /api/upload | POST | Upload new contract | No |
| /api/analyze/{id} | POST | Run risk analysis | No (but should cache) |
| /api/compare | POST | Compare V1 vs V2 | No (but should cache) |

### 3.2 Response Standards

| Scenario | Response |
|----------|----------|
| Success | 200 + JSON body |
| Created | 201 + resource ID |
| Not Found | 404 + error message |
| Server Error | 500 + error message (no stack trace) |
| Cached Result | 200 + cached: true flag |

### 3.3 Caching Behavior

| Operation | Cache Strategy |
|-----------|---------------|
| Risk Analysis | Cache on first run. Return cached if source_hash unchanged. |
| Comparison | Cache on first run per (v1_id, v2_id) pair. Return cached if both content_hash unchanged. |
| Invalidation | Source document change → invalidate linked caches |
| Re-analysis | Explicit user request only. Warn before overwriting cache. |

---

## 4. DATA FLOW REQUIREMENTS

### 4.1 Upload Flow
```
INPUT:  .docx file
STEPS:  1. Compute SHA-256 hash of file bytes
        2. Check if hash exists (duplicate detection)
        3. Store file to uploads/
        4. Insert contracts record with content_hash
        5. Return contract_id
OUTPUT: { id: X, filename: "...", content_hash: "...", duplicate: false }
```

### 4.2 Analysis Flow
```
INPUT:  contract_id
STEPS:  1. Check analysis_snapshots for matching source_hash
        2. IF cached AND not stale → Return cached
        3. ELSE → Run Claude analysis
        4. Store results in risk_assessments + analysis_snapshots
        5. Update contracts.last_analyzed_at
OUTPUT: { cached: bool, overall_risk: "...", clauses: [...] }
```

### 4.3 Comparison Flow
```
INPUT:  v1_contract_id, v2_contract_id
STEPS:  1. Compute comparison_hash from (v1_hash, v2_hash)
        2. Check comparison_snapshots for matching hash
        3. IF cached → Return cached
        4. ELSE → Run Claude comparison
        5. Store results in comparison_snapshots
OUTPUT: { cached: bool, comparison_id: X, clause_pairs: [...] }
```

### 4.4 Delete Flow
```
INPUT:  contract_id
STEPS:  1. DELETE FROM contracts WHERE id = X
        2. CASCADE removes: clauses, risk_assessments, analysis_snapshots
        3. CASCADE removes: comparison_snapshots where v1 or v2 = X
        4. Remove file from uploads/
OUTPUT: { deleted: true, cascaded: { clauses: N, assessments: N, ... } }
```

---

## 5. RESILIENCE REQUIREMENTS

### 5.1 Error Handling

| Error Type | Required Behavior |
|------------|-------------------|
| DB Connection Failed | Retry 3x with backoff → Return 503 |
| Claude API Timeout | Retry 2x → Return partial result with warning |
| File Not Found | Return 404, don't crash |
| Invalid Input | Return 400 with specific validation error |
| Constraint Violation | Rollback transaction → Return 409 |

### 5.2 Transaction Boundaries

| Operation | Transaction Scope |
|-----------|-------------------|
| Upload | Single transaction: insert contract |
| Analysis | Transaction per table: clauses, then assessment |
| Delete | Single transaction: contract + all cascades |
| Comparison | Single transaction: snapshot insert |

### 5.3 Rollback Capability

| Scenario | Recovery Method |
|----------|-----------------|
| Failed analysis mid-run | Delete partial clauses, reset state |
| Corrupted database | Restore from backup (daily automated) |
| Bad migration | Revert script + restore backup |

---

## 6. PERFORMANCE REQUIREMENTS

### 6.1 Response Time Targets

| Operation | Target | Acceptable |
|-----------|--------|------------|
| List contracts | <200ms | <500ms |
| Get contract | <500ms | <1s |
| Upload (10MB) | <3s | <5s |
| Cached analysis | <500ms | <1s |
| Fresh analysis | <60s | <90s |
| Cached comparison | <500ms | <1s |
| Fresh comparison | <90s | <120s |

### 6.2 Capacity Targets

| Metric | Target |
|--------|--------|
| Contracts | 1,000+ |
| Clauses per contract | 200+ |
| Concurrent users | 5 |
| Database size | <1GB |

---

## 7. CURRENT STATE vs REQUIREMENTS

### 7.1 Known Gaps (from CC Reports)

| Requirement | Current State | Gap |
|-------------|---------------|-----|
| FK enforcement | OFF | Missing PRAGMA |
| Cascade deletes | None | Schema requires recreation |
| content_hash column | Missing | ALTER TABLE needed |
| last_analyzed_at column | Missing | ALTER TABLE needed |
| Comparison caching | Files only, no DB | Phase 5 not activated |
| Orphan records | 24 | Cleanup needed |
| Integrity score | 62% | Below 95% target |

### 7.2 Phase 5 Infrastructure (Built, Not Activated)

| Component | Status | Activation |
|-----------|--------|------------|
| EmbeddingCache | Code complete | Flag = False |
| ComparisonSnapshotCache | Code complete | Flag = False |
| PatternCache | Code complete | Flag = False |
| Hashing utilities | Working | Used internally |

---

## 8. VALIDATION CRITERIA

### 8.1 "Correct" Backend State

```
□ Zero orphaned records
□ FK enforcement ON in all connections
□ content_hash populated for all contracts
□ last_analyzed_at populated after analysis
□ Comparison returns cached result on second call
□ Delete cascades to all related tables
□ Integrity score ≥95%
```

### 8.2 Test Scenarios

| Test | Expected Result |
|------|-----------------|
| Upload same file twice | Second returns duplicate: true |
| Analyze → Analyze again | Second returns cached: true |
| Compare V1/V2 → Compare again | Second returns cached: true |
| Delete contract | Related clauses/assessments deleted |
| Modify source file → Re-upload | New content_hash, old cache invalidated |

---

## 9. OPEN QUESTIONS

| # | Question | Needs Answer From |
|---|----------|-------------------|
| 1 | Stale cache threshold - 7 days per trust_engine.py? | User |
| 2 | Should duplicate uploads be blocked or allowed? | User |
| 3 | CASCADE delete comparison_snapshots when either V1 or V2 deleted? | User |
| 4 | Backup frequency requirement? | User |
| 5 | Phase 5 activation priority order? | User |

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-27 | Initial draft from CC investigation reports |

---

*Awaiting User review before CC validation.*
