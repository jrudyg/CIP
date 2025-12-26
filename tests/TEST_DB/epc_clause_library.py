"""
EPC/Construction Contract Clause Library
Comprehensive clause text for 18 categories with 4 risk variations each.
Used to populate realistic test data for CIP Contract Intelligence Platform.
"""

# =============================================================================
# EPC CLAUSE LIBRARY - 18 Categories x 4 Variations = 72 Clause Templates
# =============================================================================

EPC_CLAUSE_LIBRARY = {
    # =========================================================================
    # 1. PAYMENT TERMS
    # =========================================================================
    "payment": {
        "favorable": {
            "title": "Payment Terms",
            "text": """PAYMENT. Owner shall pay Contractor within thirty (30) days of receipt of
Contractor's invoice for Work performed during the preceding month. Invoices shall be
submitted monthly based on percentage of completion. No retention shall be withheld.
Interest shall accrue on late payments at the rate of 1.5% per month. Contractor may
suspend Work upon fifteen (15) days' notice if payment is not received within sixty
(60) days of invoice date.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-PAY-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Payment Terms",
            "text": """PAYMENT. Owner shall pay Contractor within forty-five (45) days of receipt
of a properly submitted invoice. Contractor shall submit monthly progress invoices
supported by lien waivers from subcontractors. Owner shall retain ten percent (10%)
of each progress payment until Substantial Completion, at which time fifty percent
(50%) of retention shall be released. Final retention shall be released upon Final
Completion and submission of all close-out documents.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-PAY-BAL-001",
            "finding": "Standard payment terms with reasonable retention schedule",
            "recommendation": "Acceptable - verify close-out document requirements are achievable"
        },
        "unfavorable": {
            "title": "Payment Terms",
            "text": """PAYMENT. Owner shall pay Contractor within sixty (60) days after approval
of invoice by Owner and Architect. Owner may withhold payment for any reason in its
sole discretion. Ten percent (10%) retention shall be withheld until one (1) year
after Final Completion. No interest shall accrue on late payments. Pay-when-paid:
Contractor's right to payment from Owner is contingent upon Owner's receipt of
payment from its funding source.""",
            "risk_level": "CRITICAL",
            "pattern_id": "PAT-PAY-UNFAV-001",
            "finding": "Pay-when-paid clause shifts funding risk; extended retention period",
            "recommendation": "Negotiate pay-if-paid deletion; reduce retention period to 30 days after completion",
            "redline": {
                "current_text": "Pay-when-paid: Contractor's right to payment from Owner is contingent upon Owner's receipt of payment from its funding source.",
                "suggested_text": "Owner shall make payment to Contractor regardless of Owner's receipt of funds from any third party. Owner's obligation to pay is unconditional.",
                "rationale": "Pay-when-paid provisions create unacceptable cash flow risk and may be unenforceable",
                "success_probability": 0.65,
                "leverage_context": "Reference project financing status; offer payment bond as alternative security"
            }
        },
        "dealbreaker": {
            "title": "Payment Terms",
            "text": """PAYMENT. Owner may pay Contractor at Owner's sole discretion when and if
Owner determines the Work merits payment. No invoice shall be due until Owner's
lender approves the Work. Contractor waives all mechanic's lien rights. Owner may
offset any amounts owed to Contractor against any claims Owner may have against
Contractor on this or any other project. Contractor shall have no right to suspend
Work for non-payment.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-PAY-DEAL-001",
            "finding": "Waiver of lien rights and discretionary payment - unacceptable risk",
            "recommendation": "Cannot proceed - lien waiver eliminates primary security; no work without payment terms",
            "escalation": "CEO/Legal review required"
        }
    },

    # =========================================================================
    # 2. LIQUIDATED DAMAGES
    # =========================================================================
    "liquidated_damages": {
        "favorable": {
            "title": "Liquidated Damages",
            "text": """LIQUIDATED DAMAGES. In the event Contractor fails to achieve Substantial
Completion by the Scheduled Completion Date, as such date may be extended pursuant
to this Agreement, Contractor shall pay Owner liquidated damages in the amount of
Five Thousand Dollars ($5,000) per calendar day, not to exceed five percent (5%) of
the Contract Price in the aggregate. Such liquidated damages shall be Owner's sole
and exclusive remedy for delay and Contractor's sole liability therefor. No
liquidated damages shall be assessed for delays caused by Owner, Force Majeure,
or changes to the Work.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-LD-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Liquidated Damages",
            "text": """LIQUIDATED DAMAGES. Contractor shall pay liquidated damages of Ten
Thousand Dollars ($10,000) per calendar day for each day Substantial Completion
is delayed beyond the Scheduled Completion Date, capped at ten percent (10%) of
the Contract Price in the aggregate. Time extensions shall be granted for
Owner-caused delays, Force Majeure events, and changes to the Work that impact
the critical path. Contractor shall provide written notice of delay within
fourteen (14) days of the delay event.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-LD-BAL-001",
            "finding": "Standard LD provision with reasonable cap and extension rights",
            "recommendation": "Acceptable - ensure force majeure definition is adequate"
        },
        "unfavorable": {
            "title": "Liquidated Damages",
            "text": """LIQUIDATED DAMAGES. Contractor shall pay liquidated damages of Twenty-Five
Thousand Dollars ($25,000) per calendar day for each day of delay beyond the
Scheduled Completion Date, with no aggregate cap. No time extensions shall be
granted except for changes directed in writing by Owner. Liquidated damages shall
not be Owner's exclusive remedy and Owner reserves all other remedies at law and
in equity, including actual damages to the extent they exceed liquidated damages.
Contractor shall pay liquidated damages regardless of the cause of delay.""",
            "risk_level": "CRITICAL",
            "pattern_id": "PAT-LD-UNFAV-001",
            "finding": "Uncapped LDs with no delay relief creates unlimited exposure",
            "recommendation": "Negotiate 10% aggregate cap and excusable delay provisions",
            "redline": {
                "current_text": "Contractor shall pay liquidated damages of Twenty-Five Thousand Dollars ($25,000) per calendar day for each day of delay beyond the Scheduled Completion Date, with no aggregate cap.",
                "suggested_text": "Contractor shall pay liquidated damages of Fifteen Thousand Dollars ($15,000) per calendar day for each day of delay beyond the Scheduled Completion Date, not to exceed ten percent (10%) of the Contract Price in the aggregate.",
                "rationale": "Uncapped LDs create unlimited financial exposure inconsistent with project margin",
                "success_probability": 0.75,
                "leverage_context": "Schedule is critical to Owner - offer accelerated milestone in exchange for cap"
            }
        },
        "dealbreaker": {
            "title": "Liquidated Damages and Consequential Damages",
            "text": """LIQUIDATED DAMAGES AND ACTUAL DAMAGES. Contractor shall pay liquidated
damages of Fifty Thousand Dollars ($50,000) per calendar day plus all actual,
consequential, indirect, incidental, and special damages including but not limited
to lost profits, lost revenue, lost business opportunity, damage to reputation,
and loss of use of the facility. No limitation of liability shall apply to delay
damages. Contractor's obligation to pay damages shall survive termination.
Contractor waives any defense based on lack of foreseeability.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-LD-DEAL-001",
            "finding": "Consequential damages on top of LDs - catastrophic risk exposure",
            "recommendation": "Must delete consequential damages language or walk from deal",
            "escalation": "CEO/Legal review required before proceeding"
        }
    },

    # =========================================================================
    # 3. CHANGE ORDERS
    # =========================================================================
    "change_orders": {
        "favorable": {
            "title": "Changes to the Work",
            "text": """CHANGES. Owner may request changes to the Work by written Change Order.
Within ten (10) business days of receipt, Contractor shall submit a detailed
proposal including cost impact (using agreed-upon labor rates and markup) and
schedule impact. No Change Order shall be effective until signed by both parties.
Contractor shall not perform changed work without an executed Change Order.
Disputed Change Orders shall be resolved per the Disputes clause, and Contractor
shall be paid on a time and materials basis pending resolution.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-CO-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Changes to the Work",
            "text": """CHANGES. Owner may direct changes to the Work by written Change Order.
Contractor shall submit a change proposal within fourteen (14) days including
detailed cost breakdown and schedule impact. If parties cannot agree on price or
time, Owner may direct Contractor to proceed and the change shall be valued using
unit prices in the Contract or, if not applicable, actual cost plus fifteen
percent (15%) markup for overhead and profit. Contractor shall maintain detailed
time and material records for disputed changes.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-CO-BAL-001",
            "finding": "Standard change order process with defined pricing methodology",
            "recommendation": "Verify unit prices are adequate; confirm 15% markup is acceptable"
        },
        "unfavorable": {
            "title": "Changes to the Work",
            "text": """CHANGES. Owner may direct changes to the Work at any time without
Contractor's consent. Contractor shall proceed immediately with changed work upon
Owner's written or verbal direction. If parties cannot agree on price adjustment,
Owner shall determine a fair value and such determination shall be final. No time
extension shall be granted for changes unless Contractor demonstrates critical
path impact. Contractor's markup on changes shall not exceed ten percent (10%)
total for overhead and profit.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-CO-UNFAV-001",
            "finding": "Owner-determined pricing and limited time extension rights",
            "recommendation": "Negotiate mutual pricing agreement; add ADR for pricing disputes",
            "redline": {
                "current_text": "If parties cannot agree on price adjustment, Owner shall determine a fair value and such determination shall be final.",
                "suggested_text": "If parties cannot agree on price adjustment within thirty (30) days, the dispute shall be resolved pursuant to the Disputes provision of this Agreement.",
                "rationale": "Unilateral pricing determination removes Contractor recourse",
                "success_probability": 0.80,
                "leverage_context": "Industry standard requires mutual agreement or neutral dispute resolution"
            }
        },
        "dealbreaker": {
            "title": "Changes to the Work",
            "text": """CHANGES. Owner may make unlimited changes to the Work scope, sequence,
and schedule at no additional cost to Owner. Contractor's bid includes all
necessary contingency for changes. No Change Order shall result in any increase
to the Contract Price or extension to the Contract Time. Contractor waives any
claim for additional compensation or time arising from changes directed by Owner,
conditions encountered, or any other cause whatsoever.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-CO-DEAL-001",
            "finding": "Waiver of all change order rights - unlimited scope risk",
            "recommendation": "Cannot proceed - must have right to compensation for scope changes",
            "escalation": "Legal review required - cardinal change doctrine may apply"
        }
    },

    # =========================================================================
    # 4. FLOWDOWN PROVISIONS
    # =========================================================================
    "flowdown": {
        "favorable": {
            "title": "Prime Contract Flowdown",
            "text": """FLOWDOWN. The terms of the Prime Contract applicable to Subcontractor's
scope of Work are incorporated herein by reference, except for: (a) pricing and
payment terms, (b) schedule milestones not applicable to Subcontractor, (c) bond
requirements, (d) insurance limits in excess of those required herein, and (e) any
terms inconsistent with or more onerous than this Subcontract. In the event of
conflict between this Subcontract and the Prime Contract, this Subcontract shall
govern. A copy of relevant Prime Contract excerpts has been provided to
Subcontractor.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-FD-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Prime Contract Flowdown",
            "text": """FLOWDOWN. The terms of the Prime Contract are incorporated herein to the
extent applicable to Subcontractor's Work. Subcontractor shall comply with all
requirements flowing down from the Prime Contract. Contractor shall provide
Subcontractor with relevant excerpts of the Prime Contract upon request. In the
event of conflict, the more stringent requirement shall apply. Subcontractor
acknowledges it has had opportunity to review Prime Contract provisions.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-FD-BAL-001",
            "finding": "Standard flowdown with 'more stringent' conflict resolution",
            "recommendation": "Request Prime Contract excerpts before execution"
        },
        "unfavorable": {
            "title": "Prime Contract Flowdown",
            "text": """FLOWDOWN. All terms, conditions, obligations, and requirements of the
Prime Contract between Contractor and Owner are incorporated herein and shall
flow down to Subcontractor with full force and effect. Subcontractor shall be
bound by and comply with all obligations of Contractor under the Prime Contract
as if Subcontractor were a direct party thereto. Subcontractor assumes all risks
associated with Prime Contract terms whether or not disclosed to Subcontractor.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-FD-UNFAV-001",
            "finding": "Blind flowdown without visibility to Prime Contract terms",
            "recommendation": "Request copy of Prime Contract; negotiate specific carve-outs",
            "redline": {
                "current_text": "All terms, conditions, obligations, and requirements of the Prime Contract between Contractor and Owner are incorporated herein and shall flow down to Subcontractor with full force and effect.",
                "suggested_text": "The terms of the Prime Contract applicable to Subcontractor's scope of Work are incorporated herein by reference, a complete copy of which has been provided to and reviewed by Subcontractor prior to execution of this Subcontract.",
                "rationale": "Cannot accept unknown obligations; must have visibility to Prime Contract terms",
                "success_probability": 0.85,
                "leverage_context": "Standard industry practice to provide Prime Contract excerpts"
            }
        },
        "dealbreaker": {
            "title": "Prime Contract Flowdown",
            "text": """FLOWDOWN. Subcontractor shall be bound by all terms of the Prime Contract
regardless of whether such terms are disclosed, exist now, or are added in the
future through amendments. Any amendment to the Prime Contract shall automatically
amend this Subcontract. Subcontractor's price is fixed regardless of Prime Contract
flowdown requirements. Subcontractor waives any claim arising from Prime Contract
terms not specifically identified herein.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-FD-DEAL-001",
            "finding": "Future amendment incorporation without consent - unlimited risk",
            "recommendation": "Cannot proceed - cannot be bound by unknown future amendments",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 5. INDEMNIFICATION
    # =========================================================================
    "indemnification": {
        "favorable": {
            "title": "Indemnification",
            "text": """INDEMNIFICATION. Each Party shall indemnify, defend, and hold harmless
the other Party from and against any and all claims, damages, losses, and expenses
(including reasonable attorneys' fees) arising out of or resulting from the
indemnifying Party's negligent acts or omissions or willful misconduct, but only
to the extent of such Party's fault. Neither Party shall be required to indemnify
the other for claims arising from the other Party's sole negligence or willful
misconduct.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-IND-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Indemnification",
            "text": """INDEMNIFICATION. Contractor shall indemnify, defend, and hold harmless
Owner and Owner's officers, directors, employees, and agents from and against any
claims, damages, losses, and expenses arising out of or resulting from Contractor's
negligent acts, errors, or omissions in the performance of the Work. Contractor's
indemnification obligation shall not extend to claims arising from Owner's sole
negligence or willful misconduct. This indemnification shall survive completion
or termination of this Agreement.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-IND-BAL-001",
            "finding": "Standard intermediate form indemnification",
            "recommendation": "Acceptable for most projects; verify insurance covers scope"
        },
        "unfavorable": {
            "title": "Indemnification",
            "text": """INDEMNIFICATION. Contractor shall indemnify, defend, and hold harmless
Owner and Owner's officers, directors, employees, agents, affiliates, and
successors from and against ANY AND ALL claims, liabilities, damages, losses,
costs, and expenses (including attorneys' fees and costs of litigation) of
whatsoever nature, arising out of or in any way connected with the Work, the
Contract Documents, or Contractor's presence on the site, REGARDLESS OF CAUSE
and even if caused in whole or in part by the negligence (whether active, passive,
or gross) of Owner.""",
            "risk_level": "CRITICAL",
            "pattern_id": "PAT-IND-UNFAV-001",
            "finding": "Broad form indemnification including Owner's negligence",
            "recommendation": "Negotiate to intermediate form; remove 'regardless of cause' language",
            "redline": {
                "current_text": "REGARDLESS OF CAUSE and even if caused in whole or in part by the negligence (whether active, passive, or gross) of Owner.",
                "suggested_text": "but only to the extent such claims arise from Contractor's negligent acts, errors, or omissions. Contractor shall not be required to indemnify Owner for claims arising from Owner's sole negligence or willful misconduct.",
                "rationale": "Broad form indemnification creates unlimited exposure and may exceed insurance coverage",
                "success_probability": 0.70,
                "leverage_context": "Many states void broad form indemnification in construction contracts"
            }
        },
        "dealbreaker": {
            "title": "Indemnification",
            "text": """INDEMNIFICATION. Contractor shall indemnify and hold harmless Owner from
any and all claims regardless of fault, including claims arising from Owner's sole
negligence, strict liability, or intentional misconduct. Contractor's indemnification
is unlimited and shall include punitive damages. Contractor waives any defense based
on comparative or contributory negligence. Contractor shall maintain defense of all
claims at Contractor's sole expense with counsel selected by Owner.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-IND-DEAL-001",
            "finding": "Indemnification for Owner's intentional misconduct - unenforceable and uninsurable",
            "recommendation": "Must reject - indemnification for intentional acts is against public policy",
            "escalation": "Legal review required - likely unenforceable"
        }
    },

    # =========================================================================
    # 6. LIMITATION OF LIABILITY
    # =========================================================================
    "limitation_of_liability": {
        "favorable": {
            "title": "Limitation of Liability",
            "text": """LIMITATION OF LIABILITY. NOTWITHSTANDING ANY OTHER PROVISION OF THIS
AGREEMENT, NEITHER PARTY SHALL BE LIABLE TO THE OTHER FOR ANY CONSEQUENTIAL,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR PUNITIVE DAMAGES, INCLUDING BUT
NOT LIMITED TO LOSS OF PROFITS, LOSS OF REVENUE, LOSS OF USE, OR LOSS OF
BUSINESS OPPORTUNITY, ARISING OUT OF OR RELATED TO THIS AGREEMENT. THE TOTAL
AGGREGATE LIABILITY OF EITHER PARTY SHALL NOT EXCEED THE FEES PAID OR PAYABLE
UNDER THIS AGREEMENT.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-LOL-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Limitation of Liability",
            "text": """LIMITATION OF LIABILITY. EXCEPT FOR CONTRACTOR'S INDEMNIFICATION
OBLIGATIONS AND LIABILITY FOR GROSS NEGLIGENCE OR WILLFUL MISCONDUCT, NEITHER
PARTY SHALL BE LIABLE FOR CONSEQUENTIAL, INDIRECT, OR SPECIAL DAMAGES.
CONTRACTOR'S TOTAL LIABILITY SHALL NOT EXCEED THE GREATER OF (A) THE CONTRACT
PRICE OR (B) THE AVAILABLE PROCEEDS OF CONTRACTOR'S LIABILITY INSURANCE.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-LOL-BAL-001",
            "finding": "Standard limitation with carve-outs for indemnity and willful misconduct",
            "recommendation": "Verify insurance limits are adequate to cover cap"
        },
        "unfavorable": {
            "title": "Limitation of Liability",
            "text": """LIMITATION OF LIABILITY. CONTRACTOR SHALL BE LIABLE FOR ALL DAMAGES,
WHETHER DIRECT, INDIRECT, CONSEQUENTIAL, INCIDENTAL, OR SPECIAL. NO LIMITATION
OF LIABILITY SHALL APPLY TO CONTRACTOR'S PERFORMANCE UNDER THIS AGREEMENT. OWNER
SHALL NOT BE LIABLE TO CONTRACTOR FOR ANY DAMAGES WHATSOEVER, AND CONTRACTOR
WAIVES ANY RIGHT TO CLAIM DAMAGES AGAINST OWNER.""",
            "risk_level": "CRITICAL",
            "pattern_id": "PAT-LOL-UNFAV-001",
            "finding": "One-sided limitation - Contractor exposed to unlimited liability",
            "recommendation": "Negotiate mutual waiver of consequential damages and aggregate cap",
            "redline": {
                "current_text": "NO LIMITATION OF LIABILITY SHALL APPLY TO CONTRACTOR'S PERFORMANCE UNDER THIS AGREEMENT.",
                "suggested_text": "CONTRACTOR'S TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED TWO HUNDRED PERCENT (200%) OF THE CONTRACT PRICE.",
                "rationale": "Unlimited liability is not insurable and creates existential risk",
                "success_probability": 0.65,
                "leverage_context": "Insurance market requires liability caps; explain underwriting constraints"
            }
        },
        "dealbreaker": {
            "title": "Limitation of Liability",
            "text": """LIMITATION OF LIABILITY. THERE SHALL BE NO LIMITATION ON CONTRACTOR'S
LIABILITY. CONTRACTOR SHALL BE LIABLE FOR ALL DAMAGES INCLUDING CONSEQUENTIAL,
PUNITIVE, EXEMPLARY, AND MULTIPLIED DAMAGES. CONTRACTOR WAIVES ANY STATUTORY
LIMITATION ON LIABILITY. CONTRACTOR'S PRINCIPALS AND SHAREHOLDERS SHALL BE
PERSONALLY LIABLE FOR ALL OBLIGATIONS UNDER THIS AGREEMENT.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-LOL-DEAL-001",
            "finding": "Personal liability of principals - catastrophic corporate veil piercing",
            "recommendation": "Cannot proceed - personal guarantee of corporate obligations is non-starter",
            "escalation": "CEO/Legal review required"
        }
    },

    # =========================================================================
    # 7. WARRANTIES
    # =========================================================================
    "warranties": {
        "favorable": {
            "title": "Warranties",
            "text": """WARRANTIES. Contractor warrants that the Work shall be performed in a
good and workmanlike manner in accordance with the Contract Documents and
applicable codes. Contractor warrants the Work against defects in materials and
workmanship for a period of one (1) year from Substantial Completion. Manufacturer
warranties shall be assigned to Owner. THIS WARRANTY IS IN LIEU OF ALL OTHER
WARRANTIES, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-WAR-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Warranties",
            "text": """WARRANTIES. Contractor warrants that: (a) the Work shall conform to the
Contract Documents; (b) materials shall be new and of good quality; (c) the Work
shall be free from defects in design (to the extent design is Contractor's
responsibility), materials, and workmanship; and (d) the Work shall be fit for its
intended purpose. The warranty period shall be two (2) years from Substantial
Completion. Contractor shall correct defective Work at no cost to Owner.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-WAR-BAL-001",
            "finding": "Standard warranty with 2-year correction period",
            "recommendation": "Acceptable - verify design responsibility is clearly allocated"
        },
        "unfavorable": {
            "title": "Warranties",
            "text": """WARRANTIES. Contractor warrants the Work for a period of five (5) years
from Final Completion. Contractor shall correct any defects at Contractor's sole
cost regardless of cause, including defects arising from Owner's misuse or failure
to maintain. The warranty period shall restart upon completion of any correction.
Owner may perform corrections and back-charge Contractor if Contractor fails to
respond within forty-eight (48) hours of notice.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-WAR-UNFAV-001",
            "finding": "Extended warranty with restart provision creates perpetual obligation",
            "recommendation": "Negotiate 2-year warranty without restart; add Owner maintenance requirement",
            "redline": {
                "current_text": "The warranty period shall restart upon completion of any correction.",
                "suggested_text": "Warranty corrections shall not extend the original warranty period except that corrections shall be warranted for one (1) year from completion of such correction or the balance of the original warranty period, whichever is longer.",
                "rationale": "Warranty restart creates potentially perpetual obligation",
                "success_probability": 0.75,
                "leverage_context": "Industry standard caps warranty correction periods"
            }
        },
        "dealbreaker": {
            "title": "Warranties",
            "text": """WARRANTIES. Contractor warrants the Work in perpetuity. Contractor shall
be liable for any defects discovered at any time regardless of cause, including
defects arising from design provided by Owner or others, natural disasters, or
normal wear and tear. Contractor guarantees the economic performance of the facility
and shall pay Owner for any revenue shortfall. Contractor waives all defenses
including statute of limitations and statute of repose.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-WAR-DEAL-001",
            "finding": "Perpetual warranty and performance guarantee - unlimited duration risk",
            "recommendation": "Cannot proceed - no insurance available for perpetual warranties",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 8. TERMINATION
    # =========================================================================
    "termination": {
        "favorable": {
            "title": "Termination",
            "text": """TERMINATION. Either Party may terminate this Agreement for cause upon
thirty (30) days' written notice if the other Party materially breaches this
Agreement and fails to cure within the notice period. Owner may terminate for
convenience upon thirty (30) days' notice, in which case Contractor shall be paid
for Work performed to date plus reasonable demobilization costs plus five percent
(5%) of the value of unperformed Work as lost profit.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-TRM-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Termination",
            "text": """TERMINATION. Owner may terminate for cause upon fourteen (14) days'
written notice specifying the breach. Contractor shall have fourteen (14) days to
cure or submit a cure plan. Owner may terminate for convenience upon fourteen (14)
days' notice. Upon termination for convenience, Contractor shall be paid for Work
performed, materials procured, and reasonable demobilization costs. No anticipatory
profit shall be paid for unperformed Work.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-TRM-BAL-001",
            "finding": "Standard termination with cure period but no lost profit on convenience termination",
            "recommendation": "Acceptable - may want to negotiate lost profit percentage"
        },
        "unfavorable": {
            "title": "Termination",
            "text": """TERMINATION. Owner may terminate this Agreement at any time for any
reason or no reason upon forty-eight (48) hours' notice. Upon termination,
Contractor shall be paid only for Work accepted by Owner less any amounts Owner
determines are necessary to complete the Work with a replacement contractor. Owner
shall have no liability for lost profit, overhead recovery, or demobilization
costs. Contractor may not terminate for any reason.""",
            "risk_level": "CRITICAL",
            "pattern_id": "PAT-TRM-UNFAV-001",
            "finding": "One-sided termination with no recovery upon convenience termination",
            "recommendation": "Negotiate longer notice period; add demobilization cost recovery",
            "redline": {
                "current_text": "Owner shall have no liability for lost profit, overhead recovery, or demobilization costs.",
                "suggested_text": "Upon termination for convenience, Contractor shall be paid for all Work performed, materials procured, and reasonable demobilization costs.",
                "rationale": "Termination for convenience without demob recovery creates significant financial exposure",
                "success_probability": 0.80,
                "leverage_context": "Mobilization investment requires reasonable termination protection"
            }
        },
        "dealbreaker": {
            "title": "Termination",
            "text": """TERMINATION. Owner may terminate without notice for any reason. Upon
termination, Contractor shall forfeit all amounts owed and shall pay Owner
liquidated termination damages equal to twenty percent (20%) of the Contract Price.
Contractor shall remain liable for all obligations surviving termination including
indemnification and warranties. Contractor waives any claim against Owner arising
from termination.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-TRM-DEAL-001",
            "finding": "Termination damages paid TO Owner - inverts normal risk allocation",
            "recommendation": "Cannot proceed - paying damages upon termination is non-starter",
            "escalation": "CEO review required"
        }
    },

    # =========================================================================
    # 9. INSURANCE
    # =========================================================================
    "insurance": {
        "favorable": {
            "title": "Insurance Requirements",
            "text": """INSURANCE. Contractor shall maintain the following insurance: (a)
Commercial General Liability with limits of $1,000,000 per occurrence/$2,000,000
aggregate; (b) Automobile Liability of $1,000,000 combined single limit; (c)
Workers' Compensation as required by law; (d) Employer's Liability of $500,000.
Owner shall maintain Builder's Risk insurance covering the Work. Contractor shall
name Owner as additional insured on a primary and non-contributory basis for CGL
only.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-INS-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Insurance Requirements",
            "text": """INSURANCE. Contractor shall maintain: (a) CGL $2,000,000 per occurrence/
$4,000,000 aggregate including products/completed operations; (b) Auto $1,000,000;
(c) Workers' Comp statutory; (d) Employer's Liability $1,000,000; (e) Umbrella
$5,000,000. Owner shall be additional insured on CGL and Umbrella. Contractor shall
provide waivers of subrogation on all policies. Contractor shall maintain completed
operations coverage for two (2) years after Final Completion.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-INS-BAL-001",
            "finding": "Standard insurance requirements with completed operations tail",
            "recommendation": "Verify limits are achievable and included in pricing"
        },
        "unfavorable": {
            "title": "Insurance Requirements",
            "text": """INSURANCE. Contractor shall maintain: (a) CGL $5,000,000 per occurrence/
$10,000,000 aggregate; (b) Professional Liability $10,000,000; (c) Contractor's
Pollution Liability $5,000,000; (d) Umbrella $25,000,000. Owner shall be named
insured (not additional insured) on all policies. Contractor shall provide thirty
(30) days' notice of cancellation directly to Owner. Contractor shall maintain
all coverages for ten (10) years after Final Completion at Contractor's expense.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-INS-UNFAV-001",
            "finding": "Excessive limits and extended tail requirements may not be available or affordable",
            "recommendation": "Negotiate reasonable limits; verify insurability of all requirements",
            "redline": {
                "current_text": "Contractor shall maintain all coverages for ten (10) years after Final Completion at Contractor's expense.",
                "suggested_text": "Contractor shall maintain completed operations coverage for three (3) years after Final Completion. Extended coverage beyond three (3) years shall be at Owner's expense.",
                "rationale": "10-year tail requirements significantly exceed industry standard and availability",
                "success_probability": 0.70,
                "leverage_context": "Insurance market limitations; provide broker letter confirming unavailability"
            }
        },
        "dealbreaker": {
            "title": "Insurance Requirements",
            "text": """INSURANCE. Contractor shall maintain $100,000,000 in coverage for all
risks. Owner shall be loss payee and named insured on all policies. Contractor
warrants unlimited insurance availability. Contractor shall be solely responsible
for all claims regardless of insurance recovery. Any coverage gap shall be
Contractor's personal obligation. Contractor's principals shall personally
guarantee all insurance obligations.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-INS-DEAL-001",
            "finding": "Impossible insurance requirements with personal guarantee",
            "recommendation": "Cannot proceed - requirements exceed market capacity",
            "escalation": "Insurance broker review required"
        }
    },

    # =========================================================================
    # 10. INTELLECTUAL PROPERTY
    # =========================================================================
    "intellectual_property": {
        "favorable": {
            "title": "Intellectual Property",
            "text": """INTELLECTUAL PROPERTY. Contractor retains ownership of all pre-existing
intellectual property. Work product created specifically for the Project shall be
owned by Owner upon payment. Contractor grants Owner a perpetual, royalty-free
license to use Contractor's pre-existing IP incorporated in the Work for the
Project. Owner shall not use Contractor's IP for any other project without
Contractor's consent.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-IP-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Intellectual Property",
            "text": """INTELLECTUAL PROPERTY. Owner shall own all Work product and design
documents created for the Project. Contractor retains ownership of its pre-existing
tools, methods, and know-how. Contractor grants Owner a perpetual, non-exclusive,
royalty-free license to use any Contractor IP incorporated in the Work for
operation, maintenance, and modification of the facility. Contractor may use
general knowledge gained on the Project.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-IP-BAL-001",
            "finding": "Standard IP allocation with license for pre-existing IP",
            "recommendation": "Acceptable - verify scope of license is appropriate"
        },
        "unfavorable": {
            "title": "Intellectual Property",
            "text": """INTELLECTUAL PROPERTY. Owner shall own all intellectual property
created, developed, or used in connection with the Work, including Contractor's
pre-existing IP and know-how. Contractor assigns to Owner all rights in perpetuity
throughout the universe. Contractor shall execute any documents necessary to
perfect Owner's ownership. Contractor warrants it will not use any similar
processes or methods on other projects.""",
            "risk_level": "CRITICAL",
            "pattern_id": "PAT-IP-UNFAV-001",
            "finding": "Transfer of pre-existing IP and non-compete restriction",
            "recommendation": "Carve out pre-existing IP; delete non-compete provisions",
            "redline": {
                "current_text": "Owner shall own all intellectual property created, developed, or used in connection with the Work, including Contractor's pre-existing IP and know-how.",
                "suggested_text": "Owner shall own all intellectual property created specifically for the Project. Contractor retains ownership of all pre-existing intellectual property and grants Owner a license for Project use only.",
                "rationale": "Transfer of pre-existing IP would impair Contractor's ability to perform future work",
                "success_probability": 0.85,
                "leverage_context": "Standard industry practice preserves pre-existing IP"
            }
        },
        "dealbreaker": {
            "title": "Intellectual Property",
            "text": """INTELLECTUAL PROPERTY. Owner shall own all intellectual property that
Contractor has ever created or will create in the future. Contractor assigns all
patents, copyrights, trade secrets, and know-how to Owner. Contractor is prohibited
from working for any competitor of Owner for five (5) years. Contractor waives all
moral rights and attribution rights.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-IP-DEAL-001",
            "finding": "Assignment of all future IP with broad non-compete - business ending",
            "recommendation": "Cannot proceed - would destroy Contractor's business",
            "escalation": "CEO/Legal review required"
        }
    },

    # =========================================================================
    # 11. DISPUTE RESOLUTION
    # =========================================================================
    "dispute_resolution": {
        "favorable": {
            "title": "Dispute Resolution",
            "text": """DISPUTE RESOLUTION. The Parties shall attempt to resolve disputes through
good faith negotiation. If unresolved within thirty (30) days, disputes shall be
submitted to mediation under AAA Construction Mediation Rules. If mediation fails,
disputes shall be resolved by litigation in state court in the county where the
Project is located. Each Party shall bear its own attorneys' fees. Work shall
continue during dispute resolution.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-DR-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Dispute Resolution",
            "text": """DISPUTE RESOLUTION. Disputes shall first be submitted to senior
executives of each Party for negotiation. If unresolved within fourteen (14) days,
disputes shall be submitted to binding arbitration under AAA Construction Arbitration
Rules. The arbitration shall be conducted by a single arbitrator experienced in
construction disputes. The arbitrator's decision shall be final and judgment may be
entered thereon. The prevailing party shall be entitled to reasonable attorneys' fees.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-DR-BAL-001",
            "finding": "Binding arbitration with fee-shifting",
            "recommendation": "Consider whether arbitration or litigation is preferred; verify fee-shifting risk"
        },
        "unfavorable": {
            "title": "Dispute Resolution",
            "text": """DISPUTE RESOLUTION. All disputes shall be resolved by binding arbitration
administered by an arbitrator selected by Owner. The arbitration shall be conducted
in Owner's home jurisdiction. Contractor waives right to jury trial, class action,
and appeal. Contractor shall continue Work regardless of dispute and may not
withhold Work pending resolution. Contractor shall pay all arbitration costs.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-DR-UNFAV-001",
            "finding": "One-sided arbitration with Owner-selected arbitrator",
            "recommendation": "Negotiate neutral arbitrator selection; split costs",
            "redline": {
                "current_text": "All disputes shall be resolved by binding arbitration administered by an arbitrator selected by Owner.",
                "suggested_text": "Disputes shall be resolved by binding arbitration conducted by a single arbitrator mutually agreed by the Parties or, failing agreement, selected under AAA Construction Arbitration Rules.",
                "rationale": "Owner-selected arbitrator violates due process principles",
                "success_probability": 0.90,
                "leverage_context": "Standard practice requires neutral arbitrator selection"
            }
        },
        "dealbreaker": {
            "title": "Dispute Resolution",
            "text": """DISPUTE RESOLUTION. Owner's determination on all disputes shall be final
and binding. Contractor waives all right to dispute resolution, mediation,
arbitration, and litigation. Any challenge to Owner's decision shall result in
immediate termination for cause and forfeiture of all amounts owed. Contractor
waives sovereign immunity and consents to jurisdiction in any forum Owner selects.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-DR-DEAL-001",
            "finding": "No dispute resolution rights - Owner's decision is final",
            "recommendation": "Cannot proceed - must have access to neutral dispute resolution",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 12. FORCE MAJEURE
    # =========================================================================
    "force_majeure": {
        "favorable": {
            "title": "Force Majeure",
            "text": """FORCE MAJEURE. Neither Party shall be liable for delays or failures in
performance caused by events beyond its reasonable control, including: acts of God,
war, terrorism, civil disturbance, labor disputes, epidemics, pandemics, government
actions, supply chain disruptions, and unusually severe weather. The affected Party
shall provide prompt notice and mitigation efforts. Excusable delay shall entitle
Contractor to time extension and equitable adjustment of Contract Price.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-FM-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Force Majeure",
            "text": """FORCE MAJEURE. Contractor shall be entitled to time extension for delays
caused by acts of God, war, terrorism, civil disturbance, and government actions
affecting the Project. Contractor shall provide written notice within seven (7) days
of the force majeure event and shall use reasonable efforts to mitigate. No cost
adjustment shall be made for force majeure events. Either Party may terminate if
force majeure continues for more than ninety (90) days.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-FM-BAL-001",
            "finding": "Time extension only - no cost adjustment for force majeure",
            "recommendation": "Consider adding cost adjustment for extended force majeure events"
        },
        "unfavorable": {
            "title": "Force Majeure",
            "text": """FORCE MAJEURE. Force majeure shall be limited to acts of God and declared
war only. Weather, labor disputes, supply issues, and pandemics shall not constitute
force majeure. Contractor shall be entitled to time extension only, with no cost
adjustment. Notice must be provided within twenty-four (24) hours. Owner may
terminate without liability if force majeure delays Project more than thirty (30)
days.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-FM-UNFAV-001",
            "finding": "Narrow force majeure definition excludes common events",
            "recommendation": "Expand force majeure definition; extend notice period",
            "redline": {
                "current_text": "Force majeure shall be limited to acts of God and declared war only. Weather, labor disputes, supply issues, and pandemics shall not constitute force majeure.",
                "suggested_text": "Force majeure shall include: acts of God, war, terrorism, epidemics, pandemics, government actions, unusually severe weather, and labor disputes not caused by Contractor.",
                "rationale": "Narrow definition leaves Contractor exposed to common force majeure events",
                "success_probability": 0.75,
                "leverage_context": "Pandemic and supply chain events are now industry standard force majeure"
            }
        },
        "dealbreaker": {
            "title": "Force Majeure",
            "text": """FORCE MAJEURE. There shall be no force majeure relief. Contractor assumes
all risk of delays regardless of cause. Contractor shall complete the Work by the
Scheduled Completion Date regardless of events beyond Contractor's control.
Liquidated damages shall accrue for all delays. Contractor warrants uninterrupted
performance is possible and achievable.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-FM-DEAL-001",
            "finding": "No force majeure relief - assumes all delay risk",
            "recommendation": "Cannot proceed - must have force majeure protection",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 13. SCHEDULE AND DELAYS
    # =========================================================================
    "schedule_delays": {
        "favorable": {
            "title": "Schedule and Delays",
            "text": """SCHEDULE. Contractor shall perform the Work in accordance with the
Project Schedule. Float is a shared Project resource. Contractor shall be entitled
to time extension for: (a) Owner-caused delays, (b) changes to the Work, (c)
unforeseen site conditions, (d) force majeure, and (e) concurrent delays caused by
Owner. Time extensions shall include commensurate cost adjustment for extended
general conditions. Contractor shall provide monthly schedule updates.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-SCH-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Schedule and Delays",
            "text": """SCHEDULE. Time is of the essence. Contractor shall achieve Substantial
Completion by the Contract Completion Date. Contractor shall be entitled to time
extension for excusable delays that impact the critical path, provided Contractor
gives written notice within fourteen (14) days of the delay event. Float shall be
allocated to the activity that generates it. No compensation shall be paid for
delays unless Contractor can demonstrate Owner-caused delay.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-SCH-BAL-001",
            "finding": "Standard schedule provisions with proof required for compensation",
            "recommendation": "Maintain detailed daily logs to support delay claims"
        },
        "unfavorable": {
            "title": "Schedule and Delays",
            "text": """SCHEDULE. All float belongs to Owner. Contractor shall accelerate Work
at no additional cost to recover any delays regardless of cause. No time extension
shall be granted except for changes directed in writing by Owner. Concurrent delays
shall be apportioned to Contractor. Owner may direct acceleration at any time and
Contractor shall comply. Acceleration costs are included in the Contract Price.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-SCH-UNFAV-001",
            "finding": "Owner float ownership and acceleration risk",
            "recommendation": "Negotiate shared float; add acceleration compensation",
            "redline": {
                "current_text": "All float belongs to Owner.",
                "suggested_text": "Float shall be a shared Project resource, available to offset delays regardless of cause.",
                "rationale": "Owner-owned float eliminates schedule flexibility that benefits both parties",
                "success_probability": 0.70,
                "leverage_context": "Schedule risk is shared; float should be similarly shared"
            }
        },
        "dealbreaker": {
            "title": "Schedule and Delays",
            "text": """SCHEDULE. Contractor guarantees completion by the Contract Completion
Date regardless of any circumstance. No extension shall be granted for any reason.
Contractor shall perform twenty-four (24) hour operations if necessary at no
additional cost. All schedule risk is Contractor's risk. Contractor warrants the
schedule is achievable and waives any claim for delay.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-SCH-DEAL-001",
            "finding": "Absolute schedule guarantee with no delay relief",
            "recommendation": "Cannot proceed - must have delay relief provisions",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 14. SAFETY AND COMPLIANCE
    # =========================================================================
    "safety_compliance": {
        "favorable": {
            "title": "Safety and Compliance",
            "text": """SAFETY. Contractor shall comply with all applicable OSHA regulations and
maintain a safe worksite. Owner shall be responsible for safety hazards in areas
outside Contractor's Work. Contractor shall be entitled to time extension and cost
adjustment for delays caused by Owner's failure to remediate pre-existing hazards.
Each Party shall indemnify the other for safety violations caused by that Party.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-SAF-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Safety and Compliance",
            "text": """SAFETY. Contractor shall be solely responsible for worksite safety and
shall comply with all applicable laws including OSHA. Contractor shall implement a
Project-specific safety plan approved by Owner. Contractor shall stop Work
immediately upon discovering any safety hazard. Safety violations may result in
removal of personnel from site. Contractor shall bear cost of OSHA violations
resulting from Contractor's Work.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-SAF-BAL-001",
            "finding": "Standard safety provisions with Contractor responsibility for its Work",
            "recommendation": "Verify Owner's pre-existing condition disclosure; confirm safety plan requirements"
        },
        "unfavorable": {
            "title": "Safety and Compliance",
            "text": """SAFETY. Contractor assumes sole responsibility for all worksite safety
including areas controlled by Owner and other contractors. Contractor shall be
responsible for all OSHA violations regardless of cause. Contractor shall remediate
all pre-existing hazards at Contractor's cost. Contractor indemnifies Owner for all
safety-related claims including claims by Owner's employees and other contractors.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-SAF-UNFAV-001",
            "finding": "Responsibility for pre-existing hazards and other contractors' safety",
            "recommendation": "Limit responsibility to Contractor's own Work areas",
            "redline": {
                "current_text": "Contractor assumes sole responsibility for all worksite safety including areas controlled by Owner and other contractors.",
                "suggested_text": "Contractor shall be responsible for safety in areas where Contractor is performing Work. Owner shall be responsible for safety in all other areas.",
                "rationale": "Cannot control safety in areas outside Contractor's control",
                "success_probability": 0.85,
                "leverage_context": "Basic principle - responsibility follows control"
            }
        },
        "dealbreaker": {
            "title": "Safety and Compliance",
            "text": """SAFETY. Contractor guarantees zero safety incidents. Any OSHA citation
regardless of cause shall result in immediate termination for cause and forfeiture
of all amounts owed. Contractor shall be criminally liable for any safety incidents.
Contractor waives all defenses to safety claims. Contractor personally guarantees
payment of all safety fines and penalties.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-SAF-DEAL-001",
            "finding": "Zero incident guarantee with criminal liability - impossible standard",
            "recommendation": "Cannot proceed - no one can guarantee zero safety incidents",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 15. BONDS AND SECURITY
    # =========================================================================
    "bonds_security": {
        "favorable": {
            "title": "Bonds and Security",
            "text": """BONDS. Contractor shall provide Performance and Payment Bonds each in
the amount of one hundred percent (100%) of the Contract Price. Bonds shall be
issued by a surety rated A- or better by A.M. Best. Bond premium shall be reimbursed
by Owner as a separate line item. Bond forms shall be AIA A312 or equivalent. No
additional security shall be required.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-BND-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Bonds and Security",
            "text": """BONDS. Contractor shall provide Performance and Payment Bonds each equal
to one hundred percent (100%) of the Contract Price at Contractor's expense. Surety
shall be rated A- VII or better by A.M. Best and licensed in the state where the
Project is located. Bond forms shall be satisfactory to Owner. Contractor shall
maintain bonds in full force through Final Completion and correction of defects.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-BND-BAL-001",
            "finding": "Standard bonding requirements at Contractor's expense",
            "recommendation": "Verify bond cost is included in pricing; confirm surety availability"
        },
        "unfavorable": {
            "title": "Bonds and Security",
            "text": """BONDS. Contractor shall provide Performance and Payment Bonds each equal
to one hundred fifty percent (150%) of the Contract Price. Contractor shall also
provide a Subcontractor Default Insurance policy and Parent Company Guarantee.
Surety shall be rated A+ XV or better. Bonds shall remain in effect for five (5)
years after Final Completion. Contractor shall pay all bond costs including any
increase due to change orders.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-BND-UNFAV-001",
            "finding": "Excessive bonding requirements may not be available",
            "recommendation": "Confirm availability of 150% bonds; negotiate standard 100% requirement",
            "redline": {
                "current_text": "Contractor shall provide Performance and Payment Bonds each equal to one hundred fifty percent (150%) of the Contract Price.",
                "suggested_text": "Contractor shall provide Performance and Payment Bonds each equal to one hundred percent (100%) of the Contract Price.",
                "rationale": "150% bonding exceeds industry standard and may not be available from surety",
                "success_probability": 0.80,
                "leverage_context": "Surety capacity constraints; 100% is industry standard"
            }
        },
        "dealbreaker": {
            "title": "Bonds and Security",
            "text": """BONDS. Contractor shall provide bonds equal to three hundred percent
(300%) of the Contract Price. Contractor's principals shall provide personal
guarantees. Contractor shall deposit cash collateral equal to fifty percent (50%)
of Contract Price. All security shall be forfeited upon any breach. Letter of Credit
shall be issued by Owner's preferred bank only.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-BND-DEAL-001",
            "finding": "300% bonding with cash collateral - financially impossible",
            "recommendation": "Cannot proceed - requirements exceed surety market capacity",
            "escalation": "Surety review required"
        }
    },

    # =========================================================================
    # 16. ASSIGNMENT
    # =========================================================================
    "assignment": {
        "favorable": {
            "title": "Assignment",
            "text": """ASSIGNMENT. Neither Party may assign this Agreement without the prior
written consent of the other Party, which consent shall not be unreasonably withheld
or delayed. Notwithstanding the foregoing, either Party may assign this Agreement
to an affiliate or in connection with a merger, acquisition, or sale of substantially
all assets without consent. Any assignment shall not release the assigning Party
from its obligations hereunder.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-ASN-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Assignment",
            "text": """ASSIGNMENT. Contractor shall not assign this Agreement or any portion
thereof without Owner's prior written consent. Owner may assign this Agreement to
any successor owner of the Project or lender. Assignment shall not release the
assigning Party from liability. Contractor may assign to a surety performing under
a bond. Subcontracting to approved subcontractors shall not constitute assignment.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-ASN-BAL-001",
            "finding": "Standard assignment restrictions with Owner carve-out",
            "recommendation": "Acceptable - verify subcontracting approval process"
        },
        "unfavorable": {
            "title": "Assignment",
            "text": """ASSIGNMENT. Contractor shall not assign any right or obligation under
this Agreement without Owner's prior written consent, which may be withheld in
Owner's sole discretion for any reason or no reason. Owner may assign this Agreement
at any time without notice to Contractor. Any attempted assignment by Contractor
shall be void and grounds for immediate termination for cause.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-ASN-UNFAV-001",
            "finding": "Absolute assignment prohibition may impair financing and exit options",
            "recommendation": "Add 'not to be unreasonably withheld' standard",
            "redline": {
                "current_text": "which may be withheld in Owner's sole discretion for any reason or no reason.",
                "suggested_text": "which consent shall not be unreasonably withheld, conditioned, or delayed.",
                "rationale": "Absolute discretion prevents legitimate business transactions",
                "success_probability": 0.85,
                "leverage_context": "Standard industry language; enables financing flexibility"
            }
        },
        "dealbreaker": {
            "title": "Assignment",
            "text": """ASSIGNMENT. Any change in Contractor's ownership, management, or control
shall be deemed an assignment requiring Owner's consent. Contractor shall not grant
any security interest in receivables or equipment. Contractor waives all rights to
assign to surety. Owner may terminate without liability if Contractor undergoes any
change in ownership or control.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-ASN-DEAL-001",
            "finding": "Restrictions on ownership changes impair corporate flexibility",
            "recommendation": "Cannot proceed - internal corporate matters should not require consent",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 17. CONFIDENTIALITY
    # =========================================================================
    "confidentiality": {
        "favorable": {
            "title": "Confidentiality",
            "text": """CONFIDENTIALITY. Each Party shall protect the other Party's confidential
information using the same degree of care it uses for its own confidential
information, but no less than reasonable care. Confidential information excludes
information that: (a) is public, (b) was known before disclosure, (c) is received
from a third party, or (d) is independently developed. Confidentiality obligations
shall survive for three (3) years after completion.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-CNF-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Confidentiality",
            "text": """CONFIDENTIALITY. Contractor shall maintain confidentiality of all
Project information, Owner's business information, and the terms of this Agreement.
Confidential information may be disclosed to employees and subcontractors with a
need to know who are bound by similar confidentiality obligations. Contractor may
disclose information required by law with prior notice to Owner. Confidentiality
obligations survive for five (5) years.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-CNF-BAL-001",
            "finding": "Standard confidentiality with reasonable exceptions",
            "recommendation": "Verify disclosure to subcontractors is permitted"
        },
        "unfavorable": {
            "title": "Confidentiality",
            "text": """CONFIDENTIALITY. Contractor shall maintain absolute confidentiality of
all information related to the Project, Owner, and this Agreement in perpetuity.
Contractor shall not disclose any information to any person including employees
without Owner's prior written consent. Contractor shall not acknowledge the
existence of this Agreement. Breach of confidentiality shall result in liquidated
damages of $1,000,000 per occurrence.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-CNF-UNFAV-001",
            "finding": "Perpetual confidentiality with punitive damages - impractical",
            "recommendation": "Negotiate reasonable term and carve-outs for operations",
            "redline": {
                "current_text": "Contractor shall not disclose any information to any person including employees without Owner's prior written consent.",
                "suggested_text": "Contractor may disclose information to employees, subcontractors, and professional advisors with a need to know who are bound by confidentiality obligations.",
                "rationale": "Cannot perform Work without disclosing information to team members",
                "success_probability": 0.90,
                "leverage_context": "Operationally necessary; standard industry practice"
            }
        },
        "dealbreaker": {
            "title": "Confidentiality",
            "text": """CONFIDENTIALITY. All knowledge, information, and ideas that Contractor
obtains or develops in connection with the Project shall become Owner's exclusive
property. Contractor shall not use any general knowledge, skills, or experience
gained on the Project. Contractor and its employees shall sign personal
non-disclosure agreements. Breach shall result in criminal prosecution.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-CNF-DEAL-001",
            "finding": "Prohibition on using general knowledge - impossible and unreasonable",
            "recommendation": "Cannot proceed - cannot prohibit use of general skills and knowledge",
            "escalation": "Legal review required"
        }
    },

    # =========================================================================
    # 18. GOVERNING LAW
    # =========================================================================
    "governing_law": {
        "favorable": {
            "title": "Governing Law and Venue",
            "text": """GOVERNING LAW. This Agreement shall be governed by the laws of the state
where the Project is located, without regard to conflicts of law principles. Any
litigation shall be brought in state or federal court in the county where the
Project is located. Each Party waives objection to venue and personal jurisdiction
in such courts. Each Party shall bear its own costs and attorneys' fees.""",
            "risk_level": "LOW",
            "pattern_id": "PAT-GOV-FAV-001",
            "finding": None,
            "recommendation": None
        },
        "balanced": {
            "title": "Governing Law and Venue",
            "text": """GOVERNING LAW. This Agreement shall be governed by the laws of Delaware.
Exclusive venue shall be in Delaware state or federal courts. The prevailing party
in any litigation shall be entitled to recover reasonable attorneys' fees and costs.
The Parties waive any right to jury trial. Nothing herein shall limit either Party's
right to seek injunctive relief in any court of competent jurisdiction.""",
            "risk_level": "MEDIUM",
            "pattern_id": "PAT-GOV-BAL-001",
            "finding": "Delaware law with fee-shifting and jury waiver",
            "recommendation": "Consider implications of Delaware law; verify jury waiver is acceptable"
        },
        "unfavorable": {
            "title": "Governing Law and Venue",
            "text": """GOVERNING LAW. This Agreement shall be governed by the laws of Owner's
home state. Exclusive venue shall be in courts in Owner's headquarters city.
Contractor submits to personal jurisdiction in such courts and waives any objection
to venue. Contractor shall pay all litigation costs and Owner's attorneys' fees
regardless of outcome. Contractor waives right to remove to federal court.""",
            "risk_level": "HIGH",
            "pattern_id": "PAT-GOV-UNFAV-001",
            "finding": "Remote venue with one-sided fee allocation",
            "recommendation": "Negotiate project-location venue; make fees contingent on outcome",
            "redline": {
                "current_text": "Contractor shall pay all litigation costs and Owner's attorneys' fees regardless of outcome.",
                "suggested_text": "The prevailing party shall be entitled to recover reasonable attorneys' fees and costs from the non-prevailing party.",
                "rationale": "One-sided fee allocation discourages legitimate claims",
                "success_probability": 0.85,
                "leverage_context": "Standard fee-shifting creates balanced incentives"
            }
        },
        "dealbreaker": {
            "title": "Governing Law and Venue",
            "text": """GOVERNING LAW. This Agreement shall be governed by the laws of a foreign
jurisdiction selected by Owner. Exclusive venue shall be in Owner's home country.
Contractor waives all rights under U.S. law. Contractor shall post a bond equal to
the amount in dispute before commencing litigation. All proceedings shall be
conducted in a language selected by Owner.""",
            "risk_level": "DEALBREAKER",
            "pattern_id": "PAT-GOV-DEAL-001",
            "finding": "Foreign law and venue with litigation bond - denies access to justice",
            "recommendation": "Cannot proceed - must have access to U.S. courts and law",
            "escalation": "Legal review required"
        }
    },
}

# =============================================================================
# HELPER FUNCTION
# =============================================================================

def get_clause(category, risk_variant):
    """
    Get a clause from the library.

    Args:
        category: One of the 18 EPC categories
        risk_variant: 'favorable', 'balanced', 'unfavorable', or 'dealbreaker'

    Returns:
        dict with clause data or None if not found
    """
    if category in EPC_CLAUSE_LIBRARY:
        if risk_variant in EPC_CLAUSE_LIBRARY[category]:
            return EPC_CLAUSE_LIBRARY[category][risk_variant]
    return None


def get_all_categories():
    """Return list of all clause categories."""
    return list(EPC_CLAUSE_LIBRARY.keys())


def get_random_clause_set(num_clauses=10):
    """
    Generate a random set of clauses for a contract.

    Args:
        num_clauses: Number of clauses to generate

    Returns:
        list of clause dicts with section numbers
    """
    import random

    categories = get_all_categories()
    selected = random.sample(categories, min(num_clauses, len(categories)))

    clauses = []
    for i, category in enumerate(selected):
        # Weight toward balanced/unfavorable for realistic distribution
        weights = [0.20, 0.40, 0.30, 0.10]  # favorable, balanced, unfavorable, dealbreaker
        variants = ['favorable', 'balanced', 'unfavorable', 'dealbreaker']
        variant = random.choices(variants, weights=weights)[0]

        clause = get_clause(category, variant)
        if clause:
            clause_data = clause.copy()
            clause_data['category'] = category
            clause_data['section_number'] = f"{i+1}.0"
            clauses.append(clause_data)

    return clauses


if __name__ == "__main__":
    # Test the library
    print(f"EPC Clause Library loaded with {len(EPC_CLAUSE_LIBRARY)} categories")

    for category in get_all_categories():
        print(f"\n{category}:")
        for variant in ['favorable', 'balanced', 'unfavorable', 'dealbreaker']:
            clause = get_clause(category, variant)
            if clause:
                print(f"  {variant}: {clause['risk_level']}")
