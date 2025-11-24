# Report Format Specifications v2

## Document Layout

### Page Setup
- **Orientation:** Landscape (required for 5-column table readability)
- **Paper size:** Letter (11" x 8.5")
- **Margins:** 0.75" all sides (1080 DXA)

### Fonts
- **Primary font:** Arial (universally supported, clean, professional)
- **Body text:** 11pt (size: 22 in docx-js)
- **Table text:** 9pt (size: 18 in docx-js)
- **Headers:** Bold, navy color (#1F4E79)

---

## Document Structure (4 Required Sections)

### Section 1: Title Page

**Layout:**
```
[Vertical space ~2000 DXA]

[CONTRACT NAME]                    ← Title, 28pt bold, centered, navy
Version Comparison Report          ← Subtitle, 18pt, centered, medium blue
V1 (Original) → V2 (Final)         ← Version identifiers, 14pt, centered

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ← Separator line, navy

Comparison Date: [Month DD, YYYY]   ← 11pt, centered
Position: [User's role]             ← 11pt, centered
Leverage: [Strong/Balanced/Weak]    ← 11pt, centered

[Vertical space]

QA/QC VALIDATED                     ← 14pt bold, centered, green (#00B050)
```

### Section 2: Executive Summary

**2.1 Change Statistics Table**

| Impact Category | Count |
|-----------------|-------|
| CRITICAL | ## |
| HIGH PRIORITY | ## |
| MODERATE | ## |
| ADMINISTRATIVE | ## |
| **TOTAL SUBSTANTIVE** | **##** |

- Header row: Navy background (#1F4E79), white text
- Total row: Gray background (#E8E8E8), bold
- Column widths: 3000 DXA, 1500 DXA

**2.2 Key Themes (5 bullets)**

Format:
```
• **Theme Title:** Brief description of the negotiation outcome or pattern
```

Example themes:
- Phase-Based IP Transfer
- Mutual Obligations
- Operational Protections
- Removed Restrictions
- Standard Adjustments

---

### Section 3: Detailed Comparison Table

**Table Structure: 5 Columns**

| # | Section / Category | V1 (Original) | V2 (Final) - Redlined | Business Impact |
|:-:|:-------------------|:--------------|:----------------------|:----------------|

**Column Specifications:**

| Column | Header | Width (DXA) | Width (%) | Alignment |
|--------|--------|-------------|-----------|-----------|
| 1 | # | 600 | 4% | Center |
| 2 | Section / Category | 2400 | 17% | Left |
| 3 | V1 (Original) | 4200 | 29% | Left |
| 4 | V2 (Final) - Redlined | 4200 | 29% | Left |
| 5 | Business Impact | 3000 | 21% | Left |

**Column 2 Content Structure:**
```
Section 7(a)                       ← Bold, 9pt
Work Product Definition            ← Normal, 9pt
                                   ← Blank line
CRITICAL                           ← Bold, 8pt, colored by category
```

**Category Colors:**
- CRITICAL: #C00000 (dark red)
- HIGH PRIORITY: #ED7D31 (orange)
- MODERATE: #2E75B6 (blue)
- ADMINISTRATIVE: #666666 (gray)

**Column 4 Redline Formatting:**
- Deletions: RED (#FF0000), strikethrough
- Additions: GREEN (#00B050), bold
- Unchanged text: Normal formatting

**Text Limits:**
- V1/V2 columns: 500 characters max (truncate with "...")
- Business Impact: No hard limit, but 2-4 sentences typical

---

### Section 4: QA/QC Validation Notes

**4.1 Validation Summary**
- Total changes validated: [X]
- Section references verified against source documents
- V2 section numbers and text prevail in all cases
- Redline formatting verified (RED strikethrough = deleted, GREEN bold = added)
- Business impact descriptions reviewed for accuracy

**4.2 Methodology**
1. Documents extracted and converted to markdown for comparison
2. Each substantive change identified and categorized by impact level
3. Clause-by-clause validation against source documents
4. Corrections applied based on user QA/QC feedback
5. Final report generated with validated entries only

**4.3 Excluded from Analysis**
- Anonymized entity names and addresses (formatting tokens only)
- Typographical and grammatical corrections
- Formatting changes without substantive impact

---

## Color Palette (Exact Hex Values)

| Purpose | Color Name | Hex | RGB |
|---------|------------|-----|-----|
| Header background | Navy | #1F4E79 | 31, 78, 121 |
| Header text | White | #FFFFFF | 255, 255, 255 |
| Accent headings | Medium Blue | #2E75B6 | 46, 117, 182 |
| Deletion text | Red | #FF0000 | 255, 0, 0 |
| Addition text | Green | #00B050 | 0, 176, 80 |
| Table borders | Light gray | #CCCCCC | 204, 204, 204 |
| Critical badge | Dark red | #C00000 | 192, 0, 0 |
| High priority badge | Orange | #ED7D31 | 237, 125, 49 |
| Moderate badge | Blue | #2E75B6 | 46, 117, 182 |
| Admin badge | Gray | #666666 | 102, 102, 102 |
| Total row background | Light gray | #E8E8E8 | 232, 232, 232 |

---

## Headers and Footers

**Header (Right-aligned):**
```
[Contract Name] Version Comparison Report - CONFIDENTIAL
```
- 9pt, italic, gray (#666666)

**Footer (Centered):**
```
Page [X] of [Y]
```
- 9pt, normal

---

## File Naming Convention

**Format:**
```
[ContractName]_V[X]_to_V[Y]_Comparison_QA_Validated_[YYYYMMDD].docx
```

**Examples:**
- `MSA_V1_to_V2_Comparison_QA_Validated_20251124.docx`
- `ChannelPartner_Original_to_Final_Comparison_QA_Validated_20251124.docx`

**Rules:**
- No spaces (use underscores)
- Date format: YYYYMMDD
- Include "QA_Validated" if clause-by-clause review completed

---

## docx-js Implementation Notes

**Document styles:**
```javascript
styles: {
  default: { document: { run: { font: "Arial", size: 22 } } },
  paragraphStyles: [
    { id: "Title", name: "Title", basedOn: "Normal",
      run: { size: 48, bold: true, color: "1F4E79", font: "Arial" },
      paragraph: { spacing: { after: 200 }, alignment: AlignmentType.CENTER } },
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, bold: true, color: "1F4E79", font: "Arial" },
      paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 24, bold: true, color: "2E75B6", font: "Arial" },
      paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } }
  ]
}
```

**Table header cell:**
```javascript
new TableCell({
  borders: headerBorders,
  width: { size: width, type: WidthType.DXA },
  shading: { fill: "1F4E79", type: ShadingType.CLEAR },
  children: [new Paragraph({
    children: [new TextRun({ text: "Header", bold: true, color: "FFFFFF", size: 18, font: "Arial" })]
  })]
})
```

**Redline text runs:**
```javascript
// Deletion
new TextRun({ text: "deleted text", color: "FF0000", strike: true, size: 18, font: "Arial" })

// Addition
new TextRun({ text: "added text", color: "00B050", bold: true, size: 18, font: "Arial" })
```

---

## Quality Checklist (Before Delivery)

- [ ] Landscape orientation applied
- [ ] All column widths set correctly
- [ ] Header row has navy background
- [ ] All deletions are RED (#FF0000) with strikethrough
- [ ] All additions are GREEN (#00B050) with bold
- [ ] Executive summary counts match table rows
- [ ] Category badges colored correctly
- [ ] Page numbers in footer
- [ ] File saved to /mnt/user-data/outputs/
- [ ] Filename follows convention

---

**END OF REPORT FORMAT SPECIFICATIONS v2**
