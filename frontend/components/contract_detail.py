"""
Contract Detail Panel
Expandable panel with tabs for contract details, versions, relationships, history
"""
import streamlit as st
import requests

API_BASE = "http://localhost:5000/api"


def render_contract_detail(contract_id: int):
    """Render expandable contract detail panel with actions"""
    try:
        contract_resp = requests.get(f"{API_BASE}/contract/{contract_id}", timeout=5)
        if not contract_resp.ok:
            st.error(f"Failed to load contract details: {contract_resp.status_code}")
            return
        contract = contract_resp.json()
    except Exception as e:
        st.error(f"Failed to load contract details: {e}")
        return

    with st.expander(f"📋 Contract Details: {contract.get('title', 'Unknown')}", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs(["Details", "Versions", "Relationships", "History"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                **Type:** {contract.get('contract_type', 'N/A')}
                **Status:** {contract.get('status', 'N/A')}
                **Counterparty:** {contract.get('counterparty', 'N/A')}
                **Value:** ${contract.get('contract_value', 0):,.2f}
                """)
            with col2:
                st.markdown(f"""
                **Risk Level:** {contract.get('risk_level', 'N/A')}
                **Effective Date:** {contract.get('effective_date', 'N/A')}
                **Expiration:** {contract.get('expiration_date', 'N/A')}
                **Role:** {contract.get('contract_role', 'N/A')}
                """)

        with tab2:
            try:
                versions_resp = requests.get(f"{API_BASE}/contract/{contract_id}/versions", timeout=5)
                if versions_resp.ok:
                    versions = versions_resp.json()
                    if versions:
                        for v in versions:
                            st.markdown(f"• **v{v.get('version_number', '?')}** - {v.get('title', 'Unknown')} ({v.get('status', 'N/A')})")
                    else:
                        st.info("No version history")
                else:
                    st.info("Version history unavailable")
            except:
                st.info("Version history unavailable")

        with tab3:
            try:
                rels_resp = requests.get(f"{API_BASE}/contract/{contract_id}/relationships", timeout=5)
                if rels_resp.ok:
                    rels = rels_resp.json()
                    if rels.get('parent'):
                        st.markdown(f"**Parent:** {rels['parent'].get('title', 'Unknown')}")
                    if rels.get('children'):
                        st.markdown("**Children:**")
                        for child in rels['children']:
                            st.markdown(f"  • {child.get('title', 'Unknown')} ({child.get('relationship_type', 'N/A')})")
                    if rels.get('amendments'):
                        st.markdown("**Amendments:**")
                        for amend in rels['amendments']:
                            st.markdown(f"  • {amend.get('title', 'Unknown')} - {amend.get('status', 'N/A')}")
                    if not any([rels.get('parent'), rels.get('children'), rels.get('amendments')]):
                        st.info("No relationships")
                else:
                    st.info("Relationships unavailable")
            except:
                st.info("Relationships unavailable")

        with tab4:
            try:
                history_resp = requests.get(f"{API_BASE}/contract/{contract_id}/history", timeout=5)
                if history_resp.ok:
                    history = history_resp.json()
                    if history:
                        for event in history:
                            st.markdown(f"• {event.get('timestamp', 'N/A')} - {event.get('action', 'N/A')}")
                            if event.get('details'):
                                st.markdown(f"  _{event['details']}_")
                    else:
                        st.info("No history")
                else:
                    st.info("History unavailable")
            except:
                st.info("History unavailable")

        # Action buttons
        st.divider()
        st.markdown("**Actions:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔍", key=f"analyze_{contract_id}", help="Analyze contract", use_container_width=True):
                st.session_state.pending_action = ('analyze', contract_id)
                st.switch_page("pages/4_🔍_Risk_Analysis.py")
        with col2:
            if st.button("📝", key=f"redline_{contract_id}", help="Redline review", use_container_width=True):
                st.session_state.pending_action = ('redline', contract_id)
                st.switch_page("pages/5_📝_Redline_Reviews.py")
        with col3:
            if st.button("⚖️", key=f"compare_{contract_id}", help="Compare versions", use_container_width=True):
                st.session_state.pending_action = ('compare', contract_id)
                st.switch_page("pages/6_⚖️_Compare_Versions.py")
        with col4:
            if st.button("📄", key=f"export_{contract_id}", help="Export contract", use_container_width=True):
                st.info("Export feature coming soon")
