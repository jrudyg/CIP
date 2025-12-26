# pages/4_Risk_Analysis.py
"""
CIP Risk Analysis v4.3
- Category risk table (clickable to filter)
- Comprehensive analysis (all clauses reviewed)
- Renamed "Business Impact" to "RATIONALE"
- Single-column expander layout
- Improved redline display (full width, proper formatting)
- Only > LOW risk findings displayed
"""

import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from components.page_wrapper import (
    init_page,
    page_header,
    content_container
)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:5000/api"

SEVERITY_CONFIG = {
    "dealbreaker": {"icon": "🔴", "color": "#EF4444", "bg": "rgba(239,68,68,0.15)", "label": "Dealbreaker", "order": 0},
    "critical": {"icon": "🟠", "color": "#F97316", "bg": "rgba(249,115,22,0.15)", "label": "Critical", "order": 1},
    "important": {"icon": "🟡", "color": "#EAB308", "bg": "rgba(234,179,8,0.15)", "label": "Important", "order": 2},
    "standard": {"icon": "🟢", "color": "#22C55E", "bg": "rgba(34,197,94,0.15)", "label": "Standard", "order": 3},
}

RISK_LEVEL_CONFIG = {
    "DEALBREAKER": {"icon": "🔴", "order": 0},
    "HIGH": {"icon": "🔴", "order": 0},
    "CRITICAL": {"icon": "🟠", "order": 1},
    "MEDIUM": {"icon": "🟠", "order": 1},
    "IMPORTANT": {"icon": "🟡", "order": 2},
    "STANDARD": {"icon": "🟢", "order": 3},
    "LOW": {"icon": "🟢", "order": 3},
}

OVERALL_RISK_CONFIG = {
    "HIGH": {"color": "#EF4444", "bg": "rgba(239,68,68,0.15)", "icon": "🔴"},
    "MEDIUM": {"color": "#F97316", "bg": "rgba(249,115,22,0.15)", "icon": "🟠"},
    "LOW": {"color": "#22C55E", "bg": "rgba(34,197,94,0.15)", "icon": "🟢"},
}

VIEW_MODES = {
    "list": {"icon": "☰", "label": "List"},
    "compact": {"icon": "▤", "label": "Compact"},
    "table": {"icon": "▦", "label": "Table"},
}

CATEGORY_LABELS = {
    "indemnification": "Indemnification",
    "liability": "Liability",
    "ip": "Intellectual Prop.",
    "payment": "Payment",
    "termination": "Termination",
    "confidentiality": "Confidentiality",
    "warranties": "Warranties",
    "insurance": "Insurance",
    "compliance": "Compliance",
    "other": "Other",
}

# ============================================================================
# SESSION STATE
# ============================================================================

def init_risk_state():
    defaults = {
        "risk_selected_contract": None,
        "risk_findings": [],
        "risk_raw_response": {},
        "risk_summary": {},
        "risk_filter": "all",
        "risk_category_filter": None,
        "risk_expanded": False,
        "risk_error": None,
        "risk_overall": "",
        "risk_confidence": 0.0,
        "risk_scanning": False,
        "risk_scan_contract": None,
        "risk_view_mode": "list",
        "risk_search": "",
        "risk_patterns": {},
        "risk_by_category": {},
        "risk_clauses_reviewed": 0,
        "risk_clauses_flagged": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_risk_state():
    """Clear all risk-related session state for fresh start."""
    for key in list(st.session_state.keys()):
        if key.startswith("risk_"):
            del st.session_state[key]


# ============================================================================
# API CALLS
# ============================================================================

def api_get_contracts() -> List[Dict]:
    try:
        response = requests.get(f"{API_BASE}/contracts", timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        contracts = data if isinstance(data, list) else data.get("contracts", data.get("data", []))
        return [c for c in contracts if c and isinstance(c, dict)]
    except Exception:
        return []


def api_run_risk_scan(contract_id: int) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE}/analyze",
            json={"contract_id": contract_id},
            timeout=120
        )
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Analysis timed out. The contract may be too large or the server is busy."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to analysis server. Please check if the backend is running."}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# SCAN LOGIC
# ============================================================================

def execute_scan_if_pending():
    if st.session_state.get("risk_scanning"):
        contract_id = st.session_state.get("risk_scan_contract")
        st.session_state["risk_scanning"] = False
        st.session_state["risk_scan_contract"] = None
        if contract_id:
            with st.spinner("Analyzing contract... This may take 30-60 seconds."):
                run_risk_scan(contract_id)


def run_risk_scan(contract_id: int):
    st.session_state["risk_error"] = None
    st.session_state["risk_findings"] = []
    st.session_state["risk_summary"] = {}
    st.session_state["risk_raw_response"] = {}
    st.session_state["risk_patterns"] = {}
    st.session_state["risk_by_category"] = {}
    st.session_state["risk_clauses_reviewed"] = 0
    st.session_state["risk_clauses_flagged"] = 0
    st.session_state["risk_category_filter"] = None

    result = api_run_risk_scan(contract_id)

    if not result:
        st.session_state["risk_error"] = "API returned empty response"
        return

    # Store raw response for export
    st.session_state["risk_raw_response"] = result

    # Check for error first
    if "error" in result:
        st.session_state["risk_error"] = result.get("error", "Unknown error")
        return

    # Extract from nested 'analysis' key
    data = result.get("analysis", result)

    if not isinstance(data, dict):
        st.session_state["risk_error"] = "Invalid response format from API"
        return

    # Store pattern metadata if available
    if "patterns" in result:
        st.session_state["risk_patterns"] = result["patterns"]

    # Store category summary
    st.session_state["risk_by_category"] = data.get("risk_by_category", {})
    st.session_state["risk_clauses_reviewed"] = data.get("clauses_reviewed", 0)
    st.session_state["risk_clauses_flagged"] = data.get("clauses_flagged", 0)

    # Build findings list
    findings = []
    for item in data.get("dealbreakers", []):
        if item and isinstance(item, dict):
            item["severity"] = "dealbreaker"
            findings.append(item)
    for item in data.get("critical_items", []):
        if item and isinstance(item, dict):
            item["severity"] = "critical"
            findings.append(item)
    for item in data.get("important_items", []):
        if item and isinstance(item, dict):
            item["severity"] = "important"
            findings.append(item)
    # Note: standard_items not displayed per v4.3 design

    st.session_state["risk_findings"] = findings
    st.session_state["risk_summary"] = {
        "dealbreaker": len(data.get("dealbreakers", [])),
        "critical": len(data.get("critical_items", [])),
        "important": len(data.get("important_items", [])),
        "standard": 0,  # Not displayed
    }
    st.session_state["risk_selected_contract"] = contract_id
    st.session_state["risk_overall"] = data.get("overall_risk", "")
    st.session_state["risk_confidence"] = data.get("confidence_score", 0.0)


# ============================================================================
# LEFT COLUMN COMPONENTS
# ============================================================================

def render_contract_selector(contracts: List[Dict]) -> Optional[int]:
    if not contracts:
        st.caption("No contracts available")
        return None

    options = []
    for c in contracts:
        if not c or not isinstance(c, dict):
            continue
        title = (c.get("title") or "Untitled")[:30]
        counterparty = (c.get("counterparty") or "")[:15]
        label = f"{title} - {counterparty}" if counterparty else title
        options.append({"label": label, "id": c.get("id")})

    if not options:
        return None

    labels = [o["label"] for o in options]
    selected = st.selectbox("Contract", labels, key="risk_contract_select", label_visibility="collapsed")

    for o in options:
        if o["label"] == selected:
            return o["id"]
    return None


def render_overall_risk():
    """Render overall risk indicator using native Streamlit."""
    overall = st.session_state.get("risk_overall", "")
    confidence = st.session_state.get("risk_confidence", 0.0)

    if not overall:
        return

    cfg = OVERALL_RISK_CONFIG.get(overall.upper(), {"color": "#94A3B8", "bg": "rgba(148,163,184,0.15)", "icon": "⚪"})
    conf_pct = int(confidence * 100) if confidence else 0

    st.markdown("---")

    # Use native Streamlit components
    if overall.upper() == "HIGH":
        st.error(f"{cfg['icon']} **{overall.upper()} RISK**")
    elif overall.upper() == "MEDIUM":
        st.warning(f"{cfg['icon']} **{overall.upper()} RISK**")
    else:
        st.success(f"{cfg['icon']} **{overall.upper()} RISK**")

    st.caption(f"Confidence: {conf_pct}%")


def render_category_table():
    """Render clickable risk by category table."""
    risk_by_cat = st.session_state.get("risk_by_category", {})
    clauses_reviewed = st.session_state.get("risk_clauses_reviewed", 0)
    clauses_flagged = st.session_state.get("risk_clauses_flagged", 0)
    current_filter = st.session_state.get("risk_category_filter")

    if not risk_by_cat:
        return

    st.markdown("---")
    st.markdown("**RISK BY CATEGORY**")

    # Render each category as a clickable row
    for cat_key, cat_label in CATEGORY_LABELS.items():
        cat_data = risk_by_cat.get(cat_key, {})
        if not cat_data:
            continue

        risk_level = cat_data.get("risk", "LOW").upper()
        clauses = cat_data.get("clauses", 0)
        flagged = cat_data.get("flagged", 0)

        # Skip categories with 0 clauses
        if clauses == 0:
            continue

        risk_cfg = RISK_LEVEL_CONFIG.get(risk_level, {"icon": "🟢", "order": 3})
        icon = risk_cfg["icon"]

        # Highlight if this category is filtered
        is_active = current_filter == cat_key
        btn_type = "primary" if is_active else "secondary"

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{cat_label} {icon}", key=f"cat_{cat_key}", use_container_width=True, type=btn_type):
                if is_active:
                    st.session_state["risk_category_filter"] = None
                else:
                    st.session_state["risk_category_filter"] = cat_key
                st.rerun()
        with col2:
            st.markdown(f"**{flagged}**")

    # Summary line
    st.caption(f"{clauses_reviewed} reviewed • {clauses_flagged} ⚠")


def render_summary_filter():
    summary = st.session_state.get("risk_summary", {})
    current = st.session_state.get("risk_filter", "all")

    if not summary or all(v == 0 for v in summary.values()):
        st.caption("Run scan to see summary")
        return

    total = sum(summary.values())

    # Compact severity buttons
    for sev, cfg in SEVERITY_CONFIG.items():
        count = summary.get(sev, 0)
        if count == 0:
            continue

        is_active = current == sev
        btn_type = "primary" if is_active else "secondary"

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{cfg['icon']} {cfg['label']}", key=f"f_{sev}", use_container_width=True, type=btn_type):
                st.session_state["risk_filter"] = sev
                st.session_state["risk_category_filter"] = None  # Clear category filter
                st.rerun()
        with col2:
            st.markdown(f"**{count}**")

    # All button
    st.markdown("")
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("All", key="f_all", use_container_width=True, type="primary" if current == "all" else "secondary"):
            st.session_state["risk_filter"] = "all"
            st.session_state["risk_category_filter"] = None
            st.rerun()
    with col2:
        st.markdown(f"**{total}**")


# ============================================================================
# RIGHT COLUMN - FINDINGS
# ============================================================================

def get_filtered_findings() -> List[Dict]:
    findings = st.session_state.get("risk_findings", [])
    sev_filter = st.session_state.get("risk_filter", "all")
    cat_filter = st.session_state.get("risk_category_filter")
    search = st.session_state.get("risk_search", "").lower().strip()

    filtered = findings

    # Apply severity filter
    if sev_filter != "all":
        filtered = [f for f in filtered if f and f.get("severity") == sev_filter]

    # Apply category filter
    if cat_filter:
        filtered = [f for f in filtered if f and f.get("category", "").lower() == cat_filter.lower()]

    # Apply search filter
    if search:
        searched = []
        for f in filtered:
            searchable = " ".join([
                str(f.get("section_number") or ""),
                str(f.get("section_title") or ""),
                str(f.get("category") or ""),
                str(f.get("finding") or ""),
                str(f.get("rationale") or ""),
            ]).lower()
            if search in searchable:
                searched.append(f)
        filtered = searched

    def order(f):
        sev = f.get("severity", "standard") if f else "standard"
        return SEVERITY_CONFIG.get(sev, {}).get("order", 99)

    return sorted(filtered, key=order)


def format_redline(text: str) -> str:
    """Format redline text with ~~deletions~~ and `additions` styling."""
    if not text:
        return ""
    # Replace ~~deletions~~ with red strikethrough
    text = re.sub(
        r'~~(.+?)~~',
        r'<span style="color:#EF4444;text-decoration:line-through;background:rgba(239,68,68,0.1);">\1</span>',
        text
    )
    # Replace `additions` with green highlight
    text = re.sub(
        r'`([^`]+)`',
        r'<span style="color:#22C55E;background:rgba(34,197,94,0.15);padding:0 4px;border-radius:2px;">\1</span>',
        text
    )
    return text


def render_finding_card(finding: Dict, index: int = 0):
    """Render a finding in list view using native Streamlit components."""
    if not finding or not isinstance(finding, dict):
        return

    sev = str(finding.get("severity") or "standard").lower()
    cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["standard"])

    # Build title from section info
    sec_num = finding.get("section_number") or ""
    sec_title = finding.get("section_title") or ""
    category = finding.get("category") or ""
    confidence = finding.get("confidence") or 0
    finding_text = finding.get("finding") or ""

    if sec_num and sec_title:
        title = f"§{sec_num} {sec_title}"
    elif sec_title:
        title = sec_title
    elif category:
        title = category
    else:
        title = cfg['label']

    # Render with native components
    with st.container():
        # Header row
        col_icon, col_title, col_cat = st.columns([1, 10, 3])
        with col_icon:
            st.write(cfg['icon'])
        with col_title:
            st.markdown(f"**{title}**")
        with col_cat:
            cat_label = CATEGORY_LABELS.get(category.lower(), category) if category else cfg['label']
            if sev == "dealbreaker":
                st.error(cat_label)
            elif sev == "critical":
                st.warning(cat_label)
            elif sev == "important":
                st.info(cat_label)
            else:
                st.success(cat_label)

        # Finding text (issue summary)
        if finding_text:
            st.caption(finding_text)

        # Expandable details - SINGLE COLUMN LAYOUT
        with st.expander("View Details", expanded=False):

            # Original Clause (full width)
            clause_text = finding.get("clause_text") or ""
            if clause_text:
                st.markdown("**ORIGINAL CLAUSE**")
                st.text_area(
                    "Original",
                    value=clause_text,
                    height=120,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"clause_{index}"
                )
                st.markdown("")

            # Suggested Revision (full width, rendered redline)
            redline = finding.get("redline_suggestion") or ""
            if redline:
                st.markdown("**SUGGESTED REVISION**")
                st.markdown(
                    f'<div style="background:rgba(30,41,59,0.6);padding:12px;border-radius:6px;line-height:1.6;">'
                    f'{format_redline(redline)}'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.caption("Format: ~~strikethrough~~ = delete, `green` = add")
                st.markdown("")

            # Rationale (business justification)
            rationale = finding.get("rationale") or ""
            if rationale:
                st.markdown("**RATIONALE**")
                st.info(rationale)
                st.markdown("")

            # Cascade Impacts
            cascades = finding.get("cascade_impacts") or []
            if cascades:
                st.markdown("**CASCADE IMPACTS**")
                for impact in cascades[:5]:
                    st.markdown(f"• {impact}")
                st.markdown("")

            # Confidence (bottom right)
            if confidence:
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.markdown(
                        f'<div style="background:rgba(30,41,59,0.4);padding:8px;border-radius:6px;text-align:center;">'
                        f'<div style="color:#94A3B8;font-size:0.75rem;">Confidence</div>'
                        f'<div style="color:#E2E8F0;font-size:1.5rem;font-weight:600;">{int(confidence * 100)}%</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        st.divider()


def render_finding_card_compact(finding: Dict, index: int = 0):
    """Render a finding in compact view using native Streamlit."""
    if not finding or not isinstance(finding, dict):
        return

    sev = str(finding.get("severity") or "standard").lower()
    cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["standard"])

    sec_num = finding.get("section_number") or ""
    sec_title = (finding.get("section_title") or "")[:30]
    category = finding.get("category") or ""
    preview = (finding.get("finding") or "")[:60]

    title = f"§{sec_num} {sec_title}" if sec_num else sec_title or category
    cat_label = CATEGORY_LABELS.get(category.lower(), category) if category else ""

    # Single row compact display
    cols = st.columns([1, 4, 6, 2])
    with cols[0]:
        st.write(cfg['icon'])
    with cols[1]:
        st.markdown(f"**{title}**")
    with cols[2]:
        st.caption(f"{preview}..." if preview else "-")
    with cols[3]:
        st.caption(cat_label)


def render_findings_table(findings: List[Dict]):
    """Render findings in table view."""
    if not findings:
        return

    table_data = []
    for f in findings:
        sev = f.get("severity") or "standard"
        cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["standard"])
        finding_text = f.get("finding") or "-"
        finding_preview = finding_text[:80] + "..." if len(finding_text) > 80 else finding_text
        category = f.get("category") or "-"
        cat_label = CATEGORY_LABELS.get(category.lower(), category) if category else "-"

        table_data.append({
            "Risk": f"{cfg['icon']} {cfg['label']}",
            "Section": f.get("section_number") or "-",
            "Title": (f.get("section_title") or "-")[:40],
            "Category": cat_label,
            "Finding": finding_preview,
            "Confidence": f"{int((f.get('confidence') or 0) * 100)}%",
        })

    st.dataframe(table_data, use_container_width=True, hide_index=True)


def render_view_mode_selector():
    """Render view mode toggle buttons."""
    current_mode = st.session_state.get("risk_view_mode", "list")

    cols = st.columns(len(VIEW_MODES))
    for i, (mode, cfg) in enumerate(VIEW_MODES.items()):
        with cols[i]:
            btn_type = "primary" if current_mode == mode else "secondary"
            if st.button(f"{cfg['icon']} {cfg['label']}", key=f"vm_{mode}", type=btn_type, use_container_width=True):
                st.session_state["risk_view_mode"] = mode
                st.rerun()


def render_export_button():
    """Render export button for findings."""
    findings = st.session_state.get("risk_findings", [])

    if not findings:
        return

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "overall_risk": st.session_state.get("risk_overall", ""),
        "confidence_score": st.session_state.get("risk_confidence", 0),
        "clauses_reviewed": st.session_state.get("risk_clauses_reviewed", 0),
        "clauses_flagged": st.session_state.get("risk_clauses_flagged", 0),
        "risk_by_category": st.session_state.get("risk_by_category", {}),
        "findings_count": len(findings),
        "summary": st.session_state.get("risk_summary", {}),
        "findings": findings,
    }

    json_str = json.dumps(export_data, indent=2, default=str)

    st.download_button(
        label="Export",
        data=json_str,
        file_name=f"risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        type="secondary",
    )


def render_findings_panel():
    findings = get_filtered_findings()
    total = len(st.session_state.get("risk_findings", []))
    view_mode = st.session_state.get("risk_view_mode", "list")
    cat_filter = st.session_state.get("risk_category_filter")

    # Empty state
    if not findings and total == 0:
        st.info("🔍 No analysis results. Select a contract and run a scan to see findings.")
        return

    if not findings:
        filter_msg = f"No findings match your filters"
        if cat_filter:
            cat_label = CATEGORY_LABELS.get(cat_filter, cat_filter)
            filter_msg = f"No flagged findings in {cat_label}"
        st.info(filter_msg)
        return

    # Header row with view modes and export
    sev_filter = st.session_state.get("risk_filter", "all")
    if cat_filter:
        cat_label = CATEGORY_LABELS.get(cat_filter, cat_filter)
        count_text = f"{len(findings)} in {cat_label}"
    elif sev_filter == "all":
        count_text = f"{len(findings)}"
    else:
        count_text = f"{len(findings)} of {total}"

    header_cols = st.columns([2, 3, 1])
    with header_cols[0]:
        st.markdown(f"**FINDINGS** ({count_text})")
    with header_cols[1]:
        render_view_mode_selector()
    with header_cols[2]:
        render_export_button()

    # Search bar
    search = st.text_input("Search", key="risk_search_input", label_visibility="collapsed", placeholder="Search findings...")
    if search != st.session_state.get("risk_search", ""):
        st.session_state["risk_search"] = search
        st.rerun()

    st.markdown("")

    # Render based on view mode
    if view_mode == "table":
        render_findings_table(findings)
    else:
        expanded = st.session_state.get("risk_expanded", False)
        visible = findings if expanded else findings[:10]

        for i, f in enumerate(visible):
            if view_mode == "compact":
                render_finding_card_compact(f, i)
            else:
                render_finding_card(f, i)

        # Show remaining / expand controls
        remaining = len(findings) - len(visible)
        if remaining > 0:
            st.caption(f"+ {remaining} more findings")
            if st.button("Show All", key="expand_all", use_container_width=True, type="secondary"):
                st.session_state["risk_expanded"] = True
                st.rerun()

        if expanded and len(findings) > 10:
            if st.button("Collapse", key="collapse", use_container_width=True, type="secondary"):
                st.session_state["risk_expanded"] = False
                st.rerun()


# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Risk Analysis", "🔍", max_width=1400)

page_header(
    "Risk Analysis",
    subtitle="AI-powered contract risk assessment and clause analysis",
    show_status=True,
    show_version=True
)

init_risk_state()
execute_scan_if_pending()

with content_container():
    # Error display with Start Over option
    if st.session_state.get("risk_error"):
        st.error(st.session_state["risk_error"])
        if st.button("↻ Start Over", type="primary"):
            clear_risk_state()
            st.rerun()

    contracts = api_get_contracts()

    # Two-panel layout
    col_scan, col_findings = st.columns([1, 3])

    # LEFT PANEL - SCAN CONTROLS
    with col_scan:
        st.markdown("**SCAN**")

        # Contract selector
        st.markdown("**Select Contract**")
        selected_id = render_contract_selector(contracts)

        # Scan button
        if selected_id:
            if st.button("🔍 Run Scan", key="btn_scan", type="primary", use_container_width=True):
                st.session_state["risk_scanning"] = True
                st.session_state["risk_scan_contract"] = selected_id
                st.rerun()
        else:
            st.button("🔍 Run Scan", key="btn_scan_disabled", type="secondary", use_container_width=True, disabled=True)

        # Overall risk display (integrated with confidence)
        render_overall_risk()

        # Category risk table (below overall risk)
        render_category_table()

        # Pattern info (if available)
        patterns = st.session_state.get("risk_patterns", {})
        if patterns:
            pattern_count = patterns.get("pattern_count", 0)
            if pattern_count:
                st.caption(f"📊 {pattern_count} patterns applied")

        # Severity filter
        st.markdown("")
        st.markdown("**Filter by Severity**")
        render_summary_filter()

    # RIGHT PANEL - FINDINGS
    with col_findings:
        render_findings_panel()
