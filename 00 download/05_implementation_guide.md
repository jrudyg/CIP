# CIP Enhanced Metadata Implementation Guide
# Version: 2.0
# Date: 2026-01-05

## OVERVIEW
Add 5 new metadata fields, update AI extraction, and make all fields editable on Contract Details page.

## FILES IN THIS PACKAGE
1. `01_db_migration.sql` - Database schema update
2. `02_extraction_prompt.md` - Reference prompt (embedded in api.py)
3. `03_api_updates.py` - API endpoint updates (parse-metadata, verify-metadata, PUT contract)
4. `04_Contract_Details.py` - New frontend page (replaces existing)
5. `05_implementation_guide.md` - This file

## INSTALLATION STEPS

### Step 1: Database Migration
```bash
cd C:\Users\jrudy\CIP
sqlite3 data/contracts.db < 00_download/01_db_migration.sql
```

Verify:
```bash
sqlite3 data/contracts.db ".schema contracts" | grep -E "counterparty_role|payment_terms|liability_cap|governing_law|warranty_period|file_size"
```

### Step 2: Update api.py

**2a. Replace /api/parse-metadata endpoint (~lines 613-764)**
- Find: `@app.route('/api/parse-metadata', methods=['POST'])`
- Replace entire function with version from `03_api_updates.py`

**2b. Replace /api/verify-metadata endpoint (~lines 767-850)**
- Find: `@app.route('/api/verify-metadata', methods=['POST'])`
- Replace entire function with version from `03_api_updates.py`

**2c. Add new PUT endpoint**
- Find: GET `/api/contract/<int:contract_id>` (~line 1909)
- Insert PUT endpoint from `03_api_updates.py` AFTER the GET endpoint

### Step 3: Update Frontend
```bash
cp 00_download/04_Contract_Details.py frontend/pages/3_Contract_Details.py
```

### Step 4: Restart Services
```bash
# Terminal 1: Backend
cd backend
python api.py

# Terminal 2: Frontend
cd frontend
streamlit run app.py
```

## NEW DATABASE COLUMNS
| Column | Type | Description |
|--------|------|-------------|
| counterparty_role | TEXT | Customer/Vendor/Partner/etc |
| payment_terms | TEXT | Net 30, Net 60, etc |
| liability_cap | TEXT | Dollar amount or formula |
| governing_law | TEXT | State/jurisdiction |
| warranty_period | TEXT | Duration after completion |
| file_size | INTEGER | Bytes (system captured) |

## AI EXTRACTION FIELDS (16 total)
| Field | AI Extracted | N/A Rules |
|-------|--------------|-----------|
| title | ✅ | Never N/A |
| contract_type | ✅ | Never N/A |
| effective_date | ✅ | Never N/A |
| expiration_date | ✅ | Never N/A |
| our_entity | ✅ | Never N/A |
| our_role (position) | ✅ | Never N/A |
| counterparty | ✅ | Never N/A |
| counterparty_role | ✅ | Never N/A |
| contract_value | ✅ | N/A for NDA/MNDA |
| payment_terms | ✅ | N/A for NDA/MNDA |
| liability_cap | ✅ | Never N/A |
| auto_renewal | ✅ | N/A for SOW/Amendment |
| termination_notice_days | ✅ | Never N/A |
| governing_law | ✅ | Never N/A |
| warranty_period | ✅ | N/A for NDA/MNDA |
| file_size | ❌ (system) | Never N/A |

## CONTRACT DETAILS PAGE BEHAVIOR
- All fields always editable (no Edit button)
- Save/Cancel buttons appear dynamically when changes detected
- Buttons positioned top-right
- "Not found" displayed for missing AI extractions
- "N/A" displayed for inapplicable fields

## TESTING CHECKLIST
- [ ] DB migration runs without errors
- [ ] New columns exist in contracts table
- [ ] /api/parse-metadata extracts all 16 fields
- [ ] /api/verify-metadata stores all fields
- [ ] PUT /api/contract/<id> updates fields
- [ ] Contract Details page loads without errors
- [ ] Fields show current values (not blank)
- [ ] Save/Cancel appear only on change
- [ ] Save persists changes to database
- [ ] Cancel reverts to original values

## ROLLBACK
If issues occur:
```bash
# Restore api.py from git
git checkout backend/api.py

# Restore frontend page from git
git checkout frontend/pages/3_Contract_Details.py
```

Note: DB columns cannot be easily removed in SQLite. They will remain but be unused.
