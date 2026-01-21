# ADD TO api.py - Contract Update Endpoint
# Insert after line ~1985 (after GET /api/contract/<int:contract_id>)

@app.route('/api/contract/<int:contract_id>', methods=['PUT'])
def update_contract(contract_id):
    """
    Update contract metadata fields.
    
    Body: {
        title: string,
        contract_type: string,
        effective_date: string (YYYY-MM-DD),
        expiration_date: string (YYYY-MM-DD),
        our_entity: string,
        counterparty: string,
        position: string,
        contract_value: float|null,
        auto_renewal: bool|null,
        termination_notice_days: int|null
    }
    
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
        
        # Build dynamic UPDATE statement for provided fields
        updatable_fields = [
            'title', 'contract_type', 'effective_date', 'expiration_date',
            'our_entity', 'counterparty', 'position', 'contract_value',
            'auto_renewal', 'termination_notice_days'
        ]
        
        updates = []
        values = []
        
        for field in updatable_fields:
            if field in data:
                updates.append(f"{field} = ?")
                values.append(data[field])
        
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
                   position, contract_value, auto_renewal, termination_notice_days,
                   status, risk_level, created_at, updated_at
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
                'contract_value': row[10],
                'auto_renewal': row[11],
                'termination_notice_days': row[12],
                'status': row[13],
                'risk_level': row[14],
                'created_at': row[15],
                'updated_at': row[16]
            }
            
            logger.info(f"[UPDATE] Contract {contract_id} updated successfully")
            return jsonify({'success': True, 'contract': contract}), 200
        
        return jsonify({'error': 'Update failed'}), 500
        
    except Exception as e:
        logger.error(f"[UPDATE] Failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
