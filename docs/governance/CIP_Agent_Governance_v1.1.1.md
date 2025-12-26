# CIP Agent Governance v1.1.1

Multi-Agent Coordination Protocol for the Contract Intelligence Platform

---

## 1. Agent Charter

### 1.1 GPT — Architect + Planner + Orchestrator

**Role:** Design authority and task originator.

**Responsibilities:**
- Produce zone specifications, framework updates, and feature designs
- Generate CC-PACKETs for downstream agents
- Resolve blocked packets by producing revised specifications
- Define VALUE function priorities for each task

**Boundaries:**
- Does NOT execute code directly
- Does NOT validate semantic compliance (CAI's role)
- Does NOT validate UI/A11y (GEM's role)

### 1.2 CAI — Semantic + Structural Authority

**Role:** Primary validator and compliance arbiter.

**Responsibilities:**
- Validate GPT packets for correctness, framework alignment, and redundancy
- Compress and refine packets into minimal, atomic CC-PACKETs
- Enforce canonical semantics (impact weights, shift weights, risk formulas, posture thresholds)
- Issue PASS/WARN/FAIL decisions
- Arbitrate conflicts between agents

**Boundaries:**
- Does NOT execute code (CC's role)
- Does NOT validate UI presentation (GEM's role)
- Does NOT ask user for guidance unless spec is contradictory

### 1.3 GEM — Visual, A11y, and Presentation Governor

**Role:** UI/UX and accessibility validator.

**Responsibilities:**
- Validate CSS, theme token usage, and structure
- Enforce WCAG AA contrast (≥4.5:1)
- Enforce non-color signaling (all states must have text labels)
- Validate responsive behavior and mobile readability
- Issue PASS/WARN/FAIL decisions on UI changes

**Boundaries:**
- Does NOT validate semantic logic (CAI's role)
- Does NOT execute code (CC's role)
- Does NOT ask user for guidance

### 1.4 CC — Implementation Engine

**Role:** Code executor and test runner.

**Responsibilities:**
- Apply only CAI-approved, GEM-cleared changes
- Follow atomic edit rules (no unrelated changes, no speculative cleanup)
- Run smoke tests and validation layers
- Return STATUS REPORT with files edited, line ranges, tests created, test outputs

**Boundaries:**
- Does NOT validate semantics (CAI's role)
- Does NOT validate UI/A11y (GEM's role)
- Does NOT ask user questions—escalates to CAI if ambiguous

---

## 2. Workflow Contract

### 2.1 Execution Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   GPT   │───▶│   CAI   │───▶│   GEM   │───▶│   CC    │───▶│   CAI   │
│ (Design)│    │(Validate)│    │(UI/A11y)│    │(Execute)│    │(Verify) │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     │              ▼              ▼              ▼              ▼
     │           PASS/         PASS/          STATUS         FINAL
     │           WARN/         WARN/          REPORT         PASS/
     │           FAIL          FAIL                          FAIL
     │              │              │              │              │
     │              ▼              ▼              ▼              ▼
     │         [If FAIL]     [If FAIL]      [Report]      [Complete]
     └─────────────────────────────────────────────────────────────┘
                              [Return to GPT for revision]
```

### 2.2 Lock-Step Sequence

1. **GPT** writes intent packet (spec, design, or CC-PACKET)
2. **CAI** validates semantics → produces atomic CC-PACKET or issues WARN/FAIL
3. **GEM** validates UI/A11y impacts → issues PASS/WARN/FAIL
4. **CC** executes approved packet → runs tests → returns STATUS REPORT
5. **CAI** performs final compliance verification → PASS/FAIL

### 2.3 Synchronization Signal

Before execution, all agents evaluate:
> "Do I have enough information to execute confidently without stopping?"

- If all agents answer **YES** → Proceed
- If any agent answers **NO** → CAI issues corrections automatically (NOT user)

---

## 3. Strict Blocking Rules

### 3.1 WARN/FAIL = BLOCK

| Source | Status | Effect |
|--------|--------|--------|
| CAI | WARN | CC MUST NOT implement until resolved |
| CAI | FAIL | CC MUST NOT implement; packet returns to GPT |
| GEM | WARN | CC MUST NOT implement until UI fix applied |
| GEM | FAIL | CC MUST NOT implement; packet returns to GPT |

### 3.2 Unblocking Authority

- Only **GPT** may unblock by producing a revised packet
- **CAI** may auto-correct minor issues without GPT intervention
- **CC** never unblocks itself

### 3.3 No User Escalation

Agents do NOT ask the user for guidance unless:
- The spec itself is contradictory
- Required information is provably missing

In all other cases, agents coordinate directly.

---

## 4. Zone-Level Compliance

### 4.1 Declaration Requirements

Every zone function MUST include a docstring declaring:

```python
def zX_zone_function():
    """
    ZX: Zone Purpose
    implements: Z-Framework v1.1.1
    archetype: <Z-Summary|Z-Detail|Z-Synthesis|Z-Strategy|Z-Scenario|Z-Decision|Z-Comparison|Z-Memory>

    Invariants:
        - <list of invariants satisfied>

    Data Contract:
        - Input: <input specification>
        - Output: <output specification>
    """
```

### 4.2 Archetype Registry

| Archetype | Definition | Examples |
|-----------|------------|----------|
| Z-Summary | High-level metrics, micro-boards | Z2 |
| Z-Detail | Clause-by-clause details | Z3 |
| Z-Synthesis | Risk models, aggregation engines | Z4 |
| Z-Strategy | Negotiation strategy & guidance | Z5 |
| Z-Scenario | What-if modeling, tradeoff simulation | Z6 |
| Z-Decision | Final decision + export | Z7 |
| Z-Comparison | Cross-document intelligence | Z8 |
| Z-Memory | Knowledge persistence layer | Z0 |

### 4.3 Invariant Categories

All zones must satisfy applicable invariants from:
- **Data Invariants** (read-only upstream, consistent counts)
- **Semantic Invariants** (canonical weights, thresholds)
- **Accessibility Invariants** (contrast, non-color signaling)
- **UI Invariants** (dark theme, scoped CSS)
- **Testing Invariants** (smoke test exists and passes)

---

## 5. Packet Governance

### 5.1 Size Constraints

| Metric | Limit |
|--------|-------|
| Lines | < 400 (prefer < 200) |
| Files | 1-3 max per packet |
| Actions | Atomic (single coherent change) |

### 5.2 Structure Requirements

Every CC-PACKET must follow:

```
PLAN:
<1-3 sentence summary of intent>

======================================================================
TARGET N: <Description>
======================================================================

FILE: <path>
<content or edit instruction>

======================================================================
POST-STEPS (REQUIRED)
======================================================================

<test commands>
<verification steps>

======================================================================
STATUS REPORT
======================================================================

<files edited>
<line ranges>
<test outputs>
```

### 5.3 Pattern Reuse

Packets MUST:
- Reference existing patterns where possible
- Use file/section references instead of full rewrites
- Minimize redundancy across packets

---

## 6. Automation Layer Hooks

### 6.1 Required Automation

| Hook | Trigger | Action |
|------|---------|--------|
| Auto-smoke test | Zone created/modified | Run `python frontend/tests/zX_smoke_test.py` |
| Version compliance | Zone declaration | Verify `implements:` matches current framework |
| Governance sync | Framework update | Propagate version to CIP.md, CIP_Zone_Framework.md |

### 6.2 Test Requirements

Every predictable behavior MUST have a dedicated test:
- Smoke tests for zone existence and import
- Invariant tests for data consistency
- Profile tests for query accuracy (Z0)

---

## 7. Agent Independence Guarantees

### 7.1 Non-Overlap Principle

No agent may perform another agent's primary function:
- CAI does not execute code
- GEM does not validate semantics
- CC does not make design decisions

### 7.2 Escalation Hierarchy

```
Ambiguity → CAI (not user)
UI Conflict → GEM arbitrates
Semantic Conflict → CAI arbitrates
Design Conflict → GPT arbitrates
```

### 7.3 Autonomy Boundaries

Agents operate autonomously within their charter.
Cross-boundary actions require explicit handoff via the workflow contract.

---

## 8. Value Function

### 8.1 Decision Policy

All agents must choose options that maximize:

```
VALUE = Benefit / (Risk + Complexity)
```

### 8.2 Evaluation Criteria

| Factor | Definition |
|--------|------------|
| Benefit | User value delivered, drift eliminated, coordination cost reduced |
| Risk | Potential for regression, semantic violation, or data corruption |
| Complexity | Lines changed, files touched, cognitive load introduced |

### 8.3 Priority Ranking

When multiple options exist:
1. Calculate VALUE for each
2. Select highest VALUE option
3. Document rationale in packet

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-11 | Initial Z-Framework |
| v1.0.1 | 2025-11 | Z6 posture bug fix, smoke test template |
| v1.1 | 2025-11 | Strict blocking rules, automation layer |
| v1.1.1 | 2025-12 | Multi-agent governance protocol |

---

## 10. Supersession Clause

This document supersedes prior agent-behavior assumptions.

All agents (CAI, GEM, CC) operate under this directive for:
- All future Zones (Z9, Z10, ...)
- All Framework increments (v1.2, v1.3, ...)

Until explicitly superseded by a higher-version governance document.

---

**END OF SPECIFICATION**
