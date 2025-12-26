# CONTRACT REVIEW SYSTEM - TEST SCENARIOS

## Test Scenario 1: Basic Function Test
Upload the Mujin contract and provide:
- Position: Reseller (Company)
- Leverage: Balanced
- Context: "Black box vendor who wants direct customer relationships. Concerned about vendor displacement."

**Expected System Behavior:**
- Should catch Section 1(A) direct fulfillment issue
- Should flag Section 3(H) non-compete trap
- Should identify Section 11(C) unilateral termination
- Should provide customer protection period language

---

## Test Scenario 2: Format Verification Test
For any clause revision, verify:
- Red font is applied
- Deletions use strikethrough
- Additions use underline
- No brackets, tildes, or special characters
- Grammar is perfect

**Expected Output Example:**
<span style="color:red">~~original text~~ <u>replacement text</u></span>

---

## Test Scenario 3: Confidence Threshold Test

### DEALBREAKER Test
When system encounters: "Vendor may engage directly with Company's customers"
**Expected:** Immediate stop and user consultation

### CRITICAL Test (95%+)
For liability cap revision
**Expected:** 3-5x verification before presenting

### STANDARD Test (85%)
For notice provision change
**Expected:** 1-2x verification sufficient

---

## Test Scenario 4: Dependency Detection Test
Change payment terms from "advance" to "Net 30"
**Expected System Response:**
- "This impacts Section X.X (late fees)"
- "This impacts Section Y.Y (termination for non-payment)"
- "This impacts Section Z.Z (suspension rights)"

---

## Test Scenario 5: Context Window Management Test
After reviewing 15-20 clauses, check if system:
- Monitors context usage
- Alerts at 80% capacity
- Creates proper checkpoint
- Can resume from checkpoint

**Checkpoint should contain only:**
- Position, leverage, brief context
- Current clause number
- Simple decision list

---

## Test Scenario 6: QA/QC Loop Test

### User Keeps Original
Say: "Keep original - we can accept this risk given other protections"
**Expected:** System learns and adjusts remaining approach

### User Modifies
Say: "Change 30 days to 45 days"
**Expected:** System implements and recalibrates

### User Accepts
Say: "Accept your suggestion"
**Expected:** System proceeds to next clause

---

## Test Scenario 7: Cascade Recalibration Test
After user rejects a liability cap change:
**Expected:** System should recognize this affects:
- Indemnification strategy
- Insurance requirements
- Warranty approach

---

## Test Scenario 8: Error Recovery Test

### Missing Section
Reference "Section 12" when contract only has 11 sections
**Expected:** System asks for guidance rather than guessing

### Ambiguous Reference  
Contract has 3.1(a) and 3.1(A)
**Expected:** System asks which one rather than assuming

### Low Confidence
System at 87% confidence on CRITICAL item
**Expected:** Flags for user verification

---

## Test Scenario 9: Position/Leverage Application Test

### Weak Leverage Test
Position: Vendor, Leverage: Weak
**Expected:** System suggests protective fallbacks, accepts more standard terms

### Strong Leverage Test  
Position: Customer, Leverage: Strong
**Expected:** System suggests aggressive positions, multiple alternatives

---

## Test Scenario 10: Schedule Impact Detection Test
For clause with "subject to approval"
**Expected:** System adds "within 5 business days, deemed approved if no response"

For "commercially reasonable efforts"
**Expected:** System flags as schedule risk

---

## SYSTEM HEALTH INDICATORS

✅ **Healthy System:**
- Catches all DEALBREAKERS
- Formats perfectly every time
- Asks for help when uncertain
- Maintains decision consistency
- Identifies dependencies

⚠️ **System Issues:**
- Missing section references
- Paraphrasing instead of quoting
- Format errors in output
- Proceeding despite uncertainty
- Not flagging cascades

🔴 **System Failure:**
- Wrong section numbers
- Inventing contract language
- Missing vendor displacement
- Breaking format requirements
- Ignoring user corrections

---

## QUICK VALIDATION CHECKLIST

After uploading contract, system should:
- [ ] Immediately ask for position
- [ ] Ask for leverage  
- [ ] Ask for context narrative
- [ ] Begin with Clause 1 or Section 1
- [ ] Present one clause at a time
- [ ] Wait for user response
- [ ] Apply correct formatting
- [ ] Flag dependencies
- [ ] Show success probability
- [ ] Adjust based on feedback

---

## NOTES FOR TESTING

1. Start with simple contract (5-10 pages) for initial test
2. Mujin agreement is good complex test (vendor displacement)
3. Test format on first 3 clauses before full review
4. Intentionally challenge system with corrections
5. Verify learning between clauses

If system fails any test scenario, note:
- What was expected
- What actually happened  
- Which system file might need adjustment