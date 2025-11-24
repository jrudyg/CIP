# Validation Checklist v2

## Purpose

This checklist ensures each comparison table entry meets quality standards before inclusion in the final report.

---

## Pre-Comparison Checklist

### Document Verification
- [ ] Both files are .docx format (not .doc, .pdf, .rtf)
- [ ] Files are versions of the SAME contract (not different agreements)
- [ ] V1 (baseline) and V2 (revised) clearly identified
- [ ] Files open without errors
- [ ] Text extractable via pandoc or python-docx

### Context Verification
- [ ] User's position confirmed (Buyer/Seller/Vendor/etc.)
- [ ] Comparison purpose clear (QA/QC, negotiation, presentation)
- [ ] Expected changes provided (if available)
- [ ] Leverage level understood (Strong/Balanced/Weak)

---

## Entry-Level Validation (For Each Change)

### 1. Section Reference Accuracy
**Requirement:** Section number exists in V2 document and matches content

**Check:**
- [ ] Section number format matches V2 document style
- [ ] Section exists in V2 (search document to verify)
- [ ] Section title accurate
- [ ] If section renumbered from V1, V2 number prevails

**Common Errors:**
- Using V1 section number instead of V2
- Invented section numbers not in document
- Wrong section title

---

### 2. V1 Text Accuracy
**Requirement:** Quoted text matches V1 document exactly

**Check:**
- [ ] Text found in V1 document (search to verify)
- [ ] Minimum 10-15 words of context
- [ ] No paraphrasing (exact quote)
- [ ] Truncation indicated with "..." if over 500 chars

**Common Errors:**
- Paraphrased instead of exact quote
- Text from wrong section
- Missing context (too short)

---

### 3. V2 Text Accuracy
**Requirement:** Quoted text matches V2 document exactly

**Check:**
- [ ] Text found in V2 document (search to verify)
- [ ] Full change captured (not partial)
- [ ] No paraphrasing
- [ ] Truncation indicated with "..." if over 500 chars

**Common Errors:**
- Incomplete change capture
- Mixed V1 and V2 text
- Summary instead of quote

---

### 4. Redline Formatting
**Requirement:** Deletions and additions properly marked

**Check:**
- [ ] Deleted text: RED (#FF0000) with strikethrough
- [ ] Added text: GREEN (#00B050) with bold
- [ ] Unchanged text: Normal formatting
- [ ] All segments accounted for (no gaps)
- [ ] Inline format (deletion and addition in flow)

**Common Errors:**
- Wrong colors
- Missing strikethrough on deletions
- Missing bold on additions
- Gaps in redline (missing text)

---

### 5. Change Completeness
**Requirement:** All substantive differences captured

**Check:**
- [ ] No missing deletions
- [ ] No missing additions
- [ ] No missing modifications
- [ ] Full clause captured (not just first sentence)

**Common Errors:**
- Partial capture (first change only)
- Missed nested changes
- Missed definition changes

---

### 6. Business Impact Narrative
**Requirement:** Clear, accurate explanation of change significance

**Check:**
- [ ] Written from user's position perspective
- [ ] 2-4 sentences (not too short, not too long)
- [ ] Plain language (no legalese)
- [ ] Concrete and specific (not vague)
- [ ] Accurate characterization of change

**Common Errors:**
- Too vague ("significant change")
- Wrong perspective (Company vs Provider)
- Missing financial/operational impact
- Inaccurate characterization

---

### 7. Impact Classification
**Requirement:** Category matches change type

**Classification Rules:**

| Category | Clause Types |
|----------|--------------|
| CRITICAL | Liability, Indemnification, IP Ownership, Compliance, Insurance |
| HIGH PRIORITY | Termination, Warranties, Acceptance, Fees/Pricing |
| MODERATE | Payment terms, Operational, Confidentiality, Assignment |
| ADMINISTRATIVE | Force majeure, Contact info, Definitions |

**Check:**
- [ ] Category matches clause type
- [ ] Not over-classified (moderate as critical)
- [ ] Not under-classified (critical as moderate)

---

### 8. Text Length Compliance
**Requirement:** Text within 500 character limit per column

**Check:**
- [ ] V1 text ≤500 characters (or truncated with "...")
- [ ] V2 text ≤500 characters (or truncated with "...")
- [ ] Truncation at logical break (end of sentence preferred)
- [ ] No mid-word truncation

---

### 9. Section Title Accuracy
**Requirement:** Title matches document heading

**Check:**
- [ ] Title matches V2 document exactly
- [ ] Capitalization correct
- [ ] No invented titles

---

## Report-Level Validation

### Executive Summary
- [ ] Change counts accurate (match table rows)
- [ ] Category totals correct
- [ ] Key themes reflect actual changes (5 max)
- [ ] Statistics table formatted correctly

### Comparison Table
- [ ] All validated entries included
- [ ] Entries in logical order (by section number or category)
- [ ] Row numbers sequential
- [ ] No duplicate entries
- [ ] No missing entries

### QA/QC Section
- [ ] Validation summary accurate
- [ ] Methodology described
- [ ] Exclusions listed
- [ ] Review date correct

### Formatting
- [ ] Landscape orientation applied
- [ ] Column widths correct
- [ ] Header row navy background
- [ ] Footer with page numbers
- [ ] Header with document title

---

## QA/QC User Response Handling

### On APPROVE
- [ ] Entry marked as validated
- [ ] Proceed to next clause
- [ ] No changes needed

### On MODIFY
- [ ] Specific corrections identified
- [ ] Corrections applied exactly as specified
- [ ] Entry re-presented for confirmation
- [ ] Re-approval obtained before proceeding

### On FLAG
- [ ] Concern documented
- [ ] Added to flagged items list
- [ ] User decision on handling obtained
- [ ] Appropriate action taken (include with flag, separate section, etc.)

### On REJECT
- [ ] Entry rebuilt from source documents
- [ ] Root cause identified (wrong section, wrong quote, etc.)
- [ ] Rebuilt entry presented for validation
- [ ] Approval obtained before proceeding

---

## Common Validation Failures

### Category: Section Reference
| Error | Cause | Fix |
|-------|-------|-----|
| "Section not found" | Using V1 numbering | Search V2 for content, use V2 number |
| "Wrong title" | Copied from summary | Extract title from actual document |
| "Invented section" | AI hallucination | Verify section exists in source |

### Category: Text Accuracy
| Error | Cause | Fix |
|-------|-------|-----|
| "Text not in document" | Paraphrasing | Extract exact quote |
| "Partial quote" | Insufficient context | Expand to 10-15 words minimum |
| "Mixed versions" | V1/V2 confusion | Re-extract from correct version |

### Category: Redline Formatting
| Error | Cause | Fix |
|-------|-------|-----|
| "Missing deletion" | Incomplete diff | Re-compare texts |
| "Wrong color" | Swapped del/add | RED=delete, GREEN=add |
| "No strikethrough" | Formatting omission | Apply strike to deletions |

### Category: Business Impact
| Error | Cause | Fix |
|-------|-------|-----|
| "Too vague" | Generic language | Add specific implications |
| "Wrong perspective" | Position confusion | Rewrite from user's position |
| "Inaccurate" | Misunderstood change | Re-analyze actual modification |

---

## Pre-Delivery Final Check

Before generating final report:

- [ ] All entries APPROVED (or MODIFIED and re-approved)
- [ ] Flagged items addressed
- [ ] Statistics verified
- [ ] Key themes accurate
- [ ] Output filename follows convention
- [ ] Output location: `/mnt/user-data/outputs/`

---

## Validation Metrics

**Target Quality Levels:**
- Section reference accuracy: 100%
- Quote accuracy: 100%
- Redline formatting: 100%
- Business impact completeness: 100%
- Classification accuracy: 95%+

**Acceptable Error Rate:** 0% for CRITICAL changes, <5% for others

---

**END OF VALIDATION CHECKLIST v2**
