"""
Report reproducibility verification utility.

Usage:
    python verify_report.py --report-id RPT-2026-01-03-001
"""

import argparse
from audit_trail import AuditTrail
from report_generator import ReportGenerator
import os


def main():
    parser = argparse.ArgumentParser(description='Verify report reproducibility')
    parser.add_argument('--report-id', required=True, help='Report ID to verify')
    parser.add_argument('--db', default='../data/contracts.db', help='Database path')

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return 1

    # Initialize
    audit = AuditTrail(args.db)
    generator = ReportGenerator(args.db, api_key)

    # Get audit record
    record = audit.get_audit_record(args.report_id)
    if not record:
        print(f"Report not found: {args.report_id}")
        return 1

    print(f"Verifying report: {args.report_id}")
    print(f"Type: {record['report_type']}")
    print(f"Created: {record['created_at']}")
    print(f"Original hash: {record['output_hash'][:16]}...")

    # Define regeneration function
    def regenerate(audit_record):
        if audit_record['report_type'] == 'REDLINE_REPORT':
            content, _ = generator.generate_redline_report(
                audit_record['contract_id'],
                template_version=audit_record['template_version']
            )
        elif audit_record['report_type'] == 'COMPARISON_REPORT':
            content, _ = generator.generate_comparison_report(
                audit_record['v1_contract_id'],
                audit_record['v2_contract_id'],
                template_version=audit_record['template_version']
            )
        else:
            raise ValueError(f"Unknown report type: {audit_record['report_type']}")

        return content, {}

    # Verify
    match, message = audit.verify_report(args.report_id, regenerate_fn=regenerate)

    if match:
        print("[OK] VERIFIED - Report is reproducible")
        return 0
    else:
        print(f"[FAILED] {message}")
        return 1


if __name__ == "__main__":
    exit(main())
