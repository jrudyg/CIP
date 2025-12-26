"""
CIP - Get Reports Page
Generate contract analysis reports
v2.0: Simplified - removed PDF/HTML, email, print, schedule, history, stats
"""

import streamlit as st
import datetime
import requests
import sys
sys.path.append('C:\\Users\\jrudy\\CIP\\frontend')
from ui_components import (
    page_header, section_header,
    toast_success, toast_warning, apply_spacing
)
from components.contract_context import (
    init_contract_context,
    get_active_contract,
    get_active_contract_data,
    render_active_contract_header,
    render_recent_contracts_widget
)
from theme_system import apply_theme, inject_cip_logo
from cip_components import document_viewer

# Configuration
DB_PATH = "C:\\Users\\jrudy\\CIP\\data\\contracts.db"

# Page config
st.set_page_config(page_title="Get Reports", page_icon="📑", layout="wide")
apply_theme()
apply_spacing()

# Inject centralized dark theme
from components.theme import inject_dark_theme
inject_dark_theme()

API_BASE = "http://localhost:5000/api"

# Sidebar - navigation only
with st.sidebar:
    inject_cip_logo()

# Initialize contract context
init_contract_context()

page_header("📑 Get Reports", "Generate comprehensive contract analysis reports")
render_active_contract_header()

# Auto-load active contract from context
active_id = get_active_contract()
active_data = get_active_contract_data()

# Session state for report preview
if 'report_preview_content' not in st.session_state:
    st.session_state.report_preview_content = None
if 'report_metadata' not in st.session_state:
    st.session_state.report_metadata = None

# Max-width container to prevent page stretching
st.markdown("""
<style>
    .main .block-container {
        max-width: 1200px;
        padding-left: 2rem;
        padding-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Main content in two columns
col_left, col_right = st.columns([1, 1])

with col_left:
    # Report Generator Section
    section_header("Report Generator", "📋")

    if active_id:
        st.info(f"📋 Active Contract: #{active_id} - {active_data.get('title', 'Unknown')}")

    report_type = st.selectbox(
        "Select Report Type",
        [
            "Contract Analysis Report",
            "Version Comparison Report",
            "Risk Assessment Report",
            "Portfolio Summary Report",
            "Negotiation Strategy Report",
            "Compliance Audit Report"
        ],
        key="report_type_selector"
    )

    # Contract selection for specific report types
    if report_type in ["Contract Analysis Report", "Version Comparison Report", "Risk Assessment Report"]:
        contract_selection = st.selectbox(
            "Select Contract",
            ["No contracts available"] if not active_id else [f"#{active_id} - {active_data.get('title', 'Unknown')}"],
            key="contract_selector"
        )
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            date_from = st.date_input(
                "From Date",
                value=datetime.date.today() - datetime.timedelta(days=30),
                key="date_from"
            )
        with col_b:
            date_to = st.date_input("To Date", value=datetime.date.today(), key="date_to")

    # Report sections selection
    st.markdown("**Include Sections**")
    sections = st.multiselect(
        "Select sections",
        [
            "Overview & Metadata",
            "Risk Assessment",
            "Key Clauses",
            "Compliance Check",
            "Recommendations",
            "Appendices",
            "Change Log (for comparisons)"
        ],
        default=["Overview & Metadata", "Risk Assessment", "Key Clauses"],
        key="report_sections"
    )

    st.markdown("---")

    # Export Format (DOCX and XLSX only)
    section_header("Export Format", "📤")

    output_format = st.radio(
        "Format",
        ["DOCX", "XLSX"],
        key="output_format",
        horizontal=True
    )

    # Generate Report button
    if st.button("🚀 Generate Report", type="primary", use_container_width=True, key="generate_btn"):
        with st.spinner("Generating report..."):
            try:
                report_type_mapping = {
                    "Contract Analysis Report": "risk_review",
                    "Version Comparison Report": "comparison",
                    "Risk Assessment Report": "risk_review",
                    "Negotiation Strategy Report": "redline",
                    "Portfolio Summary Report": "risk_review",
                    "Compliance Audit Report": "risk_review"
                }

                api_report_type = report_type_mapping.get(report_type, "risk_review")
                contract_id = active_id if active_id else None

                if not contract_id:
                    st.error("❌ Please select a contract first")
                else:
                    report_params = {
                        "contract_id": contract_id,
                        "report_type": api_report_type,
                        "output_format": output_format.lower(),
                        "parameters": {
                            "our_entity": active_data.get('our_entity', 'Our Company'),
                            "counterparty": active_data.get('counterparty', 'Counterparty'),
                            "position": active_data.get('position', 'Party A'),
                            "include_sections": sections
                        }
                    }

                    response = requests.post(
                        f"{API_BASE}/reports/generate",
                        json=report_params,
                        timeout=60
                    )

                    if response.status_code == 200:
                        report_data = response.json()
                        st.success("✅ Report generated!")

                        # Store metadata
                        st.session_state.report_metadata = {
                            'generated_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'report_id': report_data.get('report_id', 'N/A'),
                            'page_count': report_data.get('page_count', 'N/A'),
                            'contract_name': active_data.get('title', 'Unknown'),
                            'download_url': report_data.get('download_url', None)
                        }

                        # Store preview content
                        st.session_state.report_preview_content = report_data.get('preview', 'Report generated successfully. Click download to get the full document.')

                        st.rerun()
                    else:
                        error_msg = response.json().get('error', 'Unknown error') if response.headers.get('content-type') == 'application/json' else response.text
                        st.error(f"❌ {error_msg}")

            except requests.exceptions.Timeout:
                st.error("⏱️ Report generation timed out")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {str(e)}")
            except Exception as e:
                st.error(f"❌ {str(e)}")

with col_right:
    # Report Preview Section
    section_header("Report Preview", "👁️")

    preview_content = st.session_state.report_preview_content
    metadata = st.session_state.report_metadata

    if preview_content:
        # Show metadata
        if metadata:
            st.markdown(f"**Generated:** {metadata.get('generated_date', 'N/A')} | **Report ID:** {metadata.get('report_id', 'N/A')}")

        # Document viewer
        document_viewer(
            content=preview_content,
            height=350,
            highlights=[
                {"text": "HIGH RISK", "color": "#EF4444"},
                {"text": "MEDIUM RISK", "color": "#F97316"},
                {"text": "LOW RISK", "color": "#22C55E"},
            ]
        )

        # Download button
        st.markdown("---")
        if st.button("📥 Download Report", type="primary", use_container_width=True, key="download_btn"):
            if metadata and metadata.get('download_url'):
                toast_success(f"Downloading {output_format} report...")
            else:
                toast_success(f"Preparing {output_format} download...")
    else:
        st.info("Report preview will appear here after generation")

        with st.expander("📊 Executive Summary"):
            st.markdown("Executive summary content will appear here")

        with st.expander("⚠️ Risk Assessment"):
            st.markdown("Risk assessment details will appear here")

        with st.expander("📋 Detailed Analysis"):
            st.markdown("Detailed analysis will appear here")
