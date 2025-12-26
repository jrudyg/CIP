"""
Global Streamlit CSS overrides for CIP.

This is where we fix:
- DataFrame width/overflow
- Block container max-width and padding
- Code block wrapping

Individual pages must NOT declare their own <style> blocks
for these concerns; they should rely on this module.
"""

import streamlit as st


def inject_streamlit_overrides() -> None:
    """Inject global CSS overrides into the app."""
    st.markdown(
        """
        <style>
        /* Ensure dataframes span the available width cleanly */
        [data-testid="stDataFrame"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        [data-testid="stDataFrame"] > div {
            width: 100% !important;
            max-width: 100% !important;
        }

        /* Normalize main content width and horizontal padding */
        .main .block-container {
            max-width: 1200px;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Make long code samples wrap instead of overflowing */
        .stCodeBlock, pre, code {
            max-width: 100% !important;
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
