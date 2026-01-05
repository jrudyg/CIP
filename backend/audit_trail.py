"""
Audit trail for report reproducibility.

Tracks full provenance of every report:
- Input hashes
- System versions
- Prompt/template versions
- Output hashes

Enables verification: regenerate report and compare hash.
"""

import sqlite3
import hashlib
import json
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path


class AuditTrail:
    """Manage report audit trail."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _generate_report_id(self) -> str:
        """Generate unique report ID: RPT-YYYY-MM-DD-NNN"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")
        prefix = f"RPT-{today}"

        cursor.execute(
            "SELECT COUNT(*) FROM audit_trail WHERE report_id LIKE ?",
            (f"{prefix}-%",)
        )
        count = cursor.fetchone()[0]
        conn.close()

        seq = str(count + 1).zfill(3)
        return f"{prefix}-{seq}"

    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def log_report(
        self,
        report_type: str,
        contract_id: int,
        input_hash: str,
        output_hash: str,
        versions: Dict,
        output_path: str,
        v1_contract_id: int = None,
        v2_contract_id: int = None,
        created_by: str = "CCE-Plus"
    ) -> str:
        """
        Log report generation to audit trail.

        Args:
            report_type: 'REDLINE_REPORT' or 'COMPARISON_REPORT'
            contract_id: Primary contract ID
            input_hash: SHA-256 of input data
            output_hash: SHA-256 of generated report
            versions: Dict with system/prompt/template versions and hashes
            output_path: Where report was saved
            v1_contract_id: For comparisons - V1 contract
            v2_contract_id: For comparisons - V2 contract
            created_by: User/system identifier

        Returns:
            report_id (e.g., RPT-2026-01-03-001)
        """
        report_id = self._generate_report_id()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_trail (
                report_id, report_type, contract_id,
                v1_contract_id, v2_contract_id, input_hash,
                system_version, risk_scorer_version, ucc_logic_version,
                prompt_name, prompt_version, prompt_hash,
                template_name, template_version, template_hash,
                output_hash, output_path, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                report_type,
                contract_id,
                v1_contract_id,
                v2_contract_id,
                input_hash,
                versions.get('system_version', '1.0'),
                versions.get('risk_scorer_version', '1.0'),
                versions.get('ucc_logic_version', '1.0'),
                versions.get('prompt_name', 'unknown'),
                versions.get('prompt_version', '1.0'),
                versions.get('prompt_hash', ''),
                versions.get('template_name', 'unknown'),
                versions.get('template_version', '1.0'),
                versions.get('template_hash', ''),
                output_hash,
                output_path,
                created_by
            )
        )

        conn.commit()
        conn.close()

        return report_id

    def get_audit_record(self, report_id: str) -> Dict:
        """
        Retrieve complete audit record for a report.

        Returns:
            Dict with full audit record or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM audit_trail WHERE report_id = ?",
            (report_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)

    def verify_report(
        self,
        report_id: str,
        regenerate_fn=None
    ) -> Tuple[bool, str]:
        """
        Verify report reproducibility by comparing hashes.

        Args:
            report_id: Report ID to verify
            regenerate_fn: Optional function to regenerate report
                          Should return (report_content, versions)

        Returns:
            (match: bool, message: str)
        """
        record = self.get_audit_record(report_id)

        if not record:
            return False, "Report not found in audit trail"

        if not regenerate_fn:
            return False, "Regeneration function not provided"

        # Regenerate report
        try:
            new_content, new_versions = regenerate_fn(record)
            new_hash = self._compute_hash(new_content)
        except Exception as e:
            return False, f"Regeneration failed: {e}"

        # Compare output hash
        if new_hash != record['output_hash']:
            return False, f"Hash mismatch: {new_hash[:8]}... != {record['output_hash'][:8]}..."

        # Update verification record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE audit_trail
            SET last_verified_at = CURRENT_TIMESTAMP,
                last_verified_by = 'system',
                verification_status = 'VERIFIED',
                verification_notes = 'Hash match confirmed'
            WHERE report_id = ?
            """,
            (report_id,)
        )

        conn.commit()
        conn.close()

        return True, "Report verified successfully"

    def get_report_history(self, contract_id: int) -> List[Dict]:
        """
        Get all reports generated for a contract.

        Returns:
            List of audit records, sorted by created_at DESC
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM audit_trail
            WHERE contract_id = ?
            ORDER BY created_at DESC
            """,
            (contract_id,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python audit_trail.py <db_path> <report_id>")
        print("       python audit_trail.py <db_path> --contract <contract_id>")
        sys.exit(1)

    db_path = sys.argv[1]
    trail = AuditTrail(db_path)

    if sys.argv[2] == '--contract':
        contract_id = int(sys.argv[3])
        history = trail.get_report_history(contract_id)
        print(f"Report History for Contract {contract_id}:")
        for record in history:
            print(f"  {record['report_id']} - {record['report_type']} - {record['created_at']}")
    else:
        report_id = sys.argv[2]
        record = trail.get_audit_record(report_id)
        if record:
            print(json.dumps(record, indent=2))
        else:
            print("Report not found")
