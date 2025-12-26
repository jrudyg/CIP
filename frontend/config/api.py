"""
Central API configuration for CIP frontend.

All pages should import API_BASE_URL (and related constants) from here
instead of hard-coding URLs or timeouts.
"""

API_BASE_URL: str = "http://localhost:5000/api"

# Default timeout for most API calls (seconds)
API_TIMEOUT_DEFAULT: int = 30
