# CC HANDOFF: CIP UI Design Implementation

**Date:** November 29, 2025  
**From:** CAI (Claude.ai)  
**To:** CC (Claude Code)  
**Priority:** MEDIUM (Future Sprint)

---

## OVERVIEW

CAI and USER designed the CIP (Contract Intelligence Platform) UI with a Modern Dark theme. The splash screen animation is complete. CC needs to implement the remaining pages using the established design system.

---

## COMPLETED ASSETS

| Asset | Status | Location |
|-------|--------|----------|
| Splash Animation | ✅ Complete | `CIP_Splash_Animation.html` |
| Design System | ✅ Defined | See specs below |
| Dashboard (Basic) | ✅ Skeleton | Included in splash file |

---

## DESIGN SYSTEM SPECIFICATIONS

### Color Palette

| Purpose | Color | Hex |
|---------|-------|-----|
| **Background (primary)** | Near-black | `#0F172A` |
| **Background (surface)** | Dark slate | `#1E293B` |
| **Border** | Subtle white | `rgba(255,255,255,0.05)` |
| **Text (primary)** | White | `#FFFFFF` |
| **Text (secondary)** | Light gray | `#E2E8F0` |
| **Text (muted)** | Gray | `#94A3B8` |
| **Text (subtle)** | Dark gray | `#64748B` |
| **Primary gradient** | Blue→Purple | `linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)` |
| **Primary solid** | Blue | `#3B82F6` |
| **Accent** | Purple | `#8B5CF6` |

### Risk Level Colors

| Level | Hex | Background (15% opacity) | Border (30% opacity) |
|-------|-----|--------------------------|----------------------|
| 🔴 CRITICAL | `#EF4444` | `rgba(239, 68, 68, 0.15)` | `rgba(239, 68, 68, 0.3)` |
| 🟠 HIGH | `#F97316` | `rgba(249, 115, 22, 0.15)` | `rgba(249, 115, 22, 0.3)` |
| 🟡 MODERATE | `#FBBF24` | `rgba(251, 191, 36, 0.15)` | `rgba(251, 191, 36, 0.3)` |
| 🟢 LOW | `#10B981` | `rgba(16, 185, 129, 0.15)` | `rgba(16, 185, 129, 0.3)` |

### Status Colors

| Status | Hex |
|--------|-----|
| Success | `#10B981` |
| Warning | `#F59E0B` |
| Error | `#EF4444` |
| Info | `#3B82F6` |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Page title | Inter/System | 32px | 800 |
| Card title | Inter/System | 16px | 700 |
| Body | Inter/System | 14px | 400/500 |
| Label | Inter/System | 13px | 500 |
| Caption | Inter/System | 12px | 400 |
| Nav label | Inter/System | 11px | 600 |

### Spacing

| Size | Value |
|------|-------|
| xs | 4px |
| sm | 8px |
| md | 16px |
| lg | 24px |
| xl | 32px |
| 2xl | 48px |

### Border Radius

| Element | Radius |
|---------|--------|
| Buttons | 10px |
| Cards | 16px |
| Badges | 8px |
| Nav items | 12px |
| Inputs | 8px |

### Shadows & Effects

```css
/* Card hover glow */
box-shadow: 0 0 30px rgba(59, 130, 246, 0.1);

/* Button shadow */
box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);

/* Button hover shadow */
box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);

/* Risk dot glow */
box-shadow: 0 0 8px [risk-color];
```

---

## COMPONENT LIBRARY

### Buttons

```css
/* Primary */
.btn-primary {
    background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 10px;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
}

/* Secondary */
.btn-secondary {
    background: rgba(255,255,255,0.05);
    color: #E2E8F0;
    border: 1px solid rgba(255,255,255,0.1);
}

.btn-secondary:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.2);
}
```

### Cards

```css
.card {
    background: #1E293B;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
}

.card:hover {
    box-shadow: 0 0 30px rgba(59, 130, 246, 0.1);
}
```

### Stat Cards

```css
.stat-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.05);
}

.stat-card:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 130, 246, 0.3);
}
```

### Risk Badges

```css
.risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
}

/* Example: Critical */
.risk-critical {
    background: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Risk dot with glow */
.risk-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #EF4444;
    box-shadow: 0 0 8px #EF4444;
}
```

### Navigation

```css
.nav-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    border-radius: 12px;
    color: #94A3B8;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
}

.nav-item:hover {
    background: rgba(59, 130, 246, 0.1);
    color: #E2E8F0;
}

.nav-item.active {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
    color: white;
}

/* Active indicator bar */
.nav-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 24px;
    background: linear-gradient(180deg, #3B82F6 0%, #8B5CF6 100%);
    border-radius: 0 4px 4px 0;
}
```

### Tables

```css
.table {
    width: 100%;
    border-collapse: collapse;
}

.table th {
    text-align: left;
    padding: 14px 20px;
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.table td {
    padding: 18px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    font-size: 14px;
}

.table tr:hover {
    background: rgba(59, 130, 246, 0.05);
}
```

---

## PAGES TO IMPLEMENT

### 1. Dashboard (Enhance existing)
- [ ] Complete stats grid with icons
- [ ] Contracts table with full data
- [ ] Activity feed with timestamps
- [ ] Risk distribution chart (pie/donut)
- [ ] Upcoming expirations widget

### 2. Contracts List
- [ ] Filterable/sortable table
- [ ] Search bar
- [ ] Status filters (tabs or dropdown)
- [ ] Bulk actions
- [ ] Pagination

### 3. Contract Detail
- [ ] Contract metadata header
- [ ] Risk summary card
- [ ] Clause analysis accordion
- [ ] Version history timeline
- [ ] Action buttons (Analyze, Generate Report, etc.)

### 4. Risk Analysis
- [ ] Risk heat map visualization
- [ ] Clause-by-clause breakdown
- [ ] Risk trend chart
- [ ] Recommendations panel

### 5. Reports
- [ ] Report list/history
- [ ] Report type selector
- [ ] Generate new report form
- [ ] Download/export options

### 6. Contract Upload
- [ ] Drag-and-drop zone
- [ ] File type validation
- [ ] Upload progress indicator
- [ ] Metadata input form

### 7. Settings
- [ ] User profile section
- [ ] Notification preferences
- [ ] Theme toggle (if supporting light mode later)
- [ ] API configuration

---

## STREAMLIT IMPLEMENTATION NOTES

### Using streamlit-shadcn-ui

```bash
pip install streamlit-shadcn-ui
```

```python
import streamlit as st
import streamlit_shadcn_ui as ui

# Cards
ui.card(
    title="Total Contracts",
    content="47",
    description="+12% vs last month",
    key="card1"
)

# Tabs
ui.tabs(
    options=['Dashboard', 'Contracts', 'Reports'],
    default_value='Dashboard',
    key="nav_tabs"
)

# Badges
ui.badges(
    badge_list=[("CRITICAL", "destructive"), ("5 items", "secondary")],
    key="risk_badges"
)
```

### Custom CSS in Streamlit

```python
st.markdown("""
<style>
    /* Apply dark theme */
    .stApp {
        background-color: #0F172A;
    }
    
    /* Custom component styling */
    .risk-badge-critical {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        padding: 6px 14px;
        border-radius: 8px;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
</style>
""", unsafe_allow_html=True)
```

### Streamlit Config (.streamlit/config.toml)

```toml
[theme]
base = "dark"
primaryColor = "#3B82F6"
backgroundColor = "#0F172A"
secondaryBackgroundColor = "#1E293B"
textColor = "#E2E8F0"
```

---

## BRANDING

| Element | Value |
|---------|-------|
| **Logo text** | CIP |
| **Tagline** | Contract Intelligence Platform |
| **Logo style** | Gradient text (Blue→Purple) |
| **Letter spacing** | 4-12px depending on size |

### Logo CSS

```css
.logo {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 4px;
    background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
```

---

## ANIMATION GUIDELINES

### Transitions
- Default: `all 0.2s ease`
- Cards: `all 0.3s ease`
- Modals: `all 0.3s cubic-bezier(0.4, 0, 0.2, 1)`

### Hover Effects
- Buttons: `translateY(-2px)` + enhanced shadow
- Cards: `translateY(-4px)` + glow
- Table rows: Background color change

### Loading States
- Use skeleton screens (not spinners)
- Pulse animation for loading placeholders

---

## FILE STRUCTURE (Recommended)

```
CIP/
├── frontend/
│   ├── app.py                 # Main Streamlit app
│   ├── pages/
│   │   ├── 1_Dashboard.py
│   │   ├── 2_Contracts.py
│   │   ├── 3_Risk_Analysis.py
│   │   ├── 4_Reports.py
│   │   └── 5_Settings.py
│   ├── components/
│   │   ├── sidebar.py
│   │   ├── cards.py
│   │   ├── tables.py
│   │   └── charts.py
│   ├── styles/
│   │   └── custom.css
│   └── .streamlit/
│       └── config.toml
├── assets/
│   ├── splash/
│   │   └── CIP_Splash_Animation.html
│   └── images/
└── docs/
    └── UI_Design_System.md
```

---

## PRIORITY ORDER

1. **Dashboard** - Enhance with full functionality
2. **Contracts List** - Core workflow
3. **Contract Detail** - Core workflow
4. **Risk Analysis** - Key differentiator
5. **Reports** - Integration with document generation skill
6. **Upload** - User onboarding
7. **Settings** - Lower priority

---

## REFERENCE FILES

- `CIP_Splash_Animation.html` - Complete splash with animation
- `CIP_UI_Option2_Modern_Dark.html` - Original dark theme mockup
- This document - Design system specs

---

## QUESTIONS FOR USER (Before Starting)

1. **Light mode support?** - Design for dark-only or include toggle?
2. **Charts library?** - Plotly, Altair, or custom?
3. **Mobile responsive?** - Priority level for mobile support?

---

**END OF HANDOFF**
