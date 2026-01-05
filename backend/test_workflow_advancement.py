"""Test workflow advancement for risk analysis completion."""

from workflow_gates import WorkflowGate

db_path = '../data/contracts.db'
contract_id = 49

print("Testing workflow advancement for contract 49...")
print()

gate = WorkflowGate(db_path)

# Get status before
status_before = gate.get_workflow_status(contract_id)
print(f"BEFORE:")
print(f"  Intake:  {status_before['intake']}")
print(f"  Risk:    {status_before['risk']}")
print(f"  Redline: {status_before['redline']}")
print(f"  Compare: {status_before['compare']}")
print()

# Advance risk stage
print("Advancing risk stage...")
success = gate.advance_stage(contract_id, 'risk')
print(f"Result: {'SUCCESS' if success else 'FAILED'}")
print()

# Get status after
status_after = gate.get_workflow_status(contract_id)
print(f"AFTER:")
print(f"  Intake:  {status_after['intake']}")
print(f"  Risk:    {status_after['risk']}")
print(f"  Redline: {status_after['redline']}")
print(f"  Compare: {status_after['compare']}")
print()

# Verify
if status_after['risk'] == 'COMPLETE' and status_after['redline'] == 'PENDING':
    print("[OK] Workflow advancement works correctly!")
    print("     Risk marked COMPLETE, Redline unlocked (PENDING)")
else:
    print("[ERROR] Unexpected status after advancement")
