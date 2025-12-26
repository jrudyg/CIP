# Component Design Notes — Phase 6 UI Upgrade

**Document Version**: 1.0
**Author**: CC2 (UI Component Specialist)
**Date**: 2024-12-09
**Phase**: P6.C2.T1 & P6.C2.T2

---

## Table of Contents

1. [Overview](#overview)
2. [P6.C2.T1: High-Contrast TopNav](#p6c2t1-high-contrast-topnav)
3. [P6.C2.T2: Selection Component Upgrade](#p6c2t2-selection-component-upgrade)
4. [Token System Design](#token-system-design)
5. [Accessibility Strategy](#accessibility-strategy)
6. [CSS Architecture](#css-architecture)
7. [CC3 Integration Points](#cc3-integration-points)
8. [Future Enhancements](#future-enhancements)

---

## Overview

Phase 6 UI Upgrade introduces a unified component system with:
- Consistent color token architecture
- WCAG AA accessibility compliance (AAA in high-contrast mode)
- Streamlit-native rendering with custom CSS enhancement
- Session state persistence across reruns
- Modular integration points for CC3 data binding

### Design Philosophy

1. **Token-First Styling**: All colors derive from `color_tokens.py`, enabling global theme control
2. **Progressive Enhancement**: Components work with native Streamlit, CSS adds polish
3. **Accessibility by Default**: Focus indicators, ARIA semantics, and keyboard navigation are built-in
4. **State Isolation**: Each component manages its own session state with namespaced keys
5. **CC3-Ready**: Binder-compatible output formats for seamless backend integration

---

## P6.C2.T1: High-Contrast TopNav

### Design Rationale

The TopNav component serves as the global navigation anchor for all CIP pages. Key design decisions:

**1. Tabbed Navigation Model**
- Four primary tabs: Upload → Compare → Analyze → Export
- Reflects the natural workflow progression in contract analysis
- Badge count support for notification scenarios (e.g., pending uploads)

**2. Sticky Positioning**
- `position: sticky` keeps nav visible during scroll
- Z-index of 1000 ensures overlay priority
- Negative margins (-1rem) extend to page edges

**3. High-Contrast Toggle**
- System-wide toggle affects all components consuming tokens
- Session state persistence survives page navigation
- Visual feedback: icon changes (🔲 ↔ 🔳) plus border highlight

### Component Files

| File | Purpose |
|------|---------|
| `color_tokens.py` | Token definitions + contrast mode state |
| `topnav.py` | Navigation component + rendering |

### State Keys

```
_cip_high_contrast_mode    - Boolean, contrast toggle state
_cip_topnav_active_tab     - String, active tab ID
```

---

## P6.C2.T2: Selection Component Upgrade

### Design Rationale

The Clause Selector manages V1/V2 clause pair selection with filtering capabilities.

**1. Linked Selection Mode**
- Default: selecting V1 auto-selects matching V2 (linked mode)
- Optional: independent selection for cross-version comparison
- Visual indicator: 🔗 (linked) vs 🔓 (independent)

**2. Filter Tabs**
- All: Shows complete clause list
- Changed: Filters to `has_changes=True` clauses
- Critical: Filters to `severity="CRITICAL"`
- High Risk: Filters to `severity in ("CRITICAL", "HIGH")`

**3. Multi-State Styling**
- Seven distinct visual states for clause items
- Each state has unique border, background, and focus treatment
- High-contrast mode increases indicator visibility

### State Keys

```
_cip_clause_v1_id          - Optional[int], V1 selection
_cip_clause_v2_id          - Optional[int], V2 selection
_cip_clause_linked         - Boolean, linked mode flag
_cip_clause_filter_tab     - String, active filter tab
_cip_clause_v1_clauses     - List[ClauseInfo], available V1 clauses
_cip_clause_v2_clauses     - List[ClauseInfo], available V2 clauses
_cip_clause_topnav_sync    - Boolean, TopNav sync enabled
```

---

## Token System Design

### Architecture

```
color_tokens.py
├── ColorToken dataclass
│   ├── name: str
│   ├── standard: str (hex/rgba)
│   ├── high_contrast: str (hex/rgba)
│   └── description: str
├── BASE_TOKENS (17 tokens)
│   ├── bg-primary, bg-secondary, bg-tertiary
│   ├── surface-default, surface-elevated, surface-overlay
│   ├── text-primary, text-secondary, text-muted, text-disabled
│   ├── border-default, border-strong, border-focus
│   └── accent-primary, accent-success, accent-warning, accent-error
├── PIPELINE_TOKENS (20 tokens)
│   ├── SAE: sae-primary, sae-bg, sae-border
│   ├── ERCE: erce-critical(-bg), erce-high(-bg), erce-moderate(-bg), erce-admin(-bg)
│   ├── BIRL: birl-margin, birl-risk, birl-compliance, birl-schedule, birl-quality, birl-cashflow
│   └── FAR: far-critical, far-high, far-moderate
└── NAV_TOKENS (6 tokens)
    └── nav-bg, nav-border, nav-tab-active, nav-tab-hover, nav-tab-text, nav-tab-text-inactive
```

### Token Naming Convention

```
{category}-{variant}[-{modifier}]

Examples:
- bg-primary          → Background, primary variant
- text-muted          → Text, muted variant
- erce-critical-bg    → ERCE pipeline, critical severity, background modifier
- nav-tab-active      → Navigation, tab element, active state
```

### High-Contrast Strategy

Standard mode uses subtle distinctions suitable for typical displays:
- Background: `#0F172A` (dark slate)
- Text: `#F1F5F9` (light gray)
- Accents: Saturated but not harsh

High-contrast mode maximizes differentiation:
- Background: `#000000` (pure black)
- Text: `#FFFFFF` (pure white)
- Accents: Brighter variants (e.g., `#3B82F6` → `#60A5FA`)
- Borders: Increased width (1px → 2px, 2px → 3px)

### CSS Variable Generation

Tokens are injected as CSS custom properties:

```css
:root {
  --cip-bg-primary: #0F172A;
  --cip-text-primary: #F1F5F9;
  --cip-accent-primary: #3B82F6;
  /* ... 41 total variables */
}
```

Usage in component CSS:
```css
.cip-component {
  background: var(--cip-bg-primary);
  color: var(--cip-text-primary);
}
```

---

## Accessibility Strategy

### WCAG Compliance Target

| Level | Status | Notes |
|-------|--------|-------|
| A | ✅ PASS | All criteria met |
| AA | ✅ PASS | Default mode |
| AAA | ✅ PASS | High-contrast mode only |

### Focus Indicator Design

Focus indicators use the `a11y_utils.py` helper system:

```python
from components.a11y_utils import generate_focus_css, FocusConfig

config = FocusConfig(
    outline_width="2px",
    outline_style="solid",
    outline_color="#3B82F6",
    outline_offset="-2px",
    high_contrast_width="3px",
    high_contrast_color="#60A5FA",
)

css = generate_focus_css(".my-element", config, high_contrast=False)
```

**Generated CSS:**
```css
.my-element:focus {
    outline: 2px solid #3B82F6;
    outline-offset: -2px;
}

.my-element:focus-visible {
    outline: 2px solid #3B82F6;
    outline-offset: -2px;
}

.my-element:focus:not(:focus-visible) {
    outline: none;
}
```

### Keyboard Navigation

| Component | Keys | Behavior |
|-----------|------|----------|
| TopNav tabs | Tab, Enter/Space | Navigate and activate tabs |
| Selection tabs | Tab, Enter/Space | Navigate and activate filter tabs |
| Clause items | Tab, Enter/Space | Navigate list, select item |
| Link toggle | Tab, Enter/Space | Toggle linked mode |

### ARIA Implementation

**TopNav:**
```html
<nav role="navigation" aria-label="Main navigation">
    <div role="tablist">
        <button role="tab"
                aria-selected="true"
                tabindex="0">
            Upload
        </button>
    </div>
</nav>
```

**Clause Selector:**
```html
<div role="tablist" aria-label="Clause filter tabs">
    <button role="tab"
            aria-selected="true"
            aria-controls="clause-panel-all">
        All
    </button>
</div>

<div role="listbox" aria-label="Version 1 clauses">
    <div role="option"
         aria-selected="true"
         tabindex="0">
        Clause #1: Liability
    </div>
</div>

<button aria-pressed="true"
        aria-label="Selection mode: Linked">
    🔗 Linked
</button>

<div aria-live="polite" aria-atomic="true">
    Current Selection: V1 #1 ↔ V2 #1
</div>
```

---

## CSS Architecture

### Class Naming Convention

All CIP components use the `cip-` prefix:

```
.cip-{component}[-{element}][-{modifier}]

Examples:
- .cip-topnav                    → TopNav container
- .cip-topnav-tab                → Tab element
- .cip-topnav-tab.active         → Active state modifier
- .cip-clause-selector           → Clause selector container
- .cip-clause-item.selected      → Selected clause item
- .cip-selection-tab-count       → Badge count element
```

### State Classes

| Class | Purpose |
|-------|---------|
| `.active` | Currently active/selected |
| `.selected` | User-selected item |
| `.disabled` | Interaction disabled |
| `.has-changes` | Item has modifications |
| `.linked` | Linked mode enabled |
| `.compact` | Compact display mode |

### CSS Generation Pattern

Components generate CSS dynamically based on current token values:

```python
def _generate_component_css() -> str:
    high_contrast = is_high_contrast_mode()

    # Get tokens (respects contrast mode)
    bg = get_token("bg-primary")
    text = get_token("text-primary")

    # Generate focus CSS from a11y_utils
    focus_css = generate_focus_css(".cip-item", config, high_contrast)

    # Adjust dimensions for high-contrast
    border_width = "2px" if high_contrast else "1px"

    return f"""
    <style>
    .cip-component {{
        background: {bg};
        color: {text};
        border-width: {border_width};
    }}
    {focus_css}
    </style>
    """
```

### Print Styles

All components include print-friendly styles:

```css
@media print {
    .cip-topnav {
        position: relative;
        background: white;
        border-bottom: 2px solid #333;
    }

    .cip-topnav-actions {
        display: none;  /* Hide contrast toggle */
    }
}
```

---

## CC3 Integration Points

### TopNav Integration

**State Access:**
```python
from components.topnav import get_active_tab, set_active_tab

# Read current tab
current = get_active_tab()  # "upload" | "compare" | "analyze" | "export"

# Programmatic navigation
set_active_tab("compare")
```

**Conditional Rendering:**
```python
from components.topnav import get_active_tab

tab = get_active_tab()
if tab == "compare":
    # Show comparison UI
elif tab == "analyze":
    # Show analysis pipelines
```

### Clause Selector Integration

**Binder Output Format:**
```python
from components.clause_selector import get_selection_for_binder

selection = get_selection_for_binder()
# Returns:
{
    "v1_clause_id": Optional[int],      # Selected V1 clause
    "v2_clause_id": Optional[int],      # Selected V2 clause
    "is_linked": bool,                   # Linked selection mode
    "has_selection": bool,               # Any selection exists
    "filter_tab": str,                   # Active filter ("all", "changed", etc.)
    "topnav_sync": Optional[str],        # Current TopNav tab if synced
}
```

**Direct State Access:**
```python
from components.clause_selector import (
    get_clause_selection,
    get_selected_clause_pair,
    has_valid_selection,
)

# ClauseSelection dataclass
selection = get_clause_selection()
print(selection.v1_clause_id, selection.v2_clause_id, selection.is_linked)

# Tuple format for simple cases
v1_id, v2_id = get_selected_clause_pair()

# Validation check
if has_valid_selection():
    # Proceed with analysis
```

**Clause Data Loading:**
```python
from components.clause_selector import (
    ClauseInfo,
    set_v1_clauses,
    set_v2_clauses,
)

# Populate from CC3 data
v1_clauses = [
    ClauseInfo(
        clause_id=1,
        title="Liability Limitation",
        section="Section 5.1",
        preview="The total liability shall not exceed...",
        severity="CRITICAL",
        has_changes=True,
        word_count=150,
        metadata={"far_ref": "52.249-2"},
    ),
    # ... more clauses
]

set_v1_clauses(v1_clauses)
set_v2_clauses(v2_clauses)
```

### TopNav-Selector Coordination

The clause selector can sync with TopNav state:

```python
from components.clause_selector import sync_with_topnav, is_topnav_compare_mode

# Get current TopNav tab
current_tab = sync_with_topnav()  # Returns tab ID or None

# Check if in compare mode
if is_topnav_compare_mode():
    # Enable comparison-specific features
```

---

## Future Enhancements

### Non-Blocking Improvements

These enhancements are recommended for future phases but do not block current functionality:

**1. Token System Expansion**
- Add semantic tokens for status indicators (info, success, warning, error)
- Support custom theme definitions (user-defined color schemes)
- Dark/light mode toggle (beyond high-contrast)

**2. TopNav Enhancements**
- Tab memory per session (restore last active tab on return)
- Sub-navigation support (dropdown menus within tabs)
- Breadcrumb integration for deep navigation
- Mobile hamburger menu for responsive layouts

**3. Clause Selector Improvements**
- Multi-select mode (select multiple clauses for batch operations)
- Search/filter by text within clauses
- Clause grouping by category/section
- Drag-and-drop reordering for custom sort
- Clause diff preview on hover
- Keyboard shortcuts (j/k for navigation, Enter for select)

**4. A11y Utils Expansion**
- Screen reader announcement queue
- Skip navigation links
- High contrast detection from OS settings
- Reduced motion support
- Focus trap for modal dialogs

**5. Performance Optimizations**
- CSS caching to reduce regeneration
- Virtual scrolling for large clause lists
- Lazy loading of clause previews
- Memoization of token lookups

### Integration Roadmap for CC3

| Phase | CC3 Action | UI Support |
|-------|------------|------------|
| P7 | SAE match data loading | `ClauseInfo.metadata` for SAE scores |
| P7 | ERCE risk propagation | Severity colors via `erce-*` tokens |
| P7 | BIRL narrative binding | `InsightsPanel` tab integration |
| P7 | FAR flowdown mapping | `far-*` tokens + action bar |

### Known Limitations

1. **Streamlit Rerun Model**: Full page reruns on state change; mitigated by session state
2. **CSS Injection**: Repeated injection on rerun; cached by browser
3. **Button-Based Interaction**: HTML buttons non-functional; Streamlit buttons required
4. **No JS Execution**: Pure CSS + Python; no client-side JavaScript

---

## Appendix: Quick Reference

### Token Access

```python
from components.color_tokens import get_token, is_high_contrast_mode

# Get token (respects current mode)
color = get_token("text-primary")

# Force specific mode
standard = get_token("text-primary", force_high_contrast=False)
hc = get_token("text-primary", force_high_contrast=True)

# Check mode
if is_high_contrast_mode():
    # Adjust for HC
```

### A11y Utils

```python
from components.a11y_utils import (
    generate_focus_css,
    get_tabindex,
    get_aria_attrs,
    format_aria_attrs,
    validate_focus_visible,
    validate_aria_role,
)

# Focus CSS
css = generate_focus_css(".selector", config, high_contrast=True)

# Tabindex
idx = get_tabindex(is_interactive=True, is_disabled=False)

# ARIA
attrs = get_aria_attrs("tab", selected=True, controls="panel-1")
html = format_aria_attrs(attrs)  # 'role="tab" aria-selected="true" ...'

# Validation
result = validate_focus_visible(css)
result = validate_aria_role("option", {"aria-selected": "true"})
```

### State Management

```python
# TopNav
from components.topnav import get_active_tab, set_active_tab
from components.color_tokens import toggle_high_contrast_mode

# Clause Selector
from components.clause_selector import (
    get_clause_selection,
    set_v1_clause,
    set_v2_clause,
    toggle_linked_mode,
    get_filter_tab,
    set_filter_tab,
    clear_clause_selection,
)
```

---

**End of Document**

*Generated by CC2 for Phase 6 UI Upgrade documentation.*
