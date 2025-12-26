# CIP Zone Framework Specification (Z-Framework v1.1.1)

## Purpose

Define a reusable architecture, invariant set, and implementation contract for all CIP "Z-zones" (Z1–Z∞), ensuring consistency, auditability, accessibility, and agent-safe generation across the CIP platform.

---

## 1. Definition of a Zone

A **Zone** is a modular analytic component within the CIP Redline/Contract Intelligence system.

Every Zone must meet ALL of the following properties:

- **Single responsibility**
- **Deterministic** (same inputs → same outputs)
- **Read-only** (never mutates upstream state)
- **Composable** (fit into the zone_layout pipeline)
- **Exportable** (generate consistent JSON + Markdown)
- **Governed** (meets standards enforceable by CAI/GEM/CC)

---

## 2. Zone Lifecycle

Each Zone follows a seven-stage lifecycle:

| Stage | Description |
|-------|-------------|
| 1. Specification | Declare purpose, inputs, outputs, invariants. |
| 2. Data Model | Normalize/transform raw clauses into zone-specific structures. |
| 3. Semantic Logic | Compute risk, posture, priorities, simulations, etc. |
| 4. UI Construction | Build UI using CIP dark-theme standards + governed CSS classes. |
| 5. Accessibility Layer | Apply GEM rules: contrast, non-color signaling, responsiveness. |
| 6. Validation Layer | CAI audits: structural, semantic, cross-zone consistency. |
| 7. Testing Layer | CC smoke tests + invariant tests ensure zone correctness. |

A Zone is not considered "complete" unless all 7 layers are implemented.

---

## 3. Standard Input Contract

All Zones accept the same upstream redline data:

```python
redline_result = st.session_state.redline_result
```

Each clause entry must supply:

| Field | Required | Description |
|-------|----------|-------------|
| `clause_id` | Yes | Unique ID |
| `section_title` | Yes | Human-readable label |
| `change_type` | Yes | `inserted` / `removed` / `modified` |
| `impact` | Yes | `low` / `medium` / `high` |
| `position_shift` | Yes | `favors_customer` / `balanced` / `favors_counterparty` |
| `inline_diff` | Optional | Diff highlight string |
| `focus_first` | Optional | Boolean marker for Z2 |

**Zones must not mutate `redline_result` under any circumstance.**

Derived structures (Z4 risk model, Z5 strategy list, Z6 simulations, etc.) must be recalculable from these raw fields.

---

## 4. Standard Output Contract

Every Z-zone must output:

- **UI component** (Streamlit or equivalent)
- **Structured Python object** representing the zone's computed state
- **Invariant structure** used by CAI
- **Clean error surface** (errors returned, not thrown)

---

## 5. Universal Zone Invariants

These invariants apply to every Z-zone, current and future.

### 5.1 Data Invariants

- Upstream data is read-only.
- All clause references must originate from `redline_result`.
- All counts and percentages must be internally consistent.
- All metrics must be computable solely from upstream data.

### 5.2 Semantic Invariants

**Impact → weights:**
- `low` = 1
- `medium` = 2
- `high` = 3

**Favorability → weights:**
- `favors_customer` = 0.5
- `balanced` = 1.0
- `favors_counterparty` = 1.5

**Risk Score:**
```
risk_score = impact_weight × favorability_weight
```

**RAG thresholds (global constants):**
- Red ≥ 4.0
- Amber 2.0–3.99
- Green < 2.0

**Posture semantics (Z4–Z7 standard):**
```
High Risk:     red_pct > 40
Moderate:      red_pct > 20
Favorable:     green_pct > 60
Balanced:      otherwise
```

**These semantics must not be redefined by any Zone.**

**Implementation Note (v1.0.1):**
Earlier implementations of Z6 incorrectly used `red_pct < 20` to classify a deal as "Favorable."
The canonical posture rule is:

```
Favorable = green_pct > 60
```

All future zones must follow the canonical rule.
This note may be removed once all code paths comply with the correct posture semantics.

### 5.3 Accessibility (GEM) Invariants

All UI rendering must meet:

- WCAG AA contrast ratio ≥ 4.5:1
- Text labels always accompany colored elements
- All CSS must use theme tokens:
  - `var(--color-status-danger-light)`
  - `var(--color-status-warning-light)`
  - `var(--color-status-success-light)`
  - `var(--color-border-main)`
  - `var(--color-text-light)`
- Mobile stacking must remain readable
- CSS class names MUST follow `.zX-*` namespace rules

### 5.4 UI Invariants

All Zones must:

- Use dark surfaces (`#1A1A1A`, `#222`, `#333` equivalents via theme tokens)
- Use flex/column/grid layout for mobile survival
- Partition content into:
  - Header
  - Summary or primary content
  - Secondary insights or sub-panels
- Avoid global CSS leakage—Zone CSS must be scoped to `.zX-*`

### 5.5 Testing Invariants

Each Zone must ship with a smoke test:

```
frontend/tests/zX_smoke_test.py
```

It must:

- Import the page module dynamically
- Confirm zone function exists
- Run the function without Streamlit runtime context
- Exit non-zero on failure

Tests must always be runnable via:

```bash
python frontend/tests/zX_smoke_test.py
```

### 5.6 Standard Smoke Test Template

Every zone must include a smoke test following the template below.
This test MUST import the page without requiring a Streamlit runtime and MUST exit non-zero on failure.

```python
"""Smoke test for ZX zone"""

import sys
from pathlib import Path

# Add the frontend directory to the module path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_zX_exists():
    import pages.Redline_Reviews as page
    assert hasattr(page, "zX_zone_function"), "Zone function missing"
    print("✅ ZX function exists")

if __name__ == "__main__":
    try:
        test_zX_exists()
        sys.exit(0)
    except Exception as e:
        print(f"❌ ZX smoke test failed: {e}")
        sys.exit(1)
```

This template must be adapted for each zone by renaming ZX and the function name.

---

## 6. Canonical Zone Archetypes

The Z-Framework defines six reusable Zone types:

| Archetype | Definition | Example |
|-----------|------------|---------|
| Z-Summary | High-level metrics, micro-boards | Z2 |
| Z-Detail | Clause-by-clause details | Z3 |
| Z-Synthesis | Risk models, aggregation engines | Z4 |
| Z-Strategy | Negotiation strategy & guidance | Z5 |
| Z-Scenario | What-if modeling, tradeoff simulation | Z6 |
| Z-Decision | Final decision + export | Z7 |

New Zones must declare their archetype and must comply with its structural rules.

---

## 7. Folder & Governance Structure (Target Layout)

The following directory structure is the **target model** for all CIP Zone implementations.
CC must verify the structure exists before marking any zone complete.

```
CIP/
  CIP.md
  CIP_Zone_Framework.md

frontend/
  pages/
    5_📝_Redline_Reviews.py
  validators/
    redline_consistency.py   # Create if missing
  tests/
    z2_smoke_test.py         # Each zone must include its own test
    z3_smoke_test.py
    z4_smoke_test.py
    z5_smoke_test.py
    z6_smoke_test.py
    z7_smoke_test.py
```

Notes:
- Tests must be runnable with:
  `python frontend/tests/zX_smoke_test.py`
- Folder structure is enforceable by CAI.
- Missing folders must be created by CC when needed.

---

## 8. Agent-Oriented Workflow (GPT → CAI → GEM → CC)

### GPT (Planner)
- Writes specs
- Defines zone boundaries & invariants
- Produces CC packets for editing files

### CAI (Structural Validator)
- Validates:
  - Zone semantics
  - Cross-zone consistency
  - Invariant compliance
  - Export integrity

### GEM (UI/A11y Validator)

GEM validates:

- Theme token usage (`var(--color-*)`, no hardcoded hex)
- Text/background contrast ratio ≥ 4.5:1 (WCAG AA)
- Non-color signaling (RAG states must include explicit text labels)
- Responsive layout (must remain readable at 375px width)
- Pill readability and non-overlap on wrap

**Enforcement Rule:**
A GEM audit packet is required before ANY CC merge.
CC must correct ALL GEM WARN/FAIL findings before marking a zone complete.

### CC (Executor)
- Writes code
- Writes CSS
- Writes tests
- Updates CIP.md
- Must remain deterministic and idempotent

**All Zones must be created in compliance with this four-agent execution lifecycle.**

---

## 9. Export Semantics (JSON + Markdown)

Every export-capable Zone (Z7 and similar) must provide:

- **JSON export** with canonical keys
- **Markdown export** suitable for leadership review

Requirements:

- No reordering of clauses unless explicitly stated
- Export must reflect exact zone state
- No lossy transformations

---

## 10. Versioning

```
Z-Framework v1.1.1 — Strict Automation & Blocking + Multi-Agent Governance
```

Each new Zone must declare:

```
implements: Z-Framework v1.1.1
```

Future framework versions will be appended to a global governance file.

**Automation Note (v1.1.1):**
Operational enforcement, strict blocking rules, and agent workflows
for this framework are defined in:
- `CIP_Zone_Automation.md` - Automation layer and workflow rules
- `CIP_Agent_Governance_v1.1.1.md` - Multi-agent coordination protocol

All zones declaring `implements: Z-Framework v1.1.1` must comply with
this document, the automation layer, and the agent governance protocol.

### Zone Compliance Declaration

Every zone function MUST include a docstring declaring its framework version and archetype.

Example:

```python
def z7_decision_log_zone():
    """
    Z7: Decision & Export Zone
    implements: Z-Framework v1.1.1
    archetype: Z-Decision

    Invariants:
        - Uses canonical risk model
        - Read-only access to upstream data

    Data Contract:
        - Input: st.session_state["redline_result"]
        - Output: JSON/Markdown export
    """
```

CAI may scan docstrings to ensure compliance with the current framework version.

---

## 11. Agent Governance Binding (v1.1.1)

All zones (Z0–Z∞) and all automation steps MUST follow the multi-agent governance model:

### 11.1 Required Roles

- **GPT:** Planner / Architect
- **CAI:** Semantic + Structural Authority
- **GEM:** UI, Theme, A11y Governor
- **CC:** Implementation Engine
- **AGENT–U:** VALUE-based strategic overseer

### 11.2 Execution Loop

1. GPT produces packet
2. CAI validates + compresses
3. GEM validates UI/A11y
4. CC implements
5. CAI verifies
6. AGENT–U approves or redirects

### 11.3 Blocking & Enforcement

- WARN or FAIL from CAI/GEM = BLOCK
- Only GPT can unblock by issuing updated packet
- CC MUST NOT proceed without PASS
- AGENT–U can override at any time

### 11.4 Packet Governance

- Max packet size: ≤ 400 lines (target: ≤ 200)
- Max files per packet: ≤ 3
- Scope must remain atomic
- Reuse patterns instead of rewriting
- CAI/GEM may require packet splitting

### 11.5 Zone Compliance Declaration

Every zone function MUST declare:

```
implements: Z-Framework v1.1.1
archetype: <Zone Archetype>
```

### 11.6 Cross-Document Version Coherence

Automation MUST verify:
- CIP.md
- CIP_Zone_Automation.md
- CIP_Zone_Framework.md

All reference the exact framework version defined here.

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-11 | Initial Z-Framework |
| v1.0.1 | 2025-11 | Z6 posture bug fix, smoke test template |
| v1.1 | 2025-11 | Strict blocking rules, automation layer |
| v1.1.1 | 2025-12 | Multi-agent governance protocol, packet governance, AGENT–U role |

---

**End of Specification**
