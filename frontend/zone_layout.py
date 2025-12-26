"""
CIP Zone Layout System
======================
7-zone golden ratio layout for all CIP pages.
"""

import streamlit as st
from typing import Callable, Optional


def system_status(api_healthy: bool = True, db_healthy: bool = True, ai_healthy: bool = True) -> None:
    """Render system status indicators with accessible text labels."""
    st.markdown("---")
    st.markdown("**System Status**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"{'🟢 OK' if api_healthy else '🔴 Down'} API")
    with col2:
        st.markdown(f"{'🟢 OK' if db_healthy else '🔴 Down'} DB")
    with col3:
        st.markdown(f"{'🟢 OK' if ai_healthy else '🔴 Down'} AI")


def zone_layout(
    z1: Optional[Callable] = None,
    z2: Optional[Callable] = None,
    z3: Optional[Callable] = None,
    z4: Optional[Callable] = None,
    z5: Optional[Callable] = None,
    z6: Optional[Callable] = None,
    z7: Optional[Callable] = None,
    z8: Optional[Callable] = None,
    z9: Optional[Callable] = None,
    z7_system_status: bool = True,
    api_healthy: bool = True,
    db_healthy: bool = True,
    ai_healthy: bool = True
) -> None:
    """Render 9-zone page layout."""
    col1, col2, col3 = st.columns([34, 21, 13])
    with col1:
        if z1: z1()
    with col2:
        if z2: z2()
    with col3:
        if z3: z3()

    if z4:
        with st.container():
            z4()

    col5, col6, col7 = st.columns([38, 38, 24])
    with col5:
        if z5: z5()
    with col6:
        if z6: z6()
    with col7:
        if z7: z7()
        if z7_system_status:
            system_status(api_healthy, db_healthy, ai_healthy)

    # Z8: Cross-Document Intelligence (full-width below Z5-Z7)
    if z8:
        with st.container():
            z8()

    # Z9: Contract Playbook Synthesis (full-width below Z8)
    if z9:
        with st.container():
            z9()


def check_system_health() -> tuple[bool, bool, bool]:
    """Check system health. Returns: (api, db, ai) booleans."""
    import requests
    try:
        r = requests.get("http://localhost:5000/health", timeout=2)
        if r.ok:
            h = r.json()
            # API is healthy if we got a response
            api_ok = h.get("status") == "healthy"
            # Database is healthy if contracts db exists
            db_info = h.get("database", {})
            db_ok = db_info.get("contracts", False) if isinstance(db_info, dict) else bool(db_info)
            # AI is healthy if api_key is configured
            ai_ok = h.get("api_key_configured", False)
            return api_ok, db_ok, ai_ok
        return False, False, False
    except:
        return False, False, False
