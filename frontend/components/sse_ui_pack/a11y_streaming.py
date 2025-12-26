"""
P7 A11y Streaming Checklist
P7.CC2.01 - Task 4

Provides:
- aria-live rules for high-frequency updates
- Focus stability rules
- Scroll independence rules
- Streaming accessibility validation

CIP Protocol: CC2 implementation for P7 accessibility.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CHECKLIST DEFINITION
# ============================================================================

class A11yPriority(Enum):
    """Accessibility rule priority."""
    CRITICAL = "critical"    # Must implement for WCAG compliance
    HIGH = "high"            # Strongly recommended
    MEDIUM = "medium"        # Recommended for better UX
    LOW = "low"              # Nice to have


class A11yCategory(Enum):
    """Accessibility rule category."""
    ARIA_LIVE = "aria_live"
    FOCUS = "focus"
    SCROLL = "scroll"
    TIMING = "timing"
    MOTION = "motion"
    KEYBOARD = "keyboard"


@dataclass
class A11yRule:
    """An accessibility rule definition."""
    rule_id: str
    category: A11yCategory
    priority: A11yPriority
    title: str
    description: str
    wcag_criterion: Optional[str] = None
    implementation_notes: str = ""
    test_method: str = ""


# ============================================================================
# P7 STREAMING ACCESSIBILITY CHECKLIST
# ============================================================================

A11Y_STREAMING_CHECKLIST: List[A11yRule] = [
    # =========================================================================
    # ARIA-LIVE RULES FOR HIGH-FREQUENCY UPDATES
    # =========================================================================
    A11yRule(
        rule_id="P7-A11Y-001",
        category=A11yCategory.ARIA_LIVE,
        priority=A11yPriority.CRITICAL,
        title="Throttle aria-live announcements",
        description="High-frequency SSE updates must be throttled before announcing to screen readers. "
                    "Announce no more than once per 2 seconds for polite regions, 5 seconds for status updates.",
        wcag_criterion="4.1.3 Status Messages",
        implementation_notes="""
- Use a debounce/throttle mechanism for aria-live updates
- Aggregate multiple updates into single announcements
- Connection state changes: announce immediately (assertive)
- Event counts: batch and announce every 5 seconds (polite)
- Progress updates: announce at 25%, 50%, 75%, 100% milestones
        """,
        test_method="Screen reader testing with NVDA/VoiceOver during high-frequency events",
    ),

    A11yRule(
        rule_id="P7-A11Y-002",
        category=A11yCategory.ARIA_LIVE,
        priority=A11yPriority.CRITICAL,
        title="Use appropriate aria-live politeness",
        description="Choose correct aria-live politeness level based on update urgency.",
        wcag_criterion="4.1.3 Status Messages",
        implementation_notes="""
- aria-live="assertive": Connection lost, critical errors, security alerts
- aria-live="polite": Event counts, progress updates, status changes
- aria-live="off": Diagnostic data, debug information, raw event streams
- Use aria-atomic="true" for complete replacement announcements
- Use aria-relevant="additions text" for incremental updates
        """,
        test_method="Verify announcements don't interrupt user during normal operation",
    ),

    A11yRule(
        rule_id="P7-A11Y-003",
        category=A11yCategory.ARIA_LIVE,
        priority=A11yPriority.HIGH,
        title="Provide summary announcements",
        description="Instead of announcing each event, provide periodic summaries.",
        wcag_criterion="4.1.3 Status Messages",
        implementation_notes="""
- "5 new events received" instead of announcing each
- "Reconnection successful, 12 events replayed" for batch operations
- Include error counts in summary if any errors occurred
- Announce completion of long-running operations
        """,
        test_method="Verify summaries are informative without being verbose",
    ),

    A11yRule(
        rule_id="P7-A11Y-004",
        category=A11yCategory.ARIA_LIVE,
        priority=A11yPriority.MEDIUM,
        title="Allow users to configure announcement verbosity",
        description="Provide user preference for announcement frequency and detail level.",
        wcag_criterion="1.4.2 Audio Control",
        implementation_notes="""
- Verbosity levels: Minimal, Standard, Verbose
- Minimal: Only critical alerts (connection lost, errors)
- Standard: Status changes + periodic summaries
- Verbose: All state changes with details
- Store preference in session/localStorage
        """,
        test_method="User testing with different verbosity preferences",
    ),

    # =========================================================================
    # FOCUS STABILITY RULES
    # =========================================================================
    A11yRule(
        rule_id="P7-A11Y-005",
        category=A11yCategory.FOCUS,
        priority=A11yPriority.CRITICAL,
        title="Never steal focus on streaming updates",
        description="SSE events must never move keyboard focus away from user's current position.",
        wcag_criterion="2.4.3 Focus Order, 3.2.1 On Focus",
        implementation_notes="""
- NEVER use focus() on elements during event processing
- UI updates must preserve document.activeElement
- If DOM is modified, restore focus to equivalent element
- Use aria-live for notifications instead of focus changes
        """,
        test_method="Navigate with keyboard during active event stream, verify focus doesn't jump",
    ),

    A11yRule(
        rule_id="P7-A11Y-006",
        category=A11yCategory.FOCUS,
        priority=A11yPriority.CRITICAL,
        title="Preserve focus through reconnection",
        description="When connection is lost and restored, user's focus position must be preserved.",
        wcag_criterion="2.4.3 Focus Order",
        implementation_notes="""
- Store activeElement ID before reconnection UI appears
- After reconnection completes, restore focus to stored element
- If element no longer exists, focus nearest equivalent
- Don't focus the "connection restored" banner
        """,
        test_method="Simulate disconnect during form input, verify focus returns to input",
    ),

    A11yRule(
        rule_id="P7-A11Y-007",
        category=A11yCategory.FOCUS,
        priority=A11yPriority.HIGH,
        title="Focus trap for modal dialogs only",
        description="Only use focus trapping for true modal dialogs, not status overlays.",
        wcag_criterion="2.4.3 Focus Order",
        implementation_notes="""
- Connection lost banner: NOT a modal, no focus trap
- Diagnostics tray: NOT a modal, no focus trap
- Error inspector modal: IS a modal, use focus trap
- Tab key should cycle through page normally with overlays visible
        """,
        test_method="Tab through page with diagnostics tray open, verify all page elements accessible",
    ),

    A11yRule(
        rule_id="P7-A11Y-008",
        category=A11yCategory.FOCUS,
        priority=A11yPriority.MEDIUM,
        title="Visible focus indicators during streaming",
        description="Focus indicators must remain visible even when content is updating.",
        wcag_criterion="2.4.7 Focus Visible",
        implementation_notes="""
- Use CSS :focus-visible for keyboard focus
- Ensure focus outline contrasts with dynamic backgrounds
- Don't remove focus styles during loading states
- Consider thicker borders in high-contrast mode
        """,
        test_method="Visual inspection of focus indicators during event stream",
    ),

    # =========================================================================
    # SCROLL INDEPENDENCE RULES
    # =========================================================================
    A11yRule(
        rule_id="P7-A11Y-009",
        category=A11yCategory.SCROLL,
        priority=A11yPriority.CRITICAL,
        title="Never auto-scroll main content",
        description="Main page scroll position must never change due to streaming updates.",
        wcag_criterion="2.2.2 Pause, Stop, Hide",
        implementation_notes="""
- New content inserted above viewport: adjust scroll to maintain position
- New content below viewport: no scroll adjustment needed
- If user is at bottom and expects updates: optional "stick to bottom" feature
- User must be able to disable any auto-scrolling behavior
        """,
        test_method="Scroll to middle of page, trigger events, verify scroll doesn't change",
    ),

    A11yRule(
        rule_id="P7-A11Y-010",
        category=A11yCategory.SCROLL,
        priority=A11yPriority.HIGH,
        title="Contained scroll for event lists",
        description="Event lists should scroll independently from the main page.",
        wcag_criterion="1.4.10 Reflow",
        implementation_notes="""
- Use overflow-y: auto on event list containers
- Set max-height to prevent list from growing unbounded
- Implement virtual scrolling for large event counts
- Don't let list container affect main page layout
        """,
        test_method="Verify event list scrolls independently from main page",
    ),

    A11yRule(
        rule_id="P7-A11Y-011",
        category=A11yCategory.SCROLL,
        priority=A11yPriority.HIGH,
        title="Provide 'scroll to latest' control",
        description="Give users explicit control to jump to latest content.",
        wcag_criterion="2.4.1 Bypass Blocks",
        implementation_notes="""
- Button: "Jump to latest" when user has scrolled up in event list
- Button should be keyboard accessible
- Announce when new content is available below
- Don't auto-invoke; wait for user action
        """,
        test_method="Scroll up in event list, verify 'jump to latest' button appears",
    ),

    A11yRule(
        rule_id="P7-A11Y-012",
        category=A11yCategory.SCROLL,
        priority=A11yPriority.MEDIUM,
        title="Respect prefers-reduced-motion for scroll animations",
        description="Smooth scrolling should be disabled for users who prefer reduced motion.",
        wcag_criterion="2.3.3 Animation from Interactions",
        implementation_notes="""
- Check prefers-reduced-motion media query
- Use instant scroll behavior when reduced motion preferred
- Apply to both manual and programmatic scrolling
- CSS: scroll-behavior: auto when prefers-reduced-motion
        """,
        test_method="Enable reduced motion in OS, verify smooth scrolling is disabled",
    ),

    # =========================================================================
    # TIMING RULES
    # =========================================================================
    A11yRule(
        rule_id="P7-A11Y-013",
        category=A11yCategory.TIMING,
        priority=A11yPriority.HIGH,
        title="Provide time to read status messages",
        description="Status messages must remain visible long enough to be read.",
        wcag_criterion="2.2.1 Timing Adjustable",
        implementation_notes="""
- Success toasts: minimum 5 seconds, or until dismissed
- Warning messages: remain until acknowledged or condition cleared
- Error messages: remain until acknowledged
- Progress updates: update text in place, don't replace rapidly
        """,
        test_method="Time how long status messages remain visible",
    ),

    A11yRule(
        rule_id="P7-A11Y-014",
        category=A11yCategory.TIMING,
        priority=A11yPriority.MEDIUM,
        title="Allow pause of auto-updating content",
        description="Users must be able to pause content that updates automatically.",
        wcag_criterion="2.2.2 Pause, Stop, Hide",
        implementation_notes="""
- Provide pause button for event stream display
- Paused state: new events buffered but not displayed
- Resume shows buffered events with summary
- Diagnostics tray: pause button for event list
        """,
        test_method="Verify pause button stops visual updates",
    ),

    # =========================================================================
    # MOTION RULES
    # =========================================================================
    A11yRule(
        rule_id="P7-A11Y-015",
        category=A11yCategory.MOTION,
        priority=A11yPriority.HIGH,
        title="Respect prefers-reduced-motion",
        description="All animations must respect prefers-reduced-motion setting.",
        wcag_criterion="2.3.3 Animation from Interactions",
        implementation_notes="""
- Spinner animations: show static icon instead
- Pulse animations on status dots: use opacity change only
- Slide-in animations: use instant display
- Progress bars: update without animation
        """,
        test_method="Enable reduced motion, verify all animations are disabled",
    ),

    A11yRule(
        rule_id="P7-A11Y-016",
        category=A11yCategory.MOTION,
        priority=A11yPriority.MEDIUM,
        title="Avoid continuous animations",
        description="Continuous animations should be time-limited or user-controlled.",
        wcag_criterion="2.2.2 Pause, Stop, Hide",
        implementation_notes="""
- Reconnecting spinner: acceptable during reconnection
- Pulsing indicators: limit to 5 seconds, then static
- Loading animations: acceptable during active loading
- Background animations: avoid entirely
        """,
        test_method="Observe page for 30 seconds idle, verify no continuous motion",
    ),

    # =========================================================================
    # KEYBOARD RULES
    # =========================================================================
    A11yRule(
        rule_id="P7-A11Y-017",
        category=A11yCategory.KEYBOARD,
        priority=A11yPriority.CRITICAL,
        title="All controls keyboard accessible",
        description="All SSE-related controls must be operable via keyboard.",
        wcag_criterion="2.1.1 Keyboard",
        implementation_notes="""
- Diagnostics toggle: Tab + Enter/Space
- Tray close button: Tab + Enter/Space
- Reconnect button: Tab + Enter/Space
- Event list items: Arrow keys for navigation
- All buttons must have visible focus indicator
        """,
        test_method="Complete all SSE operations using only keyboard",
    ),

    A11yRule(
        rule_id="P7-A11Y-018",
        category=A11yCategory.KEYBOARD,
        priority=A11yPriority.HIGH,
        title="Escape key closes overlays",
        description="Diagnostics tray and error details should close with Escape.",
        wcag_criterion="2.1.2 No Keyboard Trap",
        implementation_notes="""
- Escape closes diagnostics tray
- Escape closes error inspector
- Escape does NOT dismiss connection lost banner (important info)
- After close, focus returns to trigger element
        """,
        test_method="Open tray, press Escape, verify closure and focus return",
    ),
]


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class StreamingA11yConfig:
    """Configuration for streaming accessibility."""
    # Announcement settings
    announcement_throttle_ms: int = 2000
    status_update_interval_ms: int = 5000
    verbosity_level: str = "standard"  # minimal, standard, verbose

    # Focus settings
    preserve_focus_on_update: bool = True
    restore_focus_after_reconnect: bool = True

    # Scroll settings
    auto_scroll_enabled: bool = False
    stick_to_bottom: bool = False
    smooth_scroll: bool = True

    # Motion settings
    respect_reduced_motion: bool = True
    animation_duration_ms: int = 200

    # Timing settings
    toast_duration_ms: int = 5000
    allow_pause: bool = True


# ============================================================================
# ARIA-LIVE POLICY
# ============================================================================

class LiveRegionPolicy(Enum):
    """Policy for aria-live region updates."""
    IMMEDIATE = "immediate"       # Announce immediately
    THROTTLED = "throttled"       # Throttle to max rate
    BATCHED = "batched"           # Batch into summaries
    SILENT = "silent"             # Don't announce


@dataclass
class AriaLivePolicy:
    """Policy for a specific event type."""
    event_type: str
    politeness: str  # "off", "polite", "assertive"
    policy: LiveRegionPolicy
    throttle_ms: int = 2000
    summary_template: str = ""


DEFAULT_ARIA_LIVE_POLICIES: Dict[str, AriaLivePolicy] = {
    "connection_lost": AriaLivePolicy(
        event_type="connection_lost",
        politeness="assertive",
        policy=LiveRegionPolicy.IMMEDIATE,
        summary_template="Connection lost. Attempting to reconnect.",
    ),
    "connection_restored": AriaLivePolicy(
        event_type="connection_restored",
        politeness="assertive",
        policy=LiveRegionPolicy.IMMEDIATE,
        summary_template="Connection restored.",
    ),
    "reconnecting": AriaLivePolicy(
        event_type="reconnecting",
        politeness="polite",
        policy=LiveRegionPolicy.THROTTLED,
        throttle_ms=3000,
        summary_template="Reconnection attempt {attempt} of {max}.",
    ),
    "replay_started": AriaLivePolicy(
        event_type="replay_started",
        politeness="polite",
        policy=LiveRegionPolicy.IMMEDIATE,
        summary_template="Syncing {count} missed events.",
    ),
    "replay_complete": AriaLivePolicy(
        event_type="replay_complete",
        politeness="polite",
        policy=LiveRegionPolicy.IMMEDIATE,
        summary_template="Sync complete. {count} events processed.",
    ),
    "event_received": AriaLivePolicy(
        event_type="event_received",
        politeness="off",
        policy=LiveRegionPolicy.BATCHED,
        throttle_ms=5000,
        summary_template="{count} new events received.",
    ),
    "error": AriaLivePolicy(
        event_type="error",
        politeness="assertive",
        policy=LiveRegionPolicy.THROTTLED,
        throttle_ms=5000,
        summary_template="Error: {message}",
    ),
    "sequence_gap": AriaLivePolicy(
        event_type="sequence_gap",
        politeness="polite",
        policy=LiveRegionPolicy.BATCHED,
        throttle_ms=10000,
        summary_template="{count} events may have been missed.",
    ),
}


def get_aria_live_policy(event_type: str) -> AriaLivePolicy:
    """
    Get aria-live policy for event type.

    Args:
        event_type: Type of event

    Returns:
        AriaLivePolicy for the event type
    """
    return DEFAULT_ARIA_LIVE_POLICIES.get(
        event_type,
        AriaLivePolicy(
            event_type=event_type,
            politeness="off",
            policy=LiveRegionPolicy.SILENT,
        )
    )


def should_announce_update(
    event_type: str,
    last_announcement_ms: int,
    config: Optional[StreamingA11yConfig] = None,
) -> bool:
    """
    Determine if an update should be announced.

    Args:
        event_type: Type of event
        last_announcement_ms: Time since last announcement
        config: Optional config

    Returns:
        True if update should be announced
    """
    config = config or StreamingA11yConfig()
    policy = get_aria_live_policy(event_type)

    if policy.policy == LiveRegionPolicy.SILENT:
        return False

    if policy.policy == LiveRegionPolicy.IMMEDIATE:
        return True

    if policy.policy in (LiveRegionPolicy.THROTTLED, LiveRegionPolicy.BATCHED):
        return last_announcement_ms >= policy.throttle_ms

    return False


# ============================================================================
# FOCUS STABILITY
# ============================================================================

@dataclass
class FocusStabilityRule:
    """A focus stability rule."""
    rule_id: str
    description: str
    check_function: str  # Name of function to check


FOCUS_STABILITY_RULES: List[FocusStabilityRule] = [
    FocusStabilityRule(
        rule_id="focus-001",
        description="Focus must not change during event processing",
        check_function="check_focus_unchanged",
    ),
    FocusStabilityRule(
        rule_id="focus-002",
        description="Focus must be restored after reconnection",
        check_function="check_focus_restored",
    ),
    FocusStabilityRule(
        rule_id="focus-003",
        description="Overlays must not trap focus unless modal",
        check_function="check_no_trap",
    ),
    FocusStabilityRule(
        rule_id="focus-004",
        description="Focus indicators must be visible during updates",
        check_function="check_focus_visible",
    ),
]


def get_focus_stability_rules() -> List[Dict[str, str]]:
    """
    Get focus stability rules as dictionaries.

    Returns:
        List of rule dictionaries
    """
    return [
        {
            "rule_id": rule.rule_id,
            "description": rule.description,
            "check_function": rule.check_function,
        }
        for rule in FOCUS_STABILITY_RULES
    ]


# ============================================================================
# SCROLL INDEPENDENCE
# ============================================================================

def get_scroll_independence_css(respect_reduced_motion: bool = True) -> str:
    """
    Get CSS for scroll independence.

    Args:
        respect_reduced_motion: Whether to respect prefers-reduced-motion

    Returns:
        CSS string
    """
    reduced_motion_rule = """
@media (prefers-reduced-motion: reduce) {
    .cip-event-list,
    .cip-diagnostics-content {
        scroll-behavior: auto !important;
    }

    * {
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
    }
}
""" if respect_reduced_motion else ""

    return f"""
/* Scroll Independence Rules - P7 A11y */

/* Event lists scroll independently */
.cip-event-list {{
    max-height: 300px;
    overflow-y: auto;
    overflow-x: hidden;
    scroll-behavior: smooth;
    overscroll-behavior: contain;
}}

/* Diagnostics content contained */
.cip-diagnostics-content {{
    max-height: 400px;
    overflow-y: auto;
    overscroll-behavior: contain;
}}

/* Prevent main page scroll on overlay interaction */
.cip-overlay-active body {{
    overflow: hidden;
}}

/* Jump to latest button */
.cip-jump-to-latest {{
    position: sticky;
    bottom: 0;
    background: var(--cip-bg-secondary);
    padding: 8px;
    text-align: center;
    border-top: 1px solid var(--cip-border-default);
}}

{reduced_motion_rule}
"""


# ============================================================================
# VALIDATION
# ============================================================================

def validate_streaming_a11y(
    has_aria_live: bool = False,
    has_focus_management: bool = False,
    has_scroll_containment: bool = False,
    respects_reduced_motion: bool = False,
    has_keyboard_support: bool = False,
) -> Dict[str, Any]:
    """
    Validate streaming accessibility implementation.

    Args:
        has_aria_live: Whether aria-live regions are implemented
        has_focus_management: Whether focus is properly managed
        has_scroll_containment: Whether scroll is contained
        respects_reduced_motion: Whether reduced motion is respected
        has_keyboard_support: Whether keyboard navigation works

    Returns:
        Validation results
    """
    issues = []
    passed = []

    checks = [
        ("aria_live", has_aria_live, "ARIA live regions for announcements"),
        ("focus_management", has_focus_management, "Focus stability during updates"),
        ("scroll_containment", has_scroll_containment, "Independent scroll for event lists"),
        ("reduced_motion", respects_reduced_motion, "Respects prefers-reduced-motion"),
        ("keyboard_support", has_keyboard_support, "Full keyboard accessibility"),
    ]

    for check_id, check_passed, description in checks:
        if check_passed:
            passed.append({"id": check_id, "description": description})
        else:
            issues.append({"id": check_id, "description": f"Missing: {description}"})

    # Calculate compliance
    total_critical = len([r for r in A11Y_STREAMING_CHECKLIST if r.priority == A11yPriority.CRITICAL])
    passed_critical = len([c for c in passed if c["id"] in ["aria_live", "focus_management", "keyboard_support"]])

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "passed": passed,
        "checklist_items": len(A11Y_STREAMING_CHECKLIST),
        "critical_items": total_critical,
        "wcag_level": "AA" if len(issues) == 0 else "Partial",
        "compliance_pct": (len(passed) / len(checks) * 100) if checks else 0,
    }


def get_checklist_by_category(category: A11yCategory) -> List[A11yRule]:
    """
    Get checklist items by category.

    Args:
        category: Category to filter by

    Returns:
        List of rules in category
    """
    return [r for r in A11Y_STREAMING_CHECKLIST if r.category == category]


def get_checklist_by_priority(priority: A11yPriority) -> List[A11yRule]:
    """
    Get checklist items by priority.

    Args:
        priority: Priority to filter by

    Returns:
        List of rules with priority
    """
    return [r for r in A11Y_STREAMING_CHECKLIST if r.priority == priority]


def export_checklist_markdown() -> str:
    """
    Export checklist as Markdown document.

    Returns:
        Markdown string
    """
    lines = [
        "# P7 Streaming Accessibility Checklist",
        "",
        "CIP Protocol: CC2 Implementation",
        "",
        "## Summary",
        "",
        f"- Total Rules: {len(A11Y_STREAMING_CHECKLIST)}",
        f"- Critical: {len(get_checklist_by_priority(A11yPriority.CRITICAL))}",
        f"- High: {len(get_checklist_by_priority(A11yPriority.HIGH))}",
        f"- Medium: {len(get_checklist_by_priority(A11yPriority.MEDIUM))}",
        "",
    ]

    for category in A11yCategory:
        rules = get_checklist_by_category(category)
        if not rules:
            continue

        lines.append(f"## {category.value.replace('_', ' ').title()}")
        lines.append("")

        for rule in rules:
            priority_badge = {
                A11yPriority.CRITICAL: "[CRITICAL]",
                A11yPriority.HIGH: "[HIGH]",
                A11yPriority.MEDIUM: "[MEDIUM]",
                A11yPriority.LOW: "[LOW]",
            }.get(rule.priority, "")

            lines.append(f"### {rule.rule_id}: {rule.title} {priority_badge}")
            lines.append("")
            lines.append(rule.description)
            lines.append("")

            if rule.wcag_criterion:
                lines.append(f"**WCAG:** {rule.wcag_criterion}")
                lines.append("")

            if rule.implementation_notes:
                lines.append("**Implementation:**")
                lines.append("```")
                lines.append(rule.implementation_notes.strip())
                lines.append("```")
                lines.append("")

            if rule.test_method:
                lines.append(f"**Test:** {rule.test_method}")
                lines.append("")

    return "\n".join(lines)
