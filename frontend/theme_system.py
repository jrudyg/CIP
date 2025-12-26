"""
CIP Theme System - Modern Dark Theme
Professional dark color palette optimized for extended use

Usage:
    from theme_system import apply_theme
    apply_theme()
"""

import streamlit as st
from typing import Dict, Literal, Optional

# Dark Theme Color Palette
THEME = {
        'name': 'Modern Dark',

        # Primary colors - Blue to Purple gradient
        'primary': '#3B82F6',           # Primary blue
        'primary_light': '#60A5FA',     # Lighter blue
        'primary_dark': '#2563EB',      # Darker blue

        # Secondary colors - Purple accent
        'secondary': '#8B5CF6',         # Primary purple
        'secondary_light': '#A78BFA',   # Lighter purple
        'secondary_dark': '#7C3AED',    # Darker purple

        # Accent colors - Complementary purple
        'accent': '#8B5CF6',            # Purple
        'accent_light': '#A78BFA',      # Light purple
        'accent_dark': '#7C3AED',       # Dark purple

        # Neutrals - Modern dark slate (from design)
        'background': '#0F172A',        # Near-black background
        'surface': '#1E293B',           # Dark slate cards/sidebar
        'surface_raised': '#334155',    # Slightly lighter for depth

        'text_primary': '#FFFFFF',      # Pure white
        'text_secondary': '#E2E8F0',    # Light gray
        'text_tertiary': '#94A3B8',     # Medium gray (muted)
        'text_disabled': '#64748B',     # Dark gray (subtle)

        # Borders & dividers (subtle in dark mode)
        'border': 'rgba(255, 255, 255, 0.05)',     # Subtle border
        'border_light': 'rgba(255, 255, 255, 0.03)', # Very subtle
        'divider': 'rgba(255, 255, 255, 0.1)',     # Visible divider

        # Status colors (from Modern Dark design)
        'success': '#10B981',           # Green
        'success_bg': 'rgba(16, 185, 129, 0.15)',  # Green background
        'warning': '#F59E0B',           # Amber
        'warning_bg': 'rgba(245, 158, 11, 0.15)',  # Amber background
        'error': '#EF4444',             # Red
        'error_bg': 'rgba(239, 68, 68, 0.15)',     # Red background
        'info': '#3B82F6',              # Blue
        'info_bg': 'rgba(59, 130, 246, 0.15)',     # Blue background

        # Gradients (blue to purple)
        'gradient_primary': 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
        'gradient_secondary': 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)',
        'gradient_accent': 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
        'gradient_neutral': 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',

        # Shadows (blue glow in dark mode)
        'shadow_sm': '0 1px 2px 0 rgba(59, 130, 246, 0.1)',
        'shadow_md': '0 4px 6px -1px rgba(59, 130, 246, 0.15), 0 2px 4px -1px rgba(59, 130, 246, 0.1)',
        'shadow_lg': '0 10px 15px -3px rgba(59, 130, 246, 0.2), 0 4px 6px -2px rgba(59, 130, 246, 0.15)',
        'shadow_xl': '0 20px 25px -5px rgba(59, 130, 246, 0.25), 0 10px 10px -5px rgba(59, 130, 246, 0.2)',
}


def get_theme() -> Dict[str, str]:
    """
    Get dark theme colors

    Returns:
        Dictionary of theme colors and styles
    """
    return THEME


def get_current_theme() -> Dict[str, str]:
    """Get current theme (always dark)"""
    return THEME


def apply_theme():
    """
    Apply dark theme to Streamlit app via CSS injection
    """
    theme = THEME
    
    css = f"""
    <style>
    /* Global theme variables */
    :root {{
        --primary: {theme['primary']};
        --primary-light: {theme['primary_light']};
        --primary-dark: {theme['primary_dark']};
        
        --secondary: {theme['secondary']};
        --secondary-light: {theme['secondary_light']};
        --secondary-dark: {theme['secondary_dark']};
        
        --accent: {theme['accent']};
        --accent-light: {theme['accent_light']};
        --accent-dark: {theme['accent_dark']};
        
        --background: {theme['background']};
        --surface: {theme['surface']};
        --surface-raised: {theme['surface_raised']};
        
        --text-primary: {theme['text_primary']};
        --text-secondary: {theme['text_secondary']};
        --text-tertiary: {theme['text_tertiary']};
        --text-disabled: {theme['text_disabled']};
        
        --border: {theme['border']};
        --border-light: {theme['border_light']};
        --divider: {theme['divider']};
        
        --success: {theme['success']};
        --success-bg: {theme['success_bg']};
        --warning: {theme['warning']};
        --warning-bg: {theme['warning_bg']};
        --error: {theme['error']};
        --error-bg: {theme['error_bg']};
        --info: {theme['info']};
        --info-bg: {theme['info_bg']};
        
        --shadow-sm: {theme['shadow_sm']};
        --shadow-md: {theme['shadow_md']};
        --shadow-lg: {theme['shadow_lg']};
        --shadow-xl: {theme['shadow_xl']};
    }}
    
    /* Main app background */
    .stApp {{
        background-color: {theme['background']};
        color: {theme['text_primary']};
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {theme['gradient_neutral']};
        border-right: 1px solid {theme['border']};
    }}

    [data-testid="stSidebar"] .css-1d391kg {{
        color: {theme['text_primary']};
    }}

    /* NOTE: Sidebar nav link styling is handled in app.py ONLY */
    /* Do NOT add nav link CSS here - it causes inconsistent spacing */

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {theme['text_primary']} !important;
        font-weight: 600;
    }}
    
    h1 {{
        background: {theme['gradient_primary']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Paragraphs and text */
    p, span, div {{
        color: {theme['text_secondary']};
    }}
    
    /* Cards and containers */
    .stCard, [data-testid="stMetricValue"] {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: {theme['shadow_md']};
        transition: all 0.3s ease;
    }}
    
    .stCard:hover {{
        box-shadow: {theme['shadow_lg']};
        transform: translateY(-2px);
    }}
    
    /* Buttons - Primary */
    .stButton > button[kind="primary"] {{
        background: {theme['gradient_primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        box-shadow: {theme['shadow_md']};
        transition: all 0.3s ease;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        box-shadow: {theme['shadow_lg']};
        transform: translateY(-2px);
    }}
    
    /* Buttons - Secondary */
    .stButton > button[kind="secondary"] {{
        background-color: {theme['surface']};
        color: {theme['primary']};
        border: 2px solid {theme['primary']};
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background-color: {theme['primary']};
        color: white;
        transform: translateY(-2px);
    }}
    
    /* Buttons - Default */
    .stButton > button {{
        background-color: {theme['surface']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {theme['surface_raised']};
        border-color: {theme['primary']};
        box-shadow: {theme['shadow_sm']};
    }}
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        background-color: {theme['surface']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {theme['primary']};
        box-shadow: 0 0 0 3px {theme['primary']}33;
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: {theme['primary']};
        font-size: 2rem;
        font-weight: 700;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {theme['text_secondary']};
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    [data-testid="stMetricDelta"] {{
        font-size: 0.875rem;
        font-weight: 600;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: {theme['surface']};
        border-radius: 8px;
        padding: 0.25rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {theme['text_secondary']};
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {theme['surface_raised']};
        color: {theme['text_primary']};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {theme['gradient_primary']};
        color: white !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {theme['surface']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .streamlit-expanderHeader:hover {{
        background-color: {theme['surface_raised']};
        border-color: {theme['primary']};
    }}
    
    /* Success/Warning/Error/Info messages */
    .stSuccess {{
        background-color: {theme['success_bg']};
        color: {theme['success']};
        border-left: 4px solid {theme['success']};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stWarning {{
        background-color: {theme['warning_bg']};
        color: {theme['warning']};
        border-left: 4px solid {theme['warning']};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stError {{
        background-color: {theme['error_bg']};
        color: {theme['error']};
        border-left: 4px solid {theme['error']};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stInfo {{
        background-color: {theme['info_bg']};
        color: {theme['info']};
        border-left: 4px solid {theme['info']};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    /* Divider */
    hr {{
        border: none;
        border-top: 1px solid {theme['divider']};
        margin: 2rem 0;
    }}
    
    /* Progress bar */
    .stProgress > div > div > div {{
        background: {theme['gradient_secondary']};
        border-radius: 8px;
    }}
    
    /* Dataframe/Table */
    .stDataFrame {{
        border: 1px solid {theme['border']};
        border-radius: 8px;
        overflow: hidden;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        background-color: {theme['surface']};
        border: 2px dashed {theme['border']};
        border-radius: 12px;
        padding: 2rem;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {theme['primary']};
        background-color: {theme['surface_raised']};
    }}
    
    /* Spinner */
    .stSpinner > div {{
        border-top-color: {theme['primary']} !important;
    }}
    
    /* Links */
    a {{
        color: {theme['secondary']};
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    a:hover {{
        color: {theme['secondary_light']};
        text-decoration: underline;
    }}
    
    /* Radio buttons */
    [data-testid="stRadio"] > label {{
        color: {theme['text_primary']};
        font-weight: 600;
    }}
    
    /* Checkboxes */
    .stCheckbox > label {{
        color: {theme['text_primary']};
    }}
    
    /* Selectbox */
    [data-baseweb="select"] {{
        background-color: {theme['surface']};
        border-radius: 8px;
    }}
    
    /* Toast notifications */
    .stToast {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        box-shadow: {theme['shadow_xl']};
    }}
    
    /* Scrollbar (webkit browsers) */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {theme['background']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {theme['border']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {theme['divider']};
    }}
    
    /* Custom classes for specific components */
    .gradient-header {{
        background: {theme['gradient_primary']};
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: {theme['shadow_lg']};
    }}
    
    .metric-card {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: {theme['shadow_md']};
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        box-shadow: {theme['shadow_lg']};
        transform: translateY(-2px);
        border-color: {theme['primary']};
    }}
    
    .status-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }}
    
    .badge-success {{
        background-color: {theme['success_bg']};
        color: {theme['success']};
    }}
    
    .badge-warning {{
        background-color: {theme['warning_bg']};
        color: {theme['warning']};
    }}
    
    .badge-error {{
        background-color: {theme['error_bg']};
        color: {theme['error']};
    }}
    
    .badge-info {{
        background-color: {theme['info_bg']};
        color: {theme['info']};
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)


# Utility functions for themed components
def metric_card(label: str, value: str, delta: Optional[str] = None, delta_color: str = "normal"):
    """Create a themed metric card"""
    theme = get_current_theme()
    
    delta_html = ""
    if delta:
        delta_colors = {
            'normal': theme['text_secondary'],
            'success': theme['success'],
            'warning': theme['warning'],
            'error': theme['error'],
            'inverse': theme['text_tertiary']
        }
        delta_html = f'<div style="color: {delta_colors.get(delta_color, theme["text_secondary"])}; font-size: 0.875rem; font-weight: 600; margin-top: 0.5rem;">{delta}</div>'
    
    html = f"""
    <div class="metric-card">
        <div style="color: {theme['text_secondary']}; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">{label}</div>
        <div style="color: {theme['primary']}; font-size: 2rem; font-weight: 700;">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def gradient_header(title: str, subtitle: Optional[str] = None):
    """Create a gradient header"""
    theme = get_current_theme()
    
    subtitle_html = f'<div style="font-size: 1rem; opacity: 0.9; margin-top: 0.5rem;">{subtitle}</div>' if subtitle else ''
    
    html = f"""
    <div class="gradient-header">
        <div style="font-size: 2rem; font-weight: 700;">{title}</div>
        {subtitle_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def status_badge(text: str, status: Literal['success', 'warning', 'error', 'info']):
    """Create a status badge"""
    return f'<span class="status-badge badge-{status}">{text}</span>'


def inject_cip_logo():
    """
    Inject clickable CIP logo at top of sidebar.
    Clicking logo restarts splash screen.

    Uses CSS flexbox reordering to position above navigation.
    """

    # Clickable button - will be styled as gradient text
    with st.sidebar:
        if st.button("CIP", key="cip_logo_btn", use_container_width=False):
            st.session_state.splash_complete = False
            st.rerun()

        # Subtitle
        st.markdown(
            '<p style="text-align:center; color:#64748B; font-size:11px; '
            'letter-spacing:1px; text-transform:uppercase; margin-top:-10px; '
            'margin-bottom:20px;">Contract Intelligence</p>',
            unsafe_allow_html=True
        )

    # All the CSS magic
    st.markdown("""
        <style>
        /* ==============================================
           CIP LOGO POSITIONING - Logo above centered nav
           ============================================== */

        /* User content (CIP logo) at top */
        [data-testid="stSidebarUserContent"] {
            order: 1 !important;
            flex: 0 0 auto !important;
        }

        /* ==============================================
           CIP LOGO BUTTON STYLING
           ============================================== */

        /* Target the CIP button specifically */
        [data-testid="stSidebarUserContent"] button[kind="secondary"] {
            background: transparent !important;
            border: 2px solid transparent !important;
            border-image: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%) 1 !important;
            border-radius: 12px !important;
            padding: 16px 32px !important;
            margin: 0 auto 5px auto !important;
            display: block !important;
            width: auto !important;
            min-width: 120px !important;
        }

        /* The button text - gradient */
        [data-testid="stSidebarUserContent"] button[kind="secondary"] p {
            font-size: 32px !important;
            font-weight: 800 !important;
            letter-spacing: 4px !important;
            background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            margin: 0 !important;
        }

        /* Hover effect */
        [data-testid="stSidebarUserContent"] button[kind="secondary"]:hover {
            border-image: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%) 1 !important;
            transform: scale(1.02);
            transition: all 0.2s ease !important;
        }

        </style>
    """, unsafe_allow_html=True)
