# Impact Classification Rules

## Priority Hierarchy

### CRITICAL (Highest Priority)

**1. Limitation of Liability**
- Liability caps (changes to amounts or removal)
- Carve-outs to liability limits
- Unlimited liability provisions
- Insurance requirements tied to liability

**Classification triggers:**
- Any change to "shall not exceed" language
- Addition/removal of liability carve-outs
- Changes to indemnification limits
- Modifications to consequential damages exclusions

---

**2. Indemnification**
- Indemnification scope (who indemnifies whom)
- Knowledge qualifiers ("to Company's knowledge")
- Defense obligations and cost allocation
- Third-party claim procedures

**Classification triggers:**
- Changes from mutual to one-way indemnification
- Addition/removal of knowledge qualifiers
- Modifications to indemnity scope
- Defense cost allocation changes

---

**3. IP Ownership**
- Work-for-hire provisions
- IP ownership transfers
- License grants and restrictions
- Background vs. foreground IP

**Classification triggers:**
- Changes to IP ownership (customer vs. vendor)
- License scope modifications
- IP warranty changes
- Background IP exclusions

---

**4. Compliance & Regulatory**
- Regulatory compliance requirements
- Audit rights and obligations
- Data protection and privacy
- Export control restrictions

**Classification triggers:**
- New compliance obligations
- Audit right additions/expansions
- Data protection requirement changes
- Industry-specific regulation additions

---

**5. Insurance**
- Insurance types required
- Coverage limits
- Additional insured requirements
- Proof of insurance timing

**Classification triggers:**
- Changes to required coverage limits
- Addition of insurance types
- Additional insured modifications
- Certificate of insurance timing

---

### HIGH PRIORITY

**6. Operational**
- Termination rights and cure periods
- Warranties and representations
- Acceptance criteria
- Service level agreements

**Classification triggers:**
- Changes to termination notice periods
- Cure period modifications
- Warranty scope changes
- SLA metric adjustments

---

**7. Financial**
- Fee structures and pricing
- Markup limitations
- Cost reimbursement terms
- Financial reporting requirements

**Classification triggers:**
- Pricing structure changes
- Markup cap additions/removals
- Reimbursable cost modifications
- Financial audit right changes

---

### IMPORTANT (Context-Dependent)

**8. Payment Terms**

**Requires context analysis:**

**Scenario A - Tied to SOW:**
If payment terms reference Statement of Work milestones:
- Classification: **IMPORTANT** or **HIGH PRIORITY**
- Rationale: Direct impact on cash flow timing

**Scenario B - Flowdown from Owner Contract:**
If payment terms must match upstream owner contract:
- Classification: **CRITICAL** or **HIGH PRIORITY**
- Rationale: Misalignment creates financing gap

**Scenario C - Standard Net 30/60:**
If payment terms are standard commercial terms:
- Classification: **IMPORTANT** or **OPERATIONAL**
- Rationale: Routine business terms

**Classification triggers:**
- Payment timing changes (Net 30 → Net 45)
- Milestone payment structure modifications
- Advance payment percentage changes
- Disputed payment procedures

**Analysis checklist:**
- [ ] Is payment tied to SOW deliverables?
- [ ] Must payment match owner contract terms?
- [ ] Does change create financing burden?
- [ ] Is payment method modified (ACH, wire, check)?

---

### OPERATIONAL

**9. Administrative Procedures**
- Notice requirements and addresses
- Approval processes and response times
- Reporting and documentation
- Meeting and communication protocols

**Classification triggers:**
- Response time changes
- Approval authority modifications
- Reporting frequency changes
- Notice method updates

---

### ADMINISTRATIVE

**10. Non-Substantive Changes**
- Contact information updates
- Definition clarifications (no meaning change)
- Exhibit reference corrections
- Grammar and spelling fixes

**Classification triggers:**
- Company address changes
- Phone/email updates
- Exhibit renumbering
- Typographical corrections

---

## Hybrid Classification Logic

**Use rules for obvious cases:**
- Liability cap change → CRITICAL (automatic)
- Indemnification scope → CRITICAL (automatic)
- IP ownership transfer → CRITICAL (automatic)

**Use AI judgment for ambiguous cases:**
- Is this warranty change CRITICAL or HIGH PRIORITY?
- Is this payment term IMPORTANT or OPERATIONAL?
- Does this operational change have CRITICAL implications?

**When uncertain:**
- Classify one level higher for safety
- Flag for user review in recommendations
- Explain reasoning in business impact narrative

---

## Examples

**Example 1: Clear CRITICAL**
```
Change: "Liability shall not exceed $1,000,000" → "Liability is unlimited"
Classification: CRITICAL
Rationale: Removes all liability protection, creates unquantifiable exposure
```

**Example 2: Context-Dependent IMPORTANT**
```
Change: "Payment Net 30 days" → "Payment Net 45 days"
Context: Downstream supplier requires Net 30 from you
Classification: HIGH PRIORITY (creates 15-day financing gap)
Rationale: You must pay supplier before customer pays you
```

**Example 3: Ambiguous → AI Judgment**
```
Change: "30-day cure period" → "7-day cure period"
AI Analysis:
- 7 days insufficient for operational remedy
- Creates termination risk
- User has weak leverage
Classification: HIGH PRIORITY (not CRITICAL, but significant)
Rationale: Operational risk elevated, but not dealbreaker
```

**Example 4: ADMINISTRATIVE**
```
Change: "Company address: 123 Old St" → "Company address: 456 New St"
Classification: ADMINISTRATIVE
Rationale: Contact information update, no business impact
```

---

**END OF IMPACT CLASSIFICATION REFERENCE**
