"""
Standard CIP page wrapper.

ALL CIP pages should enter through render_page(...).

This centralizes:
- Streamlit page config
- Theme + dark theme
- Global CSS overrides
- Contract context initialization
- Sidebar branding
- System health checks
- zone_layout plumbing
"""

import streamlit as st

from theme_system import apply_theme
# NOTE: inject_cip_logo is handled in app.py, not here
from theme_overrides import inject_streamlit_overrides
from zone_layout import zone_layout, check_system_health
from components.contract_context import init_contract_context


def render_page(
    page_title: str,
    page_icon: str,
    layout: str = "wide",
    *,
    content_fn=None,
    z1=None,
    z2=None,
    z3=None,
    z4=None,
    z5=None,
    z6=None,
    z7=None,
) -> None:
    """
    Standard entry point for ALL CIP pages.

    Usage patterns:

    1) Simple zone-based pages:
       render_page(
           page_title="Contracts Portfolio",
           page_icon="📊",
           z1=z1_header_and_filters,
           z2=z2_kpi_summary,
           ...
       )

    2) Complex pages that want full control:
       def my_content(**kwargs):
           ...  # can call zone_layout internally, or do custom layout

       render_page(
           page_title="Get Reports",
           page_icon="📑",
           content_fn=my_content,
       )
    """

    # Page-level config
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

    # Theme + dark theme + global overrides
    apply_theme()

    from components.theme import inject_dark_theme

    inject_dark_theme()
    inject_streamlit_overrides()

    # Initialize contract context
    init_contract_context()

    # System health
    api_healthy, db_healthy, ai_healthy = check_system_health()

    # Sidebar branding is handled in app.py

    # Delegate to content function OR zone layout
    if content_fn is not None:
        content_fn(
            api_healthy=api_healthy,
            db_healthy=db_healthy,
            ai_healthy=ai_healthy,
        )
    else:
        zone_layout(
            z1=z1,
            z2=z2,
            z3=z3,
            z4=z4,
            z5=z5,
            z6=z6,
            z7=z7,
            z7_system_status=True,
            api_healthy=api_healthy,
            db_healthy=db_healthy,
            ai_healthy=ai_healthy,
        )
