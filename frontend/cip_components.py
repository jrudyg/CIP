"""
CIP Extended Components
=======================
Additional components for zone-based layout system.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Callable


def filter_bar(
    filters: List[Dict[str, Any]],
    key_prefix: str = "filter"
) -> Dict[str, Any]:
    """
    Horizontal filter bar with configurable slots.

    Args:
        filters: List of filter configs, each with:
            - type: "dropdown" | "text" | "date"
            - label: Display label
            - options: List of options (for dropdown)
            - default: Default value
        key_prefix: Prefix for component keys

    Returns:
        Dict of filter values keyed by label

    Example:
        >>> values = filter_bar([
        ...     {"type": "dropdown", "label": "Status", "options": ["All", "Active", "Pending"], "default": "All"},
        ...     {"type": "text", "label": "Search", "default": ""},
        ... ])
        >>> print(values["Status"])  # "All"
    """
    cols = st.columns(len(filters))
    values = {}

    for idx, (col, f) in enumerate(zip(cols, filters)):
        with col:
            key = f"{key_prefix}_{idx}"
            ftype = f.get("type", "text")
            label = f.get("label", "")

            if ftype == "dropdown":
                options = f.get("options", [])
                default = f.get("default")
                index = 0
                if default is not None and default in options:
                    index = options.index(default)
                values[label] = st.selectbox(label, options=options, index=index, key=key)

            elif ftype == "text":
                values[label] = st.text_input(label, value=f.get("default", ""), key=key)

            elif ftype == "date":
                values[label] = st.date_input(label, value=f.get("default"), key=key)

    return values


def smart_list(
    items: List[Dict[str, Any]],
    mode: str = "default",
    key_prefix: str = "list"
) -> Optional[str]:
    """
    Flexible list component with multiple display modes.

    Args:
        items: List of items, each with:
            - title: Main text
            - subtitle: Secondary text (optional)
            - timestamp: Datetime string (optional)
            - status: Status string (optional)
            - id: Unique identifier (optional)
        mode: "default" | "accordion" | "compact" | "timestamped"
        key_prefix: Prefix for component keys

    Returns:
        ID of clicked item (if clickable), None otherwise

    Example:
        >>> items = [
        ...     {"title": "Contract A", "subtitle": "MSA", "status": "Active"},
        ...     {"title": "Contract B", "subtitle": "NDA", "status": "Pending"}
        ... ]
        >>> smart_list(items, mode="compact")
    """
    clicked = None

    for idx, item in enumerate(items):
        if mode == "accordion":
            with st.expander(item.get("title", "Untitled"), expanded=False):
                if item.get("subtitle"):
                    st.write(item["subtitle"])
                if item.get("timestamp"):
                    st.caption(item["timestamp"])

        elif mode == "compact":
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{item.get('title', 'Untitled')}**")
            with col2:
                if item.get("status"):
                    st.caption(item["status"])

        elif mode == "timestamped":
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item.get('title', 'Untitled')}**")
                if item.get("subtitle"):
                    st.caption(item["subtitle"])
            with col2:
                if item.get("timestamp"):
                    st.caption(item["timestamp"])

        else:  # default
            st.markdown(f"**{item.get('title', 'Untitled')}**")
            if item.get("subtitle"):
                st.caption(item["subtitle"])

        if idx < len(items) - 1:
            st.divider()

    return clicked


def data_table(
    data: List[Dict[str, Any]],
    columns: List[str],
    selectable: bool = False,
    key: str = "table"
) -> List[Dict[str, Any]]:
    """
    Sortable data table with optional row selection.

    Args:
        data: List of row dictionaries
        columns: Column keys to display
        selectable: Enable row selection
        key: Component key

    Returns:
        Selected rows if selectable=True, otherwise empty list

    Example:
        >>> data = [
        ...     {"name": "Contract A", "value": 100000, "status": "Active"},
        ...     {"name": "Contract B", "value": 250000, "status": "Pending"}
        ... ]
        >>> selected = data_table(data, columns=["name", "value"], selectable=True)
    """
    import pandas as pd

    if not data:
        st.info("No data to display")
        return []

    df = pd.DataFrame(data)

    if columns:
        df = df[[c for c in columns if c in df.columns]]

    if selectable:
        try:
            # Streamlit 1.35+
            event = st.dataframe(df, use_container_width=True, key=key, on_select="rerun", selection_mode="multi-row")
            selected_indices = event.selection.rows if hasattr(event, 'selection') and event.selection else []
            return [data[i] for i in selected_indices if i < len(data)]
        except TypeError:
            # Fallback for older Streamlit
            st.dataframe(df, use_container_width=True, key=key)
            st.caption("⚠️ Row selection requires Streamlit 1.35+")
            return []
    else:
        st.dataframe(df, use_container_width=True, key=key)
        return []


def split_panel(
    left_content: Callable,
    right_content: Callable,
    ratio: tuple = (1, 1)
) -> None:
    """
    Two-column split panel layout.

    Args:
        left_content: Function to render left panel content
        right_content: Function to render right panel content
        ratio: Column width ratio (default 1:1, e.g., (2, 1) for 2:1)

    Example:
        >>> def show_version_1():
        ...     st.write("Version 1 text here...")
        >>>
        >>> def show_version_2():
        ...     st.write("Version 2 text here...")
        >>>
        >>> split_panel(show_version_1, show_version_2, ratio=(1, 1))
    """
    col1, col2 = st.columns(ratio)

    with col1:
        left_content()

    with col2:
        right_content()


def document_viewer(
    content: str,
    height: int = 400,
    highlights: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Scrollable document viewer with optional text highlights.

    Args:
        content: Document text content
        height: Viewer height in pixels
        highlights: List of highlight configs with:
            - text: Text to highlight
            - color: Highlight color (hex code, default "#FBBF24")

    Example:
        >>> document_viewer(
        ...     content="This is a contract...",
        ...     highlights=[
        ...         {"text": "liability", "color": "#EF4444"},
        ...         {"text": "termination", "color": "#F97316"}
        ...     ]
        ... )
    """
    display_content = content

    if highlights:
        for h in highlights:
            text = h.get("text", "")
            color = h.get("color", "#FBBF24")
            if text:
                # Escape HTML in text to prevent injection
                import html
                safe_text = html.escape(text)
                safe_display = html.escape(text)
                display_content = display_content.replace(
                    text,
                    f'<mark style="background-color:{color};padding:2px 4px;border-radius:2px;">{safe_display}</mark>'
                )

    viewer_html = f'''
    <div style="
        height: {height}px;
        overflow-y: auto;
        background-color: #1E293B;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #334155;
        font-family: 'Courier New', monospace;
    ">
        <pre style="
            white-space: pre-wrap;
            color: #E2E8F0;
            font-family: inherit;
            margin: 0;
            line-height: 1.6;
        ">{display_content}</pre>
    </div>
    '''
    st.markdown(viewer_html, unsafe_allow_html=True)


def action_bar(
    actions: List[Dict[str, Any]],
    key_prefix: str = "action"
) -> Optional[str]:
    """
    Horizontal row of icon action buttons.

    Args:
        actions: List of action configs with:
            - icon: Emoji icon
            - label: Button label
            - tooltip: Hover tooltip (optional, not implemented)
        key_prefix: Prefix for button keys

    Returns:
        Label of clicked action, None if no click

    Example:
        >>> clicked = action_bar([
        ...     {"icon": "📥", "label": "Download"},
        ...     {"icon": "📤", "label": "Export"},
        ...     {"icon": "🗑️", "label": "Delete"}
        ... ])
        >>> if clicked == "Download":
        ...     download_file()
    """
    cols = st.columns(len(actions))

    for idx, (col, action) in enumerate(zip(cols, actions)):
        with col:
            key = f"{key_prefix}_{idx}"
            icon = action.get("icon", "")
            label = action.get("label", "Action")
            btn_label = f"{icon} {label}".strip()

            if st.button(btn_label, key=key, use_container_width=True):
                return label

    return None


def system_status(
    api_status: bool = True,
    db_status: bool = True,
    ai_status: bool = True
) -> None:
    """
    System health status indicator with colored dots.

    Args:
        api_status: API health (True=green dot, False=red dot)
        db_status: Database health
        ai_status: AI service health

    Example:
        >>> # Show in sidebar
        >>> with st.sidebar:
        ...     system_status(api_status=True, db_status=True, ai_status=False)
    """
    def status_dot(healthy: bool, label: str) -> str:
        color = "#10B981" if healthy else "#EF4444"
        return f'''
        <span style="color:{color};font-size:0.875rem;" title="{label}">●</span>
        <span style="color:#64748B;font-size:0.625rem;margin-right:0.75rem;">{label}</span>
        '''

    status_html = f'''
    <div style="
        display: flex;
        gap: 0.25rem;
        align-items: center;
        justify-content: flex-end;
        padding: 0.5rem;
        background-color: #0F172A;
        border-radius: 0.25rem;
    ">
        {status_dot(api_status, "API")}
        {status_dot(db_status, "DB")}
        {status_dot(ai_status, "AI")}
    </div>
    '''
    st.markdown(status_html, unsafe_allow_html=True)


# Verification checklist
__all__ = [
    'filter_bar',
    'smart_list',
    'data_table',
    'split_panel',
    'document_viewer',
    'action_bar',
    'system_status'
]
