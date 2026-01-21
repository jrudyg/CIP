"""
Redline Formatter Utility
Canonical implementations for redline text formatting in CIP.

Consolidated from:
- frontend/pages/5_Redline_Reviews.py:345 (format_redline)
- frontend/pages/5_Redline_Reviews.py:530 (format_redline_html)
"""

import re


def format_redline(text: str) -> str:
    """Convert ~~del~~ to red strikethrough, `add` to green bold."""
    if not text:
        return ""
    # Handle deletions: ~~deleted text~~
    text = re.sub(
        r'~~(.+?)~~',
        r'<span style="color:#EF4444;text-decoration:line-through;background:rgba(239,68,68,0.1);padding:0 2px;">\1</span>',
        text
    )
    # Handle additions: `added text`
    text = re.sub(
        r'`([^`]+)`',
        r'<span style="color:#22C55E;font-weight:600;background:rgba(34,197,94,0.15);padding:0 4px;border-radius:2px;">\1</span>',
        text
    )
    return text


def format_redline_html(text: str) -> str:
    """Convert redline delimiters to styled HTML.

    - ~~text~~ becomes strikethrough (red, deleted)
    - `text` becomes highlighted (green, added)
    """
    # Escape HTML entities first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Convert ~~strikethrough~~ to red deletion styling
    text = re.sub(
        r'~~(.+?)~~',
        r'<span style="text-decoration: line-through; color: #ff6b6b; background-color: rgba(239,68,68,0.1); padding: 1px 3px;">\1</span>',
        text,
        flags=re.DOTALL
    )

    # Convert `backticks` to green addition styling
    text = re.sub(
        r'`(.+?)`',
        r'<span style="background-color: #2d5a3d; color: #90EE90; padding: 2px 4px; border-radius: 3px;">\1</span>',
        text,
        flags=re.DOTALL
    )

    # Convert newlines to <br> for HTML display
    text = text.replace("\n", "<br>")


    return text
