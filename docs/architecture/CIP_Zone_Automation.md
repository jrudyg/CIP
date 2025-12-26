# CIP Zone Automation Layer (Z-Framework v1.1.1)

**Purpose:**
Define the automation, enforcement, and agent workflow rules that govern all Z-zones (Z1–Z∞) under Z-Framework v1.1.1, with STRICT blocking:
> No CC merge is allowed if CAI or GEM report WARN or FAIL.

This document sits alongside `CIP_Zone_Framework.md` and operationalizes it.

**Agent Governance:**
See `CIP_Agent_Governance_v1.1.1.md` for the complete multi-agent coordination protocol.

---

## 1. Scope

The Automation Layer applies to:

- All Z-zones covered by `CIP_Zone_Framework.md` (Z0, Z2–Z8 and future).
- All edits in `frontend/pages/5_📝_Redline_Reviews.py` that touch Z-zones.
- All future pages that declare `implements: Z-Framework v1.1.1`.

It governs the behavior of four agents:

- GPT (Architect + Planner + Orchestrator)
- CAI (Semantic + Structural Authority)
- GEM (Visual, A11y, and Presentation Governor)
- CC (Implementation Engine)

**Value Function:** All agent decisions maximize `VALUE = Benefit / (Risk + Complexity)`

---

## 2. Agent Automation Governance v1.1.1

**implements:** Z-Framework v1.1.1
**scope:** GPT, CAI, GEM, CC, AGENT–U
**objective:** Provide deterministic, auditable automation for packet-based zone evolution.

### 2.1 Multi-Agent Pipeline Contract

1. **GPT (Planner / Architect)**
   Produces high-level zone/framework packets.

2. **CAI (Semantic + Structural Authority)**
   - Validates packet alignment to Z-Framework
   - Compresses into atomic CC-PACKET (≤ 3 files, ≤ 400 lines)
   - Emits PASS / WARN / FAIL
   - WARN or FAIL → BLOCK

3. **GEM (A11y / UI / Structure Governor)**
   - Validates UI, theme tokens, layout, and downstream presentation impact
   - Emits PASS / WARN / FAIL
   - WARN or FAIL → BLOCK

4. **CC (Implementation Engine)**
   - Applies CAI-approved packets
   - Runs tests
   - Outputs STATUS report
   - Never requests clarification from the user

5. **AGENT–U (UserAgent)**
   - Evaluates VALUE = Benefit / (Risk + Complexity)
   - Issues [CONFIRM], [FEEDBACK], [CONSIDER], [SUGGEST]
   - Only agent permitted to override outcomes

### 2.2 Blocking Rules

- Any WARN or FAIL from CAI or GEM = **BLOCK**
- CC executes only when **both** CAI and GEM return PASS
- GPT must produce a revised packet to unblock
- AGENT–U may veto at any stage

### 2.3 Automation Enforcement

For each packet:

1. CAI produces atomic CC-PACKET
2. GEM validates UI/structure
3. CC applies edits + tests
4. CAI verifies final compliance
5. AGENT–U issues final approval

Automation logs must include:
- File changes
- Line ranges
- PASS/WARN/FAIL
- Version implemented (Z-Framework v1.1.1)

### 2.4 Cross-File Consistency

All CIP docs must reference the same:
- Governance version
- Pipeline contract
- Blocking rules

Automation MUST verify:
- No doc references outdated governance
- No zone declares an older framework version

---

## 3. Strict Blocking Rule

**Canonical Rule:**

> A zone is **NOT** allowed to be marked complete, nor can related code be treated as merge-ready, if any CAI or GEM check returns WARN or FAIL.

Formally:

- CAI status:
  - PASS → Eligible to proceed
  - WARN → BLOCK
  - FAIL → BLOCK
- GEM status:
  - PASS → Eligible to proceed
  - WARN → BLOCK
  - FAIL → BLOCK

This applies to:

- New zones (Z8+)
- Major changes to existing zones (Z2–Z7)
- Any change that affects:
  - Risk semantics
  - Posture logic
  - RAG thresholds
  - A11y/theme behavior

---

## 3. Automation Workflow (GPT → CAI → GEM → CC)

### 3.1 GPT Phase (Spec & Packets)

GPT must:

1. Declare:
   - Zone archetype
   - Z-Framework version (must be v1.1 or higher)
2. Produce:
   - CC-PACKET(s) for file edits
   - CAI-PACKET for structural audit
   - GEM-PACKET for UI/A11y audit

GPT must NOT declare a zone "complete" until CAI and GEM both produce PASS with no WARN.

---

### 3.2 CAI Phase (Structural & Semantic Audit)

CAI must at minimum validate:

- Data invariants:
  - read-only access to upstream data
  - no invented clause_ids
- Semantic invariants:
  - impact/favor weights match framework
  - RAG thresholds match framework
  - posture semantics match framework
- Cross-zone consistency:
  - Z2 summary ↔ Z3 detail
  - Z4 risk model ↔ Z5 strategy view
  - Z5 posture ↔ Z6 posture baseline
  - Z6 outcome(s) ↔ Z7 decision log

**CAI Output Contract (per zone):**

- For each check:
  - PASS / WARN / FAIL
  - 1–3 sentence rationale
- Summary verdict:
  - Must be one of:
    - "PASS"
    - "WARN"
    - "FAIL"

**Strict Rule:**
- If CAI returns WARN or FAIL, CC must treat the zone as BLOCKED until fixes are implemented and CAI returns PASS.

---

### 3.3 GEM Phase (UI/A11y Audit)

GEM must validate:

- Theme token usage:
  - `var(--color-*)` for colors, no raw hex unless used as fallback.
- Contrast:
  - Text vs background must meet WCAG AA (≥ 4.5:1).
- Non-color signaling:
  - RAG states must include text labels, not color alone.
- Responsive behavior:
  - Layout remains legible at 375px width.
- Pill readability:
  - No overlapping or visually fused pills when wrapping.

**GEM Output Contract:**

- For each checked criterion:
  - PASS / WARN / FAIL
  - 1–3 sentence rationale
- Summary verdict:
  - "PASS" / "WARN" / "FAIL"

**Strict Rule:**
- If GEM returns WARN or FAIL, CC must treat the zone as BLOCKED until GEM returns PASS after remediation.

---

### 3.4 CC Phase (Execution & Enforcement)

CC responsibilities under v1.1:

- Execute GPT's CC-PACKET instructions.
- Ensure:
  - Zones are read-only wrt upstream data.
  - Smoke tests exist and pass.
  - Z-Framework docstrings are present and accurate.
  - CIP.md sections exist and match the implementation.

**Mandatory steps for any zone change:**

1. Apply code edits.
2. Run zone's smoke test:
   - `python frontend/tests/zX_smoke_test.py`
   - Exit code must be 0.
3. Provide STATUS report:
   - Files changed
   - Tests executed
   - Exit codes
4. Await CAI-PACKET and GEM-PACKET audits.
5. If CAI or GEM return WARN/FAIL:
   - Apply remediation CC-PACKETs.
   - Repeat tests and audits until both return PASS.

**STRICT Merge Safety:**

CC must NOT declare:

- "Zone complete"
- "Ready to merge"
- or similar language

unless:

- CAI verdict: PASS
- GEM verdict: PASS
- Smoke tests: all PASS (exit 0)

---

## 4. Z-Framework v1.1 Compliance Checklist (Per Zone)

For each zone, the following MUST be true:

1. Zone function docstring:
   - Includes:
     - `implements: Z-Framework v1.1`
     - `archetype: Z-<ArchetypeName>`
2. Zone semantics:
   - Impact weights, favorability weights, risk_score, RAG thresholds, posture logic match the framework.
3. CSS:
   - Namespaced `.zX-*`
   - Uses theme tokens for colors and borders.
4. Tests:
   - zX_smoke_test exists and passes.
5. Governance:
   - CIP.md has a section describing the zone under CC Operations.
6. CAI:
   - Most recent audit: PASS (no WARN/FAIL).
7. GEM:
   - Most recent audit: PASS (no WARN/FAIL).

If any item is missing or non-compliant → BLOCK.

---

## 5. Versioning and Upgrade Path

This Automation Layer is:

- **Z-Framework v1.1.1 – STRICT Automation & Blocking + Multi-Agent Governance**

Zones declaring `implements: Z-Framework v1.0.1` or `v1.1` are legacy and should be upgraded to v1.1.1 at the next significant change.

Upgrade rule:

- When modifying a legacy zone:
  - update docstring to `implements: Z-Framework v1.1.1`
  - ensure full compliance with:
    - `CIP_Zone_Framework.md`
    - `CIP_Zone_Automation.md`
    - `CIP_Agent_Governance_v1.1.1.md`

---

## 6. Agent Coordination Protocol

### 6.1 Execution Flow

```
GPT → CAI → GEM → CC → CAI (verify) → Complete
```

### 6.2 Non-Escalation Rule

Agents do NOT ask the user for guidance unless:
- The spec itself is contradictory
- Required information is provably missing

All ambiguity is resolved by CAI (semantic) or GEM (UI).

### 6.3 Packet Governance

| Constraint | Limit |
|------------|-------|
| Lines | < 400 (prefer < 200) |
| Files | 1-3 max |
| Scope | Atomic (single coherent change) |

---

## 7. Enforcement Summary (One-Line Rule)

> No Z-zone is considered complete or merge-ready unless:
> - Smoke tests PASS
> - CAI verdict = PASS
> - GEM verdict = PASS
> AND the zone declares `implements: Z-Framework v1.1.1`.

---

**End of CIP Zone Automation Layer (v1.1.1)**
