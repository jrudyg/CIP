---
name: contract-version-comparison
description: Generate professional .docx comparison reports for two contract versions with executive summary, 5-column analysis table, visual redlines (RED deletions, GREEN additions), business impact narratives, QA/QC validation, and alignment tracking. Use when user uploads two .docx contract versions and requests comparison analysis for internal review, negotiation preparation, or client presentation.
---

# Contract Version Comparison

## Overview

This skill compares two contract versions and generates a professional Word document with:
- Executive summary with change statistics table and key themes
- 5-column detailed comparison table (landscape orientation)
- Visual redlines (RED #FF0000 strikethrough deletions, GREEN #00B050 bold additions)
- Business impact narratives in plain language
- QA/QC validation section with methodology documentation
- Category-based impact classification (CRITICAL → ADMINISTRATIVE)

**Core value proposition:** Consistent, quality .docx generation with full clause-by-clause QA/QC workflow.

---

## When to Use This Skill

**Triggers:**
- User uploads two .docx files (versions of same contract)
- User asks to "compare versions" or "show what changed"
- User needs "redline analysis" or "comparison report"
- User has a risk report and wants to validate changes implemented

---

## Document Generation Approach

**Preferred: docx-js (JavaScript)**
- Better formatting control for complex tables
- Reliable redline color application
- Landscape orientation support
- See `scripts/generate_report_template.js`

**Fallback: python-docx (Python)**
- Use when JavaScript not available
- See `scripts/generate_report.py`

**Always read `/mnt/skills/public/docx/SKILL.md` and `/mnt/skills/public/docx/docx-js.md` before generating.**

---

## Workflow

### Phase 1: Clarify Requirements

Ask these questions **ONE AT A TIME** (wait for response before next):

**Q1:** "What are the version identifiers?"
- Example: "V1 (Original) vs V2 (Final)", "October Draft vs November Signed"

**Q2:** "What's your role/position in this agreement?"
- Buyer, Seller, Vendor, Customer, Systems Integrator, Channel Partner, Provider

**Q3:** "What's the comparison purpose?"
- Internal QA/QC, Negotiation preparation, Stakeholder presentation, Due diligence

**Q4:** "Should I analyze all sections or focus on specific areas?"
- All substantive changes (default)
- Specific sections only (user lists)
- Exclude certain sections (user specifies)

**Q5:** "Do you have expected changes from a risk report to validate against?"
- If yes: User provides risk mapping for alignment tracking

---

### Phase 2: Extract Documents

**Read docx skill first:**
```bash
cat /mnt/skills/public/docx/SKILL.md
```

**Extract both documents:**
```bash
pandoc --track-changes=accept v1.docx -o v1_extracted.md
pandoc --track-changes=accept v2.docx -o v2_extracted.md
```

**Alternative (python-docx):**
```python
from docx import Document
doc = Document('file.docx')
text = '\n'.join([p.text for p in doc.paragraphs])
```

---

### Phase 3: Detect Changes

**Content-based section matching:**
1. Match sections by clause title/content (NOT section numbers alone)
2. V2 section numbers prevail (latest version is definitive)
3. Mark tie-breaker cases with asterisk (*) if confidence < 85%

**Change detection:**
- Identify substantive text differences
- Ignore: formatting, company name tokens, typos, grammar fixes

**Classify each change:**
- CRITICAL: Liability, Indemnification, IP Ownership, Compliance, Insurance
- HIGH PRIORITY: Termination, Warranties, Acceptance, Fees
- MODERATE: Payment terms, Operational procedures
- ADMINISTRATIVE: Minor updates, Force majeure additions

---

### Phase 4: Clause-by-Clause QA/QC Validation

**For each change, present:**

```
═══════════════════════════════════════════════════════════════
CLAUSE [X] OF [TOTAL] - QA/QC REVIEW
═══════════════════════════════════════════════════════════════

📋 SECTION: [number] - [title]
⚠️ IMPACT: [CRITICAL/HIGH PRIORITY/MODERATE/ADMINISTRATIVE]

V1 (Original):
[Exact quoted text from V1]

V2 (Final) with Redlines:
[Text with ~~strikethrough deletions~~ and **bold additions**]

Business Impact:
[2-4 sentence narrative explaining business implications]

═══════════════════════════════════════════════════════════════
QA/QC DECISION
═══════════════════════════════════════════════════════════════

Please verify against source documents and respond:

**APPROVE** - Entry accurate, proceed to next
**MODIFY** - Specify corrections needed
**FLAG** - Needs special attention (explain concern)
**REJECT** - Major error, rebuild entry
```

**Wait for user response before proceeding to next clause.**

**On MODIFY:** Apply corrections, re-present for confirmation.
**On FLAG:** Add to flagged items list, ask how to handle.
**On REJECT:** Regenerate entry from source documents.

---

### Phase 5: Generate Report

**After all clauses validated, generate Word document.**

**Read docx-js documentation:**
```bash
cat /mnt/skills/public/docx/docx-js.md
```

**Use template structure from `scripts/generate_report_template.js`**

**Key specifications:**
- Landscape orientation
- Arial font throughout
- Navy color scheme (#1F4E79 headers)
- RED deletions (#FF0000 strikethrough)
- GREEN additions (#00B050 bold)
- 5-column table with specified widths

**Output to:** `/mnt/user-data/outputs/[Name]_V[X]_to_V[Y]_Comparison_QA_Validated_[YYYYMMDD].docx`

---

### Phase 6: Deliver

**Present completion summary:**

```
✅ COMPARISON REPORT COMPLETE

[View Final Report](computer:///mnt/user-data/outputs/filename.docx)

REPORT SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Changes documented: [X]
  CRITICAL: [X]
  HIGH PRIORITY: [X]
  MODERATE: [X]
  ADMINISTRATIVE: [X]

DOCUMENT COMPONENTS:
✓ Title page with version identifiers
✓ Executive summary with statistics table
✓ Key themes (5 major findings)
✓ 5-column detailed comparison table
✓ Visual redlines (RED/GREEN)
✓ Business impact narratives
✓ QA/QC validation notes
```

---

## Report Structure (Required Sections)

### 1. Title Page
- Contract name (large, centered)
- "Version Comparison Report" subtitle
- Version identifiers: "V1 (Original) → V2 (Final)"
- Comparison date
- Position and leverage
- "QA/QC VALIDATED" badge (green)

### 2. Executive Summary
- Change Statistics Table (Impact Category | Count)
- Key Themes (5 bullet points summarizing major changes)

### 3. Detailed Comparison Table (5 Columns)
| # | Section / Category | V1 (Original) | V2 (Final) - Redlined | Business Impact |
|---|---|---|---|---|

### 4. QA/QC Validation Notes
- Validation summary (changes validated, corrections applied)
- Methodology (extraction, comparison, validation steps)
- Exclusions (what was NOT analyzed)

---

## Column Width Specifications

**Landscape orientation, 0.75" margins, ~14400 DXA total width**

| Column | Purpose | Width (DXA) | Width (%) |
|--------|---------|-------------|-----------|
| 1 | # | 600 | 4% |
| 2 | Section/Category | 2400 | 17% |
| 3 | V1 (Original) | 4200 | 29% |
| 4 | V2 (Redlined) | 4200 | 29% |
| 5 | Business Impact | 3000 | 21% |

---

## Color Specifications

| Element | Color | Hex |
|---------|-------|-----|
| Header background | Navy | #1F4E79 |
| Header text | White | #FFFFFF |
| Accent blue | Medium blue | #2E75B6 |
| Deletion text | Red | #FF0000 |
| Addition text | Green | #00B050 |
| Critical badge | Dark red | #C00000 |
| High priority badge | Orange | #ED7D31 |
| Moderate badge | Blue | #2E75B6 |
| Administrative badge | Gray | #666666 |

---

## Impact Classification Rules

**CRITICAL (highest priority):**
- Limitation of Liability (caps, carve-outs)
- Indemnification (scope, qualifiers, mutuality)
- IP Ownership (work product, transfers, licenses)
- Compliance & Regulatory (new obligations)
- Insurance (limits, additional insured)

**HIGH PRIORITY:**
- Termination rights (for cause, for convenience, cure periods)
- Warranties (scope, duration, standards)
- Acceptance criteria (objectivity, timing)
- Fees and pricing (payment timing, discounts)

**MODERATE:**
- Payment terms (Net 30 vs Net 60)
- Operational procedures (audit, reporting, subcontractors)
- Confidentiality (mutuality, scope)
- Assignment (restrictions, M&A carve-outs)

**ADMINISTRATIVE:**
- Force majeure additions
- Contact information updates
- Governing law (without venue)
- Definition clarifications

---

## Business Impact Writing Guidelines

**Focus on:**
- Financial implications (cash flow, exposure, costs)
- Timeline impacts (delays, extensions)
- Operational changes (processes, burdens)
- Risk allocation (who bears what risk)
- Relationship dynamics (balance of obligations)

**Style:**
- 2-4 sentences maximum
- Plain language (no legalese)
- Concrete and specific
- From user's position perspective

**Example (Good):**
> "Phase-based IP transfer replaces immediate work-for-hire. Provider retains Design Phase Work Product until Implementation SOW executed AND deposit paid. Protects Provider from free design work if customer doesn't proceed with implementation."

**Example (Bad):**
> "Modified provisions may create operational inefficiencies under commercially reasonable standards applicable to the foregoing circumstances."

---

## Quality Standards

**Before generating report, verify:**
- [ ] All substantive changes captured
- [ ] Section numbers match V2 document (V2 prevails)
- [ ] Exact quotes from source documents (no paraphrasing)
- [ ] Redline formatting correct (RED strikethrough, GREEN bold)
- [ ] Business impact narratives complete (2-4 sentences each)
- [ ] Impact classifications follow rules above
- [ ] Executive summary totals match table count
- [ ] No company name tokens included (unless entity changed)

**Excluded from analysis:**
- Company name anonymization tokens
- Formatting-only changes
- Typographical corrections
- Grammar fixes without meaning change

---

## References

- `references/report-format.md` - Detailed output specifications
- `references/impact-classification.md` - Classification logic and examples
- `references/validation-checklist.md` - QA/QC gate criteria

---

## Scripts

- `scripts/generate_report_template.js` - Reusable docx-js template (preferred)
- `scripts/compare_documents.py` - Document extraction and comparison
- `scripts/generate_report.py` - Python fallback for report generation
- `scripts/validate_entry.py` - Entry validation utility

---

**END OF SKILL.md**
