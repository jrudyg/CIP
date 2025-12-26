"""
Enhanced Error Handling for CIP Frontend
User-friendly error messages with actionable guidance
"""

import streamlit as st
import traceback
from typing import Optional, Callable, Any
import requests

from ui_components import toast_error

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_possible: bool = True):
        self.message = message
        self.status_code = status_code
        self.retry_possible = retry_possible
        super().__init__(self.message)

def handle_api_error(error: Exception, operation: str = "operation",
                    show_retry: bool = True, retry_callback: Optional[Callable[..., Any]] = None) -> None:
    """
    Display user-friendly error message with actionable guidance

    Args:
        error: The exception that occurred
        operation: Name of the operation that failed
        show_retry: Whether to show a retry button
        retry_callback: Function to call when retry button is clicked
    """

    # Determine error type and message
    if isinstance(error, requests.exceptions.ConnectionError):
        title = "Cannot Connect to Backend"
        message = "The CIP backend service is not running or not accessible."
        help_text = """
        **What to do:**
        1. Check if the backend API is running
        2. Run: `python backend/api.py`
        3. Verify the API is accessible at http://127.0.0.1:5000
        4. Check your firewall settings
        """
        retry_possible = True

    elif isinstance(error, requests.exceptions.Timeout):
        title = "Request Timeout"
        message = f"The {operation} is taking longer than expected."
        help_text = """
        **What to do:**
        1. The analysis may still be processing - wait a moment
        2. Check the backend logs for progress
        3. Try refreshing the page
        4. Contact support if the issue persists
        """
        retry_possible = True

    elif isinstance(error, requests.exceptions.HTTPError):
        status_code = getattr(error.response, 'status_code', None)
        title = f"API Error ({status_code})"

        if status_code == 400:
            message = "Invalid request - please check your input."
            help_text = """
            **What to do:**
            1. Verify all required fields are filled
            2. Check file format (PDF, DOCX, or TXT only)
            3. Ensure file size is under 50MB
            """
        elif status_code == 404:
            message = "The requested resource was not found."
            help_text = """
            **What to do:**
            1. Verify the contract exists in the database
            2. Try refreshing the contract list
            3. The contract may have been deleted
            """
        elif status_code == 503:
            message = "Service temporarily unavailable."
            help_text = """
            **What to do:**
            1. The backend service may be starting up
            2. Wait 30 seconds and try again
            3. Check if the API service is running
            """
        else:
            message = f"An error occurred (Status: {status_code})"
            help_text = """
            **What to do:**
            1. Try the operation again
            2. Check the browser console for details
            3. Contact support with the error code
            """
        retry_possible = status_code in [408, 429, 500, 502, 503, 504]

    elif isinstance(error, ValueError):
        title = "Invalid Input"
        message = str(error)
        help_text = """
        **What to do:**
        1. Check that all inputs are in the correct format
        2. Verify dates are valid
        3. Ensure numeric fields contain only numbers
        """
        retry_possible = False

    elif isinstance(error, FileNotFoundError):
        title = "File Not Found"
        message = "The requested file could not be found."
        help_text = """
        **What to do:**
        1. Verify the file was successfully uploaded
        2. Check if the file still exists on disk
        3. Try uploading the file again
        """
        retry_possible = True

    else:
        title = "Unexpected Error"
        message = str(error) or "An unexpected error occurred"
        help_text = """
        **What to do:**
        1. Try the operation again
        2. Refresh the page
        3. If the problem persists, contact support
        """
        retry_possible = True

    # Display error message
    st.error(f"**{title}**")
    st.markdown(message)

    # Show help text
    with st.expander("ℹ️ How to fix this"):
        st.markdown(help_text)

    # Show technical details in debug expander
    with st.expander("🔍 Technical Details (for developers)"):
        st.code(f"Error Type: {type(error).__name__}\nMessage: {str(error)}")
        st.code(traceback.format_exc())

    # Retry button
    if show_retry and retry_possible and retry_callback is not None:
        if st.button("🔄 Retry", key=f"retry_{operation}"):
            retry_callback()

def safe_api_call(func: Callable, operation: str = "operation",
                 success_message: Optional[str] = None,
                 show_retry: bool = True) -> Optional[Any]:
    """
    Wrapper for API calls with automatic error handling

    Args:
        func: Function to call (should make the API request)
        operation: Name of the operation for error messages
        success_message: Message to show on success (optional)
        show_retry: Whether to show retry button on failure

    Returns:
        Result of func() if successful, None if error

    Example:
        result = safe_api_call(
            lambda: requests.post(url, json=data),
            operation="contract upload",
            success_message="Contract uploaded successfully!"
        )
    """
    try:
        result = func()

        # Show success message if provided
        if success_message:
            st.success(f"✅ {success_message}")

        return result

    except Exception as e:
        handle_api_error(
            error=e,
            operation=operation,
            show_retry=show_retry,
            retry_callback=func if show_retry else None
        )
        return None

def validate_file_upload(file) -> bool:
    """
    Validate uploaded file with user-friendly error messages

    Args:
        file: Streamlit UploadedFile object

    Returns:
        True if valid, False otherwise (with error message displayed)
    """
    if not file:
        toast_error("Please select a file to upload")
        return False

    # Check file type
    allowed_extensions = ['.pdf', '.docx', '.txt']
    file_ext = file.name.split('.')[-1].lower()

    if f".{file_ext}" not in allowed_extensions:
        st.error("**Invalid File Type**")
        st.markdown(f"File: `{file.name}`")
        st.markdown(f"Detected type: `.{file_ext}`")
        st.markdown(f"**Allowed types:** {', '.join(allowed_extensions)}")
        with st.expander("ℹ️ Why is this file type not supported?"):
            st.markdown("""
            Currently, CIP supports:
            - **PDF**: Most common contract format
            - **DOCX**: Microsoft Word documents
            - **TXT**: Plain text files

            If you have a different format:
            1. Convert to PDF using your document viewer
            2. Export as .docx from your word processor
            3. Save as .txt for simple text contracts
            """)
        return False

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    file_size = file.size

    if file_size > max_size:
        st.error("**File Too Large**")
        st.markdown(f"File size: {file_size / 1024 / 1024:.1f} MB")
        st.markdown(f"Maximum allowed: 50 MB")
        with st.expander("ℹ️ How to reduce file size"):
            st.markdown("""
            **For PDF files:**
            1. Use a PDF compressor tool (e.g., Adobe Acrobat)
            2. Reduce image quality if the PDF contains scans
            3. Remove unnecessary pages

            **For DOCX files:**
            1. Compress embedded images
            2. Remove formatting and use plain text
            3. Convert to PDF for better compression
            """)
        return False

    return True

def with_error_handling(operation: str):
    """
    Decorator for functions that need error handling

    Example:
        @with_error_handling("contract analysis")
        def analyze_contract(contract_id):
            # ... your code ...
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_api_error(e, operation)
                return None
        return wrapper
    return decorator

__all__ = [
    'APIError',
    'handle_api_error',
    'safe_api_call',
    'validate_file_upload',
    'with_error_handling'
]
