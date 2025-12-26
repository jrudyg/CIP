"""
CIP API Additions for Intelligent Intake
Add these routes to backend/api.py

INSTALLATION:
1. Copy these functions into api.py
2. Add import at top: from extraction_service import extract_contract_metadata, find_related_contracts
3. Copy extraction_service.py to backend/
4. Copy extraction_prompt.md to backend/prompts/

REQUIRED DB COLUMNS (verified against schema 12/15/25):
- id, title, filename, filepath, contract_type, contract_purpose
- our_entity, counterparty, party_relationship, leverage
- parent_id, status, parsed_metadata, created_at
"""

# ============================================================================
# INTELLIGENT INTAKE ENDPOINTS
# ============================================================================

# Add this import at top of api.py:
# from extraction_service import extract_contract_metadata, find_related_contracts, check_dependencies

@app.route('/api/intake/upload', methods=['POST'])
def intake_upload():
    """
    Upload a contract file for intelligent intake.
    
    Accepts: .docx files only
    Returns: {file_id, filename, status}
    """
    logger.info("[INTAKE] Upload request received")
    
    try:
        # Validate file present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type (.docx only for now)
        if not file.filename.lower().endswith('.docx'):
            return jsonify({
                'error': 'Unsupported file type',
                'details': 'Only .docx files are currently supported',
                'filename': file.filename
            }), 400
        
        # Save file
        file_path = save_uploaded_file(file)
        
        # Generate a simple file_id (timestamp-based)
        import hashlib
        file_id = hashlib.md5(str(file_path).encode()).hexdigest()[:12]
        
        logger.info(f"[INTAKE] File uploaded: {file_path} (ID: {file_id})")
        
        return jsonify({
            'status': 'success',
            'file_id': file_id,
            'filename': file.filename,
            'file_path': str(file_path)
        }), 200
        
    except Exception as e:
        logger.error(f"[INTAKE] Upload failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/intake/extract', methods=['POST'])
def intake_extract():
    """
    Extract metadata from uploaded contract.
    
    Body: {file_path: string}
    Returns: {extraction: {...}, related_contracts: [...]}
    """
    logger.info("[INTAKE] Extract request received")
    
    try:
        # Import extraction service
        from extraction_service import extract_contract_metadata, find_related_contracts, check_dependencies
        
        # Check dependencies
        deps = check_dependencies()
        if not deps.get('python-docx'):
            return jsonify({
                'error': 'python-docx not installed',
                'action': 'Run: pip install python-docx'
            }), 503
        
        if not deps.get('api_key_configured'):
            return jsonify({
                'error': 'ANTHROPIC_API_KEY not configured',
                'action': 'Set ANTHROPIC_API_KEY in .env file'
            }), 503
        
        # Get file path from request
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path required'}), 400
        
        file_path = Path(data['file_path'])
        
        if not file_path.exists():
            return jsonify({'error': f'File not found: {file_path}'}), 404
        
        # Run extraction
        logger.info(f"[INTAKE] Extracting metadata from: {file_path}")
        result = extract_contract_metadata(file_path)
        
        # Find related contracts if we have party names
        related = []
        if result.success and result.parties:
            related = find_related_contracts(result.parties)
            logger.info(f"[INTAKE] Found {len(related)} related contracts")
        
        return jsonify({
            'status': 'success' if result.success else 'partial',
            'extraction': result.to_dict(),
            'related_contracts': related
        }), 200
        
    except ImportError as e:
        logger.error(f"[INTAKE] Import error: {e}")
        return jsonify({
            'error': 'Extraction service not available',
            'details': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"[INTAKE] Extract failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/intake/store', methods=['POST'])
def intake_store():
    """
    Store confirmed contract metadata in database.
    
    Body: {
        file_path: string,
        title: string,
        contract_type: string,
        purpose: string,
        party: string,
        counterparty: string,
        orientation: string,
        leverage: string,
        related_contract_id: int|null,
        full_text: string (optional)
    }
    
    Returns: {contract_id: int, suggested_next: string}
    """
    logger.info("[INTAKE] Store request received")
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Required fields
        required = ['file_path', 'title', 'contract_type', 'party', 'counterparty', 'orientation']
        missing = [f for f in required if not data.get(f)]
        
        if missing:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing
            }), 400
        
        # Extract filename from path
        file_path = Path(data['file_path'])
        filename = file_path.name
        
        # Get full text if not provided
        full_text = data.get('full_text', '')
        if not full_text and file_path.exists():
            try:
                from extraction_service import extract_text_from_docx
                full_text, _ = extract_text_from_docx(file_path)
            except:
                pass
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Column names matched to actual schema (verified 12/15/25)
        cursor.execute("""
            INSERT INTO contracts (
                filename, filepath, title, contract_type, contract_purpose,
                our_entity, counterparty, party_relationship, leverage,
                parent_id, status, parsed_metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            filename,
            str(file_path),
            data['title'],
            data['contract_type'],
            data.get('purpose'),
            data['party'],           # Maps to 'our_entity' column
            data['counterparty'],
            data['orientation'],     # Maps to 'party_relationship' (CUSTOMER/VENDOR)
            data.get('leverage'),
            data.get('related_contract_id'),  # Maps to 'parent_id'
            'intake',                # Initial status per schema default
            full_text[:50000] if full_text else None  # Store in parsed_metadata
        ))
        
        contract_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"[INTAKE] Contract stored: ID={contract_id}, Title={data['title']}")
        
        # Determine suggested next step
        suggested_next = "Risk Analysis"
        if data['contract_type'] == 'Amendment':
            suggested_next = "Compare Versions"
        
        return jsonify({
            'status': 'success',
            'contract_id': contract_id,
            'suggested_next': suggested_next
        }), 201
        
    except sqlite3.IntegrityError as e:
        logger.error(f"[INTAKE] Database integrity error: {e}")
        return jsonify({'error': 'Database constraint violation', 'details': str(e)}), 409
        
    except Exception as e:
        logger.error(f"[INTAKE] Store failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/intake/status', methods=['GET'])
def intake_status():
    """
    Check intake service status and dependencies.
    
    Returns: {ready: bool, dependencies: {...}}
    """
    try:
        from extraction_service import check_dependencies
        deps = check_dependencies()
        
        ready = all(deps.values())
        
        return jsonify({
            'ready': ready,
            'dependencies': deps
        }), 200 if ready else 503
        
    except ImportError:
        return jsonify({
            'ready': False,
            'error': 'extraction_service not found'
        }), 503


# ============================================================================
# INSTALLATION INSTRUCTIONS
# ============================================================================
"""
To add these endpoints to your existing api.py:

1. Add import near top of file (after other imports):
   
   from extraction_service import (
       extract_contract_metadata,
       find_related_contracts,
       check_dependencies,
       extract_text_from_docx
   )

2. Copy the 4 route functions above into api.py (before the __main__ block)

3. Ensure these files exist:
   - backend/extraction_service.py
   - backend/prompts/extraction_prompt.md

4. Install dependencies:
   pip install python-docx

5. Verify DB schema includes required columns:
   sqlite3 data/contracts.db ".schema contracts"
   
   Required columns:
   - filename, file_path, title, contract_type, purpose
   - party, counterparty, position, leverage
   - related_contract_id, status, full_text, created_at

6. Test endpoints:
   curl -X GET http://localhost:5000/api/intake/status
"""
