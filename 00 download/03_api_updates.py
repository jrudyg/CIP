# CIP API Updates for Enhanced Metadata
# Version: 2.0
# Date: 2026-01-05
#
# INSTALLATION:
# 1. Run 01_db_migration.sql first
# 2. Replace extraction prompt section in /api/parse-metadata
# 3. Replace /api/verify-metadata endpoint
# 4. Add new /api/contract/<id> PUT endpoint
# 5. Copy 02_extraction_prompt.md to backend/prompts/

# ============================================================================
# UPDATED: /api/parse-metadata - Enhanced extraction (replace lines ~680-765)
# ============================================================================

@app.route('/api/parse-metadata', methods=['POST'])
def parse_metadata():
    """
    Extract contract metadata using Claude AI - Enhanced 16 fields
    """
    logger.info("Parse metadata request received")

    claude_error = validate_claude_available()
    if claude_error:
        return jsonify(claude_error[0]), claude_error[1]

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    contract_id = data.get('contract_id')
    if not contract_id:
        return jsonify({'error': 'contract_id required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT filepath, filename FROM contracts WHERE id = ?", (contract_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': f'Contract {contract_id} not found'}), 404

        filepath = row[0]
        filename = row[1]

        # Get file size
        file_size = None
        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)

        # Read contract text
        from docx import Document
        doc = Document(filepath)
        full_text = "\n".join([p.text for p in doc.paragraphs])

        # Truncate for API
        max_chars = 50000
        contract_text = full_text[:max_chars] if len(full_text) > max_chars else full_text

        # Enhanced extraction prompt
        extraction_prompt = f"""You are a contract analysis expert. Extract metadata from the following contract text.

## Instructions:
1. Extract ALL fields listed below
2. For fields not found in the document, return "NOT_FOUND"
3. For fields not applicable to this contract type, return "N/A"
4. Use exact formats specified for dates and numbers
5. Be precise - do not guess or infer values not explicitly stated

## N/A Rules by Contract Type:
- NDA/MNDA: contract_value=N/A, payment_terms=N/A, warranty_period=N/A
- SOW: auto_renewal=N/A
- Amendment/Addendum: auto_renewal=N/A

## Response Format - Return ONLY valid JSON:
{{
    "title": "string or NOT_FOUND",
    "contract_type": "MSA|SOW|NDA|MNDA|Amendment|Addendum|Service Agreement|License Agreement|Other",
    "effective_date": "YYYY-MM-DD or NOT_FOUND",
    "expiration_date": "YYYY-MM-DD or NOT_FOUND",
    "our_entity": "string or NOT_FOUND",
    "our_role": "Customer|Vendor|Partner|Licensor|Licensee|NOT_FOUND",
    "counterparty": "string or NOT_FOUND",
    "counterparty_role": "Customer|Vendor|Partner|Licensor|Licensee|NOT_FOUND",
    "contract_value": "number or NOT_FOUND or N/A",
    "payment_terms": "string or NOT_FOUND or N/A",
    "liability_cap": "string or NOT_FOUND",
    "auto_renewal": "true|false|NOT_FOUND|N/A",
    "termination_notice_days": "number or NOT_FOUND",
    "governing_law": "string or NOT_FOUND",
    "warranty_period": "string or NOT_FOUND or N/A"
}}

## Contract Text:
{contract_text}"""

        # Call Claude API
        if not claude_client:
            logger.error("Claude client not initialized")
            return jsonify({'error': 'AI service not available'}), 503

        response = claude_client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=2000,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": extraction_prompt
            }]
        )

        response_text = response.content[0].text.strip()
        logger.debug(f"Claude response: {response_text}")

        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

        if json_match:
            metadata = json.loads(json_match.group())
            
            # Add file_size (system-captured, not AI)
            metadata['file_size'] = file_size
            
            # Normalize NOT_FOUND to consistent format
            for key, value in metadata.items():
                if value == "NOT_FOUND" or value == "null" or value is None:
                    metadata[key] = "Not found"
            
            logger.info(f"Metadata extracted successfully for contract {contract_id}")

            # Store parsed_metadata in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE contracts
                SET parsed_metadata = ?,
                    file_size = ?
                WHERE id = ?
            """, (json.dumps(metadata), file_size, contract_id))
            conn.commit()
            conn.close()

            return jsonify({'metadata': metadata}), 200
        else:
            logger.error("Could not parse JSON from Claude response")
            return jsonify({'error': 'Failed to parse metadata from AI response'}), 500

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return jsonify({'error': f'Invalid JSON response from AI: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# UPDATED: /api/verify-metadata - Store all 16 fields (replace lines ~767-850)
# ============================================================================

@app.route('/api/verify-metadata', methods=['POST'])
def verify_metadata():
    """
    Save user-verified metadata to database - Enhanced 16 fields
    """
    logger.info("Verify metadata request received")

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    contract_id = data.get('contract_id')
    metadata = data.get('metadata')

    if not contract_id or not metadata:
        return jsonify({'error': 'contract_id and metadata required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update contract with verified metadata - all 16 fields
        cursor.execute("""
            UPDATE contracts
            SET title = ?,
                contract_type = ?,
                effective_date = ?,
                expiration_date = ?,
                our_entity = ?,
                position = ?,
                counterparty = ?,
                counterparty_role = ?,
                contract_value = ?,
                payment_terms = ?,
                liability_cap = ?,
                auto_renewal = ?,
                termination_notice_days = ?,
                governing_law = ?,
                warranty_period = ?,
                file_size = ?,
                metadata_verified = 1,
                status = 'active',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            metadata.get('title'),
            metadata.get('contract_type'),
            metadata.get('effective_date'),
            metadata.get('expiration_date'),
            metadata.get('our_entity'),
            metadata.get('our_role'),  # stored as 'position' in DB
            metadata.get('counterparty'),
            metadata.get('counterparty_role'),
            metadata.get('contract_value') if metadata.get('contract_value') not in ['Not found', 'N/A'] else None,
            metadata.get('payment_terms'),
            metadata.get('liability_cap'),
            metadata.get('auto_renewal') if metadata.get('auto_renewal') not in ['Not found', 'N/A'] else None,
            metadata.get('termination_notice_days') if metadata.get('termination_notice_days') not in ['Not found', 'N/A'] else None,
            metadata.get('governing_law'),
            metadata.get('warranty_period'),
            metadata.get('file_size'),
            contract_id
        ))

        conn.commit()
        conn.close()

        logger.info(f"Metadata verified and saved for contract {contract_id}")

        return jsonify({
            'success': True,
            'contract_id': contract_id,
            'message': 'Metadata verified and saved'
        }), 200

    except Exception as e:
        logger.error(f"Metadata verification failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# NEW: PUT /api/contract/<id> - Update contract metadata
# ============================================================================

@app.route('/api/contract/<int:contract_id>', methods=['PUT'])
def update_contract(contract_id):
    """
    Update contract metadata fields.
    
    Body: Any subset of editable fields
    Returns: {success: bool, contract: {...}}
    """
    logger.info(f"[UPDATE] Contract {contract_id} update request")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify contract exists
        cursor.execute("SELECT id FROM contracts WHERE id = ?", (contract_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': f'Contract {contract_id} not found'}), 404
        
        # All updatable fields (16 metadata fields)
        updatable_fields = [
            'title', 'contract_type', 'effective_date', 'expiration_date',
            'our_entity', 'position', 'counterparty', 'counterparty_role',
            'contract_value', 'payment_terms', 'liability_cap',
            'auto_renewal', 'termination_notice_days', 'governing_law', 'warranty_period'
        ]
        
        updates = []
        values = []
        
        for field in updatable_fields:
            if field in data:
                value = data[field]
                # Handle special values
                if value in ['Not found', '', None]:
                    if field in ['contract_value', 'termination_notice_days']:
                        value = None
                    elif field == 'auto_renewal':
                        value = None
                # Note: "N/A" is a valid value for auto_renewal, don't convert to None
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            conn.close()
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Add updated_at timestamp
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(contract_id)
        
        sql = f"UPDATE contracts SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, values)
        conn.commit()
        
        # Fetch updated contract
        cursor.execute("""
            SELECT id, title, filename, filepath, contract_type, 
                   effective_date, expiration_date, our_entity, counterparty,
                   position, counterparty_role, contract_value, 
                   payment_terms, liability_cap, auto_renewal, 
                   termination_notice_days, governing_law, warranty_period,
                   file_size, status, risk_level, created_at, updated_at
            FROM contracts WHERE id = ?
        """, (contract_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            contract = {
                'id': row[0],
                'title': row[1],
                'filename': row[2],
                'filepath': row[3],
                'contract_type': row[4],
                'effective_date': row[5],
                'expiration_date': row[6],
                'our_entity': row[7],
                'counterparty': row[8],
                'position': row[9],
                'counterparty_role': row[10],
                'contract_value': row[11],
                'payment_terms': row[12],
                'liability_cap': row[13],
                'auto_renewal': row[14],
                'termination_notice_days': row[15],
                'governing_law': row[16],
                'warranty_period': row[17],
                'file_size': row[18],
                'status': row[19],
                'risk_level': row[20],
                'created_at': row[21],
                'updated_at': row[22]
            }
            
            logger.info(f"[UPDATE] Contract {contract_id} updated successfully")
            return jsonify({'success': True, 'contract': contract}), 200
        
        return jsonify({'error': 'Update failed'}), 500
        
    except Exception as e:
        logger.error(f"[UPDATE] Failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
