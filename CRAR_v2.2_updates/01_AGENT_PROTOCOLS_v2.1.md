# 01_AGENT_PROTOCOLS v2.1

**Version:** 2.1
**Date:** January 18, 2026
**Purpose:** Detailed execution workflows for contract analysis agents
**Pattern Library:** v2.1 (113 patterns + rules + 4 clusters)

---

## VERSION 2.1 CHANGES

### From v2.0 → v2.1
- Added **Phase 2.5.1: UCC Statutory Conflict Detection** to contract-risk agent
- Added **UCC Violation Output Section** to contract-risk template
- Updated pattern library references: 87 → 113 (includes 26 UCC statutory rules)
- Added **Statutory Risk** as 7th risk category

### Contract Type Taxonomy (v2.0)

| Code | Full Name | Description | Agent Focus |
|------|-----------|-------------|-------------|
| NDA | Non-Disclosure Agreement | One-way confidentiality | compliance-check |
| MNDA | Mutual Non-Disclosure Agreement | Two-way confidentiality | compliance-check |
| MSA | Master Services Agreement | Framework agreement | contract-risk, clause-compare |
| IPA | Individual Project Agreement | Standalone project | contract-risk |
| SOW | Statement of Work | Scope under MSA | clause-compare |
| CHGORD | Change Order | Modifications to SOW/IPA | clause-compare |
| AMEND | Amendment | Modifications to base | clause-compare |
| VERSION | Version (V1, V2...) | Negotiation iterations | clause-compare |
| PO | Purchase Order | Procurement | compliance-check |
| MOU | Memorandum of Understanding | Pre-contractual intent | contract-summary |

---

## AGENT OVERVIEW

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| **contract-risk** | Primary | Multi-lens risk analysis | Risk matrix, TOP 5, triggers |
| **clause-compare** | Primary | Version comparison | Redline report, change log |
| **contract-summary** | Primary | Executive summaries | 1-page brief |
| **negotiation-advisor** | Supporting | Counter-proposals | Tiered positions, talking points |
| **compliance-check** | Supporting | Pre-approval validation | Pass/Fail checklist |

### Agent-to-Pattern Mapping

| Agent | Primary Patterns (v2.1) |
|-------|-------------------------|
| contract-risk | 2.1.x, 2.2.x, 2.10.x, Part 6, Part 7, Part 8 (UCC) |
| clause-compare | All Part 2, 3.1-3.2, 3.9-3.12 |
| negotiation-advisor | All patterns (fallbacks in Part 5) |
| compliance-check | 2.1.1, 2.2.1, 2.8.2, 3.1.1 |

---

# AGENT 1: CONTRACT-RISK

## Purpose
Analyze contracts for risk exposure using three analytical lenses. Use proactively when reviewing any contract, MSA, SOW, or agreement.

## Trigger
- Single document uploaded
- User asks for risk assessment
- Initial contract review

## Execution Workflow

**CRITICAL: Execute ALL phases in order. Do not skip.**

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: PRIOR REPORT CHECK (If Available)                      │
├─────────────────────────────────────────────────────────────────┤
│ □ Prior risk report provided?                                   │
│ □ Extract key findings for cross-validation                     │
│ □ Note combined triggers previously identified                  │
│ □ Count total issues for capture rate calculation               │
│ □ Flag items for alignment verification                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: CONTEXT CAPTURE                                        │
├─────────────────────────────────────────────────────────────────┤
│ Ask ONE question at a time:                                     │
│                                                                 │
│ Q1: "What type of contract is this?"                           │
│     □ NDA / MNDA (confidentiality)                              │
│     □ MSA (master framework)                                    │
│     □ IPA (individual project)                                  │
│     □ SOW (scope under MSA)                                     │
│     □ AMEND / CHGORD (modification)                             │
│     □ PO (purchase order)                                       │
│     □ MOU (pre-contractual)                                     │
│                                                                 │
│ Q2: "What's your position and leverage?"                       │
│     • Position: Buyer, Seller, Prime, Sub, Partner              │
│     • Leverage: Strong / Balanced / Weak                       │
│                                                                 │
│ Q3: "Brief context on this project/relationship?"              │
│     • Project type                                              │
│     • Key concerns                                              │
│     • Prior relationship                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1.5: COMPETITOR-SUPPLIER DETECTION ⚠️ CRITICAL            │
├─────────────────────────────────────────────────────────────────┤
│ □ Is counterparty also a competitor in your services?           │
│ □ Do they offer systems integration / your core services?       │
│ □ Could they bypass you to serve your customers directly?       │
│                                                                 │
│ IF YES to any:                                                  │
│ → Apply "COMPETITOR LENS" to ALL remaining phases               │
│ → Flag ALL one-sided provisions as HIGH RISK minimum            │
│ → Check for customer handoff clauses                            │
│ → Verify exclusivity is MUTUAL or doesn't exist                 │
│ → Run DISPLACEMENT CASCADE DETECTION (see below)                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1.5.1: DISPLACEMENT CASCADE DETECTION ⚠️ NEW v2.0        │
├─────────────────────────────────────────────────────────────────┤
│ Check for 4-component cascade system:                           │
│                                                                 │
│ Component 1: TERRITORY DEFINITIONS                              │
│ □ Territory defined? Geographic scope clear?                    │
│ □ Exclusions listed? (existing customers, specific accounts)    │
│ □ Modification rights mutual or one-sided?                      │
│                                                                 │
│ Component 2: CUSTOMER DATA ACCESS                               │
│ □ Who owns customer contact information?                        │
│ □ Required reporting reveals customer identity?                 │
│ □ Post-termination data rights?                                 │
│                                                                 │
│ Component 3: TRANSITION PROVISIONS                              │
│ □ Customer transition clause exists?                            │
│ □ Who controls communication to customers?                      │
│ □ "Orderly transition" = handoff mechanism?                     │
│                                                                 │
│ Component 4: POST-TERMINATION GAPS                              │
│ □ Non-compete period? (0 = immediate displacement)              │
│ □ Non-solicitation period? (< 24 months = weak)                 │
│ □ Commission on direct sales post-term?                         │
│                                                                 │
│ IF 3+ components favor counterparty → ESCALATE AS DEALBREAKER   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXHIBIT/ATTACHMENT REVIEW                              │
├─────────────────────────────────────────────────────────────────┤
│ □ List all exhibits and attachments                             │
│ □ Security requirements (SOC audits, compliance costs)          │
│ □ Insurance schedules (coverage amounts, tail periods)          │
│ □ Service levels (SLAs with penalty exposure)                   │
│ □ Rate schedules (markup limitations, billing constraints)      │
│ □ Flag items with cost impact > $10K annually                   │
│ □ Check for BLANK/PLACEHOLDER text (incomplete contract)        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2.5: DEFINITIONS REVIEW ⚠️ CRITICAL (ENHANCED v2.0)      │
├─────────────────────────────────────────────────────────────────┤
│ REQUIRED DEFINITIONS CHECKLIST:                                 │
│ □ Force Majeure - Mutual or one-sided?                          │
│   → One-sided protecting only counterparty = HIGH RISK          │
│   → Includes operational risks (equipment breakdown) = FLAG     │
│   → Check FM exclusions list per Pattern 2.11.2                 │
│                                                                 │
│ □ Material Breach - Reasonable definition?                      │
│   → Overly broad = risk of arbitrary termination                │
│                                                                 │
│ □ Insolvency/Bankruptcy triggers - Balanced?                    │
│   → Check if counterparty can exit on your financial stress     │
│                                                                 │
│ □ Confidential Information - Scope appropriate?                 │
│   → Too broad = operational burden                              │
│   → Too narrow = inadequate protection                          │
│                                                                 │
│ □ Affiliate/Related Party - Expansive definitions?              │
│   → Can they assign to affiliates without consent?              │
│                                                                 │
│ MISSING DEFINITIONS DETECTION ⚠️ NEW v2.0:                      │
│ □ "Customer" defined? (critical for displacement)               │
│ □ "Competing Products" defined? (non-compete scope)             │
│ □ "Territory" defined? (geographic boundaries)                  │
│ □ "End-User" vs "Customer" distinguished?                       │
│ □ "Gross Negligence" defined? (indemnity threshold)             │
│                                                                 │
│ IF CRITICAL DEFINITION MISSING → Flag for addition before sign  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2.5.1: UCC STATUTORY CONFLICT DETECTION ⚠️ NEW v2.1      │
├─────────────────────────────────────────────────────────────────┤
│ Check clauses against Delaware UCC Article 2 (26 rules):        │
│                                                                 │
│ □ Load UCC rules from UCC_Statutory_Logic_v2.json              │
│ □ For each clause, match text against trigger concepts          │
│ □ If match found, extract:                                     │
│   • Rule ID (e.g., UCC-2-719)                                   │
│   • Severity (CRITICAL/HIGH/MODERATE)                           │
│   • Risk Multiplier (5.0-10.0)                                  │
│   • Matched concepts (trigger keywords found)                   │
│                                                                 │
│ UCC RULES BY CATEGORY:                                         │
│ • UCC-2-719: Remedy Limitations                                │
│   → Consequential damages waivers                              │
│   → Exclusive/sole remedy clauses                              │
│   → Prepayment locks with no refund                            │
│                                                                 │
│ • UCC-2-302: Unconscionability                                 │
│   → One-sided payment terms                                    │
│   → Excessive prepayment requirements                          │
│                                                                 │
│ • UCC-2-314/2-316: Warranty Disclaimers                        │
│   → "AS IS" / "WITH ALL FAULTS" language                        │
│   → Merchantability disclaimers                                │
│   → Fitness for purpose waivers                                │
│                                                                 │
│ RISK SCORE ESCALATION (40% Weight):                            │
│ If UCC violation detected:                                     │
│   Final Score = (Base Score × 0.6) + (Risk Multiplier × 0.4)   │
│                                                                 │
│ Example:                                                        │
│   Base Score: 6.8 → UCC 10.0 → Final: 8.08 (escalated)         │
│                                                                 │
│ IF UCC VIOLATION DETECTED:                                     │
│ → Add to TOP 5 risks with "STATUTORY CONFLICT" label           │
│ → Include in output UCC Violations section                     │
│ → Apply 40% weight to risk score calculation                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: THREE-LENS RISK ANALYSIS                               │
├─────────────────────────────────────────────────────────────────┤
│ Score all 7 risk categories (1-5):                              │
│ • Financial Risk                                                │
│ • Operational Risk                                              │
│ • Legal Risk                                                    │
│ • Compliance Risk                                               │
│ • Flowdown Risk (EPC-specific)                                  │
│ • Displacement Risk (EPC-specific)                              │
│ • Statutory Risk (UCC violations) ⚠️ NEW v2.1                  │
│                                                                 │
│ Apply three lenses:                                             │
│ • Conservative (maximum protection)                             │
│ • Moderate (balanced risk/relationship)                         │
│ • Relationship-Friendly (maximize flexibility)                  │
│                                                                 │
│ Identify TOP 5 risks with exposure quantification               │
│                                                                 │
│ IF COMPETITOR-SUPPLIER DETECTED:                                │
│ → Weight displacement risk 2x in scoring                        │
│ → Flag any provision that benefits them more than you           │
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
│ TRIGGER F (Channel Partner Squeeze) ⚠️ ENHANCED v2.0:          │
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
│ PHASE 5: SECONDARY RISK SWEEP                                   │
├─────────────────────────────────────────────────────────────────┤
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
│ □ All 8 phases executed (including Phase 2.5.1)?                │
│ □ All 5 triggers explicitly answered Y/N?                       │
│ □ Competitor lens applied (if applicable)?                      │
│ □ Displacement cascade checked (if applicable)?                 │
│ □ Missing definitions flagged?                                  │
│ □ UCC violations detected and scored? ⚠️ NEW v2.1              │
│                                                                 │
│ ACCURACY:                                                       │
│ □ Section numbers verified against document?                    │
│ □ Risk scores justified with specific clause text?              │
│ □ Pattern references correct (check Part 2/3/8 numbers)?        │
│ □ No assumptions made without evidence?                         │
│                                                                 │
│ ATTRIBUTION:                                                    │
│ □ Each recommendation linked to Pattern Library pattern?        │
│ □ Success rate cited for each pattern?                          │
│ □ Source noted for non-standard recommendations?                │
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

## Output Format (v2.1 Enhanced with UCC)

```
═══════════════════════════════════════════════════════════════════
CONTRACT RISK ANALYSIS (v2.1)
═══════════════════════════════════════════════════════════════════

CONTRACT: [Name]
TYPE: [NDA|MNDA|MSA|IPA|SOW|CHGORD|AMEND|PO|MOU]
POSITION: [Buyer/Seller/Prime/Sub/Partner]
PHASE: [Design/Implementation/Both]
COMPETITOR-SUPPLIER: [Yes - COMPETITOR LENS ACTIVE / No]
ANALYSIS DATE: [Date]
PRIOR REPORT: [Yes - Date / No]
CONFIDENCE: [XX%]

───────────────────────────────────────────────────────────────────
PHASE MISMATCH CHECK
───────────────────────────────────────────────────────────────────

Contract Phase: [Design / Implementation / Both]
T&Cs Match Phase: [Yes / No - explain]
Work-for-Hire in Design: [Yes - ALERT / No / N/A]
⚠️ TRIGGER G STATUS: [Clear / DETECTED - escalate]

───────────────────────────────────────────────────────────────────
COMPETITOR-SUPPLIER CHECK
───────────────────────────────────────────────────────────────────

Counterparty competes in your services: [Yes / No]
Customer handoff clause detected: [Yes - Section X.X / No]
Exclusivity asymmetry: [Yes - explain / No / Mutual]
Displacement Cascade: [X/4 components favor counterparty]
⚠️ COMPETITOR LENS: [ACTIVE - all sections reviewed / Not Required]

───────────────────────────────────────────────────────────────────
DEFINITIONS STATUS ⚠️ v2.0
───────────────────────────────────────────────────────────────────

| Definition | Status | Risk |
|------------|--------|------|
| Force Majeure | ✅/⚠️/❌ | [Assessment] |
| Material Breach | ✅/⚠️/❌ | [Assessment] |
| Customer | ✅/⚠️/❌ MISSING | [Impact] |
| Territory | ✅/⚠️/❌ MISSING | [Impact] |
| Gross Negligence | ✅/⚠️/❌ | [Assessment] |

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
• [Section Y.Y]: Base 5.2 → UCC 9.0 → Final 6.72 (escalated to MEDIUM-HIGH)

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
TOP 5 RISKS
───────────────────────────────────────────────────────────────────

1. [Risk] - Section X.X ⚠️ STATUTORY CONFLICT
   Impact: $[Amount] / [Description]
   UCC Rule: UCC-2-719 (Remedy Limitation)
   Pattern: 2.1.2 (Carve-Out Protection) - 60%
   Recommendation: [Specific language]

2. [Risk] - Section X.X
   Impact: $[Amount] / [Description]
   Pattern: [X.X.X] ([Success Rate]%)
   Recommendation: [Specific language]

───────────────────────────────────────────────────────────────────
COMBINED TRIGGERS
───────────────────────────────────────────────────────────────────

| Trigger | Components | Status |
|---------|------------|--------|
| A (Displacement) | [X/3] | ✅ Clear / ⚠️ DETECTED |
| B (Liability) | [X/3] | ✅ Clear / ⚠️ DETECTED |
| C (Cash Flow) | [X/3] | ✅ Clear / ⚠️ DETECTED |
| F (Channel) | [X/5] | ✅ Clear / ⚠️ DETECTED |
| G (Phase) | [X/4] | ✅ Clear / ⚠️ DETECTED |

───────────────────────────────────────────────────────────────────
ATTRIBUTION TRACKING ⚠️ v2.0
───────────────────────────────────────────────────────────────────

| Recommendation | Pattern | Success Rate | Source |
|----------------|---------|--------------|--------|
| [Rec 1] | 2.1.1 | 75% | Pattern Library v2.1 |
| [Rec 2] | UCC-2-719 | N/A | UCC Statutory Logic |
| [Rec 3] | 3.9.3 | 70% | Channel Partner V1→V2 |

───────────────────────────────────────────────────────────────────
QA/QC VALIDATION ⚠️ v2.0
───────────────────────────────────────────────────────────────────

Phases Completed: [8/8] (including Phase 2.5.1 UCC)
Triggers Checked: [5/5]
UCC Rules Checked: [26/26]
Patterns Referenced: [X patterns + Y UCC rules]
Section Numbers Verified: [Yes/No]
Confidence: [XX%]

⚠️ UNCERTAINTIES (if any):
• [Area 1]: [Reason for uncertainty]

───────────────────────────────────────────────────────────────────
RECOMMENDATION: [Proceed / Conditional / Do Not Proceed]
───────────────────────────────────────────────────────────────────
```

---

# AGENT 2: CLAUSE-COMPARE

## Purpose
Compare contract versions, generate redlines, and track changes with business impact assessment.

## Trigger
- Two versions of same contract uploaded
- User requests comparison or "what changed"
- QA/QC validation of changes

## Auto-Start Questions (One at a Time)

**Q1:** "What are the version identifiers?"
- Example: "V1 (Original) vs V2 (Final)"

**Q2:** "What's your position in this agreement?"
- Buyer, Seller, Vendor, Customer, Systems Integrator, Channel Partner

**Q3:** "What's the comparison purpose?"
- Internal QA/QC, Negotiation prep, Stakeholder presentation, Due diligence

**Q4:** "Do you have expected changes to validate against?"
- If yes: User provides for alignment tracking

**Q5:** "How should clauses be ordered in the report?"
- **By Risk Category** - CRITICAL → HIGH PRIORITY → MODERATE → ADMINISTRATIVE
- **By Contract Order** - §1, §2, §3... (follows document structure)
- **Hybrid** - Executive summary by risk, detailed table by contract order

## Execution Workflow

### Phase 1: Extract Documents

```bash
# Read docx skill first
cat /mnt/skills/public/docx/SKILL.md

# Extract both versions
pandoc --track-changes=accept v1.docx -o v1_extracted.md
pandoc --track-changes=accept v2.docx -o v2_extracted.md
```

### Phase 2: Detect and Classify Changes

**Section Matching Rules:**
- Match by clause title/content (NOT section numbers alone)
- V2 section numbers prevail (latest version definitive)
- Mark tie-breakers with asterisk (*) if confidence < 85%

**Impact Classification:**

| Level | Categories |
|-------|------------|
| **CRITICAL** | Liability, Indemnification, IP, Compliance, Insurance |
| **HIGH PRIORITY** | Termination, Warranties, Acceptance, Fees |
| **MODERATE** | Payment, Operations, Confidentiality, Assignment |
| **ADMINISTRATIVE** | Force majeure, Contact info, Definitions |

**Silent Change Detection (Flag These):**
- "shall" → "may" (obligation removed)
- "will" → "may endeavor" (weakened)
- "mutual" removed (one-sided now)
- Time periods shortened
- Caps lowered or removed
- Carve-outs added
- "Reasonable"/"material" qualifiers changed

### Phase 2.5: Surgical Redline Rules ⚠️ CRITICAL

**Default Approach: SURGICAL REDLINES**

All redlines must be word-level surgical edits showing precisely what changed. Do NOT summarize or paraphrase changes.

**5-Column Table Structure:**
| # | Section/Impact | V1 (Original) | V2 (Redlined) | Business Impact |

**Redline Formatting:**
- Normal text = unchanged
- ~~Strikethrough red~~ = deleted
- **Bold green** = added

---

#### RULE 1: Surgical Edits (DEFAULT)

Use for most changes. Edit at word/phrase level in V2 column.

**Example - Word Swap:**
```
V1: "...within seven (7) calendar days..."
V2: "...within ~~seven (7) calendar days~~ **thirty (30) days**..."
```

**Example - Partial Word Deletion:**
```
V1: "...non-transferable license..."
V2: "...~~non-~~transferable license..."
```
⚠️ Strike only "non-" NOT the entire word

**Example - Insertion:**
```
V1: "...consent of the other Party."
V2: "...consent of the other Party**, which consent shall not be unreasonably withheld**."
```

---

#### RULE 2: Surviving Text Stays Normal

If a word/phrase exists in both V1 and V2 (even if repositioned), keep it NORMAL and edit around it.

**Example - "acts of terrorism" survives but list changes:**
```
V1: "...sabotage, acts of terrorism, breakdown or major repair..."
V2: "...sabotage~~,~~ **and** acts of terrorism~~, breakdown or major repair...~~**. Force Majeure shall not include...**"
```
✅ "acts of terrorism" stays normal — only comma changed to "and"

---

#### RULE 3: Wholesale Replacement (SPECIAL CASE)

Use ONLY when text is truly rewritten — different structure, different concept, not just edited.

**Test:** Does less than 20% of original text carry over verbatim?
- YES → Wholesale replacement
- NO → Use surgical edits

**Format for Wholesale Replacement:**
- V1 Column: Show deletion with strikethrough (preserved text normal)
- V2 Column: Show addition in bold (preserved text normal)

**Example - §16.4 Liability (only opening phrase survives):**
```
V1: "Unless otherwise agreed in a respective Project Agreement, ~~the Company shall pay...15% of the Contract Price...~~"
V2: "Unless otherwise agreed in a respective Project Agreement, **each Party's aggregate liability...100% of Contract Price...**"
```

---

#### RULE 4: New/Deleted Sections

**Entire Section Deleted:**
- V1: Full text with strikethrough
- V2: "[ENTIRE SECTION DELETED]" with strikethrough

**New Section Added:**
- V1: "[No provision existed in V1]"
- V2: "[NEW SECTION]" + full text in bold

---

#### Surgical Redline Decision Tree

```
CHANGE DETECTED
      │
      ├─── New section? ────────────────► V1: "[No provision]" / V2: Bold all
      │
      ├─── Section deleted? ────────────► V1: Strike all / V2: "[DELETED]"
      │
      ├─── <20% text survives? ─────────► WHOLESALE: V1 strike + V2 bold
      │
      └─── ≥20% text survives? ─────────► SURGICAL in V2 only
                │
                ├─── Word/phrase swap? ──► ~~old~~ **new**
                │
                ├─── Partial deletion? ──► Strike only deleted chars
                │
                └─── Text repositioned? ─► Keep normal, edit around it
```

### Phase 3: Clause-by-Clause QA/QC

Present each change for validation:

```
═══════════════════════════════════════════════════════════════
CLAUSE [X] OF [TOTAL] - QA/QC REVIEW
═══════════════════════════════════════════════════════════════

📋 SECTION: [number] - [title]
⚠️ IMPACT: [CRITICAL/HIGH/MODERATE/ADMINISTRATIVE]
📐 REDLINE TYPE: [Surgical / Wholesale / New / Deleted]

V1 (Original):
[Verbatim text - strikethrough if wholesale replacement]

V2 (Redlined):
[Surgical redline OR bold addition for wholesale]

Business Impact:
[2-4 sentences from user's position]

Pattern Match: [X.X.X] - [Pattern Name] ([Success Rate]%) ⚠️ v2.0

═══════════════════════════════════════════════════════════════
QA/QC DECISION: APPROVE / MODIFY / FLAG / REJECT
═══════════════════════════════════════════════════════════════
```

**Wait for response before next clause.**

**Redline Accuracy Checklist:**
- [ ] Surviving text shown as normal (not re-struck and re-added)?
- [ ] Partial deletions strike only deleted portion?
- [ ] Wholesale replacement justified (<20% survives)?
- [ ] Word-level precision (no summarizing)?
- [ ] Pattern match identified (v2.0)?

### Phase 3.5: Comments Protocol ⚠️ NEW v2.0

**When to Add Comments:**
- Risk identified that needs stakeholder attention
- Alternative language available from Pattern Library
- Section requires legal review
- Ambiguity detected

**Comment Format:**
```
[COMMENT - Author: CIP]
Risk: [Description]
Pattern: [X.X.X] - [Success Rate]%
Recommendation: [Specific action]
```

**Comment Author:** Always use "CIP" as author for machine-generated comments

### Phase 4: Generate Report

**Document Specifications:**
- Orientation: Landscape
- Font: Arial
- Header color: Navy #1F4E79
- Deletions: RED #FF0000 strikethrough
- Additions: GREEN #00B050 bold
- Columns: 5 (Section, Rec, V1, V2, Impact)

**Redline Accuracy Standards:**
- V1 Column: Verbatim original (strikethrough only for wholesale deletions)
- V2 Column: Surgical redlines OR bold additions (never both strike and add same text)
- Surviving text appears NORMAL in both columns
- Strike only deleted characters/words, not entire words when partial

**Report Structure:**
1. Title page with QA/QC VALIDATED badge
2. Executive summary (statistics, themes)
3. Detailed 5-column comparison table
4. QA/QC validation notes
5. Attribution table (v2.0)
6. Outcome tracking section (v2.0)

### Phase 5: Outcome Tracking ⚠️ NEW v2.0

**After Negotiation Completes:**
```
───────────────────────────────────────────────────────────────────
OUTCOME TRACKING (Complete After Negotiation)
───────────────────────────────────────────────────────────────────

| Change # | Our Position | Counterparty Response | Final Outcome |
|----------|--------------|----------------------|---------------|
| 1 | [Pattern X.X.X] | [Accepted/Rejected/Modified] | [WON/LOST/MUTUAL] |
| 2 | ... | ... | ... |

Patterns Used: [X]
Patterns Won: [X] ([XX]%)
Patterns Lost: [X] ([XX]%)
Patterns Modified: [X] ([XX]%)

⚠️ Update Pattern Library success rates based on outcomes
```

### Phase 6: Deliver

**Filename:** `[Contract]_V[X]_to_V[Y]_Comparison_[YYYYMMDD].docx`

**Location:** `/mnt/user-data/outputs/`

## Output Summary

```
✅ COMPARISON REPORT COMPLETE

[View Report](computer:///mnt/user-data/outputs/filename.docx)

Changes: [X] total
  CRITICAL: [X]
  HIGH: [X]
  MODERATE: [X]
  ADMINISTRATIVE: [X]

Risk Shift: [Toward Us / Toward Them / Balanced]
Silent Changes: [X] flagged
Patterns Applied: [X] (from 113 available)
```

---

# AGENT 3: CONTRACT-SUMMARY

## Purpose
Create executive summaries for leadership briefings or quick reference.

## Trigger
- User requests summary
- Stakeholder preparation
- Quick reference needed

## Output Format (1 Page Maximum)

```
═══════════════════════════════════════════════════════════════════
CONTRACT EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════

HEADER
───────────────────────────────────────────────────────────────────
Contract: [Full title]
Type: [NDA|MNDA|MSA|IPA|SOW|CHGORD|AMEND|PO|MOU]
Parties: [Party A] ↔ [Party B]
Effective: [Date] | Term: [Duration]
Value: [Amount]

KEY COMMERCIAL TERMS
───────────────────────────────────────────────────────────────────
Scope: [2-3 sentences]
Pricing: [Model, rates, markup]
Payment: [Terms, schedule]
Performance: [SLAs, guarantees, LDs]

CRITICAL DATES
───────────────────────────────────────────────────────────────────
| Date | Event | Action Required |
|------|-------|-----------------|
| [Date] | [Event] | [Action] |

RISK HIGHLIGHTS (TOP 5)
───────────────────────────────────────────────────────────────────
1. [Risk] - [Impact] (Pattern [X.X.X])
2. [Risk] - [Impact] (Pattern [X.X.X])
3. [Risk] - [Impact] (Pattern [X.X.X])
4. [Risk] - [Impact] (Pattern [X.X.X])
5. [Risk] - [Impact] (Pattern [X.X.X])

EPC CONCERNS
───────────────────────────────────────────────────────────────────
• Upstream Alignment: [Status]
• Downstream Flowdown: [Status]
• Cash Flow Gap: [X days]
• Customer Protection: [Present/Missing/Weak]
• Liability Gap: [None/Quantified]

ACTION ITEMS
───────────────────────────────────────────────────────────────────
| Item | Owner | Deadline |
|------|-------|----------|
| [Item] | [Name] | [Date] |

───────────────────────────────────────────────────────────────────
RECOMMENDATION: [Proceed / Conditional / Do Not Proceed]
───────────────────────────────────────────────────────────────────
```

---

# AGENT 4: NEGOTIATION-ADVISOR

## Purpose
Provide negotiation strategy and counter-proposals.

## Trigger
- User asks "how do I negotiate this?"
- Counter-proposal needed
- Responding to counterparty markup

## Four-Tier Response Framework

| Tier | Definition | When to Use |
|------|------------|-------------|
| **Optimal** | Best protection | Strong leverage |
| **Strong** | Good protection | Balanced leverage |
| **Acceptable** | Minimum acceptable | Weak leverage |
| **Walk-Away** | Deal unviable | Non-negotiable floor |

## Output Format (Per Issue)

```
═══════════════════════════════════════════════════════════════════
NEGOTIATION STRATEGY
═══════════════════════════════════════════════════════════════════

ISSUE: [Section X.X - Title]

───────────────────────────────────────────────────────────────────
POSITION ANALYSIS
───────────────────────────────────────────────────────────────────

Their Position: [What they want]
Their Motivation: [Why]
Our Concern: [Risk created]

Impact:
• Financial: $[Amount]
• Operational: [Description]
• Legal: [Description]

───────────────────────────────────────────────────────────────────
TIERED RESPONSES
───────────────────────────────────────────────────────────────────

TIER 1 - OPTIMAL (Success: XX%)
Position: [Ideal outcome]
Language: "[Draft text]"
Pattern: [X.X.X] - [Pattern Name]
Source: Pattern Library v2.1

TIER 2 - STRONG (Success: XX%)
Position: [Compromise]
Trade-offs: [What we give]
Language: "[Draft text]"

TIER 3 - ACCEPTABLE (Success: XX%)
Position: [Minimum]
Conditions: [What we need in exchange]
Language: "[Draft text]"

TIER 4 - WALK-AWAY
Trigger: [What makes unacceptable]
Alternative: [Walk away or escalate]

───────────────────────────────────────────────────────────────────
TALKING POINTS
───────────────────────────────────────────────────────────────────

1. "[Key argument]"
2. "[Supporting point]"
3. "[Relationship framing]"
```

## Success Rate Reference (v2.0 Updated)

| Contract Type | Leverage | Tier 1 | Tier 2 | Tier 3 |
|---------------|----------|--------|--------|--------|
| MSA (Standard) | Strong | 75-85% | 85-95% | 95%+ |
| MSA (Competitor) | Balanced | 55-65% | 70-80% | 85%+ |
| MSA (Competitor) | Weak | 35-45% | 55-65% | 75%+ |
| IPA/SOW | Strong | 70-80% | 80-90% | 95%+ |
| IPA/SOW | Balanced | 60-70% | 75-85% | 90%+ |
| NDA/MNDA | Any | 80-90% | 90-95% | 98%+ |
| PO | Any | 50-60% | 70-80% | 90%+ |

---

# AGENT 5: COMPLIANCE-CHECK

## Purpose
Pre-approval validation against company standards.

## Trigger
- Pre-signature review
- Final check before approval
- Policy compliance validation

## Required Terms Checklist (Updated v2.0)

| Requirement | Pattern | Threshold |
|-------------|---------|-----------|
| ☐ Liability cap | 2.1.1 | ≤ 2x Contract value |
| ☐ Mutual indemnity | 2.2.1 | Not one-sided |
| ☐ Insurance minimums | 3.9.6 | Per policy |
| ☐ Governing law | — | Acceptable jurisdiction |
| ☐ Dispute resolution | 3.9.5 | Arbitration preferred |
| ☐ Termination rights | 2.8.1 | Preserved |
| ☐ IP ownership | 3.1.4 | Ours or licensed |
| ☐ Confidentiality | 3.3.2 | Mutual, reasonable |
| ☐ Cure period | 2.8.2 | ≥ 30 days |
| ☐ Change orders | 3.12.1 | Defined |
| ☐ Term duration | 3.9.1 | ≥ 24 months or auto-renewal |

## EPC-Specific Requirements

| Requirement | Pattern | Threshold |
|-------------|---------|-----------|
| ☐ Customer protection | 3.1.1, 2.4.1 | 24-month non-solicit |
| ☐ Back-to-back | 2.10.x | Flowdown enabled |
| ☐ Acceptance alignment | 3.1.3 | Tied to Owner |
| ☐ Payment timing | 2.3.2 | Gap < 30 days |
| ☐ Warranty coordination | 3.1.2 | Claims through us |
| ☐ Displacement cascade | Phase 1.5.1 | < 3 components favor them |

## Prohibited Terms

| Prohibition | Severity | Pattern Ref |
|-------------|----------|-------------|
| ☐ Unlimited liability | CRITICAL | 2.1.1 |
| ☐ Consequential damages exposure | CRITICAL | 2.1.2 |
| ☐ Direct supplier contact permitted | CRITICAL | 3.1.1 |
| ☐ Work-for-hire in design | CRITICAL | 3.7.1 |
| ☐ Auto-renewal without notice | HIGH | 3.9.1 |
| ☐ Exclusive dealing | HIGH | 2.7.x |
| ☐ Pricing control by supplier | HIGH | Trigger F |
| ☐ 100% prepayment | HIGH | Part 7.2 |

## Output Format

```
═══════════════════════════════════════════════════════════════════
COMPLIANCE CHECK REPORT (v2.0)
═══════════════════════════════════════════════════════════════════

CONTRACT: [Name]
DATE: [Date]
TYPE: [NDA|MNDA|MSA|IPA|SOW|CHGORD|AMEND|PO|MOU]

───────────────────────────────────────────────────────────────────
OVERALL STATUS
───────────────────────────────────────────────────────────────────

   ╔═══════════════════════════════════════╗
   ║                                       ║
   ║    [PASS / FAIL / CONDITIONAL]        ║
   ║                                       ║
   ╚═══════════════════════════════════════╝

───────────────────────────────────────────────────────────────────
CHECKLIST RESULTS
───────────────────────────────────────────────────────────────────

| Requirement | Status | Section | Pattern | Notes |
|-------------|--------|---------|---------|-------|
| [Item] | ✅/❌/⚠️ | X.X | X.X.X | [Notes] |

───────────────────────────────────────────────────────────────────
COMBINED TRIGGERS
───────────────────────────────────────────────────────────────────

| Trigger | Status |
|---------|--------|
| A (Displacement) | ✅/⚠️ |
| B (Liability) | ✅/⚠️ |
| C (Cash Flow) | ✅/⚠️ |
| F (Channel) | ✅/⚠️ |
| G (Phase) | ✅/⚠️ |

───────────────────────────────────────────────────────────────────
RISK INDICATORS DETECTED ⚠️ v2.0
───────────────────────────────────────────────────────────────────

| Risk Indicator | Section | Severity | Trade-off Accepted? |
|----------------|---------|----------|---------------------|
| [Indicator] | X.X | HIGH/MED | [Yes/No/Pending] |

───────────────────────────────────────────────────────────────────
DEVIATIONS REQUIRING ACTION
───────────────────────────────────────────────────────────────────

| # | Deviation | Section | Action |
|---|-----------|---------|--------|
| 1 | [Description] | X.X | [Waiver/Negotiate/Dealbreaker] |

───────────────────────────────────────────────────────────────────
APPROVALS REQUIRED
───────────────────────────────────────────────────────────────────

| Approver | Reason | Status |
|----------|--------|--------|
| [Role] | [Condition] | ⬜ Pending |

───────────────────────────────────────────────────────────────────
RECOMMENDATION: [Approve / Conditional / Do Not Approve]
───────────────────────────────────────────────────────────────────
```

---

## CROSS-AGENT WORKFLOW

### Typical Full Review Sequence

```
1. contract-risk     → Initial assessment, dealbreaker check
2. [clause-by-clause] → Detailed revision (Pattern Library v2.1)
3. compliance-check  → Pre-approval validation
4. contract-summary  → Leadership brief

If counterparty responds:
5. clause-compare    → Track their changes
6. negotiation-advisor → Counter-proposal strategy
7. [outcome-tracking] → Log results for learning loop (v2.0)
```

### Agent Handoff Protocol

When switching agents:
1. Summarize current state
2. Note key decisions made
3. Identify open items
4. Pass context to next agent
5. Include pattern references used (v2.0)

---

## APPENDIX A: PATTERN LIBRARY QUICK REFERENCE

**Version:** 2.1 (113 patterns + rules + 4 clusters)

### Most-Used Patterns

| Pattern | Name | Success Rate | Use Case |
|---------|------|--------------|----------|
| 2.1.1 | Mutual Cap | 75% | Liability limitation |
| 2.2.1 | Mutual Indemnification | 70% | Risk allocation |
| 2.8.2 | Cure Period | 80% | Termination protection |
| 2.9.1 | Defined Response Times | 85% | Operational barriers |
| 3.1.1 | Customer Protection | 75% | SI displacement |
| 3.9.1 | Term + Auto-Renewal | 80% | Contract duration |
| 3.9.3 | Territory Protection | 70% | Geographic rights |
| 3.10.2 | Objection Period | 85% | Acceptance timing |

### New v2.1: UCC Statutory Rules

| Section | Name | Count |
|---------|------|-------|
| Part 8 | Statutory Conflicts (UCC) | 26 rules |

**UCC Rule Categories:**
- UCC-2-719: Remedy Limitations (3 rules)
- UCC-2-302: Unconscionability (2 rules)
- UCC-2-314/2-316: Warranty Disclaimers (2 rules)
- Additional 19 rules covering delivery, inspection, risk of loss

---

## APPENDIX B: OUTCOME TRACKING SCHEMA

```yaml
OUTCOME_TRACKING:
  pattern_id: "2.1.1"
  pattern_name: "Mutual Cap"
  contract_type: [NDA|MNDA|MSA|IPA|SOW|CHGORD|AMEND|VERSION|PO|MOU]
  position: [BUYER|SELLER|BALANCED]
  leverage: [STRONG|BALANCED|WEAK]
  success_rate_estimated: 75%
  outcome: [WON|MUTUAL|ACCEPTED|LOST|PENDING]
  source_contract: "MSA_2025_11"
  outcome_date: 2025-11-17
  notes: "Accepted with 2x cap variant"
```

---

**END OF AGENT PROTOCOLS v2.1**

*Pattern Library Reference: 02_PATTERN_LIBRARY_v2.1.md (113 patterns + rules)*
