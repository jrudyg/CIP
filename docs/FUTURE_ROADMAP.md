# CIP Future Development Roadmap

**Contract Intelligence Platform - Strategic Development Plan**

**Version:** 1.0
**Last Updated:** 2025-11-22
**Status:** Phase A Complete, Ready for Phase B Planning

---

## TABLE OF CONTENTS

1. [Overview](#1-overview)
2. [Phase B: User Profiles & Multi-Entity Support](#2-phase-b-user-profiles--multi-entity-support)
3. [Phase C: Advanced Search & Filtering](#3-phase-c-advanced-search--filtering)
4. [Phase D: Clause Library System](#4-phase-d-clause-library-system)
5. [Phase E: Remaining Workflows](#5-phase-e-remaining-workflows)
6. [Technical Enhancements](#6-technical-enhancements)
7. [UI/UX Improvements](#7-uiux-improvements)
8. [Integration Opportunities](#8-integration-opportunities)
9. [Security & Compliance](#9-security--compliance)
10. [Implementation Notes](#10-implementation-notes)

---

## 1. OVERVIEW

### 1.1 Current System State

**Phase A: Enhanced Upload System** ✅ COMPLETE (2025-11-22)

**Implemented Features:**
- Drag-and-drop contract upload
- AI-powered metadata extraction (Claude Sonnet 4)
- Intelligent version detection (80% similarity threshold)
- Business context suggestions
- 3-stage confirmation workflow
- Database persistence with version chains
- Thread-safe concurrent operations

**Current Capabilities:**
- Upload: DOCX, PDF, TXT contracts
- Analysis: Risk assessment, dealbreaker detection, clause analysis
- Comparison: Side-by-side version comparison with redlines
- Database: Contracts, risk assessments, comparisons

**System Metrics:**
- Total API Endpoints: 10
- Database Tables: 8
- Knowledge Base Documents: 12
- Frontend Pages: 6 (2 fully functional: Upload, Analysis)

---

### 1.2 Vision for Complete CIP Platform

**Mission:** Transform contract management from reactive document review to proactive risk intelligence and strategic negotiation support.

**Strategic Goals:**
1. **Reduce contract review time** from days to hours
2. **Increase negotiation success rate** through data-driven insights
3. **Build institutional knowledge** via clause library and pattern recognition
4. **Enable multi-entity management** for organizations with multiple subsidiaries
5. **Provide executive visibility** through metrics and dashboards

**Target Users:**
- Legal teams (in-house counsel, contract managers)
- Procurement departments
- Sales operations
- Risk management
- Executive leadership (dashboard consumers)

---

### 1.3 Development Priority Framework

**Priority Levels:**

**P0 - Critical (Must Have):**
- Features blocking core workflow
- Security vulnerabilities
- Data integrity issues
- Critical user experience problems

**P1 - High (Should Have):**
- Features significantly improving productivity
- User-requested enhancements with clear ROI
- Competitive differentiation features
- Technical debt reduction

**P2 - Medium (Nice to Have):**
- Convenience features
- UI polish
- Performance optimizations (non-critical)
- Advanced features for power users

**P3 - Low (Future Consideration):**
- Experimental features
- Edge case handling
- Integrations with niche platforms

**Prioritization Criteria:**
1. User impact (how many users benefit?)
2. Effort required (development time)
3. Dependencies (what must be done first?)
4. Risk (technical complexity, unknowns)
5. Strategic value (competitive advantage)

---

## 2. PHASE B: USER PROFILES & MULTI-ENTITY SUPPORT

**Priority:** P1 (High)
**Estimated Effort:** 2-3 weeks
**Dependencies:** Phase A complete ✅
**Target Users:** Organizations managing contracts for multiple entities/subsidiaries

---

### 2.1 Business Case

**Problem:**
Currently, every contract upload requires manual entry of position, leverage, and business context. For users managing multiple entities (e.g., holding company with 5 subsidiaries), this becomes repetitive and error-prone.

**Solution:**
User profiles that pre-configure defaults for each business entity, with AI suggestions biased toward profile settings while maintaining full override capability.

**Benefits:**
- **60% faster uploads** for repeat scenarios
- **Consistency** across similar contracts
- **Multi-entity support** without system complexity
- **Audit trail** showing which profile was used
- **Quick switching** between company perspectives

---

### 2.2 Database Schema

```sql
-- New table: user_profiles
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT NOT NULL,
    company_name TEXT NOT NULL,
    company_type TEXT,  -- Vendor, Customer, Service Provider, etc.
    default_position TEXT NOT NULL,
    default_leverage TEXT NOT NULL,  -- Strong, Balanced, Weak
    business_context_template TEXT,
    industry TEXT,
    jurisdiction_preference TEXT,
    risk_tolerance TEXT,  -- Conservative, Moderate, Aggressive
    active INTEGER DEFAULT 0,  -- Only one active at a time
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    metadata_json TEXT  -- Additional profile settings as JSON
);

-- Index for performance
CREATE INDEX idx_profiles_active ON user_profiles(active);
CREATE INDEX idx_profiles_company ON user_profiles(company_name);

-- Add to contracts table
ALTER TABLE contracts ADD COLUMN profile_id INTEGER;
ALTER TABLE contracts ADD COLUMN profile_name TEXT;  -- Snapshot for audit

-- Foreign key (optional, for referential integrity)
-- ALTER TABLE contracts ADD FOREIGN KEY (profile_id) REFERENCES user_profiles(id);
```

---

### 2.3 Workflow Description

#### Profile Management Workflow

**Create Profile:**
1. Navigate to Settings → Profiles
2. Click "Create New Profile"
3. Form fields:
   - Profile Name (e.g., "Acme Corp - Vendor Perspective")
   - Company Name
   - Company Type (dropdown)
   - Default Position (dropdown)
   - Default Leverage (radio: Strong/Balanced/Weak)
   - Business Context Template (text area with placeholders)
   - Industry (dropdown)
   - Jurisdiction Preference (text)
   - Risk Tolerance (radio)
4. Save profile
5. Optionally set as active

**Switch Active Profile:**
1. Settings → Profiles
2. View list of profiles with current active highlighted
3. Click "Set Active" on desired profile
4. Confirmation toast: "Active profile changed to [Name]"

**Upload with Active Profile:**
1. Upload file (Stage 1)
2. AI extraction runs normally
3. **NEW:** AI context suggestions biased by active profile:
   - Default position pre-selected
   - Default leverage pre-selected
   - Business context template merged with AI narrative
4. User can still override any field
5. Profile info saved with contract for audit trail

---

### 2.4 UI Mockups (Text-Based)

#### Settings Page - Profile Management

```
┌──────────────────────────────────────────────────────────────┐
│ ⚙️ Settings                                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 👤 User Profiles                    [+ Create New Profile]  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ Acme Corp - Vendor Perspective         [Active]     │ │
│ │    Company: Acme Corporation                           │ │
│ │    Position: Vendor | Leverage: Balanced               │ │
│ │    Last Used: 2025-11-20 | Usage: 42 contracts         │ │
│ │    [Edit] [Duplicate] [Delete]                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │    Acme Corp - Customer Perspective                    │ │
│ │    Company: Acme Corporation                           │ │
│ │    Position: Customer | Leverage: Strong               │ │
│ │    Last Used: 2025-11-15 | Usage: 18 contracts         │ │
│ │    [Edit] [Set Active] [Duplicate] [Delete]            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │    Beta Industries - Landlord Perspective              │ │
│ │    Company: Beta Industries LLC                        │ │
│ │    Position: Landlord | Leverage: Strong               │ │
│ │    Last Used: 2025-10-05 | Usage: 7 contracts          │ │
│ │    [Edit] [Set Active] [Duplicate] [Delete]            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### Upload Page - Profile Indicator

```
┌──────────────────────────────────────────────────────────────┐
│ 📤 Enhanced Contract Upload                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Active Profile: ✅ Acme Corp - Vendor Perspective            │
│                    [Switch Profile]                          │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │   Drag and drop contract file here                     │ │
│ │              or click to browse                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### Stage 3 - Context with Profile Bias

```
┌──────────────────────────────────────────────────────────────┐
│ 💡 Stage 3: Confirm Business Context                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ℹ️  AI suggestions biased by active profile:                │
│    "Acme Corp - Vendor Perspective"                          │
│                                                              │
│ Our Position in this Contract: [Vendor ▼]                   │
│    (Profile default: Vendor)                                 │
│                                                              │
│ Business Leverage Assessment:                                │
│    ⚫ Strong  ⚫ Balanced  ⚪ Weak                            │
│    (Profile default: Balanced)                               │
│                                                              │
│ Business Context Summary:                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ As a vendor, Acme Corporation is providing software    │ │
│ │ services under this MSA. Key obligations include...    │ │
│ │ (Profile template + AI analysis)                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ AI Confidence: 85%                                           │
│                                                              │
│ [✅ Confirm Context]  [← Back to Metadata]                  │
└──────────────────────────────────────────────────────────────┘
```

---

### 2.5 Implementation Specifications

#### Backend Changes

**New API Endpoints:**
```python
# Profile Management
POST   /api/profiles                  # Create new profile
GET    /api/profiles                  # List all profiles
GET    /api/profiles/<id>             # Get profile details
PUT    /api/profiles/<id>             # Update profile
DELETE /api/profiles/<id>             # Delete profile
POST   /api/profiles/<id>/activate    # Set as active profile
GET    /api/profiles/active           # Get currently active profile
```

**Orchestrator Changes:**
```python
# In orchestrator.py, update suggest_context():
def suggest_context(
    self,
    file_path: str,
    metadata: Dict,
    active_profile: Optional[Dict] = None  # NEW parameter
) -> Dict:
    """
    Suggest business context with optional profile bias

    If active_profile provided:
    - Include profile defaults in Claude prompt
    - Bias AI toward profile settings
    - Merge business_context_template with AI narrative
    """

    # Enhance prompt with profile context
    if active_profile:
        context_prompt += f"""

        USER PROFILE CONTEXT:
        Company: {active_profile['company_name']}
        Typical Position: {active_profile['default_position']}
        Typical Leverage: {active_profile['default_leverage']}
        Business Template: {active_profile['business_context_template']}

        Bias your suggestions toward this profile while remaining accurate
        to the actual contract terms.
        """
```

**Upload Endpoint Changes:**
```python
# In api.py, update upload endpoint:
@app.route('/api/upload', methods=['POST'])
def upload_contract():
    # ... existing code ...

    # Get active profile
    active_profile = get_active_profile()  # New helper function

    # Pass profile to context suggestion
    suggested_context = orchestrator.suggest_context(
        str(file_path),
        detected_metadata,
        active_profile=active_profile
    )

    # Include profile info in response
    return jsonify({
        # ... existing fields ...
        'active_profile': active_profile,
        'suggested_context': suggested_context
    })
```

#### Frontend Changes

**New Page: Settings**
```python
# frontend/pages/6_⚙️_Settings.py

import streamlit as st
import requests

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")

# Profile Management
st.markdown("### 👤 User Profiles")

# Fetch profiles
response = requests.get(f"{API_BASE_URL}/api/profiles")
profiles = response.json()

# Create new profile button
if st.button("+ Create New Profile"):
    st.session_state.show_profile_form = True

# Profile form (modal-style)
if st.session_state.get('show_profile_form'):
    with st.form("new_profile_form"):
        profile_name = st.text_input("Profile Name")
        company_name = st.text_input("Company Name")
        # ... more fields ...

        submitted = st.form_submit_button("Create Profile")
        if submitted:
            # POST to /api/profiles
            # Refresh list
            pass

# Display existing profiles
for profile in profiles:
    with st.expander(f"{'✅' if profile['active'] else '  '} {profile['profile_name']}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Company:** {profile['company_name']}")
            st.write(f"**Position:** {profile['default_position']}")
        with col2:
            st.write(f"**Leverage:** {profile['default_leverage']}")
            st.write(f"**Usage:** {profile['usage_count']} contracts")

        # Actions
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if not profile['active'] and st.button("Set Active", key=f"activate_{profile['id']}"):
                # POST to /api/profiles/<id>/activate
                st.rerun()
```

**Upload Page Updates:**
```python
# In frontend/pages/1_📤_Upload.py

# At top of page, show active profile
try:
    profile_response = requests.get(f"{API_BASE_URL}/api/profiles/active")
    if profile_response.status_code == 200:
        active_profile = profile_response.json()
        st.info(f"Active Profile: ✅ {active_profile['profile_name']}")

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Switch Profile"):
                st.switch_page("pages/6_⚙️_Settings.py")
except:
    st.caption("No active profile - using default AI analysis")
```

---

### 2.6 Success Criteria

**Functional Requirements:**
- [ ] User can create/edit/delete profiles
- [ ] Only one profile can be active at a time
- [ ] Active profile auto-populates context suggestions
- [ ] User can override profile defaults
- [ ] Profile info saved with contract for audit
- [ ] Switch profile workflow takes <5 seconds

**Performance Requirements:**
- [ ] Profile list loads in <500ms
- [ ] Profile activation instant (<100ms)
- [ ] No impact on upload speed (still 30-60s)

**User Experience:**
- [ ] Profile indicator visible on upload page
- [ ] One-click profile switching
- [ ] Profile usage statistics accurate
- [ ] Clear visual distinction between active/inactive

---

### 2.7 Testing Plan

**Unit Tests:**
- Profile CRUD operations
- Active profile enforcement (only one)
- Profile bias in AI suggestions
- Audit trail (profile_name snapshot)

**Integration Tests:**
- Full upload workflow with active profile
- Profile switch mid-workflow
- Override profile defaults
- No profile scenario (fallback to pure AI)

**User Acceptance Tests:**
1. Create 3 profiles for different entities
2. Upload 5 contracts using Profile A
3. Switch to Profile B, upload 2 contracts
4. Verify context suggestions differ appropriately
5. Check database: profile_id and profile_name saved
6. Delete Profile B, verify contracts still accessible

---

### 2.8 Rollout Plan

**Phase B.1:** Backend Implementation (Week 1)
- Database schema migration
- API endpoints
- Profile management logic
- Update orchestrator suggest_context()

**Phase B.2:** Frontend Implementation (Week 2)
- Settings page with profile management
- Upload page profile indicator
- Profile switching workflow
- Context form profile bias display

**Phase B.3:** Testing & Refinement (Week 3)
- Unit tests
- Integration tests
- User acceptance testing
- Bug fixes and polish

**Phase B.4:** Documentation & Deployment
- User guide: "Managing Profiles"
- Migration guide for existing contracts
- Release notes
- Deploy to production

---

## 3. PHASE C: ADVANCED SEARCH & FILTERING

**Priority:** P1 (High)
**Estimated Effort:** 3-4 weeks
**Dependencies:** Phase A complete ✅
**Target Users:** All users managing >20 contracts

---

### 3.1 Business Case

**Problem:**
Current system only shows "Recent Uploads" list with no search or filter capabilities. Users managing 50+ contracts cannot efficiently find specific contracts, leading to:
- Re-uploading duplicates
- Unable to find prior versions
- No way to analyze contracts by category/party/date

**Solution:**
Comprehensive search and filtering system with:
- Full-text search across contract content
- Metadata filters (type, parties, dates, risk level)
- Saved searches
- Tag system for custom categorization
- Export search results

**Benefits:**
- **90% reduction** in time to find specific contract
- **Prevent duplicates** through better search
- **Category analysis** (e.g., "all NDAs with critical risk")
- **Relationship mapping** (all contracts with specific party)

---

### 3.2 Search Capabilities

#### 3.2.1 Full-Text Search

**Implementation: PostgreSQL Full-Text Search or SQLite FTS5**

```sql
-- SQLite FTS5 Virtual Table
CREATE VIRTUAL TABLE contracts_fts USING fts5(
    contract_id,
    filename,
    content,
    parties,
    contract_type,
    tokenize = 'porter unicode61'
);

-- Populate from contracts table
INSERT INTO contracts_fts
SELECT id, filename, content_text, parties, contract_type
FROM contracts;

-- Search query
SELECT c.*
FROM contracts c
JOIN contracts_fts fts ON c.id = fts.contract_id
WHERE contracts_fts MATCH 'liability AND indemnification'
ORDER BY rank;
```

**Features:**
- Boolean operators (AND, OR, NOT)
- Phrase search ("unlimited liability")
- Wildcard search (liab*)
- Proximity search (near/5)
- Ranking by relevance

---

#### 3.2.2 Metadata Filters

**Filter Categories:**

**Contract Type:**
- Multi-select: MSA, NDA, SOW, Purchase Order, Service Agreement, etc.
- "Select All" / "Clear All" options

**Parties:**
- Autocomplete text input with suggestions from all known parties
- Multi-party filter (contracts involving both Party A AND Party B)

**Date Ranges:**
- Upload Date: From [date] To [date]
- Effective Date: From [date] To [date]
- Expiration Date: From [date] To [date]
- Custom: "Uploaded in last 30 days", "Expiring in next 90 days"

**Risk Assessment:**
- Overall Risk: High, Medium, Low
- Has Dealbreakers: Yes/No
- Critical Items: Min [0] Max [10]
- Confidence Score: Min [0%] Max [100%]

**Version Status:**
- Latest Version Only: ✓/✗
- Has Child Versions: Yes/No
- Parent Contract ID: [input]

**Status:**
- Pending Confirmation
- Ready for Analysis
- Analyzed
- Archived

**Position & Leverage:**
- Position: Vendor, Customer, etc.
- Leverage: Strong, Balanced, Weak

**Profile (if Phase B implemented):**
- Filter by profile used

---

#### 3.2.3 Tag System

**Purpose:** User-defined categorization orthogonal to contract metadata

**Use Cases:**
- Project tags: "Project Apollo", "Q4 2025 Initiative"
- Department tags: "Legal", "Procurement", "Sales"
- Priority tags: "High Priority", "Pending Renewal"
- Custom categories: "Audit Required", "Board Approved"

**Database Schema:**
```sql
-- Tags table
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE,
    tag_color TEXT,  -- Hex color for UI display
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Contract-Tag mapping (many-to-many)
CREATE TABLE contract_tags (
    contract_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT,
    PRIMARY KEY (contract_id, tag_id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_contract_tags_contract ON contract_tags(contract_id);
CREATE INDEX idx_contract_tags_tag ON contract_tags(tag_id);
```

**Tag Operations:**
- Create tag with color
- Assign multiple tags to contract
- Remove tag from contract
- Delete tag (removes from all contracts)
- Rename tag
- Merge tags

---

#### 3.2.4 Saved Searches

**Database Schema:**
```sql
CREATE TABLE saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_name TEXT NOT NULL,
    search_criteria JSON NOT NULL,  -- Serialized filter state
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    is_favorite INTEGER DEFAULT 0
);
```

**Features:**
- Save current filter state with name
- Quick-load saved searches
- Edit saved search
- Favorite searches (shown at top)
- Share search (export/import JSON)

**Examples:**
- "High Risk NDAs"
  - Contract Type: NDA
  - Overall Risk: High
  - Status: Analyzed

- "Acme Corp Contracts"
  - Parties: Contains "Acme"
  - All time

- "Pending Renewal (Next 90 Days)"
  - Expiration Date: Next 90 days
  - Status: Analyzed

---

### 3.3 UI Mockup - Search Page

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🔍 Search & Filter Contracts                                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ 🔎 [Search: liability indemnification          ] [Search]  [Clear]   │
│                                                                        │
│ ⭐ Saved Searches: [High Risk NDAs ▼] [Acme Corp Contracts]          │
│                                                                        │
│ ┌─ Filters ──────────────────────────────────────────────────────┐  │
│ │ Contract Type: [MSA] [NDA] [SOW] [+ More...]                   │  │
│ │                                                                  │  │
│ │ Parties: [Acme Corporation         ] [+ Add]                    │  │
│ │                                                                  │  │
│ │ Date Range:                                                      │  │
│ │   Upload Date:  [2025-01-01] to [2025-11-22]                   │  │
│ │   Expires:      [▼ Expiring in next 90 days]                   │  │
│ │                                                                  │  │
│ │ Risk Level: ☑ High  ☑ Medium  ☐ Low                            │  │
│ │                                                                  │  │
│ │ Status: ☑ Analyzed  ☐ Pending  ☐ Archived                      │  │
│ │                                                                  │  │
│ │ Tags: [Legal] [Q4-2025] [+ Add tag filter]                     │  │
│ │                                                                  │  │
│ │ [Apply Filters]  [Clear All]  [Save Search...]                 │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│ Results: 24 contracts found   [Export CSV] [Export Excel]            │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────┐  │
│ │ ✓ | ID  | Filename              | Type | Party      | Risk ... │  │
│ ├────────────────────────────────────────────────────────────────┤  │
│ │ ☐ | 143 | Acme_MSA_v2.docx     | MSA  | Acme Corp  | 🔴 High │  │
│ │   |     | Tags: [Legal] [Q4-2025]                             │  │
│ │   |     | Uploaded: 2025-11-20 | Dealbreakers: 2              │  │
│ │   |     | [View] [Analyze] [Compare] [Add Tags]               │  │
│ ├────────────────────────────────────────────────────────────────┤  │
│ │ ☐ | 128 | Acme_NDA.docx        | NDA  | Acme Corp  | 🟡 Med  │  │
│ │   |     | Tags: [Legal]                                       │  │
│ │   |     | Uploaded: 2025-11-15 | Dealbreakers: 0              │  │
│ │   |     | [View] [Analyze] [Compare] [Add Tags]               │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│ [Bulk Actions ▼] [Select All] [Select None]                          │
│   - Add Tags to Selected                                              │
│   - Export Selected                                                   │
│   - Archive Selected                                                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3.4 Implementation Plan

**Week 1: Database & Backend**
- Implement FTS5 full-text search
- Create tags tables
- Create saved_searches table
- API endpoints for search, filters, tags

**Week 2: Search API**
- Complex query builder
- Filter combination logic
- Saved search CRUD
- Tag management API

**Week 3: Frontend**
- Search page UI
- Filter panel
- Tag management interface
- Results grid with pagination

**Week 4: Testing & Polish**
- Performance testing (search <1s for 1000 contracts)
- UI refinement
- Saved search export/import
- Documentation

---

### 3.5 Success Criteria

**Performance:**
- [ ] Full-text search completes in <1 second for 10,000 contracts
- [ ] Filter application <500ms
- [ ] Tag assignment instant (<100ms)

**Functionality:**
- [ ] All filter combinations work correctly
- [ ] Saved searches persist across sessions
- [ ] Tag colors display consistently
- [ ] Export includes all filtered results

**User Experience:**
- [ ] Filter panel collapsible to save screen space
- [ ] Search suggestions as user types
- [ ] Results sortable by any column
- [ ] Keyboard shortcuts (Ctrl+F for search)

---

## 4. PHASE D: CLAUSE LIBRARY SYSTEM

**Priority:** P1 (High)
**Estimated Effort:** 4-5 weeks
**Dependencies:** Phase C (tags system)
**Target Users:** Legal teams building institutional knowledge

---

### 4.1 Business Case

**Problem:**
After negotiating better contract terms, there's no systematic way to:
- Extract successful clause language
- Store in reusable library
- Track which clauses succeed in negotiations
- Insert library clauses into new contracts

**Solution:**
Comprehensive clause library system that:
- Extracts clauses from analyzed contracts
- Categorizes and tags clauses
- Tracks negotiation success rates
- Provides template insertion during upload/edit
- Shows pattern evolution over time

**Benefits:**
- **Build institutional knowledge** from past negotiations
- **Accelerate future negotiations** with proven language
- **Measure negotiation effectiveness** via success tracking
- **Onboard new team members** faster with clause library

---

### 4.2 Database Schema

```sql
-- Clause library table
CREATE TABLE clause_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clause_name TEXT NOT NULL,
    clause_category TEXT NOT NULL,  -- liability, IP, termination, etc.
    clause_subcategory TEXT,
    clause_text TEXT NOT NULL,
    alternate_text TEXT,  -- Alternative wording
    clause_rationale TEXT,  -- Why this clause is preferred

    -- Source information
    source_contract_id INTEGER,
    source_section_number TEXT,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Success tracking
    times_used INTEGER DEFAULT 0,
    times_accepted INTEGER DEFAULT 0,  -- Accepted without modification
    times_modified INTEGER DEFAULT 0,  -- Accepted with changes
    times_rejected INTEGER DEFAULT 0,  -- Not accepted
    success_rate REAL,  -- Calculated: (accepted + modified) / times_used

    -- Effectiveness metrics
    avg_negotiation_rounds REAL,  -- How many rounds to acceptance
    risk_reduction_score REAL,  -- Estimated risk reduction vs standard

    -- Metadata
    applicable_contract_types TEXT,  -- JSON array: ["MSA", "SOW"]
    applicable_positions TEXT,  -- JSON array: ["Vendor", "Service Provider"]
    jurisdiction_specific TEXT,  -- If only for certain jurisdictions
    industry_specific TEXT,  -- If industry-dependent

    -- Version control
    version_number INTEGER DEFAULT 1,
    parent_clause_id INTEGER,  -- Links to previous version
    is_active INTEGER DEFAULT 1,
    deprecated_date TIMESTAMP,
    deprecated_reason TEXT,

    -- Tags and classification
    tags TEXT,  -- JSON array
    risk_level TEXT,  -- How aggressive/defensive this clause is

    -- User management
    created_by TEXT,
    last_modified_date TIMESTAMP,
    last_modified_by TEXT,

    FOREIGN KEY (source_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (parent_clause_id) REFERENCES clause_library(id)
);

-- Clause usage tracking
CREATE TABLE clause_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clause_id INTEGER NOT NULL,
    contract_id INTEGER NOT NULL,
    usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_context TEXT,  -- "template_insertion", "manual_reference", "comparison"
    negotiation_outcome TEXT,  -- "accepted", "modified", "rejected", "pending"
    modification_notes TEXT,  -- What changes were made
    negotiation_rounds INTEGER,

    FOREIGN KEY (clause_id) REFERENCES clause_library(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- Clause relationships (for clause patterns)
CREATE TABLE clause_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clause_id_1 INTEGER NOT NULL,
    clause_id_2 INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,  -- "depends_on", "conflicts_with", "enhances"
    relationship_strength REAL,  -- 0.0 to 1.0
    notes TEXT,

    FOREIGN KEY (clause_id_1) REFERENCES clause_library(id),
    FOREIGN KEY (clause_id_2) REFERENCES clause_library(id)
);

-- Indexes
CREATE INDEX idx_clause_category ON clause_library(clause_category);
CREATE INDEX idx_clause_active ON clause_library(is_active);
CREATE INDEX idx_clause_source ON clause_library(source_contract_id);
CREATE INDEX idx_usage_clause ON clause_usage(clause_id);
CREATE INDEX idx_usage_contract ON clause_usage(contract_id);
```

---

### 4.3 Clause Extraction Workflow

#### 4.3.1 Automated Extraction (After Analysis)

**Trigger:** After risk assessment completes

**Process:**
1. Identify high-value sections from risk assessment
   - Sections with high confidence scores
   - Sections that mitigated risks
   - Dealbreaker resolutions

2. Prompt user: "Extract clauses to library?"

3. Display extraction candidates:
   ```
   ┌─────────────────────────────────────────┐
   │ 📚 Extract Clauses to Library?          │
   ├─────────────────────────────────────────┤
   │                                         │
   │ The following sections may be useful    │
   │ for future contracts:                   │
   │                                         │
   │ ☑ Section 7.2: Limitation of Liability │
   │   "Vendor's total liability shall not   │
   │   exceed..."                            │
   │   Category: Liability                   │
   │   Risk Level: Critical                  │
   │                                         │
   │ ☑ Section 9.1: IP Ownership             │
   │   "All intellectual property developed  │
   │   under this agreement..."              │
   │   Category: IP                          │
   │   Risk Level: Critical                  │
   │                                         │
   │ ☐ Section 12.3: Termination for Cause  │
   │   "Either party may terminate..."       │
   │   Category: Termination                 │
   │   Risk Level: Important                 │
   │                                         │
   │ [Extract Selected]  [Extract All]       │
   │ [Skip]                                  │
   └─────────────────────────────────────────┘
   ```

4. For each selected clause:
   - Pre-populate metadata from contract analysis
   - User reviews and edits
   - Save to clause_library

---

#### 4.3.2 Manual Extraction

**From Contract View:**
1. User highlights text in contract viewer
2. Right-click → "Extract to Clause Library"
3. Form appears:
   ```
   ┌─────────────────────────────────────────┐
   │ 📚 Add to Clause Library                │
   ├─────────────────────────────────────────┤
   │ Clause Name: [Liability Cap           ] │
   │ Category: [Liability            ▼]      │
   │ Subcategory: [Limitation         ▼]     │
   │                                         │
   │ Clause Text:                            │
   │ ┌───────────────────────────────────┐  │
   │ │ Vendor's total liability under    │  │
   │ │ this Agreement shall not exceed   │  │
   │ │ the fees paid in the 12 months    │  │
   │ │ preceding the claim.              │  │
   │ └───────────────────────────────────┘  │
   │                                         │
   │ Rationale:                              │
   │ ┌───────────────────────────────────┐  │
   │ │ Standard 12-month cap, typical    │  │
   │ │ for SaaS vendor contracts         │  │
   │ └───────────────────────────────────┘  │
   │                                         │
   │ Applicable to:                          │
   │ Contract Types: [MSA] [Service Agree]  │
   │ Position: [Vendor]                     │
   │                                         │
   │ Tags: [Add tag...]                     │
   │                                         │
   │ [Save to Library]  [Cancel]            │
   └─────────────────────────────────────────┘
   ```

---

### 4.4 Clause Library Interface

```
┌──────────────────────────────────────────────────────────────────┐
│ 📚 Clause Library                                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 🔍 [Search clauses...                    ] [+ Add New Clause]  │
│                                                                  │
│ Filters: Category [All ▼] | Position [All ▼] | Type [All ▼]   │
│          Show: ⚫ Active Only  ⚪ Include Deprecated             │
│                                                                  │
│ Sort by: [Success Rate ▼]  View: [Grid] [List]                 │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ 📄 Limitation of Liability - 12 Month Cap                  │ │
│ │ Category: Liability > Limitation                            │ │
│ │                                                             │ │
│ │ Success Rate: ⭐⭐⭐⭐⭐ 85% (17/20)                          │ │
│ │ Used: 20 times | Avg Rounds: 1.5 | Risk Reduction: High   │ │
│ │                                                             │ │
│ │ "Vendor's total liability under this Agreement shall not   │ │
│ │ exceed the fees paid in the 12 months preceding the claim."│ │
│ │                                                             │ │
│ │ Applicable: MSA, Service Agreement | Position: Vendor      │ │
│ │ Tags: [SaaS] [Standard] [Low-Risk]                        │ │
│ │                                                             │ │
│ │ [Use in Contract] [View History] [Edit] [Duplicate] [...] │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ 📄 IP Ownership - Work for Hire                            │ │
│ │ Category: Intellectual Property > Ownership                 │ │
│ │                                                             │ │
│ │ Success Rate: ⭐⭐⭐⭐☆ 73% (11/15)                          │ │
│ │ Used: 15 times | Avg Rounds: 2.1 | Risk Reduction: Medium │ │
│ │                                                             │ │
│ │ "All work product created under this Agreement shall be    │ │
│ │ considered a 'work made for hire' and shall be the         │ │
│ │ exclusive property of Customer."                           │ │
│ │                                                             │ │
│ │ Applicable: SOW, Service Agreement | Position: Customer    │ │
│ │ Tags: [IP] [Work-for-Hire] [Aggressive]                   │ │
│ │                                                             │ │
│ │ [Use in Contract] [View History] [Edit] [Duplicate] [...] │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 4.5 Template Insertion During Upload

**Enhanced Stage 2 - Metadata Confirmation:**

After AI extracts metadata, show relevant clauses:

```
┌──────────────────────────────────────────────────────────────────┐
│ 📋 Stage 2: Confirm Metadata                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Contract Type: [MSA ▼]                                          │
│ Position: [Vendor ▼]                                            │
│ ...                                                              │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ 💡 Suggested Clauses from Library                          │ │
│ ├────────────────────────────────────────────────────────────┤ │
│ │ Based on contract type (MSA) and position (Vendor),        │ │
│ │ these library clauses may be relevant:                     │ │
│ │                                                             │ │
│ │ ☐ Limitation of Liability - 12 Month Cap                  │ │
│ │   Success Rate: 85% | Used in 20 similar contracts        │ │
│ │   [Preview] [Add to Contract]                              │ │
│ │                                                             │ │
│ │ ☐ Indemnification - Mutual Limited                        │ │
│ │   Success Rate: 78% | Used in 14 similar contracts        │ │
│ │   [Preview] [Add to Contract]                              │ │
│ │                                                             │ │
│ │ [View All Library Clauses]                                 │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [✅ Confirm Metadata]  [← Back]                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

### 4.6 Success Rate Tracking

**Workflow:**

1. **Clause Inserted:**
   ```python
   clause_usage.insert({
       'clause_id': 123,
       'contract_id': 456,
       'usage_date': now(),
       'usage_context': 'template_insertion',
       'negotiation_outcome': 'pending'
   })
   ```

2. **After Negotiation (User Updates):**

   Contract detail page shows:
   ```
   ┌─────────────────────────────────────────┐
   │ 📊 Clause Usage Tracking                │
   ├─────────────────────────────────────────┤
   │ This contract used 3 library clauses:   │
   │                                         │
   │ • Limitation of Liability               │
   │   Outcome: [Accepted ▼]                │
   │   Rounds: [2]                           │
   │                                         │
   │ • Indemnification                       │
   │   Outcome: [Modified ▼]                │
   │   Rounds: [3]                           │
   │   Notes: [Changed cap amount]          │
   │                                         │
   │ • Termination for Convenience           │
   │   Outcome: [Rejected ▼]                │
   │   Rounds: [4]                           │
   │   Notes: [Customer required 30-day]    │
   │                                         │
   │ [Save Outcomes]                         │
   └─────────────────────────────────────────┘
   ```

3. **Success Rate Calculation:**
   ```python
   def update_clause_success_rate(clause_id):
       usages = clause_usage.filter(clause_id=clause_id, outcome!='pending')

       accepted = usages.filter(outcome='accepted').count()
       modified = usages.filter(outcome='modified').count()
       rejected = usages.filter(outcome='rejected').count()

       total = accepted + modified + rejected
       success_rate = (accepted + modified) / total if total > 0 else 0

       avg_rounds = usages.avg('negotiation_rounds')

       clause_library.update({
           'times_used': total,
           'times_accepted': accepted,
           'times_modified': modified,
           'times_rejected': rejected,
           'success_rate': success_rate,
           'avg_negotiation_rounds': avg_rounds
       })
   ```

---

### 4.7 Pattern Evolution Analysis

**Clause Version History:**

Track how successful clauses evolve over time:

```
┌──────────────────────────────────────────────────────────────────┐
│ 📊 Clause Evolution: Limitation of Liability                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Version Timeline:                                                │
│                                                                  │
│ v1 (2023-01-15) ───────> v2 (2024-06-20) ───────> v3 (Current) │
│ Success: 45%              Success: 68%              Success: 85% │
│ 6-month cap               12-month cap              12-month cap │
│                           + carve-outs              + IP exception│
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Version 1 (Deprecated 2024-06-20)                          │ │
│ │ "Liability limited to 6 months fees"                       │ │
│ │ Outcome: 45% success (9/20)                                │ │
│ │ Why deprecated: Too aggressive, frequently rejected        │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Version 2 (Deprecated 2025-11-10)                          │ │
│ │ "Liability limited to 12 months fees, except for IP..."    │ │
│ │ Outcome: 68% success (17/25)                               │ │
│ │ Why deprecated: Needed IP exception carve-out              │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Version 3 (Current)                                        │ │
│ │ "Liability limited to 12 months fees, except for IP        │ │
│ │ breach and confidentiality violations"                     │ │
│ │ Outcome: 85% success (17/20)                               │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Success Trend: 📈 Improving (↑ 40 pp over 2 years)              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 4.8 Implementation Milestones

**Week 1:** Database & Basic CRUD
- Clause library schema
- Clause usage tracking
- API endpoints (create, read, update, delete, search)

**Week 2:** Extraction Workflows
- Automated extraction after analysis
- Manual extraction from contract view
- Metadata auto-population

**Week 3:** Library Interface
- Clause library browse/search page
- Clause detail view
- Success rate display
- Filtering and sorting

**Week 4:** Template Insertion
- Suggested clauses during upload
- Insert clause into contract
- Usage tracking on insertion

**Week 5:** Success Tracking & Analytics
- Outcome tracking UI
- Success rate calculations
- Version evolution analysis
- Pattern reports

---

### 4.9 Success Criteria

**Functional:**
- [ ] Extract clauses from any analyzed contract
- [ ] Library searchable by category, tags, success rate
- [ ] Suggested clauses appear during upload
- [ ] Success rates update based on outcomes
- [ ] Clause versioning tracks improvements

**User Experience:**
- [ ] Extraction flow takes <1 minute
- [ ] Library search <500ms
- [ ] Clause preview loads instantly
- [ ] Success metrics clearly visualized

**Business Value:**
- [ ] >50% of uploaded contracts use library clauses
- [ ] Demonstrated success rate improvement over time
- [ ] Negotiation round reduction measurable

---

## 5. PHASE E: REMAINING WORKFLOWS

**Priority:** P2 (Medium)
**Estimated Effort:** 6-8 weeks total
**Dependencies:** Phases A-D

---

### 5.1 Negotiate Workflow

**Purpose:** AI-powered negotiation strategy generation

**Current Gap:** After analysis, users get risk findings but no negotiation guidance.

**Proposed Solution:**

**Negotiation Strategy Generator:**

1. Input: Risk assessment + user priorities
2. AI Analysis:
   - Identify negotiation opportunities
   - Generate position statements
   - Suggest fallback positions
   - Estimate success probability

3. Output: Negotiation playbook

**UI Mockup:**
```
┌──────────────────────────────────────────────────────────────────┐
│ 🤝 Negotiation Strategy                                          │
├──────────────────────────────────────────────────────────────────┤
│ Contract: Acme_MSA_v2.docx                                       │
│ Overall Risk: HIGH | Dealbreakers: 2 | Critical: 4              │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ 🎯 Your Negotiation Priorities                             │ │
│ │ Rank these items (drag to reorder):                        │ │
│ │                                                             │ │
│ │ 1. ☰ Unlimited Liability (Dealbreaker)                    │ │
│ │ 2. ☰ IP Ownership Ambiguity (Dealbreaker)                 │ │
│ │ 3. ☰ Indemnification Scope (Critical)                     │ │
│ │ 4. ☰ Termination Notice Period (Critical)                 │ │
│ │ ...                                                         │ │
│ │                                                             │ │
│ │ [Generate Strategy]                                         │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ── Generated Strategy ────────────────────────────────────────  │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ 📋 Issue #1: Unlimited Liability (Section 7.2)            │ │
│ │                                                             │ │
│ │ Current Language:                                           │ │
│ │ "Vendor shall be liable for all damages..."                │ │
│ │                                                             │ │
│ │ 🎯 Primary Position:                                       │ │
│ │ "Liability limited to 12 months of fees paid"              │ │
│ │ Justification: Industry standard for SaaS vendors          │ │
│ │ Success Probability: 75% (based on similar negotiations)   │ │
│ │                                                             │ │
│ │ 🔄 Fallback Position:                                      │ │
│ │ "Liability limited to 24 months of fees, carve out IP"    │ │
│ │ Justification: More generous cap, shows flexibility        │ │
│ │ Success Probability: 90%                                    │ │
│ │                                                             │ │
│ │ 📚 Library Clauses: [View 3 matching clauses]             │ │
│ │                                                             │ │
│ │ 💬 Position Statement:                                     │ │
│ │ "We propose limiting liability to fees paid in the         │ │
│ │ 12 months preceding any claim. This is consistent with     │ │
│ │ industry standards and provides both parties with          │ │
│ │ reasonable protection while maintaining a sustainable      │ │
│ │ business relationship."                                     │ │
│ │                                                             │ │
│ │ [Mark as Resolved] [Edit Strategy] [Export]                │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [Export Full Playbook (PDF)] [Email to Team]                   │
└──────────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Backend: New `generate_negotiation_strategy()` method
- Prompt engineering: Strategy generation with clause library integration
- Database: `negotiation_strategies` table
- Frontend: New "Negotiate" workflow page

**Estimated Effort:** 2-3 weeks

---

### 5.2 Dashboard (Metrics & Visualizations)

**Purpose:** Executive-level visibility into contract portfolio

**Metrics to Display:**

**Portfolio Overview:**
- Total contracts: Count by status
- Risk distribution: High/Medium/Low pie chart
- Upload trend: Contracts per month (line graph)
- Active dealbreakers: Count with drill-down

**Risk Analytics:**
- Average confidence score over time
- Dealbreaker categories (bar chart)
- Critical items by category
- Top risk parties (which counterparties have highest risk contracts)

**Negotiation Performance:**
- Success rate by clause type
- Average negotiation rounds
- Time to contract finalization
- Clause library ROI (time saved)

**Party Analytics:**
- Most frequent counterparties
- Risk profile by party
- Contract value by party
- Renewal upcoming (next 90 days)

**UI Mockup:**
```
┌──────────────────────────────────────────────────────────────────┐
│ 📊 Dashboard                                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Portfolio Overview                            Date Range: [▼]   │
│                                                                  │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │ Total    │ │ High     │ │ Active   │ │ Pending  │           │
│ │ Contracts│ │ Risk     │ │ Deal-    │ │ Review   │           │
│ │   247    │ │   23     │ │ breakers │ │    12    │           │
│ │   ↑ 12%  │ │   ↓ 8%   │ │    15    │ │   ↑ 3    │           │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│ ┌────────────────────────────┐ ┌──────────────────────────────┐│
│ │  Risk Distribution         │ │  Upload Trend (6 months)     ││
│ │                            │ │                              ││
│ │   🔴 High: 23 (9%)        │ │   60 ┤                  ●   ││
│ │   🟡 Med:  89 (36%)       │ │   50 ┤              ●        ││
│ │   🟢 Low: 135 (55%)       │ │   40 ┤          ●            ││
│ │                            │ │   30 ┤      ●                ││
│ │   [Pie Chart Visual]       │ │   20 ┤  ●                    ││
│ │                            │ │      └──────────────────────││
│ └────────────────────────────┘ │       Jun Jul Aug Sep Oct Nov││
│                                 └──────────────────────────────┘│
│                                                                  │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Top Risk Areas                                            │  │
│ │ ┌───────────────────────────────────────────────────────┐ │  │
│ │ │ Liability       ████████████████████ 45 contracts     │ │  │
│ │ │ Indemnification ██████████████ 32 contracts           │ │  │
│ │ │ IP Ownership    ███████████ 28 contracts              │ │  │
│ │ │ Termination     ████████ 19 contracts                 │ │  │
│ │ │ Payment Terms   █████ 12 contracts                    │ │  │
│ │ └───────────────────────────────────────────────────────┘ │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│ [View Full Analytics] [Export Report] [Schedule Email]         │
└──────────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Backend: Aggregation queries, caching for performance
- Frontend: Chart.js or Plotly for visualizations
- Real-time updates via WebSocket (optional)
- Export to Excel/PDF

**Estimated Effort:** 2-3 weeks

---

### 5.3 Reports (PDF/DOCX Export)

**Purpose:** Generate professional reports for stakeholders

**Report Types:**

**1. Contract Analysis Report**
- Executive summary
- Risk assessment details
- Dealbreakers and critical items
- Recommendations
- Appendix with clause-by-clause analysis

**2. Portfolio Summary Report**
- Contract inventory
- Risk distribution
- Key metrics
- Upcoming renewals
- Trend analysis

**3. Party Profile Report**
- All contracts with specific party
- Risk trends over time
- Financial exposure
- Negotiation history

**4. Comparison Report** (already implemented in Phase A)
- Side-by-side comparison with redlines
- Impact analysis
- Business narratives

**5. Negotiation Playbook Export**
- Strategy for each issue
- Position statements
- Success probabilities
- Library clause references

**Implementation:**
- Backend: python-docx, ReportLab (PDF)
- Templates: Customizable report templates
- Branding: Logo, colors configurable
- Scheduling: Automated weekly/monthly reports

**Estimated Effort:** 1-2 weeks

---

## 6. TECHNICAL ENHANCEMENTS

**Priority:** P1-P2 (varies by feature)
**Estimated Effort:** 8-12 weeks total

---

### 6.1 RAG Integration for Clause Patterns

**Current:** Clause Pattern Library stored as markdown, loaded into memory

**Enhancement:** Vector database for semantic search

**Implementation:**

```python
# Vector store for clause patterns
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# Embed clause patterns on startup
def build_clause_pattern_vectorstore():
    patterns = load_clause_patterns()  # From markdown

    documents = []
    for pattern in patterns:
        doc = {
            'content': pattern['description'],
            'metadata': {
                'pattern_id': pattern['id'],
                'category': pattern['category'],
                'success_rate': pattern['success_rate'],
                'risk_level': pattern['risk_level']
            }
        }
        documents.append(doc)

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(documents, embeddings)

    return vectorstore

# Semantic search during analysis
def find_matching_patterns(clause_text):
    vectorstore = get_clause_vectorstore()

    # Semantic search (not just keyword)
    results = vectorstore.similarity_search(
        clause_text,
        k=5,  # Top 5 matches
        filter={'risk_level': 'CRITICAL'}
    )

    return results
```

**Benefits:**
- Better pattern matching (semantic vs keyword)
- Find similar clauses even with different wording
- Rank by relevance
- Filter by metadata

**Estimated Effort:** 2 weeks

---

### 6.2 Law Library Integration

**Current:** Law library exists as separate tool in `/tools/law_library/`

**Enhancement:** Integrate into analysis workflow

**Use Cases:**

1. **Jurisdiction-Specific Guidance:**
   ```
   Contract: Delaware law governs
   → Automatically load Delaware case law
   → Check clauses against Delaware precedents
   → Flag non-compliant terms
   ```

2. **Regulatory Compliance:**
   ```
   Contract Type: Employment Agreement
   → Load employment law references
   → Check mandatory clauses (at-will, arbitration, etc.)
   → Flag missing required provisions
   ```

3. **Citation Support:**
   ```
   Recommendation: "Consider adding arbitration clause"
   → AI provides: "See Delaware Code Title 6, §2701"
   → Link to full statute text
   ```

**Implementation:**

```python
# In orchestrator.py
from tools.law_library.src.retrieval import LawLibraryRetriever

class ContractAnalyzer:
    def __init__(self, ...):
        # ... existing init ...
        self.law_library = LawLibraryRetriever()

    def analyze_with_legal_context(self, contract_text, jurisdiction):
        # Get relevant legal context
        legal_context = self.law_library.query(
            query=contract_text[:1000],  # Summary
            jurisdiction=jurisdiction,
            contract_type=self.contract_type
        )

        # Include in Claude prompt
        enhanced_prompt = f"""
        {base_prompt}

        LEGAL CONTEXT:
        {legal_context}

        Ensure your analysis aligns with these legal requirements.
        """

        # ... rest of analysis ...
```

**Estimated Effort:** 3 weeks

---

### 6.3 Multi-LLM Orchestration

**Current:** Single model (Claude Sonnet 4) for all tasks

**Enhancement:** Use different models for different tasks

**Rationale:**
- Cost optimization (use cheaper models for simple tasks)
- Latency optimization (use faster models when accuracy less critical)
- Redundancy (fallback if primary model unavailable)
- A/B testing (compare model performance)

**Implementation:**

```python
# Model router based on task
class MultiLLMOrchestrator:
    def __init__(self):
        self.models = {
            'metadata_extraction': 'claude-3-haiku-20240307',  # Fast, cheap
            'context_suggestion': 'claude-sonnet-4-20250514',  # Balanced
            'risk_analysis': 'claude-opus-4-20250514',         # Most capable
            'clause_matching': 'gpt-4-turbo',                  # Alternative
        }

    def route_request(self, task_type, prompt):
        model = self.models.get(task_type, self.models['context_suggestion'])

        # Call appropriate model
        if model.startswith('claude'):
            return self._call_anthropic(model, prompt)
        elif model.startswith('gpt'):
            return self._call_openai(model, prompt)

    def _call_anthropic(self, model, prompt):
        # Anthropic API call
        pass

    def _call_openai(self, model, prompt):
        # OpenAI API call
        pass
```

**Cost Analysis:**
```
Current (all Claude Sonnet 4):
- Metadata extraction: $0.015 per contract
- Context suggestion: $0.020 per contract
- Risk analysis: $0.100 per contract
TOTAL: $0.135 per contract

Optimized (multi-model):
- Metadata extraction (Haiku): $0.001 per contract (-93%)
- Context suggestion (Sonnet): $0.020 per contract (no change)
- Risk analysis (Opus): $0.150 per contract (+50% quality)
TOTAL: $0.171 per contract (+27% cost, +50% quality)

OR cost-optimized:
- Metadata extraction (Haiku): $0.001
- Context suggestion (Haiku): $0.002
- Risk analysis (Sonnet): $0.100
TOTAL: $0.103 per contract (-24% cost)
```

**Estimated Effort:** 2 weeks

---

### 6.4 Performance Optimizations

**Current Bottlenecks:**

1. **Upload workflow: 30-60 seconds**
   - Metadata extraction: ~20s
   - Context suggestion: ~15s
   - Version detection: ~5s
   - Sequential execution

2. **Search: Linear scan for large datasets**
   - No full-text index
   - No query caching
   - No pagination limits

3. **Dashboard: Re-calculates on every load**
   - No aggregation caching
   - No incremental updates

**Optimizations:**

**1. Parallel AI Calls:**
```python
# Current (sequential):
metadata = extract_metadata()       # 20s
context = suggest_context(metadata) # 15s
# Total: 35s

# Optimized (parallel where possible):
import asyncio

async def analyze_contract():
    # Parallel tasks
    metadata_task = extract_metadata()
    version_task = detect_version()  # Independent

    metadata, version_info = await asyncio.gather(
        metadata_task,
        version_task
    )

    # Dependent task (must wait for metadata)
    context = await suggest_context(metadata)

    return metadata, version_info, context

# Time: 20s (metadata) + 15s (context) = 35s
# But version_task runs during metadata_task, so total ~25s
# Savings: ~10 seconds
```

**2. Caching Strategy:**
```python
from functools import lru_cache
import redis

# Redis cache for expensive queries
redis_client = redis.Redis(host='localhost', port=6379)

@lru_cache(maxsize=1000)
def get_contract_statistics(time_range):
    # Check Redis cache first
    cache_key = f"stats:{time_range}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    # Compute if not cached
    stats = compute_statistics(time_range)

    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(stats))

    return stats
```

**3. Database Indexing:**
```sql
-- Full-text search index (if using PostgreSQL)
CREATE INDEX idx_contracts_fts ON contracts
USING GIN(to_tsvector('english', content_text));

-- Composite indexes for common queries
CREATE INDEX idx_contracts_type_status ON contracts(contract_type, status);
CREATE INDEX idx_contracts_party_date ON contracts(parties, upload_date);
CREATE INDEX idx_contracts_risk_date ON contracts(overall_risk, upload_date DESC);

-- Partial indexes for common filters
CREATE INDEX idx_contracts_latest ON contracts(is_latest_version)
WHERE is_latest_version = 1;

CREATE INDEX idx_contracts_dealbreakers ON contracts(id)
WHERE dealbreaker_count > 0;
```

**4. Query Optimization:**
```python
# Current: N+1 query problem
for contract in contracts:
    assessment = get_assessment(contract.id)  # Separate query
    display(contract, assessment)

# Optimized: JOIN
contracts_with_assessments = db.execute("""
    SELECT c.*, ra.*
    FROM contracts c
    LEFT JOIN risk_assessments ra ON c.id = ra.contract_id
    WHERE c.status = 'analyzed'
    ORDER BY c.upload_date DESC
    LIMIT 50
""")
# Single query, much faster
```

**Estimated Effort:** 3 weeks

---

### 6.5 Bulk Operations

**Use Case:** Process 50+ contracts uploaded at once

**Features:**

1. **Batch Upload:**
   ```
   ┌──────────────────────────────────────────┐
   │ 📤 Batch Upload                          │
   ├──────────────────────────────────────────┤
   │ Drop multiple files here                 │
   │                                          │
   │ Files selected: 23                       │
   │                                          │
   │ Apply to all:                            │
   │ Profile: [Acme Vendor ▼]                │
   │                                          │
   │ [Upload All]                             │
   │                                          │
   │ Progress: ████████░░ 18/23 (78%)        │
   │                                          │
   │ ✓ contract_001.docx - Complete          │
   │ ✓ contract_002.docx - Complete          │
   │ ⏳ contract_003.docx - Analyzing...     │
   │ ⏸️ contract_004.docx - Queued           │
   └──────────────────────────────────────────┘
   ```

2. **Batch Analysis:**
   - Queue system (Celery + Redis)
   - Progress tracking
   - Email notification when complete
   - Error handling (retry failed, skip corrupted)

3. **Bulk Tag Assignment:**
   - Select multiple contracts
   - Apply tags to all selected
   - Bulk metadata updates

4. **Bulk Export:**
   - Export all filtered contracts
   - Generate combined report
   - ZIP download with all files

**Implementation:**
```python
# Task queue with Celery
from celery import Celery

app = Celery('cip', broker='redis://localhost:6379')

@app.task(bind=True)
def analyze_contract_async(self, contract_id):
    """Async task for contract analysis"""
    try:
        # Update progress
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing...'})

        # Run analysis
        result = orchestrator.analyze_contract_file(contract_id)

        return {'status': 'Complete', 'result': result}

    except Exception as e:
        # Retry up to 3 times
        raise self.retry(exc=e, countdown=60, max_retries=3)

# API endpoint
@app.route('/api/batch/upload', methods=['POST'])
def batch_upload():
    files = request.files.getlist('files')
    profile_id = request.form.get('profile_id')

    # Create batch
    batch_id = create_batch()

    # Queue all uploads
    for file in files:
        contract_id = save_contract(file, profile_id)
        analyze_contract_async.delay(contract_id)

    return jsonify({'batch_id': batch_id, 'count': len(files)})
```

**Estimated Effort:** 3 weeks

---

## 7. UI/UX IMPROVEMENTS

**Priority:** P2 (Medium)
**Estimated Effort:** 4-6 weeks total

---

### 7.1 Keyboard Shortcuts

**Power User Feature:** Accelerate common actions

**Shortcuts:**

```
Global:
Ctrl/Cmd + K     : Command palette (search all actions)
Ctrl/Cmd + /     : Toggle help overlay
Ctrl/Cmd + B     : Toggle sidebar
ESC              : Close modal/dialog

Navigation:
Ctrl/Cmd + 1-6   : Navigate to page 1-6
G then U         : Go to Upload
G then A         : Go to Analysis
G then C         : Go to Compare
G then D         : Go to Dashboard

Upload Page:
Ctrl/Cmd + U     : Upload file
Ctrl/Cmd + Enter : Confirm current stage

Analysis Page:
Ctrl/Cmd + F     : Search within contract
Ctrl/Cmd + J     : Jump to section
Ctrl/Cmd + E     : Export report

Search Page:
/                : Focus search box
Ctrl/Cmd + F     : Filter panel toggle
```

**Implementation:**
```python
# In Streamlit app (custom component)
import streamlit.components.v1 as components

keyboard_shortcuts = components.html("""
<script>
document.addEventListener('keydown', function(e) {
    // Ctrl+K: Command palette
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        showCommandPalette();
    }

    // G then U: Go to Upload
    if (lastKey === 'g' && e.key === 'u') {
        window.location = '/Upload';
    }

    lastKey = e.key;
});
</script>
""", height=0)
```

**Estimated Effort:** 1 week

---

### 7.2 Batch Upload

See Section 6.5 (implemented as technical enhancement)

**Estimated Effort:** 3 weeks (already counted in 6.5)

---

### 7.3 Quick Actions

**Inline Actions:** Reduce clicks for common operations

**Contract List Quick Actions:**
```
┌────────────────────────────────────────────────────────┐
│ Contract: Acme_MSA_v2.docx                 [⋯]        │
│ Type: MSA | Risk: 🔴 High | Uploaded: 2025-11-20     │
│                                                        │
│ Quick Actions (hover):                                 │
│ [👁️ View] [🔍 Analyze] [📊 Compare] [📎 Tag] [⋯ More]│
└────────────────────────────────────────────────────────┘

On click [⋯ More]:
  • Duplicate
  • Archive
  • Export PDF
  • Email Link
  • Download Original
  • Move to Folder
  • Delete
```

**Right-Click Context Menu:**
```
Right-click on contract →
  ┌─────────────────────┐
  │ Open               │
  │ Analyze            │
  │ Compare with...    │
  │ ──────────────────│
  │ Add Tags           │
  │ Edit Metadata      │
  │ ──────────────────│
  │ Export             │
  │ Email              │
  │ ──────────────────│
  │ Archive            │
  │ Delete             │
  └─────────────────────┘
```

**Drag-and-Drop Actions:**
```
Drag contract → Drop on:
  • Tag → Apply tag
  • Folder → Move to folder
  • Compare zone → Add to comparison
  • Trash → Archive/delete
```

**Estimated Effort:** 2 weeks

---

### 7.4 Mobile Responsiveness

**Current:** Desktop-only layout

**Enhancement:** Responsive design for tablets and phones

**Breakpoints:**
- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: < 768px

**Mobile Optimizations:**

**Upload Page:**
```
┌──────────────────────┐
│ 📤 Upload            │
├──────────────────────┤
│ Active: Acme Vendor  │
│ [Switch]             │
│                      │
│ ┌──────────────────┐│
│ │ Tap to upload    ││
│ │ or take photo    ││
│ └──────────────────┘│
│                      │
│ Recent:              │
│ • Contract_001.docx  │
│ • Contract_002.docx  │
└──────────────────────┘
```

**Analysis Page (Mobile):**
```
┌──────────────────────┐
│ 🔍 Analysis          │
├──────────────────────┤
│ Acme_MSA_v2.docx     │
│                      │
│ Risk: 🔴 HIGH        │
│ Confidence: 92%      │
│                      │
│ Tabs:                │
│ [Overview▼]          │
│   Risk               │
│   Clauses            │
│   Recommendations    │
│                      │
│ ┌──────────────────┐│
│ │ 🚨 DEALBREAKERS: ││
│ │ 2 items          ││
│ │                  ││
│ │ [View Details]   ││
│ └──────────────────┘│
└──────────────────────┘
```

**Implementation:**
```css
/* Streamlit custom CSS */
@media (max-width: 768px) {
    .main-container {
        padding: 0.5rem;
    }

    .stButton > button {
        width: 100%;
        margin: 0.25rem 0;
    }

    .stDataFrame {
        font-size: 0.8rem;
    }

    /* Hide sidebar on mobile by default */
    .sidebar {
        display: none;
    }

    /* Hamburger menu for navigation */
    .mobile-nav {
        display: block;
    }
}
```

**Estimated Effort:** 2-3 weeks

---

## 8. INTEGRATION OPPORTUNITIES

**Priority:** P2-P3 (varies)
**Estimated Effort:** 2-4 weeks per integration

---

### 8.1 Microsoft 365 Integration

**SharePoint Integration:**

**Use Cases:**
- Auto-import contracts from SharePoint library
- Save analyzed contracts back to SharePoint
- Sync metadata to SharePoint columns
- Trigger analysis on SharePoint upload

**Implementation:**
```python
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential

class SharePointConnector:
    def __init__(self, site_url, client_id, client_secret):
        credentials = ClientCredential(client_id, client_secret)
        self.ctx = ClientContext(site_url).with_credentials(credentials)

    def get_contracts_library(self):
        """Get contracts document library"""
        return self.ctx.web.lists.get_by_title("Contracts")

    def import_contract(self, file_id):
        """Import contract from SharePoint to CIP"""
        lib = self.get_contracts_library()
        file = lib.get_item_by_id(file_id).file

        # Download file
        file_content = file.read()

        # Upload to CIP
        contract_id = cip_upload(file_content, file.name)

        # Save CIP ID back to SharePoint metadata
        item = lib.get_item_by_id(file_id)
        item.set_property('CIP_Contract_ID', contract_id)
        item.update()

        return contract_id

    def sync_risk_assessment(self, contract_id, sharepoint_file_id):
        """Sync CIP risk assessment to SharePoint columns"""
        assessment = get_risk_assessment(contract_id)

        item = lib.get_item_by_id(sharepoint_file_id)
        item.set_property('Risk_Level', assessment['overall_risk'])
        item.set_property('Dealbreaker_Count', len(assessment['dealbreakers']))
        item.set_property('Analysis_Date', datetime.now().isoformat())
        item.update()
```

**Teams Integration:**

**Use Cases:**
- Send analysis notifications to Teams channel
- Approve/reject from Teams
- Share negotiation playbooks in Teams chat
- Teams bot for contract queries

**Implementation:**
```python
import requests

def send_teams_notification(webhook_url, contract_analysis):
    """Send adaptive card to Teams channel"""

    card = {
        "@type": "MessageCard",
        "summary": f"Contract Analysis Complete: {contract_analysis['filename']}",
        "sections": [
            {
                "activityTitle": "Contract Analysis Complete",
                "facts": [
                    {"name": "Contract", "value": contract_analysis['filename']},
                    {"name": "Risk Level", "value": contract_analysis['overall_risk']},
                    {"name": "Dealbreakers", "value": len(contract_analysis['dealbreakers'])}
                ]
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "View Analysis",
                "targets": [
                    {"os": "default", "uri": f"https://cip.company.com/analysis/{contract_analysis['id']}"}
                ]
            }
        ]
    }

    requests.post(webhook_url, json=card)
```

**Estimated Effort:** 3-4 weeks

---

### 8.2 Google Drive Sync

**Use Cases:**
- Monitor Google Drive folder for new contracts
- Auto-upload to CIP on file add
- Sync CIP metadata to Drive custom properties
- Two-way sync

**Implementation:**
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

class GoogleDriveConnector:
    def __init__(self, credentials_file):
        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=creds)

    def watch_folder(self, folder_id, callback_url):
        """Set up webhook for folder changes"""
        body = {
            'id': f'cip-watch-{folder_id}',
            'type': 'web_hook',
            'address': callback_url
        }

        response = self.service.files().watch(
            fileId=folder_id,
            body=body
        ).execute()

        return response

    def import_file(self, file_id):
        """Import file from Drive to CIP"""
        # Get file metadata
        file = self.service.files().get(fileId=file_id).execute()

        # Download file
        request = self.service.files().get_media(fileId=file_id)
        file_content = request.execute()

        # Upload to CIP
        contract_id = cip_upload(file_content, file['name'])

        # Add CIP ID to Drive custom properties
        self.service.files().update(
            fileId=file_id,
            body={
                'properties': {
                    'cip_contract_id': contract_id,
                    'cip_synced_at': datetime.now().isoformat()
                }
            }
        ).execute()

        return contract_id
```

**Estimated Effort:** 2-3 weeks

---

### 8.3 CRM Integration (Salesforce, HubSpot)

**Use Cases:**
- Link contracts to opportunities/deals
- Auto-create contracts from won deals
- Sync contract metadata to CRM
- Contract value in pipeline reporting

**Salesforce Integration:**
```python
from simple_salesforce import Salesforce

class SalesforceConnector:
    def __init__(self, username, password, security_token):
        self.sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token
        )

    def link_contract_to_opportunity(self, contract_id, opportunity_id):
        """Link CIP contract to SF opportunity"""

        # Get contract details
        contract = get_contract(contract_id)

        # Create custom object record (Contract__c)
        result = self.sf.Contract__c.create({
            'Name': contract['filename'],
            'Opportunity__c': opportunity_id,
            'CIP_Contract_ID__c': contract_id,
            'Risk_Level__c': contract['overall_risk'],
            'Analysis_Date__c': contract['analysis_date']
        })

        return result

    def create_contract_from_opportunity(self, opportunity_id):
        """Auto-create contract when opportunity is won"""

        # Get opportunity details
        opp = self.sf.Opportunity.get(opportunity_id)

        if opp['StageName'] == 'Closed Won':
            # Create contract metadata
            metadata = {
                'type': opp['Type'],
                'parties': [opp['Account']['Name'], 'Our Company'],
                'total_value': opp['Amount'],
                'expected_close': opp['CloseDate']
            }

            # Generate contract template
            contract_id = create_contract_from_template(metadata)

            # Link back to SF
            self.link_contract_to_opportunity(contract_id, opportunity_id)

            return contract_id
```

**Estimated Effort:** 3-4 weeks per CRM

---

### 8.4 E-Signature Platforms (DocuSign, Adobe Sign)

**Use Cases:**
- Send contracts for signature from CIP
- Track signature status
- Import signed contracts back to CIP
- Version management (draft → signed)

**DocuSign Integration:**
```python
from docusign_esign import ApiClient, EnvelopesApi

class DocuSignConnector:
    def __init__(self, access_token, account_id):
        self.api_client = ApiClient()
        self.api_client.set_default_header("Authorization", f"Bearer {access_token}")
        self.envelopes_api = EnvelopesApi(self.api_client)
        self.account_id = account_id

    def send_for_signature(self, contract_id, signers):
        """Send CIP contract via DocuSign"""

        # Get contract file
        contract = get_contract(contract_id)
        file_path = contract['file_path']

        # Create envelope definition
        envelope_definition = {
            'emailSubject': f"Please sign: {contract['filename']}",
            'documents': [
                {
                    'documentId': '1',
                    'name': contract['filename'],
                    'fileExtension': 'docx',
                    'documentBase64': encode_file(file_path)
                }
            ],
            'recipients': {
                'signers': [
                    {
                        'email': signer['email'],
                        'name': signer['name'],
                        'recipientId': str(idx + 1)
                    }
                    for idx, signer in enumerate(signers)
                ]
            },
            'status': 'sent'
        }

        # Send envelope
        result = self.envelopes_api.create_envelope(
            self.account_id,
            envelope_definition=envelope_definition
        )

        # Save envelope ID to contract
        update_contract(contract_id, {
            'docusign_envelope_id': result.envelope_id,
            'signature_status': 'sent'
        })

        return result.envelope_id

    def check_signature_status(self, envelope_id):
        """Check signature status and import if complete"""

        envelope = self.envelopes_api.get_envelope(
            self.account_id,
            envelope_id
        )

        if envelope.status == 'completed':
            # Download signed document
            signed_doc = self.envelopes_api.get_document(
                self.account_id,
                envelope_id,
                '1'  # Document ID
            )

            # Import as new version
            contract_id = import_signed_contract(signed_doc)

            return {'status': 'completed', 'contract_id': contract_id}

        return {'status': envelope.status}
```

**Estimated Effort:** 2-3 weeks per platform

---

## 9. SECURITY & COMPLIANCE

**Priority:** P0 (Critical for enterprise deployment)
**Estimated Effort:** 6-8 weeks

---

### 9.1 Encryption at Rest

**Current:** SQLite database unencrypted, files stored as-is

**Enhancement:** Full encryption for sensitive data

**Implementation:**

**Database Encryption:**
```python
# Option 1: SQLCipher (encrypted SQLite)
import pysqlcipher3

conn = pysqlcipher3.connect('contracts.db')
conn.execute("PRAGMA key='your-encryption-key'")
conn.execute("PRAGMA cipher='aes-256-cbc'")

# Option 2: Encrypt specific columns
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.fernet = Fernet(key)

    def encrypt(self, plaintext):
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext):
        return self.fernet.decrypt(ciphertext.encode()).decode()

# Usage
crypto = EncryptedField(encryption_key)

# Store
encrypted_content = crypto.encrypt(contract_text)
db.execute("INSERT INTO contracts (content_encrypted) VALUES (?)", (encrypted_content,))

# Retrieve
encrypted_content = db.execute("SELECT content_encrypted FROM contracts WHERE id=?", (id,))
plaintext = crypto.decrypt(encrypted_content)
```

**File Encryption:**
```python
from cryptography.fernet import Fernet

def encrypt_file(file_path, key):
    """Encrypt file on disk"""
    fernet = Fernet(key)

    with open(file_path, 'rb') as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(file_path + '.enc', 'wb') as f:
        f.write(encrypted)

    # Remove original
    os.remove(file_path)

    return file_path + '.enc'

def decrypt_file(encrypted_path, key):
    """Decrypt file for processing"""
    fernet = Fernet(key)

    with open(encrypted_path, 'rb') as f:
        encrypted = f.read()

    decrypted = fernet.decrypt(encrypted)

    # Return decrypted bytes (don't save to disk)
    return decrypted
```

**Key Management:**
- AWS KMS or Azure Key Vault for key storage
- Key rotation policy (every 90 days)
- Separate keys per environment (dev/staging/prod)

**Estimated Effort:** 2 weeks

---

### 9.2 Audit Logging

**Purpose:** Track all user actions for compliance and security

**Database Schema:**
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    user_email TEXT,
    ip_address TEXT,
    user_agent TEXT,

    -- Action details
    action_type TEXT NOT NULL,  -- 'upload', 'analyze', 'view', 'edit', 'delete', 'export'
    action_category TEXT,  -- 'contract', 'profile', 'clause', 'setting'
    action_result TEXT,  -- 'success', 'failure', 'partial'

    -- Resource details
    resource_type TEXT,  -- 'contract', 'assessment', 'clause', etc.
    resource_id INTEGER,
    resource_name TEXT,

    -- Change tracking
    old_value TEXT,  -- JSON of previous state
    new_value TEXT,  -- JSON of new state

    -- Context
    session_id TEXT,
    api_endpoint TEXT,
    request_id TEXT,

    -- Metadata
    metadata_json TEXT,  -- Additional context

    -- Security
    auth_method TEXT,  -- 'password', 'sso', 'api_key'
    risk_score REAL  -- 0.0-1.0, for anomaly detection
);

-- Indexes for common queries
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action_type);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
```

**Logging Implementation:**
```python
class AuditLogger:
    @staticmethod
    def log_action(
        user_id, action_type, resource_type, resource_id,
        old_value=None, new_value=None, metadata=None
    ):
        """Log user action to audit trail"""

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO audit_log (
                user_id, user_email, ip_address, user_agent,
                action_type, action_category, action_result,
                resource_type, resource_id,
                old_value, new_value,
                session_id, api_endpoint,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            get_user_email(user_id),
            request.remote_addr,
            request.user_agent.string,
            action_type,
            get_category(resource_type),
            'success',
            resource_type,
            resource_id,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None,
            session.get('session_id'),
            request.endpoint,
            json.dumps(metadata) if metadata else None
        ))

        conn.commit()
        conn.close()

# Usage in API endpoints
@app.route('/api/contract/<int:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    # Get current state before deletion
    contract = get_contract(contract_id)

    # Perform deletion
    delete_contract_db(contract_id)

    # Log action
    AuditLogger.log_action(
        user_id=current_user.id,
        action_type='delete',
        resource_type='contract',
        resource_id=contract_id,
        old_value={'filename': contract['filename'], 'status': contract['status']},
        new_value=None,
        metadata={'reason': request.json.get('reason')}
    )

    return jsonify({'status': 'deleted'})
```

**Audit Report Generation:**
```python
def generate_audit_report(start_date, end_date, user_id=None):
    """Generate audit report for date range"""

    query = """
        SELECT
            timestamp,
            user_email,
            action_type,
            resource_type,
            resource_name,
            action_result
        FROM audit_log
        WHERE timestamp BETWEEN ? AND ?
    """

    params = [start_date, end_date]

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    query += " ORDER BY timestamp DESC"

    results = db.execute(query, params).fetchall()

    # Generate report
    report = {
        'period': {'start': start_date, 'end': end_date},
        'total_actions': len(results),
        'actions_by_type': {},
        'actions_by_user': {},
        'failed_actions': [],
        'high_risk_actions': []
    }

    for row in results:
        # Count by type
        action_type = row['action_type']
        report['actions_by_type'][action_type] = \
            report['actions_by_type'].get(action_type, 0) + 1

        # Count by user
        user = row['user_email']
        report['actions_by_user'][user] = \
            report['actions_by_user'].get(user, 0) + 1

        # Track failures
        if row['action_result'] == 'failure':
            report['failed_actions'].append(row)

        # Track high-risk actions
        if row['action_type'] in ['delete', 'export']:
            report['high_risk_actions'].append(row)

    return report
```

**Estimated Effort:** 2 weeks

---

### 9.3 Role-Based Access Control (RBAC)

**Roles:**

**1. Admin**
- Full access to all features
- User management
- System configuration
- Audit log access

**2. Legal Team Member**
- Upload contracts
- Run analysis
- View all contracts
- Create/edit clause library
- Generate reports
- Cannot delete contracts

**3. Reviewer**
- View contracts
- View analysis
- Add comments
- Cannot upload or edit

**4. Executive**
- Dashboard access only
- View high-level metrics
- Export reports
- Cannot view individual contract details (privacy)

**Database Schema:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,  -- If not using SSO
    full_name TEXT,
    role TEXT NOT NULL,  -- 'admin', 'legal', 'reviewer', 'executive'
    is_active INTEGER DEFAULT 1,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    resource TEXT NOT NULL,  -- 'contract', 'analysis', 'clause_library', etc.
    action TEXT NOT NULL,  -- 'create', 'read', 'update', 'delete', 'export'
    allowed INTEGER DEFAULT 1
);

-- Seed permissions
INSERT INTO permissions (role, resource, action, allowed) VALUES
-- Admin: full access
('admin', '*', '*', 1),

-- Legal: most actions
('legal', 'contract', 'create', 1),
('legal', 'contract', 'read', 1),
('legal', 'contract', 'update', 1),
('legal', 'contract', 'delete', 0),  -- Cannot delete
('legal', 'analysis', '*', 1),
('legal', 'clause_library', '*', 1),

-- Reviewer: read-only
('reviewer', 'contract', 'read', 1),
('reviewer', 'analysis', 'read', 1),
('reviewer', 'comment', 'create', 1),

-- Executive: dashboard only
('executive', 'dashboard', 'read', 1),
('executive', 'report', 'export', 1);
```

**Authorization Middleware:**
```python
from functools import wraps
from flask import session, abort

def require_permission(resource, action):
    """Decorator to check user permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                abort(401)  # Unauthorized

            if not has_permission(user.role, resource, action):
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(role, resource, action):
    """Check if role has permission for action on resource"""

    # Admin has all permissions
    if role == 'admin':
        return True

    # Check specific permission
    result = db.execute("""
        SELECT allowed FROM permissions
        WHERE role = ? AND
              (resource = ? OR resource = '*') AND
              (action = ? OR action = '*')
        ORDER BY
            CASE WHEN resource = '*' THEN 1 ELSE 0 END,
            CASE WHEN action = '*' THEN 1 ELSE 0 END
        LIMIT 1
    """, (role, resource, action)).fetchone()

    return result and result['allowed'] == 1

# Usage
@app.route('/api/contract/<int:contract_id>', methods=['DELETE'])
@require_permission('contract', 'delete')
def delete_contract(contract_id):
    # Only users with delete permission can access this
    delete_contract_db(contract_id)
    return jsonify({'status': 'deleted'})
```

**Frontend Access Control:**
```python
# In Streamlit pages
import streamlit as st

def check_permission(resource, action):
    """Check if current user has permission"""
    user = st.session_state.get('user')

    if not user:
        st.error("Not logged in")
        st.stop()

    if not has_permission(user['role'], resource, action):
        st.error("You don't have permission to perform this action")
        st.stop()

# Usage in upload page
check_permission('contract', 'create')

# Only show delete button if user has permission
if has_permission(st.session_state.user['role'], 'contract', 'delete'):
    if st.button("Delete Contract"):
        delete_contract(contract_id)
```

**Estimated Effort:** 3 weeks

---

### 9.4 Data Retention Policies

**Purpose:** Automatically delete old data per compliance requirements

**Retention Policy Examples:**

- **Contracts:** Keep for 7 years after expiration
- **Analysis Results:** Keep for 5 years
- **Audit Logs:** Keep for 3 years
- **Temporary Files:** Delete after 30 days
- **Draft Contracts:** Delete after 1 year if not finalized

**Database Schema:**
```sql
CREATE TABLE retention_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT NOT NULL,
    retention_period_days INTEGER NOT NULL,
    retention_basis TEXT,  -- 'from_upload', 'from_expiration', 'from_last_access'
    auto_delete INTEGER DEFAULT 1,
    archive_before_delete INTEGER DEFAULT 1,
    archive_location TEXT
);

-- Example policies
INSERT INTO retention_policies (resource_type, retention_period_days, retention_basis) VALUES
('contract', 2555, 'from_expiration'),  -- 7 years
('risk_assessment', 1825, 'from_creation'),  -- 5 years
('audit_log', 1095, 'from_creation'),  -- 3 years
('temp_file', 30, 'from_creation');

-- Track deletion schedule
CREATE TABLE deletion_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT,
    resource_id INTEGER,
    scheduled_deletion_date DATE,
    deletion_reason TEXT,
    deletion_status TEXT,  -- 'scheduled', 'archived', 'deleted', 'retained'
    archived_location TEXT,
    deleted_date TIMESTAMP
);
```

**Automated Cleanup Job:**
```python
import schedule
import time

def cleanup_expired_data():
    """Daily job to delete expired data"""

    # Get all retention policies
    policies = db.execute("SELECT * FROM retention_policies").fetchall()

    for policy in policies:
        resource_type = policy['resource_type']
        retention_days = policy['retention_period_days']
        basis = policy['retention_basis']

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # Find expired resources
        if resource_type == 'contract':
            if basis == 'from_expiration':
                expired = db.execute("""
                    SELECT id FROM contracts
                    WHERE expiration_date < ?
                    AND is_deleted = 0
                """, (cutoff_date,)).fetchall()

            for contract in expired:
                # Archive before delete
                if policy['archive_before_delete']:
                    archive_contract(contract['id'], policy['archive_location'])

                # Soft delete
                db.execute("""
                    UPDATE contracts
                    SET is_deleted = 1,
                        deleted_date = ?,
                        deletion_reason = 'retention_policy'
                    WHERE id = ?
                """, (datetime.now(), contract['id']))

                # Log deletion
                AuditLogger.log_action(
                    user_id='system',
                    action_type='auto_delete',
                    resource_type='contract',
                    resource_id=contract['id'],
                    metadata={'policy': policy['id'], 'reason': 'retention_policy'}
                )

        # Similar logic for other resource types

    db.commit()

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(cleanup_expired_data)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

**User Override:**
```python
@app.route('/api/contract/<int:contract_id>/retain', methods=['POST'])
@require_permission('contract', 'update')
def extend_retention(contract_id):
    """Extend retention period for specific contract"""

    data = request.json
    extend_days = data.get('extend_days', 365)
    reason = data.get('reason')

    # Remove from deletion schedule
    db.execute("""
        UPDATE deletion_schedule
        SET deletion_status = 'retained',
            scheduled_deletion_date = DATE(scheduled_deletion_date, '+' || ? || ' days')
        WHERE resource_type = 'contract' AND resource_id = ?
    """, (extend_days, contract_id))

    # Log retention extension
    AuditLogger.log_action(
        user_id=current_user.id,
        action_type='extend_retention',
        resource_type='contract',
        resource_id=contract_id,
        metadata={'extend_days': extend_days, 'reason': reason}
    )

    return jsonify({'status': 'retained', 'new_deletion_date': new_date})
```

**Estimated Effort:** 2 weeks

---

## 10. IMPLEMENTATION NOTES

### 10.1 Dependencies Between Phases

**Critical Path:**

```
Phase A (Complete) ───────┐
                          ├──> Phase B (Profiles) ───┐
                          │                           ├──> Phase E (Workflows)
                          ├──> Phase C (Search) ──────┤
                          │                           │
                          └──> Phase D (Clause Lib) ──┘

Phases B, C, D can be developed in parallel
Phase E benefits from all previous phases
```

**Recommended Order:**

1. **Phase A** ✅ (Complete)
2. **Phase C** (Search & Filtering)
   - Foundational for all other features
   - Enables users to manage growing contract library
   - No dependencies

3. **Phase B** (User Profiles)
   - Improves upload efficiency
   - Independent from other phases
   - Can be developed in parallel with Phase C

4. **Phase D** (Clause Library)
   - Depends on search/tagging from Phase C
   - Major value-add for long-term users

5. **Phase E** (Remaining Workflows)
   - Benefits from all previous phases
   - Negotiate workflow uses clause library
   - Dashboard shows comprehensive metrics

6. **Technical Enhancements**
   - Can be done incrementally throughout
   - Priority: RAG integration, then Law Library

7. **Security & Compliance**
   - Essential before enterprise deployment
   - Implement alongside Phases C-D

8. **Integrations**
   - Last priority
   - Implement based on customer demand

---

### 10.2 Risk Mitigation

**Technical Risks:**

**Risk 1: AI Model Availability/Cost**
- **Mitigation:** Multi-LLM orchestration (Section 6.3)
- **Fallback:** Cache frequent queries, reduce model calls
- **Monitoring:** Track API usage and costs daily

**Risk 2: Performance Degradation at Scale**
- **Mitigation:** Implement caching, indexing, pagination early
- **Testing:** Load test with 10,000+ contracts
- **Monitoring:** Track response times, set alerts

**Risk 3: Data Loss/Corruption**
- **Mitigation:** Daily backups, transaction safety
- **Testing:** Backup/restore procedures
- **Monitoring:** Integrity checks on database

**Risk 4: Integration Breaking Changes**
- **Mitigation:** Version pin external APIs, adapter pattern
- **Testing:** Integration tests in CI/CD
- **Monitoring:** Alert on API errors

**Product Risks:**

**Risk 1: Low Clause Library Adoption**
- **Mitigation:** Make extraction frictionless, show ROI
- **Testing:** User testing before release
- **Monitoring:** Track library usage metrics

**Risk 2: Version Detection False Positives**
- **Mitigation:** Tunable threshold, user override always available
- **Testing:** Test with diverse contract sets
- **Monitoring:** Track user override rate

**Risk 3: AI Suggestions Inaccurate**
- **Mitigation:** Always require human confirmation, show confidence
- **Testing:** Benchmark against human experts
- **Monitoring:** Track user edit rate (how often AI is overridden)

---

### 10.3 Testing Requirements

**Unit Tests:**
- All backend methods
- Database operations
- API endpoints
- Business logic

**Integration Tests:**
- Full upload → analyze → compare workflow
- Multi-stage confirmation flow
- Search with complex filters
- Clause library extraction and reuse

**Performance Tests:**
- Upload 100 contracts simultaneously
- Search across 10,000 contracts
- Dashboard with 50,000 data points
- Concurrent user load (50+ users)

**Security Tests:**
- SQL injection attempts
- XSS attempts
- Authentication bypass attempts
- Permission escalation attempts
- Data exfiltration scenarios

**User Acceptance Tests:**
- Real users test each workflow
- A/B test UI changes
- Usability study for new features

**Regression Tests:**
- Automated suite runs on every commit
- Test backward compatibility
- Test data migration scripts

---

### 10.4 Rollback Procedures

**Database Rollback:**
```sql
-- Before schema change, create backup
CREATE TABLE contracts_backup AS SELECT * FROM contracts;

-- If migration fails, restore
DROP TABLE contracts;
ALTER TABLE contracts_backup RENAME TO contracts;
```

**Code Rollback:**
- Git tags for each release
- Docker images tagged by version
- Rollback command: `git checkout v1.2.3 && docker-compose up -d`

**Feature Flags:**
```python
# Feature flag system for gradual rollout
FEATURE_FLAGS = {
    'clause_library': os.getenv('ENABLE_CLAUSE_LIBRARY', 'false').lower() == 'true',
    'bulk_upload': os.getenv('ENABLE_BULK_UPLOAD', 'false').lower() == 'true',
    'negotiation_workflow': os.getenv('ENABLE_NEGOTIATION', 'false').lower() == 'true'
}

# Usage
if FEATURE_FLAGS['clause_library']:
    show_clause_library_ui()
else:
    st.info("Clause library coming soon!")
```

**Rollback Decision Matrix:**

| Severity | Issue Example | Action | Rollback? |
|----------|---------------|--------|-----------|
| Critical | Data loss, security breach | Immediate rollback | Yes |
| High | Feature completely broken | Rollback within 1 hour | Yes |
| Medium | Feature partially broken | Fix forward if possible | Maybe |
| Low | UI glitch, typo | Fix in next release | No |

---

### 10.5 Success Metrics

**Per Phase:**

**Phase B (Profiles):**
- Metric: % of uploads using profiles
- Target: >60% within 1 month
- Metric: Time to upload (with vs without profile)
- Target: 30% faster

**Phase C (Search):**
- Metric: Time to find specific contract
- Target: <30 seconds for 1000+ contracts
- Metric: Search usage
- Target: >80% of users use search weekly

**Phase D (Clause Library):**
- Metric: % of new contracts using library clauses
- Target: >40% within 3 months
- Metric: Success rate improvement over time
- Target: +10 percentage points per quarter

**Phase E (Workflows):**
- Metric: Negotiation playbook generation time
- Target: <2 minutes
- Metric: Dashboard load time
- Target: <3 seconds for 10,000 contracts

**Overall Platform:**
- Contract review time: 70% reduction vs manual (days → hours)
- User satisfaction: >4.5/5 rating
- Daily active users: >80% of licensed users
- Contract upload rate: +50% month-over-month (indicates adoption)

---

## CONCLUSION

This roadmap provides a comprehensive plan for evolving the Contract Intelligence Platform from a functional MVP (Phase A complete) to a enterprise-grade contract management system.

**Immediate Priorities (Next 3 Months):**
1. Phase C: Search & Filtering (4 weeks)
2. Phase B: User Profiles (3 weeks)
3. Security & Compliance foundation (4 weeks)

**Medium-Term Goals (3-6 Months):**
1. Phase D: Clause Library (5 weeks)
2. RAG Integration (2 weeks)
3. Performance Optimizations (3 weeks)

**Long-Term Vision (6-12 Months):**
1. Phase E: Complete all workflows
2. Law Library Integration
3. M365/SharePoint Integration
4. Advanced Analytics & Reporting

**Maintenance & Evolution:**
- Continuous user feedback incorporation
- Monthly feature releases
- Quarterly security audits
- Annual roadmap review

---

**Document Version:** 1.0
**Next Review Date:** 2026-02-22 (3 months)
**Owner:** CIP Product Team
**Status:** Active Planning Document
