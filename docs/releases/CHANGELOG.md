# Changelog

All notable changes to the Contract Intelligence Platform (CIP) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-11-26

### Added

#### Phase 6D: High-Value Enhancements
- **Deep Linking Support** - URL parameters for direct contract loading (`?contract=1`)
  - Auto-loads contracts from URL on page load
  - Updates URL when setting active contract
  - Enables bookmarking and sharing specific contracts
- **Recent Contracts Widget** - Sidebar widget showing last 5 viewed contracts
  - One-click access to recently viewed contracts
  - Automatic tracking (no duplicates, most recent first)
  - Export via `render_recent_contracts_widget()`

#### Phase 6B: Critical Fixes
- **Database Tables**
  - `clauses` table with indexes for contract analysis
  - `negotiations` table with indexes for negotiation tracking
- **Test Data** - 5 fully populated contracts:
  - Master Service Agreement ($250K, TechCorp Inc.)
  - Mutual NDA (Acme Corporation)
  - SOW - Project Alpha ($125K, Enterprise Solutions)
  - Software License ($48K, CloudSoft Systems)
  - Support Contract ($36K, DataGuard Inc.)
- **Error Handling** - Validation helpers for API endpoints:
  - `validate_claude_available()` - Check Claude API status
  - `validate_orchestrator_available()` - Check orchestrator status
  - `safe_db_connection()` - Database connection with error handling
- **Context Integration** - Added to Negotiate and Reports pages
  - Consistent context management across all 7 pages
  - Active contract header on every page
  - Auto-load from context

#### Phase 6C: Testing Infrastructure
- **Database Integrity Check** - `scripts/database_integrity_check.py`
  - Validates schema, data integrity, and relationships
  - Checks foreign keys, indexes, and data quality metrics
  - Exit code 0 on success, 1 on issues

#### Documentation
- **AUDIT_REPORT.md** - Phase 6A comprehensive audit findings
- **PHASE_6B_COMPLETE.md** - Phase 6B detailed completion report
- **TEST_RESULTS.md** - Phase 6C testing results with bug fixes
- **PHASE_6_COMPLETE.md** - Phase 6 final summary
- **CHANGELOG.md** - This file

### Fixed

#### Phase 6C: Bug Fixes
- **SQL Column Name Mismatch** (`backend/api.py` line 1620)
  - Query used `assessment_date` but column is `analysis_date`
  - Contract detail endpoint now returns correct data
- **filepath vs file_path Inconsistency** (`backend/api.py` line 1130)
  - Added fallback logic: `contract.get('filepath') or contract.get('file_path')`
  - Analysis endpoint no longer crashes with KeyError

### Changed

#### Phase 6B: Improvements
- **Enhanced Error Messages** - Structured JSON responses with actionable guidance
  ```json
  {
    "error": "Claude API not configured",
    "details": "ANTHROPIC_API_KEY environment variable not set",
    "action": "Set ANTHROPIC_API_KEY in your environment or .env file"
  }
  ```
- **API Validation** - Added to `/api/parse-metadata` and `/api/analyze`
- **Context Management** - Enhanced `contract_context.py`:
  - Deep linking support in `init_contract_context()`
  - URL management in `set_active_contract()` and `clear_active_contract()`
  - Recent contracts tracking with `_add_to_recent()`

### Performance

#### Phase 6C: Response Times
- Health Check: <50ms
- Contracts List: <100ms
- KPI Calculation: <150ms
- Contract Detail: <100ms
- Backend Startup: ~3 seconds

### Testing

#### Phase 6C: Test Coverage
- **API Endpoints Tested:** 8/8 (100% pass rate)
  - Health check
  - Contracts list
  - Portfolio KPIs
  - Portfolio filters
  - Contract detail
  - Contract versions
  - Analyze endpoint (initialization)
- **Bugs Found & Fixed:** 2 critical SQL bugs
- **Integration Tests:** Database integrity, API validation

---

## [1.0.0] - 2025-11-25

### Added - Phase 5: Context System Integration

#### Core Features
- **Contract Context Management** (`frontend/components/contract_context.py`)
  - Cross-page active contract state
  - Functions: `init_contract_context()`, `set_active_contract()`, `get_active_contract()`
  - Active contract header with clear button
- **Contract Detail Panel** (`frontend/components/contract_detail.py`)
  - Expandable 4-tab interface (Details, Versions, Relationships, History)
  - Action buttons: Analyze, Compare, Redline Review
  - Navigation to tool pages with context preserved

#### Page Integrations
- **Analyze Page** - Auto-loads active contract, shows header
- **Compare Page** - Suggests active contract as "Contract A"
- **Redline Review Page** - Auto-loads active contract for review

#### API Endpoints (Phase 4)
- `GET /api/portfolio/filters` - Get available filter values
- `POST /api/portfolio/contracts` - Get filtered contracts
- `POST /api/portfolio/kpis` - Get portfolio KPI metrics
- `GET /api/contract/<id>/versions` - Get version history
- `GET /api/contract/<id>/relationships` - Get related contracts
- `GET /api/contract/<id>/history` - Get activity log

#### Components
- `frontend/components/__init__.py` - Module exports for clean imports

### Changed

#### Phase 4: Portfolio Enhancement
- **Contracts Portfolio Page** - Complete rewrite (105 → 222 lines)
  - Sidebar filters (type, status, risk level)
  - Clickable KPI cards that filter table
  - Dynamic contract table
  - Contract selection and activation
  - Expandable detail panel

---

## Earlier Releases

### [0.9.0] - Phase 1-3
- Initial project structure
- Backend API with Flask
- Frontend with Streamlit
- Claude API integration
- Contract analysis engine
- Comparison tools
- 7 main pages: Intake, Portfolio, Analyze, Compare, Negotiate, Redline, Reports

---

## Development Timeline

| Phase | Date | Duration | Key Deliverables |
|-------|------|----------|------------------|
| Phases 1-3 | 2025-11-24 | Multiple days | Core platform, 7 pages, analysis engine |
| Phase 4 | 2025-11-25 | 2 hours | Portfolio filters, KPIs, detail panel |
| Phase 5 | 2025-11-25 | 15 minutes | Context system integration |
| Phase 6A | 2025-11-26 | 15 minutes | Comprehensive audit |
| Phase 6B | 2025-11-26 | 30 minutes | Critical fixes, test data |
| Phase 6C | 2025-11-26 | 20 minutes | Testing, 2 bugs fixed |
| Phase 6D | 2025-11-26 | 10 minutes | Deep linking, recent contracts |

**Total Phase 6 Time:** 75 minutes (Target: 240 min, Beat by 69%)

---

## Statistics

### Code Metrics
- **Backend Files:** 9 core files
- **Frontend Pages:** 7 pages
- **Frontend Components:** 3 reusable components
- **API Endpoints:** 20 endpoints
- **Database Tables:** 8 tables (5 contracts, 3 reports)
- **Test Coverage:** 8/8 API endpoints tested

### Phase 6 Deliverables
- **New Files:** 6 (3 scripts, 3 docs)
- **Modified Files:** 6
- **New Code:** ~600 lines
- **Documentation:** ~1500 lines
- **Bugs Fixed:** 2 critical
- **Features Added:** 2 enhancements
- **Tests Written:** 8 API tests

---

## Links

- [Phase 6 Complete Summary](PHASE_6_COMPLETE.md)
- [Audit Report](AUDIT_REPORT.md)
- [Test Results](TEST_RESULTS.md)
- [Phase 6B Details](PHASE_6B_COMPLETE.md)
- [Phase 5 Completion](PHASE_5_COMPLETE.md)

---

*Generated by Claude Code - Autonomous Development Protocol*
