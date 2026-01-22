#!/usr/bin/env python3
"""
Generate HTML report from PDF metadata extraction results.

Creates a comprehensive HTML dashboard with:
- Execution status distribution
- Priority contracts
- Duplicate detection
- Signature statistics
- Searchable contract table
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter


def generate_html_report(json_path, output_path):
    """Generate HTML report from extraction results."""

    # Load data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['pdfs']
    metadata = data['metadata']

    # Calculate statistics
    total = len(results)
    statuses = Counter(r['execution_status'] for r in results)
    has_sigs = sum(1 for r in results if r['has_digital_signatures'])
    avg_conf = sum(r['execution_confidence'] for r in results) / total
    high_conf = sum(1 for r in results if r['execution_confidence'] >= 70)

    # Priority contracts
    priority = [r for r in results if r['execution_status'] in ['unsigned', 'unknown'] or r['execution_confidence'] < 60]
    priority.sort(key=lambda x: x['execution_confidence'])

    # HTML template
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Metadata Extraction Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }}

        .status-bars {{
            margin: 20px 0;
        }}

        .status-bar {{
            margin-bottom: 15px;
        }}

        .status-bar-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}

        .status-bar-bg {{
            background: #f0f0f0;
            height: 30px;
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }}

        .status-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
            transition: width 0.5s ease;
        }}

        .status-bar-fill.partial {{
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        }}

        .status-bar-fill.unknown {{
            background: linear-gradient(90deg, #ffecd2 0%, #fcb69f 100%);
            color: #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #dee2e6;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}

        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .confidence {{
            font-weight: 600;
        }}

        .confidence-high {{
            color: #28a745;
        }}

        .confidence-medium {{
            color: #ffc107;
        }}

        .confidence-low {{
            color: #dc3545;
        }}

        .search-box {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }}

        .search-box:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .filename {{
            color: #667eea;
            font-weight: 500;
        }}

        .sig-yes {{
            color: #28a745;
            font-weight: bold;
        }}

        .sig-no {{
            color: #dc3545;
        }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        .chart {{
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 PDF Metadata Extraction Report</h1>
            <div class="subtitle">
                Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} |
                Total Contracts: {total}
            </div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Contracts</div>
            </div>

            <div class="stat-card">
                <div class="stat-value">{statuses.get('fully_executed', 0)}</div>
                <div class="stat-label">Fully Executed</div>
            </div>

            <div class="stat-card">
                <div class="stat-value">{has_sigs}</div>
                <div class="stat-label">With Digital Signatures</div>
            </div>

            <div class="stat-card">
                <div class="stat-value">{avg_conf:.1f}%</div>
                <div class="stat-label">Average Confidence</div>
            </div>
        </div>

        <div class="section">
            <h2>Execution Status Distribution</h2>
            <div class="status-bars">
                <div class="status-bar">
                    <div class="status-bar-header">
                        <span><strong>Fully Executed</strong></span>
                        <span>{statuses.get('fully_executed', 0)} contracts ({statuses.get('fully_executed', 0)/total*100:.1f}%)</span>
                    </div>
                    <div class="status-bar-bg">
                        <div class="status-bar-fill" style="width: {statuses.get('fully_executed', 0)/total*100}%">
                            {statuses.get('fully_executed', 0)} contracts
                        </div>
                    </div>
                </div>

                <div class="status-bar">
                    <div class="status-bar-header">
                        <span><strong>Partially Executed</strong></span>
                        <span>{statuses.get('partially_executed', 0)} contracts ({statuses.get('partially_executed', 0)/total*100:.1f}%)</span>
                    </div>
                    <div class="status-bar-bg">
                        <div class="status-bar-fill partial" style="width: {statuses.get('partially_executed', 0)/total*100}%">
                            {statuses.get('partially_executed', 0)} contracts
                        </div>
                    </div>
                </div>

                <div class="status-bar">
                    <div class="status-bar-header">
                        <span><strong>Unknown</strong></span>
                        <span>{statuses.get('unknown', 0)} contracts ({statuses.get('unknown', 0)/total*100:.1f}%)</span>
                    </div>
                    <div class="status-bar-bg">
                        <div class="status-bar-fill unknown" style="width: {statuses.get('unknown', 0)/total*100}%">
                            {statuses.get('unknown', 0)} contracts
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>⚠️ Priority Contracts ({len(priority)} need attention)</h2>
            <p style="margin-bottom: 20px; color: #666;">
                Contracts with unknown execution status or low confidence scores requiring manual review.
            </p>

            <table id="priorityTable">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Signatures</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add priority contracts
    for r in priority[:50]:  # Limit to first 50
        filename = r['document_metadata']['filename']
        status = r['execution_status']
        conf = r['execution_confidence']
        has_sig = r['has_digital_signatures']

        status_badge = 'badge-danger' if status == 'unknown' else 'badge-warning'
        conf_class = 'confidence-high' if conf >= 70 else ('confidence-medium' if conf >= 50 else 'confidence-low')
        sig_text = '<span class="sig-yes">Yes</span>' if has_sig else '<span class="sig-no">No</span>'

        html += f"""
                    <tr>
                        <td class="filename">{filename[:80]}</td>
                        <td><span class="badge {status_badge}">{status.replace('_', ' ').title()}</span></td>
                        <td class="{conf_class}">{conf}%</td>
                        <td>{sig_text}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📋 All Contracts</h2>
            <input type="text" id="searchBox" class="search-box" placeholder="🔍 Search contracts by filename...">

            <table id="contractsTable">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Signatures</th>
                        <th>Pages</th>
                    </tr>
                </thead>
                <tbody id="contractsBody">
"""

    # Add all contracts (sorted by filename)
    sorted_results = sorted(results, key=lambda x: x['document_metadata']['filename'])
    for r in sorted_results:
        filename = r['document_metadata']['filename']
        status = r['execution_status']
        conf = r['execution_confidence']
        has_sig = r['has_digital_signatures']
        pages = r['document_metadata'].get('page_count', 'N/A')

        if status == 'fully_executed':
            status_badge = 'badge-success'
        elif status == 'partially_executed':
            status_badge = 'badge-warning'
        else:
            status_badge = 'badge-danger'

        conf_class = 'confidence-high' if conf >= 70 else ('confidence-medium' if conf >= 50 else 'confidence-low')
        sig_text = '<span class="sig-yes">Yes</span>' if has_sig else '<span class="sig-no">No</span>'

        html += f"""
                    <tr>
                        <td class="filename">{filename[:80]}</td>
                        <td><span class="badge {status_badge}">{status.replace('_', ' ').title()}</span></td>
                        <td class="{conf_class}">{conf}%</td>
                        <td>{sig_text}</td>
                        <td>{pages}</td>
                    </tr>
"""

    html += f"""
                </tbody>
            </table>
        </div>

        <footer>
            <p>CIP PDF Metadata Extraction System | {total} contracts processed</p>
        </footer>
    </div>

    <script>
        // Search functionality
        document.getElementById('searchBox').addEventListener('keyup', function() {{
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#contractsBody tr');

            rows.forEach(row => {{
                const filename = row.cells[0].textContent.toLowerCase();
                if (filename.includes(searchTerm)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] HTML report generated: {output_path}")
    return output_path


if __name__ == '__main__':
    # Find latest JSON export (check recurring first, then full_portfolio)
    search_paths = [
        Path('outputs/recurring/exports'),
        Path('outputs/full_portfolio/exports')
    ]

    json_files = []
    for path in search_paths:
        if path.exists():
            json_files.extend(path.glob('metadata_export_*.json'))

    if not json_files:
        print("ERROR: No JSON export found in outputs/recurring or outputs/full_portfolio")
        exit(1)

    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    output_dir = latest_json.parent.parent
    output_path = output_dir / 'extraction_report.html'

    print(f"\nGenerating HTML report from: {latest_json.name}")
    generate_html_report(latest_json, output_path)
    print(f"\nHTML report created: {output_path.absolute()}")
    print(f"Open in browser to view interactive dashboard")
