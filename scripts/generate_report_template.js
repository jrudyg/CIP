/**
 * Contract Version Comparison Report Generator
 * 
 * Usage: Adapt this template for specific contract comparisons
 * 
 * Steps:
 * 1. Update CONFIG section with contract-specific details
 * 2. Populate CHANGES array with validated comparison data
 * 3. Run: node generate_report_template.js
 * 
 * Output: Professional Word document with executive summary, 
 *         5-column comparison table, and QA/QC validation notes
 */

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        Header, Footer, AlignmentType, BorderStyle, WidthType, ShadingType, 
        PageNumber, HeadingLevel, PageBreak } = require('docx');
const fs = require('fs');

// ═══════════════════════════════════════════════════════════════
// CONFIG - Update these values for each comparison
// ═══════════════════════════════════════════════════════════════

const CONFIG = {
  contractName: "MASTER SERVICES AGREEMENT",    // e.g., "CHANNEL PARTNER AGREEMENT"
  v1Label: "V1 (Original)",                      // e.g., "October Draft"
  v2Label: "V2 (Final)",                         // e.g., "November Signed"
  comparisonDate: "November 24, 2025",
  position: "Provider (Seller/Vendor)",          // User's role
  leverage: "Balanced",                          // Strong/Balanced/Weak
  outputFilename: "Contract_Comparison_Report.docx"
};

// ═══════════════════════════════════════════════════════════════
// CHANGES - Populate with validated comparison data
// ═══════════════════════════════════════════════════════════════

const CHANGES = [
  // Example entry - copy and modify for each change
  {
    num: 1,
    category: "CRITICAL",        // CRITICAL | HIGH PRIORITY | MODERATE | ADMINISTRATIVE
    section: "Section 7(a)",     // V2 section number (V2 prevails)
    title: "Work Product Definition",
    v1: "Original text from V1 document...",
    // Redline segments: { text, del (boolean), add (boolean) }
    v2Redline: [
      { text: "Unchanged text ", del: false, add: false },
      { text: "deleted text", del: true, add: false },
      { text: "added text", del: false, add: true },
      { text: " more unchanged text.", del: false, add: false }
    ],
    impact: "Business impact narrative explaining the change. 2-4 sentences covering financial, operational, or risk implications from user's position."
  }
  // Add more changes here...
];

// ═══════════════════════════════════════════════════════════════
// STYLING - Color palette and formatting constants
// ═══════════════════════════════════════════════════════════════

const COLORS = {
  navy: "1F4E79",
  mediumBlue: "2E75B6",
  white: "FFFFFF",
  deletion: "FF0000",
  addition: "00B050",
  borderGray: "CCCCCC",
  textGray: "666666",
  criticalRed: "C00000",
  highOrange: "ED7D31",
  moderateBlue: "2E75B6",
  adminGray: "666666",
  totalRowBg: "E8E8E8"
};

const BORDERS = {
  thin: { style: BorderStyle.SINGLE, size: 1, color: COLORS.borderGray },
  header: { style: BorderStyle.SINGLE, size: 2, color: COLORS.navy }
};

const cellBorders = { 
  top: BORDERS.thin, bottom: BORDERS.thin, 
  left: BORDERS.thin, right: BORDERS.thin 
};

const headerBorders = { 
  top: BORDERS.header, bottom: BORDERS.header, 
  left: BORDERS.header, right: BORDERS.header 
};

// Column widths for landscape (total ~14400 DXA)
const COL_WIDTHS = {
  num: 600,           // 4%
  section: 2400,      // 17%
  v1: 4200,           // 29%
  v2: 4200,           // 29%
  impact: 3000        // 21%
};

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Get category color based on impact level
 */
function getCategoryColor(category) {
  const colors = {
    "CRITICAL": COLORS.criticalRed,
    "HIGH PRIORITY": COLORS.highOrange,
    "MODERATE": COLORS.moderateBlue,
    "ADMINISTRATIVE": COLORS.adminGray
  };
  return colors[category] || COLORS.textGray;
}

/**
 * Count changes by category
 */
function countByCategory() {
  const counts = { "CRITICAL": 0, "HIGH PRIORITY": 0, "MODERATE": 0, "ADMINISTRATIVE": 0 };
  CHANGES.forEach(c => counts[c.category] = (counts[c.category] || 0) + 1);
  return counts;
}

/**
 * Create redline text runs from redline segments
 */
function createRedlineRuns(redlineData) {
  return redlineData.map(segment => {
    if (segment.del) {
      return new TextRun({ 
        text: segment.text, 
        color: COLORS.deletion, 
        strike: true, 
        size: 18, 
        font: "Arial" 
      });
    } else if (segment.add) {
      return new TextRun({ 
        text: segment.text, 
        color: COLORS.addition, 
        bold: true, 
        size: 18, 
        font: "Arial" 
      });
    } else {
      return new TextRun({ 
        text: segment.text, 
        size: 18, 
        font: "Arial" 
      });
    }
  });
}

/**
 * Create a standard table cell
 */
function createCell(content, width, isHeader = false, alignment = AlignmentType.LEFT) {
  const children = [];
  
  if (Array.isArray(content)) {
    content.forEach(item => {
      if (typeof item === 'string') {
        children.push(new Paragraph({ 
          alignment, 
          children: [new TextRun({ 
            text: item, 
            size: isHeader ? 18 : 18, 
            bold: isHeader, 
            font: "Arial",
            color: isHeader ? COLORS.white : undefined
          })] 
        }));
      } else {
        children.push(item);
      }
    });
  } else {
    children.push(new Paragraph({ 
      alignment, 
      children: [new TextRun({ 
        text: content, 
        size: isHeader ? 18 : 18, 
        bold: isHeader, 
        font: "Arial",
        color: isHeader ? COLORS.white : undefined
      })] 
    }));
  }
  
  return new TableCell({
    borders: isHeader ? headerBorders : cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: isHeader ? { fill: COLORS.navy, type: ShadingType.CLEAR } : undefined,
    children
  });
}

/**
 * Create a data row for the comparison table
 */
function createDataRow(change) {
  return new TableRow({
    children: [
      // Column 1: Number
      new TableCell({
        borders: cellBorders,
        width: { size: COL_WIDTHS.num, type: WidthType.DXA },
        children: [new Paragraph({ 
          alignment: AlignmentType.CENTER, 
          children: [new TextRun({ text: String(change.num), size: 18, font: "Arial" })] 
        })]
      }),
      // Column 2: Section / Category
      new TableCell({
        borders: cellBorders,
        width: { size: COL_WIDTHS.section, type: WidthType.DXA },
        children: [
          new Paragraph({ children: [new TextRun({ text: change.section, bold: true, size: 18, font: "Arial" })] }),
          new Paragraph({ children: [new TextRun({ text: change.title, size: 18, font: "Arial" })] }),
          new Paragraph({ spacing: { before: 100 }, children: [new TextRun({ 
            text: change.category, 
            bold: true, 
            size: 16, 
            color: getCategoryColor(change.category), 
            font: "Arial" 
          })] })
        ]
      }),
      // Column 3: V1 Original
      new TableCell({
        borders: cellBorders,
        width: { size: COL_WIDTHS.v1, type: WidthType.DXA },
        children: [new Paragraph({ children: [new TextRun({ 
          text: change.v1.substring(0, 500) + (change.v1.length > 500 ? "..." : ""), 
          size: 18, 
          font: "Arial" 
        })] })]
      }),
      // Column 4: V2 Redlined
      new TableCell({
        borders: cellBorders,
        width: { size: COL_WIDTHS.v2, type: WidthType.DXA },
        children: [new Paragraph({ children: createRedlineRuns(change.v2Redline) })]
      }),
      // Column 5: Business Impact
      new TableCell({
        borders: cellBorders,
        width: { size: COL_WIDTHS.impact, type: WidthType.DXA },
        children: [new Paragraph({ children: [new TextRun({ text: change.impact, size: 18, font: "Arial" })] })]
      })
    ]
  });
}

// ═══════════════════════════════════════════════════════════════
// DOCUMENT GENERATION
// ═══════════════════════════════════════════════════════════════

function generateReport() {
  const counts = countByCategory();
  const total = CHANGES.length;
  
  const doc = new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 22 } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal",
          run: { size: 48, bold: true, color: COLORS.navy, font: "Arial" },
          paragraph: { spacing: { after: 200 }, alignment: AlignmentType.CENTER } },
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 28, bold: true, color: COLORS.navy, font: "Arial" },
          paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, color: COLORS.mediumBlue, font: "Arial" },
          paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } }
      ]
    },
    sections: [{
      properties: {
        page: { 
          margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }, 
          size: { orientation: "landscape" } 
        }
      },
      headers: {
        default: new Header({ children: [new Paragraph({ 
          alignment: AlignmentType.RIGHT, 
          children: [new TextRun({ 
            text: `${CONFIG.contractName} Version Comparison Report - CONFIDENTIAL`, 
            size: 18, italics: true, color: COLORS.textGray, font: "Arial" 
          })] 
        })] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({ 
          alignment: AlignmentType.CENTER, 
          children: [
            new TextRun({ text: "Page ", size: 18, font: "Arial" }), 
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial" }), 
            new TextRun({ text: " of ", size: 18, font: "Arial" }), 
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: "Arial" })
          ] 
        })] })
      },
      children: [
        // ═══════════════════════════════════════════════════════════════
        // TITLE PAGE
        // ═══════════════════════════════════════════════════════════════
        new Paragraph({ spacing: { before: 2000 } }),
        new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun(CONFIG.contractName)] }),
        new Paragraph({ 
          alignment: AlignmentType.CENTER, spacing: { after: 400 }, 
          children: [new TextRun({ text: "Version Comparison Report", size: 36, color: COLORS.mediumBlue, font: "Arial" })] 
        }),
        new Paragraph({ 
          alignment: AlignmentType.CENTER, spacing: { after: 600 }, 
          children: [new TextRun({ text: `${CONFIG.v1Label} → ${CONFIG.v2Label}`, size: 28, font: "Arial" })] 
        }),
        new Paragraph({ 
          alignment: AlignmentType.CENTER, 
          children: [new TextRun({ text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", color: COLORS.navy, font: "Arial" })] 
        }),
        new Paragraph({ spacing: { before: 400 } }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `Comparison Date: ${CONFIG.comparisonDate}`, size: 22, font: "Arial" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `Position: ${CONFIG.position}`, size: 22, font: "Arial" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `Leverage: ${CONFIG.leverage}`, size: 22, font: "Arial" })] }),
        new Paragraph({ spacing: { before: 600 } }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "QA/QC VALIDATED", size: 28, bold: true, color: COLORS.addition, font: "Arial" })] }),
        
        // ═══════════════════════════════════════════════════════════════
        // EXECUTIVE SUMMARY
        // ═══════════════════════════════════════════════════════════════
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("EXECUTIVE SUMMARY")] }),
        new Paragraph({ 
          spacing: { after: 200 }, 
          children: [new TextRun({ 
            text: `This report documents all substantive changes between ${CONFIG.v1Label} and ${CONFIG.v2Label}. All changes have been validated through clause-by-clause QA/QC review.`, 
            size: 22, font: "Arial" 
          })] 
        }),
        
        // Statistics table
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Change Statistics")] }),
        new Table({
          columnWidths: [3000, 1500],
          rows: [
            new TableRow({ children: [
              createCell("Impact Category", 3000, true),
              createCell("Count", 1500, true, AlignmentType.CENTER)
            ]}),
            new TableRow({ children: [createCell("CRITICAL", 3000), createCell(String(counts["CRITICAL"]), 1500, false, AlignmentType.CENTER)] }),
            new TableRow({ children: [createCell("HIGH PRIORITY", 3000), createCell(String(counts["HIGH PRIORITY"]), 1500, false, AlignmentType.CENTER)] }),
            new TableRow({ children: [createCell("MODERATE", 3000), createCell(String(counts["MODERATE"]), 1500, false, AlignmentType.CENTER)] }),
            new TableRow({ children: [createCell("ADMINISTRATIVE", 3000), createCell(String(counts["ADMINISTRATIVE"]), 1500, false, AlignmentType.CENTER)] }),
            new TableRow({ children: [
              new TableCell({ 
                borders: headerBorders, width: { size: 3000, type: WidthType.DXA }, 
                shading: { fill: COLORS.totalRowBg, type: ShadingType.CLEAR }, 
                children: [new Paragraph({ children: [new TextRun({ text: "TOTAL SUBSTANTIVE", bold: true, size: 20, font: "Arial" })] })] 
              }),
              new TableCell({ 
                borders: headerBorders, width: { size: 1500, type: WidthType.DXA }, 
                shading: { fill: COLORS.totalRowBg, type: ShadingType.CLEAR }, 
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: String(total), bold: true, size: 20, font: "Arial" })] })] 
              })
            ]})
          ]
        }),
        
        // Key themes placeholder
        new Paragraph({ spacing: { before: 300 }, heading: HeadingLevel.HEADING_2, children: [new TextRun("Key Themes")] }),
        new Paragraph({ children: [
          new TextRun({ text: "• ", font: "Arial" }), 
          new TextRun({ text: "Theme 1: ", bold: true, font: "Arial" }), 
          new TextRun({ text: "Description of first major theme or pattern", font: "Arial" })
        ] }),
        new Paragraph({ children: [
          new TextRun({ text: "• ", font: "Arial" }), 
          new TextRun({ text: "Theme 2: ", bold: true, font: "Arial" }), 
          new TextRun({ text: "Description of second major theme or pattern", font: "Arial" })
        ] }),
        new Paragraph({ children: [
          new TextRun({ text: "• ", font: "Arial" }), 
          new TextRun({ text: "Theme 3: ", bold: true, font: "Arial" }), 
          new TextRun({ text: "Description of third major theme or pattern", font: "Arial" })
        ] }),
        
        // ═══════════════════════════════════════════════════════════════
        // DETAILED COMPARISON TABLE
        // ═══════════════════════════════════════════════════════════════
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("DETAILED COMPARISON TABLE")] }),
        new Paragraph({ 
          spacing: { after: 100 }, 
          children: [
            new TextRun({ text: "Legend: ", bold: true, size: 20, font: "Arial" }), 
            new TextRun({ text: "Deleted text", strike: true, color: COLORS.deletion, size: 20, font: "Arial" }), 
            new TextRun({ text: " | ", size: 20, font: "Arial" }), 
            new TextRun({ text: "Added text", bold: true, color: COLORS.addition, size: 20, font: "Arial" })
          ] 
        }),
        
        // Comparison table
        new Table({
          columnWidths: [COL_WIDTHS.num, COL_WIDTHS.section, COL_WIDTHS.v1, COL_WIDTHS.v2, COL_WIDTHS.impact],
          rows: [
            // Header row
            new TableRow({ 
              tableHeader: true, 
              children: [
                createCell("#", COL_WIDTHS.num, true, AlignmentType.CENTER),
                createCell("Section / Category", COL_WIDTHS.section, true),
                createCell(CONFIG.v1Label, COL_WIDTHS.v1, true),
                createCell(`${CONFIG.v2Label} - Redlined`, COL_WIDTHS.v2, true),
                createCell("Business Impact", COL_WIDTHS.impact, true)
              ]
            }),
            // Data rows
            ...CHANGES.map(c => createDataRow(c))
          ]
        }),
        
        // ═══════════════════════════════════════════════════════════════
        // QA/QC VALIDATION NOTES
        // ═══════════════════════════════════════════════════════════════
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("QA/QC VALIDATION NOTES")] }),
        new Paragraph({ children: [new TextRun({ 
          text: "This comparison report has been validated through systematic clause-by-clause QA/QC review.", 
          size: 22, font: "Arial" 
        })] }),
        
        new Paragraph({ spacing: { before: 200 }, heading: HeadingLevel.HEADING_2, children: [new TextRun("Validation Summary")] }),
        new Paragraph({ children: [new TextRun({ text: `• Total changes validated: ${total}`, font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "• Section references verified against source documents", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "• V2 section numbers and text prevail in all cases", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "• Redline formatting verified (RED strikethrough = deleted, GREEN bold = added)", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "• Business impact descriptions reviewed for accuracy", font: "Arial" })] }),
        
        new Paragraph({ spacing: { before: 200 }, heading: HeadingLevel.HEADING_2, children: [new TextRun("Methodology")] }),
        new Paragraph({ children: [new TextRun({ text: "1. Documents extracted and converted to markdown for comparison", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "2. Each substantive change identified and categorized by impact level", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "3. Clause-by-clause validation against source documents", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "4. Corrections applied based on user QA/QC feedback", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "5. Final report generated with validated entries only", font: "Arial" })] }),
        
        new Paragraph({ spacing: { before: 200 }, heading: HeadingLevel.HEADING_2, children: [new TextRun("Excluded from Analysis")] }),
        new Paragraph({ children: [new TextRun({ text: "• Anonymized entity names and addresses (formatting tokens only)", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "• Typographical and grammatical corrections", font: "Arial" })] }),
        new Paragraph({ children: [new TextRun({ text: "• Formatting changes without substantive impact", font: "Arial" })] }),
        
        new Paragraph({ spacing: { before: 400 }, children: [new TextRun({ text: "— END OF REPORT —", bold: true, color: COLORS.navy, font: "Arial" })] })
      ]
    }]
  });
  
  return doc;
}

// ═══════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ═══════════════════════════════════════════════════════════════

const doc = generateReport();

Packer.toBuffer(doc).then(buffer => {
  const outputPath = `/mnt/user-data/outputs/${CONFIG.outputFilename}`;
  fs.writeFileSync(outputPath, buffer);
  console.log(`✅ Report generated: ${CONFIG.outputFilename}`);
}).catch(err => {
  console.error('❌ Error generating report:', err);
});
