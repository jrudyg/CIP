# components/theme.py
import streamlit as st


def inject_dark_theme():
    """
    Inject centralized dark theme CSS matching the CIP design system.
    Uses colors from theme_system.py for consistency.
    
    NOTE: Sidebar logo/branding is handled in app.py, NOT here.
    """
    st.markdown(
        """
        <style>

        /************  COLOR PALETTE (CIP Theme)  ************/
        :root {
            --bg-app:        #0F172A;
            --bg-surface:    #1E293B;
            --bg-card:       #1E293B;
            --bg-input:      #1E293B;
            --bg-input-alt:  #334155;
            --border-subtle: rgba(255, 255, 255, 0.05);
            --border-strong: rgba(255, 255, 255, 0.1);
            --accent-main:   #3B82F6;
            --accent-secondary: #8B5CF6;
            --accent-soft:   rgba(59, 130, 246, 0.15);
            --accent-danger: #EF4444;
            --text-main:     #FFFFFF;
            --text-secondary: #E2E8F0;
            --text-muted:    #94A3B8;
            --text-soft:     #64748B;
            --shadow-soft:   0 4px 6px -1px rgba(59, 130, 246, 0.15), 0 2px 4px -1px rgba(59, 130, 246, 0.1);
            --shadow-lg:     0 10px 15px -3px rgba(59, 130, 246, 0.2), 0 4px 6px -2px rgba(59, 130, 246, 0.15);
            --radius-lg:     12px;
            --radius-pill:   999px;
            --gradient-primary: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
            --gradient-neutral: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }

        /************  APP SHELL  ************/
        [data-testid="stAppViewContainer"] {
            background: #0F172A;
            color: var(--text-main);
        }

        [data-testid="stHeader"], header {
            background: #0F172A !important;
        }

        [data-testid="stAppViewBlockContainer"] {
            padding-top: 1.5rem;
        }

        section.main > div {
            max-width: 1200px;
            margin: 0 auto;
        }

        /************  TYPOGRAPHY  ************/
        body, [data-testid="stMarkdownContainer"] {
            color: var(--text-main);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text-main);
            letter-spacing: 0.01em;
        }

        p, label, span {
            color: var(--text-main);
        }

        small, .markdown-text-container p,
        [data-testid="stCaptionContainer"] {
            color: var(--text-soft);
        }

        /************  CARD / CONTAINER LOOK  ************/
        [data-testid="stExpander"],
        [data-testid="stForm"],
        .stTabs [data-baseweb="tab-list"] + div,
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="column"]) {
            background: var(--bg-surface);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-subtle);
            box-shadow: var(--shadow-soft);
        }

        [data-testid="stExpander"] > details {
            background: transparent;
            border-radius: var(--radius-lg);
        }

        [data-testid="stExpander"] summary {
            background: var(--bg-surface);
            padding: 0.8rem 1rem;
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            font-weight: 600;
            color: var(--text-main);
        }

        /************  INPUTS: TEXT, TEXTAREA, NUMBER  ************/
        [data-baseweb="input"],
        [data-baseweb="textarea"] {
            background-color: var(--bg-input) !important;
            border-radius: var(--radius-lg) !important;
            border: 1px solid var(--border-subtle) !important;
            color: var(--text-main) !important;
        }

        [data-baseweb="input"]:hover,
        [data-baseweb="textarea"]:hover {
            border-color: var(--border-strong) !important;
        }

        [data-baseweb="input"]:focus-within,
        [data-baseweb="textarea"]:focus-within {
            border-color: var(--accent-main) !important;
            box-shadow: 0 0 0 1px var(--accent-main) !important;
        }

        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            color: var(--text-main) !important;
            background: transparent !important;
        }

        [data-baseweb="input"] input::placeholder,
        [data-baseweb="textarea"] textarea::placeholder {
            color: var(--text-soft) !important;
        }

        /************  SELECTBOX / MULTISELECT  ************/
        [data-baseweb="select"] > div {
            background-color: var(--bg-input) !important;
            border-radius: var(--radius-lg) !important;
            border: 1px solid var(--border-subtle) !important;
            min-height: 2.5rem;
        }

        [data-baseweb="select"] > div:hover {
            border-color: var(--border-strong) !important;
        }

        [data-baseweb="select"]:focus-within > div {
            border-color: var(--accent-main) !important;
            box-shadow: 0 0 0 1px var(--accent-main) !important;
        }

        /* Selected value text - WILDCARD SELECTOR for version compatibility */
        [data-baseweb="select"] [class*="singleValue"] {
            color: #E2E8F0 !important;
        }

        /* Placeholder */
        [data-baseweb="select"] [class*="placeholder"] {
            color: #64748B !important;
        }

        /* Dropdown menu surface */
        [data-baseweb="menu"] {
            background-color: var(--bg-surface) !important;
            border-radius: var(--radius-lg) !important;
            border: 1px solid var(--border-subtle) !important;
            box-shadow: var(--shadow-lg) !important;
        }

        [data-baseweb="menu"] div[role="option"] {
            color: var(--text-main) !important;
        }

        [data-baseweb="menu"] div[role="option"][aria-selected="true"],
        [data-baseweb="menu"] div[role="option"]:hover {
            background-color: var(--accent-soft) !important;
        }

        [data-baseweb="select"] svg {
            fill: var(--text-main) !important;
        }

        /************  CHECKBOXES & RADIOS  ************/
        [data-baseweb="checkbox"] > div {
            color: var(--text-main) !important;
        }

        [data-baseweb="checkbox"] input:checked + div {
            background-color: var(--accent-main) !important;
            border-color: var(--accent-main) !important;
        }

        [data-baseweb="radio"] label {
            color: var(--text-main) !important;
        }

        [data-baseweb="radio"] input:checked + div {
            border-color: var(--accent-main) !important;
        }

        /************  SLIDERS  ************/
        [data-baseweb="slider"] {
            color: var(--accent-main) !important;
        }

        [data-baseweb="slider"] div[role="slider"] {
            background-color: var(--accent-main) !important;
        }

        /************  BUTTONS  ************/
        .stButton > button {
            background: var(--gradient-primary);
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            box-shadow: var(--shadow-soft);
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .stButton > button:focus-visible {
            outline: 2px solid var(--accent-main);
            outline-offset: 2px;
        }

        .secondary-button > button {
            background: var(--bg-surface) !important;
            color: var(--text-main) !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-strong) !important;
        }

        .secondary-button > button:hover {
            background-color: var(--bg-input-alt) !important;
            border-color: var(--accent-main) !important;
        }

        /************  TABS  ************/
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background-color: var(--bg-surface);
            border-radius: 8px;
            padding: 0.25rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: var(--text-muted);
            border-radius: 6px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--bg-input-alt);
            color: var(--text-main);
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--gradient-primary);
            color: white !important;
        }

        /************  SIDEBAR - BASE STYLING ONLY  ************/
        /* Logo positioning is handled in app.py */
        
        [data-testid="stSidebar"] {
            background: #0F172A !important;
            border-right: 1px solid rgba(255,255,255,0.05) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #E2E8F0 !important;
        }

        /* Hide sidebar header/title */
        [data-testid="stSidebarHeader"] {
            display: none !important;
        }

        /* Hide nav separator */
        [data-testid="stSidebarNavSeparator"] {
            display: none !important;
        }

        /* COMPACT nav links */
        [data-testid="stSidebarNavLink"] {
            border-radius: 8px !important;
            margin: 2px 12px !important;
            padding: 10px 14px !important;
            min-height: 40px !important;
            display: flex !important;
            align-items: center !important;
            transition: all 0.15s ease !important;
            background: transparent !important;
        }

        [data-testid="stSidebarNavLink"]:hover {
            background: rgba(59, 130, 246, 0.1) !important;
        }

        [data-testid="stSidebarNavLink"] span {
            color: #94A3B8 !important;
            font-weight: 500 !important;
            font-size: 14px !important;
        }

        /* Active nav link */
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.15) 100%) !important;
            border-left: 3px solid #3B82F6 !important;
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] span {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /************  METRICS & STATUS  ************/
        [data-testid="stMetric"] {
            background: var(--bg-surface);
            padding: 0.9rem 1.1rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-subtle);
            box-shadow: var(--shadow-soft);
        }

        [data-testid="stMetricDelta"] {
            color: #22C55E !important;
        }

        .stAlert {
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-soft);
        }

        /************  DATAFRAME / TABLES  ************/
        [data-testid="stDataFrame"] {
            width: 100% !important;
            max-width: 100% !important;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-subtle);
        }

        [data-testid="stDataFrame"] > div {
            width: 100% !important;
            max-width: 100% !important;
        }

        [data-testid="stDataFrame"] table {
            color: var(--text-main);
        }

        [data-testid="stDataFrame"] thead tr {
            background-color: var(--bg-input-alt);
        }

        [data-testid="stDataFrame"] tbody tr:nth-child(odd) {
            background-color: var(--bg-surface);
        }

        [data-testid="stDataFrame"] tbody tr:nth-child(even) {
            background-color: var(--bg-app);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
