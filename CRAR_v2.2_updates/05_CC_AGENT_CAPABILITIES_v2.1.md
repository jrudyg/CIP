# 05_CC_AGENT_CAPABILITIES v2.1

**Version:** 2.1
**Date:** January 18, 2026
**Status:** Production Ready
**Purpose:** Reference for Claude.ai integration - replicate Claude Code agent behaviors

---

## VERSION 2.1 CHANGES

### From v2.0 → v2.1
- Added Phase 2.5.1: UCC Statutory Conflict Detection to contract-risk agent workflow
- Added 7th risk category: **Statutory Risk** (UCC violations)
- Updated pattern count references: 87 → 113 (26 UCC statutory rules added)
- Added UCC Violations section to output template
- Updated Pattern Library cross-reference map to include Part 8 (UCC)
- Integration with 40% statutory weight formula for risk scoring

### From v1.x → v2.0
- Updated to Pattern Library v2.0 (87 patterns)
- Added Phase 7: QA/QC Validation
- Enhanced Displacement Cascade integration (Phase 1.5.1)
- Added Outcome Tracking integration (post-negotiation)
- Added Attribution requirements (all recommendations must cite patterns)
- Expanded contract-type-specific checklists (Channel Partner, NDA, IPA/SOW)

---

## OVERVIEW

### Purpose
This document serves as the **authoritative reference** for Claude.ai Projects to replicate Claude Code agent capabilities in contract analysis. It bridges the gap between Claude Code's specialized agents and Claude.ai's general-purpose environment.

### Core Agents (5 Total)

| Agent | Purpose | Primary Patterns | Outcome |
|-------|---------|------------------|---------|
| **contract-risk** | Complete contract risk analysis | 2.1.x, 2.2.x, 2.10.x, Part 6, Part 7, **Part 8** ⚠️ NEW | Risk matrix + recommendations |
| **clause-compare** | Version comparison / redline | All Part 2, 3.1-3.2, 3.9-3.12 | Change impact analysis |
| **contract-summary** | Executive summary generation | All | High-level overview |
| **negotiation-advisor** | Counter-proposal strategy | All (fallbacks in Part 5) | Position guidance |
| **compliance-check** | Regulatory/policy compliance | 2.1.1, 2.2.1, 2.8.2, 3.1.1, **Part 8** ⚠️ NEW | Compliance status |

### CAI + CC Protocol (9 Steps)

When Claude.ai user uploads contract, follow this protocol:

1. **Classification:** Identify contract type (NDA/MSA/IPA/SOW/etc.)
2. **Agent Selection:** Map to appropriate agent workflow
3. **Execution:** Run agent's full workflow (8 phases for contract-risk)
4. **Output Generation:** Format per agent template
5. **Pattern Attribution:** Link recommendations to Pattern Library
6. **Confidence Check:** Verify ≥ 91% confidence
7. **QA/QC Validation:** Run Phase 7 checklist
8. **Presentation:** Deliver formatted report
9. **Outcome Tracking:** Log results post-negotiation (if applicable)

---

### Cross-Validation Protocol (V2+ Contracts)

When user provides both:
- **V1** (original contract)
- **V2** (counterparty redline)

**Mandatory steps:**
1. Run contract-risk on V1
2. Run clause-compare on V1 vs. V2
3. Cross-validate risks identified in both
4. Calculate capture rate: (Risks in V2 / Risks in V1)
5. Flag gaps (in V1, not V2)
6. Explain any V1 risks missed in V2

**Output:** Comprehensive V2 report + alignment section

---

## CONTRACT TYPE TAXONOMY

### 10-Type System

| Code | Full Name | Typical Duration | Detection Rules |
|------|-----------|------------------|-----------------|
| **NDA** | Non-Disclosure Agreement | 2-5 years | "confidential", one-way disclosure |
| **MNDA** | Mutual Non-Disclosure Agreement | 2-5 years | "mutual", two-way disclosure |
| **MSA** | Master Services Agreement | 1-5 years | "SOW", "purchase order", framework |
| **IPA** | Individual Project Agreement | 6-18 months | Standalone project scope |
| **SOW** | Statement of Work | 3-12 months | References MSA, specific deliverables |
| **CHGORD** | Change Order | N/A | Modifies SOW/IPA |
| **AMEND** | Amendment | N/A | Modifies base agreement |
| **VERSION** | Version (V1, V2, V3...) | N/A | Negotiation iterations |
| **PO** | Purchase Order | N/A | Procurement/supply |
| **MOU** | Memorandum of Understanding | N/A | Pre-contractual, non-binding |

### Detection Logic

**Step 1:** Search title for type indicator
**Step 2:** Search for structure keywords:
- MSA: "individual project agreement", "purchase order"
- IPA: "scope of work", standalone deliverable
- SOW: "this SOW is subject to MSA dated..."
- NDA/MNDA: "confidential information", "disclosing party"

**Step 3:** Default to MSA if ambiguous commercial contract

---

## AGENT 1: contract-risk

### Full 9-Phase Workflow ⚠️ UPDATED v2.1

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: PRIOR REPORT CHECK (If Version > 1)                   │
├─────────────────────────────────────────────────────────────────┤
│ □ User provided prior report?                                   │
│ □ Read prior findings completely                                │
│ □ Note issues to cross-validate in Phase 6                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: CONTEXT EXTRACTION                                     │
├─────────────────────────────────────────────────────────────────┤
│ □ Contract type (NDA/MSA/IPA/SOW/etc.)                          │
│ □ Parties (who is buyer, who is seller)                         │
│ □ Term/duration                                                 │
│ □ Payment structure (upfront/milestone/Net 30)                  │
│ □ Scope summary (1-2 sentences)                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1.5: COMPETITOR-SUPPLIER DETECTION (NEW v2.0)             │
├─────────────────────────────────────────────────────────────────┤
│ CRITICAL: Does supplier ALSO offer SI/integration services?     │
│                                                                 │
│ □ Supplier provides systems integration?      [YES/NO]          │
│ □ Supplier sells directly to end-customers?   [YES/NO]          │
│ □ Could supplier bypass you post-intro?       [YES/NO]          │
│                                                                 │
│ IF YES to any → COMPETITOR-SUPPLIER = Apply displacement lens   │
│ IF NO → Standard supplier = Skip to Phase 1.5.1                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1.5.1: DISPLACEMENT CASCADE (If Competitor-Supplier)      │
├─────────────────────────────────────────────────────────────────┤
│ Score 4 components (Favors Us / Favors Them / N/A):             │
│                                                                 │
│ 1. TERRITORY DEFINITIONS:                                       │
│    □ Exclusive territory defined for you?      [Us/Them/N/A]    │
│    □ Territory modification unilateral or mutual? [Criteria]    │
│                                                                 │
│ 2. CUSTOMER DATA ACCESS:                                        │
│    □ Do reporting requirements reveal customer identity?        │
│    □ Can supplier identify high-value targets from your data?   │
│                                                                 │
│ 3. TRANSITION PROVISIONS:                                       │
│    □ Post-termination customer handoff language exists?         │
│    □ Does supplier gain relationship upon exit?                 │
│                                                                 │
│ 4. POST-TERMINATION PROTECTION GAPS:                            │
│    □ Customer protection period < 24 months?                    │
│    □ No commission on direct sales after intro?                 │
│                                                                 │
│ SCORING:                                                        │
│ • Components Favor Them: [X/4]                                  │
│ • IF ≥3 favor them → ESCALATE AS DEALBREAKER                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXHIBIT REVIEW                                         │
├─────────────────────────────────────────────────────────────────┤
│ □ Pricing/rate schedules (hourly rates, unit prices)            │
│ □ Insurance requirements (coverage types, amounts)              │
│ □ SOW templates (if MSA)                                        │
│ □ Service Level Agreements (SLAs)                               │
│ □ Acceptance criteria (objective vs. subjective)                │
│                                                                 │
│ FLAG: Missing critical exhibits (insurance, SLA, acceptance)    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2.5: DEFINITIONS REVIEW                                   │
├─────────────────────────────────────────────────────────────────┤
│ □ "Confidential Information" defined? (scope/exclusions)        │
│ □ "Force Majeure" defined? (check for overbroad triggers)       │
│ □ "Material Breach" defined? (objective criteria?)              │
│ □ "Intellectual Property" / "Work Product" defined?             │
│ □ "Affiliate" defined? (impacts assignment rights)              │
│ □ "Business Day" defined? (impacts cure periods)                │
│ □ "Gross Negligence" defined? (indemnity threshold)             │
│                                                                 │
│ IF CRITICAL DEFINITION MISSING → Flag for addition before sign  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2.5.1: UCC STATUTORY CONFLICT DETECTION ⚠️ NEW v2.1     │
├─────────────────────────────────────────────────────────────────┤
│ Check contract clauses against Delaware UCC Article 2:          │
│                                                                 │
│ □ Load UCC rules from Part 8 Pattern Library (26 rules)         │
│ □ For each clause, match text against trigger concepts          │
│ □ If match found, extract:                                     │
│   • Rule ID (e.g., UCC-2-719)                                   │
│   • Severity (CRITICAL/HIGH/MEDIUM)                             │
│   • Risk Multiplier (5.0-10.0)                                  │
│   • Matched concepts (keywords that triggered detection)        │
│                                                                 │
│ UCC RULES BY CATEGORY:                                         │
│ • UCC-2-719: Remedy Limitations (consequential damages)         │
│ • UCC-2-302: Unconscionability (prepayment traps)               │
│ • UCC-2-314/2-316: Warranty Disclaimers (AS IS)                 │
│ • UCC-2-717: Deduction Rights (no set-off clauses)              │
│ • UCC-2-313/2-315: Express/Fitness Warranties                   │
│ • SI-001 to SI-008: Systems Integrator Flow-Down Gaps           │
│                                                                 │
│ RISK SCORE ESCALATION:                                         │
│ If UCC violation detected:                                     │
│   Final Score = (Base Score × 0.6) + (Risk Multiplier × 0.4)   │
│                                                                 │
│ Example:                                                        │
│   Base Score: 6.8 (from severity/complexity/impact)            │
│   UCC Multiplier: 10.0 (UCC-2-719 detected)                    │
│   Final Score: (6.8 × 0.6) + (10.0 × 0.4) = 8.08              │
│   Result: MEDIUM → HIGH risk escalation                        │
│                                                                 │
│ IF UCC VIOLATION DETECTED → Add to risk matrix + output        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: THREE-LENS RISK ANALYSIS                               │
├─────────────────────────────────────────────────────────────────┤
│ □ Score all 7 risk categories (1-5) ⚠️ UPDATED v2.1           │
│ □ Apply Conservative / Moderate / Relationship lenses           │
│ □ Identify TOP 5 risks with exposure quantification             │
│ □ Include cost impacts where calculable                         │
│                                                                 │
│ IF COMPETITOR-SUPPLIER DETECTED:                                │
│ → Weight displacement risk 2x in scoring                        │
│ → Flag any provision that benefits them more than you           │
│                                                                 │
│ IF UCC VIOLATIONS DETECTED:                                     │
│ → Escalate risk scores using 40% statutory weight               │
│ → Flag statutory violations as high-priority risks              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: MANDATORY COMBINED TRIGGER CHECKLIST                   │
├─────────────────────────────────────────────────────────────────┤
│ Run ALL triggers as explicit Y/N - do not skip                  │
│                                                                 │
│ TRIGGER A (Vendor Displacement):                                │
│   □ No customer protection?                    [Y/N]            │
│   □ Competitor assignment permitted?           [Y/N]            │
│   □ Direct warranty to customer?               [Y/N]            │
│   → ALL Y = DEALBREAKER                                         │
│                                                                 │
│ TRIGGER B (Uninsurable Liability):                              │
│   □ No liability cap / unlimited?              [Y/N]            │
│   □ One-sided indemnification?                 [Y/N]            │
│   □ No flowdown possible?                      [Y/N]            │
│   → ALL Y = DEALBREAKER                                         │
│                                                                 │
│ TRIGGER C (Cash Flow Death):                                    │
│   □ Payment 100% upfront required?             [Y/N]            │
│   □ No milestone structure?                    [Y/N]            │
│   □ No wind-down provisions?                   [Y/N]            │
│   → ALL Y = DEALBREAKER                                         │
│                                                                 │
│ TRIGGER F (Channel Partner Squeeze) - ENHANCED v2.0:            │
│   □ Supplier controls pricing?                 [Y/N]            │
│   □ Weak/no customer protection?               [Y/N]            │
│   □ Vague performance quotas?                  [Y/N]            │
│   □ No commission on direct sales?             [Y/N]            │
│   □ Term < 24 months without auto-renewal?     [Y/N]            │
│   → 4+ Y = DEALBREAKER                                          │
│                                                                 │
│ TRIGGER G (Design-Build Phase Trap):                            │
│   □ Design phase contract?                     [Y/N]            │
│   □ Work-for-hire IP transfer?                 [Y/N]            │
│   □ No phase-gating on IP?                     [Y/N]            │
│   □ No implementation leverage preserved?      [Y/N]            │
│   → ALL Y = DEALBREAKER                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: SECONDARY RISK SWEEP (EXPANDED v2.0)                   │
├─────────────────────────────────────────────────────────────────┤
│ After TOP 5, scan for operational/cost items:                   │
│                                                                 │
│ STANDARD SWEEP:                                                 │
│ □ Insurance tail period (cost impact)                           │
│ □ Audit frequency/scope (operational burden)                    │
│ □ Subcontracting restrictions (flexibility)                     │
│ □ Notice period requirements (operational)                      │
│ □ Reporting obligations (administrative burden)                 │
│ □ Compliance certifications required (SOC, ISO - cost)          │
│ □ Response time requirements (SLA risk)                         │
│ □ Travel/expense limitations (margin impact)                    │
│                                                                 │
│ EXPANDED SWEEP:                                                 │
│ □ Jurisdiction/venue (home court advantage for them?)           │
│ □ Warranty exclusion breadth (vague causation standards?)       │
│ □ IP transfer/sublicensing rights (can you serve customers?)    │
│ □ Scope limitation/interface clauses (disclaimer detection)     │
│ □ Term duration vs. investment recovery (ROI viability)         │
│ □ Consequential damages carve-outs (critical exclusions?)       │
│ □ Financial disclosure requirements (competitive exposure)      │
│                                                                 │
│ Flag items with:                                                │
│ • Annual cost impact > $10K                                     │
│ • Operational burden > 20 hours/month                           │
│ • Compliance gap vs. current capabilities                       │
│ • Competitive information exposure (if competitor-supplier)     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: CROSS-VALIDATION (If Prior Report Available)           │
├─────────────────────────────────────────────────────────────────┤
│ □ Compare findings against prior report                         │
│ □ Note alignment (✅) or gaps (❌)                               │
│ □ Calculate capture rate: Issues Found / Prior Issues           │
│ □ Explain any differences in assessment                         │
│ □ Reconcile combined trigger identification                     │
│ □ Document solution variants (where prior was better)           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 7: QA/QC VALIDATION ⚠️ NEW v2.0                          │
├─────────────────────────────────────────────────────────────────┤
│ SELF-AUDIT CHECKLIST (Before Presenting Report):                │
│                                                                 │
│ COMPLETENESS:                                                   │
│ □ All 9 phases executed? ⚠️ UPDATED v2.1                       │
│ □ All 5 triggers explicitly answered Y/N?                       │
│ □ Competitor lens applied (if applicable)?                      │
│ □ Displacement cascade checked (if applicable)?                 │
│ □ UCC statutory violations checked? ⚠️ NEW v2.1                │
│ □ Missing definitions flagged?                                  │
│                                                                 │
│ ACCURACY:                                                       │
│ □ Section numbers verified against document?                    │
│ □ Risk scores justified with specific clause text?              │
│ □ Pattern references correct (check Part 2/3/8 numbers)?        │
│ □ UCC risk multipliers applied correctly? ⚠️ NEW v2.1          │
│ □ No assumptions made without evidence?                         │
│                                                                 │
│ ATTRIBUTION:                                                    │
│ □ Each recommendation linked to Pattern Library pattern?        │
│ □ Success rate cited for each pattern?                          │
│ □ Source noted for non-standard recommendations?                │
│ □ UCC rules cited with risk multipliers? ⚠️ NEW v2.1           │
│                                                                 │
│ ACTIONABILITY:                                                  │
│ □ TOP 5 risks have specific section references?                 │
│ □ Recommendations have draft language (not just concepts)?      │
│ □ Dealbreakers clearly marked with escalation path?             │
│                                                                 │
│ CONFIDENCE GATE:                                                │
│ □ Overall confidence ≥ 91% before presenting?                   │
│ □ If below 91%, flag specific uncertainty areas?                │
│                                                                 │
│ IF ANY CHECKBOX FAILS → Loop back to relevant phase             │
└─────────────────────────────────────────────────────────────────┘
```

### Three-Lens Analysis Framework

| Lens | Philosophy | Risk Tolerance | Best For |
|------|------------|----------------|----------|
| **Conservative** | Maximum protection | Low | High-value contracts, new counterparties, weak leverage |
| **Moderate** | Balanced risk/relationship | Medium | Standard commercial deals, existing relationships |
| **Relationship-Friendly** | Maximize flexibility | Higher | Strategic partnerships, strong leverage, repeat customers |

### Risk Categories (Score 1-5) ⚠️ UPDATED v2.1

#### Financial Risk
- Payment terms and schedules
- Liability caps and exclusions
- Liquidated damages
- Warranty obligations
- Cost impacts (insurance, compliance)

#### Operational Risk
- SLA/performance requirements
- Audit/reporting obligations
- Subcontracting restrictions
- Resource commitments
- Response time requirements

#### Legal Risk
- Indemnification scope
- IP ownership/licensing
- Confidentiality obligations
- Termination provisions
- Dispute resolution

#### Compliance Risk
- Regulatory requirements
- Certification mandates
- Data protection/privacy
- Export control
- Industry-specific compliance

#### Flowdown Risk
- Back-to-back alignment
- Warranty coordination
- Liability cap matching
- Payment term alignment
- Performance guarantee gaps

#### Displacement Risk
- Customer protection periods
- Territory restrictions
- Competitor assignment clauses
- Direct sales provisions
- Post-termination gaps

#### Statutory Risk ⚠️ NEW v2.1
- UCC statutory violations (UCC-2-719, UCC-2-302, etc.)
- Warranty disclaimer issues (UCC-2-314/2-316)
- Remedy limitation problems (failure of essential purpose)
- Systems Integrator flow-down gaps (SI-001 to SI-008)
- Unconscionable terms (UCC-2-302)

**Note:** Statutory Risk is detected via Phase 2.5.1 and escalates risk scores using 40% weight formula.

---

### Output Format (contract-risk) ⚠️ ENHANCED v2.1

```markdown
───────────────────────────────────────────────────────────────────
CONTRACT RISK ANALYSIS
───────────────────────────────────────────────────────────────────

Contract: [Name]
Type: [NDA/MSA/IPA/SOW/etc.]
Parties: [Buyer] ←→ [Seller]
Term: [Duration]
Analysis Date: [YYYY-MM-DD]
Confidence: [XX%]

───────────────────────────────────────────────────────────────────
CONTEXT SUMMARY
───────────────────────────────────────────────────────────────────

[1-2 sentence scope summary]

Payment Structure: [Upfront/Milestone/Net 30/etc.]
Competitor-Supplier: [YES/NO]
Prior Report: [Available/Not Available]

───────────────────────────────────────────────────────────────────
RISK MATRIX (7 Categories) ⚠️ UPDATED v2.1
───────────────────────────────────────────────────────────────────

| Category | Score | Rating | Key Concern |
|----------|-------|--------|-------------|
| Financial | X/5 | [H/M/L] | [Concern] |
| Operational | X/5 | [H/M/L] | [Concern] |
| Legal | X/5 | [H/M/L] | [Concern] |
| Compliance | X/5 | [H/M/L] | [Concern] |
| Flowdown | X/5 | [H/M/L] | [Concern] |
| Displacement | X/5 | [H/M/L] | [Concern] |
| **Statutory** | **X/5** | **[H/M/L]** | **[UCC violations]** ⚠️ NEW |

OVERALL RISK: [X.X/5] - [CRITICAL/HIGH/MODERATE/LOW]

───────────────────────────────────────────────────────────────────
UCC STATUTORY VIOLATIONS ⚠️ NEW v2.1
───────────────────────────────────────────────────────────────────

| Section | Rule ID | Violation | Severity | Risk Multiplier |
|---------|---------|-----------|----------|-----------------|
| [X.X] | [UCC-2-719] | [Description] | CRITICAL | 10.0 |
| [Y.Y] | [UCC-2-302] | [Description] | HIGH | 9.0 |

VIOLATIONS DETECTED: [X total]

UCC IMPACT ON RISK SCORES:
• [Section X.X]: Base 6.8 → UCC 10.0 → Final 8.08 (escalated to HIGH)
• [Section Y.Y]: Base 5.2 → UCC 9.0 → Final 6.72 (escalated to MODERATE-HIGH)

STATUTORY RECOMMENDATIONS:
• [Rule UCC-2-719]: REMOVE consequential damages waiver OR add carve-outs
  (Pattern 2.1.2 - Carve-Out Protection)
• [Rule UCC-2-302]: RESTORE ordinary negligence standard OR eliminate
  cumulative unconscionable limitations (Pattern 2.2.1)

───────────────────────────────────────────────────────────────────
TOP 5 RISKS (With Attribution) ⚠️ ENHANCED v2.0
───────────────────────────────────────────────────────────────────

1. [Risk] - Section X.X
   Impact: $[Amount] / [Description]
   Pattern: [X.X.X] - [Pattern Name] ([Success Rate]%)
   UCC Impact: [If applicable, note UCC risk multiplier] ⚠️ NEW v2.1
   Recommendation: [Specific language]

2. [Risk] - Section X.X
   ...

───────────────────────────────────────────────────────────────────
MANDATORY COMBINED TRIGGER CHECKLIST
───────────────────────────────────────────────────────────────────

| Trigger | C1 | C2 | C3 | C4 | C5 | Status |
|---------|----|----|----|----|----| -------|
| **A** (Displacement) | [Y/N] | [Y/N] | [Y/N] | - | - | ✅/⚠️ |
| **B** (Liability) | [Y/N] | [Y/N] | [Y/N] | - | - | ✅/⚠️ |
| **C** (Cash Flow) | [Y/N] | [Y/N] | [Y/N] | - | - | ✅/⚠️ |
| **F** (Channel) | [Y/N] | [Y/N] | [Y/N] | [Y/N] | [Y/N] | ✅/⚠️ |
| **G** (Phase Trap) | [Y/N] | [Y/N] | [Y/N] | [Y/N] | - | ✅/⚠️ |

TRIGGERS DETECTED: [None / List with sections]

───────────────────────────────────────────────────────────────────
ATTRIBUTION TRACKING ⚠️ NEW v2.0
───────────────────────────────────────────────────────────────────

| Recommendation | Pattern | Success Rate | Source |
|----------------|---------|--------------|--------|
| [Rec 1] | 2.1.1 | 75% | Pattern Library v2.1 |
| [Rec 2] | 3.9.3 | 70% | Channel Partner V1→V2 |
| [Rec 3] | UCC-2-719 | N/A (Statutory) | Part 8 UCC ⚠️ NEW |
| [Rec 4] | Custom | N/A | User-specific |

───────────────────────────────────────────────────────────────────
QA/QC VALIDATION ⚠️ NEW v2.0
───────────────────────────────────────────────────────────────────

Phases Completed: [9/9] ⚠️ UPDATED v2.1
Triggers Checked: [5/5]
Patterns Referenced: [X patterns]
UCC Rules Applied: [X violations detected] ⚠️ NEW v2.1
Section Numbers Verified: [Yes/No]
Confidence: [XX%]

⚠️ UNCERTAINTIES (if any):
• [Area 1]: [Reason for uncertainty]
```

---

## CONTRACT-TYPE-SPECIFIC CHECKLISTS (v2.0)

### Channel Partner / MSA Agreement Checklist

**CRITICAL - Run BEFORE standard workflow if contract type = Channel Partner or MSA**

```
┌─────────────────────────────────────────────────────────────────┐
│ CHANNEL PARTNER / MSA AGREEMENT CHECKLIST (v2.0)               │
├─────────────────────────────────────────────────────────────────┤
│ COMPETITOR-SUPPLIER DETECTION:                                  │
│ □ Does supplier also provide systems integration?               │
│ □ Does supplier sell directly to end-customers?                 │
│ □ Could supplier bypass you after customer introduction?        │
│ → IF YES: Apply COMPETITOR LENS + Run Displacement Cascade      │
│                                                                 │
│ DISPLACEMENT CASCADE (Pattern 3.9.x) ⚠️ NEW v2.0:              │
│ □ Territory definitions favor them?            [Component 1]    │
│ □ Customer data access reveals identity?       [Component 2]    │
│ □ Transition provisions enable handoff?        [Component 3]    │
│ □ Post-termination gaps < 24 months?          [Component 4]    │
│ → 3+ FAVOR THEM = ESCALATE AS DEALBREAKER                       │
│                                                                 │
│ CUSTOMER PROTECTION (Pattern 3.1.1 - 75%):                      │
│ □ Protection period defined? (24 months minimum)                │
│ □ Protection survives termination?                              │
│ □ Documentation requirements clear?                             │
│ □ Commission on direct sales if bypassed? (15%+ target)         │
│ → MISSING = DEALBREAKER                                         │
│                                                                 │
│ EXCLUSIVITY SYMMETRY:                                           │
│ □ If non-exclusive for you, is it non-exclusive for them?       │
│ □ If you have non-compete, do they have reciprocal?             │
│ □ Check for one-way restrictions (you locked, they free)        │
│ → ASYMMETRY = HIGH RISK                                         │
│                                                                 │
│ CUSTOMER HANDOFF DETECTION:                                     │
│ □ Who contracts with end-customer? (You or Supplier?)           │
│ □ "Assist Company in negotiating with End-Customer" = FLAG      │
│ □ "Contract between End-Customer and Company" = DEALBREAKER     │
│ → HANDOFF CLAUSE = DEALBREAKER                                  │
│                                                                 │
│ UCC STATUTORY CHECKS (NEW v2.1):                                │
│ □ AS IS / merchantability disclaimers? (UCC-2-314/2-316)        │
│ □ Prepayment lock without refund? (UCC-2-719)                   │
│ □ Vendor warranty shorter than client warranty? (SI-001)        │
│ □ Liability cap lower than client exposure? (SI-002)            │
│ → UCC VIOLATIONS = Apply 40% statutory weight                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### NDA / MNDA Checklist

**CRITICAL - Run for all confidentiality agreements**

```
┌─────────────────────────────────────────────────────────────────┐
│ NDA / MNDA CHECKLIST (v2.0)                                     │
├─────────────────────────────────────────────────────────────────┤
│ SCOPE:                                                          │
│ □ One-way (NDA) or mutual (MNDA)?                               │
│ □ Confidential Information defined? (check exclusions)          │
│ □ Scope reasonable for contemplated transaction?                │
│                                                                 │
│ TERM:                                                           │
│ □ Disclosure period vs. protection period separated?            │
│ □ Protection period: 2-5 years standard                         │
│ □ Perpetual protection = RED FLAG (negotiate finite term)       │
│                                                                 │
│ EXCLUSIONS (Critical - Pattern 3.3.2):                          │
│ □ Public domain exception                                       │
│ □ Independently developed exception                             │
│ □ Rightfully received from third party exception                │
│ □ Required by law exception (with notice requirement)           │
│                                                                 │
│ RETURN/DESTRUCTION (Pattern 3.3.3):                             │
│ □ Return or destroy upon request?                               │
│ □ Certification of destruction required?                        │
│ □ Electronic copies addressed?                                  │
│                                                                 │
│ RED FLAGS:                                                      │
│ □ Non-solicitation clause (beyond NDA scope)                    │
│ □ Non-compete clause (reject unless strategic partnership)      │
│ □ IP assignment language (remove - not appropriate for NDA)     │
│ □ Unlimited liability (add mutual cap - Pattern 2.1.1)          │
└─────────────────────────────────────────────────────────────────┘
```

---

### IPA / SOW Checklist (NEW v2.0)

**CRITICAL - Run for project agreements**

```
┌─────────────────────────────────────────────────────────────────┐
│ IPA / SOW CHECKLIST (v2.0)                                      │
├─────────────────────────────────────────────────────────────────┤
│ SCOPE DEFINITION:                                               │
│ □ Deliverables objectively defined?                             │
│ □ Acceptance criteria specified? (Pattern 3.5.1)                │
│ □ Out-of-scope items clearly listed?                            │
│ □ Change order process defined? (Pattern 3.2.1)                 │
│                                                                 │
│ ACCEPTANCE (Pattern 3.9.8, 3.10.2):                             │
│ □ Acceptance criteria objective (not "satisfactory")?           │
│ □ Inspection period ≥ 14 days?                                  │
│ □ Deemed acceptance clause? (30 days standard)                  │
│ □ Acceptance tied to end-customer acceptance? (AVOID)           │
│                                                                 │
│ PAYMENT ALIGNMENT (Pattern 2.3.2, 3.10.1):                      │
│ □ Milestone payments tied to deliverables?                      │
│ □ Retainage ≤ 10%?                                              │
│ □ Payment upon acceptance (not delivery)?                       │
│ □ Withholding rights for breach?                                │
│                                                                 │
│ IP OWNERSHIP (Pattern 3.7.1, SI-004):                           │
│ □ Work product ownership defined?                               │
│ □ Pre-existing IP carved out?                                   │
│ □ License back for methodologies?                               │
│ □ Avoid blanket work-for-hire (negotiate limited transfer)      │
│                                                                 │
│ FLOWDOWN ALIGNMENT (Pattern 3.11.1):                            │
│ □ If subcontract, prime contract terms reviewed?                │
│ □ Flowdown addendum for prime contract requirements?            │
│ □ Warranty period ≥ client warranty? (SI-001)                   │
│ □ Liability cap ≥ client exposure? (SI-002)                     │
│                                                                 │
│ UCC STATUTORY CHECKS (NEW v2.1):                                │
│ □ 100% prepayment without escrow? (UCC-2-719, UCC-2-302)        │
│ □ Subjective acceptance criteria? (SI-005)                      │
│ □ No payment for extra work without signed CO? (SI-006)         │
│ □ Performance guarantee without vendor backup? (SI-007)         │
│ → UCC VIOLATIONS = Apply 40% statutory weight                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## AGENT 2: clause-compare

### Workflow

**Input:** Two contract versions (V1 and V2)

**Process:**
1. Extract all sections from V1 and V2
2. Compare section-by-section
3. Categorize changes (Added/Deleted/Modified/Moved)
4. Assess impact (Material/Administrative/Favorable/Unfavorable)
5. Link changes to Pattern Library patterns

**Output:** Change impact matrix with recommendations

### Change Categories

| Category | Definition | Example |
|----------|------------|---------|
| **Added** | New clause in V2 not in V1 | Added indemnification clause |
| **Deleted** | Clause in V1 removed in V2 | Deleted customer protection period |
| **Modified** | Clause text changed | Liability cap reduced from unlimited to $500K |
| **Moved** | Clause relocated (no text change) | Section 8.2 → Section 12.5 |

### Impact Classification

| Impact | Definition | Action |
|--------|------------|--------|
| **Material - Favorable** | Change improves your position | Accept |
| **Material - Unfavorable** | Change worsens your position | Reject or counter |
| **Administrative** | No substantive impact | Accept |
| **Ambiguous** | Impact unclear | Request clarification |

---

### Output Format (clause-compare)

```markdown
───────────────────────────────────────────────────────────────────
REDLINE COMPARISON: V1 → V2
───────────────────────────────────────────────────────────────────

Contract: [Name]
V1 Date: [Date]
V2 Date: [Date]
Total Changes: [X]

───────────────────────────────────────────────────────────────────
CHANGE SUMMARY
───────────────────────────────────────────────────────────────────

| Category | Count | Material | Administrative |
|----------|-------|----------|----------------|
| Added | X | X | X |
| Deleted | X | X | X |
| Modified | X | X | X |
| Moved | X | - | X |

───────────────────────────────────────────────────────────────────
MATERIAL CHANGES (Detail)
───────────────────────────────────────────────────────────────────

1. **ADDED: Liability Cap** - Section 8.2 (NEW)
   Impact: FAVORABLE
   V2 Language: "Neither party's liability shall exceed fees paid"
   Pattern: 2.1.1 (Mutual Cap - 75% success rate)
   Recommendation: ACCEPT

2. **DELETED: Customer Protection Period** - Section 4.3 (REMOVED)
   Impact: UNFAVORABLE
   V1 Language: "24-month protection for introduced customers"
   Pattern: 2.4.1 (Customer Protection Period - 55% success rate)
   Recommendation: REJECT - Restore customer protection

3. **MODIFIED: Cure Period** - Section 10.2
   V1: "7 days written notice"
   V2: "30 days written notice and opportunity to cure"
   Impact: FAVORABLE
   Pattern: 2.8.2 (Cure Period - 80% success rate)
   Recommendation: ACCEPT

───────────────────────────────────────────────────────────────────
OUTCOME TRACKING (Complete After Negotiation) ⚠️ NEW v2.0
───────────────────────────────────────────────────────────────────

| Change | Pattern | Our Response | Outcome |
|--------|---------|--------------|---------|
| Added Liability Cap | 2.1.1 | ACCEPT | WON |
| Deleted Customer Protection | 2.4.1 | REJECT + restore language | TBD |
| Modified Cure Period | 2.8.2 | ACCEPT | WON |

WIN RATE (Favorable Outcomes): TBD
```

---

## AGENT 3-5: Summary

### contract-summary

**Purpose:** Generate executive summary for leadership review

**Process:**
1. Extract contract type, parties, term, scope
2. Identify TOP 3 risks
3. Summarize in 1-page format (≤500 words)

**Output:** Executive summary suitable for C-suite review

---

### negotiation-advisor

**Purpose:** Provide counter-proposal strategy

**Process:**
1. Identify unfavorable terms
2. Map to Pattern Library negotiation patterns
3. Provide 4-tier fallback positions (Optimal/Strong/Acceptable/Walk-Away)
4. Cite success rates for each position

**Output:** Negotiation playbook with prioritized positions

---

### compliance-check

**Purpose:** Check against company policies or regulatory requirements

**Process:**
1. Load compliance requirements (user-provided or standard)
2. Check contract against requirements
3. Flag non-compliant clauses
4. Recommend corrections

**Output:** Compliance status report with remediation steps

**Note:** Now includes UCC statutory compliance checks (Part 8) for commercial contracts. ⚠️ NEW v2.1

---

## PATTERN LIBRARY CROSS-REFERENCE MAP ⚠️ UPDATED v2.1

### Agent → Pattern Quick Lookup

| Agent | Use These Patterns |
|-------|-------------------|
| contract-risk (Displacement) | 2.4.1, 2.4.2, 2.4.3, 3.1.1, 3.6.3, 3.9.3 |
| contract-risk (Liability) | 2.1.1, 2.1.2, 2.1.3, 2.2.1, 2.2.4, 2.10.3, SI-002 |
| contract-risk (Payment) | 2.3.1, 2.3.2, 2.3.3, 3.9.10, 3.10.1 |
| contract-risk (IP) | 3.1.4, 3.7.1, 3.10.5, SI-004 |
| contract-risk (Termination) | 2.8.1, 2.8.2, 2.8.3, 3.9.9 |
| contract-risk (Acceptance) | 3.1.3, 3.9.7, 3.9.8, 3.10.2, SI-005 |
| **contract-risk (UCC Statutory)** | **Part 8: UCC-2-719, UCC-2-302, UCC-2-717, UCC-2-314/2-316, SI-001 to SI-008** ⚠️ NEW |
| clause-compare | All Part 2, Part 3, Part 8 |
| negotiation-advisor | Part 5 (Four-Tier Fallback Framework) |
| compliance-check | 2.1.1, 2.2.1, 2.8.2, 3.1.1, Part 8 (UCC statutory) |

---

### Pattern → Agent Quick Lookup

| Pattern Category | Primary Agent | Secondary Agent |
|-----------------|---------------|-----------------|
| 2.1.x (Limitation of Liability) | contract-risk | negotiation-advisor |
| 2.2.x (Indemnification) | contract-risk | compliance-check |
| 2.3.x (Payment Terms) | contract-risk | clause-compare |
| 2.4.x (Vendor Displacement) | contract-risk | negotiation-advisor |
| 2.8.x (Termination) | contract-risk | negotiation-advisor |
| 3.1.x (Systems Integrator) | contract-risk | clause-compare |
| 3.9.x (MSA Commercial Terms) | contract-risk | clause-compare |
| 3.10.x (Services Procurement) | contract-risk | clause-compare |
| 3.11.x (Project Agreements) | contract-risk | clause-compare |
| **Part 8 (UCC Statutory)** | **contract-risk** | **compliance-check** ⚠️ NEW |

---

## OUTCOME TRACKING INTEGRATION (v2.0)

### Logging Outcomes

After negotiation completes, log outcomes in structured format:

```yaml
OUTCOME_LOG:
  contract_id: "[ID]"
  contract_type: [MSA/IPA/SOW/etc.]
  date_analyzed: [YYYY-MM-DD]
  date_outcome: [YYYY-MM-DD]
  patterns_proposed: [X]
  won: [X]
  mutual: [X]
  lost: [X]
  win_rate: [X%]

  pattern_details:
    - pattern_id: "2.1.1"
      outcome: WON
      notes: "Accepted without modification"
    - pattern_id: "3.9.3"
      outcome: MUTUAL
      notes: "Compromised at 18 months (our 24 vs. their 12)"
```

---

### Outcome Summary

```markdown
───────────────────────────────────────────────────────────────────
OUTCOME SUMMARY (Post-Negotiation)
───────────────────────────────────────────────────────────────────

Contract: [Name]
Patterns Proposed: [X]
Patterns Won: [X]
Patterns Mutual: [X]
Patterns Lost: [X]

WIN RATE: [X%] ((WON + MUTUAL) / Total)

TOP WINS:
• Pattern 2.1.1 (Mutual Cap): Accepted 2x variant without negotiation
• Pattern 2.8.2 (Cure Period): 30 days accepted (industry standard)

COMPROMISES:
• Pattern 3.9.3 (Territory Protection): 18 months (our 24 vs. their 12)

LOSSES:
• Pattern 2.4.1 (Customer Protection): Rejected entirely

LEARNINGS:
• Success Rate Update: Pattern 3.9.3 → Adjust from 70% to 65% (compromise)
• New Pattern Needed: Tiered territory protection (12/18/24 month options)
```

---

## VALIDATION SCORECARD INTEGRATION

### Capture Rate Tracking

**Target:** 75%+ capture rate (identified risks / applicable patterns)

**Calculation:**
```
Capture Rate = (Patterns Identified / Total Applicable Patterns) × 100%
```

**Example:**
- Contract: MSA
- Applicable Patterns: 87
- Patterns Identified: 52
- Capture Rate: 59.8% (below target → investigate gaps)

---

### Gap Pattern Analysis (v2.0)

**8 Common Gaps:**
1. Definitions gaps (Force Majeure, Confidential Information)
2. Operational barriers (Response times, approval timeframes)
3. Back-to-back gaps (Liability flow-through, warranty coordination)
4. IP provisions (Work-for-hire, license scope)
5. Termination nuances (Wind-down, post-term obligations)
6. Displacement signals (Customer protection, territory rights)
7. Payment mechanics (Milestone alignment, withholding rights)
8. **Warranty disclaimers (AS IS, fitness for purpose) - now addressed with Part 8 UCC v2.1**

**Remediation:** Use contract-type-specific checklists to systematically cover gaps

---

## CAI WORKFLOW INTEGRATION

### Decision Tree: Single vs. Two-Version Analysis

```
User uploads contract
         ↓
    Is this V2+?
    /        \
  YES         NO
  ↓           ↓
Ask: "Do you have V1?"   Run contract-risk
  /        \              (8 phases)
YES        NO                ↓
↓          ↓            Present report
Run both:  Run V2 only      ↓
• contract-risk on V1       DONE
• clause-compare V1→V2
• Merge outputs
    ↓
Present combined report
    ↓
DONE
```

---

### Phase Flow Diagram

```
Phase 0: Prior Report Check (if V2+)
    ↓
Phase 1: Context Extraction
    ↓
Phase 1.5: Competitor Detection
    ↓
Phase 1.5.1: Displacement Cascade (if competitor)
    ↓
Phase 2: Exhibit Review
    ↓
Phase 2.5: Definitions Review
    ↓
Phase 2.5.1: UCC Statutory Conflict Detection ⚠️ NEW v2.1
    ↓
Phase 3: Three-Lens Risk Analysis (7 categories) ⚠️ UPDATED v2.1
    ↓
Phase 4: Combined Trigger Checklist (5 triggers)
    ↓
Phase 5: Secondary Risk Sweep
    ↓
Phase 6: Cross-Validation (if V2+)
    ↓
Phase 7: QA/QC Validation
    ↓
Present Report
```

---

## INTEGRATION NOTES FOR CLAUDE.AI

### Pattern Library Reference

**CRITICAL:** All recommendations MUST cite Pattern Library patterns by number.

**Example:**
- ❌ Bad: "Consider adding liability cap"
- ✅ Good: "Add mutual liability cap (Pattern 2.1.1, 75% balanced leverage)"

**UCC Statutory Citations:** ⚠️ NEW v2.1
- ❌ Bad: "This clause may be problematic"
- ✅ Good: "UCC § 2-719 violation detected (Part 8: UCC-2-719, risk multiplier 10.0)"

---

### Success Rate Calibration

When citing patterns, always include success rate:
- "Pattern 2.1.1 (Mutual Cap) - 75% balanced leverage"
- "Pattern 2.8.2 (Cure Period) - 80% any leverage"
- "Pattern 3.9.3 (Territory Protection) - 70% balanced leverage"

**UCC Rules:** Do not have success rates (they are statutory, not negotiable).
- Instead cite: "UCC-2-719 (statutory violation, not negotiable)"

---

### Confidence Gate

**Never present reports with confidence < 91%** without explicit uncertainty flagging.

**If confidence < 91%:**
1. Flag specific areas of uncertainty
2. Explain why confidence is low
3. Recommend manual review for those sections
4. Do NOT guess or make assumptions

---

### Outcome Tracking

After negotiation, log outcomes for continuous improvement:
- Update success rates based on actual outcomes
- Identify new patterns from novel solutions
- Refine trigger thresholds based on detection accuracy
- Document UCC detection accuracy (false positives/negatives)

---

**END OF CC AGENT CAPABILITIES v2.1**

*Generated: January 18, 2026*
*Confidence: 96%*
*Integration: Claude.ai Projects + Pattern Library v2.1 + Part 8 UCC Statutory Logic*
