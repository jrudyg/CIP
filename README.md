# Contract Intelligence Platform (CIP)

AI-powered contract analysis, comparison, and negotiation support system powered by Claude.

**Version:** 1.3.0
**Status:** ✅ Production Ready
**Last Updated:** 2025-11-27

---

## 🎯 Overview

The Contract Intelligence Platform (CIP) is a comprehensive system for analyzing, comparing, and managing legal contracts using AI. Built with Python, Flask, Streamlit, and Claude API, it provides:

- **AI-Powered Analysis** - Risk assessment and clause extraction
- **Pattern-Enhanced Prompts** - 59-pattern deck with v1.3 Pattern Library (NEW v1.3)
- **Contract Stage Filtering** - MNDA/NDA/COMMERCIAL/EXECUTED stage awareness
- **Escalation Tracking** - CEO, LEGAL, INSURANCE approval requirements
- **Dealbreaker Detection** - Automatic flagging of non-negotiable patterns
- **Version Comparison** - Track changes between contract versions
- **Redline Generation** - Automated revision suggestions
- **Portfolio Management** - Track and manage multiple contracts
- **Negotiation Support** - Strategy recommendations
- **Deep Linking** - Share contracts via URL

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.9+
Anthropic API Key (Claude)
Git
```

### Installation

```bash
# Clone repository
git clone <repository-url>
cd CIP

# Install dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-api-key-here"

# Initialize database
python data/setup_databases.py
```

### Running the Application

```bash
# Terminal 1: Start backend
cd backend
python api.py
# Backend runs on http://localhost:5000

# Terminal 2: Start frontend
cd frontend
streamlit run app.py
# Frontend runs on http://localhost:8501
```

---

## 📊 Features

### Contract Analysis
- AI-powered risk assessment
- Dealbreaker identification
- Clause categorization
- Confidence scoring
- Context-aware analysis (position, leverage, narrative)

### Version Comparison
- Side-by-side comparison
- Change tracking (substantive vs administrative)
- Executive summary generation
- DOCX report export
- JSON data export

### Portfolio Management
- Real-time KPI dashboard ($459K test portfolio)
- Advanced filtering (type, status, risk, counterparty)
- Contract detail panels with tabs
- Version tracking and relationships
- Expiration alerts

### Context Management
- Active contract persists across pages
- Deep linking support (`?contract=1`)
- Recent contracts widget (last 5)
- One-click navigation between tools

### Redline Review
- Clause-by-clause review
- Pattern-based suggestions
- Risk level indicators
- Change metrics (minimal vs substantial)

---

## 🏗️ Architecture

### Backend (Flask API)
```
backend/
├── api.py                  # Main Flask application (21 endpoints)
├── config.py               # Configuration management
├── orchestrator.py         # Analysis orchestration
├── prompt_composer.py      # Pattern-enhanced prompt composition (NEW v1.2)
├── pattern_matcher.py      # Legacy pattern matching (DEPRECATED)
├── logger_config.py        # Logging infrastructure
└── redline_analyzer.py     # Redline generation
```

### Frontend (Streamlit)
```
frontend/
├── app.py                  # Main application entry
├── pages/
│   ├── 0_📋_Intake.py              # Contract upload wizard
│   ├── 1_📊_Contracts_Portfolio.py  # Portfolio dashboard
│   ├── 2_🔍_Analyze.py              # AI analysis
│   ├── 3_⚖️_Compare.py              # Version comparison
│   ├── 4_🤝_Negotiate.py            # Negotiation support
│   ├── 5_📝_Redline_Review.py       # Redline generation
│   └── 6_📑_Reports.py              # Report management
└── components/
    ├── contract_context.py  # Context management + deep linking
    ├── contract_detail.py   # Detail panel component
    └── __init__.py          # Module exports
```

### Database
```
data/
├── contracts.db     # Main contracts database
│   ├── contracts           (5 records)
│   ├── risk_assessments    (analysis results)
│   ├── clauses             (extracted clauses)
│   ├── negotiations        (strategy tracking)
│   └── prompts             (composed prompts - NEW v1.2)
└── reports.db       # Reports database
    ├── comparisons         (28 records)
    ├── risk_reports        (generated reports)
    ├── redlines            (revision suggestions)
    └── audit_log           (action tracking)
```

### Pattern Deck (v1.3)
```
CCE/memory/patterns/
└── deck_v3_phase3.json    # 59 patterns with v1.3 Pattern Library confirmations
    ├── Core (2.x.x)       # 37 patterns: liability, payment, termination, etc.
    ├── Specialized (3.x.x) # 22 patterns: integrator, service provider, NDA
    └── v1.3 Metadata:
        ├── v1_3_status        # CONFIRMED, RESEARCH_NEEDED, DEALBREAKER, LEGAL_REVIEW
        ├── stage_restrictions # MNDA, NDA, COMMERCIAL, EXECUTED
        ├── escalation         # CEO, LEGAL, INSURANCE
        └── v1_3_user_notes    # Interview confirmations
```

---

## 🔌 API Endpoints

### Core Operations
- `GET /health` - Health check
- `GET /api/contracts` - List all contracts
- `GET /api/contract/<id>` - Get contract details
- `POST /api/analyze` - Analyze contract with AI (pattern-enhanced)
- `POST /api/compare` - Compare two versions
- `POST /api/patterns/select` - Select patterns for contract type with stage filtering (v1.3)

### Portfolio
- `GET /api/portfolio/filters` - Get filter options
- `POST /api/portfolio/contracts` - Get filtered contracts
- `POST /api/portfolio/kpis` - Get KPI metrics

### Contract Details
- `GET /api/contract/<id>/versions` - Version history
- `GET /api/contract/<id>/relationships` - Related contracts
- `GET /api/contract/<id>/history` - Activity log

### Intake Wizard
- `POST /api/upload-enhanced` - Upload contract
- `POST /api/parse-metadata` - Extract metadata with AI
- `POST /api/verify-metadata` - Save verified metadata
- `POST /api/find-similar` - Find similar contracts
- `POST /api/link-contracts` - Create relationships

### Analysis
- `POST /api/redline-review` - Generate redline suggestions
- `GET /api/assessment/<id>` - Get risk assessment
- `GET /api/statistics` - Platform statistics
- `GET /api/dashboard/stats` - Dashboard metrics

**Total:** 21 endpoints | **Tested:** 8/8 core (100% pass rate)

---

## 💾 Database Schema

### contracts table (23 columns)
```sql
id, filename, filepath, upload_date, contract_type, parties,
effective_date, term_months, status, version_number, position,
leverage, narrative, metadata_json, title, counterparty,
contract_value, expiration_date, risk_level, parent_id,
relationship_type, last_amended_date, created_at, parsed_metadata,
contract_role, is_latest_version, contract_stage  -- v1.3: MNDA|NDA|COMMERCIAL|EXECUTED
```

### clauses table
```sql
id, contract_id, section_number, title, text,
category, risk_level, pattern_id
```

### risk_assessments table
```sql
id, contract_id, overall_risk, analysis_date, details
```

### negotiations table
```sql
id, contract_id, strategy, leverage, position,
key_points, created_date
```

---

## 📈 Test Data

The system includes 5 pre-populated test contracts:

| ID | Title | Counterparty | Value | Risk | Status |
|----|-------|--------------|-------|------|--------|
| 1 | Master Service Agreement | TechCorp Inc. | $250,000 | Moderate | active |
| 2 | Mutual NDA | Acme Corporation | N/A | Low | active |
| 3 | SOW - Project Alpha | Enterprise Solutions | $125,000 | High | review |
| 4 | Software License | CloudSoft Systems | $48,000 | Moderate | active |
| 5 | Support Contract | DataGuard Inc. | $36,000 | Low | expiring |

**Portfolio KPIs:**
- Total Value: $459,000
- Active Contracts: 3
- High Risk: 1
- Expiring in 90 Days: 2

---

## 🧪 Testing

### Run API Tests
```bash
# Backend health check
curl http://localhost:5000/health

# Get contracts list
curl http://localhost:5000/api/contracts

# Get portfolio KPIs
curl -X POST http://localhost:5000/api/portfolio/kpis \
  -H "Content-Type: application/json" -d '{}'
```

### Run Database Integrity Check
```bash
python scripts/database_integrity_check.py
# Expected output: [OK] All checks passed
```

### Manual UI Testing
See `TEST_RESULTS.md` for comprehensive testing checklist.

---

## 🐛 Debugging

### Backend Not Starting
```bash
# Check Python version
python --version  # Should be 3.9+

# Check API key
echo $ANTHROPIC_API_KEY  # Should not be empty

# Check logs
cat backend/api_test.log
```

### Frontend Not Loading
```bash
# Check backend is running
curl http://localhost:5000/health

# Check Streamlit version
streamlit --version

# Run with debug mode
streamlit run app.py --logger.level=debug
```

### Database Issues
```bash
# Run integrity check
python scripts/database_integrity_check.py

# Reset database (WARNING: Deletes all data)
rm data/contracts.db data/reports.db
python data/setup_databases.py
python data/populate_test_data.py
```

---

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[PHASE_6_COMPLETE.md](PHASE_6_COMPLETE.md)** - Phase 6 final summary
- **[AUDIT_REPORT.md](AUDIT_REPORT.md)** - Comprehensive system audit
- **[TEST_RESULTS.md](TEST_RESULTS.md)** - Testing results and bug fixes
- **[PHASE_6B_COMPLETE.md](PHASE_6B_COMPLETE.md)** - Critical fixes details
- **[PHASE_5_COMPLETE.md](PHASE_5_COMPLETE.md)** - Context system integration

---

## 🔧 Configuration

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY="your-claude-api-key"

# Optional
CIP_API_HOST="127.0.0.1"        # API host
CIP_API_PORT="5000"             # API port
CIP_DEBUG="True"                # Debug mode
LOG_LEVEL="INFO"                # Logging level
MOCK_CLAUDE_API="False"         # Mock mode for testing
```

### Configuration File
Edit `backend/config.py` to customize:
- Database paths
- Model selection (default: claude-sonnet-4-20250514)
- Confidence thresholds
- Risk classification
- Workflow timeouts

---

## 🎨 UI Components

### Context Management
```python
from components import (
    init_contract_context,
    set_active_contract,
    get_active_contract,
    render_active_contract_header,
    render_recent_contracts_widget
)

# Initialize context (call once per page)
init_contract_context()

# Render header
render_active_contract_header()

# Set active contract
set_active_contract(contract_id=1)

# Get active contract
active_id = get_active_contract()

# Render recent contracts in sidebar
with st.sidebar:
    render_recent_contracts_widget()
```

### Deep Linking
```python
# Auto-load from URL
http://localhost:8501/?contract=1

# Programmatic navigation
set_active_contract(1, update_url=True)
```

---

## 🚦 Performance

### Response Times (Phase 6C Benchmark)
| Endpoint | Response Time |
|----------|---------------|
| Health Check | <50ms |
| Contracts List | <100ms |
| KPI Calculation | <150ms |
| Contract Detail | <100ms |
| Backend Startup | ~3 seconds |

### Analysis Times
| Operation | Duration |
|-----------|----------|
| Contract Analysis | 30-90 seconds |
| Version Comparison | 5-8 minutes |
| Redline Generation | 2-5 minutes |

---

## 🛣️ Roadmap

### Completed (v1.1.0)
- ✅ Deep linking support
- ✅ Recent contracts widget
- ✅ Database integrity check
- ✅ Error handling improvements
- ✅ Context system integration

### Completed (v1.3.0)
- ✅ Pattern Library v1.3 integration (59 patterns with user confirmations)
- ✅ Contract stage filtering (MNDA/NDA/COMMERCIAL/EXECUTED)
- ✅ Escalation tracking (CEO, LEGAL, INSURANCE requirements)
- ✅ Dealbreaker detection and alerting
- ✅ Category C (NDA) and G (Broker) pattern enrichment
- ✅ Stage-aware pattern selection in prompt_composer
- ✅ UI updates for stage selection and escalation display

### Future Enhancements
- [ ] Automated UI testing (Selenium/Playwright)
- [ ] Contract health score calculation
- [ ] Bulk export functionality
- [ ] Workflow breadcrumbs visualization
- [ ] Session persistence (localStorage)
- [ ] Multi-contract selection for batch operations
- [ ] Analytics dashboard for usage tracking

---

## 🤝 Contributing

### Development Workflow
1. Create feature branch
2. Make changes
3. Run tests: `python scripts/database_integrity_check.py`
4. Update CHANGELOG.md
5. Create pull request

### Code Style
- Python: PEP 8
- Type hints: Required for new code
- Docstrings: Required for public functions
- Logging: Use `logger_config.py` infrastructure

---

## 📝 License

[Add your license here]

---

## 🙏 Acknowledgments

Built with:
- **[Anthropic Claude](https://www.anthropic.com/)** - AI analysis engine
- **[Flask](https://flask.palletsprojects.com/)** - Backend API
- **[Streamlit](https://streamlit.io/)** - Frontend framework
- **[SQLite](https://www.sqlite.org/)** - Database
- **[python-docx](https://python-docx.readthedocs.io/)** - Document processing

---

## 📞 Support

For issues, questions, or contributions:
- Check [AUDIT_REPORT.md](AUDIT_REPORT.md) for system status
- Review [TEST_RESULTS.md](TEST_RESULTS.md) for known issues
- See [CHANGELOG.md](CHANGELOG.md) for recent changes

---

**Generated by Claude Code - Autonomous Development Protocol**
**v1.3 Integration Complete: Pattern Library v1.3 | Stage Filtering | Escalation Tracking | 6/6 E2E Tests Passed**
