# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contract Intelligence Platform (CIP) - AI-powered contract analysis with Flask backend, Streamlit frontend, and Claude Sonnet 4 integration.

## Commands

### Start Services
```bash
# Both services (recommended)
cd C:\Users\jrudy\CIP && .\00_start_cip.bat

# Backend only (port 5000)
cd C:\Users\jrudy\CIP\backend && python api.py

# Frontend only (port 8501)
cd C:\Users\jrudy\CIP\frontend && streamlit run app.py
```

### Testing
```bash
# API health check
curl http://localhost:5000/health

# Database integrity
python scripts/database_integrity_check.py

# Integration tests
cd C:\Users\jrudy\CIP\tests && python test_api.py
```

## Architecture

### Backend (`backend/`)
- `api.py` - Flask REST API (21 endpoints), CORS enabled for Streamlit
- `orchestrator.py` - Claude API integration for contract analysis
- `prompt_composer.py` - Pattern-enhanced prompt composition (59 patterns)
- `config.py` - Loads from `.env`, defines model/paths/thresholds
- `redline_analyzer.py` + `redline_exporter.py` - Revision generation and DOCX export

### Frontend (`frontend/`)
**Entry Point:** `app.py` handles:
1. `st.set_page_config()` (must be first)
2. Dark theme injection via `components/theme.py`
3. Splash screen via `components/splash.py`
4. Redirect to `pages/1_🏠_Home.py`

**Theme System (centralized in app.py):**
- `theme_system.py` - Base theme + `inject_cip_logo()`
- `components/theme.py` - Dark theme CSS injection
- `ui_components.py` - Reusable UI components (dark theme colors)

**Page Wrapper Pattern:**
Pages use `components/page_wrapper.py` for consistent layout:
```python
from components.page_wrapper import init_page, page_header, page_footer
init_page("Title", "🏠")  # Session state, max-width, sidebar logo
page_header("Welcome", subtitle="...")
# ... page content ...
page_footer(show_status=True)
```

**Pages:** 8 pages (1-8) covering Home, Portfolio, Intake, Risk, Redlines, Compare, Negotiate, Reports

### Databases (`data/`)
- `contracts.db` - Main contracts, clauses, risk_assessments, negotiations, prompts
- `reports.db` - Comparisons, redlines, risk_reports, audit_log

## Key Patterns

### Dark Theme Colors
```python
BG = "#0F172A"       # Main background
SURFACE = "#1E293B"  # Cards, panels
RAISED = "#334155"   # Elevated elements
TEXT = "#E2E8F0"     # Primary text
MUTED = "#94A3B8"    # Secondary text
```

### API Key Handling
- **CIP Backend:** Uses `ANTHROPIC_API_KEY` from `C:\Users\jrudy\CIP\.env`
- **Claude Code:** Uses Claude.ai subscription only, NOT the API key
- Never set `ANTHROPIC_API_KEY` as environment variable globally

### Contract Stages (v1.3)
Pattern selection filters by stage: `MNDA`, `NDA`, `COMMERCIAL`, `EXECUTED`

## Forbidden Actions

1. **No PowerShell sound commands** - Never run `[System.Media.SystemSounds]::*`
2. **No global API key** - Never `export ANTHROPIC_API_KEY` or set in system environment
3. **No permission requests for pre-approved actions** - File I/O, Python scripts, git ops, pip installs are pre-approved

## UI Work Protocol

Claude Code cannot see browser output. For UI changes:

1. Report as `IMPLEMENTED (untested)` with max 70% confidence
2. Request specific user testing with screenshot verification
3. Only mark `COMPLETE` after user confirms visually

## File Locations

| Purpose | Path |
|---------|------|
| API Key | `C:\Users\jrudy\CIP\.env` |
| Contracts DB | `C:\Users\jrudy\CIP\data\contracts.db` |
| Reports DB | `C:\Users\jrudy\CIP\data\reports.db` |
| Uploads | `C:\Users\jrudy\CIP\data/uploads/` |
| Logs | `C:\Users\jrudy\CIP\logs/` |

---
## Git Workflow (MANDATORY)

Remote: https://github.com/jrudyg/CIP.git

### After ANY file changes:
1. Stage: `git add .`
2. Commit: `git commit -m "[descriptive message]"`
3. Push: Automatic via post-commit hook

### Commit triggers:
- After each completed fix
- Before ending session
- Before/after major changes

### If push fails:
1. Check remote: `git remote -v`
2. Manual push: `git push origin <branch>`
3. If auth error: Report to user

### Commands:
- Status: `git status`
- History: `git log --oneline -10`
- Restore file: `git checkout [hash] -- path/to/file`
- Sync check: `git log origin/main --oneline -3`
- Current branch: `git branch --show-current`
