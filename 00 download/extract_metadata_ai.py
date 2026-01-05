# =============================================================================
# STEP 6: METADATA EXTRACTION (AI-Powered with Regex Fallback)
# =============================================================================
# 
# INTEGRATION INSTRUCTIONS:
# 1. Add to imports at top of intake_engine.py:
#    import anthropic
# 
# 2. Add to CONFIGURATION section:
#    CLAUDE_MODEL = "claude-sonnet-4-20250514"
#    EXTRACTION_TIMEOUT = 30
# 
# 3. Replace existing extract_metadata function (lines 509-565) with this code
# =============================================================================

def extract_metadata_ai(full_text: str, clauses: List[Clause]) -> ContractMetadata:
    """
    Extract contract metadata using Claude AI with regex fallback.
    
    Primary: Claude API structured extraction
    Fallback: Regex patterns if API unavailable
    
    Returns ContractMetadata with extraction_method and extraction_confidence populated.
    """
    metadata = ContractMetadata()
    
    # Try AI extraction first
    try:
        metadata = _extract_with_claude(full_text)
        metadata.extraction_method = 'AI'
    except Exception as e:
        print(f"AI extraction failed, using regex fallback: {e}")
        metadata = _extract_with_regex(full_text)
        metadata.extraction_method = 'REGEX'
    
    return metadata


def _extract_with_claude(full_text: str) -> ContractMetadata:
    """
    Extract metadata using Claude API with structured prompt.
    """
    import anthropic
    
    # Truncate text if too long (use first 15000 chars for extraction)
    text_sample = full_text[:15000] if len(full_text) > 15000 else full_text
    
    extraction_prompt = f"""Analyze this contract text and extract the following metadata. 
Respond ONLY with valid JSON, no other text.

CONTRACT TEXT:
{text_sample}

EXTRACT (respond in this exact JSON format):
{{
    "party_client": "Name of the client/customer/buyer or null if not found",
    "party_vendor": "Name of the vendor/supplier/seller or null if not found",
    "effective_date": "Date in YYYY-MM-DD format or null if not found",
    "expiration_date": "Date in YYYY-MM-DD format or null if not found",
    "contract_value": 0.00 or null if not found (numeric only, no currency symbols),
    "currency": "USD" or appropriate currency code,
    "governing_law": "State or jurisdiction name or null if not found",
    "contract_type": "One of: MSA, SOW, NDA, MNDA, IPA, EULA, Amendment, Purchase Order, Services Agreement, License Agreement, Other",
    "purpose": "One of: Equipment, Services, Professional Services, Engineering, Installation, Staffing, Transportation, Maintenance, Software, Consulting, Integration, Other",
    "relationship": "One of: Standalone, Parent, Child, Amendment, Renewal, Other",
    "confidence": {{
        "party_client": 0.0-1.0,
        "party_vendor": 0.0-1.0,
        "effective_date": 0.0-1.0,
        "expiration_date": 0.0-1.0,
        "contract_value": 0.0-1.0,
        "governing_law": 0.0-1.0,
        "contract_type": 0.0-1.0,
        "purpose": 0.0-1.0
    }}
}}

RULES:
- Extract actual entity names, not placeholders like [COMPANY_A]
- If a party is labeled "Client" or "Customer", that's party_client
- If a party is labeled "Vendor", "Supplier", "Contractor", that's party_vendor
- For dates, convert to YYYY-MM-DD format
- For contract_value, extract the primary/total value, not individual line items
- Confidence should reflect how certain you are (1.0 = explicitly stated, 0.5 = inferred, 0.0 = not found)
"""

    client = anthropic.Anthropic()
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": extraction_prompt}
        ]
    )
    
    # Parse response
    response_text = message.content[0].text.strip()
    
    # Clean JSON (remove markdown code blocks if present)
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip()
    
    data = json.loads(response_text)
    
    # Build metadata object
    metadata = ContractMetadata()
    metadata.party_client = data.get('party_client')
    metadata.party_vendor = data.get('party_vendor')
    metadata.effective_date = data.get('effective_date')
    metadata.expiration_date = data.get('expiration_date')
    metadata.contract_value = data.get('contract_value')
    metadata.currency = data.get('currency', 'USD')
    metadata.governing_law = data.get('governing_law')
    metadata.contract_type = data.get('contract_type')
    metadata.purpose = data.get('purpose')
    metadata.relationship = data.get('relationship')
    metadata.extraction_confidence = data.get('confidence', {})
    
    return metadata


def _extract_with_regex(full_text: str) -> ContractMetadata:
    """
    Fallback regex-based extraction (original logic).
    """
    metadata = ContractMetadata()
    
    # Party extraction patterns
    party_patterns = [
        r'between\s+([A-Z][A-Za-z\s,\.]+(?:Inc|LLC|Corp|Ltd|Company|LP|LLP))',
        r'(?:"Client"|"Customer"|"Buyer")\s+(?:means|refers to)?\s*([A-Z][A-Za-z\s,\.]+)',
        r'(?:"Vendor"|"Supplier"|"Seller"|"Contractor")\s+(?:means|refers to)?\s*([A-Z][A-Za-z\s,\.]+)',
    ]
    
    for pattern in party_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            party = match.group(1).strip()
            # Remove trailing punctuation
            party = re.sub(r'[,\.\s]+$', '', party)
            
            if any(kw in pattern.lower() for kw in ['client', 'customer', 'buyer']):
                if not metadata.party_client:
                    metadata.party_client = party
                    metadata.extraction_confidence['party_client'] = 0.6
            else:
                if not metadata.party_vendor:
                    metadata.party_vendor = party
                    metadata.extraction_confidence['party_vendor'] = 0.6
    
    # Date extraction
    date_patterns = [
        (r'effective\s+(?:date|as of)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'effective'),
        (r'(?:dated|entered into)(?:\s+as of)?[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'effective'),
        (r'expires?\s+(?:on)?[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'expiration'),
        (r'expiration\s+date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'expiration'),
        (r'term\s+(?:shall\s+)?(?:end|expire)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', 'expiration'),
    ]
    
    for pattern, date_type in date_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            if date_type == 'effective' and not metadata.effective_date:
                metadata.effective_date = match.group(1)
                metadata.extraction_confidence['effective_date'] = 0.7
            elif date_type == 'expiration' and not metadata.expiration_date:
                metadata.expiration_date = match.group(1)
                metadata.extraction_confidence['expiration_date'] = 0.7
    
    # Value extraction
    value_pattern = r'\$\s?([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars)?'
    values = re.findall(value_pattern, full_text)
    if values:
        numeric_values = [float(v.replace(',', '')) for v in values]
        if numeric_values:
            metadata.contract_value = max(numeric_values)
            metadata.extraction_confidence['contract_value'] = 0.5
    
    # Governing law
    law_patterns = [
        r'governed by.*?(?:laws? of|law of)\s+(?:the\s+)?(?:State of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'jurisdiction.*?(?:State of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]
    
    for pattern in law_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            metadata.governing_law = match.group(1)
            metadata.extraction_confidence['governing_law'] = 0.7
            break
    
    # Contract type detection (keyword-based)
    type_keywords = {
        'MSA': ['master service', 'master agreement', 'msa'],
        'SOW': ['statement of work', 'sow', 'work order'],
        'NDA': ['non-disclosure', 'nda', 'confidentiality agreement'],
        'MNDA': ['mutual non-disclosure', 'mnda', 'mutual nda'],
        'Amendment': ['amendment', 'addendum', 'modification'],
        'Purchase Order': ['purchase order', 'po'],
        'Services Agreement': ['services agreement', 'professional services'],
        'License Agreement': ['license agreement', 'software license', 'eula'],
    }
    
    text_lower = full_text.lower()
    for contract_type, keywords in type_keywords.items():
        if any(kw in text_lower for kw in keywords):
            metadata.contract_type = contract_type
            metadata.extraction_confidence['contract_type'] = 0.6
            break
    
    # Purpose detection
    purpose_keywords = {
        'Equipment': ['equipment', 'hardware', 'machinery'],
        'Software': ['software', 'saas', 'application'],
        'Services': ['services', 'support'],
        'Professional Services': ['professional services', 'consulting', 'advisory'],
        'Engineering': ['engineering', 'design'],
        'Installation': ['installation', 'implementation'],
        'Maintenance': ['maintenance', 'support services'],
        'Integration': ['integration', 'system integration'],
    }
    
    for purpose, keywords in purpose_keywords.items():
        if any(kw in text_lower for kw in keywords):
            metadata.purpose = purpose
            metadata.extraction_confidence['purpose'] = 0.5
            break
    
    metadata.relationship = 'Standalone'  # Default
    metadata.extraction_confidence['relationship'] = 0.3
    
    return metadata


# =============================================================================
# UPDATED extract_metadata FUNCTION (replaces original)
# =============================================================================

def extract_metadata(full_text: str, clauses: List[Clause]) -> ContractMetadata:
    """
    Extract contract metadata using AI with regex fallback.
    
    This is the main entry point - replaces the original regex-only version.
    """
    return extract_metadata_ai(full_text, clauses)
