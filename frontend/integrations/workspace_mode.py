"""
Phase 6 Workspace Mode Integration
CIP Frontend - Three-Panel Layout Support

Provides data flow patterns for:
- Three-panel split layout (V1 | Diff | V2)
- Scroll synchronization engine with SAT (Scroll Authority Token)
- Multi-clause data flow patterns
- SSE integration for real-time insights
- TopNav workspace mode binding
- A11y-consistent scroll behavior
- Diagnostic instrumentation hooks

CC3 P6.C3.T1 - Workspace Layout + Scroll Sync Integration
Version: 6.1.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import json
import uuid

if TYPE_CHECKING:
    from .layout_diagnostics import LayoutDiagnosticPanel


# ============================================================================
# WORKSPACE LAYOUT ENUMS
# ============================================================================

class PanelPosition(str, Enum):
    """Panel positions in three-panel layout."""
    LEFT = "left"      # V1 (Original)
    CENTER = "center"  # Diff/Intelligence
    RIGHT = "right"    # V2 (Revised)


class ScrollSyncMode(str, Enum):
    """Scroll synchronization modes."""
    LOCKED = "locked"           # All panels scroll together
    CLAUSE_ALIGNED = "clause"   # Sync by clause alignment
    FREE = "free"               # Independent scrolling
    LEADER_FOLLOW = "leader"    # One panel leads, others follow


class WorkspaceViewMode(str, Enum):
    """Workspace view modes."""
    COMPARISON = "comparison"   # Side-by-side comparison
    INTELLIGENCE = "intelligence"  # Intelligence focus (center expanded)
    REVIEW = "review"           # Review mode (annotations enabled)
    COMPACT = "compact"         # Compact single-panel mode




class TopNavTab(str, Enum):
    """TopNav active tab identifiers for workspace mode binding."""
    COMPARE = "compare"
    RISK_ANALYSIS = "risk_analysis"
    INTELLIGENCE = "intelligence"
    REVIEW = "review"
    SETTINGS = "settings"



# ============================================================================
# SCROLL AUTHORITY TOKEN (SAT) - REIL RECOMMENDATION
# ============================================================================

@dataclass
class ScrollAuthorityToken:
    """
    Scroll Authority Token (SAT) prevents event-loop drift
    by ensuring only one scroll authority at a time.
    """
    token_id: str
    holder_panel: PanelPosition
    issued_at: str
    is_valid: bool = True
    sequence_number: int = 0

    @classmethod
    def issue(cls, panel: PanelPosition) -> "ScrollAuthorityToken":
        return cls(
            token_id=str(uuid.uuid4())[:8],
            holder_panel=panel,
            issued_at=datetime.now().isoformat(),
        )

    def revoke(self) -> None:
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "holder_panel": self.holder_panel.value,
            "issued_at": self.issued_at,
            "is_valid": self.is_valid,
        }


class ScrollAuthorityManager:
    """Manages Scroll Authority Tokens to prevent event-loop drift."""

    def __init__(self):
        self._current_token: Optional[ScrollAuthorityToken] = None
        self._token_history: List[ScrollAuthorityToken] = []
        self._lock_callbacks: List[Callable[[PanelPosition], None]] = []
        self._release_callbacks: List[Callable[[PanelPosition], None]] = []

    def request_authority(self, panel: PanelPosition) -> Optional[ScrollAuthorityToken]:
        if self._current_token and self._current_token.is_valid:
            old_holder = self._current_token.holder_panel
            self._current_token.revoke()
            self._token_history.append(self._current_token)
            for cb in self._release_callbacks:
                cb(old_holder)
        self._current_token = ScrollAuthorityToken.issue(panel)
        for cb in self._lock_callbacks:
            cb(panel)
        return self._current_token

    def validate_token(self, token: ScrollAuthorityToken) -> bool:
        return (self._current_token is not None and 
                self._current_token.token_id == token.token_id and 
                self._current_token.is_valid)

    def get_current_holder(self) -> Optional[PanelPosition]:
        if self._current_token and self._current_token.is_valid:
            return self._current_token.holder_panel
        return None

    def release_authority(self) -> None:
        if self._current_token:
            old_holder = self._current_token.holder_panel
            self._current_token.revoke()
            self._token_history.append(self._current_token)
            self._current_token = None
            for cb in self._release_callbacks:
                cb(old_holder)

    def on_lock(self, cb: Callable[[PanelPosition], None]) -> None:
        self._lock_callbacks.append(cb)

    def on_release(self, cb: Callable[[PanelPosition], None]) -> None:
        self._release_callbacks.append(cb)

    def get_token_history(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._token_history]


# ============================================================================
# TOPNAV WORKSPACE MODE BINDING
# ============================================================================

@dataclass
class PanelPreset:
    """Predefined panel width configuration."""
    left: float
    center: float
    right: float
    name: str = ""

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.left, self.center, self.right)


class TopNavWorkspaceBinding:
    """
    Binds TopNav tab selection to workspace view modes and panel presets.
    Handles tab -> workspace mode linkage per REIL directive.
    """

    # Default panel presets per view mode
    PRESETS: Dict[WorkspaceViewMode, "PanelPreset"] = {
        WorkspaceViewMode.COMPARISON: PanelPreset(35.0, 30.0, 35.0, "comparison"),
        WorkspaceViewMode.INTELLIGENCE: PanelPreset(25.0, 50.0, 25.0, "intelligence_focus"),
        WorkspaceViewMode.REVIEW: PanelPreset(40.0, 20.0, 40.0, "review"),
        WorkspaceViewMode.COMPACT: PanelPreset(0.0, 100.0, 0.0, "compact"),
    }

    # Tab to view mode mapping
    TAB_MODE_MAP: Dict[TopNavTab, WorkspaceViewMode] = {
        TopNavTab.COMPARE: WorkspaceViewMode.COMPARISON,
        TopNavTab.RISK_ANALYSIS: WorkspaceViewMode.COMPARISON,
        TopNavTab.INTELLIGENCE: WorkspaceViewMode.INTELLIGENCE,
        TopNavTab.REVIEW: WorkspaceViewMode.REVIEW,
        TopNavTab.SETTINGS: WorkspaceViewMode.COMPACT,
    }

    # Tab to scroll sync mode mapping
    TAB_SCROLL_MAP: Dict[TopNavTab, ScrollSyncMode] = {
        TopNavTab.COMPARE: ScrollSyncMode.CLAUSE_ALIGNED,
        TopNavTab.RISK_ANALYSIS: ScrollSyncMode.CLAUSE_ALIGNED,
        TopNavTab.INTELLIGENCE: ScrollSyncMode.LOCKED,
        TopNavTab.REVIEW: ScrollSyncMode.CLAUSE_ALIGNED,
        TopNavTab.SETTINGS: ScrollSyncMode.FREE,
    }

    def __init__(self):
        self._current_tab: TopNavTab = TopNavTab.COMPARE
        self._tab_change_callbacks: List[Callable[[TopNavTab, WorkspaceViewMode], None]] = []

    def get_view_mode_for_tab(self, tab: TopNavTab) -> WorkspaceViewMode:
        """Get the workspace view mode for a given tab."""
        return self.TAB_MODE_MAP.get(tab, WorkspaceViewMode.COMPARISON)

    def get_scroll_mode_for_tab(self, tab: TopNavTab) -> ScrollSyncMode:
        """Get the scroll sync mode for a given tab."""
        return self.TAB_SCROLL_MAP.get(tab, ScrollSyncMode.CLAUSE_ALIGNED)

    def get_preset_for_mode(self, mode: WorkspaceViewMode) -> "PanelPreset":
        """Get panel preset for a view mode."""
        return self.PRESETS.get(mode, self.PRESETS[WorkspaceViewMode.COMPARISON])

    def set_active_tab(self, tab: TopNavTab) -> Tuple[WorkspaceViewMode, "PanelPreset", ScrollSyncMode]:
        """
        Set active tab and return configuration tuple.

        Returns:
            Tuple of (view_mode, panel_preset, scroll_mode)
        """
        self._current_tab = tab
        view_mode = self.get_view_mode_for_tab(tab)
        preset = self.get_preset_for_mode(view_mode)
        scroll_mode = self.get_scroll_mode_for_tab(tab)

        for cb in self._tab_change_callbacks:
            cb(tab, view_mode)

        return (view_mode, preset, scroll_mode)

    def get_current_tab(self) -> TopNavTab:
        """Get currently active tab."""
        return self._current_tab

    def on_tab_change(self, callback: Callable[[TopNavTab, WorkspaceViewMode], None]) -> None:
        """Register callback for tab changes."""
        self._tab_change_callbacks.append(callback)

    def apply_to_workspace_state(self, tab: TopNavTab, state: "WorkspaceState") -> None:
        """Apply tab configuration to a workspace state object."""
        view_mode, preset, scroll_mode = self.set_active_tab(tab)
        state.view_mode = view_mode
        state.scroll_sync_mode = scroll_mode
        state.set_panel_widths(preset.left, preset.center, preset.right)


# ============================================================================
# A11Y SCROLL PREFERENCES
# ============================================================================

@dataclass
class A11yScrollPreferences:
    """Accessibility preferences for scroll behavior."""
    reduce_motion: bool = False
    smooth_scroll_duration_ms: int = 300
    focus_highlight_enabled: bool = True
    keyboard_scroll_step: float = 100.0  # pixels
    screen_reader_announce: bool = True

    def get_scroll_behavior(self) -> str:
        """Get CSS scroll-behavior value."""
        return "auto" if self.reduce_motion else "smooth"

    def get_transition_duration(self) -> int:
        """Get transition duration respecting reduced motion."""
        return 0 if self.reduce_motion else self.smooth_scroll_duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reduce_motion": self.reduce_motion,
            "smooth_scroll_duration_ms": self.smooth_scroll_duration_ms,
            "focus_highlight_enabled": self.focus_highlight_enabled,
            "keyboard_scroll_step": self.keyboard_scroll_step,
            "screen_reader_announce": self.screen_reader_announce,
        }


# ============================================================================
# CLAUSE ALIGNMENT DATA STRUCTURES
# ============================================================================

@dataclass
class ClausePosition:
    """Position of a clause in a panel."""
    clause_id: int
    panel: PanelPosition
    scroll_offset: float  # Pixels from top
    height: float         # Rendered height in pixels
    visible: bool         # Currently in viewport


@dataclass
class AlignedClausePair:
    """A pair of aligned clauses across panels."""
    pair_id: int
    v1_clause_id: Optional[int]
    v2_clause_id: Optional[int]
    v1_position: Optional[ClausePosition] = None
    v2_position: Optional[ClausePosition] = None

    # Intelligence attachments
    sae_match_id: Optional[int] = None
    erce_result_id: Optional[int] = None
    birl_narrative_id: Optional[int] = None

    def has_both(self) -> bool:
        """Check if both clauses exist."""
        return self.v1_clause_id is not None and self.v2_clause_id is not None

    def is_added(self) -> bool:
        """Check if clause was added in V2."""
        return self.v1_clause_id is None and self.v2_clause_id is not None

    def is_removed(self) -> bool:
        """Check if clause was removed from V1."""
        return self.v1_clause_id is not None and self.v2_clause_id is None


@dataclass
class ScrollState:
    """Current scroll state across all panels."""
    left_offset: float = 0.0
    center_offset: float = 0.0
    right_offset: float = 0.0
    sync_mode: ScrollSyncMode = ScrollSyncMode.CLAUSE_ALIGNED
    active_clause_pair: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "left_offset": self.left_offset,
            "center_offset": self.center_offset,
            "right_offset": self.right_offset,
            "sync_mode": self.sync_mode.value,
            "active_clause_pair": self.active_clause_pair,
        }


# ============================================================================
# WORKSPACE STATE CONTAINER
# ============================================================================

@dataclass
class WorkspaceState:
    """
    Complete workspace state for three-panel layout.
    Designed for session state persistence.
    """
    # View configuration
    view_mode: WorkspaceViewMode = WorkspaceViewMode.COMPARISON
    scroll_sync_mode: ScrollSyncMode = ScrollSyncMode.CLAUSE_ALIGNED

    # Panel visibility
    left_panel_visible: bool = True
    center_panel_visible: bool = True
    right_panel_visible: bool = True

    # Panel widths (percentages, must sum to 100)
    left_panel_width: float = 35.0
    center_panel_width: float = 30.0
    right_panel_width: float = 35.0

    # Scroll state
    scroll_state: ScrollState = field(default_factory=ScrollState)

    # Clause alignment data
    aligned_pairs: List[AlignedClausePair] = field(default_factory=list)
    active_pair_index: Optional[int] = None

    # Intelligence panel state
    intelligence_expanded: bool = False
    active_engine_tab: str = "SAE"  # SAE | ERCE | BIRL | FAR

    def get_panel_widths(self) -> Tuple[float, float, float]:
        """Get panel widths as tuple."""
        return (self.left_panel_width, self.center_panel_width, self.right_panel_width)

    def set_panel_widths(self, left: float, center: float, right: float) -> None:
        """Set panel widths (auto-normalizes to 100%)."""
        total = left + center + right
        if total > 0:
            self.left_panel_width = (left / total) * 100
            self.center_panel_width = (center / total) * 100
            self.right_panel_width = (right / total) * 100

    def toggle_intelligence_panel(self) -> None:
        """Toggle intelligence panel expansion."""
        self.intelligence_expanded = not self.intelligence_expanded
        if self.intelligence_expanded:
            # Expand center, shrink sides
            self.set_panel_widths(25, 50, 25)
        else:
            # Reset to default
            self.set_panel_widths(35, 30, 35)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for session state."""
        return {
            "view_mode": self.view_mode.value,
            "scroll_sync_mode": self.scroll_sync_mode.value,
            "left_panel_visible": self.left_panel_visible,
            "center_panel_visible": self.center_panel_visible,
            "right_panel_visible": self.right_panel_visible,
            "left_panel_width": self.left_panel_width,
            "center_panel_width": self.center_panel_width,
            "right_panel_width": self.right_panel_width,
            "scroll_state": self.scroll_state.to_dict(),
            "active_pair_index": self.active_pair_index,
            "intelligence_expanded": self.intelligence_expanded,
            "active_engine_tab": self.active_engine_tab,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceState":
        """Deserialize from session state."""
        state = cls()
        if data:
            state.view_mode = WorkspaceViewMode(data.get("view_mode", "comparison"))
            state.scroll_sync_mode = ScrollSyncMode(data.get("scroll_sync_mode", "clause"))
            state.left_panel_visible = data.get("left_panel_visible", True)
            state.center_panel_visible = data.get("center_panel_visible", True)
            state.right_panel_visible = data.get("right_panel_visible", True)
            state.left_panel_width = data.get("left_panel_width", 35.0)
            state.center_panel_width = data.get("center_panel_width", 30.0)
            state.right_panel_width = data.get("right_panel_width", 35.0)
            state.active_pair_index = data.get("active_pair_index")
            state.intelligence_expanded = data.get("intelligence_expanded", False)
            state.active_engine_tab = data.get("active_engine_tab", "SAE")
        return state


# ============================================================================
# SCROLL SYNCHRONIZATION ENGINE
# ============================================================================

class ScrollSyncEngine:
    """
    Engine for synchronizing scroll positions across panels.
    Supports multiple sync modes.
    """

    def __init__(self, aligned_pairs: List[AlignedClausePair]):
        self.aligned_pairs = aligned_pairs
        self._clause_positions: Dict[int, Dict[str, ClausePosition]] = {}

    def register_clause_position(self, position: ClausePosition) -> None:
        """Register a clause's rendered position."""
        pair_id = self._find_pair_for_clause(position.clause_id, position.panel)
        if pair_id is not None:
            if pair_id not in self._clause_positions:
                self._clause_positions[pair_id] = {}
            self._clause_positions[pair_id][position.panel.value] = position

    def _find_pair_for_clause(self, clause_id: int, panel: PanelPosition) -> Optional[int]:
        """Find the aligned pair containing this clause."""
        for pair in self.aligned_pairs:
            if panel == PanelPosition.LEFT and pair.v1_clause_id == clause_id:
                return pair.pair_id
            if panel == PanelPosition.RIGHT and pair.v2_clause_id == clause_id:
                return pair.pair_id
        return None

    def calculate_sync_offset(
        self,
        source_panel: PanelPosition,
        source_offset: float,
        target_panel: PanelPosition,
        mode: ScrollSyncMode
    ) -> float:
        """
        Calculate target panel offset based on source panel scroll.

        Args:
            source_panel: Panel being scrolled
            source_offset: New scroll offset of source
            target_panel: Panel to synchronize
            mode: Synchronization mode

        Returns:
            Calculated offset for target panel
        """
        if mode == ScrollSyncMode.LOCKED:
            # Direct 1:1 mapping
            return source_offset

        elif mode == ScrollSyncMode.FREE:
            # No synchronization
            return -1  # Indicator to not update

        elif mode == ScrollSyncMode.CLAUSE_ALIGNED:
            # Find clause at source offset, align to same clause in target
            source_pair = self._find_pair_at_offset(source_panel, source_offset)
            if source_pair:
                return self._get_pair_offset(source_pair, target_panel)
            return source_offset

        elif mode == ScrollSyncMode.LEADER_FOLLOW:
            # Proportional scroll based on document heights
            # (simplified - would need document height info)
            return source_offset

        return source_offset

    def _find_pair_at_offset(self, panel: PanelPosition, offset: float) -> Optional[int]:
        """Find the aligned pair visible at the given offset."""
        for pair_id, positions in self._clause_positions.items():
            pos = positions.get(panel.value)
            if pos and pos.scroll_offset <= offset < (pos.scroll_offset + pos.height):
                return pair_id
        return None

    def _get_pair_offset(self, pair_id: int, panel: PanelPosition) -> float:
        """Get the scroll offset to show a pair in a panel."""
        positions = self._clause_positions.get(pair_id, {})
        pos = positions.get(panel.value)
        if pos:
            return pos.scroll_offset
        return 0.0

    def get_visible_pairs(self, panel: PanelPosition, viewport_top: float, viewport_height: float) -> List[int]:
        """Get list of pair IDs visible in viewport."""
        visible = []
        viewport_bottom = viewport_top + viewport_height

        for pair_id, positions in self._clause_positions.items():
            pos = positions.get(panel.value)
            if pos:
                clause_bottom = pos.scroll_offset + pos.height
                if pos.scroll_offset < viewport_bottom and clause_bottom > viewport_top:
                    visible.append(pair_id)

        return visible


# ============================================================================
# MULTI-CLAUSE DATA FLOW PATTERNS
# ============================================================================

@dataclass
class ClauseDataPacket:
    """
    Data packet for a single clause with all attached intelligence.
    Used for multi-clause data flow.
    """
    clause_id: int
    panel: PanelPosition

    # Clause content
    number: str
    title: str
    text: str

    # Intelligence attachments (from Phase 5 engines)
    sae_data: Optional[Dict[str, Any]] = None
    erce_data: Optional[Dict[str, Any]] = None
    birl_data: Optional[Dict[str, Any]] = None
    far_data: Optional[Dict[str, Any]] = None

    # Rendering hints
    highlight_ranges: List[Tuple[int, int]] = field(default_factory=list)
    risk_level: Optional[str] = None

    def has_intelligence(self) -> bool:
        """Check if any intelligence is attached."""
        return any([self.sae_data, self.erce_data, self.birl_data, self.far_data])

    def get_risk_badge(self) -> Optional[str]:
        """Get risk badge based on ERCE data."""
        if self.erce_data:
            return self.erce_data.get("risk_category")
        return None


class MultiClauseDataFlow:
    """
    Manages data flow for multiple clauses across panels.
    Optimized for incremental updates and streaming.
    """

    def __init__(self):
        self._packets: Dict[Tuple[int, str], ClauseDataPacket] = {}
        self._update_callbacks: List[Callable[[ClauseDataPacket], None]] = []

    def register_packet(self, packet: ClauseDataPacket) -> None:
        """Register a clause data packet."""
        key = (packet.clause_id, packet.panel.value)
        self._packets[key] = packet

    def get_packet(self, clause_id: int, panel: PanelPosition) -> Optional[ClauseDataPacket]:
        """Get packet for a clause."""
        return self._packets.get((clause_id, panel.value))

    def attach_intelligence(
        self,
        clause_id: int,
        panel: PanelPosition,
        engine: str,
        data: Dict[str, Any]
    ) -> None:
        """Attach intelligence data to a clause packet."""
        packet = self.get_packet(clause_id, panel)
        if packet:
            if engine == "SAE":
                packet.sae_data = data
            elif engine == "ERCE":
                packet.erce_data = data
                packet.risk_level = data.get("risk_category")
            elif engine == "BIRL":
                packet.birl_data = data
            elif engine == "FAR":
                packet.far_data = data

            # Notify callbacks
            for callback in self._update_callbacks:
                callback(packet)

    def on_update(self, callback: Callable[[ClauseDataPacket], None]) -> None:
        """Register callback for packet updates."""
        self._update_callbacks.append(callback)

    def get_all_packets(self, panel: Optional[PanelPosition] = None) -> List[ClauseDataPacket]:
        """Get all packets, optionally filtered by panel."""
        if panel:
            return [p for p in self._packets.values() if p.panel == panel]
        return list(self._packets.values())


# ============================================================================
# SSE STREAMING INTEGRATION (PREP)
# ============================================================================

class SSEEventType(str, Enum):
    """Server-Sent Event types for real-time insights."""
    INTELLIGENCE_UPDATE = "intelligence_update"
    CLAUSE_HIGHLIGHT = "clause_highlight"
    SCROLL_SYNC = "scroll_sync"
    PANEL_RESIZE = "panel_resize"
    ENGINE_STATUS = "engine_status"
    ERROR = "error"


@dataclass
class SSEEvent:
    """
    Server-Sent Event structure for streaming updates.
    """
    event_type: SSEEventType
    data: Dict[str, Any]
    timestamp: str
    sequence_id: int

    def to_sse_format(self) -> str:
        """Format as SSE wire protocol."""
        return f"event: {self.event_type.value}\ndata: {json.dumps(self.data)}\nid: {self.sequence_id}\n\n"

    @classmethod
    def from_sse_format(cls, raw: str) -> Optional["SSEEvent"]:
        """Parse from SSE wire protocol."""
        lines = raw.strip().split("\n")
        event_type = None
        data = {}
        seq_id = 0

        for line in lines:
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
            elif line.startswith("id:"):
                seq_id = int(line[3:].strip())

        if event_type:
            return cls(
                event_type=SSEEventType(event_type),
                data=data,
                timestamp="",
                sequence_id=seq_id,
            )
        return None


class SSEStreamHandler:
    """
    Handler for SSE streaming events.
    Manages connection state and event routing.
    """

    def __init__(self):
        self._connected = False
        self._last_sequence: int = 0
        self._event_handlers: Dict[SSEEventType, List[Callable[[SSEEvent], None]]] = {}

    def connect(self, endpoint: str) -> bool:
        """
        Connect to SSE endpoint.
        (Mock implementation for prep phase)
        """
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from SSE stream."""
        self._connected = False

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected

    def on_event(self, event_type: SSEEventType, handler: Callable[[SSEEvent], None]) -> None:
        """Register event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def dispatch_event(self, event: SSEEvent) -> None:
        """Dispatch event to registered handlers."""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)

    def process_raw_event(self, raw: str) -> None:
        """Process raw SSE event string."""
        event = SSEEvent.from_sse_format(raw)
        if event:
            self._last_sequence = event.sequence_id
            self.dispatch_event(event)




# ============================================================================
# ENHANCED SCROLL SYNC ENGINE WITH SAT INTEGRATION
# ============================================================================

class EnhancedScrollSyncEngine(ScrollSyncEngine):
    """
    Enhanced scroll sync engine with SAT integration and diagnostic hooks.
    Provides event-loop drift prevention and diagnostic instrumentation.
    """

    def __init__(
        self,
        aligned_pairs: List[AlignedClausePair],
        sat_manager: Optional[ScrollAuthorityManager] = None,
        a11y_prefs: Optional[A11yScrollPreferences] = None
    ):
        super().__init__(aligned_pairs)
        self._sat_manager = sat_manager or ScrollAuthorityManager()
        self._a11y_prefs = a11y_prefs or A11yScrollPreferences()
        self._diagnostic_panel: Optional["LayoutDiagnosticPanel"] = None
        self._scroll_callbacks: List[Callable[[PanelPosition, float, ScrollSyncMode], None]] = []

    def attach_diagnostics(self, panel: "LayoutDiagnosticPanel") -> None:
        """Attach diagnostic panel for instrumentation."""
        self._diagnostic_panel = panel
        self._log_diagnostic("INFO", "Diagnostic panel attached to scroll engine")

    def _log_diagnostic(self, level: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log to diagnostic panel if attached."""
        if self._diagnostic_panel:
            if level == "INFO":
                self._diagnostic_panel.info("scroll_sync", message, data)
            elif level == "WARN":
                self._diagnostic_panel.warn("scroll_sync", message, data)
            elif level == "ERROR":
                self._diagnostic_panel.error("scroll_sync", message, data)

    def handle_scroll(
        self,
        source_panel: PanelPosition,
        offset: float,
        mode: ScrollSyncMode
    ) -> Dict[PanelPosition, float]:
        """
        Handle scroll event with SAT validation.

        Args:
            source_panel: Panel initiating scroll
            offset: New scroll offset
            mode: Synchronization mode

        Returns:
            Dict mapping panels to their calculated offsets
        """
        # Request scroll authority
        token = self._sat_manager.request_authority(source_panel)
        if not token:
            self._log_diagnostic("WARN", "Failed to acquire scroll authority", {
                "source_panel": source_panel.value
            })
            return {}

        # Log scroll event to diagnostics
        if self._diagnostic_panel:
            self._diagnostic_panel.scroll_monitor.start_monitoring()
            self._diagnostic_panel.scroll_monitor.record_event(
                source_panel=source_panel.value,
                source_offset=offset,
                sync_mode=mode.value,
            )

        # Calculate target offsets
        results: Dict[PanelPosition, float] = {source_panel: offset}

        for target in [PanelPosition.LEFT, PanelPosition.CENTER, PanelPosition.RIGHT]:
            if target != source_panel:
                target_offset = self.calculate_sync_offset(
                    source_panel, offset, target, mode
                )
                if target_offset >= 0:  # -1 means no update
                    results[target] = target_offset

        # Notify callbacks
        for cb in self._scroll_callbacks:
            cb(source_panel, offset, mode)

        self._log_diagnostic("INFO", "Scroll handled", {
            "source": source_panel.value,
            "offset": offset,
            "mode": mode.value,
            "token_id": token.token_id,
        })

        return results

    def on_scroll(self, callback: Callable[[PanelPosition, float, ScrollSyncMode], None]) -> None:
        """Register scroll event callback."""
        self._scroll_callbacks.append(callback)

    def get_a11y_scroll_params(self) -> Dict[str, Any]:
        """Get A11y-aware scroll parameters."""
        return {
            "behavior": self._a11y_prefs.get_scroll_behavior(),
            "duration": self._a11y_prefs.get_transition_duration(),
            "step": self._a11y_prefs.keyboard_scroll_step,
        }

    def get_sat_manager(self) -> ScrollAuthorityManager:
        """Get the SAT manager instance."""
        return self._sat_manager


# ============================================================================
# WORKSPACE CONTROLLER (UNIFIED)
# ============================================================================

class WorkspaceController:
    """
    Unified controller for workspace layout and scroll synchronization.
    Coordinates TopNav binding, SAT, scroll sync, and diagnostics.
    """

    def __init__(self):
        self._state = WorkspaceState()
        self._nav_binding = TopNavWorkspaceBinding()
        self._sat_manager = ScrollAuthorityManager()
        self._a11y_prefs = A11yScrollPreferences()
        self._scroll_engine: Optional[EnhancedScrollSyncEngine] = None
        self._diagnostic_panel: Optional["LayoutDiagnosticPanel"] = None
        self._state_change_callbacks: List[Callable[[WorkspaceState], None]] = []

    def initialize(self, aligned_pairs: List[AlignedClausePair]) -> None:
        """Initialize the controller with clause alignment data."""
        self._scroll_engine = EnhancedScrollSyncEngine(
            aligned_pairs=aligned_pairs,
            sat_manager=self._sat_manager,
            a11y_prefs=self._a11y_prefs,
        )
        if self._diagnostic_panel:
            self._scroll_engine.attach_diagnostics(self._diagnostic_panel)

    def attach_diagnostics(self, panel: "LayoutDiagnosticPanel") -> None:
        """Attach diagnostic panel for instrumentation."""
        self._diagnostic_panel = panel
        if self._scroll_engine:
            self._scroll_engine.attach_diagnostics(panel)
        panel.info("controller", "WorkspaceController initialized with diagnostics")

    def set_tab(self, tab: TopNavTab) -> WorkspaceState:
        """
        Handle TopNav tab change.

        Args:
            tab: New active tab

        Returns:
            Updated workspace state
        """
        self._nav_binding.apply_to_workspace_state(tab, self._state)
        self._notify_state_change()
        return self._state

    def handle_scroll(
        self,
        source_panel: PanelPosition,
        offset: float
    ) -> Dict[PanelPosition, float]:
        """
        Handle scroll event from a panel.

        Args:
            source_panel: Panel that scrolled
            offset: New scroll offset

        Returns:
            Dict of calculated offsets for all panels
        """
        if not self._scroll_engine:
            return {source_panel: offset}

        results = self._scroll_engine.handle_scroll(
            source_panel, offset, self._state.scroll_sync_mode
        )

        # Update state
        for panel, panel_offset in results.items():
            if panel == PanelPosition.LEFT:
                self._state.scroll_state.left_offset = panel_offset
            elif panel == PanelPosition.CENTER:
                self._state.scroll_state.center_offset = panel_offset
            elif panel == PanelPosition.RIGHT:
                self._state.scroll_state.right_offset = panel_offset

        return results

    def set_scroll_mode(self, mode: ScrollSyncMode) -> None:
        """Set the scroll synchronization mode."""
        self._state.scroll_sync_mode = mode
        self._state.scroll_state.sync_mode = mode
        self._notify_state_change()

    def set_a11y_preferences(self, prefs: A11yScrollPreferences) -> None:
        """Update accessibility preferences."""
        self._a11y_prefs = prefs
        if self._scroll_engine:
            self._scroll_engine._a11y_prefs = prefs

    def get_state(self) -> WorkspaceState:
        """Get current workspace state."""
        return self._state

    def get_diagnostic_report(self) -> Optional[Dict[str, Any]]:
        """Get diagnostic report if panel attached."""
        if self._diagnostic_panel:
            return self._diagnostic_panel.generate_report()
        return None

    def on_state_change(self, callback: Callable[[WorkspaceState], None]) -> None:
        """Register callback for state changes."""
        self._state_change_callbacks.append(callback)

    def _notify_state_change(self) -> None:
        """Notify all callbacks of state change."""
        for cb in self._state_change_callbacks:
            cb(self._state)

    def export_state(self) -> Dict[str, Any]:
        """Export full controller state for debugging/persistence."""
        holder = self._sat_manager.get_current_holder()
        return {
            "workspace_state": self._state.to_dict(),
            "current_tab": self._nav_binding.get_current_tab().value,
            "sat_holder": holder.value if holder else None,
            "a11y_prefs": self._a11y_prefs.to_dict(),
        }


# ============================================================================
# MODULE VERSION
# ============================================================================

__version__ = "6.1.0"
__phase__ = "Phase 6 - P6.C3.T1 Integration"
__features__ = [
    "three_panel_layout",
    "scroll_synchronization",
    "scroll_authority_token",
    "topnav_workspace_binding",
    "a11y_scroll_behavior",
    "diagnostic_instrumentation",
    "multi_clause_data_flow",
    "sse_streaming_prep",
    "enhanced_scroll_engine",
    "workspace_controller",
]
