# Report Format Specifications v2.0

## Critical Changes from v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Orientation | Portrait (default) | **LANDSCAPE (mandatory)** |
| Table width | Variable | **Full page width (15,300 DXA)** |
| Section numbers | Text-based extraction | **Word numbering.xml extraction** |
| QA/QC section | Optional | **Mandatory** |
| Reviewer attribution | Not included | **Mandatory signature line** |
| Legal disclaimer | Not included | **Mandatory boilerplate** |
| Page breaks | After each section | **NONE unless natural** |
| Whitespace | Default spacing | **Minimized throughout** |

---

## Document Structure

### 1. Title Block (Compact)

**Required Elements (single page area):**
- Title: "Version Comparison Report" (centered, 20pt bold)
- Version line: "[V1 Name] → [V2 Name]" (centered, 10pt)
- Context line: "Date | Position: [Role] ([Party]) | Purpose: [Purpose]" (centered, 10pt)

**Formatting:**
- NO page break after title
- Minimal spacing: 60 twips after title
- Combine metadata on single line where possible

---

### 2. Executive Summary

**2.1 Impact Summary Table**
- 2 columns: Impact Category | Count
- Color-coded rows by impact level
- Compact: no extra spacing between rows

**2.2 Key Themes**
- Numbered list (1-5 items)
- Single line per theme, concise
- Format: "**Theme:** Description"

**Spacing:**
- 160 twips before heading
- 40 twips between items
- 80 twips after section

---

### 3. Detailed Comparison Table

**MANDATORY: Landscape, Full Width**

#### Column Specifications (DXA values)

| Col | Header | Width | Notes |
|-----|--------|-------|-------|
| 1 | # | 650 | Center aligned, row number |
| 2 | Section/Impact | 2,350 | Section number + title + impact level |
| 3 | V1 (Original) | 4,450 | Original text, italics if "[No provision]" |
| 4 | V2 (Final) - Redlined | 4,450 | Redlined changes |
| 5 | Business Impact | 3,400 | Plain language impact narrative |

**Total Width:** 15,300 DXA = full landscape page with 0.5" margins

#### Column 2 Content Structure

```
[Section Number]     ← Bold, e.g., "IV.B", "II.", "Exh. A"
[Section Title]      ← Bold, smaller, e.g., "Records and Audit"
[Subsection Title]   ← Italic, e.g., "Customer Confidentiality"
[IMPACT LEVEL]       ← Bold, colored text
```

**Section Number Formats:**
- Roman numerals: I., II., III., IV., V., VI., VII.
- Subsections: IV.A, IV.B, IV.C, IV.D
- Exhibits: Exh. A, Exh. B

#### Impact Level Colors (Cell Background)

| Impact | Background Color | Text Color |
|--------|-----------------|------------|
| CRITICAL | #FFCDD2 (light red) | #C00000 (dark red) |
| HIGH PRIORITY | #FFE0B2 (light orange) | #E65100 (dark orange) |
| MODERATE | #FFF9C4 (light yellow) | #F9A825 (dark yellow) |
| LOW | #C8E6C9 (light green) | #2E7D32 (dark green) |

#### Table Row Properties

```javascript
new TableRow({
  cantSplit: true,  // CRITICAL: prevents row from breaking across pages
  children: [...]
})
```

---

## Redline Formatting Standards

### Color Codes (v2.0)

| Type | Color | Hex | RGB |
|------|-------|-----|-----|
| Deletion | Dark Red | #C00000 | 192, 0, 0 |
| Addition | Dark Green | #006400 | 0, 100, 0 |

### Formatting

**Deletions:**
```javascript
new TextRun({ text: "deleted text", color: "C00000", strike: true, size: 18 })
```

**Additions:**
```javascript
new TextRun({ text: "added text", color: "006400", bold: true, size: 18 })
```

---

## QA/QC Section (Mandatory)

### Required Components

**1. Quality Assurance Statement**
Single paragraph describing methodology.

**2. Validation Summary Table**

| Validation Item | Status |
|-----------------|--------|
| Source Documents Extracted | ✓ V1 and V2 .docx files extracted |
| Changes Identified | ✓ [N] substantive changes documented |
| Impact Classification | ✓ [breakdown by level] |
| Redline Accuracy | ✓ Visual redlines match source text |

**3. Review Information Line**
```
Report Generated: [Date]  |  Methodology: [Tool]  |  Reviewed By: _______________________
```

**4. Items Requiring Attention**
Numbered list of flagged items with section references.

**5. Legal Disclaimer**
Standard boilerplate (see below), gray background (#F5F5F5), italic, 8pt.

---

## Legal Disclaimer (Mandatory Boilerplate)

```
LEGAL DISCLAIMER: This comparison report is provided for informational purposes 
only and does not constitute legal advice. The analysis reflects a summary of 
changes between document versions and should not be relied upon as a complete 
legal review. Users should consult with qualified legal counsel before making 
any decisions based on this report. The authors and generators of this report 
make no warranties, express or implied, regarding the accuracy, completeness, 
or fitness for any particular purpose of the information contained herein. 
By using this report, you acknowledge that you have read and understood this 
disclaimer.
```

**Formatting:**
- Background: #F5F5F5 (light gray)
- Font: 8pt italic
- Spacing before: 200 twips

---

## Spacing Guidelines (Minimize Whitespace)

### Heading Spacing

| Element | Before (twips) | After (twips) |
|---------|----------------|---------------|
| Title | 0 | 60 |
| Heading 1 | 160 | 80 |
| Heading 2 | 120 | 60 |

### Paragraph Spacing

| Context | After (twips) |
|---------|---------------|
| Key Themes items | 40 |
| Table cell content | 40 |
| QA/QC items | 80 |

### Table Cell Padding

```javascript
spacing: { before: 40, after: 40 }  // Inside paragraph
```

---

## Font Specifications (Compact)

| Element | Font | Size (half-pts) | Actual Size |
|---------|------|-----------------|-------------|
| Title | Arial | 40 | 20pt |
| Heading 1 | Arial | 26 | 13pt |
| Heading 2 | Arial | 22 | 11pt |
| Body text | Arial | 20 | 10pt |
| Table headers | Arial | 20 | 10pt |
| Table content | Arial | 18-20 | 9-10pt |
| Business Impact | Arial | 16 | 8pt |
| Disclaimer | Arial | 16 | 8pt |

---

## Page Layout

### Orientation: LANDSCAPE (Mandatory)

```javascript
properties: {
  page: {
    size: { orientation: PageOrientation.LANDSCAPE },
    margin: { top: 720, right: 720, bottom: 720, left: 720 }  // 0.5" all sides
  }
}
```

### Page Breaks: NONE

Do NOT use `pageBreakBefore: true` on any section unless absolutely necessary.

Let content flow naturally. The table's `cantSplit: true` rows will handle page breaks appropriately.

---

## Section Number Extraction

### Problem
Word contracts often use automatic numbering (Roman numerals) that renders visually but isn't in the paragraph text.

### Solution
Parse `word/numbering.xml` to reconstruct rendered numbers:

1. **Extract numId from paragraph:** `w:pPr/w:numPr/w:numId`
2. **Get indent level:** `w:pPr/w:numPr/w:ilvl`
3. **Look up abstract numbering definition**
4. **Track counters per numId**
5. **Render based on format:** `upperRoman`, `lowerLetter`, `decimal`

### Common Patterns

| Pattern | Level 0 | Level 1 | Level 2 |
|---------|---------|---------|---------|
| Legal outline | I., II., III. | A., B., C. | 1., 2., 3. |
| Contract sections | I., II. | IV.A, IV.B | - |
| Exhibits | Exh. A, Exh. B | - | - |

---

## File Naming Convention

```
[ContractName]_V[X]_to_V[Y]_Comparison_[YYYYMMDD].docx
```

**Examples:**
- `PET_RETAILER_ROYALTY_V1_to_V2_Comparison_20251216.docx`
- `MSA_V3_to_V4_Comparison_20250118.docx`

---

## Quality Checklist

### Before Generation
- [ ] Landscape orientation set
- [ ] Full-width table (15,300 DXA)
- [ ] Column widths correct: `[650, 2350, 4450, 4450, 3400]`
- [ ] Section numbers from Word numbering (not text regex)
- [ ] cantSplit: true on all table rows

### After Generation
- [ ] No excessive whitespace
- [ ] No unexpected page breaks
- [ ] QA/QC section present
- [ ] Reviewed By field with signature line
- [ ] Legal disclaimer present
- [ ] Redlines render correctly (RED/GREEN)

---

**END OF REPORT FORMAT SPECIFICATIONS v2.0**
