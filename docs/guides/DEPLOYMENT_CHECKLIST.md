# CIP v1.0 Deployment Checklist

**Version:** 1.0
**Framework:** Z-Framework v1.1.1

---

## Pre-Deployment Validation

### 1. Smoke Tests (All Must PASS)

```bash
cd C:\Users\jrudy\CIP

# Run all zone smoke tests
python frontend/tests/z0_ingest_test.py
python frontend/tests/z1_smoke_test.py
python frontend/tests/z2_smoke_test.py
python frontend/tests/z3_smoke_test.py
python frontend/tests/z4_smoke_test.py
python frontend/tests/z5_smoke_test.py
python frontend/tests/z6_smoke_test.py
python frontend/tests/z7_smoke_test.py
python frontend/tests/z8_smoke_test.py
python frontend/tests/z9_smoke_test.py
```

| Test | Expected Output | Status |
|------|-----------------|--------|
| z0_ingest_test.py | "Z0 ingest/profile test passed" | [ ] |
| z1_smoke_test.py | "Z1 smoke test passed" | [ ] |
| z2_smoke_test.py | "Z2 smoke test passed" | [ ] |
| z3_smoke_test.py | "Z3 smoke test passed" | [ ] |
| z4_smoke_test.py | "Z4 smoke test passed" | [ ] |
| z5_smoke_test.py | "Z5 smoke test passed" | [ ] |
| z6_smoke_test.py | "Z6 smoke test passed" | [ ] |
| z7_smoke_test.py | "Z7 smoke test passed" | [ ] |
| z8_smoke_test.py | "Z8 smoke test passed" | [ ] |
| z9_smoke_test.py | "Z9 smoke test passed" | [ ] |

### 2. Environment Configuration

| Item | Check | Status |
|------|-------|--------|
| Python version | 3.10+ | [ ] |
| requirements.txt installed | `pip install -r requirements.txt` | [ ] |
| ANTHROPIC_API_KEY set | Environment variable configured | [ ] |
| Backend port available | 5000 (default) | [ ] |
| Frontend port available | 8501 (Streamlit default) | [ ] |

---

## File Manifest

### Core Application Files

```
CIP/
├── frontend/
│   ├── app.py                           [REQUIRED]
│   ├── zone_layout.py                   [REQUIRED]
│   ├── pages/
│   │   └── 5_📝_Redline_Reviews.py      [REQUIRED]
│   ├── tests/
│   │   ├── z0_ingest_test.py            [REQUIRED]
│   │   ├── z1_smoke_test.py             [REQUIRED]
│   │   ├── z2_smoke_test.py             [REQUIRED]
│   │   ├── z3_smoke_test.py             [REQUIRED]
│   │   ├── z4_smoke_test.py             [REQUIRED]
│   │   ├── z5_smoke_test.py             [REQUIRED]
│   │   ├── z6_smoke_test.py             [REQUIRED]
│   │   ├── z7_smoke_test.py             [REQUIRED]
│   │   ├── z8_smoke_test.py             [REQUIRED]
│   │   └── z9_smoke_test.py             [REQUIRED]
│   ├── validators/
│   │   └── redline_consistency.py       [REQUIRED]
│   └── z0/
│       ├── __init__.py                  [REQUIRED]
│       └── store.py                     [REQUIRED]
├── backend/
│   ├── api.py                           [REQUIRED]
│   └── contracts.db                     [CREATED AT RUNTIME]
└── requirements.txt                     [REQUIRED]
```

### Governance Documentation

```
CIP/
├── CIP.md                               [REQUIRED]
├── CIP_Zone_Framework.md                [REQUIRED]
├── CIP_Zone_Automation.md               [REQUIRED]
├── CIP_Agent_Governance_v1.1.1.md       [REQUIRED]
├── RELEASE_NOTES_v1.0.md                [REQUIRED]
└── DEPLOYMENT_CHECKLIST.md              [THIS FILE]
```

---

## Deployment Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Key
```bash
# Linux/Mac
export ANTHROPIC_API_KEY="your-key-here"

# Windows
set ANTHROPIC_API_KEY=your-key-here
```

### Step 3: Start Backend
```bash
python backend/api.py
```
Expected: Server running on http://localhost:5000

### Step 4: Start Frontend
```bash
streamlit run frontend/app.py
```
Expected: App running on http://localhost:8501

### Step 5: Verify Health
- Navigate to http://localhost:8501
- Check system status indicators (API, DB, AI should show green)
- Navigate to Redline Reviews page
- Verify all zones render without errors

---

## Post-Deployment Verification

### Functional Checks

| Check | Action | Expected Result | Status |
|-------|--------|-----------------|--------|
| Home page loads | Navigate to / | Home page renders | [ ] |
| Redline page loads | Navigate to Redline Reviews | Z1-Z9 render | [ ] |
| API health | GET /health | `{"status": "healthy"}` | [ ] |
| File upload | Upload test .docx | Document processed | [ ] |
| Risk analysis | Analyze uploaded doc | Z4-Z6 populate | [ ] |
| Export | Click export in Z7 | JSON/MD downloaded | [ ] |

### Performance Baselines

| Metric | Target | Status |
|--------|--------|--------|
| Page load time | < 3s | [ ] |
| Analysis time | < 30s | [ ] |
| Memory usage | < 2GB | [ ] |

---

## Rollback Procedure

If deployment fails:

1. Stop frontend: `Ctrl+C` in Streamlit terminal
2. Stop backend: `Ctrl+C` in Flask terminal
3. Review error logs
4. Restore from last known good state
5. Re-run smoke tests before retry

---

## CAI/GEM Validation Summary

| Zone | CAI Status | GEM Status | Final |
|------|------------|------------|-------|
| Z0 | PASS | N/A | PASS |
| Z1 | PASS | PASS | PASS |
| Z2 | PASS | PASS | PASS |
| Z3 | PASS | PASS | PASS |
| Z4 | PASS | PASS | PASS |
| Z5 | PASS | PASS | PASS |
| Z6 | PASS | PASS | PASS |
| Z7 | PASS | PASS | PASS |
| Z8 | PASS | PASS | PASS |
| Z9 | PASS | PASS | PASS |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| CAI (Semantic Authority) | | | [ ] PASS |
| GEM (UI/A11y Governor) | | | [ ] PASS |
| CC (Implementation) | | | [ ] PASS |
| AGENT-U (Strategic Approval) | | | [ ] DEPLOY |

---

**Deployment Status:** READY FOR AGENT-U [DEPLOY] CONFIRMATION
