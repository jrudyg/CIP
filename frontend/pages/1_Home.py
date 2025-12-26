# pages/1_Home.py
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from components.page_wrapper import (
    init_page,
    page_header,
    content_container
)
from components.workflow_animation import render_workflow_animation
from components.learning_animation import render_learning_animation


def get_contract_stats():
    """Fetch contract statistics from database."""
    db_path = Path(__file__).parent.parent.parent / "data" / "contracts.db"
    
    stats = {
        # Portfolio (Active)
        "portfolio_vendor": 0,
        "portfolio_customer": 0,
        "portfolio_total": 0,
        # Pipeline (In Progress)
        "pipeline_vendor": 0,
        "pipeline_customer": 0,
        "pipeline_total": 0,
        # Timeline (Next 90d)
        "timeline_expiring": 0,
        "timeline_renewal": 0,
        "timeline_pending": 0,
        # Activity (Past 90d)
        "activity_analyzed": 0,
        "activity_negotiating": 0,
        "activity_feedback": 0,
    }
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Date calculations
        today = datetime.now().date()
        next_90d = today + timedelta(days=90)
        past_90d = today - timedelta(days=90)
        
        # Portfolio - Active contracts by type
        cursor.execute("""
            SELECT contract_type, COUNT(*) 
            FROM contracts 
            WHERE status NOT IN ('archived', 'expired', 'terminated')
            GROUP BY contract_type
        """)
        for row in cursor.fetchall():
            contract_type, count = row
            if contract_type and 'vendor' in contract_type.lower():
                stats["portfolio_vendor"] += count
            elif contract_type and 'customer' in contract_type.lower():
                stats["portfolio_customer"] += count
            else:
                stats["portfolio_vendor"] += count
        
        stats["portfolio_total"] = stats["portfolio_vendor"] + stats["portfolio_customer"]
        
        # Pipeline - In Progress
        cursor.execute("""
            SELECT contract_type, COUNT(*) 
            FROM contracts 
            WHERE status IN ('intake', 'uploaded', 'analyzing', 'review', 'in_progress')
            GROUP BY contract_type
        """)
        for row in cursor.fetchall():
            contract_type, count = row
            if contract_type and 'vendor' in contract_type.lower():
                stats["pipeline_vendor"] += count
            elif contract_type and 'customer' in contract_type.lower():
                stats["pipeline_customer"] += count
            else:
                stats["pipeline_vendor"] += count
        
        stats["pipeline_total"] = stats["pipeline_vendor"] + stats["pipeline_customer"]
        
        # Timeline - Expiring in next 90 days
        cursor.execute("""
            SELECT COUNT(*) FROM contracts 
            WHERE expiration_date BETWEEN ? AND ?
            AND status NOT IN ('archived', 'expired', 'terminated')
        """, (today.isoformat(), next_90d.isoformat()))
        stats["timeline_expiring"] = cursor.fetchone()[0]
        
        # Timeline - Up for Renewal
        cursor.execute("""
            SELECT COUNT(*) FROM contracts 
            WHERE renewal_date BETWEEN ? AND ?
            AND status NOT IN ('archived', 'expired', 'terminated')
        """, (today.isoformat(), next_90d.isoformat()))
        result = cursor.fetchone()
        stats["timeline_renewal"] = result[0] if result else 0
        
        # Timeline - Pending Review
        cursor.execute("""
            SELECT COUNT(*) FROM contracts 
            WHERE status IN ('intake', 'uploaded', 'pending_review')
        """)
        stats["timeline_pending"] = cursor.fetchone()[0]
        
        # Activity - Analyzed in past 90 days
        cursor.execute("""
            SELECT COUNT(*) FROM risk_assessments 
            WHERE assessed_at >= ?
        """, (past_90d.isoformat(),))
        result = cursor.fetchone()
        stats["activity_analyzed"] = result[0] if result else 0
        
        # Activity - Negotiating
        cursor.execute("""
            SELECT COUNT(*) FROM contracts 
            WHERE status = 'negotiating'
            AND updated_at >= ?
        """, (past_90d.isoformat(),))
        result = cursor.fetchone()
        stats["activity_negotiating"] = result[0] if result else 0
        
        # Activity - Feedback received
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE created_at >= ?
        """, (past_90d.isoformat(),))
        result = cursor.fetchone()
        stats["activity_feedback"] = result[0] if result else 0
        
        conn.close()
    except Exception:
        pass
    
    return stats


def render_quick_stats():
    """Render compact Quick Stats section with 4 categories."""
    stats = get_contract_stats()
    
    # Ultra-compact Quick Stats styling
    st.markdown("""
        <style>
            .quick-stats-title {
                font-size: 1rem;
                font-weight: 600;
                color: #E2E8F0;
                margin-bottom: 8px;
            }
            .stat-category {
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.6));
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 10px;
                padding: 10px 12px;
            }
            .stat-category:hover {
                border-color: rgba(139, 92, 246, 0.4);
            }
            .stat-header {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-bottom: 2px;
            }
            .stat-header-icon {
                font-size: 0.9rem;
            }
            .stat-header-title {
                font-size: 0.7rem;
                font-weight: 700;
                letter-spacing: 1px;
                color: #A78BFA;
                text-transform: uppercase;
            }
            .stat-header-sub {
                font-size: 0.6rem;
                color: #64748B;
                margin-bottom: 6px;
                padding-left: 22px;
            }
            .stat-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 3px 0;
            }
            .stat-label {
                font-size: 0.7rem;
                color: #94A3B8;
            }
            .stat-value {
                font-size: 0.95rem;
                font-weight: 600;
                color: #E2E8F0;
            }
            .stat-value-highlight {
                color: #10B981;
            }
            .stat-value-warning {
                color: #F59E0B;
            }
            .stat-value-alert {
                color: #EF4444;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="quick-stats-title">Quick Stats</div>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    
    # Portfolio (Active)
    with cols[0]:
        st.markdown(f"""
            <div class="stat-category">
                <div class="stat-header">
                    <span class="stat-header-icon">📊</span>
                    <span class="stat-header-title">Portfolio</span>
                </div>
                <div class="stat-header-sub">(Active)</div>
                <div class="stat-row">
                    <span class="stat-label">Vendor</span>
                    <span class="stat-value">{stats['portfolio_vendor']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Customer</span>
                    <span class="stat-value">{stats['portfolio_customer']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total</span>
                    <span class="stat-value stat-value-highlight">{stats['portfolio_total']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Pipeline (In Progress)
    with cols[1]:
        st.markdown(f"""
            <div class="stat-category">
                <div class="stat-header">
                    <span class="stat-header-icon">🔄</span>
                    <span class="stat-header-title">Pipeline</span>
                </div>
                <div class="stat-header-sub">(In Progress)</div>
                <div class="stat-row">
                    <span class="stat-label">Vendor</span>
                    <span class="stat-value">{stats['pipeline_vendor']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Customer</span>
                    <span class="stat-value">{stats['pipeline_customer']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total</span>
                    <span class="stat-value stat-value-highlight">{stats['pipeline_total']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Timeline (Next 90d)
    with cols[2]:
        expiring_class = "stat-value-alert" if stats['timeline_expiring'] > 0 else "stat-value"
        renewal_class = "stat-value-warning" if stats['timeline_renewal'] > 0 else "stat-value"
        pending_class = "stat-value-warning" if stats['timeline_pending'] > 0 else "stat-value"
        
        st.markdown(f"""
            <div class="stat-category">
                <div class="stat-header">
                    <span class="stat-header-icon">📅</span>
                    <span class="stat-header-title">Timeline</span>
                </div>
                <div class="stat-header-sub">(Next 90d)</div>
                <div class="stat-row">
                    <span class="stat-label">Expiring</span>
                    <span class="stat-value {expiring_class}">{stats['timeline_expiring']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Renewal</span>
                    <span class="stat-value {renewal_class}">{stats['timeline_renewal']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Pending</span>
                    <span class="stat-value {pending_class}">{stats['timeline_pending']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Activity (Past 90d)
    with cols[3]:
        st.markdown(f"""
            <div class="stat-category">
                <div class="stat-header">
                    <span class="stat-header-icon">⚡</span>
                    <span class="stat-header-title">Activity</span>
                </div>
                <div class="stat-header-sub">(Past 90d)</div>
                <div class="stat-row">
                    <span class="stat-label">Analyzed</span>
                    <span class="stat-value">{stats['activity_analyzed']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Negotiating</span>
                    <span class="stat-value">{stats['activity_negotiating']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Feedback</span>
                    <span class="stat-value">{stats['activity_feedback']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


init_page("Home", "🏠", max_width=1400)

page_header(
    "Welcome to CIP",
    subtitle="Contract Intelligence Platform",
    show_status=True,
    show_version=True
)

with content_container():
    # Two animations side by side - REDUCED HEIGHT
    col1, col2 = st.columns(2)
    
    with col1:
        render_workflow_animation(height=320)
    
    with col2:
        render_learning_animation(height=320)
    
    # Quick Stats - Compact layout (NO DIVIDER, NO FOOTER)
    render_quick_stats()
