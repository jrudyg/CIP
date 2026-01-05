# pages/3_Intelligent_Intake.py
"""
CIP Intelligent Intake v5.1 - CCE-Plus Integration
- Direct integration with intake_engine.py
- Automated clause extraction and risk scoring
- Workflow gate integration
- Session state persistence for form stability
"""

import streamlit as st
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import tempfile

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from components.page_wrapper import init_page, page_header, content_container

# ============================================================================
# PAGE SETUP
# ============================================================================

init_page("Contract Intake", "📄")

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_intake_state():
    """Initialize session state for intake form persistence."""
    if 'intake_result' not in st.session_state:
        st.session_state.intake_result = None
    if 'intake_processed' not in st.session_state:
        st.session_state.intake_processed = False
    if 'intake_db_path' not in st.session_state:
        st.session_state.intake_db_path = None
    if 'intake_filename' not in st.session_state:
        st.session_state.intake_filename = None

def clear_intake_state():
    """Clear intake session state for fresh start."""
    st.session_state.intake_result = None
    st.session_state.intake_processed = False
    st.session_state.intake_db_path = None
    st.session_state.intake_filename = None

# Initialize state
init_intake_state()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_contract_metadata(
    contract_id: int,
    db_path: str,
    party_client: str = None,
    party_vendor: str = None,
    governing_law: str = None,
    contract_type: str = None,
    purpose: str = None,
    relationship: str = None,
    counterparty_type: str = None
):
    """Update contract with user-confirmed metadata and mark intake COMPLETE."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE contracts SET
            party_client = ?,
            party_vendor = ?,
            governing_law = ?,
            contract_type = ?,
            contract_purpose = ?,
            party_relationship = ?,
            counterparty_type = ?,
            intake_status = 'COMPLETE',
            risk_status = 'PENDING'
        WHERE id = ?
    """, (
        party_client or None,
        party_vendor or None,
        governing_law or None,
        contract_type or None,
        purpose or None,
        relationship or None,
        counterparty_type or None,
        contract_id
    ))

    conn.commit()
    conn.close()


def set_intake_pending(contract_id: int, db_path: str):
    """Set intake status back to PENDING to await user confirmation."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE contracts
            SET intake_status = 'PENDING',
                risk_status = 'BLOCKED'
            WHERE id = ?
        """, (contract_id,))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.close()
        return False


# ============================================================================
# MAIN INTAKE INTERFACE
# ============================================================================

page_header(
    "Contract Intake",
    "Upload and process contracts with automated risk scoring"
)

with content_container():
    st.markdown("""
    ### Upload Contract

    The system will automatically:
    - Extract verbatim text and clauses
    - Score all clauses for risk (CCE-Plus)
    - Extract key metadata
    - Create intake record
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Contract Document",
        type=['docx', 'pdf', 'txt'],
        help="Upload a contract in DOCX, PDF, or TXT format",
        key="intake_file_uploader"
    )

    # Check if file changed - reset state if so
    if uploaded_file:
        current_filename = uploaded_file.name
        if st.session_state.intake_filename and st.session_state.intake_filename != current_filename:
            # File changed - clear previous processing state
            clear_intake_state()
        st.session_state.intake_filename = current_filename
    else:
        # No file - clear state
        if st.session_state.intake_processed:
            clear_intake_state()

    # Show file info and process button only if file uploaded and not yet processed
    if uploaded_file and not st.session_state.intake_processed:
        st.info(f"📄 File: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")

        # Process button
        if st.button("🚀 Process Contract", type="primary", use_container_width=True, key="btn_process"):

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                temp_path = tmp_file.name

            try:
                # Import and run intake engine
                with st.spinner("🔄 Processing intake with CCE-Plus risk scoring..."):
                    try:
                        from intake_engine import process_intake

                        # Get database path
                        db_path = str(backend_path.parent / "data" / "contracts.db")

                        # Process (without embeddings for speed)
                        result = process_intake(
                            file_path=temp_path,
                            db_path=db_path,
                            embed=False,
                            verbose=False,
                            original_filename=uploaded_file.name
                        )

                        if result.success:
                            # Set intake to PENDING to await user confirmation
                            set_intake_pending(result.contract_id, db_path)

                            # Store in session state for persistence
                            st.session_state.intake_result = result
                            st.session_state.intake_processed = True
                            st.session_state.intake_db_path = db_path

                            # Trigger rerun to show form
                            st.rerun()

                        else:
                            # Error
                            st.error("❌ Intake failed")
                            if result.errors:
                                st.error("\n".join(result.errors))

                    except ImportError as e:
                        st.error(f"❌ Could not import intake_engine: {e}")
                        st.info("Make sure intake_engine.py is in the backend directory")

                    except Exception as e:
                        st.error(f"❌ Error during processing: {e}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass

    # ========================================================================
    # METADATA CONFIRMATION FORM - Rendered from session state (persists!)
    # ========================================================================
    
    if st.session_state.intake_processed and st.session_state.intake_result:
        result = st.session_state.intake_result
        metadata = result.metadata
        db_path = st.session_state.intake_db_path

        # Show file info
        st.info(f"📄 File: **{st.session_state.intake_filename}**")

        # Success notification
        st.success(f"✅ Document processed! {result.clause_count} clauses extracted.")

        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Contract ID", result.contract_id)
        with col2:
            st.metric("Clauses Extracted", result.clause_count)
        with col3:
            avg_risk = result.risk_summary.get('avg_score', 0)
            risk_level = (
                "🔴 CRITICAL" if avg_risk >= 9.0 else
                "🟠 HIGH" if avg_risk >= 7.0 else
                "🟡 MEDIUM" if avg_risk >= 5.0 else
                "🟢 LOW"
            )
            st.metric("Overall Risk", risk_level)

        # Metadata confirmation form
        st.markdown("---")
        st.subheader("📝 Confirm Contract Metadata")
        st.info("Please verify and complete the extracted information:")

        # Editable fields with extracted values as defaults
        col_left, col_right = st.columns(2)

        with col_left:
            party = st.text_input(
                "Party (Client)",
                value=metadata.party_client or "",
                help="The organization you represent",
                key="form_party"
            )
            counterparty = st.text_input(
                "CounterParty (Vendor)",
                value=metadata.party_vendor or "",
                help="The other party to the contract",
                key="form_counterparty"
            )
            governing_law = st.text_input(
                "Governing Law",
                value=metadata.governing_law or "",
                help="Jurisdiction (e.g., Delaware, New York)",
                key="form_governing_law"
            )

        with col_right:
            contract_type = st.selectbox(
                "Contract Type",
                options=["", "MSA", "IPA", "MNDA", "NDA", "SOW", "EULA",
                         "Amendment", "Purchase Order", "Services Agreement",
                         "License Agreement", "Other"],
                index=0,
                help="Type of agreement",
                key="form_contract_type"
            )

            purpose = st.selectbox(
                "Purpose",
                options=["", "Equipment", "Services", "Professional Services",
                         "Engineering", "Installation", "Staffing", "Transportation",
                         "Maintenance", "Software", "Consulting", "Integration", "Other"],
                index=0,
                help="Primary purpose of the contract",
                key="form_purpose"
            )

            doc_relationship = st.selectbox(
                "Document Relationship",
                options=["", "Standalone", "Parent", "Child", "Amendment", "Version",
                         "Renewal", "Supersedes", "Flow-Down", "Back-to-Back"],
                index=0,
                help="How this contract relates to other contracts in your portfolio",
                key="form_doc_relationship"
            )

            counterparty_type = st.selectbox(
                "Counterparty Type",
                options=["", "Client", "OEM/Manufacturer", "Subcontractor",
                         "Software Vendor", "Engineering Firm", "Consultant",
                         "Distributor", "Partner/JV", "Other"],
                index=0,
                help="Your relationship with the other party (downstream=Client, upstream=Vendor)",
                key="form_counterparty_type"
            )

        # Confirmation button
        st.markdown("---")
        
        col_confirm, col_cancel = st.columns([3, 1])
        
        with col_confirm:
            if st.button("✅ Confirm & Complete Intake", type="primary", use_container_width=True, key="btn_confirm"):
                update_contract_metadata(
                    contract_id=result.contract_id,
                    db_path=db_path,
                    party_client=party,
                    party_vendor=counterparty,
                    governing_law=governing_law,
                    contract_type=contract_type,
                    purpose=purpose,
                    relationship=doc_relationship,
                    counterparty_type=counterparty_type
                )
                st.success("✅ Intake complete! Risk Analysis now unlocked.")
                st.balloons()
                # Clear state after successful completion
                clear_intake_state()
                st.rerun()
        
        with col_cancel:
            if st.button("🔄 Reset", type="secondary", use_container_width=True, key="btn_reset"):
                clear_intake_state()
                st.rerun()

    # Instructions
    st.markdown("---")
    st.markdown("### 📖 How It Works")

    with st.expander("Intake Process Details"):
        st.markdown("""
        **Automated Intake Pipeline:**

        1. **Document Parsing**
           - Extracts verbatim text from DOCX/PDF
           - Preserves formatting and structure

        2. **Clause Segmentation**
           - Identifies contract sections
           - Splits into analyzable clauses

        3. **Risk Scoring (CCE-Plus)**
           - Severity: Business impact assessment
           - Complexity: Legal complexity evaluation
           - Impact: Overall risk calculation
           - Formula: `RiskScore = (Severity × 0.3) + (Complexity × 0.3) + (Impact × 0.4)`

        4. **Statutory Detection**
           - Checks against Delaware UCC (§ 2-719, § 2-302, § 2-717)
           - Identifies limitation of remedy issues
           - Flags unconscionability concerns

        5. **Metadata Extraction**
           - Parties, dates, values
           - Public company lookup (if applicable)
           - Contract classification

        6. **Workflow Initialization**
           - Marks intake as COMPLETE
           - Unlocks risk analysis stage
           - Initializes workflow gates
        """)

    # Workflow status
    st.markdown("---")
    st.markdown("### 🔄 Workflow Stages")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**1. Intake**")
        st.markdown("📄 Upload & Process")
        st.caption("Current stage")

    with col2:
        st.markdown("**2. Risk Analysis**")
        st.markdown("🔒 Locked")
        st.caption("Unlocks after intake")

    with col3:
        st.markdown("**3. Redlines**")
        st.markdown("🔒 Locked")
        st.caption("Unlocks after risk")

    with col4:
        st.markdown("**4. Compare**")
        st.markdown("🔒 Locked")
        st.caption("Unlocks after redlines")
