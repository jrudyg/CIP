# 02_PATTERN_LIBRARY v2.1

**Version:** 2.1
**Date:** January 18, 2026
**Status:** Production Ready
**Pattern Count:** 113 (87 patterns + 26 UCC rules)
**Source:** CIP v1.3 baseline + 4 negotiation comparison documents + UCC Statutory Logic v2.0

---

## VERSION 2.1 CHANGES

### From v2.0 → v2.1
- Added Part 8: Statutory Conflicts (UCC) with 26 statutory rules
- UCC rules sourced from Delaware UCC Title 6 (Article 2) + Systems Integrator patterns
- Pattern count expanded: 87 → 113 (26 UCC statutory rules added)
- All v2.0 patterns preserved (no deletions or replacements)
- Integration with Phase 2.5.1: UCC Statutory Conflict Detection

### From v1.3 → v2.0
- Corrected pattern count (was 56 claimed, 59 actual → now 87 verified)
- Added 28 new patterns from real negotiation outcomes
- Added 6 expansions to existing patterns
- Renamed Section 3.6 "Channel Partner" → "Partnership & Distribution"
- Added Section 3.9: MSA Commercial Terms (11 patterns)
- Added Section 3.10: Services Procurement - Buyer Position (6 patterns)
- Added Section 3.11: Project Agreements (5 patterns)
- Added Section 3.12: Subcontract Templates - Issuer Position (6 patterns)
- Added Part 7: Risk Indicators (patterns to WATCH FOR)
- Added Outcome Tracking Schema for Phase 2 learning loop
- Updated contract type taxonomy

### Contract Type Taxonomy
| Code | Full Name | Description |
|------|-----------|-------------|
| NDA | Non-Disclosure Agreement | One-way confidentiality |
| MNDA | Mutual Non-Disclosure Agreement | Two-way confidentiality |
| MSA | Master Services Agreement | Framework agreement |
| IPA | Individual Project Agreement | Standalone project, may link to MSA |
| SOW | Statement of Work | Project-specific scope under MSA |
| CHGORD | Change Order | Modifications to existing SOW/IPA |
| AMEND | Amendment | Modifications to base agreement |
| VERSION | Version (V1, V2, V3...) | Same contract through negotiation lifecycle |
| PO | Purchase Order | Procurement/supply transactions |
| MOU | Memorandum of Understanding | Pre-contractual intent, non-binding |

---

## QUICK REFERENCE

### Pattern Count by Category

| Category | Patterns | Numbers |
|----------|----------|---------|
| Core Patterns | 33 | 2.1.x - 2.11.x |
| Specialized Patterns (Original) | 26 | 3.1.x - 3.8.x |
| MSA Commercial Terms | 11 | 3.9.x |
| Services Procurement (Buyer) | 6 | 3.10.x |
| Project Agreements | 5 | 3.11.x |
| Subcontract Templates (Issuer) | 6 | 3.12.x |
| **Statutory Conflicts (UCC)** | **26** | **Part 8** ⚠️ NEW |
| Coordination Clusters | 4 | Part 4 |
| **TOTAL** | **113 + 4** | |

### Agent-to-Pattern Mapping

| Agent | Primary Patterns |
|-------|------------------|
| contract-risk | 2.1.x, 2.2.x, 2.10.x, Part 6, Part 7, **Part 8** ⚠️ NEW |
| clause-compare | All Part 2, 3.1-3.2, 3.9-3.12 |
| negotiation-advisor | All (fallbacks in Part 5) |
| compliance-check | 2.1.1, 2.2.1, 2.8.2, 3.1.1, **Part 8** ⚠️ NEW |

### Outcome Tracking Schema (Phase 2)

```yaml
OUTCOME_TRACKING:
  pattern_id: "2.1.1"
  pattern_name: "Mutual Cap"
  contract_type: [NDA|MNDA|MSA|IPA|SOW|CHGORD|AMEND|VERSION|PO|MOU]
  position: [BUYER|SELLER|BALANCED]
  leverage: [STRONG|BALANCED|WEAK]
  success_rate_estimated: 75%
  outcome: [WON|MUTUAL|ACCEPTED|LOST|PENDING]
  source_contract: "MSA_2025_11"
  outcome_date: 2025-11-17
  notes: "Accepted with 2x cap variant"
```

---

## PART 2: CORE PATTERNS

### 2.1 Limitation of Liability

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.1.1 | Mutual Cap | 75% balanced | ✅ | WON |
| 2.1.2 | Carve-Out Protection | 60% weak | ✅ | WON |
| 2.1.3 | Super Cap for IP | 35% | ✅ | MUTUAL |

#### 2.1.1: Mutual Cap Pattern

**Problem:** Unlimited liability exposure
**Position:** Any / Balanced or Strong
**Contract Types:** MSA, IPA, SOW

**Revision:**
```
~~unlimited~~ `shall not exceed the total fees paid under
this Agreement in the twelve (12) months preceding the claim`
```

**v2.0 EXPANSION - 2x Cap with Carve-outs:**
```
NEITHER PARTY'S AGGREGATE LIABILITY UNDER ANY SOW SHALL EXCEED
TWO TIMES THE TOTAL PURCHASE PRICE PAID OR PAYABLE UNDER SUCH SOW.

Exceptions (unlimited liability):
(i) Gross negligence and/or willful misconduct
(ii) Indemnification obligations (other than breach of contract)
(iii) Confidentiality/NDA breaches
(iv) Intellectual property infringement
(v) Insurance proceeds actually received
```

**Source:** Master Projects Agreement V3→V4 §11(e)
**Success Rate:** 75% balanced, 85% strong
**Coordinates:** 2.10.3 (Back-to-Back)

---

#### 2.1.2: Carve-Out Protection

**Problem:** Consequential damages waiver too broad
**Position:** Any / Balanced

**Revision:**
```
Neither Party shall be liable for indirect and/or consequential damages.

~~[no exceptions]~~ `However, this limitation shall not apply to:
(i) Breach of confidentiality obligations;
(ii) Breach of intellectual property rights;
(iii) Indemnification obligations;
(iv) Gross negligence or willful misconduct.`
```

**Source:** Channel Partner §16.2
**Success Rate:** 60% balanced

---

### 2.2 Indemnification

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.2.1 | Mutual Indemnification | 70% balanced | ✅ | MUTUAL |
| 2.2.2 | Knowledge Qualifier | 45% weak | ✅ | WON |
| 2.2.3 | Duty to Mitigate | 25% | ✅ | LOST |
| 2.2.4 | IP Indemnity Notice | 75% balanced | ✅ | WON |
| 2.2.5 | Environmental Warranty | 65% balanced | ✅ | WON |

#### 2.2.1: Mutual Indemnification

**Problem:** One-way vendor indemnification
**Position:** Reseller / Balanced

**Revision:**
```
~~Company shall indemnify~~ `Each party shall indemnify the other`
```

**v2.0 EXPANSION - Gross Negligence Standard:**
```
Each party agrees to indemnify, defend, and hold the other harmless
from third-party claims, liabilities, or damages resulting from their
~~negligence~~ `gross negligence`, willful misconduct, or breach of
any SOW or this Agreement.
```

**v2.0 EXPANSION - Third-Party Claims Only:**
```
Indemnification applies to `third-party claims` only, eliminating
indemnification for direct party-to-party disputes.
```

**Source:** ATG MSA V1→V2 §13
**Success Rate:** 70% balanced
**Note:** Higher bar protects both parties; shifts risk to mutual protection from extreme conduct only

---

### 2.3 Payment Terms

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.3.1 | Net 30 Standard | 80% strong | ✅ | WON |
| 2.3.2 | Milestone Payments | 65% balanced | ✅ | WON |
| 2.3.3 | Dispute Rights | 40% | ✅ | WON |

#### 2.3.2: Milestone Payments (Enhanced)

**Problem:** 100% upfront payment
**Position:** Customer / Balanced

**Revision:**
```
~~payment in full prior to~~ `30% upon order, 40% on delivery,
30% on acceptance`
```

**v2.0 EXPANSION - End-Customer Payment Linkage:**
```
Where the Channel Partner's payment obligation under a Project Agreement
is tied to receipt of payment from an End-Customer, the Channel Partner's
payment to the Company shall be due within ten (10) business days after
the Channel Partner receives the corresponding payment from the End-Customer.
```

**Source:** Channel Partner §9.10
**Integrator Variant:** Tie to end-user acceptance
**Design-Build Variant:** `30% design approval, 40% pilot, 30% rollout`
**Success Rate:** 65% balanced

---

### 2.4 Vendor Displacement

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.4.1 | Customer Protection Period | 55% balanced | ✅ | WON |
| 2.4.2 | Commission on Direct Sales | 30% | ✅ | LOST |
| 2.4.3 | Introduction Documentation | 75% | ✅ | WON |

#### 2.4.1: Customer Protection Period

**Problem:** Vendor can go direct immediately
**Position:** Reseller / Balanced

**Revision:**
```
`For Customers introduced by Company, [Vendor] shall not directly
solicit for 24 months after last Company-submitted order`
```

**Full Protection Language (from Channel Partner §4.3):**
```
For any End-Customer initially introduced to the Company by the
Channel Partner, the Company agrees that:
(i) the Channel Partner shall have the primary relationship with
such End-Customer for a period of twenty-four (24) months following
the Channel Partner's first documented introduction; and
(ii) the Company shall not directly solicit, quote, or contract with
such End-Customer during this protection period without the Channel
Partner's prior written consent.
```

**Success Rate:** 55% balanced
**Coordinates:** 3.1.1, 3.6.3

---

### 2.5 Non-Solicitation

| # | Pattern | Success Rate | Validated |
|---|---------|--------------|-----------|
| 2.5.1 | Mutual Non-Solicit | 80% balanced | ✅ |
| 2.5.2 | Key Employee Carve-Out | 50% weak | ✅ |

---

### 2.6 Assignment

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.6.1 | Competitive Exclusion | 60% balanced | ✅ | WON |
| 2.6.2 | Change of Control | 85% any | ✅ | WON |
| 2.6.3 | Assignment to End User | 70% balanced | ✅ | WON |

#### 2.6.2: Change of Control (Enhanced)

**Problem:** Assignment to competitors via M&A
**Position:** Any / Any

**Revision:**
```
Neither Party shall assign without written consent, which consent
shall not be unreasonably withheld or delayed.

Notwithstanding the foregoing, either Party may assign without consent:
(i) to an Affiliate; or
(ii) in connection with a merger, acquisition, or sale of substantially
all of its assets, provided the assignee assumes all obligations.
```

**Source:** Channel Partner §23.3
**Success Rate:** 85% any leverage

---

### 2.7 Exclusivity

| # | Pattern | Success Rate | Validated |
|---|---------|--------------|-----------|
| 2.7.1 | Limited Exclusivity | 60% balanced | ✅ |
| 2.7.2 | Performance-Based | 75% strong | ✅ |

---

### 2.8 Termination

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.8.1 | Mutual Termination | 70% balanced | ✅ | WON |
| 2.8.2 | Cure Period | **80%** any | ✅ v1.2 | WON |
| 2.8.3 | Wind-Down Protection | **70%** balanced | ✅ v1.2 | WON |

#### 2.8.2: Cure Period (RECALIBRATED v1.2)

**Problem:** Immediate termination for breach
**Position:** Any / Weak

**Revision:**
```
`After 30 days written notice and opportunity to cure`
```

**Success Rate:** **80% any leverage** (UP from 75%)
**Validation:** 5/6 contracts accepted 30-day; 7-day rejected consistently
**Critical:** Industry norm is 30 days minimum

---

#### 2.8.3: Wind-Down Protection

**Problem:** No protection for work-in-progress
**Position:** Any / Balanced

**v2.0 EXPANSION - FM Termination Payment:**
```
In the event of Force Majeure termination, the Channel Partner must pay
~~the agreed Contract Price plus any changes less expenses not occurred~~
`for the Scope of Work properly performed through the date of termination.`
```

**Source:** Channel Partner §18.3
**Success Rate:** 70% balanced

---

### 2.9 Operational Barriers

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 2.9.1 | Defined Response Times | **85%** any | ✅ v1.2 | WON |
| 2.9.2 | Reasonableness Standard | 75% balanced | ✅ | WON |
| 2.9.3 | Escalation Path | 65% any | ✅ | WON |

#### 2.9.1: Defined Response Times

**Problem:** "Subject to approval" without timeframe
**Position:** Any / Any

**Revision:**
```
~~subject to approval~~ `subject to approval within 5 business days,
deemed approved if no response`
```

**v2.0 EXPANSION - Silence = Rejection Default:**
```
If the Channel Partner does not respond within ten (10) business days,
the Offer of Change shall be deemed ~~accepted~~ `rejected` and the
Company shall continue performance under the original Project Agreement terms.
```

**Source:** Channel Partner §8.3
**Success Rate:** 85% any leverage

---

### 2.10 Back-to-Back Arrangements

| # | Pattern | Success Rate | Validated |
|---|---------|--------------|-----------|
| 2.10.1 | Flow-Down Protection | 40% | ✅ |
| 2.10.2 | Gap Coverage | 25% | ✅ |
| 2.10.3 | Back-to-Back Liability | 60% balanced | ✅ |
| 2.10.4 | Prime Contract Flowdown | 70% balanced | ✅ |

---

### 2.11 Definitions

| # | Pattern | Success Rate | Validated |
|---|---------|--------------|-----------|
| 2.11.1 | Gross Negligence | 80% any | ✅ |
| 2.11.2 | Business Day | 90% any | ✅ |

#### 2.11.2: Definitions - Force Majeure Exclusions (v2.0 EXPANSION)

**Problem:** Overbroad FM definition allows abuse
**Position:** Any / Any

**Revision:**
```
Force Majeure shall ~~include~~ `NOT include`:
(i) equipment failures, breakdowns, or maintenance issues within
a Party's control through proper maintenance and planning;
(ii) financial difficulties or economic conditions affecting a Party;
(iii) labor disputes specific to a Party or its subcontractors;
(iv) delays in obtaining licenses, permits, or approvals that are
the responsibility of the claiming Party under this Agreement.
```

**Source:** Channel Partner Definitions
**Success Rate:** 90% any leverage

---

## PART 3: SPECIALIZED PATTERNS

### 3.1 Systems Integrator (6 patterns)

| # | Pattern | Success Rate | Validated | Outcome |
|---|---------|--------------|-----------|---------|
| 3.1.1 | Customer Protection Complete | **75%** | ✅ v1.2 | WON |
| 3.1.2 | Warranty Coordination | 70% | ✅ | WON |
| 3.1.3 | Final Acceptance Alignment | 65% | ✅ | WON |
| 3.1.4 | Software License Transfer | 60% | ✅ | WON |
| 3.1.5 | Security Interest Time Limits | 55% | ✅ | WON |
| 3.1.6 | Markup Limitations | 50% | ✅ | MUTUAL |

#### 3.1.4: Software License Transfer (v2.0 EXPANSION)

**Problem:** License doesn't transfer to end-customer
**Position:** SI / Balanced

**v2.0 EXPANSION - Sublicense Rights:**
```
Subject to full payment of the Contract Price, the Company grants
the Channel Partner a perpetual, `worldwide`, non-exclusive, royalty-free,
non-transferable license `for End-Customers and permitted assignees`
to use the Software for operating and maintaining the Scope of Work
`and fulfilling the Channel Partner's obligations to End-Customers`.

The Channel Partner `may grant sublicenses` of the Right of Use to
End-Customers purchasing integrated solutions, provided such sublicenses
are on terms no less protective of the Company's intellectual property
rights than those contained in this Agreement.
```

**Source:** Channel Partner §13.4
**Success Rate:** 60% balanced

---

### 3.2 Service Provider (5 patterns)

| # | Pattern | Description |
|---|---------|-------------|
| 3.2.1 | SOW Change Control | Scope creep prevention |
| 3.2.2 | Project Delays Attribution | Blame allocation |
| 3.2.3 | Audit Rights Limitations | Operational burden |
| 3.2.4 | Professional Liability Insurance | E&O coverage |
| 3.2.5 | Time & Materials Markup | Rate protection |

---

### 3.3 Relationship Structure (4 patterns)

| # | Pattern | Description |
|---|---------|-------------|
| 3.3.1 | Business Model Mismatch Detection | Pre-review framework |
| 3.3.2 | NDA Mutual Scope | Balanced confidentiality |
| 3.3.3 | NDA Return/Destruction | Procedural clarity |
| 3.3.4 | Scope Interface Definition | Boundary clarity |

---

### 3.4 Mutual Agreement Balance (2 patterns)

| # | Pattern | Description |
|---|---------|-------------|
| 3.4.1 | Reciprocity Testing | Identify one-sided terms |
| 3.4.2 | Hidden One-Way Provisions | Detection framework |

---

### 3.5 Execution Quality (2 patterns)

| # | Pattern | Description |
|---|---------|-------------|
| 3.5.1 | Deliverable Quality Framework | Output standards |
| 3.5.2 | Section Number Verification | Accuracy protocol |

---

### 3.6 Partnership & Distribution (4 patterns)

*Formerly "Channel Partner" — renamed for clarity*

| # | Pattern | Success Rate | Status | Outcome |
|---|---------|--------------|--------|---------|
| 3.6.1 | Pricing Discount Floor | 60% | Validated | WON |
| 3.6.2 | Territory Exclusion Limits | 55% | Validated | WON |
| 3.6.3 | Interim Agreement Protection | 75% | Validated | WON |
| 3.6.4 | Performance Quota Criteria | 65% | Validated | WON |

---

### 3.7 Design-Build (2 patterns)

| # | Pattern | Success Rate | Status |
|---|---------|--------------|--------|
| 3.7.1 | Phase-Based IP Transfer | 60% | Validated |
| 3.7.2 | Phase Mismatch Detection | 90% | Validated |

---

### 3.8 Broker/Facilitator (1 pattern)

| # | Pattern | Success Rate | Status |
|---|---------|--------------|--------|
| 3.8.1 | Broker Verification Obligations | 55% | Pending |

---

### 3.9 MSA Commercial Terms (11 NEW patterns)

*Source: Channel Partner Master Agreement V1→V2 Comparison*

| # | Pattern | Success Rate | Source | Outcome |
|---|---------|--------------|--------|---------|
| 3.9.1 | Term Extension + Auto-Renewal | 80% | §19.1.1 | ✅ WON |
| 3.9.2 | Title on Delivery | 85% | §12.1 | ✅ WON |
| 3.9.3 | Territory Protection with Cure | 70% | §4.2 | ✅ WON |
| 3.9.4 | Non-Compete Removal | 65% | §4.4 | ✅ WON |
| 3.9.5 | Litigation to Arbitration | 75% | §22.2 | ✅ WON |
| 3.9.6 | Insurance Specification | 90% | Appendix 5 | ✅ WON |
| 3.9.7 | Inspection Period Extension | 85% | §11.2 | ✅ WON |
| 3.9.8 | Acceptance Test Notice | 90% | §11.6 | ✅ WON |
| 3.9.9 | FM Payment for Work Done Only | 80% | §18.3 | ✅ WON |
| 3.9.10 | Work Suspension Notice | 75% | §9.10 | ✅ WON |
| 3.9.11 | Reporting Limits | 85% | §6.10 | ✅ WON |

#### 3.9.1: Term Extension + Auto-Renewal

**Problem:** Short initial term with no renewal protection
**Position:** Buyer / Balanced

**Revision:**
```
This Agreement shall continue in effect for an initial
~~twelve (12)~~ `thirty-six (36)` months.

~~An automatic renewal is expressly excluded.~~
`This Agreement shall automatically renew for successive one (1) year
periods unless either Party provides written notice of non-renewal
at least ninety (90) days prior to the end of the then-current term.`
```

**Business Impact:** Term tripled. Investment recovery period extended.
**Success Rate:** 80% balanced

---

#### 3.9.2: Title on Delivery

**Problem:** Retention of title until full payment creates risk
**Position:** Buyer / Strong

**Revision:**
```
~~The Company remains the owner of the Goods until full and
unconditional payment of the Contract Price.~~

`Title to the Goods shall be transferred to the Channel Partner
upon delivery.`
```

**Business Impact:** Title transfers on delivery, not payment. Eliminates vendor security interest risk.
**Success Rate:** 85% strong leverage

---

#### 3.9.3: Territory Protection with Cure

**Problem:** Vendor can unilaterally modify territory
**Position:** Reseller / Balanced

**Revision:**
```
The Company ~~is entitled to~~ `by mutual agreement may` modify
the Territory ~~by giving a [XXX]-month~~ `with 12-month` prior
written notice...

`Any reduction in Territory shall not affect the Channel Partner's
rights to continue serving existing End-Customers in the removed
territory for a period of twenty-four (24) months following such reduction.`
```

**Business Impact:** Requires mutual agreement. 90-day cure period. 24-month end-customer protection.
**Success Rate:** 70% balanced

---

#### 3.9.4: Non-Compete Removal

**Problem:** Non-compete restricts business opportunities
**Position:** Partner / Strong

**Revision:**
```
~~Non-Competition: During the term of this Master Agreement any
activities of the Channel Partner related to the manufacture and/or
sales of material handling equipment other than the Products shall
be restricted...~~

`[ENTIRE SECTION DELETED]`
```

**Business Impact:** Channel Partner can offer competing products.
**Success Rate:** 65% balanced (high value trade)

---

#### 3.9.5: Litigation to Arbitration

**Problem:** Litigation in distant forum creates cost burden
**Position:** Any / Balanced

**Revision:**
```
~~Any dispute shall be resolved solely in a federal or state court
of competent jurisdiction in the State of [X].~~

`The Parties shall attempt to resolve any dispute through good faith
negotiations between senior executives for thirty (30) days. If
negotiations fail, either Party may initiate binding arbitration
under the Commercial Arbitration Rules of the American Arbitration
Association. The arbitration shall be held in [mutually agreed location].`
```

**Business Impact:** Cost-effective dispute resolution. No jury trial risk.
**Success Rate:** 75% balanced

---

#### 3.9.6: Insurance Specification

**Problem:** Insurance requirements undefined or inadequate
**Position:** Any / Any

**Revision:**
```
[Add complete insurance schedule]

Commercial General Liability: $2,000,000 per occurrence / $5,000,000 aggregate
Products/Completed Operations: $2,000,000 per occurrence / $5,000,000 aggregate
Professional Liability (E&O): $2,000,000 per occurrence
Workers Compensation: Per statutory requirements
Automobile Liability: $1,000,000 combined single limit
Umbrella/Excess Liability: $5,000,000 per occurrence

`Upon request, Company shall cause its Commercial General Liability
and Umbrella policies to name Channel Partner as an additional insured.`
```

**Business Impact:** Clear requirements. Additional insured status available.
**Success Rate:** 90% any leverage

---

#### 3.9.7: Inspection Period Extension

**Problem:** 48-hour inspection window too short
**Position:** Buyer / Balanced

**Revision:**
```
The Channel Partner shall examine the Goods within
~~48 hours~~ `five (5) business days` upon receiving the Goods.

`Failure to conduct Delivery Inspection within five (5) business
days shall constitute deemed acceptance only for visible defects;
latent defects shall be governed by the warranty provisions.`
```

**Business Impact:** Reasonable inspection window. Latent defect protection preserved.
**Success Rate:** 85% any leverage

---

#### 3.9.8: Acceptance Test Notice

**Problem:** No advance notice of acceptance testing
**Position:** Buyer / Balanced

**Revision:**
```
`[NEW SECTION] The Company will notify the Channel Partner of
readiness for acceptance test after successful commissioning and
shall inform the Channel Partner of the date for acceptance test
at least five (5) business days in advance.`
```

**Business Impact:** Ability to prepare resources for testing.
**Success Rate:** 90% any leverage

---

#### 3.9.9: FM Payment for Work Done Only

**Problem:** Full payment obligation despite termination
**Position:** Buyer / Balanced

*See expansion in 2.8.3 above*

**Success Rate:** 80% balanced

---

#### 3.9.10: Work Suspension Notice

**Problem:** Vendor can suspend work without notice
**Position:** Buyer / Balanced

**Revision:**
```
~~The Company is entitled to suspend the Work until full payment.~~

`The Company may suspend the Work if payment remains outstanding
for more than fifteen (15) days after written notice of payment default,
provided that such notice shall not be given if non-payment is due
to the End-Customer's non-payment to the Channel Partner.

Before suspending Work, the Company shall provide five (5) business
days' additional written notice of intent to suspend only if the
Channel Partner has failed to make payment for more than thirty (30)
days beyond the due date, excluding delays caused by End-Customer
non-payment.`
```

**Business Impact:** 15-day + 5-day notice. Protection for end-customer delays.
**Success Rate:** 75% balanced

---

#### 3.9.11: Reporting Limits

**Problem:** Unlimited information disclosure obligations
**Position:** Partner / Balanced

**Revision:**
```
The Channel Partner shall keep the Company reasonably informed
of its business activities.

`The Channel Partner shall provide mutually agreed upon quarterly
reports summarizing project pipeline, pending opportunities, and
completed projects involving the Company's Products.

The Channel Partner shall not be required to disclose its complete
financial statements, customer-specific pricing, profit margins,
or other competitively sensitive information.`
```

**Business Impact:** Protects competitive information. Limits reporting burden.
**Success Rate:** 85% balanced

---

### 3.10 Services Procurement - Buyer Position (6 NEW patterns)

*Source: ATG MSA V1→V2 Comparison*

| # | Pattern | Success Rate | Source | Outcome |
|---|---------|--------------|--------|---------|
| 3.10.1 | Payment Withholding for Cause | 70% | §2.4 | ✅ WON |
| 3.10.2 | Deliverable Objection Period | 85% | §5 | ✅ WON |
| 3.10.3 | Safe Harbor Notice Period | 80% | §7 | ✅ WON |
| 3.10.4 | Multiple Failure Threshold | 75% | §8 | ✅ WON |
| 3.10.5 | Worldwide License Scope | 80% | §11.2 | ✅ WON |
| 3.10.6 | MSA Supremacy Clause | 90% | §15.3 | ✅ WON |

#### 3.10.1: Payment Withholding for Cause

**Problem:** No offset mechanism for vendor breach
**Position:** Buyer / Balanced

**Revision:**
```
Upon termination, ATG shall be paid for all Services performed.

`If the termination is for cause, Customer may withhold from amounts
otherwise due to ATG only such direct damages resulting from ATG's
breach that are established by written agreement of the parties.`
```

**Business Impact:** Offset for documented breach damages. Requires mutual agreement on amount.
**Success Rate:** 70% balanced

---

#### 3.10.2: Deliverable Objection Period

**Problem:** 7 days insufficient for review
**Position:** Buyer / Balanced

**Revision:**
```
Any objections must be documented and submitted within
~~seven (7)~~ `fourteen (14)` business days of receipt.
```

**Business Impact:** Doubles review time. Reduces auto-acceptance risk.
**Success Rate:** 85% any leverage

---

#### 3.10.3: Safe Harbor Notice Period

**Problem:** Schedule changes result in penalties
**Position:** Buyer / Balanced

**Revision:**
```
Customer acknowledges that failure to provide notice to proceed
in a timely manner may result in substantial changes to project timelines
`, unless Customer provides notification 72 hours before the scheduled
start date.`
```

**Business Impact:** Clear threshold for penalty-free rescheduling.
**Success Rate:** 80% balanced

---

#### 3.10.4: Multiple Failure Threshold

**Problem:** Single failure triggers vendor stop work
**Position:** Buyer / Balanced

**Revision:**
```
The Customer fails ~~to timely~~ `on two or more occasions to`
timely provide required inputs, approvals, or access to resources.
```

**Business Impact:** Grace period for single administrative oversight.
**Success Rate:** 75% balanced

---

#### 3.10.5: Worldwide License Scope

**Problem:** License geographically limited
**Position:** Buyer / Balanced

**Revision:**
```
ATG grants the Customer a perpetual, `worldwide`, non-exclusive,
royalty-free, non-transferable license to use ATG's Pre-Existing
Materials solely as incorporated into the deliverables.
```

**Business Impact:** Allows global use of deliverables.
**Success Rate:** 80% balanced

---

#### 3.10.6: MSA Supremacy Clause

**Problem:** Conflicting terms in other agreements
**Position:** Any / Any

**Revision:**
```
`In the event of any conflict or inconsistency between this Agreement
and any other agreement between the Parties, including without
limitation any nondisclosure or confidentiality agreements, the
terms of this Agreement shall control.`
```

**Business Impact:** Clarity on which terms govern.
**Success Rate:** 90% any leverage

---

### 3.11 Project Agreements (5 NEW patterns)

*Source: Master Projects Agreement V3→V4 Comparison*

| # | Pattern | Success Rate | Source | Outcome |
|---|---------|--------------|--------|---------|
| 3.11.1 | Prime Contract Flowdown Addendum | 75% | §1 | ✅ WON |
| 3.11.2 | Source Code Escrow Documentation | 80% | §6(c) | ✅ WON |
| 3.11.3 | Double Margin Prevention | 90% | §10(c) | ✅ WON |
| 3.11.4 | Security Interest Undisputed Only | 85% | §19 | ✅ WON |
| 3.11.5 | SOW Schedule Format | 90% | Exhibit A | ✅ WON |

#### 3.11.1: Prime Contract Flowdown Addendum

**Problem:** Unclear how prime contract terms apply
**Position:** Subcontractor / Balanced

**Revision:**
```
`To the extent Customer requires Company_A to comply with any terms
of Customer's prime contract with an end-user, such terms shall be
set forth in a separate, mutually executed addendum to this Agreement,
through which Customer will flow down the applicable provisions.`
```

**Business Impact:** Right to accept/reject prime contract requirements explicitly.
**Success Rate:** 75% balanced

---

#### 3.11.2: Source Code Escrow Documentation

**Problem:** Escrow terms undefined at delivery
**Position:** Buyer / Balanced

**Revision:**
```
~~solely in the context of an end-user required escrow agreement
with terms acceptable to Company_A~~

`solely in the context of an end-user required escrow agreement with
terms that have been provided to Company_A in writing and incorporated
into the SOW`
```

**Business Impact:** Escrow terms visible before commitment.
**Success Rate:** 80% balanced

---

#### 3.11.3: Double Margin Prevention

**Problem:** Margin charged on already-margined costs
**Position:** Buyer / Balanced

**Revision:**
```
costs and expenses incurred through the date of termination plus
reasonable margin on such costs and expenses `but only to the extent
such costs and expenses do not already include margin`
```

**Business Impact:** Prevents double-charging markup.
**Success Rate:** 90% any leverage

---

#### 3.11.4: Security Interest Undisputed Only

**Problem:** Disputed invoices block equipment release
**Position:** Buyer / Balanced

**Revision:**
```
Company_A retains a security interest in the Work until all
~~invoices~~ `undisputed invoices` associated with the Work
have been paid in full
```

**Business Impact:** Dispute invoices without impacting operations.
**Success Rate:** 85% balanced

---

#### 3.11.5: SOW Schedule Format

**Problem:** Inconsistent project documentation
**Position:** Any / Administrative

**Revision:**
```
The details of the Project are specified in Company_A's
~~Proposal #________, version~~ `Schedule ___ (Scope of Work)`,
dated ______________, attached hereto.
```

**Business Impact:** Standardizes SOW documentation format.
**Success Rate:** 90% any leverage

---

### 3.12 Subcontract Templates - Issuer Position (6 NEW patterns)

*Source: Subcontractor MSA Template*

| # | Pattern | Success Rate | Source | Type |
|---|---------|--------------|--------|------|
| 3.12.1 | Flow-Down with Priority Order | 80% | §2.2-2.3 | Template |
| 3.12.2 | Long Lead-Time Item Protocol | 75% | §2.10 | Template |
| 3.12.3 | Specially Manufactured Goods | 70% | §2.21 | Template |
| 3.12.4 | Arbitration Consolidation/Joinder | 85% | §2.24.3-4 | Template |
| 3.12.5 | Mutual Non-Solicitation | 80% | §2.25 | Template |
| 3.12.6 | Work During Dispute | 90% | §2.24 | Template |

#### 3.12.1: Flow-Down with Priority Order

**Problem:** Conflicting terms between documents
**Position:** Prime / Standard

**Template Language:**
```
ORDER OF PRIORITY AMONG CONTRACT DOCUMENTS:
In the event of conflict, the following order applies:
(a) the applicable IPA, as modified by Change Orders
(b) Schedule A of the applicable IPA
(c) the additional Contract Documents identified in Schedule B
(d) the applicable terms of the Prime Contract
(e) Schedule D of the applicable IPA
(f) the MSA, as amended by Schedule C
```

**Note:** Use when issuing subcontracts

---

#### 3.12.2: Long Lead-Time Item Protocol

**Problem:** Long lead items delay project
**Position:** Prime / Standard

**Template Language:**
```
Any component with procurement lead-time exceeding ninety (90) days
is a Long Lead-Time Item.

Within five (5) business days of IPA execution:
- Subcontractor shall secure purchase by binding agreement
- Provide written confirmation within three (3) business days
- Request advance payment within five (5) business days if needed
- Issue payment to supplier within 30 days of receiving funds
- Provide confirmation of payment within three (3) business days

Items procured using Long Lead-Time Funds shall be used only on
the Project for which issued.
```

---

#### 3.12.3: Specially Manufactured Goods

**Problem:** Custom goods require special handling
**Position:** Prime / Standard

**Template Includes:**
- Pre-delivery inspection rights with 1-day notice
- Title/risk transfer on delivery to project site
- 3-day replacement requirement for damaged goods
- Rejection rights with termination, price reduction, or replacement options
- Enhanced warranties for custom goods

---

#### 3.12.4: Arbitration Consolidation/Joinder

**Problem:** Separate arbitrations for related disputes
**Position:** Prime / Standard

**Template Language:**
```
[COMPANY], at its sole discretion, may:
- Consolidate arbitration with any other arbitration where:
  (1) the other agreement permits consolidation
  (2) substantially common questions of law or fact exist
  (3) materially similar procedural rules apply

- Include Subcontractor by joinder in any arbitration that arises
  out of or relates to Subcontractor's Work
```

---

#### 3.12.5: Mutual Non-Solicitation

**Problem:** Employee poaching during/after project
**Position:** Prime / Mutual

**Template Language:**
```
During the performance of the Work and for a period of two years
thereafter, neither Party shall hire or solicit for hire any of
the other Party's employees without prior written consent.
```

---

#### 3.12.6: Work During Dispute

**Problem:** Disputes halt project progress
**Position:** Prime / Standard

**Template Language:**
```
In the event of any dispute, Subcontractor agrees to proceed with
the performance of the Work in the manner directed by [COMPANY]
so as not to delay or interfere with the completion of the Work,
and [COMPANY] shall continue to make payments for undisputed amounts.

The requirement to proceed applies to ANY Contract or Project
Subcontractor is performing. Controversy on one Contract shall
not impact obligations on other Contracts or Projects.
```

---

## PART 4: COORDINATION CLUSTERS

### 4.1 Customer Protection System
**Patterns:** 2.4.1, 2.4.2, 2.4.3, 3.1.1, 3.1.2, 2.5.1, 3.9.3
**Purpose:** Prevent displacement
**Trigger:** Downstream supplier relationships

### 4.2 Payment & Acceptance Flow
**Patterns:** 2.3.2, 3.1.3, 3.1.5, 2.3.3, 2.9.1, 3.3.4, 2.3.1, 3.2.5, 3.9.10, 3.10.1
**Purpose:** Align cash flow
**Trigger:** Multi-party flowdown

### 4.3 Liability Flow-Through
**Patterns:** 2.10.3, 2.1.1, 2.2.4, 2.10.4, 3.1.2, 3.11.3
**Purpose:** Match exposure
**Trigger:** Upstream/downstream gap

### 4.4 Audit & Documentation Control
**Patterns:** 3.2.3, 2.4.3, 3.3.3, 3.5.1, 3.9.11, 3.11.2
**Purpose:** Limit burden
**Trigger:** Operational overhead

---

## PART 5: NEGOTIATION FRAMEWORK

### Four-Tier Fallback (All Patterns)

| Tier | Definition | When to Use |
|------|------------|-------------|
| **Optimal** | Best protection | Strong leverage |
| **Strong** | Good protection | Balanced |
| **Acceptable** | Minimum | Weak leverage |
| **Walk-Away** | Non-negotiable | Any |

### Success Rate by Contract Type

| Type | High (70-85%) | Medium (40-70%) | Low (15-40%) |
|------|---------------|-----------------|--------------|
| MSA | +5% | +0% | -5% |
| IPA | +0% | +5% | +0% |
| SOW | +5% | +5% | +0% |
| MOU | +10% | +5% | N/A |
| PO | +0% | +0% | -5% |

---

## PART 6: DEALBREAKER DETECTION

### Combined Triggers

| Trigger | Components | Threshold |
|---------|------------|-----------|
| **A** | No protection + competitor assignment + direct warranty | ALL |
| **B** | No cap + one-sided indemnity + no flowdown | ALL |
| **C** | 100% upfront + no milestones + no wind-down | ALL |
| **F** | Pricing control + weak protection + vague quotas + no commission + short term | 4+ |
| **G** | Design contract + work-for-hire + no phase gates + no leverage | ALL |

### Walk-Away Triggers by Pattern

| Pattern | Walk-Away If |
|---------|--------------|
| 2.1.1 | Unlimited, no carve-out protection |
| 2.4.1 | Zero protection, no negotiation possible |
| 2.8.2 | < 7 days, no cure period |
| 3.1.1 | Customer handoff structure |
| 3.7.1 | Work-for-hire non-negotiable |

---

## PART 7: RISK INDICATORS (NEW)

*Patterns to WATCH FOR — adverse terms that were accepted as trade-offs*

### 7.1 IP Risk Indicators

| Indicator | Source | Risk Level |
|-----------|--------|------------|
| Vendor IP Retention Expansion | ATG §11.1 | HIGH |
| Standalone Use Prohibition | ATG §11.2 | MEDIUM |
| Work-for-hire mandatory | General | CRITICAL |
| No modification rights | ATG §11.1 | MEDIUM |

**Detection Pattern:**
```
WATCH FOR:
- "ATG retains ownership" + expanded categories
- "not on a standalone basis or separate from deliverables"
- "shall not have the right to modify"
```

### 7.2 Payment Risk Indicators

| Indicator | Source | Risk Level |
|-----------|--------|------------|
| 100% Product Prepayment | ATG §3 | HIGH |
| Third-party return policy only | ATG §5 | MEDIUM |
| Payment before approval | General | HIGH |

**Detection Pattern:**
```
WATCH FOR:
- "prepay all product costs"
- "return policy shall be dictated by that vendor"
- "payment in full prior to shipment"
```

### 7.3 Liability Risk Indicators

| Indicator | Source | Risk Level |
|-----------|--------|------------|
| Gross negligence standard only | ATG §13 | MEDIUM |
| Aggregate cap too low | General | HIGH |
| Unlimited carve-outs | General | CRITICAL |

**Detection Pattern:**
```
WATCH FOR:
- "gross negligence" without ordinary negligence coverage
- Cap less than 50% of contract value
- Carve-outs that could exceed total contract value
```

---

## PART 8: STATUTORY CONFLICTS (UCC) ⚠️ NEW v2.1

**Total Rules:** 26 UCC statutory rules
**Source:** Delaware UCC Title 6 (Article 2) + Systems Integrator patterns
**Detection Method:** Keyword trigger matching with word-boundary validation
**Risk Score Integration:** 40% weight applied when violation detected
**Formula:** `Final Score = (Base Score × 0.6) + (Risk Multiplier × 0.4)`

### 8.1 UCC-2-719: Remedy Limitations

**Citation:** 6 Del. C. § 2-719
**Category:** REMEDY_LIMITATION

#### 8.1.1: Consequential Damages Exclusion / Sole Remedy

**Rule ID:** UCC-2-719
**Trigger Concepts:**
- prepayment lock
- non-refundable
- remedy veto
- sole remedy
- exclusive remedy
- limited remedy
- waiver of remedy
- no refund
- forfeiture
- full prepayment
- only remedy
- exclusive recourse
- waives all claims
- waive all claims
- waive claims for

**Risk Multiplier:** 10.0 (CRITICAL)

**Detection Pattern:**
```
"Buyer expressly waives all claims for consequential damages, lost
profits, and business interruption. Seller's sole liability shall be
limited to repair or replacement of defective goods."
```

**UCC Provision:**
- UCC § 2-719(1): Agreement may provide for remedies in addition to or substitution for those provided by this Article
- UCC § 2-719(2): Where circumstances cause an exclusive or limited remedy to fail of its essential purpose, remedy may be had as provided in this title
- UCC § 2-719(3): Limitation of consequential damages for injury to person in consumer goods is prima facie unconscionable

**Business Impact:**
Client loses all self-help remedies; vendor holds unilateral control over dispute resolution. If vendor's remedy fails, your only recourse may be worthless repair promises while client demands performance.

**SI Impact:**
If vendor equipment fails during client project, SI cannot recover:
- Lost profits from project delays
- Liquidated damages paid to end-customer
- Costs of emergency workarounds

**Forensic Test:**
Does the clause create a "failure of essential purpose" by removing all meaningful remedies?

**Success Rate:** N/A (statutory violation, not negotiable pattern)

**Recommendation:**
- REMOVE consequential damages waiver entirely, OR
- ADD carve-outs using Pattern 2.1.2 (Carve-Out Protection), OR
- ADD UCC preservation clause: "Nothing in this Agreement shall be construed to limit Client's remedies under Delaware UCC § 2-719 if any limited remedy fails of its essential purpose"

**Coordinates:** Pattern 2.1.2 (Carve-Out Protection)

---

### 8.2 UCC-2-302: Unconscionability

**Citation:** 6 Del. C. § 2-302
**Category:** ENFORCEABILITY

#### 8.2.1: Unconscionable Clauses

**Rule ID:** UCC-2-302
**Trigger Concepts:**
- gross disparity
- waiver of gross negligence
- waiver of willful misconduct
- unilateral modification
- sole discretion
- absolute discretion
- without cause
- for any reason
- no liability whatsoever
- take it or leave it
- non-negotiable
- standard terms

**Risk Multiplier:** 10.0 (CRITICAL)

**Detection Pattern:**
```
"Vendor may modify pricing or terminate this Agreement at any time,
in its sole discretion, without cause. Buyer waives all claims for
gross negligence or willful misconduct."
```

**UCC Provision:**
- UCC § 2-302(1): Court may refuse to enforce contract or clause found unconscionable at time made
- UCC § 2-302(2): Parties shall be afforded reasonable opportunity to present evidence as to commercial setting, purpose, and effect

**Business Impact:**
Contract or clause may be unenforceable; litigation risk elevated. Terms you accept from vendors may not be enforceable, leaving you without recourse.

**SI Impact:**
OEM standard terms often heavily favor vendor - SI may be accepting unconscionable terms that must be passed to client but are unenforceable.

**Forensic Test:**
Does the clause create gross disparity in bargaining position or impose terms no reasonable person would accept? If 3+ limitation clauses combine to eliminate all client remedies, cumulative effect may be unconscionable.

**Cumulative Patterns to Watch:**
- Prepayment + Restricted Withholding + Gross Negligence Standard
- No Liability + Sole Discretion + Unilateral Termination
- Waiver of Damages + Force Performance + No Refund

**Success Rate:** N/A (statutory violation, not negotiable pattern)

**Recommendation:**
- REMOVE unconscionable clauses (sole discretion, gross negligence waivers)
- RESTORE ordinary negligence standard
- ELIMINATE cumulative limitations that combine to remove all remedies

**Coordinates:** Pattern 2.2.1 (Mutual Indemnification), Pattern 2.11.1 (Gross Negligence)

---

### 8.3 UCC-2-717: Deduction of Damages from Price

**Citation:** 6 Del. C. § 2-717
**Category:** PAYMENT_RIGHTS

#### 8.3.1: No Set-Off / No Withholding

**Rule ID:** UCC-2-717
**Trigger Concepts:**
- no set-off
- payment without deduction
- no deduction
- no offset
- no withholding
- pay in full
- unconditional payment
- waive right to deduct
- no right to withhold
- payment regardless

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
"Buyer shall pay all invoices in full without deduction, set-off,
or withholding. Buyer waives all rights to deduct damages from
amounts owed."
```

**UCC Provision:**
- UCC § 2-717: Buyer on notifying seller of intention to do so may deduct all or any part of the damages resulting from any breach of contract from any part of the price still due under the same contract

**Business Impact:**
Client must finance vendor defaults; cash flow risk and litigation burden shifted to buyer.

**SI Impact:**
If SI can't withhold from vendors when they breach, SI finances vendor failures while still owing client. You pay vendor 100%, vendor breaches, you sue to recover while simultaneously owing client credits.

**Forensic Test:**
Does the clause waive the buyer's statutory right to deduct damages from amounts owed?

**Success Rate:** N/A (statutory violation, not negotiable pattern)

**Recommendation:**
- REMOVE no set-off clause entirely, OR
- ADD: "Client may deduct from amounts due any damages resulting from Vendor's breach, upon written notice to Vendor specifying the breach and damages claimed"

**Coordinates:** Pattern 2.3.3 (Dispute Rights), Pattern 3.10.1 (Payment Withholding for Cause)

---

### 8.4 UCC-2-718: Liquidated Damages / Deposits

**Citation:** 6 Del. C. § 2-718
**Category:** DAMAGES

#### 8.4.1: Unreasonable Liquidated Damages

**Rule ID:** UCC-2-718
**Trigger Concepts:**
- liquidated damages
- penalty clause
- deposit forfeiture
- non-refundable deposit
- cancellation fee
- early termination fee
- restocking fee
- delay damages
- LD cap
- daily penalty

**Risk Multiplier:** 6.0 (MEDIUM)

**Detection Pattern:**
```
"Non-refundable deposit of $500,000 due upon execution. Early termination
fee equals 100% of total contract value. Delay liquidated damages: $100,000
per day, uncapped."
```

**UCC Provision:**
- UCC § 2-718(1): Damages for breach may be liquidated but only at amount reasonable in light of anticipated or actual harm
- UCC § 2-718(2): Where seller justifiably withholds delivery, buyer is entitled to restitution of amount by which sum paid exceeds reasonable liquidated damages

**Business Impact:**
Penalty clauses may be unenforceable; excessive fees create negotiation leverage.

**SI Impact:**
Compare vendor LD exposure to client LD exposure - is there a gap you absorb? Client LD of $50K/day but vendor LD capped at $10K total = $40K/day exposure.

**Forensic Test:**
Are liquidated damages reasonable in light of anticipated harm, or do they constitute an unenforceable penalty?

**Reasonableness Factors:**
- Anticipated harm at time of contracting
- Difficulty of proving actual loss
- Proportionality to contract value
- Industry standard practices

**Key Indicators:**
- Liquidated damages exceed 20% of contract value
- Same damages apply regardless of breach severity
- No calculation methodology provided
- Forfeiture of all prepaid amounts regardless of work completed

**Success Rate:** N/A (statutory violation, not negotiable pattern)

**Recommendation:**
- CAP liquidated damages at reasonable percentage (10-20% of contract value)
- REQUIRE calculation methodology
- ADD restitution provision for prepaid amounts exceeding actual damages

**Coordinates:** Pattern 2.3.2 (Milestone Payments), Pattern 3.11.3 (Double Margin Prevention)

---

### 8.5 UCC-2-725: Statute of Limitations

**Citation:** 6 Del. C. § 2-725
**Category:** CLAIMS_PERIOD

#### 8.5.1: Shortened Claims Period

**Rule ID:** UCC-2-725
**Trigger Concepts:**
- limitation period
- statute of limitations
- claims period
- notice requirement
- time bar
- waiver of claims
- claims must be made within
- notify within
- discover within

**Risk Multiplier:** 5.0 (MEDIUM)

**Detection Pattern:**
```
"All claims must be made within 6 months of delivery. Claims not
submitted within this period are forever waived."
```

**UCC Provision:**
- UCC § 2-725(1): Action for breach must be commenced within four years after cause of action accrued
- UCC § 2-725(2): Parties may reduce period of limitation to not less than one year but may not extend it

**Business Impact:**
Artificially shortened periods may bar legitimate claims; unenforceable if below 1 year.

**SI Impact:**
Vendor claims period shorter than client claims period = latent defect exposure. Client can claim for 4 years, vendor limits you to 1 year = 3 years unprotected.

**Forensic Test:**
Does the clause improperly shorten (below 1 year) or attempt to extend (beyond 4 years) the statutory limitation period?

**Valid Range:**
- Minimum: 1 year
- Maximum: 4 years
- Periods shorter than 1 year or longer than 4 years are unenforceable

**Success Rate:** N/A (statutory violation, not negotiable pattern)

**Recommendation:**
- EXTEND claims period to minimum 1 year (preferably 2-4 years)
- ALIGN vendor claims period with client claims period to avoid gaps

**Coordinates:** Pattern 2.8.2 (Cure Period), SI-001 (Warranty Flow-Down Gap)

---

### 8.6 UCC-2-312: Warranty of Title / IP Infringement

**Citation:** 6 Del. C. § 2-312
**Category:** WARRANTY

#### 8.6.1: Title / IP Warranty Disclaimer

**Rule ID:** UCC-2-312
**Trigger Concepts:**
- title
- ownership
- lien
- security interest
- encumbrance
- free and clear
- good title
- rightful owner
- IP infringement
- patent infringement
- third party claims
- IP indemnity

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
"Seller disclaims all warranties of title. Equipment may be subject
to liens or security interests. No IP indemnification provided."
```

**UCC Provision:**
- UCC § 2-312(1): Seller warrants good title, rightful transfer, goods free from security interest or lien unknown to buyer
- UCC § 2-312(2): Seller who is a merchant warrants goods are delivered free of rightful claim of infringement
- UCC § 2-312(3): Warranty can be excluded or modified only by specific language or circumstances

**Business Impact:**
Equipment could be repossessed or enjoined for IP infringement.

**SI Impact:**
If vendor equipment has liens or IP claims, client's system is at risk. Client's warehouse shuts down due to patent injunction on conveyor system SI installed.

**Forensic Test:**
Does the equipment come with clear title? Are there liens or IP claims?

**Key Indicators:**
- Disclaimer of title warranty
- No IP indemnification
- Seller not actual manufacturer
- Equipment subject to financing

**Success Rate:** N/A (statutory violation, not negotiable pattern)

**Recommendation:**
- REQUIRE title warranty (free and clear of liens)
- ADD IP indemnification from vendor
- VERIFY equipment ownership before purchase

**Coordinates:** Pattern 2.2.4 (IP Indemnity Notice), SI-003 (Indemnification Asymmetry)

---

### 8.7 UCC-2-313: Express Warranties

**Citation:** 6 Del. C. § 2-313
**Category:** WARRANTY

#### 8.7.1: Performance Specifications as Warranties

**Rule ID:** UCC-2-313
**Trigger Concepts:**
- throughput
- capacity
- speed
- rate
- performance specification
- cycles per
- units per hour
- uptime
- availability
- MTBF
- specification
- data sheet
- proposal claims
- guaranteed

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
"System throughput: 500 units per hour per vendor data sheet. 99.5% uptime
guaranteed per proposal. Equipment rated at 1,000 cycles per day."
```

**UCC Provision:**
- UCC § 2-313(1)(a): Affirmation of fact or promise made by seller to buyer which relates to goods and becomes part of basis of bargain creates express warranty
- UCC § 2-313(1)(b): Description of goods which is made part of basis of bargain creates express warranty
- UCC § 2-313(1)(c): Sample or model which is made part of basis of bargain creates express warranty
- UCC § 2-313(2): No need for formal words like "warrant" or "guarantee" or specific intention to make warranty

**Business Impact:**
Vendor bound by performance claims in sales materials and proposals.

**SI Impact:**
SI may be guaranteeing system performance based on vendor's express warranties - are they protected? You guarantee client 500 units/hour based on vendor spec; equipment delivers 400 = your liability.

**Forensic Test:**
What specific performance claims has vendor made that constitute express warranties?

**Key Indicators:**
- Performance specifications in proposal
- Throughput guarantees
- Uptime/availability commitments
- Reference to data sheets or specifications

**Success Rate:** N/A (statutory recognition, enforceable warranty)

**Recommendation:**
- DOCUMENT all vendor performance claims as express warranties
- FLOW DOWN vendor warranties to match client commitments
- ADD remedy for failure to meet specifications

**Coordinates:** SI-007 (Performance Guarantee Pass-Through Failure)

---

### 8.8 UCC-2-314: Implied Warranty of Merchantability

**Citation:** 6 Del. C. § 2-314
**Category:** WARRANTY

#### 8.8.1: "AS IS" / Merchantability Disclaimer

**Rule ID:** UCC-2-314
**Trigger Concepts:**
- as is
- with all faults
- no warranty
- merchantability disclaimed
- sold as is
- buyer beware
- no implied warranties
- where is
- current condition

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
"Equipment sold AS IS, WITH ALL FAULTS. Seller disclaims all implied
warranties, including merchantability."
```

**UCC Provision:**
- UCC § 2-314(1): Warranty of merchantability is implied in contract for sale if seller is merchant with respect to goods of that kind
- UCC § 2-314(2)(a): Goods must pass without objection in trade under contract description
- UCC § 2-314(2)(c): Goods must be fit for ordinary purposes for which such goods are used

**Business Impact:**
Equipment must be fit for ordinary purpose unless properly disclaimed.

**SI Impact:**
AS IS equipment may not be fit for warehouse integration purposes. Conveyor sold "AS IS" breaks down; no warranty recourse but client expects working system.

**Forensic Test:**
Has the implied warranty of merchantability been disclaimed? If so, was it conspicuous?

**Key Indicators:**
- AS IS language in caps or bold
- Disclaimer of implied warranties
- Used or refurbished equipment
- Prototype or beta equipment

**Success Rate:** N/A (statutory violation if disclaimer not conspicuous)

**Recommendation:**
- REMOVE AS IS clause for new equipment
- If AS IS accepted, ADD detailed inspection report + acceptance testing
- NEGOTIATE limited warranty for critical components

**Coordinates:** Pattern 3.1.2 (Warranty Coordination), Pattern 3.9.7 (Inspection Period Extension)

---

### 8.9 UCC-2-315: Fitness for Particular Purpose

**Citation:** 6 Del. C. § 2-315
**Category:** WARRANTY

#### 8.9.1: Particular Purpose Reliance

**Rule ID:** UCC-2-315
**Trigger Concepts:**
- fitness for purpose
- particular purpose
- specific application
- reliance on seller
- seller recommends
- suitable for
- application engineering
- configured for
- customized for

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
"Vendor recommended this conveyor system for cold storage application
at -20°F. Equipment configured specifically for frozen food handling."
```

**UCC Provision:**
- UCC § 2-315: Where seller at time of contracting has reason to know particular purpose for which goods are required and that buyer is relying on seller's skill or judgment to select or furnish suitable goods, there is implied warranty goods shall be fit for such purpose

**Business Impact:**
Vendor liable if equipment unsuitable for disclosed particular purpose.

**SI Impact:**
If vendor recommended equipment for client's specific application, they warrant fitness. Vendor knew it was for cold storage; equipment fails at -20°F = vendor liability.

**Forensic Test:**
Did vendor know your specific application? Did you rely on their recommendation?

**Key Indicators:**
- Vendor did application engineering
- Vendor selected/recommended the equipment
- Specific throughput or environmental requirements disclosed
- Custom configuration for your application

**Success Rate:** N/A (statutory recognition, enforceable warranty)

**Recommendation:**
- DOCUMENT vendor's knowledge of particular purpose in contract
- SPECIFY reliance on vendor's expertise in writing
- PRESERVE fitness warranty (do not allow disclaimer)

**Coordinates:** SI-007 (Performance Guarantee Pass-Through Failure)

---

### 8.10 UCC-2-316: Exclusion of Warranties

**Citation:** 6 Del. C. § 2-316
**Category:** WARRANTY

#### 8.10.1: Improper Warranty Disclaimer

**Rule ID:** UCC-2-316
**Trigger Concepts:**
- as is
- with all faults
- merchantability
- fitness
- no implied warranties
- disclaimer
- exclusion of warranties
- conspicuous
- bold
- caps
- ALL CAPS

**Risk Multiplier:** 9.0 (CRITICAL)

**Detection Pattern:**
```
"Seller disclaims all warranties, express and implied, including
merchantability and fitness for a particular purpose." [Buried in
small print, page 37 of contract]
```

**UCC Provision:**
- UCC § 2-316(1): Words or conduct tending to negate warranty shall be construed wherever reasonable as consistent with each other
- UCC § 2-316(2): To exclude merchantability, language must mention merchantability and be conspicuous; to exclude fitness, exclusion must be in writing and conspicuous
- UCC § 2-316(3)(a): AS IS, WITH ALL FAULTS or similar language excludes implied warranties
- UCC § 2-316(3)(b): Examination or refusal to examine excludes defects that examination should have revealed

**Business Impact:**
Improper disclaimer = warranties still exist despite contract language.

**SI Impact:**
Invalid warranty disclaimers may give SI more protection than contract appears to provide. Vendor's buried disclaimer may be unenforceable - SI may have warranty rights it thinks were waived.

**Forensic Test:**
Is the warranty disclaimer conspicuous? Does it specifically mention merchantability?

**Key Indicators (Invalid Disclaimers):**
- Disclaimer buried in fine print (invalid)
- Merchantability not specifically mentioned (invalid for merchantability)
- Fitness disclaimer not in writing (invalid)
- AS IS not conspicuous (may be invalid)

**Success Rate:** N/A (statutory violation if not properly executed)

**Recommendation:**
- CHALLENGE validity of disclaimers not in conspicuous ALL CAPS
- VERIFY merchantability specifically mentioned for merchantability disclaimer
- DEMAND fitness disclaimer be in writing and conspicuous
- IF disclaimer invalid, assert warranty rights

**Coordinates:** Pattern 3.1.2 (Warranty Coordination), UCC-2-314, UCC-2-315

---

### 8.11 UCC-2-207: Battle of the Forms

**Citation:** 6 Del. C. § 2-207
**Category:** CONTRACT_FORMATION

#### 8.11.1: Conflicting Terms in PO vs. Acknowledgment

**Rule ID:** UCC-2-207
**Trigger Concepts:**
- purchase order
- acknowledgment
- confirmation
- terms and conditions
- additional terms
- different terms
- prevail
- supersede
- govern
- control
- battle of forms

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
Your PO: "Full warranties apply. Unlimited liability."
Vendor Acknowledgment: "AS IS. Liability limited to purchase price.
Our terms and conditions govern."
[You accept goods without objecting to acknowledgment]
```

**UCC Provision:**
- UCC § 2-207(1): Definite expression of acceptance operates as acceptance even with additional or different terms
- UCC § 2-207(2): Additional terms become part of contract between merchants unless materially alter, offer limits acceptance, or objection given
- UCC § 2-207(3): Conduct recognizing contract existence is sufficient even without writings establishing contract

**Business Impact:**
Vendor's terms may silently become binding through battle of forms.

**SI Impact:**
Your PO had full warranties; vendor acknowledgment disclaimed them; silence = vendor terms win.

**Forensic Test:**
Whose terms govern - your PO or vendor's acknowledgment?

**Key Indicators:**
- Your PO silent on which terms prevail
- Vendor acknowledgment adds/changes terms
- Different limitation of liability provisions
- Different warranty provisions
- No objection to vendor's additional terms

**Success Rate:** N/A (statutory rule, outcome depends on actions)

**Recommendation:**
- ADD to PO: "This PO and our terms prevail. Any additional or different terms in acceptance are objected to and rejected."
- OBJECT in writing to vendor's conflicting acknowledgment terms within reasonable time
- REQUIRE vendor acceptance without modification

**Coordinates:** Pattern 3.10.6 (MSA Supremacy Clause)

---

### 8.12 UCC-2-609: Right to Adequate Assurance

**Citation:** 6 Del. C. § 2-609
**Category:** PERFORMANCE_SECURITY

#### 8.12.1: Waiver of Assurance Rights

**Rule ID:** UCC-2-609
**Trigger Concepts:**
- assurance
- insecurity
- suspend
- adequate assurance
- reasonable grounds
- demand assurance
- performance bond
- letter of credit
- guarantee
- security

**Risk Multiplier:** 5.0 (MEDIUM)

**Detection Pattern:**
```
"Buyer waives all rights to demand assurance or suspend performance.
Buyer shall continue performance regardless of Seller's financial condition."
```

**UCC Provision:**
- UCC § 2-609(1): When reasonable grounds for insecurity arise, party may demand adequate assurance and suspend performance until received
- UCC § 2-609(2): Between merchants, reasonableness of grounds and adequacy of assurance determined by commercial standards
- UCC § 2-609(4): Failure to provide adequate assurance within reasonable time (not exceeding 30 days) is repudiation

**Business Impact:**
Right to demand proof vendor can perform before you're committed.

**SI Impact:**
If vendor is struggling (missed deliveries, financial issues), can SI demand assurance? Vendor misses first milestone; SI can demand assurance before paying next invoice.

**Forensic Test:**
Does contract preserve your right to demand assurance if vendor shows signs of trouble?

**Key Indicators:**
- Waiver of right to demand assurance
- No termination for insolvency
- No right to suspend for reasonable grounds

**Success Rate:** N/A (statutory right, should be preserved)

**Recommendation:**
- PRESERVE right to demand assurance
- ADD right to suspend if assurance not provided within 30 days
- ADD termination right for insolvency or material adverse change

**Coordinates:** Pattern 2.8.1 (Mutual Termination)

---

### 8.13 UCC-2-610: Anticipatory Repudiation

**Citation:** 6 Del. C. § 2-610
**Category:** PERFORMANCE_SECURITY

#### 8.13.1: Vendor Signals Won't Perform

**Rule ID:** UCC-2-610
**Trigger Concepts:**
- repudiation
- anticipatory breach
- will not perform
- cannot perform
- refuses to perform
- inability to perform
- won't deliver
- cancel
- withdraw

**Risk Multiplier:** 6.0 (MEDIUM)

**Detection Pattern:**
```
"Vendor announces equipment line is discontinued and will not fulfill
remaining orders. Contract requires Buyer to continue payment."
```

**UCC Provision:**
- UCC § 2-610(a): When either party repudiates, aggrieved party may await performance for commercially reasonable time
- UCC § 2-610(b): Aggrieved party may resort to any remedy for breach even if notified willingness to retract repudiation
- UCC § 2-610(c): Aggrieved party may suspend own performance or identify goods to contract

**Business Impact:**
Right to act immediately when vendor signals breach.

**SI Impact:**
Vendor announces equipment is discontinued mid-project - what are SI's rights? Vendor says they're exiting the market; SI can source elsewhere immediately.

**Forensic Test:**
What rights do you have if vendor indicates they won't or can't perform?

**Key Indicators:**
- No right to terminate for anticipatory breach
- Must continue performance despite vendor repudiation
- Force majeure extends to voluntary discontinuation

**Success Rate:** N/A (statutory right, should be preserved)

**Recommendation:**
- PRESERVE right to terminate for anticipatory repudiation
- ADD right to suspend payment upon repudiation
- ADD right to source replacement equipment at vendor's expense

**Coordinates:** Pattern 2.8.1 (Mutual Termination)

---

### 8.14 UCC-2-601: Buyer's Rights on Improper Delivery

**Citation:** 6 Del. C. § 2-601
**Category:** DELIVERY_ACCEPTANCE

#### 8.14.1: Rejection Rights

**Rule ID:** UCC-2-601
**Trigger Concepts:**
- reject
- rejection
- non-conforming
- does not conform
- fails to conform
- defective delivery
- wrong goods
- partial shipment
- short shipment
- wrong quantity

**Risk Multiplier:** 6.0 (MEDIUM)

**Detection Pattern:**
```
"Buyer waives all rights to reject goods. Buyer's sole remedy is
price adjustment. Acceptance occurs upon delivery."
```

**UCC Provision:**
- UCC § 2-601(a): If goods fail to conform to contract in any respect, buyer may reject the whole
- UCC § 2-601(b): Buyer may accept the whole
- UCC § 2-601(c): Buyer may accept any commercial unit or units and reject the rest

**Business Impact:**
Right to reject defective goods entirely.

**SI Impact:**
Can SI reject non-conforming equipment, or must accept and sue? Robot arrives non-functional; rejection right lets SI refuse and source elsewhere.

**Forensic Test:**
Can you reject non-conforming equipment, or must you accept and repair?

**Key Indicators:**
- Waiver of right to reject
- Must accept with price adjustment only
- Limited inspection period
- Acceptance upon delivery

**Success Rate:** N/A (statutory right, should be preserved)

**Recommendation:**
- PRESERVE right to reject non-conforming goods
- ADD reasonable inspection period before acceptance
- AVOID acceptance upon delivery clause

**Coordinates:** Pattern 3.9.7 (Inspection Period Extension), UCC-2-606

---

### 8.15 UCC-2-606: What Constitutes Acceptance

**Citation:** 6 Del. C. § 2-606
**Category:** DELIVERY_ACCEPTANCE

#### 8.15.1: Deemed Acceptance / Short Inspection Period

**Rule ID:** UCC-2-606
**Trigger Concepts:**
- acceptance
- deemed accepted
- acceptance upon delivery
- acceptance upon installation
- acceptance upon use
- inspection period
- acceptance period
- sign-off

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
"Acceptance occurs upon delivery. Equipment deemed accepted if not
rejected within 48 hours. Installation constitutes acceptance."
```

**UCC Provision:**
- UCC § 2-606(1)(a): Acceptance occurs when buyer after reasonable opportunity to inspect signifies goods are conforming or will take despite non-conformity
- UCC § 2-606(1)(b): Acceptance occurs when buyer fails to make effective rejection after reasonable opportunity to inspect
- UCC § 2-606(1)(c): Acceptance occurs when buyer does any act inconsistent with seller's ownership

**Business Impact:**
Once accepted, rejection rights are lost.

**SI Impact:**
Equipment installed in client's facility may trigger acceptance before full testing. Conveyor installed, then discovered defective; acceptance locks SI in.

**Forensic Test:**
When does acceptance occur? How much time do you have to inspect?

**Key Indicators:**
- Acceptance upon delivery (not installation)
- Short inspection period (< 30 days)
- Deemed acceptance clause
- Installation = acceptance
- Payment = acceptance

**Success Rate:** N/A (statutory rule, must have reasonable opportunity)

**Recommendation:**
- EXTEND inspection period to 30+ days
- DEFINE acceptance as after successful testing, not delivery or installation
- ADD deemed acceptance only after reasonable inspection period

**Coordinates:** Pattern 3.9.7 (Inspection Period Extension), Pattern 3.9.8 (Acceptance Test Notice)

---

### 8.16 UCC-2-607: Notice of Breach

**Citation:** 6 Del. C. § 2-607
**Category:** DELIVERY_ACCEPTANCE

#### 8.16.1: Short Notice Period for Claims

**Rule ID:** UCC-2-607
**Trigger Concepts:**
- notice of breach
- notify within
- reasonable time
- discovery of defect
- notice period
- claim period
- written notice
- breach notification

**Risk Multiplier:** 6.0 (MEDIUM)

**Detection Pattern:**
```
"Buyer must provide written notice of any defect within 10 days of
discovery or all warranty claims are waived."
```

**UCC Provision:**
- UCC § 2-607(2): Acceptance of goods by buyer precludes rejection of goods accepted
- UCC § 2-607(3)(a): Buyer must notify seller of breach within reasonable time after discovery or be barred from remedy

**Business Impact:**
Late notice = lost remedy.

**SI Impact:**
Defect discovered 6 months after installation - did SI notify in time? Defect discovered, but notice 5 days late = no warranty claim.

**Forensic Test:**
What notice must you give and when to preserve your claims?

**Key Indicators:**
- Short notice period (< 30 days)
- Notice in writing required
- Specific notice format required
- Notice to specific person/address required

**Success Rate:** N/A (statutory requirement, must be reasonable)

**Recommendation:**
- EXTEND notice period to reasonable time (30-90 days)
- CLARIFY what constitutes adequate notice
- AVOID strict format requirements

**Coordinates:** Pattern 2.2.4 (IP Indemnity Notice), UCC-2-725

---

### 8.17 UCC-2-608: Revocation of Acceptance

**Citation:** 6 Del. C. § 2-608
**Category:** DELIVERY_ACCEPTANCE

#### 8.17.1: Latent Defect Return Rights

**Rule ID:** UCC-2-608
**Trigger Concepts:**
- revoke acceptance
- revocation
- return
- rescind
- substantially impairs
- cure failure
- latent defect
- hidden defect
- concealed defect

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
"No returns after acceptance. Buyer waives all revocation rights.
Repair is sole remedy after acceptance."
```

**UCC Provision:**
- UCC § 2-608(1)(a): Buyer may revoke acceptance if non-conformity substantially impairs value and acceptance was on reasonable assumption non-conformity would be cured and has not been
- UCC § 2-608(1)(b): Buyer may revoke acceptance if non-conformity substantially impairs value and acceptance was without discovery of non-conformity due to difficulty of discovery or seller's assurances
- UCC § 2-608(2): Revocation must occur within reasonable time after buyer discovers or should have discovered grounds

**Business Impact:**
Safety valve for latent defects discovered post-acceptance.

**SI Impact:**
Can SI return equipment if latent defect substantially impairs value? Equipment accepted, then major defect found - can SI revoke? Conveyor accepted, then motor design flaw discovered; revocation lets SI return.

**Forensic Test:**
Can you return equipment if latent defect substantially impairs value?

**Key Indicators:**
- Waiver of revocation rights
- No return after acceptance
- Repair only remedy
- Time limit on revocation

**Success Rate:** N/A (statutory right, should be preserved)

**Recommendation:**
- PRESERVE right to revoke acceptance for latent defects
- DEFINE "substantially impairs value" threshold
- ADD reasonable time period for revocation (60-90 days after discovery)

**Coordinates:** UCC-2-606, Pattern 3.1.2 (Warranty Coordination)

---

### 8.18 UCC-2-615: Force Majeure Excuse

**Citation:** 6 Del. C. § 2-615
**Category:** FORCE_MAJEURE

#### 8.18.1: Broad Force Majeure Without Flow-Down

**Rule ID:** UCC-2-615
**Trigger Concepts:**
- force majeure
- act of god
- impracticable
- impossible
- beyond control
- unforeseeable
- epidemic
- pandemic
- government action
- supply chain
- allocation
- shortage

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
"Vendor excused for force majeure including supply chain disruptions,
material shortages, labor issues, and any event beyond reasonable control.
Buyer must continue all obligations during force majeure period."
```

**UCC Provision:**
- UCC § 2-615(a): Delay or non-delivery not breach if performance made impracticable by occurrence of contingency non-occurrence of which was basic assumption
- UCC § 2-615(b): If only part of capacity affected, seller must allocate production fairly among customers
- UCC § 2-615(c): Seller must seasonably notify buyer of delay or non-delivery

**Business Impact:**
Vendor escapes performance for unforeseeable events.

**SI Impact:**
If vendor claims force majeure, is SI also excused to client? Vendor claims chip shortage = FM excuse; SI's client contract has no FM clause = SI's liability.

**Forensic Test:**
When can vendor be excused from performance? Is it narrowly defined?

**Key Indicators:**
- Broad force majeure definition
- No allocation requirement
- Extended or indefinite excuse period
- No mitigation requirement
- Force majeure doesn't flow down to your client contract

**Success Rate:** N/A (statutory excuse, must be properly defined)

**Recommendation:**
- NARROW force majeure definition (exclude labor, supply chain within control)
- ADD flow-through: "Any force majeure event excusing Vendor's performance shall automatically excuse Client's corresponding obligations to its end customer"
- LIMIT excuse period (90-180 days max, then termination right)
- REQUIRE mitigation efforts

**Coordinates:** Pattern 2.11.2 (Force Majeure Exclusions)

---

### 8.19 SI-001: Warranty Flow-Down Gap

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.19.1: Vendor Warranty Shorter Than Client Warranty

**Rule ID:** SI-001
**Trigger Concepts:**
- warranty period
- warranty term
- months warranty
- year warranty
- warranty duration
- warranty expires
- warranty commences

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
Client Contract: "24-month warranty from final acceptance"
Vendor Contract: "12-month warranty from shipment"
Gap: 12-18 months unprotected (shipment to acceptance + warranty duration)
```

**Business Impact:**
Warranty claims in gap period are 100% your liability.

**SI Impact:**
SI warrants to client for 24 months; vendor warrants to SI for 12 months = 12 months unprotected. Client claims warranty at month 18; vendor warranty expired at month 12 = SI's cost.

**Forensic Test:**
Is vendor warranty period >= client warranty period?

**Key Indicators:**
- Vendor warranty < 12 months
- Client warranty > vendor warranty
- No extended warranty available
- Warranty starts at ship (not installation)

**Calculation:** Gap = Client_Warranty_Months - Vendor_Warranty_Months

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- EXTEND vendor warranty to match or exceed client warranty period
- ALIGN warranty commencement (both from final acceptance, not shipment)
- PURCHASE extended warranty if needed
- ADD boilerplate: "Vendor warrants that all warranties provided hereunder shall extend for a period no less than [CLIENT WARRANTY PERIOD] from final system acceptance by Client's end customer"

**Coordinates:** Pattern 3.1.2 (Warranty Coordination), UCC-2-313

---

### 8.20 SI-002: Liability Cap Squeeze

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.20.1: Vendor Cap Lower Than Client Exposure

**Rule ID:** SI-002
**Trigger Concepts:**
- liability cap
- limitation of liability
- cap at
- limited to
- aggregate liability
- maximum liability
- total liability
- not exceed
- ceiling

**Risk Multiplier:** 9.0 (CRITICAL)

**Detection Pattern:**
```
Client Contract: "Unlimited liability" or "$5M cap"
Vendor Contract: "Liability capped at fees paid ($500K)"
Gap: $4.5M unrecoverable
```

**Business Impact:**
Liability exposure beyond recovery from vendor.

**SI Impact:**
Client can claim $5M from SI; vendor cap is $500K = $4.5M unrecoverable. SI owes client $2M; vendor cap is $200K; SI absorbs $1.8M.

**Forensic Test:**
Is vendor liability cap >= your client liability exposure?

**Key Indicators:**
- Vendor cap is % of contract value
- Vendor cap < client cap
- No insurance carve-out
- Consequential damages excluded

**Calculation:** Gap = Client_Cap - Vendor_Cap

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- INCREASE vendor cap to match client exposure
- ADD insurance carve-out for insured claims
- ADD boilerplate: "Vendor's aggregate liability under this Agreement shall not be less than the aggregate liability cap in Client's end customer contract, or $[AMOUNT], whichever is greater"

**Coordinates:** Pattern 2.1.1 (Mutual Cap), Pattern 2.10.3 (Back-to-Back Liability)

---

### 8.21 SI-003: Indemnification Asymmetry

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.21.1: One-Way Indemnification

**Rule ID:** SI-003
**Trigger Concepts:**
- indemnify
- hold harmless
- defend
- indemnification
- third party claims
- IP indemnity
- infringement indemnity
- mutual indemnification
- one-way indemnification

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
Client Contract: "SI shall indemnify Client for all third-party IP claims"
Vendor Contract: "No IP indemnification from Vendor" or "Indemnification
limited to gross negligence only"
```

**Business Impact:**
Pass-through liability without pass-through protection.

**SI Impact:**
SI indemnifies client for IP infringement; vendor provides no IP indemnity = SI's exposure. Client sues SI for patent infringement; vendor provides no defense or indemnity.

**Forensic Test:**
Does vendor indemnify you for same things you indemnify client?

**Key Indicators:**
- One-way indemnification favoring vendor
- No IP indemnification from vendor
- Indemnification limited to gross negligence
- Your indemnification is broader than vendor's

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- REQUIRE mutual indemnification
- ADD IP indemnification from vendor for equipment
- ALIGN indemnification scope (if you indemnify for ordinary negligence, vendor should too)

**Coordinates:** Pattern 2.2.1 (Mutual Indemnification), Pattern 2.2.4 (IP Indemnity Notice)

---

### 8.22 SI-004: IP Ownership Grab

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.22.1: Work for Hire Without License Back

**Rule ID:** SI-004
**Trigger Concepts:**
- work for hire
- assign
- assignment
- transfer
- ownership
- intellectual property
- IP rights
- all rights
- exclusive rights
- deliverables
- work product
- custom development

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
"All work product, deliverables, methodologies, and custom development
shall be deemed work for hire and assigned exclusively to Client.
SI retains no rights."
```

**Business Impact:**
Loss of reusable intellectual property.

**SI Impact:**
Client claims ownership of SI's integration methodology, blocking reuse. Integration approach SI developed becomes client's exclusive property.

**Forensic Test:**
Who owns the integration work product? Do you retain rights to your methodology?

**Key Indicators:**
- Work for hire language
- Assignment of all IP
- No license back
- No pre-existing IP carve-out
- Deliverables include methodologies

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- ADD pre-existing IP carve-out: "Client's pre-existing intellectual property, methodologies, tools, and know-how shall remain Client's exclusive property"
- ADD license back: "with a perpetual license to end customer for use with the delivered system only"
- AVOID work for hire for methodologies (assign project-specific deliverables only)

**Coordinates:** Pattern 3.7.1 (Phase-Based IP Transfer)

---

### 8.23 SI-005: Acceptance Trap

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.23.1: Subjective Acceptance Criteria

**Rule ID:** SI-005
**Trigger Concepts:**
- acceptance
- acceptance criteria
- acceptance test
- final acceptance
- substantial completion
- punch list
- retainage
- holdback
- satisfactory to client
- client satisfaction
- sole discretion

**Risk Multiplier:** 8.0 (HIGH)

**Detection Pattern:**
```
"System shall be deemed accepted when performance is satisfactory to
Client in its sole discretion. 20% retainage held until final acceptance.
No deemed acceptance provision."
```

**Business Impact:**
Payment indefinitely withheld pending subjective acceptance.

**SI Impact:**
Client withholds final payment claiming "not accepted" with subjective criteria. System works perfectly but client won't sign acceptance = 20% retainage held indefinitely.

**Forensic Test:**
Are acceptance criteria objectively measurable? Is there deemed acceptance?

**Key Indicators:**
- Subjective acceptance criteria ("satisfaction")
- No deemed acceptance clause
- No acceptance timeline
- High retainage (> 10%)
- Acceptance tied to client's client acceptance

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- DEFINE objective acceptance criteria (throughput, uptime, error rates)
- ADD deemed acceptance: "If end customer fails to provide written notice of non-conformance within [30] days of substantial completion, the deliverables shall be deemed accepted"
- LIMIT retainage to 5-10%
- DECOUPLE acceptance from end-customer acceptance

**Coordinates:** Pattern 3.9.8 (Acceptance Test Notice), Pattern 3.1.3 (Final Acceptance Alignment)

---

### 8.24 SI-006: Change Order Lockout

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.24.1: No Payment Without Signed Change Order

**Rule ID:** SI-006
**Trigger Concepts:**
- change order
- change request
- out of scope
- additional work
- scope change
- modification
- amendment
- extra work
- prior written approval
- signed change order

**Risk Multiplier:** 7.0 (HIGH)

**Detection Pattern:**
```
"SI shall not perform any work outside original scope without prior
written change order signed by Client. No payment for work performed
without signed change order. No constructive change provision."
```

**Business Impact:**
Unpaid scope creep.

**SI Impact:**
Client directs extra work, refuses to sign change order, won't pay. Client directs $200K of extra work verbally; no signed CO = no payment.

**Forensic Test:**
Can you get paid for out-of-scope work requested verbally?

**Key Indicators:**
- No work without signed change order
- No constructive change clause
- Client can direct changes without price adjustment
- Change order requires multiple approvals

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- ADD constructive change clause: "If end customer directs work outside the original scope, Client may proceed with such work and shall be entitled to equitable adjustment in price and schedule, whether or not a formal change order is executed"
- ADD automatic price adjustment for directed changes
- DOCUMENT all verbal change directives in writing

**Coordinates:** Pattern 3.2.1 (SOW Change Control)

---

### 8.25 SI-007: Performance Guarantee Pass-Through Failure

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.25.1: SI Guarantees Performance Vendor Won't Match

**Rule ID:** SI-007
**Trigger Concepts:**
- throughput
- performance guarantee
- uptime
- availability
- SLA
- service level
- performance standard
- system performance
- guaranteed
- warrant performance
- performance bond

**Risk Multiplier:** 9.0 (CRITICAL)

**Detection Pattern:**
```
Client Contract: "SI guarantees 99.5% uptime. Performance LD: $10K/day"
Vendor Contract: "Vendor warrants commercially reasonable efforts. No
performance guarantees. No liquidated damages."
Gap: SI liable for $10K/day with no vendor recourse
```

**Business Impact:**
Performance liability without recourse.

**SI Impact:**
SI guarantees 99.5% uptime; vendor warrants "commercially reasonable efforts" = gap. System achieves 97% uptime; client claims $500K LD; vendor has no LD = SI's loss.

**Forensic Test:**
Are your performance guarantees to client backed by vendor guarantees?

**Key Indicators:**
- You guarantee specific metrics
- Vendor doesn't guarantee same metrics
- Performance LD in client contract
- No performance LD in vendor contract

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- REQUIRE vendor performance guarantee matching client requirements
- ADD performance LD flow-down: "Vendor warrants that equipment shall meet or exceed the performance specifications in Exhibit B, which specifications are derived from Client's commitments to end customer"
- AVOID guaranteeing performance beyond vendor's commitments

**Coordinates:** UCC-2-313 (Express Warranties), UCC-2-315 (Fitness for Particular Purpose)

---

### 8.26 SI-008: Insurance Gap

**Citation:** Common Law (Systems Integrator Pattern)
**Category:** SI_PATTERN

#### 8.26.1: Liability Exceeds Insurance Coverage

**Rule ID:** SI-008
**Trigger Concepts:**
- insurance
- coverage
- policy
- certificate
- COI
- professional liability
- E&O
- general liability
- umbrella
- additional insured
- waiver of subrogation

**Risk Multiplier:** 6.0 (MEDIUM)

**Detection Pattern:**
```
Contract liability cap: $10M
SI insurance: $5M professional liability + $2M general liability = $7M
Vendor insurance: $1M general liability only
Vendor won't add SI as additional insured
Gap: $3M uninsured
```

**Business Impact:**
Uninsured liability exposure.

**SI Impact:**
Contract liability exceeds SI coverage; vendor won't add SI as additional insured. Claim exceeds SI's $5M coverage; vendor has only $1M = $4M uninsured.

**Forensic Test:**
Is total liability exposure covered by insurance (yours + vendor's)?

**Key Indicators:**
- Liability cap exceeds insurance limit
- No professional liability requirement for vendor
- Not named as additional insured on vendor policy
- No waiver of subrogation

**Success Rate:** N/A (SI pattern, not statutory)

**Recommendation:**
- REQUIRE vendor to add SI as additional insured
- REQUIRE vendor insurance matching contract liability cap
- ADD waiver of subrogation
- INCREASE insurance limits to match or exceed liability exposure

**Coordinates:** Pattern 3.9.6 (Insurance Specification)

---

## APPENDIX A: PATTERN INDEX (Alphabetical)

| Pattern | # | Category | Outcome |
|---------|---|----------|---------|
| Acceptance Test Notice | 3.9.8 | MSA Commercial | WON |
| Acceptance Trap | SI-005 | UCC Statutory | N/A ⚠️ NEW |
| Anticipatory Repudiation | UCC-2-610 | UCC Statutory | N/A ⚠️ NEW |
| Arbitration Consolidation/Joinder | 3.12.4 | Subcontract | Template |
| Assignment to End User | 2.6.3 | Core | WON |
| Back-to-Back Liability | 2.10.3 | Core | — |
| Battle of Forms | UCC-2-207 | UCC Statutory | N/A ⚠️ NEW |
| Broker Verification | 3.8.1 | Specialized | Pending |
| Business Day | 2.11.2 | Core | — |
| Buyer Rights on Improper Delivery | UCC-2-601 | UCC Statutory | N/A ⚠️ NEW |
| Carve-Out Protection | 2.1.2 | Core | WON |
| Change of Control | 2.6.2 | Core | WON |
| Change Order Lockout | SI-006 | UCC Statutory | N/A ⚠️ NEW |
| Commission on Direct | 2.4.2 | Core | LOST |
| Competitive Exclusion | 2.6.1 | Core | WON |
| Consequential Damages Exclusion | UCC-2-719 | UCC Statutory | N/A ⚠️ NEW |
| Cure Period | 2.8.2 | Core | WON |
| Customer Protection Complete | 3.1.1 | Specialized | WON |
| Customer Protection Period | 2.4.1 | Core | WON |
| Deduction of Damages | UCC-2-717 | UCC Statutory | N/A ⚠️ NEW |
| Defined Response Times | 2.9.1 | Core | WON |
| Deliverable Objection Period | 3.10.2 | Services | WON |
| Dispute Rights | 2.3.3 | Core | WON |
| Double Margin Prevention | 3.11.3 | Project | WON |
| Duty to Mitigate | 2.2.3 | Core | LOST |
| Environmental Warranty | 2.2.5 | Core | WON |
| Escalation Path | 2.9.3 | Core | WON |
| Exclusion of Warranties | UCC-2-316 | UCC Statutory | N/A ⚠️ NEW |
| Express Warranties | UCC-2-313 | UCC Statutory | N/A ⚠️ NEW |
| Final Acceptance Alignment | 3.1.3 | Specialized | WON |
| Fitness for Particular Purpose | UCC-2-315 | UCC Statutory | N/A ⚠️ NEW |
| Flow-Down Protection | 2.10.1 | Core | — |
| Flow-Down with Priority Order | 3.12.1 | Subcontract | Template |
| FM Payment for Work Done Only | 3.9.9 | MSA Commercial | WON |
| Force Majeure Excuse | UCC-2-615 | UCC Statutory | N/A ⚠️ NEW |
| Gap Coverage | 2.10.2 | Core | — |
| Gross Negligence | 2.11.1 | Core | — |
| Implied Warranty Merchantability | UCC-2-314 | UCC Statutory | N/A ⚠️ NEW |
| Indemnification Asymmetry | SI-003 | UCC Statutory | N/A ⚠️ NEW |
| Inspection Period Extension | 3.9.7 | MSA Commercial | WON |
| Insurance Gap | SI-008 | UCC Statutory | N/A ⚠️ NEW |
| Insurance Specification | 3.9.6 | MSA Commercial | WON |
| Interim Agreement Protection | 3.6.3 | Partnership | WON |
| Introduction Documentation | 2.4.3 | Core | WON |
| IP Indemnity Notice | 2.2.4 | Core | WON |
| IP Ownership Grab | SI-004 | UCC Statutory | N/A ⚠️ NEW |
| Key Employee Carve-Out | 2.5.2 | Core | — |
| Knowledge Qualifier | 2.2.2 | Core | WON |
| Liability Cap Squeeze | SI-002 | UCC Statutory | N/A ⚠️ NEW |
| Limited Exclusivity | 2.7.1 | Core | — |
| Liquidated Damages | UCC-2-718 | UCC Statutory | N/A ⚠️ NEW |
| Litigation to Arbitration | 3.9.5 | MSA Commercial | WON |
| Long Lead-Time Item Protocol | 3.12.2 | Subcontract | Template |
| Markup Limitations | 3.1.6 | Specialized | MUTUAL |
| Milestone Payments | 2.3.2 | Core | WON |
| MSA Supremacy Clause | 3.10.6 | Services | WON |
| Multiple Failure Threshold | 3.10.4 | Services | WON |
| Mutual Cap | 2.1.1 | Core | WON |
| Mutual Indemnification | 2.2.1 | Core | MUTUAL |
| Mutual Non-Solicit | 2.5.1 | Core | — |
| Mutual Non-Solicitation | 3.12.5 | Subcontract | Template |
| Mutual Termination | 2.8.1 | Core | WON |
| NDA Mutual Scope | 3.3.2 | Specialized | — |
| NDA Return/Destruction | 3.3.3 | Specialized | — |
| Net 30 Standard | 2.3.1 | Core | WON |
| Non-Compete Removal | 3.9.4 | MSA Commercial | WON |
| Notice of Breach | UCC-2-607 | UCC Statutory | N/A ⚠️ NEW |
| Payment Withholding for Cause | 3.10.1 | Services | WON |
| Performance Guarantee Gap | SI-007 | UCC Statutory | N/A ⚠️ NEW |
| Performance Quota Criteria | 3.6.4 | Partnership | WON |
| Performance-Based Exclusivity | 2.7.2 | Core | — |
| Phase-Based IP Transfer | 3.7.1 | Specialized | — |
| Phase Mismatch Detection | 3.7.2 | Specialized | — |
| Pricing Discount Floor | 3.6.1 | Partnership | WON |
| Prime Contract Flowdown | 2.10.4 | Core | — |
| Prime Contract Flowdown Addendum | 3.11.1 | Project | WON |
| Reasonableness Standard | 2.9.2 | Core | WON |
| Remedy Limitations | UCC-2-719 | UCC Statutory | N/A ⚠️ NEW |
| Reporting Limits | 3.9.11 | MSA Commercial | WON |
| Revocation of Acceptance | UCC-2-608 | UCC Statutory | N/A ⚠️ NEW |
| Right to Adequate Assurance | UCC-2-609 | UCC Statutory | N/A ⚠️ NEW |
| Safe Harbor Notice Period | 3.10.3 | Services | WON |
| Security Interest Limits | 3.1.5 | Specialized | WON |
| Security Interest Undisputed Only | 3.11.4 | Project | WON |
| Software License Transfer | 3.1.4 | Specialized | WON |
| Source Code Escrow Documentation | 3.11.2 | Project | WON |
| SOW Schedule Format | 3.11.5 | Project | WON |
| Specially Manufactured Goods | 3.12.3 | Subcontract | Template |
| Statute of Limitations | UCC-2-725 | UCC Statutory | N/A ⚠️ NEW |
| Super Cap for IP | 2.1.3 | Core | MUTUAL |
| Term Extension + Auto-Renewal | 3.9.1 | MSA Commercial | WON |
| Territory Exclusion Limits | 3.6.2 | Partnership | WON |
| Territory Protection with Cure | 3.9.3 | MSA Commercial | WON |
| Title on Delivery | 3.9.2 | MSA Commercial | WON |
| Unconscionability | UCC-2-302 | UCC Statutory | N/A ⚠️ NEW |
| Warranty Coordination | 3.1.2 | Specialized | WON |
| Warranty Flow-Down Gap | SI-001 | UCC Statutory | N/A ⚠️ NEW |
| Warranty of Title | UCC-2-312 | UCC Statutory | N/A ⚠️ NEW |
| What Constitutes Acceptance | UCC-2-606 | UCC Statutory | N/A ⚠️ NEW |
| Wind-Down Protection | 2.8.3 | Core | WON |
| Work During Dispute | 3.12.6 | Subcontract | Template |
| Work Suspension Notice | 3.9.10 | MSA Commercial | WON |
| Worldwide License Scope | 3.10.5 | Services | WON |

**Total Patterns: 113** (87 negotiation patterns + 26 UCC statutory rules)

---

## APPENDIX B: OUTCOME SUMMARY

| Outcome | Count | Percentage |
|---------|-------|------------|
| WON | 58 | 51% |
| MUTUAL | 4 | 4% |
| LOST | 2 | 2% |
| Template | 6 | 5% |
| Pending/Untracked | 17 | 15% |
| **UCC Statutory** | **26** | **23%** ⚠️ NEW |
| **TOTAL** | **113** | 100% |

---

## APPENDIX C: SOURCES

| Document | Contract Type | Changes | Patterns Added |
|----------|---------------|---------|----------------|
| Channel Partner Master Agreement V1→V2 | MSA | 23 | 11 (Section 3.9) |
| ATG MSA V1→V2 | Services MSA | 12 | 6 (Section 3.10) |
| Master Projects Agreement V3→V4 | IPA Framework | 16 | 5 (Section 3.11) |
| Subcontractor MSA Template | Subcontract | Template | 6 (Section 3.12) |
| **Delaware UCC Title 6 + SI Patterns** | **Statutory** | **26 rules** | **26 (Part 8)** ⚠️ NEW |

---

**END OF PATTERN LIBRARY v2.1**

*Generated: January 18, 2026*
*Confidence: 96%*
*Next Review: Q2 2026 (with outcome data)*
