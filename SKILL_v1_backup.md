---
name: contract-version-comparison
description: Generate professional .docx comparison reports for two contract versions with executive summary, 5-column analysis table, visual redlines (RED deletions, GREEN additions), and business impact narratives. Use when user uploads two .docx contract versions and requests comparison analysis for internal review, negotiation preparation, or client presentation.
---

# Contract Version Comparison

## Overview

This skill compares two contract versions and generates a professional Word document with:
- Executive summary categorizing changes by impact level
- 5-column detailed comparison table
- Visual redlines (RED strikethrough deletions, GREEN bold additions)
- Business impact narratives in plain language
- Optional risk-framed recommendations

**Core value proposition:** Consistent, quality .docx generation. Other prompts can analyze contracts; this skill delivers professional, reliable Word documents.

---

## When to Use This Skill

Use when user:
- Uploads two .docx files that are versions of the same contract
- Asks to compare contract versions
- Needs professional comparison report
- Requests redline analysis
- Wants to understand changes between versions

---

## Workflow

### Phase 1: Clarify Requirements

Ask user these questions **ONE AT A TIME** (wait for response before next):

1. **"What are the version identifiers?"**
   - Example: "V3 vs V4", "October 2025 vs November 2025", "Original vs Revised"

2. **"What's your role in this agreement?"**
   - Options: Buyer, Seller, Vendor, Customer, Systems Integrator, Channel Partner, Service Provider

3. **"What's the comparison purpose?"**
   - Options: Internal review, Negotiation preparation, Client presentation, Due diligence

4. **"Which sections should I analyze?"**
   - Options: All substantive changes, Specific sections only (user lists), Exclude certain sections

5. **"Do you want recommendations?"**
   - Options: Yes (include Accept/Negotiate/Monitor guidance), No (just document changes)

**Document type verification:**
Before proceeding, analyze both documents and alert user:
- "I see [Contract Type A] V[X] and [Contract Type B] V[Y]"
- "Confirm: comparing versions of same agreement?"
- Wait for explicit confirmation

**Checkpoint 1:** Save user context (role, purpose, scope, recommendations flag)

---

### Phase 2: Extract Documents

**Read the docx skill documentation first:**
```bash
cat /mnt/skills/public/docx/SKILL.md
```

**Extract both documents using pandoc:**
```bash
pandoc --track-changes=accept file1.docx -o v1_extracted.md
pandoc --track-changes=accept file2.docx -o v2_extracted.md
```

**Fallback if pandoc unavailable:**
Use python-docx for text extraction (see test script in scripts/ directory)

**Error handling:**
If extraction fails, stop immediately with clear error message and recovery options.

**Checkpoint 2:** Save extracted content

---

### Phase 3: Detect and Match Changes

**Content-based section matching:**
1. Match sections by clause title/content (NOT by section number)
2. Handle section numbering differences gracefully
3. Tie-breaker rule: Latest version is definitive
4. Mark tie-breaker cases with asterisk (*)

**Anonymization token handling:**
- Detect company name variations ([COMPANY_A], [CLIENT], actual names)
- Auto-handle if confidence ≥ 85% that tokens refer to same entity
- Flag for user review if confidence < 85%

**Change detection:**
For each matched section, identify substantive differences.
Ignore: company name substitutions, formatting, typos, grammar fixes

**Checkpoint 3:** Save detected changes with mappings

---

### Phase 4: Classify Impact and Generate Narratives

**Impact classification - Read references/impact-classification.md for detailed rules.**

**Priority order:**
1. Limitation of Liability → CRITICAL
2. Indemnification → CRITICAL
3. IP Ownership → CRITICAL
4. Compliance & Regulatory → CRITICAL
5. Insurance → CRITICAL
6. Operational → HIGH PRIORITY
7. Financial → HIGH PRIORITY
8. Payment terms → Context-dependent (check if tied to SOW or flowdown)

**Business impact generation:**
- Simple/clear changes: AI generates automatically
- Complex changes: Flag for user input
- Strategic QA gate: Present samples to user for approval

**Business impact writing guidelines:**
Focus on: financial, timeline, relationship, operational, risk, strategic effects
Use plain language, be concrete and specific, 2-4 sentences max

**Checkpoint 4:** Save classified changes with narratives

---

### Phase 5: Generate Recommendations (if requested)

**Risk-framed recommendation framework:**

Three-tier structure:
- **CRITICAL ATTENTION** - Significant risk/exposure
- **RECOMMEND REVIEW** - Moderate concern
- **MONITOR** - Low risk, track only

Each recommendation includes:
1. Risk tier
2. Brief rationale (1-2 sentences)
3. Reasonable talking point

**Note:** Use Pattern Library internally but do NOT cite explicitly in output.

**Checkpoint 5:** Save recommendations

---

### Phase 6: Build Document

**Document structure:**

**Part 1: Executive Summary**
- Document title and version identifiers
- Change summary table (counts by impact category)
- Executive overview narrative (2-3 paragraphs)
- Key themes (bullet list)

**Part 2: Detailed Comparison Table (5 columns)**

| # | Section / Recommendation | V[X] Clause Language | V[Y] Clause Language | Business Impact |
|:---:|:---|:---|:---|:---|
| 1 | Section X.X<br>Recommendation: [Tier]<br>Rationale: [Brief] | [Exact original] | ~~Deleted RED~~<br>**Added GREEN** | [2-4 sentence narrative] |

**Column width priority:**
1. Readability (most important)
2. Minimize pages
3. Content space needs

**Dynamic width allocation:**
- Column 1 (#): 5%
- Column 2 (Section/Rec): 20%
- Column 3 (V[X]): 25-30%
- Column 4 (V[Y]): 25-30%
- Column 5 (Impact): 20-25%

---

### Phase 7: Validate Output

**Comprehensive validation checklist:**
- [ ] All substantive changes captured
- [ ] Section references accurate
- [ ] Redline formatting correct (RED deletions, GREEN additions)
- [ ] Business impact narratives complete
- [ ] Recommendations present if requested
- [ ] Executive summary totals match table count
- [ ] Impact classifications follow rules
- [ ] No company name changes included (unless entity changed)

**If validation fails:** Stop and report issues with recovery options

**Checkpoint 6:** Final state before delivery

---

### Phase 8: Deliver

**Output file:**
```
Filename: [DocName]_V[X]_to_V[Y]_Comparison_[YYYYMMDD].docx
Location: /mnt/user-data/outputs/
Format: Microsoft Word (.docx)
```

Provide summary and download link to user.

---

## Session Continuity

**Auto-checkpoint at:**
1. After user confirmation (Phase 1)
2. After document extraction (Phase 2)
3. After change detection (Phase 3)
4. After impact analysis (Phase 4)
5. After recommendations (Phase 5)
6. Before final generation (Phase 6)

**Recovery on session break:** Load most recent checkpoint, verify context, resume.

---

## Quality Principles

**Legal subject matter - accuracy non-negotiable**
- Validate section references against source documents
- Verify all changes captured
- Check redline formatting precision
- Strategic validation gates (not over-engineering)

**Evidence-based recommendations**
- Use Pattern Library internally for guidance
- Risk-framed language (not imperative)
- Reasonable talking points

**Quality .docx generation is core value**
- Professional formatting
- Readable column widths
- Ready for distribution

---

## References

Load these files when needed:

- `references/impact-classification.md` - Detailed classification logic
- `references/report-format.md` - Complete output specifications (Phase 2)
- `references/validation-checklist.md` - Quality checks (Phase 2)
- `references/pattern-library-guide.md` - Internal pattern usage (Phase 2)

---

**END OF SKILL.md**
