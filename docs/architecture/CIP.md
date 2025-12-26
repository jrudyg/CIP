# CIP Governance Document

This document defines operational standards, validation patterns, and guardrails for the Contract Intelligence Platform (CIP).

## 1. Overview

The Contract Intelligence Platform (CIP) is a Streamlit-based application
for analyzing contract redlines, synthesizing clause-level impacts, and
providing structured guidance for negotiation workflows.

CIP follows the Z-Framework zoning model:
- **Z1** – Inputs & file handling
- **Z2** – High-density summary
- **Z3** – Clause-level detail
- **Z4** – Impact & Risk Synthesis
- **Z5** – Negotiation Strategy & Guidance
- **Z6** – Scenario Modeling
- **Z7** – Decision & Export
- **Z8** – Cross-Document Intelligence
- **Z9** – Contract Playbook Synthesis
- **Z0** – Knowledge Layer (persistent storage)

Each zone is validated using:
1. UI smoke tests (existence + import)
2. Data invariants (structural correctness)
3. Theming & accessibility review (GEM)
4. Cross-zone consistency (CAI)

CIP is maintained using the CC workflow:
PLAN → EDIT → RUN → STATUS

## 2. Architecture Summary

### 2.1 Frontend (Streamlit)
- File-based pages under `frontend/pages/`
- Zone functions grouped within each page file
- Scoped CSS per zone using `st.markdown(unsafe_allow_html=True)`
- No global CSS leakage; all classes prefixed `.zX-*`
- Supports both dark theme and theme-token color variables

### 2.2 Test & Validation Layer
- Zone-level smoke tests under `frontend/tests/`
- Data invariants under `frontend/validators/`
- Tests invoked via:
    python frontend/tests/<testfile>.py

### 2.3 Agent Framework
CIP governance interacts with three agents:

- **CAI** – Structural audit
- **GEM** – Theme/A11y audit
- **CC** – File-level implementation engine

Agents do not modify CIP.md directly; CC handles all writes.

### 2.4 Z-Stack Data Flow
1. File uploaded in Z1 → parsed into `st.session_state.redline_result`
2. Z2 summarizes:
   - Counts (inserted/removed/modified)
   - Impact level
   - Position shift
   - Focus-first clause
3. Z3 consumes the same `redline_result` to render clause detail
4. Validator ensures Z2 ↔ Z3 consistency before downstream zones use the data

## 3. Development Standards

### 3.1 Code Structure
- Functions must be deterministic and pure except Streamlit I/O
- Zone functions named `zX_<purpose>()`
- UI logic separated from validity logic where possible

### 3.2 CSS & Theming
- All semantic colors MUST use theme variables:
  var(--color-status-success-light)
  var(--color-status-warning-light)
  var(--color-status-danger-light)
- Neutral surfaces use hex only if non-semantic:
  Background: #1A1A1A
  Border: #333333
- No color-only signaling; all pills must contain text

### 3.3 Tests
Each new zone requires:
- A smoke test (import + existence)
- Data validators if the zone consumes structured data
- Optional fixtures for more complex flows

### 3.4 CC Operations
- All file edits go through CC
- Each CC cycle must include:
  - PLAN (intent)
  - EDIT (unified diff)
  - RUN (tests)
  - STATUS (explicit outcome)

### 3.5 Future-Proofing
- New zones must document:
  - Purpose
  - Inputs
  - Outputs
  - Invariants
  - Validation paths (UI + data)

## 4. CC Operations

This section documents Claude Code (CC) operational patterns and validation guardrails.

### 4.1 Zone-Level Validation – Z2 / Z3 (Redline Review Page)

This page uses a three-layer guardrail pattern:

1. **UI smoke tests (zone-specific)**
2. **Data invariants (Z2 ↔ Z3 consistency)**
3. **Theming & accessibility (GEM-driven)**

#### 4.1.1 Z2 – Summary Zone (Micro-Boards)

**Purpose:** High-density summary of redline impact.

**Guardrails:**

- **Code:** `frontend/pages/5_📝_Redline_Reviews.py`
  - Function: `z2_change_summary()`
- **Smoke test:** `frontend/tests/z2_smoke_test.py`
  - Verifies:
    - Page module imports without syntax errors
    - `z2_change_summary()` exists
  - Run:
    - `python frontend/tests/z2_smoke_test.py`
- **A11y/Theme:**
  - Uses scoped `.z2-*` CSS and theme tokens:
    - `var(--color-status-success-light, #3CCB7F)`
    - `var(--color-status-warning-light, #FFD166)`
    - `var(--color-status-danger-light, #FF6B6B)`

#### 4.1.2 Z3 – Clause-Detail Zone

**Purpose:** Clause-level drill-down backing Z2's metrics.

**Guardrails:**

- **Code:** `frontend/pages/5_📝_Redline_Reviews.py`
  - Function: `z3_clause_detail()`
  - Features:
    - Dark theme clause cards
    - Impact / favorability / risk pills
    - Prev/Next navigation
    - Clause index indicator: `Clause {idx+1} of {total}`
- **Smoke test:** `frontend/tests/z3_smoke_test.py`
  - Verifies:
    - Page module imports
    - `z3_clause_detail()` exists
  - Run:
    - `python frontend/tests/z3_smoke_test.py`
- **Theming:**
  - Risk classes use theme-aware tokens:
    - `.z3-risk-high` → `var(--color-status-danger-*, …)`
    - `.z3-risk-medium` → `var(--color-status-warning-*, …)`
    - `.z3-risk-low` → `var(--color-status-success-*, …)`
  - No color-only signaling: all pills carry explicit text labels.

#### 4.1.3 Z2/Z3 Data Consistency Validator

**Purpose:** Enforce invariants between Z2 summary metrics and Z3 clause data.

**Guardrails:**

- **Validator:** `frontend/validators/redline_consistency.py`
  - Function: `validate_redline_consistency(redline_result) -> List[str]`
  - Checks:
    - `clause_changes` / `clauses` is a list
    - Each clause has: `clause_id`, `section_title`, `change_type`
    - `change_type` ∈ {inserted, removed, modified}
    - `impact` ∈ {low, medium, high}
    - `position_shift` ∈ {favors_customer, balanced, favors_counterparty}
    - At most one `focus_first` clause
    - `inserted_count` / `removed_count` / `modified_count` (if present) match derived counts
- **Test:** `frontend/tests/redline_consistency_test.py`
  - Loads the validator and runs it against a sample redline payload.
  - Fails fast if invariants are broken.
  - Run:
    - `python frontend/tests/redline_consistency_test.py`

**Usage:**

- CAI or CI can call `validate_redline_consistency()` before or after rendering
  to ensure that Z2's numbers and Z3's clauses never silently drift apart.

### 4.2 Z4 – Impact & Risk Synthesis Zone

**Purpose:** Turn clause-level changes from Z3 into a concise, decision-oriented
view of risk, leverage, and critical clauses for the reviewer.

#### 4.2.1 Implementation

- **Code:** `frontend/pages/5_📝_Redline_Reviews.py`
  - Function: `z4_analysis_zone()`
  - Wired into the zone layout as:
    - `z4=z4_analysis_zone` (e.g., in the Z-layout helper)

- **Data Inputs:**
  - `st.session_state["redline_result"]` with one of:
    - `redline_result["clause_changes"]`
    - or `redline_result["clauses"]`

  Each clause entry may include:
  - `clause_id` (e.g., "5.2")
  - `section_title` (e.g., "Payment Terms")
  - `change_type` ("inserted" | "removed" | "modified")
  - `impact` ("low" | "medium" | "high")
  - `position_shift` ("favors_customer" | "balanced" | "favors_counterparty")
  - `focus_first` (bool)
  - `reason` (short rationale text)

#### 4.2.2 Risk Model & Views

Z4 normalizes clause metadata and derives a simple risk model:

- Impact weight:
  - low = 1.0
  - medium = 2.0
  - high = 3.0

- Position shift weight:
  - favors_customer = 0.5
  - balanced = 1.0
  - favors_counterparty = 1.5

- **Risk score:**
  `risk_score = impact_weight * shift_weight`

From this, Z4 surfaces four main views:

1. **Top Risk Drivers**
   - Top 5 clauses by `risk_score` (descending).
   - Shows clause, impact pill, favorability pill, and rationale.

2. **Negotiation Levers**
   - Clauses where `position_shift == "favors_counterparty"` AND
     `impact ∈ {"medium", "high"}` (top 5).
   - Highlighted as areas where the counterparty is pushing hardest.

3. **Customer-Advantage Opportunities**
   - Clauses where `position_shift == "favors_customer"` (top 5).
   - Highlighted as potential leverage points.

4. **Critical Clause Strip**
   - Clauses whose `section_title` contains any of:
     "payment", "liability", "indemnity", "indemnification",
     "termination", "service level", "sla", "limitation of liability".
   - Surfaces business-critical areas regardless of impact score.

#### 4.2.3 UI & Theming

- Z4 renders a structured block:

  - Wrapper and sections:
    - `.z4-wrapper`, `.z4-section`, `.z4-section-title`
  - Items and text:
    - `.z4-item`, `.z4-item-header`, `.z4-item-body`
  - Pills and tags:
    - `.z4-pills`, `.z4-pill`
    - Impact pills: `.z4-pill-impact-high`, `.z4-pill-impact-medium`, `.z4-pill-impact-low`
    - Favorability pills:
      - `.z4-pill-favor-favors_customer`
      - `.z4-pill-favor-balanced`
      - `.z4-pill-favor-favors_counterparty`
    - Tag pills: `.z4-pill-tag` (e.g., "High priority", "Counterparty leverage",
      "Your leverage", "Critical clause", "Focus first")

- Semantic colors use theme-aware tokens with safe fallbacks, e.g.:

  - Danger / high risk:
    - `var(--color-status-danger-bg, rgba(255, 107, 107, 0.15))`
    - `var(--color-status-danger-light, #FF6B6B)`

  - Warning / medium risk:
    - `var(--color-status-warning-bg, rgba(255, 209, 102, 0.15))`
    - `var(--color-status-warning-light, #FFD166)`

  - Success / low risk:
    - `var(--color-status-success-bg, rgba(60, 203, 127, 0.15))`
    - `var(--color-status-success-light, #3CCB7F)`

- Neutral surfaces:
  - Background: `#1A1A1A`
  - Border: `#333333`

- No color-only signaling:
  - All pills include explicit text (e.g., "High impact", "Favors counterparty",
    "Your leverage", etc.).

#### 4.2.4 Tests & Validation

- **Smoke Test:** `frontend/tests/z4_smoke_test.py`
  - Verifies:
    - Page module imports
    - `z4_analysis_zone()` exists
  - Run:
    - `python frontend/tests/z4_smoke_test.py`

- **Data Dependence:**
  - Z4 uses the same clause data as Z3.
  - Structural/data invariants remain enforced by:
    - `frontend/validators/redline_consistency.py`
    - `frontend/tests/redline_consistency_test.py`

  Z4 MUST NOT mutate or redefine clause counts; it is a read-only analytical
view over the Z3 data.

### 4.3 Z5 – Negotiation Strategy & Guidance Zone

**Purpose:** Convert analytical outputs from Z4 into concrete
negotiation strategy, recommended counterproposals, and a concise
deal posture summary.

#### 4.3.1 Implementation

- **Code:** `frontend/pages/5_📝_Redline_Reviews.py`
  - Function: `z5_strategy_zone()`
  - Wired into the Z-layout as:
    - `z5=z5_strategy_zone`

- **Inputs:**
  - Clause-level data already validated and used by Z3/Z4, including:
    - `clause_id`
    - `section_title`
    - `impact` ("low" | "medium" | "high")
    - `position_shift` ("favors_customer" | "balanced" | "favors_counterparty")
    - `risk_score` (derived as in Z4)
    - `reason` (short rationale)
    - `focus_first` (optional, boolean)

#### 4.3.2 Strategy Outputs

Z5 surfaces four primary strategy artifacts:

1. **RAG Negotiation Map**
   - Classifies clauses into:
     - Red (critical pushbacks)
     - Amber (monitor / potential tradeoffs)
     - Green (favorable / acceptable)
   - Uses thresholds derived from `risk_score`, e.g.:
     - Red: risk_score ≥ 4.0
     - Amber: 2.0 ≤ risk_score < 4.0
     - Green: risk_score < 2.0
   - Displays counts and labeled categories using `.z5-rag-*` classes.

2. **Negotiation Priorities List**
   - Top N (e.g., 5) clauses by risk_score, highest first.
   - Each entry includes:
     - Clause ID + title
     - Impact level
     - Favorability
     - Brief "Why" rationale
     - Priority pill (e.g., "Priority 1", "Priority 2"...).

3. **Recommended Counterproposals**
   - Rule-based, template-style suggestions for high-risk clauses, keyed by:
     - Section title keywords (e.g., "liability", "indemnity", "payment", "termination", "SLA")
     - Impact and position_shift
   - Designed to:
     - Suggest typical risk-mitigating moves (e.g., liability caps, payment term adjustments)
     - Avoid claiming changes that are not in the actual contract text.

4. **Deal Posture Summary**
   - A short narrative summary (1–2 sentences) derived from:
     - Distribution of Red/Amber/Green clauses
     - Concentration of high-risk areas (e.g., liability, indemnity, payment)
   - Example posture axes:
     - High-risk: >40% red
     - Moderate: >20% red
     - Favorable: >60% green
     - Balanced: otherwise

#### 4.3.3 UI & Theming

- Uses scoped CSS classes:
  - `.z5-wrapper`, `.z5-section`, `.z5-section-title`
  - `.z5-item`, `.z5-item-header`, `.z5-item-body`
  - `.z5-pills`, `.z5-pill`
  - `.z5-rag-red`, `.z5-rag-amber`, `.z5-rag-green`
  - `.z5-pill-priority`, `.z5-pill-action`
  - `.z5-posture-summary`, `.z5-rag-map`, `.z5-rag-item`,
    `.z5-rag-count`, `.z5-rag-label`

- Semantic colors:
  - Red = danger tokens:
    - `var(--color-status-danger-bg, ...)`
    - `var(--color-status-danger-light, #FF6B6B)`
  - Amber = warning tokens:
    - `var(--color-status-warning-bg, ...)`
    - `var(--color-status-warning-light, #FFD166)`
  - Green = success tokens:
    - `var(--color-status-success-bg, ...)`
    - `var(--color-status-success-light, #3CCB7F)`

- Neutral surfaces:
  - Background: `#1A1A1A`
  - Border: `#333333`

- Accessibility:
  - Z5 follows the same A11y rules as Z2–Z4:
    - No color-only signaling; every color state has a text label.
    - Text contrast meets WCAG AA.

#### 4.3.4 Tests & Validation

- **Smoke Test:** `frontend/tests/z5_smoke_test.py`
  - Verifies:
    - Page module imports
    - `z5_strategy_zone()` exists
  - Run:
    - `python frontend/tests/z5_smoke_test.py`

- **Data Consistency:**
  - Z5 reads clause data already validated by:
    - `frontend/validators/redline_consistency.py`
    - `frontend/tests/redline_consistency_test.py`
  - Z5 MUST NOT:
    - Modify clause data.
    - Redefine summary counts established by Z2/Z3/Z4.
  - Z5 is a read-only interpretive layer over the existing zone stack.

### 4.4 Z8 – Cross-Document Intelligence Zone

Implements Z-Framework v1.1 (archetype: Z-Comparison)

**Purpose:**
- Compare multiple redline snapshots (R1, R2, ... Rn) across negotiation rounds.
- Detect posture trajectory, RAG trends, clause evolution with stability ratings, and counterparty behavior patterns.

#### 4.4.1 Implementation

- **Code:** `frontend/pages/5_📝_Redline_Reviews.py`
  - Function: `z8_cross_document_zone()`
  - Wired into the zone layout as:
    - `z8=z8_cross_document_zone` (full-width below Z5-Z7)

- **Data Inputs:**
  - `st.session_state["comparison_set"]` – list of at least 2 redline snapshots
  - Each snapshot contains:
    - `label` (e.g., "R1", "R2")
    - `redline_result.clauses` or `redline_result.clause_changes`

#### 4.4.2 Structured Output

Z8 produces and stores `st.session_state["z8_result"]` with:

- **summary:**
  - `round_count` – number of snapshots compared
  - `baseline_posture` – posture of first round
  - `final_posture` – posture of last round
  - `trajectory` – "Improving" | "Worsening" | "Stable"

- **clause_trends:** (list of per-clause entries)
  - `clause_id`
  - `stability` – "Stable" | "Moderately volatile" | "Highly volatile"
  - `net_verdict` – "Better" | "Worse" | "No net change"
  - `impact_start`, `impact_end`
  - `shift_start`, `shift_end`
  - `transitions` – count of changes across rounds

- **behavior_insights:**
  - `concessions_count` – clauses where risk improved
  - `counterparty_leaning_changes` – clauses newly shifted to favors_counterparty

- **invariants:**
  - `clause_id_stable` – true if no clauses are missing from any round
  - `round_count` – echo of snapshot count
  - `missing_clauses` – list of clause IDs not present in all rounds
  - `trend_consistency_ok` – validation flag

#### 4.4.3 Risk Model & Semantics

Uses canonical Z-Framework v1.1 weights:

- **Impact weights:** low=1, medium=2, high=3
- **Shift weights:** favors_customer=0.5, balanced=1.0, favors_counterparty=1.5
- **Risk score:** `impact_weight × shift_weight`
- **RAG thresholds:** Red ≥4.0, Amber 2.0–3.99, Green <2.0
- **Posture thresholds:**
  - High Risk: red_pct > 40%
  - Moderate: red_pct > 20%
  - Favorable: green_pct > 60%
  - Balanced: otherwise

**Trajectory is computed as:**
- Improving: final posture rank < baseline rank
- Worsening: final posture rank > baseline rank
- Stable: no change

**Stability ratings:**
- Stable: 0 transitions
- Moderately volatile: 1 transition
- Highly volatile: 2+ transitions

**Net verdict:**
- Better: last risk < first risk
- Worse: last risk > first risk
- No net change: equal

#### 4.4.4 UI & Theming

- Uses scoped CSS classes:
  - `.z8-section`, `.z8-title`, `.z8-subtitle`
  - `.z8-trend-row`, `.z8-pill`
  - `.z8-pill-red`, `.z8-pill-amber`, `.z8-pill-green`, `.z8-pill-neutral`
  - `.z8-clause-card`, `.z8-clause-header`, `.z8-clause-timeline`
  - `.z8-behavior-item`
  - `.z8-invariant-pass`, `.z8-invariant-fail`

- Semantic colors use theme tokens with fallbacks:
  - Danger: `var(--color-status-danger-bg)`, `var(--color-status-danger-light)`
  - Warning: `var(--color-status-warning-bg)`, `var(--color-status-warning-light)`
  - Success: `var(--color-status-success-bg)`, `var(--color-status-success-light)`

- Neutral surfaces: `#1A1A1A`, `#222`, `#333`

- Accessibility:
  - No color-only signaling; all pills have text labels
  - Invariants displayed in collapsible debug expander

#### 4.4.5 Tests & Validation

**Smoke Test:** `frontend/tests/z8_smoke_test.py`
- Verifies:
  - Page module imports
  - `z8_cross_document_zone()` exists
- Run:
  - `python frontend/tests/z8_smoke_test.py`

**Compliance Requirements:**
- Uses canonical risk model (impact/favor weights, posture thresholds)
- Must not mutate upstream snapshots
- Must expose structured output in `st.session_state["z8_result"]`
- CSS scoped under `.z8-*` and theme-tokenized
- CAI/GEM WARN or FAIL = BLOCK

### 4.5 Z0 – Knowledge Layer (Data Only)

**Framework:**
- implements: Z-Framework v1.1
- archetype: Z-Memory

**Purpose:**
Aggregate Z8 results across deals and counterparties into a persistent
knowledge base that can answer questions such as:
- How does a given counterparty typically behave (posture, concessions)?
- Which clauses are structurally volatile or frequently end "Worse"?
- What is the overall posture of the deal portfolio over time?

#### 4.5.1 Input Contract (read-only)

Each ingestion call takes:
- `deal_id`: unique deal identifier
- `counterparty_id`: normalized counterparty identifier
- `timestamp`: ISO 8601 string
- `z8_result`: the structured object produced by Z8, including:
  - `summary`
  - `clause_trends`
  - `behavior_insights`
  - `invariants`

Z0 must reject ingestion if:
- `z8_result.invariants.trend_consistency_ok` is False
- `summary.round_count <= 0`
- `summary.baseline_posture` or `summary.final_posture` is missing

#### 4.5.2 Storage & Schema

Z0 uses a SQLite database at `frontend/z0/z0_knowledge.db` with tables:

- **z0_deals:**
  - `deal_id` (PK), `counterparty_id`, `timestamp`
  - `round_count`, `baseline_posture`, `final_posture`, `trajectory`

- **z0_clause_history:**
  - `deal_id`, `counterparty_id`, `clause_id`
  - `stability`, `net_verdict`
  - `start_risk_score`, `end_risk_score`
  - `changes_count`, `missing_rounds_count`

- **z0_counterparty_metrics:**
  - `counterparty_id`, `deal_id`
  - `concessions_count`, `counterparty_leaning_changes`

All writes are append-only and idempotent per `deal_id`.

#### 4.5.3 APIs (Data Layer Only)

- `ingest_z8_result(deal_id, counterparty_id, timestamp, z8_result)`
  - Validates Z8 invariants, inserts rows into all three tables
  - Idempotent: skips if deal_id already exists

- `get_counterparty_profile(counterparty_id)` returns:
  - `deal_count`, `posture_distribution`, `trajectory_distribution`
  - `avg_concessions_per_deal`, `avg_counterparty_leaning_changes`
  - `top_risky_clauses` (most frequent 'Worse' verdicts)

- `get_clause_profile(clause_id)` returns:
  - `occurrences`, `stability_distribution`, `net_verdict_distribution`
  - `avg_start_risk_score`, `avg_end_risk_score`

- `get_portfolio_summary()` returns:
  - `total_deals`, `final_posture_distribution`, `trajectory_distribution`

- `get_top_risky_clauses(limit=5)` returns:
  - List of clauses with most 'Worse' verdicts

- `get_top_aggressive_counterparties(limit=5)` returns:
  - List of counterparties by total `counterparty_leaning_changes`

These APIs provide structured Python dictionaries suitable for consumption
by other zones or reporting tools. Z0 does not provide a UI surface in v1.

#### 4.5.4 Testing

**Test:** `frontend/tests/z0_ingest_test.py`
- Verifies:
  - Ingestion creates rows in all three tables
  - Idempotence: re-ingesting same deal_id does not duplicate
  - Profile queries return expected aggregates
  - Invalid Z8 results are rejected
- Run:
  - `python frontend/tests/z0_ingest_test.py`

**CAI enforces:**
- Canonical semantics (no redefinition of weights / thresholds)
- Ingestion invariants
- Append-only behavior

### 4.6 Z9 – Contract Playbook Synthesis Zone

**Framework:**
- implements: Z-Framework v1.1.1
- archetype: Z-Decision (Synthesis)

**Purpose:**
Synthesize insights from all upstream zones (Z0–Z8) into a unified negotiation
playbook providing final posture assessment, prioritized action items,
scenario-based recommendations, and an executive summary for decision-makers.

#### 4.6.1 Implementation

- **Code:** `frontend/pages/5_📝_Redline_Reviews.py`
  - Function: `z9_playbook_synthesis()`
  - Wired into the zone layout as:
    - `z9=z9_playbook_synthesis` (full-width below Z8)

- **Data Inputs (read-only):**
  - `st.session_state["redline_result"]` – clause data from Z1-Z3
  - `st.session_state["z8_result"]` – cross-document intelligence from Z8
  - `st.session_state["clause_decisions"]` – decisions logged in Z7
  - `st.session_state["z6_scenarios"]` – scenario outcomes from Z6

#### 4.6.2 Synthesis Outputs

Z9 produces six core synthesis artifacts:

1. **Final Posture Assessment (Section A)**
   - Aggregated posture from all data sources
   - Uses canonical posture thresholds:
     - High Risk: red_pct > 40%
     - Moderate: red_pct > 20%
     - Favorable: green_pct > 60%
     - Balanced: otherwise
   - Includes trajectory if Z8 data available

2. **Risk Concentration Analysis (Section B)**
   - Groups clauses by category keywords:
     - Financial: payment, price, fee, cost
     - Liability: liability, indemnity, indemnification, limitation
     - Operational: termination, renewal, sla, service level
     - Compliance: audit, compliance, confidential, data
   - Shows per-category risk distribution

3. **Top 5 Negotiation Priorities (Section C)**
   - Highest risk clauses prioritized by risk_score
   - Each entry includes: clause ID, title, impact, shift, rationale
   - Priority pills (P1–P5) for quick reference

4. **Scenario Delta Calculations (Section D)**
   - If Z6 scenarios exist, computes delta from baseline
   - Shows risk improvement/degradation per scenario
   - Recommends optimal scenario based on risk reduction

5. **Recommendations Engine (Section E)**
   - Rule-based recommendations keyed by:
     - Posture state (High Risk, Moderate, Favorable, Balanced)
     - Category concentration
     - Decision history from Z7
   - Actionable guidance for negotiation team

6. **Executive Narrative Summary (Section F)**
   - 2-3 paragraph synthesis suitable for leadership
   - Covers: overall posture, key risks, recommended actions
   - Generated from upstream data, not invented

#### 4.6.3 Risk Model & Semantics

Uses canonical Z-Framework v1.1.1 weights:

- **Impact weights:** low=1, medium=2, high=3
- **Shift weights:** favors_customer=0.5, balanced=1.0, favors_counterparty=1.5
- **Risk score:** `impact_weight × shift_weight`
- **RAG thresholds:** Red ≥4.0, Amber 2.0–3.99, Green <2.0
- **Posture thresholds:**
  - High Risk: red_pct > 40%
  - Moderate: red_pct > 20%
  - Favorable: green_pct > 60%
  - Balanced: otherwise

Z9 MUST NOT redefine these semantics.

#### 4.6.4 UI & Theming

- Uses scoped CSS classes:
  - `.z9-wrapper`, `.z9-section`, `.z9-title`, `.z9-subtitle`
  - `.z9-posture-card`, `.z9-posture-indicator`
  - `.z9-risk-bar`, `.z9-category-row`
  - `.z9-priority-item`, `.z9-priority-pill`
  - `.z9-scenario-card`, `.z9-delta-indicator`
  - `.z9-recommendation-item`
  - `.z9-narrative-block`
  - `.z9-pill-red`, `.z9-pill-amber`, `.z9-pill-green`, `.z9-pill-neutral`

- Semantic colors use theme tokens with fallbacks:
  - Danger: `var(--color-status-danger-bg)`, `var(--color-status-danger-light)`
  - Warning: `var(--color-status-warning-bg)`, `var(--color-status-warning-light)`
  - Success: `var(--color-status-success-bg)`, `var(--color-status-success-light)`

- Neutral surfaces: `#1A1A1A`, `#222`, `#333`

- Accessibility:
  - No color-only signaling; all pills/indicators have text labels
  - Text contrast meets WCAG AA (≥4.5:1)
  - Responsive layout survives 375px width

#### 4.6.5 Tests & Validation

**Smoke Test:** `frontend/tests/z9_smoke_test.py`
- Verifies:
  - Page module imports
  - `z9_playbook_synthesis()` exists
- Run:
  - `python frontend/tests/z9_smoke_test.py`

**Compliance Requirements:**
- Uses canonical risk model (impact/favor weights, posture thresholds)
- Must not mutate upstream session state
- Read-only access to Z0-Z8 outputs
- CSS scoped under `.z9-*` and theme-tokenized
- CAI/GEM WARN or FAIL = BLOCK

### 4.7 Agent Governance v1.1.1

**Framework:**
- implements: Z-Framework v1.1.1
- scope: GPT, CAI, GEM, CC, AGENT–U (UserAgent)
- objective: maximize VALUE = Benefit / (Risk + Complexity) while enforcing strict blocking

**Agent Roles:**
- **GPT (Planner / Orchestrator)**
  Designs zones, frameworks, and packets. Produces high-level specs and intent.
  Must not emit oversized CC-PACKETs when an atomic alternative exists.

- **CAI (Semantic + Structural Authority)**
  Validates GPT intent and packets for semantic correctness and alignment with Z-Framework.
  Compresses and scopes changes into atomic CC-PACKETs (1–3 files, minimal diffs).
  Issues PASS / WARN / FAIL. WARN or FAIL = BLOCK until remediated.

- **GEM (UI / A11y / Presentation Governor)**
  Validates CSS, theme tokens, contrast, non-color signaling, and layout.
  Ensures packets are structurally clean and not bloated.
  Issues PASS / WARN / FAIL for any UI/UX or presentation concern. WARN or FAIL = BLOCK.

- **CC (Implementation Engine)**
  Applies only CAI-approved packets.
  Performs atomic edits, runs tests, and reports STATUS (files, line ranges, tests).
  Never asks the user questions; escalates ambiguity to CAI.

- **AGENT–U (UserAgent)**
  Acts as strategic evaluator for VALUE and CONFIDENCE.
  Uses [FEEDBACK], [CONSIDER], [SUGGEST], [CONFIRM] to steer or approve.
  The only agent allowed to override or veto agent behavior.

**Unified Execution Loop:**
1. GPT designs and proposes changes (zones, frameworks, automation).
2. CAI validates, compresses, and scopes into an atomic CC-PACKET.
3. GEM validates UI/A11y/structure and may require refinements.
4. CC executes the packet (edit → test → STATUS report).
5. CAI verifies final compliance with Z-Framework and automation rules.
6. AGENT–U reviews the outcome and issues [CONFIRM] or [FEEDBACK]/[CONSIDER]/[SUGGEST].

**Blocking Rules (v1.1.1):**
- Any WARN or FAIL from CAI or GEM on a zone/framework change = BLOCK for CC.
- CC must not implement changes until CAI and GEM both PASS for that packet.
- Only GPT can issue a revised packet to clear a BLOCK.
- AGENT–U can veto any packet or outcome at any time.

**Packet Governance:**
- Default maximum packet size: ≤ 400 lines, with a target of ≤ 200 lines.
- Scope: 1–3 files per packet, atomic to a single feature or fix.
- CAI must prefer pattern reuse (referencing existing code/tests) over full rewrites.
- GEM may require packet splitting when structural complexity or readability is at risk.

This governance applies to all current zones (Z0–Z8) and any future zones (Z9+), as well as future framework versions (v1.2+), unless superseded.

**Full Specification:** See `CIP_Agent_Governance_v1.1.1.md`

## 5. Future Sections

Reserved for additional governance content.
