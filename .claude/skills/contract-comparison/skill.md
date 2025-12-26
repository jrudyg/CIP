# Contract Comparison Intelligence Skill

**Version:** 1.0.0
**Purpose:** Context-aware contract change classification with business reasoning
**Model:** Claude Sonnet 4

## Overview

This skill enhances Python-based contract comparison results with intelligent, context-aware impact classification. It considers contract position (Service Provider vs Customer), leverage (Strong/Moderate/Weak), and business narrative to provide nuanced analysis with reasoning.

## Input Schema

```json
{
  "changes": [
    {
      "section_number": "3",
      "section_title": "TERM AND TERMINATION",
      "v1_content": "Original contract text for this section...",
      "v2_content": "Revised contract text for this section...",
      "change_type": "modification",
      "similarity": 0.82,
      "confidence": 0.95
    }
  ],
  "v1_context": {
    "contract_id": 44,
    "filename": "MSA Original v1.docx",
    "position": "Service Provider",
    "leverage": "Strong",
    "narrative": "Business context about the contract relationship..."
  },
  "v2_context": {
    "contract_id": 45,
    "filename": "MSA Final v2.docx",
    "position": "Service Provider",
    "leverage": "Strong",
    "narrative": "Updated business context..."
  }
}
```

## Output Schema

**IMPORTANT**: Do NOT include v1_content or v2_content fields in the output. These are provided for analysis only and should not be returned (they cause JSON parsing issues due to special characters).

```json
{
  "changes": [
    {
      "section_number": "3",
      "section_title": "TERM AND TERMINATION",
      "change_type": "modification",
      "impact": "CRITICAL",
      "reasoning": "As Service Provider, termination rights expanded from unilateral (Company) to bilateral (either party). This reduces exit flexibility and increases risk of customer terminating mid-project.",
      "risk_factors": [
        "Loss of unilateral termination control",
        "Notice period increased 15→30 days delays exit"
      ],
      "business_impact": "High risk for Service Provider: Customer gains equal termination power, potentially exiting during critical delivery phases.",
      "recommendation": "NEGOTIATE: Request retention of unilateral termination rights OR add termination fee schedule to offset customer exit risk.",
      "cumulative_notes": "This is the 2nd change weakening termination protections - compounds with payment term changes to increase customer exit risk."
    }
  ],
  "executive_summary": {
    "critical_count": 2,
    "high_priority_count": 5,
    "important_count": 3,
    "operational_count": 8,
    "administrative_count": 2,
    "key_patterns": [
      "5 changes systematically weaken Service Provider termination and payment protections",
      "Risk concentration in customer exit scenarios"
    ],
    "summary_text": "Analysis of MSA changes from Service Provider perspective (Strong leverage). Two CRITICAL changes detected...",
    "position_analysis": "As Service Provider with Strong leverage, these changes weaken your negotiating position through systematic erosion of exit controls and payment protections...",
    "top_risks": [
      "Customer can terminate mid-project with 30-day notice",
      "No restriction on serving competitors during term",
      "Payment terms extended with termination changes create cash flow risk"
    ],
    "strategic_recommendation": "NEGOTIATE",
    "cumulative_impact": "The pattern of changes creates compounding risk that exceeds the sum of individual changes"
  }
}
```

## Classification Logic

### Impact Levels

**CRITICAL** - Deal-breaking changes requiring immediate attention:
- Unlimited liability exposure
- Loss of IP rights/ownership
- Regulatory compliance violations
- Indemnification obligations (direction matters!)
- Insurance requirement increases >50%
- Unilateral termination rights lost

**HIGH_PRIORITY** - Significant business risk requiring review:
- Termination rights changes
- Warranty/guarantee obligations increased
- SLA penalties introduced or increased
- Payment terms extended >30 days
- Performance standards raised materially
- Non-compete/non-solicit additions

**IMPORTANT** - Notable changes affecting operations:
- Payment schedule modifications
- Invoice processing changes
- Milestone definitions altered
- Reporting requirements added
- Notice periods changed

**OPERATIONAL** - Process/procedural changes:
- Communication protocols
- Meeting requirements
- Approval processes
- Administrative procedures

**ADMINISTRATIVE** - Minor formatting/clarification:
- Typo corrections
- Formatting changes
- Date updates
- Party name clarifications

### Context-Aware Classification Rules

#### For Service Provider Position:

**CRITICAL if:**
- Liability INCREASES (e.g., cap removed, unlimited exposure)
- IP ownership transfers TO customer
- "Provider shall indemnify Customer" added/expanded
- Non-compete ADDED (restricts future business)
- Termination flexibility DECREASES (unilateral → bilateral)
- Insurance requirements INCREASED significantly

**HIGH_PRIORITY if:**
- Payment terms EXTENDED (Net 30 → Net 60)
- Warranty obligations INCREASED
- Performance standards RAISED
- Acceptance criteria TIGHTENED
- Late fees/penalties REMOVED
- Force majeure protections WEAKENED

**IMPORTANT if:**
- Invoice requirements MORE complex
- Milestone definitions CHANGED
- Reporting frequency INCREASED
- Approval processes ADDED

#### For Customer Position:

**CRITICAL if:**
- Liability protection DECREASED
- IP ownership transfers TO provider
- "Customer shall indemnify Provider" added/expanded
- Termination rights RESTRICTED
- SLA guarantees WEAKENED/removed
- Data protection obligations REDUCED

**HIGH_PRIORITY if:**
- Payment obligations INCREASED
- Service levels LOWERED
- Acceptance windows SHORTENED
- Warranty coverage REDUCED
- Audit rights RESTRICTED

**IMPORTANT if:**
- Payment terms SHORTENED (Net 60 → Net 30)
- Reporting from provider REDUCED
- Change control process RELAXED

### Directionality Analysis

**Critical Consideration:** WHO bears the obligation matters!

**Examples:**

1. **Indemnification:**
   - "Provider shall indemnify Customer"
     - Service Provider: BAD (increases liability)
     - Customer: GOOD (gains protection)
   - "Customer shall indemnify Provider"
     - Service Provider: GOOD (gains protection)
     - Customer: BAD (increases liability)

2. **Termination Rights:**
   - "Either party may terminate" (bilateral)
     - Service Provider: WORSE if was unilateral before
     - Customer: BETTER if was provider-only before
   - "Provider may terminate" (unilateral)
     - Service Provider: GOOD (control)
     - Customer: BAD (loss of stability)

3. **IP Ownership:**
   - "All IP belongs to Provider"
     - Service Provider: GOOD
     - Customer: BAD (paying for work but not owning it)
   - "All IP transfers to Customer"
     - Service Provider: BAD (losing work product)
     - Customer: GOOD

### Leverage Consideration

**Strong Leverage:**
- Can push back on unfavorable changes
- Recommendations: "NEGOTIATE strongly" or "REJECT"
- Higher threshold for acceptance

**Moderate Leverage:**
- Some negotiation room
- Recommendations: "NEGOTIATE" or "ACCEPT with conditions"
- Balanced approach

**Weak Leverage:**
- Limited ability to contest
- Recommendations: "FLAG for review" or "ACCEPT"
- Focus on most critical items only

## Reasoning Generation Guidelines

For each change classified as **CRITICAL** or **HIGH_PRIORITY**, provide:

### 1. WHAT Changed (Factual)
```
"Termination rights changed from 'Company may terminate with 15-day notice'
to 'Either party may terminate with 30-day notice'."
```

### 2. WHY It Matters (Context-Aware)
```
"As Service Provider, you lose unilateral control over contract exit timing,
and Customer gains equal termination power."
```

### 3. IMPACT on Position Holder (Specific Business Consequence)
```
"This increases project abandonment risk during critical delivery phases,
potentially leaving you with unrecoverable costs for work-in-progress."
```

### 4. RECOMMENDATION (Actionable)
```
"NEGOTIATE: Request retention of unilateral termination rights OR add
termination fee schedule (e.g., 50% of remaining contract value) to offset
customer exit risk."
```

## Executive Summary Generation

### Structure:

1. **Position Context:**
   ```
   "Analysis of [Contract Name] changes from [Position] perspective with
   [Leverage] leverage."
   ```

2. **Key Findings:**
   ```
   "[X] CRITICAL changes detected: (1) [Change 1], (2) [Change 2]"
   ```

3. **Position Analysis:**
   ```
   "As [Position] with [Leverage] leverage, these changes [strengthen/weaken]
   your negotiating position. [Specific analysis]"
   ```

4. **Top Risks (3-5 items):**
   - Most critical business impacts
   - Ordered by severity
   - Action-oriented

5. **Strategic Recommendation:**
   - **ACCEPT**: Changes are favorable or neutral
   - **NEGOTIATE**: Some concerning changes, leverage available
   - **REJECT**: Critical issues, too risky to proceed
   - **FLAG**: Needs legal/executive review

## Edge Cases

### No Position Specified
- Default to neutral analysis
- Provide both perspectives where relevant
- Flag: "Position not specified - generic analysis provided"

### Contradictory Changes
- Flag: "Conflicting changes detected in sections X and Y"
- Provide analysis for both interpretations
- Recommend: "Requires clarification"

### Unclear Directionality
- Request clarification in reasoning
- Provide conditional analysis: "If Provider is obligated... / If Customer is obligated..."

### Missing Context Fields
- Graceful degradation to generic classification
- Note: "Analysis limited by incomplete contract metadata"

## Example Analysis

### Input Change:
```json
{
  "section_number": "8",
  "section_title": "LIMITATION OF LIABILITY",
  "v1_content": "Provider's liability shall be limited to the total fees paid under this Agreement in the twelve (12) months preceding the claim.",
  "v2_content": "Provider shall be liable for all direct, indirect, consequential, and incidental damages arising from this Agreement without limitation.",
  "change_type": "modification",
  "v1_context": {
    "position": "Service Provider",
    "leverage": "Strong"
  }
}
```

### Expected Output:
```json
{
  "section_number": "8",
  "section_title": "LIMITATION OF LIABILITY",
  "v1_content": "Provider's liability shall be limited to the total fees paid...",
  "v2_content": "Provider shall be liable for all direct, indirect, consequential...",
  "change_type": "modification",
  "impact": "CRITICAL",
  "reasoning": "Liability cap completely removed. Original contract limited Provider's exposure to 12 months of fees (quantifiable, manageable risk). Revised version imposes UNLIMITED liability for all damage types including consequential damages. As Service Provider, this creates catastrophic financial risk - a single incident could expose you to claims exceeding your company's total assets.",
  "risk_factors": [
    "Unlimited financial exposure (no cap)",
    "Includes consequential damages (historically largest claims)",
    "Includes indirect damages (hard to predict/quantify)",
    "No carve-outs for customer negligence or third-party actions"
  ],
  "business_impact": "DEALBREAKER: Unlimited liability is typically uninsurable and creates existential risk to Service Provider. Even with Strong leverage, accepting this clause could bankrupt the company from a single major incident.",
  "recommendation": "REJECT: This change is non-negotiable. Insist on liability cap (industry standard: 12 months fees or $X million, whichever is greater). If Customer refuses, strongly recommend declining the contract - the risk outweighs any potential revenue."
}
```

## Analysis Instructions

When you receive a comparison request:

1. **Parse Input:**
   - Extract changes array
   - Extract v1_context and v2_context
   - Identify position, leverage, and narrative

2. **CRITICAL - Analyze ALL Changes Together First (Cumulative Context):**
   - Review ALL changes as a complete set BEFORE analyzing individually
   - Identify patterns across changes:
     - Do multiple changes weaken the same area? (e.g., termination + payment + performance)
     - Are obligations systematically shifting from one party to another?
     - Is risk concentration increasing in specific areas?
   - Note compound effects:
     - Changes that individually seem minor but together are significant
     - Sequential changes that create new combined risks
     - Contradictory changes that create ambiguity
   - **This cumulative view is THE KEY QUALITY ADVANTAGE of batch analysis**

3. **For Each Change (With Cumulative Context):**
   - Read v1_content and v2_content carefully
   - Identify the nature of the change (what specifically changed)
   - Determine directionality (who benefits/who is burdened)
   - Apply position-aware classification rules
   - **Reference patterns identified in Step 2** (e.g., "This is the 3rd change weakening termination rights")
   - Generate detailed reasoning for ALL changes (not just CRITICAL/HIGH_PRIORITY):
     - WHAT changed (factual)
     - WHY it matters (context-aware)
     - IMPACT on position holder (business consequences)
     - CUMULATIVE NOTES if it compounds with other changes
   - Identify specific risk factors
   - Provide actionable recommendation considering leverage

4. **Generate Executive Summary (Strategic Overview):**
   - Count changes by impact level
   - **Highlight key patterns discovered** (e.g., "5 changes systematically weaken Service Provider position")
   - Synthesize top 2-3 critical findings
   - Write position-aware summary with cumulative impact assessment
   - List top 3-5 risks (prioritized by cumulative severity)
   - Provide strategic recommendation considering:
     - Overall pattern of changes (not just individual severity)
     - Cumulative risk exposure
     - Negotiation leverage available
     - Recommendation: ACCEPT / NEGOTIATE / REJECT / FLAG

5. **Return JSON:**
   - Preserve all original fields from input
   - Add enhanced fields (impact, reasoning, risk_factors, etc.)
   - Include executive_summary object
   - Ensure valid JSON structure

## Quality Checklist

Before returning results, verify:

- [ ] All CRITICAL changes have detailed reasoning
- [ ] All HIGH_PRIORITY changes have reasoning
- [ ] Directionality correctly assessed (who bears obligation)
- [ ] Position context applied correctly (Provider vs Customer)
- [ ] Leverage reflected in recommendations
- [ ] Executive summary is position-aware
- [ ] Top risks are specific and actionable
- [ ] Strategic recommendation matches severity of findings
- [ ] JSON is valid and complete

## Usage Example

```python
# Backend will call this skill with:
skill_result = invoke_skill(
    skill_name="contract-comparison-intelligence",
    input_data={
        "changes": python_comparison_results['changes'],
        "v1_context": v1_contract_metadata,
        "v2_context": v2_contract_metadata
    }
)

# Returns enhanced results with reasoning
enhanced_results = skill_result['output']
```

---

**Note:** This skill is designed to work in tandem with Python-based structure extraction. Python handles section matching and text diffing (fast, deterministic), while this skill provides intelligent classification and reasoning (context-aware, adaptive).
