"""
CIP - Contract Intelligence Platform
Main Streamlit Application Entry Point
"""

import streamlit as st
import sys
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent))

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="CIP - Contract Intelligence Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject centralized dark theme
from components.theme import inject_dark_theme
inject_dark_theme()

# === SPLASH SCREEN ===
from components.splash import show_splash_screen, init_splash
init_splash()
if show_splash_screen():
    st.stop()

# ============================================================
# SIDEBAR BRANDING - CIP LOGO AT TOP (ABSOLUTE POSITIONING)
# ============================================================
st.markdown("""
    <style>
    /* Position sidebar content container relatively */
    [data-testid="stSidebar"] > div:first-child {
        position: relative !important;
        padding-top: 100px !important;
    }
    
    /* CIP Logo - Absolute positioned at TOP */
    [data-testid="stSidebar"] > div:first-child::before {
        content: "CIP";
        position: absolute !important;
        top: 24px !important;
        left: 0 !important;
        right: 0 !important;
        display: block !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #8B5CF6 !important;
        letter-spacing: 6px !important;
        text-align: center !important;
        z-index: 1000 !important;
    }
    
    /* Tagline below logo */
    [data-testid="stSidebar"] > div:first-child::after {
        content: "CONTRACT INTELLIGENCE PLATFORM";
        position: absolute !important;
        top: 64px !important;
        left: 0 !important;
        right: 0 !important;
        display: block !important;
        font-size: 9px !important;
        font-weight: 500 !important;
        color: #64748B !important;
        letter-spacing: 2px !important;
        text-align: center !important;
        z-index: 1000 !important;
    }
    
    /* Hide any user-added sidebar content (removes bottom logo) */
    [data-testid="stSidebarUserContent"] {
        display: none !important;
    }
    
    /* Ensure nav items don't have borders */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"],
    [data-testid="stSidebarNavLink"] {
        border: none !important;
        box-shadow: none !important;
    }

    /* CONSISTENT NAV LINK SPACING - Overrides all other CSS */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNavLink"],
    [data-testid="stSidebar"] a.stPageLink {
        display: flex !important;
        align-items: center !important;
        padding: 10px 16px !important;
        margin: 2px 8px !important;
        border-radius: 8px !important;
        min-height: 40px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #94A3B8 !important;
        background: transparent !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNavLink"]:hover {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #E2E8F0 !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.15) 100%) !important;
        border-left: 3px solid #3B82F6 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* No scrollbar */
    [data-testid="stSidebar"] > div:first-child {
        overflow: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)
# ============================================================
# END SIDEBAR BRANDING
# ============================================================

# Page definitions - 9 pages
pages = [
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Contracts_Portfolio.py", title="Contracts Portfolio", icon="📊"),
    st.Page("pages/3_Intelligent_Intake.py", title="Intelligent Intake", icon="🧠"),
    st.Page("pages/4_Risk_Analysis.py", title="Risk Analysis", icon="🔍"),
    st.Page("pages/5_Redline_Reviews.py", title="Redline Reviews", icon="📝"),
    st.Page("pages/6_Compare_Versions.py", title="Compare Versions", icon="⚖️"),
    st.Page("pages/7_Negotiation.py", title="Negotiation", icon="🤝"),
    st.Page("pages/8_Reports.py", title="Reports", icon="📋"),
    st.Page("pages/9_Contract_Details.py", title="Contract Details", icon="📄"),
]

# Navigation
nav = st.navigation(pages)
nav.run()
