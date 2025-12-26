# components/system_status.py
import streamlit as st
import requests
from datetime import datetime


def check_system_health(api_base: str = "http://localhost:5000") -> dict:
    health = {
        "api": False,
        "database": False,
        "engine": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        response = requests.get(f"{api_base}/health", timeout=5)
        if response.status_code == 200:
            health["api"] = True
            data = response.json()
            health["database"] = data.get("database", {}).get("contracts", False)
            health["engine"] = data.get("api_key_configured", False)
    except Exception:
        pass
    return health


def render_system_status(compact: bool = True) -> None:
    health = check_system_health()
    if compact:
        api_icon = "🟢" if health["api"] else "🔴"
        db_icon = "🟢" if health["database"] else "🔴"
        engine_icon = "🟢" if health["engine"] else "🔴"
        st.markdown(
            f'<div style="display: flex; gap: 1.5rem; font-size: 0.85rem; color: #9CA3AF;">'
            f'<span>{api_icon} API</span>'
            f'<span>{db_icon} DB</span>'
            f'<span>{engine_icon} Engine</span>'
            f'<span style="margin-left: auto;">Updated: {health["timestamp"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        cols = st.columns(4)
        with cols[0]:
            st.metric("API", "Online" if health["api"] else "Offline")
        with cols[1]:
            st.metric("Database", "Connected" if health["database"] else "Disconnected")
        with cols[2]:
            st.metric("Engine", "Ready" if health["engine"] else "Unavailable")
        with cols[3]:
            st.caption(f"Last check: {health['timestamp']}")
