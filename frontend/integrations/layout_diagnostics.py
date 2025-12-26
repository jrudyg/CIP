"""
Layout Diagnostics Panel
Phase 6 - Non-Blocking Utility for Workspace Validation

Provides read-only diagnostic utilities for:
- Panel dimension logging
- Scroll synchronization event monitoring
- Panel position validation

This module is INDEPENDENT and does NOT modify workspace_mode.py
or the integration pipeline. Safe to run standalone.

CC3 P6-LAYOUT-DIAGNOSTICS
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json


# ============================================================================
# DIAGNOSTIC ENUMS
# ============================================================================

class DiagnosticLevel(str, Enum):
    """Severity levels for diagnostic messages."""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class PanelId(str, Enum):
    """Panel identifiers (read-only reference)."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


# ============================================================================
# DIAGNOSTIC DATA STRUCTURES
# ============================================================================

@dataclass
class DiagnosticEntry:
    """A single diagnostic log entry."""
    timestamp: str
    level: DiagnosticLevel
    source: str
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "source": self.source,
            "message": self.message,
            "data": self.data,
        }

    def format_log(self) -> str:
        """Format as log line."""
        data_str = f" | {json.dumps(self.data)}" if self.data else ""
        return f"[{self.timestamp}] [{self.level.value}] {self.source}: {self.message}{data_str}"


@dataclass
class PanelDimensions:
    """Captured panel dimensions for diagnostics."""
    panel_id: str
    width_percent: float
    width_pixels: Optional[float] = None
    height_pixels: Optional[float] = None
    visible: bool = True
    captured_at: str = ""

    def __post_init__(self):
        if not self.captured_at:
            self.captured_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "width_percent": self.width_percent,
            "width_pixels": self.width_pixels,
            "height_pixels": self.height_pixels,
            "visible": self.visible,
            "captured_at": self.captured_at,
        }


@dataclass
class ScrollEvent:
    """Captured scroll synchronization event."""
    event_id: int
    source_panel: str
    target_panel: Optional[str]
    source_offset: float
    calculated_offset: Optional[float]
    sync_mode: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source_panel": self.source_panel,
            "target_panel": self.target_panel,
            "source_offset": self.source_offset,
            "calculated_offset": self.calculated_offset,
            "sync_mode": self.sync_mode,
            "timestamp": self.timestamp,
        }


@dataclass
class ValidationResult:
    """Result of a panel position validation."""
    valid: bool
    panel_id: str
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "panel_id": self.panel_id,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
        }


# ============================================================================
# PANEL DIMENSION LOGGER
# ============================================================================

class PanelDimensionLogger:
    """
    Read-only logger for panel dimension changes.
    Captures dimension snapshots without modifying state.
    """

    def __init__(self, max_history: int = 100):
        self._history: List[PanelDimensions] = []
        self._max_history = max_history
        self._snapshot_count = 0

    def capture(
        self,
        panel_id: str,
        width_percent: float,
        width_pixels: Optional[float] = None,
        height_pixels: Optional[float] = None,
        visible: bool = True
    ) -> PanelDimensions:
        """
        Capture a panel dimension snapshot.

        Args:
            panel_id: Panel identifier
            width_percent: Width as percentage (0-100)
            width_pixels: Optional pixel width
            height_pixels: Optional pixel height
            visible: Panel visibility state

        Returns:
            Captured PanelDimensions object
        """
        dims = PanelDimensions(
            panel_id=panel_id,
            width_percent=width_percent,
            width_pixels=width_pixels,
            height_pixels=height_pixels,
            visible=visible,
        )

        self._history.append(dims)
        self._snapshot_count += 1

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return dims

    def capture_all(
        self,
        left: Tuple[float, Optional[float], Optional[float], bool],
        center: Tuple[float, Optional[float], Optional[float], bool],
        right: Tuple[float, Optional[float], Optional[float], bool]
    ) -> List[PanelDimensions]:
        """
        Capture all three panels at once.

        Args:
            left: (width_pct, width_px, height_px, visible)
            center: (width_pct, width_px, height_px, visible)
            right: (width_pct, width_px, height_px, visible)

        Returns:
            List of captured dimensions
        """
        return [
            self.capture(PanelId.LEFT.value, *left),
            self.capture(PanelId.CENTER.value, *center),
            self.capture(PanelId.RIGHT.value, *right),
        ]

    def get_history(self, panel_id: Optional[str] = None) -> List[PanelDimensions]:
        """Get dimension history, optionally filtered by panel."""
        if panel_id:
            return [d for d in self._history if d.panel_id == panel_id]
        return self._history.copy()

    def get_latest(self, panel_id: str) -> Optional[PanelDimensions]:
        """Get most recent dimensions for a panel."""
        for dims in reversed(self._history):
            if dims.panel_id == panel_id:
                return dims
        return None

    def get_snapshot_count(self) -> int:
        """Get total number of snapshots captured."""
        return self._snapshot_count

    def clear(self) -> None:
        """Clear history (for testing)."""
        self._history = []

    def export_history(self) -> List[Dict[str, Any]]:
        """Export history as list of dicts."""
        return [d.to_dict() for d in self._history]


# ============================================================================
# SCROLL SYNCHRONIZATION EVENT MONITOR
# ============================================================================

class ScrollSyncMonitor:
    """
    Read-only monitor for scroll synchronization events.
    Captures events without interfering with sync engine.
    """

    def __init__(self, max_events: int = 500):
        self._events: List[ScrollEvent] = []
        self._max_events = max_events
        self._event_counter = 0
        self._monitoring = False

    def start_monitoring(self) -> None:
        """Start event monitoring."""
        self._monitoring = True

    def stop_monitoring(self) -> None:
        """Stop event monitoring."""
        self._monitoring = False

    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring

    def record_event(
        self,
        source_panel: str,
        source_offset: float,
        sync_mode: str,
        target_panel: Optional[str] = None,
        calculated_offset: Optional[float] = None
    ) -> Optional[ScrollEvent]:
        """
        Record a scroll sync event.

        Args:
            source_panel: Panel that initiated scroll
            source_offset: Scroll offset in source panel
            sync_mode: Synchronization mode used
            target_panel: Optional target panel
            calculated_offset: Calculated offset for target

        Returns:
            Recorded event or None if not monitoring
        """
        if not self._monitoring:
            return None

        self._event_counter += 1
        event = ScrollEvent(
            event_id=self._event_counter,
            source_panel=source_panel,
            target_panel=target_panel,
            source_offset=source_offset,
            calculated_offset=calculated_offset,
            sync_mode=sync_mode,
        )

        self._events.append(event)

        # Trim events if needed
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        return event

    def get_events(
        self,
        source_panel: Optional[str] = None,
        sync_mode: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScrollEvent]:
        """Get events with optional filtering."""
        filtered = self._events

        if source_panel:
            filtered = [e for e in filtered if e.source_panel == source_panel]

        if sync_mode:
            filtered = [e for e in filtered if e.sync_mode == sync_mode]

        if limit:
            filtered = filtered[-limit:]

        return filtered

    def get_event_count(self) -> int:
        """Get total events recorded."""
        return self._event_counter

    def get_sync_mode_stats(self) -> Dict[str, int]:
        """Get event counts by sync mode."""
        stats: Dict[str, int] = {}
        for event in self._events:
            mode = event.sync_mode
            stats[mode] = stats.get(mode, 0) + 1
        return stats

    def clear(self) -> None:
        """Clear event history."""
        self._events = []

    def export_events(self) -> List[Dict[str, Any]]:
        """Export events as list of dicts."""
        return [e.to_dict() for e in self._events]


# ============================================================================
# PANEL POSITION VALIDATOR
# ============================================================================

class PanelPositionValidator:
    """
    Validates panel positions and dimensions.
    Read-only validation without state modification.
    """

    # Validation thresholds
    MIN_PANEL_WIDTH_PERCENT = 10.0
    MAX_PANEL_WIDTH_PERCENT = 80.0
    TOTAL_WIDTH_TOLERANCE = 0.1  # Allow 0.1% deviation from 100%

    def validate_dimensions(self, dims: PanelDimensions) -> ValidationResult:
        """
        Validate a single panel's dimensions.

        Args:
            dims: Panel dimensions to validate

        Returns:
            ValidationResult with checks performed
        """
        result = ValidationResult(valid=True, panel_id=dims.panel_id)

        # Check width percentage range
        if dims.width_percent >= self.MIN_PANEL_WIDTH_PERCENT:
            result.checks_passed.append(f"width >= {self.MIN_PANEL_WIDTH_PERCENT}%")
        else:
            result.checks_failed.append(
                f"width {dims.width_percent}% < minimum {self.MIN_PANEL_WIDTH_PERCENT}%"
            )
            result.valid = False

        if dims.width_percent <= self.MAX_PANEL_WIDTH_PERCENT:
            result.checks_passed.append(f"width <= {self.MAX_PANEL_WIDTH_PERCENT}%")
        else:
            result.checks_failed.append(
                f"width {dims.width_percent}% > maximum {self.MAX_PANEL_WIDTH_PERCENT}%"
            )
            result.valid = False

        # Check visibility consistency
        if dims.visible and dims.width_percent > 0:
            result.checks_passed.append("visible panel has positive width")
        elif not dims.visible and dims.width_percent == 0:
            result.checks_passed.append("hidden panel has zero width")
        elif not dims.visible and dims.width_percent > 0:
            result.warnings.append("hidden panel has non-zero width")

        # Check pixel dimensions if provided
        if dims.width_pixels is not None:
            if dims.width_pixels >= 0:
                result.checks_passed.append("pixel width non-negative")
            else:
                result.checks_failed.append(f"negative pixel width: {dims.width_pixels}")
                result.valid = False

        return result

    def validate_layout(
        self,
        left: PanelDimensions,
        center: PanelDimensions,
        right: PanelDimensions
    ) -> Dict[str, Any]:
        """
        Validate complete three-panel layout.

        Args:
            left: Left panel dimensions
            center: Center panel dimensions
            right: Right panel dimensions

        Returns:
            Dict with overall validity and per-panel results
        """
        # Validate each panel
        left_result = self.validate_dimensions(left)
        center_result = self.validate_dimensions(center)
        right_result = self.validate_dimensions(right)

        # Check total width
        total_width = left.width_percent + center.width_percent + right.width_percent
        width_valid = abs(total_width - 100.0) <= self.TOTAL_WIDTH_TOLERANCE

        overall_valid = (
            left_result.valid and
            center_result.valid and
            right_result.valid and
            width_valid
        )

        return {
            "valid": overall_valid,
            "total_width_percent": total_width,
            "total_width_valid": width_valid,
            "panels": {
                "left": left_result.to_dict(),
                "center": center_result.to_dict(),
                "right": right_result.to_dict(),
            },
        }

    def validate_scroll_offset(
        self,
        offset: float,
        max_offset: float = 100000.0
    ) -> ValidationResult:
        """
        Validate a scroll offset value.

        Args:
            offset: Scroll offset to validate
            max_offset: Maximum allowed offset

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True, panel_id="scroll")

        if offset >= 0:
            result.checks_passed.append("offset non-negative")
        else:
            result.checks_failed.append(f"negative offset: {offset}")
            result.valid = False

        if offset <= max_offset:
            result.checks_passed.append(f"offset <= max ({max_offset})")
        else:
            result.warnings.append(f"offset {offset} exceeds typical max {max_offset}")

        return result


# ============================================================================
# DIAGNOSTIC PANEL (AGGREGATE)
# ============================================================================

class LayoutDiagnosticPanel:
    """
    Aggregate diagnostic panel combining all utilities.
    Provides unified interface for layout diagnostics.
    """

    def __init__(self):
        self.dimension_logger = PanelDimensionLogger()
        self.scroll_monitor = ScrollSyncMonitor()
        self.position_validator = PanelPositionValidator()
        self._log_entries: List[DiagnosticEntry] = []

    def log(
        self,
        level: DiagnosticLevel,
        source: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> DiagnosticEntry:
        """Add a diagnostic log entry."""
        entry = DiagnosticEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            source=source,
            message=message,
            data=data,
        )
        self._log_entries.append(entry)
        return entry

    def info(self, source: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log INFO level message."""
        self.log(DiagnosticLevel.INFO, source, message, data)

    def warn(self, source: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log WARN level message."""
        self.log(DiagnosticLevel.WARN, source, message, data)

    def error(self, source: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log ERROR level message."""
        self.log(DiagnosticLevel.ERROR, source, message, data)

    def debug(self, source: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log DEBUG level message."""
        self.log(DiagnosticLevel.DEBUG, source, message, data)

    def get_logs(
        self,
        level: Optional[DiagnosticLevel] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DiagnosticEntry]:
        """Get log entries with optional filtering."""
        filtered = self._log_entries

        if level:
            filtered = [e for e in filtered if e.level == level]

        if source:
            filtered = [e for e in filtered if e.source == source]

        if limit:
            filtered = filtered[-limit:]

        return filtered

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "dimensions": {
                "snapshot_count": self.dimension_logger.get_snapshot_count(),
                "latest": {
                    "left": self.dimension_logger.get_latest(PanelId.LEFT.value),
                    "center": self.dimension_logger.get_latest(PanelId.CENTER.value),
                    "right": self.dimension_logger.get_latest(PanelId.RIGHT.value),
                },
            },
            "scroll_events": {
                "total_count": self.scroll_monitor.get_event_count(),
                "by_sync_mode": self.scroll_monitor.get_sync_mode_stats(),
                "monitoring_active": self.scroll_monitor.is_monitoring(),
            },
            "log_summary": {
                "total_entries": len(self._log_entries),
                "by_level": {
                    level.value: len([e for e in self._log_entries if e.level == level])
                    for level in DiagnosticLevel
                },
            },
        }

    def clear_all(self) -> None:
        """Clear all diagnostic data."""
        self.dimension_logger.clear()
        self.scroll_monitor.clear()
        self._log_entries = []


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "1.0.0"
__phase__ = "Phase 6 Diagnostics"
__readonly__ = True  # This module does not modify workspace state
