"""
Progress Indicators for CIP
Enhanced progress tracking for long-running operations
"""

import streamlit as st
from typing import List, Optional
import time

class ProgressTracker:
    """Context manager for tracking multi-step progress"""

    def __init__(self, total_steps: int, operation_name: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.progress_bar: Optional[st.delta_generator.DeltaGenerator] = None
        self.status_text: Optional[st.delta_generator.DeltaGenerator] = None
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.progress_bar is not None and self.status_text is not None and self.start_time is not None:
            # Completed successfully
            self.progress_bar.progress(100)
            elapsed = time.time() - self.start_time
            self.status_text.success(f"✅ {self.operation_name} completed in {elapsed:.1f}s")
        elif self.status_text is not None:
            # Error occurred
            self.status_text.error(f"❌ {self.operation_name} failed")
        return False

    def update(self, step_name: str, step_number: Optional[int] = None):
        """Update progress with current step"""
        if step_number is not None:
            self.current_step = step_number
        else:
            self.current_step += 1

        # Calculate progress percentage
        progress = min(int((self.current_step / self.total_steps) * 100), 100)

        # Update UI
        if self.progress_bar is not None:
            self.progress_bar.progress(progress)

        # Calculate time remaining
        if self.start_time is not None and self.status_text is not None:
            elapsed = time.time() - self.start_time
            if self.current_step > 0:
                avg_time_per_step = elapsed / self.current_step
                remaining_steps = self.total_steps - self.current_step
                time_remaining = avg_time_per_step * remaining_steps

                self.status_text.text(
                    f"⏳ {step_name} ({self.current_step}/{self.total_steps}) - "
                    f"~{time_remaining:.0f}s remaining"
                )
            else:
                self.status_text.text(f"⏳ {step_name} ({self.current_step}/{self.total_steps})")

def show_analysis_progress():
    """Show analysis progress with estimated time"""
    with ProgressTracker(5, "Contract Analysis") as progress:
        progress.update("Loading contract...")
        time.sleep(0.5)  # Simulated work

        progress.update("Extracting text...")
        time.sleep(0.5)

        progress.update("Analyzing clauses...")
        time.sleep(1.0)

        progress.update("Assessing risks...")
        time.sleep(0.8)

        progress.update("Generating report...")
        time.sleep(0.7)

def multi_step_progress(steps: List[str], operation: str = "Processing") -> ProgressTracker:
    """
    Create a progress tracker for multiple steps

    Args:
        steps: List of step names
        operation: Overall operation name

    Returns:
        ProgressTracker instance

    Example:
        with multi_step_progress(["Step 1", "Step 2", "Step 3"], "Upload") as progress:
            progress.update("Step 1")
            # ... do work ...
            progress.update("Step 2")
            # ... do work ...
            progress.update("Step 3")
    """
    return ProgressTracker(len(steps), operation)

def show_percentage_progress(current: int, total: int, label: str = "Progress"):
    """
    Show a simple percentage-based progress bar

    Args:
        current: Current progress value
        total: Total value
        label: Label to display
    """
    percentage = int((current / total) * 100) if total > 0 else 0
    st.progress(percentage, text=f"{label}: {current}/{total} ({percentage}%)")

def show_indeterminate_progress(message: str = "Processing..."):
    """Show indeterminate progress (spinner) for unknown duration"""
    return st.spinner(f"⏳ {message}")

def render_progress_overlay(
    mode: str,
    percent: int = 0,
    label: str = "",
    error_message: str | None = None,
    show_cancel: bool = False,
) -> dict:
    """
    Unified Progress Overlay for CIP operations.

    Modes:
        - "determinate": Shows progress bar with color based on percent
            0-30% = red (#FF4A4A)
            31-70% = yellow (#FFCC33)
            71-100% = green (#00CC66)
        - "indeterminate": Pulsing yellow bar at 40-60%
        - "error": Red bar with error message and Retry/Dismiss buttons
        - "cancel": Shows cancel confirmation dialog

    Args:
        mode: One of "determinate", "indeterminate", "error", "cancel"
        percent: Progress percentage (0-100) for determinate mode
        label: Status label to display
        error_message: Error message for error mode
        show_cancel: Whether to show cancel button (X icon)

    Returns:
        dict with button states:
            - "retry": True if Retry clicked (error mode)
            - "dismiss": True if Dismiss clicked (error mode)
            - "cancel_confirmed": True if cancel confirmed
            - "cancel_declined": True if cancel declined
    """
    result = {
        "retry": False,
        "dismiss": False,
        "cancel_confirmed": False,
        "cancel_declined": False,
    }

    # Color mapping for determinate mode
    def get_progress_color(p: int) -> str:
        if p <= 30:
            return "#FF4A4A"  # Red
        elif p <= 70:
            return "#FFCC33"  # Yellow
        else:
            return "#00CC66"  # Green

    # Phase 4B: Enhanced overlay CSS with transition behavior
    # - 400-600ms fade-in/out for overlay (prevents UI flicker)
    # - Clean transitions between states
    overlay_css = """
    <style>
    .progress-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(15, 23, 42, 0.85);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        /* Phase 4B: Fade-in animation (500ms) */
        animation: overlayFadeIn 0.5s ease-out forwards;
    }
    /* Phase 4B: Overlay fade-in animation */
    @keyframes overlayFadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    .progress-card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 32px 48px;
        min-width: 400px;
        max-width: 500px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        text-align: center;
        /* Phase 4B: Card scale-in animation */
        animation: cardScaleIn 0.4s ease-out 0.1s forwards;
        opacity: 0;
        transform: scale(0.95);
    }
    @keyframes cardScaleIn {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    .progress-label {
        color: #E2E8F0;
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 20px;
        /* Phase 4B: Smooth label transitions */
        transition: color 0.3s ease;
    }
    .progress-bar-container {
        background-color: #334155;
        border-radius: 8px;
        height: 12px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 8px;
        /* Phase 4B: Enhanced transitions (400ms for smooth progress) */
        transition: width 0.4s ease-out, background-color 0.4s ease;
    }
    .progress-percent {
        color: #94A3B8;
        font-size: 14px;
        font-weight: 600;
        /* Phase 4B: Smooth text transitions */
        transition: color 0.3s ease;
    }
    .progress-error-message {
        color: #FF4A4A;
        font-size: 14px;
        margin-top: 12px;
        margin-bottom: 16px;
        /* Phase 4B: Error message fade-in */
        animation: errorFadeIn 0.3s ease-out forwards;
    }
    @keyframes errorFadeIn {
        from {
            opacity: 0;
            transform: translateY(-5px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .pulse-animation {
        animation: pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 0.6; width: 40%; }
        50% { opacity: 1; width: 60%; }
    }
    /* Phase 4B: Success state transition */
    .progress-bar-fill.success {
        animation: successPulse 0.6s ease-out forwards;
    }
    @keyframes successPulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 204, 102, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(0, 204, 102, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 204, 102, 0); }
    }
    /* Phase 4B: Error state transition */
    .progress-bar-fill.error {
        animation: errorPulse 0.6s ease-out forwards;
    }
    @keyframes errorPulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 74, 74, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(255, 74, 74, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 74, 74, 0); }
    }
    </style>
    """

    if mode == "determinate":
        color = get_progress_color(percent)
        st.markdown(overlay_css, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="progress-overlay">
            <div class="progress-card">
                <div class="progress-label">{label}</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {percent}%; background-color: {color};"></div>
                </div>
                <div class="progress-percent">{percent}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "indeterminate":
        st.markdown(overlay_css, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="progress-overlay">
            <div class="progress-card">
                <div class="progress-label">{label}</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill pulse-animation" style="background-color: #FFCC33;"></div>
                </div>
                <div class="progress-percent">Processing...</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "error":
        color = "#FF4A4A"
        st.markdown(overlay_css, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="progress-overlay">
            <div class="progress-card">
                <div class="progress-label">{label}</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: 100%; background-color: {color};"></div>
                </div>
                <div class="progress-error-message">{error_message or "An error occurred"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Error mode buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry", key="progress_retry_btn", use_container_width=True):
                result["retry"] = True
        with col2:
            if st.button("✕ Dismiss", key="progress_dismiss_btn", use_container_width=True):
                result["dismiss"] = True

    elif mode == "cancel":
        st.markdown(overlay_css, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="progress-overlay">
            <div class="progress-card">
                <div class="progress-label">Cancel Operation?</div>
                <div style="color: #94A3B8; margin-bottom: 20px;">
                    Are you sure you want to cancel "{label}"?
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Cancel confirmation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Cancel", key="progress_cancel_confirm_btn", use_container_width=True):
                result["cancel_confirmed"] = True
        with col2:
            if st.button("No, Continue", key="progress_cancel_decline_btn", use_container_width=True):
                result["cancel_declined"] = True

    return result


__all__ = [
    'ProgressTracker',
    'show_analysis_progress',
    'multi_step_progress',
    'show_percentage_progress',
    'show_indeterminate_progress',
    'render_progress_overlay'
]
