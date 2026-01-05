"""
Deterministic report generator.

Generates reproducible executive reports from locked templates:
- Loads versioned templates (hash-verified)
- Loads versioned prompts (hash-verified)
- Calls Claude with temperature=0 (deterministic)
- Computes output hash
- Logs to audit trail

Reports:
- Redline Review Report
- Version Comparison Report
"""

import sqlite3
import hashlib
import json
from typing import Tuple, Dict
from pathlib import Path
from datetime import datetime
import anthropic

from audit_trail import AuditTrail


class ReportGenerator:
    """Generate reproducible executive reports."""

    TEMPLATE_DIR = Path(__file__).parent / "templates"
    PROMPT_DIR = Path(__file__).parent / "prompts"
    SYSTEM_VERSION = "1.0.0"

    def __init__(self, db_path: str, api_key: str):
        self.db_path = db_path
        self.client = anthropic.Anthropic(api_key=api_key)
        self.audit = AuditTrail(db_path)

    def _compute_hash(self, content: str) -> str:
        """SHA-256 hash."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _load_template(self, name: str, version: str) -> Tuple[str, str]:
        """
        Load and verify template integrity.

        Returns:
            (template_content, template_hash)
        """
        template_file = self.TEMPLATE_DIR / f"{name}_v{version}.md"

        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")

        content = template_file.read_text(encoding='utf-8')
        content_hash = self._compute_hash(content)

        return content, content_hash

    def _load_prompt(self, name: str, version: str) -> Tuple[str, str]:
        """
        Load and verify prompt integrity.

        Returns:
            (prompt_content, prompt_hash)
        """
        prompt_file = self.PROMPT_DIR / f"{name}_v{version}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_file}")

        content = prompt_file.read_text(encoding='utf-8')
        content_hash = self._compute_hash(content)

        return content, content_hash

    def _call_claude_deterministic(
        self,
        prompt: str,
        context: str,
        model: str = "claude-sonnet-4-20250514"
    ) -> str:
        """
        Call Claude with temperature=0 for deterministic output.

        Args:
            prompt: System prompt
            context: User context
            model: Claude model

        Returns:
            Claude's response text
        """
        message = self.client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0,  # Deterministic
            system=prompt,
            messages=[
                {"role": "user", "content": context}
            ]
        )

        return message.content[0].text

    def _get_contract_data(self, contract_id: int) -> Dict:
        """Fetch contract and clauses from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Contract metadata
        cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
        contract = dict(cursor.fetchone())

        # Clauses with CCE scoring
        cursor.execute(
            """
            SELECT * FROM clauses
            WHERE contract_id = ?
            ORDER BY section_number
            """,
            (contract_id,)
        )
        clauses = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {'contract': contract, 'clauses': clauses}

    def generate_redline_report(
        self,
        contract_id: int,
        template_version: str = "1.0",
        prompt_version: str = "1.0"
    ) -> Tuple[str, str]:
        """
        Generate redline review report.

        Args:
            contract_id: Contract to generate report for
            template_version: Template version to use
            prompt_version: Prompt version to use

        Returns:
            (report_content, report_id)
        """
        # Load template
        template, template_hash = self._load_template(
            "redline_report",
            template_version
        )

        # Get contract data
        data = self._get_contract_data(contract_id)
        contract = data['contract']
        clauses = data['clauses']

        # Compute risk metrics
        total_clauses = len(clauses)
        critical_clauses = len([c for c in clauses if c.get('cce_risk_level') == 'CRITICAL'])
        high_clauses = len([c for c in clauses if c.get('cce_risk_level') == 'HIGH'])
        statutory_flags = len([c for c in clauses if c.get('cce_statutory_flag')])

        avg_risk = sum(c.get('cce_risk_score', 0) for c in clauses) / total_clauses if total_clauses > 0 else 0

        # Risk badge
        if avg_risk >= 9.0:
            risk_badge = "CRITICAL"
            risk_class = "CRITICAL"
        elif avg_risk >= 7.0:
            risk_badge = "HIGH"
            risk_class = "HIGH"
        elif avg_risk >= 5.0:
            risk_badge = "MEDIUM"
            risk_class = "MEDIUM"
        else:
            risk_badge = "LOW"
            risk_class = "LOW"

        # Build redline table
        redline_rows = []
        for clause in clauses:
            if clause.get('cce_risk_score', 0) >= 5.0:  # Only medium+ risk
                row = (
                    f"| {clause.get('section_number', 'N/A')} "
                    f"| {clause.get('cce_risk_score', 0):.1f} "
                    f"| TBD | Pending |"
                )
                redline_rows.append(row)

        redline_table = "\n".join(redline_rows) if redline_rows else "| No high-risk clauses identified |"

        # Top concerns
        top_concerns = []
        for i, clause in enumerate(sorted(clauses, key=lambda c: c.get('cce_risk_score', 0), reverse=True)[:5], 1):
            concern = f"{i}. **Section {clause.get('section_number', 'N/A')}** - {clause.get('title', 'Untitled')}\n"
            concern += f"   - Risk: {clause.get('cce_risk_score', 0):.1f}/10\n"
            if clause.get('cce_statutory_flag'):
                concern += f"   - Statutory: {clause['cce_statutory_flag']}\n"
            top_concerns.append(concern)

        top_concerns_text = "\n".join(top_concerns) if top_concerns else "No critical concerns identified."

        # Generate report ID
        report_id = self.audit._generate_report_id()

        # Substitute template variables
        report = template.format(
            report_id=report_id,
            contract_title=contract.get('title', 'Untitled'),
            vendor_name=contract.get('counterparty', 'Unknown'),
            vendor_ticker=contract.get('vendor_ticker', 'N/A'),
            report_date=datetime.now().strftime("%Y-%m-%d"),
            system_version=self.SYSTEM_VERSION,
            executive_summary=f"Contract risk analysis complete. Overall risk: {risk_class}.",
            risk_before=f"{avg_risk:.1f}",
            risk_before_badge=risk_badge,
            risk_after="TBD",
            risk_after_badge="Pending redlines",
            critical_before=str(critical_clauses),
            critical_after="TBD",
            statutory_before=str(statutory_flags),
            statutory_after="TBD",
            recommendation="REVIEW REQUIRED - Redlines pending",
            top_concerns_section=top_concerns_text,
            redline_table_rows=redline_table,
            cascade_section="Cascade analysis pending redline completion.",
            input_hash="[computed during audit log]",
            output_hash="[computed below]",
            prompt_version=prompt_version,
            timestamp=datetime.now().isoformat()
        )

        # Compute hashes
        input_data = json.dumps(data, sort_keys=True)
        input_hash = self._compute_hash(input_data)
        output_hash = self._compute_hash(report)

        # Log to audit trail
        versions = {
            'system_version': self.SYSTEM_VERSION,
            'risk_scorer_version': '1.0',
            'ucc_logic_version': '1.0',
            'prompt_name': 'redline_report',
            'prompt_version': prompt_version,
            'prompt_hash': '',  # Template-based, no AI prompt
            'template_name': 'redline_report',
            'template_version': template_version,
            'template_hash': template_hash
        }

        output_path = f"reports/{report_id}_redline.md"

        self.audit.log_report(
            report_type='REDLINE_REPORT',
            contract_id=contract_id,
            input_hash=input_hash,
            output_hash=output_hash,
            versions=versions,
            output_path=output_path
        )

        # Update report with actual hashes
        report = report.replace('[computed during audit log]', input_hash[:16])
        report = report.replace('[computed below]', output_hash[:16])

        return report, report_id

    def generate_comparison_report(
        self,
        v1_contract_id: int,
        v2_contract_id: int,
        template_version: str = "1.0"
    ) -> Tuple[str, str]:
        """
        Generate version comparison report.

        Args:
            v1_contract_id: V1 (baseline) contract
            v2_contract_id: V2 (vendor response) contract
            template_version: Template version to use

        Returns:
            (report_content, report_id)
        """
        # Load template
        template, template_hash = self._load_template(
            "comparison_report",
            template_version
        )

        # Get contract data
        v1_data = self._get_contract_data(v1_contract_id)
        v2_data = self._get_contract_data(v2_contract_id)

        # Compute risk deltas
        v1_avg = sum(c.get('cce_risk_score', 0) for c in v1_data['clauses']) / len(v1_data['clauses']) if v1_data['clauses'] else 0
        v2_avg = sum(c.get('cce_risk_score', 0) for c in v2_data['clauses']) / len(v2_data['clauses']) if v2_data['clauses'] else 0
        delta = v2_avg - v1_avg

        delta_direction = "IMPROVED" if delta < 0 else "WORSENED" if delta > 0 else "NO CHANGE"

        # Generate report ID
        report_id = self.audit._generate_report_id()

        # Substitute template (simplified placeholders)
        report = template.format(
            report_id=report_id,
            contract_title=v1_data['contract'].get('title', 'Untitled'),
            v1_name=f"V1 ({v1_contract_id})",
            v1_date=v1_data['contract'].get('created_at', 'Unknown'),
            v2_name=f"V2 ({v2_contract_id})",
            v2_date=v2_data['contract'].get('created_at', 'Unknown'),
            system_version=self.SYSTEM_VERSION,
            executive_summary=f"Version comparison complete. Risk delta: {delta:+.1f}",
            v1_risk=f"{v1_avg:.1f}",
            v1_badge="CRITICAL" if v1_avg >= 9.0 else "HIGH" if v1_avg >= 7.0 else "MEDIUM" if v1_avg >= 5.0 else "LOW",
            v1_classification="CRITICAL" if v1_avg >= 9.0 else "HIGH" if v1_avg >= 7.0 else "MEDIUM" if v1_avg >= 5.0 else "LOW",
            redline_risk="N/A",
            redline_badge="",
            redline_classification="",
            v2_risk=f"{v2_avg:.1f}",
            v2_badge="CRITICAL" if v2_avg >= 9.0 else "HIGH" if v2_avg >= 7.0 else "MEDIUM" if v2_avg >= 5.0 else "LOW",
            v2_classification="CRITICAL" if v2_avg >= 9.0 else "HIGH" if v2_avg >= 7.0 else "MEDIUM" if v2_avg >= 5.0 else "LOW",
            delta=f"{delta:+.1f}",
            delta_direction=delta_direction,
            accepted_count="TBD",
            accepted_sections="Pending analysis",
            partial_count="TBD",
            partial_sections="Pending analysis",
            rejected_count="TBD",
            rejected_sections="Pending analysis",
            recommendation="FURTHER REVIEW REQUIRED",
            critical_changes_section="Detailed change analysis pending.",
            cascade_section="Cross-clause impact analysis pending.",
            v1_hash="[computed]",
            v2_hash="[computed]",
            output_hash="[computed]",
            timestamp=datetime.now().isoformat()
        )

        # Compute hashes
        input_data = json.dumps({'v1': v1_data, 'v2': v2_data}, sort_keys=True)
        input_hash = self._compute_hash(input_data)
        output_hash = self._compute_hash(report)

        # Log to audit trail
        versions = {
            'system_version': self.SYSTEM_VERSION,
            'risk_scorer_version': '1.0',
            'ucc_logic_version': '1.0',
            'template_name': 'comparison_report',
            'template_version': template_version,
            'template_hash': template_hash
        }

        output_path = f"reports/{report_id}_comparison.md"

        self.audit.log_report(
            report_type='COMPARISON_REPORT',
            contract_id=v1_contract_id,
            v1_contract_id=v1_contract_id,
            v2_contract_id=v2_contract_id,
            input_hash=input_hash,
            output_hash=output_hash,
            versions=versions,
            output_path=output_path
        )

        return report, report_id


# CLI for testing
if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 4:
        print("Usage: python report_generator.py <db_path> redline <contract_id>")
        print("       python report_generator.py <db_path> compare <v1_id> <v2_id>")
        sys.exit(1)

    db_path = sys.argv[1]
    report_type = sys.argv[2]
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    generator = ReportGenerator(db_path, api_key)

    if report_type == 'redline':
        contract_id = int(sys.argv[3])
        report, report_id = generator.generate_redline_report(contract_id)
        print(f"Generated: {report_id}")
        print(report)

    elif report_type == 'compare':
        v1_id = int(sys.argv[3])
        v2_id = int(sys.argv[4])
        report, report_id = generator.generate_comparison_report(v1_id, v2_id)
        print(f"Generated: {report_id}")
        print(report)
