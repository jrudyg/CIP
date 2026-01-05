"""
Workflow gate enforcement for CCE-Plus contract processing.

Ensures contracts progress through stages in order:
INTAKE → RISK_ANALYSIS → REDLINES → COMPARE

Status values:
- BLOCKED: Cannot start (prerequisite not met)
- PENDING: Can start but not started
- IN_PROGRESS: Currently executing
- COMPLETE: Finished successfully
- APPROVED: Final approval (redlines only)
- REJECTED: Final rejection (redlines only)
"""

import sqlite3
from typing import Tuple, Dict
from pathlib import Path

class WorkflowGate:
    """Enforce contract workflow progression."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def can_start_risk_analysis(self, contract_id: int) -> Tuple[bool, str]:
        """
        Check if contract can enter risk analysis stage.

        Gate: intake_status = 'COMPLETE'

        Returns:
            (True, "") if allowed
            (False, "reason") if blocked
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT intake_status FROM contracts WHERE id = ?",
            (contract_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False, "Contract not found"

        intake_status = result[0]

        if intake_status != 'COMPLETE':
            return False, f"Intake not complete (status: {intake_status})"

        return True, ""

    def can_start_redlines(self, contract_id: int) -> Tuple[bool, str]:
        """
        Check if contract can enter redline phase.

        Gate: risk_status = 'COMPLETE'

        Returns:
            (True, "") if allowed
            (False, "reason") if blocked
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT intake_status, risk_status FROM contracts WHERE id = ?",
            (contract_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False, "Contract not found"

        intake_status, risk_status = result

        if intake_status != 'COMPLETE':
            return False, "Intake not complete"

        if risk_status != 'COMPLETE':
            return False, f"Risk analysis not complete (status: {risk_status})"

        return True, ""

    def can_start_compare(self, contract_id: int) -> Tuple[bool, str]:
        """
        Check if contract can enter compare phase.

        Gate: redline_status = 'APPROVED'

        Returns:
            (True, "") if allowed
            (False, "reason") if blocked
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT intake_status, risk_status, redline_status
            FROM contracts WHERE id = ?
            """,
            (contract_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False, "Contract not found"

        intake_status, risk_status, redline_status = result

        if intake_status != 'COMPLETE':
            return False, "Intake not complete"

        if risk_status != 'COMPLETE':
            return False, "Risk analysis not complete"

        if redline_status not in ('APPROVED', 'COMPLETE'):
            return False, f"Redlines not approved (status: {redline_status})"

        return True, ""

    def advance_stage(self, contract_id: int, stage: str) -> bool:
        """
        Mark stage complete and unlock next stage.

        Args:
            contract_id: Contract ID
            stage: 'intake', 'risk', 'redline', 'compare'

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if stage == 'intake':
                # Mark intake complete, unlock risk analysis
                cursor.execute(
                    """
                    UPDATE contracts
                    SET intake_status = 'COMPLETE',
                        risk_status = 'PENDING'
                    WHERE id = ?
                    """,
                    (contract_id,)
                )

            elif stage == 'risk':
                # Mark risk complete, unlock redlines
                cursor.execute(
                    """
                    UPDATE contracts
                    SET risk_status = 'COMPLETE',
                        redline_status = 'PENDING'
                    WHERE id = ?
                    """,
                    (contract_id,)
                )

            elif stage == 'redline':
                # Mark redline approved, unlock compare
                cursor.execute(
                    """
                    UPDATE contracts
                    SET redline_status = 'APPROVED',
                        compare_status = 'PENDING'
                    WHERE id = ?
                    """,
                    (contract_id,)
                )

            elif stage == 'compare':
                # Mark compare complete
                cursor.execute(
                    """
                    UPDATE contracts
                    SET compare_status = 'COMPLETE'
                    WHERE id = ?
                    """,
                    (contract_id,)
                )

            else:
                conn.close()
                return False

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            conn.close()
            print(f"Error advancing stage: {e}")
            return False

    def get_workflow_status(self, contract_id: int) -> Dict:
        """
        Get current workflow state for UI display.

        Returns:
            {
                'intake': 'COMPLETE',
                'risk': 'PENDING',
                'redline': 'BLOCKED',
                'compare': 'BLOCKED',
                'current_stage': 'risk',
                'can_proceed': True
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT intake_status, risk_status, redline_status, compare_status
            FROM contracts WHERE id = ?
            """,
            (contract_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return {'error': 'Contract not found'}

        intake, risk, redline, compare = result

        # Determine current stage
        if compare in ('IN_PROGRESS', 'COMPLETE'):
            current_stage = 'compare'
        elif redline in ('IN_PROGRESS', 'APPROVED', 'REJECTED'):
            current_stage = 'redline'
        elif risk in ('IN_PROGRESS', 'COMPLETE'):
            current_stage = 'risk'
        else:
            current_stage = 'intake'

        # Determine if can proceed to next stage
        can_proceed = False
        if current_stage == 'intake' and intake == 'COMPLETE':
            can_proceed = True
        elif current_stage == 'risk' and risk == 'COMPLETE':
            can_proceed = True
        elif current_stage == 'redline' and redline == 'APPROVED':
            can_proceed = True

        return {
            'intake': intake,
            'risk': risk,
            'redline': redline,
            'compare': compare,
            'current_stage': current_stage,
            'can_proceed': can_proceed
        }


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python workflow_gates.py <db_path> <contract_id>")
        sys.exit(1)

    db_path = sys.argv[1]
    contract_id = int(sys.argv[2])

    gate = WorkflowGate(db_path)
    status = gate.get_workflow_status(contract_id)

    print("Workflow Status:")
    print(f"  Intake: {status['intake']}")
    print(f"  Risk: {status['risk']}")
    print(f"  Redline: {status['redline']}")
    print(f"  Compare: {status['compare']}")
    print(f"  Current Stage: {status['current_stage']}")
    print(f"  Can Proceed: {status['can_proceed']}")
