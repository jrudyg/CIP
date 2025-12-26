"""
CIP - Get Reports Page
Generate contract analysis reports
v3.0: STAB Phase 3 refactor
- Uses page_wrapper.render_page
- Centralized API config (config.api.API_BASE_URL)
- Global CSS overrides via theme_system.overrides
"""

import streamlit as st
import datetime
import requests
import sys

# Ensure CIP frontend modules are importable
sys.path.append('C:\\Users\\jrudy\\CIP\\frontend')

from ui_components import (
    page_header,
    section_header,
    toast_success,
    toast_warning,
    apply_spacing,
)
from components.contract_context import (
    get_active_contract,
    get_active_contract_data,
    render_active_contract_header,
)
from theme_system import apply_theme  # still used for spacing flow
from cip_components import document_viewer
from page_wrapper import render_page
from config.api import API_BASE_URL, API_TIMEOUT_DEFAULT

def reports_content(**kwargs) -> None:
    """
    Main content for the Get Reports page.
    Wrapper is responsible for:
    - page_config
    - theme + dark theme
    - CSS overrides
    - sidebar logo
    - contract context init
    - system health (api_healthy, db_healthy, ai_healthy)
    """
    apply_spacing()

    page_header("📑 Get Reports", "Generate comprehensive contract analysis reports")
    render_active_contract_header()

    active_id = get_active_contract()
    active_data = get_active_contract_data()

    if "report_preview_content" not in st.session_state:
        st.session_state["report_preview_content"] = None
    if "report_metadata" not in st.session_state:
        st.session_state["report_metadata"] = None

    col_left, col_right = st.columns([1, 1])

    with col_left:
        section_header("Report Generator", "📋")

        if active_id:
            st.info(
                f"📋 Active Contract: #{active_id} - "
                f"{active_data.get('title', 'Unknown')}"
            )

        report_type = st.selectbox(
            "Select Report Type",
            [
                "Contract Analysis Report",
                "Version Comparison Report",
                "Risk Assessment Report",
                "Portfolio Summary Report",
                "Negotiation Strategy Report",
                "Compliance Audit Report",
            ],
            key="report_type_selector",
        )

        if report_type in [
            "Contract Analysis Report",
            "Version Comparison Report",
            "Risk Assessment Report",
        ]:
            contract_selection = st.selectbox(
                "Select Contract",
                ["No contracts available"]
                if not active_id
                else [
                    f"#{active_id} - "
                    f"{active_data.get('title', 'Unknown')}"
                ],
                key="contract_selector",
            )
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                date_from = st.date_input(
                    "From Date",
                    value=datetime.date.today()
                    - datetime.timedelta(days=30),
                    key="date_from",
                )
            with col_b:
                date_to = st.date_input(
                    "To Date",
                    value=datetime.date.today(),
                    key="date_to",
                )

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
                "Change Log (for comparisons)",
            ],
            default=[
                "Overview & Metadata",
                "Risk Assessment",
                "Key Clauses",
            ],
            key="report_sections",
        )

        st.markdown("---")

        section_header("Export Format", "📤")

        output_format = st.radio(
            "Format",
            ["DOCX", "XLSX"],
            key="output_format",
            horizontal=True,
        )

        if st.button(
            "🚀 Generate Report",
            type="primary",
            use_container_width=True,
            key="generate_btn",
        ):
            with st.spinner("Generating report..."):
                try:
                    report_type_mapping = {
                        "Contract Analysis Report": "risk_review",
                        "Version Comparison Report": "comparison",
                        "Risk Assessment Report": "risk_review",
                        "Negotiation Strategy Report": "redline",
                        "Portfolio Summary Report": "risk_review",
                        "Compliance Audit Report": "risk_review",
                    }

                    api_report_type = report_type_mapping.get(
                        report_type, "risk_review"
                    )
                    contract_id = active_id if active_id else None

                    if not contract_id:
                        st.error("❌ Please select a contract first")
                    else:
                        report_params = {
                            "contract_id": contract_id,
                            "report_type": api_report_type,
                            "output_format": output_format.lower(),
                            "parameters": {
                                "our_entity": active_data.get(
                                    "our_entity", "Our Company"
                                ),
                                "counterparty": active_data.get(
                                    "counterparty", "Counterparty"
                                ),
                                "position": active_data.get(
                                    "position", "Party A"
                                ),
                                "include_sections": sections,
                            },
                        }

                        response = requests.post(
                            f"{API_BASE_URL}/reports/generate",
                            json=report_params,
                            timeout=max(API_TIMEOUT_DEFAULT, 60),
                        )

                        if response.status_code == 200:
                            report_data = response.json()
                            st.success("✅ Report generated!")

                            st.session_state["report_metadata"] = {
                                "generated_date": datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                ),
                                "report_id": report_data.get(
                                    "report_id", "N/A"
                                ),
                                "page_count": report_data.get(
                                    "page_count", "N/A"
                                ),
                                "contract_name": active_data.get(
                                    "title", "Unknown"
                                ),
                                "download_url": report_data.get(
                                    "download_url", None
                                ),
                            }

                            st.session_state["report_preview_content"] = report_data.get(
                                "preview",
                                (
                                    "Report generated successfully. "
                                    "Click download to get the full document."
                                ),
                            )

                            st.rerun()

                        else:
                            if (
                                response.headers.get("content-type")
                                == "application/json"
                            ):
                                error_msg = response.json().get(
                                    "error", "Unknown error"
                                )
                            else:
                                error_msg = response.text
                            st.error(f"❌ {error_msg}")

                except requests.exceptions.Timeout:
                    st.error("⏱️ Report generation timed out")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    with col_right:
        section_header("Report Preview", "👁️")

        preview_content = st.session_state["report_preview_content"]
        metadata = st.session_state["report_metadata"]

        if preview_content:
            if metadata:
                st.markdown(
                    f"**Generated:** {metadata.get('generated_date', 'N/A')} "
                    f"| **Report ID:** {metadata.get('report_id', 'N/A')}"
                )

            document_viewer(
                content=preview_content,
                height=350,
                highlights=[
                    {"text": "HIGH RISK", "color": "#EF4444"},
                    {"text": "MEDIUM RISK", "color": "#F97316"},
                    {"text": "LOW RISK", "color": "#22C55E"},
                ],
            )

            st.markdown("---")
            if st.button(
                "📥 Download Report",
                type="primary",
                use_container_width=True,
                key="download_btn",
            ):
                if metadata and metadata.get("download_url"):
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
                st.markdown("Detailed analysis content will appear here")


def main() -> None:
    render_page(
        page_title="Get Reports",
        page_icon="📑",
        layout="wide",
        content_fn=reports_content,
    )


if __name__ == "__main__":
    main()
