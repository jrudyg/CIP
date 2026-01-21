# pages/4_Risk_Analysis.py
"""
CIP Risk Analysis v5.0 - CCE-Plus Integration
- Integrated risk header with severity heatmap
- Collapsible filters: "By Risk Level" (top) and "By Risk Category" (below)
- By Risk Level: 5-button row
- By Risk Category: Compact 4-column grid with 3-char abbreviations + hover tooltips
- Hybrid expander: Original|Revision side-by-side, Rationale full-width below
- Compact view as default mode
- Green filter shows compact list of low-risk clauses
- Renamed "Business Impact" → "RATIONALE"
- 11 categories (operational, closeout instead of "other")
- CCE-Plus: Workflow gate enforcement (requires intake complete)
"""

import streamlit as st
import requests
import json
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Import redline formatter utility
from frontend.utils.redline_formatter import format_redline

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from components.page_wrapper import (
    init_page,
    page_header,
    content_container
)

# Import workflow gates
try:
    from workflow_gates import WorkflowGate
    WORKFLOW_GATES_AVAILABLE = True
except ImportError:
    WORKFLOW_GATES_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:5000/api"

SEVERITY_CONFIG = {
    "dealbreaker": {"icon": "🔴", "color": "#EF4444", "label": "Dealbreaker", "order": 0},
    "critical": {"icon": "🟠", "color": "#F97316", "label": "Critical", "order": 1},
    "important": {"icon": "🟡", "color": "#EAB308", "label": "Important", "order": 2},
    "low": {"icon": "🟢", "color": "#22C55E", "label": "Low", "order": 3},
    "standard": {"icon": "🟢", "color": "#22C55E", "label": "Standard", "order": 3},
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
    "HIGH": {"color": "#EF4444", "icon": "🔴"},
    "MEDIUM": {"color": "#F97316", "icon": "🟠"},
    "LOW": {"color": "#22C55E", "icon": "🟢"},
}

CATEGORY_LABELS = {
    "indemnification": {"abbr": "IND", "full": "Indemnification"},
    "liability": {"abbr": "LIA", "full": "Liability"},
    "ip": {"abbr": "IP", "full": "Intellectual Property"},
    "payment": {"abbr": "PAY", "full": "Payment"},
    "termination": {"abbr": "TRM", "full": "Termination"},
    "confidentiality": {"abbr": "CNF", "full": "Confidentiality"},
    "warranties": {"abbr": "WAR", "full": "Warranties"},
    "insurance": {"abbr": "INS", "full": "Insurance"},
    "compliance": {"abbr": "CMP", "full": "Compliance"},
    "operational": {"abbr": "OPS", "full": "Operational"},
    "closeout": {"abbr": "CLO", "full": "Closeout"},
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
        "risk_scan_in_progress": False,
        "risk_view_mode": "compact",  # Default to compact
        "risk_search": "",
        "risk_patterns": {},
        "risk_by_category": {},
        "risk_clauses_reviewed": 0,
        "risk_clauses_flagged": 0,
        "risk_severity_counts": {},
        "risk_low_risk_clauses": [],
        "risk_show_category_filter": False,
        "risk_show_severity_filter": False,
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


def get_cce_risk_analysis(contract_id: int, db_path: str) -> Dict:
    """
    Read CCE-Plus risk data from clauses table and format for UI display.

    Replaces old API-based analysis with direct database query.
    CCE-Plus scores are already computed during intake.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, section_number, section_title, clause_type,
                   verbatim_text, cce_risk_score, cce_risk_level,
                   cce_statutory_flag, cce_cascade_risk
            FROM clauses
            WHERE contract_id = ?
            ORDER BY cce_risk_score DESC
        """, (contract_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"error": "No clauses found for this contract"}

        # Transform CCE data to UI format (compatible with existing rendering logic)
        result = {
            "analysis": {
                "dealbreakers": [],      # CRITICAL risk
                "critical_items": [],    # HIGH risk
                "important_items": [],   # MEDIUM risk
                "low_risk_clauses": [],  # LOW risk
                "clauses_reviewed": len(rows),
                "clauses_flagged": 0,
                "severity_counts": {
                    "dealbreaker": 0,
                    "critical": 0,
                    "important": 0,
                    "low": 0
                }
            }
        }

        for row in rows:
            clause_id, section_num, section_title, clause_type, text, score, level, statutory, cascade = row

            # Create item dict for UI (field names must match render_finding_card_compact)
            item = {
                "clause_id": clause_id,
                "section_number": section_num or "N/A",
                "section_title": section_title or "Untitled",
                "category": clause_type or "General",
                "finding": text[:500] if text else "",  # Preview text for display
                "original_text": text[:500] if text else "",  # Keep for compatibility
                "risk_score": score or 0,
                "risk_level": level or "LOW",
                "statutory_flag": statutory or "",
                "cascade_risk": bool(cascade)
            }

            # Route to appropriate severity bucket
            if level == 'CRITICAL':
                result["analysis"]["dealbreakers"].append(item)
                result["analysis"]["severity_counts"]["dealbreaker"] += 1
                result["analysis"]["clauses_flagged"] += 1
            elif level == 'HIGH':
                result["analysis"]["critical_items"].append(item)
                result["analysis"]["severity_counts"]["critical"] += 1
                result["analysis"]["clauses_flagged"] += 1
            elif level == 'MEDIUM':
                result["analysis"]["important_items"].append(item)
                result["analysis"]["severity_counts"]["important"] += 1
                result["analysis"]["clauses_flagged"] += 1
            else:  # LOW
                result["analysis"]["low_risk_clauses"].append(item)
                result["analysis"]["severity_counts"]["low"] += 1

        return result

    except Exception as e:
        return {"error": f"Error reading CCE-Plus risk data: {str(e)}"}


# ============================================================================
# WORKFLOW GATE HELPERS
# ============================================================================

def check_workflow_gate(contract_id: int) -> tuple[bool, str]:
    """
    Check if risk analysis can be started for this contract.

    Returns:
        (can_proceed: bool, message: str)
    """
    if not WORKFLOW_GATES_AVAILABLE:
        return True, ""  # Graceful degradation if gates not available

    try:
        db_path = str(backend_path.parent / "data" / "contracts.db")
        gate = WorkflowGate(db_path)
        can_proceed, msg = gate.can_start_risk_analysis(contract_id)
        return can_proceed, msg
    except Exception as e:
        return False, f"Error checking workflow gate: {e}"


def advance_workflow_after_analysis(contract_id: int) -> bool:
    """
    Advance workflow after successful risk analysis.
    Marks risk complete and unlocks redline stage.

    Returns:
        True if successful, False otherwise
    """
    if not WORKFLOW_GATES_AVAILABLE:
        return True  # Graceful degradation

    try:
        db_path = str(backend_path.parent / "data" / "contracts.db")
        gate = WorkflowGate(db_path)
        # Mark risk analysis complete and unlock redline stage
        success = gate.advance_stage(contract_id, 'risk')
        if success:
            return True
        return False
    except Exception:
        return False


# ============================================================================
# SCAN LOGIC
# ============================================================================

def execute_scan_if_pending():
    if st.session_state.get("risk_scanning") and not st.session_state.get("risk_scan_in_progress"):
        contract_id = st.session_state.get("risk_scan_contract")
        if contract_id:
            # Check workflow gate before proceeding
            can_proceed, gate_msg = check_workflow_gate(contract_id)
            if not can_proceed:
                st.session_state["risk_scanning"] = False
                st.session_state["risk_scan_contract"] = None
                st.session_state["risk_error"] = f"Cannot start risk analysis: {gate_msg}"
                return

            # Clear trigger flags and set lock BEFORE scan
            st.session_state["risk_scanning"] = False
            st.session_state["risk_scan_contract"] = None
            st.session_state["risk_scan_in_progress"] = True
            with st.spinner("Analyzing contract... This may take 30-60 seconds."):
                run_risk_scan(contract_id)
            st.session_state["risk_scan_in_progress"] = False


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
    st.session_state["risk_severity_counts"] = {}
    st.session_state["risk_low_risk_clauses"] = []

    # Get database path
    db_path = str(backend_path.parent / "data" / "contracts.db")

    # Use CCE-Plus data from database instead of API call
    result = get_cce_risk_analysis(contract_id, db_path)

    if not result:
        st.session_state["risk_error"] = "API returned empty response"
        return

    st.session_state["risk_raw_response"] = result

    if "error" in result:
        st.session_state["risk_error"] = result.get("error", "Unknown error")
        return

    data = result.get("analysis", result)

    if not isinstance(data, dict):
        st.session_state["risk_error"] = "Invalid response format from API"
        return

    if "patterns" in result:
        st.session_state["risk_patterns"] = result["patterns"]

    # Store v1.7 fields
    st.session_state["risk_by_category"] = data.get("risk_by_category", {})
    st.session_state["risk_clauses_reviewed"] = data.get("clauses_reviewed", 0)
    st.session_state["risk_clauses_flagged"] = data.get("clauses_flagged", 0)
    st.session_state["risk_severity_counts"] = data.get("severity_counts", {})
    st.session_state["risk_low_risk_clauses"] = data.get("low_risk_clauses", [])

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

    st.session_state["risk_findings"] = findings
    st.session_state["risk_summary"] = {
        "dealbreaker": len(data.get("dealbreakers", [])),
        "critical": len(data.get("critical_items", [])),
        "important": len(data.get("important_items", [])),
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

    # Pre-select based on session state
    pre_selected_id = st.session_state.get("risk_selected_contract")
    default_index = 0
    if pre_selected_id:
        for i, o in enumerate(options):
            if o["id"] == pre_selected_id:
                default_index = i
                break

    labels = [o["label"] for o in options]
    selected = st.selectbox("Contract", labels, index=default_index, key="risk_contract_select", label_visibility="collapsed")

    for o in options:
        if o["label"] == selected:
            return o["id"]
    return None


def render_integrated_risk_header():
    """Render integrated risk indicator with severity heatmap."""
    overall = st.session_state.get("risk_overall", "")
    confidence = st.session_state.get("risk_confidence", 0.0)
    clauses_reviewed = st.session_state.get("risk_clauses_reviewed", 0)
    clauses_flagged = st.session_state.get("risk_clauses_flagged", 0)
    severity_counts = st.session_state.get("risk_severity_counts", {})

    if not overall:
        return

    cfg = OVERALL_RISK_CONFIG.get(overall.upper(), {"color": "#94A3B8", "icon": "⚪"})
    conf_pct = int(confidence * 100) if confidence else 0

    st.markdown("---")

    # Risk + Confidence on single line
    col1, col2 = st.columns([3, 1])
    with col1:
        if overall.upper() == "HIGH":
            st.error(f"{cfg['icon']} **{overall.upper()} RISK**")
        elif overall.upper() == "MEDIUM":
            st.warning(f"{cfg['icon']} **{overall.upper()} RISK**")
        else:
            st.success(f"{cfg['icon']} **{overall.upper()} RISK**")
    with col2:
        st.markdown(f"**{conf_pct}%**")

    # Summary line
    st.markdown(f"**{clauses_reviewed} clauses** • {clauses_flagged} flagged")

    # Severity heatmap row
    db = severity_counts.get("dealbreaker", 0)
    cr = severity_counts.get("critical", 0)
    im = severity_counts.get("important", 0)
    lo = severity_counts.get("low", 0)

    # Calculate low if not provided
    if lo == 0 and clauses_reviewed > 0:
        lo = clauses_reviewed - db - cr - im

    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"🔴 **{db}**")
    with cols[1]:
        st.markdown(f"🟠 **{cr}**")
    with cols[2]:
        st.markdown(f"🟡 **{im}**")
    with cols[3]:
        st.markdown(f"🟢 **{lo}**")


def render_category_filter():
    """Render collapsible category filter with compact 4-column grid."""
    risk_by_cat = st.session_state.get("risk_by_category", {})
    findings = st.session_state.get("risk_findings", [])
    current_filter = st.session_state.get("risk_category_filter")
    show_filter = st.session_state.get("risk_show_category_filter", False)

    # Calculate counts based on current severity filter (matches filtered findings)
    sev_filter = st.session_state.get("risk_filter", "all")
    cat_counts = {}

    for f in findings:
        # Apply severity filter first
        f_sev = (f.get("severity") or "").lower()
        if sev_filter not in ["all", "low"]:
            if f_sev != sev_filter:
                continue

        # Count by category
        cat = (f.get("category") or "").lower()
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    if not cat_counts:
        return

    # Toggle header
    toggle_label = "▼ By Risk Category" if show_filter else "▶ By Risk Category"
    if st.button(toggle_label, key="toggle_cat", use_container_width=True, type="secondary"):
        st.session_state["risk_show_category_filter"] = not show_filter
        st.rerun()

    if not show_filter:
        return

    # Compact 4-column grid with abbreviations
    cat_items = list(cat_counts.items())
    rows = (len(cat_items) + 3) // 4  # 4 per row

    for row in range(rows):
        cols = st.columns(4)
        for col_idx in range(4):
            item_idx = row * 4 + col_idx
            if item_idx >= len(cat_items):
                continue

            cat_key, count = cat_items[item_idx]
            cat_info = CATEGORY_LABELS.get(cat_key, {"abbr": cat_key[:3].upper(), "full": cat_key})
            abbr = cat_info["abbr"]
            full_name = cat_info["full"]

            # Get risk level icon
            cat_data = risk_by_cat.get(cat_key, {})
            risk_level = cat_data.get("risk", "IMPORTANT").upper()
            risk_cfg = RISK_LEVEL_CONFIG.get(risk_level, {"icon": "🟡"})
            icon = risk_cfg["icon"]

            is_active = current_filter == cat_key
            btn_type = "primary" if is_active else "secondary"

            with cols[col_idx]:
                if st.button(f"{icon}{count} {abbr}", key=f"cat_{cat_key}", type=btn_type, use_container_width=True, help=full_name):
                    if is_active:
                        st.session_state["risk_category_filter"] = None
                    else:
                        st.session_state["risk_category_filter"] = cat_key
                        st.session_state["risk_filter"] = "all"
                    st.rerun()


def render_severity_filter():
    """Render collapsible severity filter with compact toggles."""
    summary = st.session_state.get("risk_summary", {})
    current = st.session_state.get("risk_filter", "all")
    show_filter = st.session_state.get("risk_show_severity_filter", False)
    low_count = len(st.session_state.get("risk_low_risk_clauses", []))

    # Calculate low from severity_counts if available
    severity_counts = st.session_state.get("risk_severity_counts", {})
    if severity_counts:
        low_count = severity_counts.get("low", low_count)

    if not summary and low_count == 0:
        return

    # Toggle header
    toggle_label = "▼ By Risk Level" if show_filter else "▶ By Risk Level"
    if st.button(toggle_label, key="toggle_sev", use_container_width=True, type="secondary"):
        st.session_state["risk_show_severity_filter"] = not show_filter
        st.rerun()

    if not show_filter:
        return

    # Compact toggle buttons in a row
    cols = st.columns(5)

    # Dealbreaker
    db_count = summary.get("dealbreaker", 0)
    with cols[0]:
        btn_type = "primary" if current == "dealbreaker" else "secondary"
        if st.button(f"🔴{db_count}", key="sev_db", type=btn_type):
            st.session_state["risk_filter"] = "dealbreaker"
            st.session_state["risk_category_filter"] = None
            st.rerun()

    # Critical
    cr_count = summary.get("critical", 0)
    with cols[1]:
        btn_type = "primary" if current == "critical" else "secondary"
        if st.button(f"🟠{cr_count}", key="sev_cr", type=btn_type):
            st.session_state["risk_filter"] = "critical"
            st.session_state["risk_category_filter"] = None
            st.rerun()

    # Important
    im_count = summary.get("important", 0)
    with cols[2]:
        btn_type = "primary" if current == "important" else "secondary"
        if st.button(f"🟡{im_count}", key="sev_im", type=btn_type):
            st.session_state["risk_filter"] = "important"
            st.session_state["risk_category_filter"] = None
            st.rerun()

    # Low (green) - shows compact list
    with cols[3]:
        btn_type = "primary" if current == "low" else "secondary"
        if st.button(f"🟢{low_count}", key="sev_lo", type=btn_type):
            st.session_state["risk_filter"] = "low"
            st.session_state["risk_category_filter"] = None
            st.rerun()

    # All
    total = db_count + cr_count + im_count
    with cols[4]:
        btn_type = "primary" if current == "all" else "secondary"
        if st.button(f"All", key="sev_all", type=btn_type):
            st.session_state["risk_filter"] = "all"
            st.session_state["risk_category_filter"] = None
            st.rerun()


# ============================================================================
# RIGHT COLUMN - FINDINGS
# ============================================================================

def get_filtered_findings() -> List[Dict]:
    findings = st.session_state.get("risk_findings", [])
    sev_filter = st.session_state.get("risk_filter", "all")
    cat_filter = st.session_state.get("risk_category_filter")
    search = st.session_state.get("risk_search", "").lower().strip()

    filtered = findings

    # Apply severity filter (except "low" which is handled separately)
    if sev_filter not in ["all", "low"]:
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


def render_finding_card(finding: Dict, index: int = 0):
    """Render a finding card with hybrid layout (Original|Revision side-by-side, Rationale below)."""
    if not finding or not isinstance(finding, dict):
        return

    sev = str(finding.get("severity") or "standard").lower()
    cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["standard"])

    sec_num = finding.get("section_number") or ""
    sec_title = finding.get("section_title") or ""
    category = finding.get("category") or ""
    confidence = finding.get("confidence") or 0
    finding_text = finding.get("finding") or ""

    if sec_num and sec_title:
        title = f"Sec {sec_num} {sec_title}"
    elif sec_title:
        title = sec_title
    elif category:
        title = category
    else:
        title = cfg['label']

    with st.container():
        # Header row
        col_icon, col_title, col_cat = st.columns([1, 10, 3])
        with col_icon:
            st.write(cfg['icon'])
        with col_title:
            st.markdown(f"**{title}**")
        with col_cat:
            cat_info = CATEGORY_LABELS.get(category.lower(), {}) if category else {}
            cat_label = cat_info.get("full", category) if cat_info else cfg['label']
            st.caption(cat_label)

        # Finding summary
        if finding_text:
            st.caption(finding_text)

        # Expandable details - HYBRID LAYOUT
        with st.expander("View Details", expanded=False):
            
            # Original Clause | Suggested Revision (side by side)
            col1, col2 = st.columns(2)
            
            with col1:
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

            with col2:
                redline = finding.get("redline_suggestion") or ""
                if redline:
                    st.markdown("**SUGGESTED REVISION**")
                    st.markdown(
                        f'<div style="background:rgba(30,41,59,0.6);padding:12px;border-radius:6px;line-height:1.6;min-height:100px;">'
                        f'{format_redline(redline)}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    st.caption("~~delete~~ `add`")

            # Rationale (full width below)
            rationale = finding.get("rationale") or ""
            if rationale:
                st.markdown("")
                st.markdown("**RATIONALE**")
                st.info(rationale)

            # Cascade Impacts | Confidence (side by side)
            cascades = finding.get("cascade_impacts") or []
            if cascades or confidence:
                st.markdown("")
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    if cascades:
                        st.markdown("**CASCADE IMPACTS**")
                        for impact in cascades[:3]:
                            st.caption(f"• {impact}")
                
                with col_b:
                    if confidence:
                        st.markdown(
                            f'<div style="background:rgba(30,41,59,0.4);padding:8px;border-radius:6px;text-align:center;">'
                            f'<div style="color:#94A3B8;font-size:0.7rem;">Confidence</div>'
                            f'<div style="color:#E2E8F0;font-size:1.25rem;font-weight:600;">{int(confidence * 100)}%</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

        st.divider()


def render_finding_card_compact(finding: Dict, index: int = 0):
    """Render a finding in compact one-line view."""
    if not finding or not isinstance(finding, dict):
        return

    sev = str(finding.get("severity") or "standard").lower()
    cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["standard"])

    sec_num = finding.get("section_number") or ""
    sec_title = (finding.get("section_title") or "")[:35]
    category = finding.get("category") or ""
    preview = (finding.get("finding") or "")[:50]

    title = f"Sec {sec_num} {sec_title}" if sec_num else sec_title or category
    cat_info = CATEGORY_LABELS.get(category.lower(), {}) if category else {}
    cat_label = cat_info.get("abbr", category[:3].upper()) if cat_info else ""

    cols = st.columns([1, 5, 6, 2])
    with cols[0]:
        st.write(cfg['icon'])
    with cols[1]:
        st.markdown(f"**{title}**")
    with cols[2]:
        st.caption(f"{preview}..." if preview else "-")
    with cols[3]:
        st.caption(cat_label)


def render_low_risk_list():
    """Render compact multi-column list of low-risk clauses."""
    low_clauses = st.session_state.get("risk_low_risk_clauses", [])
    if not low_clauses:
        st.info("No low-risk clause details available")
        return

    st.markdown(f"**LOW RISK CLAUSES ({len(low_clauses)})**")

    # Multi-column layout - 3 columns
    num_cols = 3
    cols = st.columns(num_cols)

    for idx, clause in enumerate(low_clauses):
        col_idx = idx % num_cols
        sec_num = clause.get("section_number") or ""
        sec_title = clause.get("section_title") or ""

        with cols[col_idx]:
            if sec_num and sec_title:
                st.caption(f"Sec {sec_num} {sec_title}")
            elif sec_title:
                st.caption(sec_title)


def render_findings_panel():
    findings = get_filtered_findings()
    total = len(st.session_state.get("risk_findings", []))
    view_mode = st.session_state.get("risk_view_mode", "compact")
    sev_filter = st.session_state.get("risk_filter", "all")
    cat_filter = st.session_state.get("risk_category_filter")

    # Handle LOW filter separately - show compact list
    if sev_filter == "low":
        render_low_risk_list()
        return

    # Empty state
    if not findings and total == 0:
        st.info("🔍 No analysis results. Select a contract and run a scan to see findings.")
        return

    if not findings:
        filter_msg = "No findings match your filters"
        if cat_filter:
            cat_info = CATEGORY_LABELS.get(cat_filter, {})
            cat_label = cat_info.get("full", cat_filter) if cat_info else cat_filter
            filter_msg = f"No flagged findings in {cat_label}"
        st.info(filter_msg)
        return

    # Header row
    if cat_filter:
        cat_info = CATEGORY_LABELS.get(cat_filter, {})
        cat_label = cat_info.get("full", cat_filter) if cat_info else cat_filter
        count_text = f"{len(findings)} in {cat_label}"
    elif sev_filter == "all":
        count_text = f"{len(findings)}"
    else:
        count_text = f"{len(findings)} of {total}"

    header_cols = st.columns([3, 2, 1])
    with header_cols[0]:
        st.markdown(f"**FINDINGS** ({count_text})")
    with header_cols[1]:
        # View mode toggle
        col_list, col_compact = st.columns(2)
        with col_list:
            if st.button("☰", key="vm_list", type="primary" if view_mode == "list" else "secondary"):
                st.session_state["risk_view_mode"] = "list"
                st.rerun()
        with col_compact:
            if st.button("▤", key="vm_compact", type="primary" if view_mode == "compact" else "secondary"):
                st.session_state["risk_view_mode"] = "compact"
                st.rerun()
    with header_cols[2]:
        # Export
        if findings:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "overall_risk": st.session_state.get("risk_overall", ""),
                "confidence_score": st.session_state.get("risk_confidence", 0),
                "clauses_reviewed": st.session_state.get("risk_clauses_reviewed", 0),
                "clauses_flagged": st.session_state.get("risk_clauses_flagged", 0),
                "findings": findings,
            }
            st.download_button(
                label="↓",
                data=json.dumps(export_data, indent=2, default=str),
                file_name=f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                type="secondary",
            )

    # Search bar
    search = st.text_input("Search", key="risk_search_input", label_visibility="collapsed", placeholder="Search...")
    if search != st.session_state.get("risk_search", ""):
        st.session_state["risk_search"] = search
        st.rerun()

    st.markdown("")

    # Render findings
    expanded = st.session_state.get("risk_expanded", False)
    visible = findings if expanded else findings[:10]

    for i, f in enumerate(visible):
        if view_mode == "compact":
            render_finding_card_compact(f, i)
        else:
            render_finding_card(f, i)

    # Expand controls
    remaining = len(findings) - len(visible)
    if remaining > 0:
        st.caption(f"+ {remaining} more")
        if st.button("Show All", key="expand_all", use_container_width=True, type="secondary"):
            st.session_state["risk_expanded"] = True
            st.rerun()

    if expanded and len(findings) > 10:
        if st.button("Collapse", key="collapse", use_container_width=True, type="secondary"):
            st.session_state["risk_expanded"] = False
            st.rerun()

    # Show low-risk items in collapsed expander when viewing "all"
    if sev_filter == "all":
        low_clauses = st.session_state.get("risk_low_risk_clauses", [])
        if low_clauses:
            with st.expander(f"🟢 Low Risk Items ({len(low_clauses)})", expanded=False):
                render_low_risk_list()


# ============================================================================
# MAIN PAGE
# ============================================================================

init_page("Risk Analysis", "🔍", max_width=1400)

page_header(
    "Risk Analysis",
    subtitle="AI-powered contract risk assessment with CCE-Plus workflow gates",
    show_status=True,
    show_version=True
)

init_risk_state()
execute_scan_if_pending()

with content_container():
    # Error display
    if st.session_state.get("risk_error"):
        st.error(st.session_state["risk_error"])
        if st.button("↻ Start Over", type="primary"):
            clear_risk_state()
            st.rerun()

    contracts = api_get_contracts()

    # Two-panel layout
    col_scan, col_findings = st.columns([1, 3])

    # LEFT PANEL
    with col_scan:
        st.markdown("**Select Contract**")
        selected_id = render_contract_selector(contracts)

        # Check workflow gate for selected contract
        can_scan = True
        gate_message = ""
        if selected_id:
            can_scan, gate_message = check_workflow_gate(selected_id)

        # Scan button (compact)
        if selected_id and can_scan:
            if st.button("🔍 Run Scan", key="btn_scan", type="primary", use_container_width=True):
                st.session_state["risk_scanning"] = True
                st.session_state["risk_scan_contract"] = selected_id
                st.rerun()
        elif selected_id and not can_scan:
            st.button("🔍 Run Scan", key="btn_scan_blocked", type="secondary", use_container_width=True, disabled=True, help=gate_message)
            st.warning(f"🔒 {gate_message}")
        else:
            st.button("🔍 Run Scan", key="btn_scan_disabled", type="secondary", use_container_width=True, disabled=True)

        # Integrated risk header with heatmap
        render_integrated_risk_header()

        # Complete Risk Analysis button
        if selected_id:
            findings = st.session_state.get("risk_findings", [])
            if findings:  # Only show if analysis has been run
                st.markdown("---")
                if st.button("✅ Complete Risk Analysis", key="btn_complete", type="primary", use_container_width=True):
                    success = advance_workflow_after_analysis(selected_id)
                    if success:
                        st.success("✅ Risk analysis marked complete! Redline stage unlocked.")
                        st.rerun()
                    else:
                        st.error("Failed to advance workflow. Please try again.")

        # Collapsible filters
        render_severity_filter()
        render_category_filter()

    # RIGHT PANEL
    with col_findings:
        render_findings_panel()
