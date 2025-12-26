"""
Visualization Components Library
Reusable, themed chart components for CIP

Usage:
    from viz_components import create_value_trend, create_risk_donut, create_status_bars
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from theme_system import get_current_theme


def create_value_trend(
    df: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'value',
    title: Optional[str] = None,
    height: int = 350
) -> go.Figure:
    """
    Create line chart with area fill showing value trend over time
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column
        title: Optional chart title
        height: Chart height in pixels
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    fig = go.Figure()
    
    # Area fill
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[value_col],
        mode='lines',
        name='Value',
        line=dict(color=theme['primary'], width=3, shape='spline'),
        fill='tozeroy',
        fillcolor=f"{theme['primary']}20",
        hovertemplate='<b>%{x|%B %Y}</b><br>Value: $%{y:.1f}M<extra></extra>'
    ))
    
    # Data point markers
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[value_col],
        mode='markers',
        name='Points',
        marker=dict(
            size=8,
            color=theme['secondary'],
            line=dict(color=theme['surface'], width=2)
        ),
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary'], size=12),
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor=theme['border'],
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=theme['border'],
            zeroline=False,
            tickformat='$,.0f'
        ),
        hovermode='x unified',
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


def create_risk_donut(
    df: pd.DataFrame,
    risk_col: str = 'risk',
    count_col: str = 'count',
    title: Optional[str] = None,
    height: int = 350
) -> go.Figure:
    """
    Create donut chart showing risk distribution
    
    Args:
        df: DataFrame with risk levels and counts
        risk_col: Name of risk level column
        count_col: Name of count column
        title: Optional chart title
        height: Chart height
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    # Color mapping for risk levels
    colors = {
        'Low': theme['success'],
        'Medium': theme['info'],
        'High': theme['warning'],
        'Critical': theme['error']
    }
    risk_colors = [colors.get(risk, theme['primary']) for risk in df[risk_col]]
    
    fig = go.Figure(data=[go.Pie(
        labels=df[risk_col],
        values=df[count_col],
        hole=0.6,
        marker=dict(
            colors=risk_colors,
            line=dict(color=theme['surface'], width=3)
        ),
        textinfo='label+percent',
        textfont=dict(color=theme['text_primary'], size=13),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
    )])
    
    # Center text
    total = df[count_col].sum()
    fig.add_annotation(
        text=f"<b>{total}</b><br>Total",
        x=0.5, y=0.5,
        font=dict(size=20, color=theme['text_primary']),
        showarrow=False
    )
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary']),
        showlegend=False,
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


def create_status_bars(
    df: pd.DataFrame,
    status_col: str = 'status',
    count_col: str = 'count',
    value_col: str = 'value',
    title: Optional[str] = None,
    height: int = 350
) -> go.Figure:
    """
    Create horizontal bar chart for status breakdown
    
    Args:
        df: DataFrame with status and counts
        status_col: Name of status column
        count_col: Name of count column
        value_col: Optional value column for hover
        title: Optional chart title
        height: Chart height
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    df_sorted = df.sort_values(count_col, ascending=True)
    
    # Color mapping
    status_colors = {
        'Active': theme['success'],
        'Pending': theme['info'],
        'Expiring Soon': theme['warning'],
        'Expired': theme['text_tertiary'],
        'Terminated': theme['error']
    }
    bar_colors = [status_colors.get(status, theme['primary']) for status in df_sorted[status_col]]
    
    fig = go.Figure(go.Bar(
        y=df_sorted[status_col],
        x=df_sorted[count_col],
        orientation='h',
        marker=dict(
            color=bar_colors,
            line=dict(color=theme['surface'], width=1)
        ),
        text=df_sorted[count_col],
        textposition='outside',
        textfont=dict(color=theme['text_primary'], size=13),
        hovertemplate='<b>%{y}</b><br>Count: %{x}<br>Value: $%{customdata:.1f}M<extra></extra>',
        customdata=df_sorted[value_col] if value_col in df_sorted.columns else None
    ))
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary']),
        xaxis=dict(
            showgrid=True,
            gridcolor=theme['border'],
            zeroline=False
        ),
        yaxis=dict(
            showgrid=False
        ),
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


def create_calendar_heatmap(
    df: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'count',
    title: Optional[str] = None,
    height: int = 350
) -> go.Figure:
    """
    Create calendar heat map
    
    Args:
        df: DataFrame with dates and values
        date_col: Name of date column
        value_col: Name of value column
        title: Optional chart title
        height: Chart height
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    df_copy = df.copy()
    df_copy['week'] = pd.to_datetime(df_copy[date_col]).dt.isocalendar().week
    df_copy['weekday'] = pd.to_datetime(df_copy[date_col]).dt.dayofweek
    
    pivot = df_copy.pivot_table(
        values=value_col,
        index='weekday',
        columns='week',
        aggfunc='sum',
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        colorscale=[
            [0, theme['surface']],
            [0.3, theme['info']],
            [0.6, theme['warning']],
            [1, theme['error']]
        ],
        text=pivot.values,
        texttemplate='%{text}',
        textfont=dict(color=theme['text_primary']),
        hovertemplate='<b>Week %{x}</b><br>%{y}<br>Count: %{z}<extra></extra>',
        showscale=False
    ))
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary']),
        xaxis=dict(
            title="Week",
            side='bottom',
            showgrid=False
        ),
        yaxis=dict(
            showgrid=False
        ),
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


def create_ranked_bars(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: Optional[str] = None,
    top_n: int = 10,
    orientation: str = 'h',
    height: int = 350
) -> go.Figure:
    """
    Create ranked bar chart (horizontal or vertical)
    
    Args:
        df: DataFrame with labels and values
        label_col: Name of label column
        value_col: Name of value column
        title: Optional chart title
        top_n: Number of top items to show
        orientation: 'h' for horizontal, 'v' for vertical
        height: Chart height
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    # Get top N
    df_sorted = df.nlargest(top_n, value_col)
    if orientation == 'h':
        df_sorted = df_sorted.sort_values(value_col, ascending=True)
    
    if orientation == 'h':
        fig = go.Figure(go.Bar(
            y=df_sorted[label_col],
            x=df_sorted[value_col],
            orientation='h',
            marker=dict(color=theme['secondary']),
            text=df_sorted[value_col].apply(lambda x: f'${x:.1f}M' if x >= 1 else f'${x*1000:.0f}K'),
            textposition='outside',
            textfont=dict(color=theme['text_primary']),
            hovertemplate='<b>%{y}</b><br>Value: $%{x:.1f}M<extra></extra>'
        ))
    else:
        fig = go.Figure(go.Bar(
            x=df_sorted[label_col],
            y=df_sorted[value_col],
            marker=dict(color=theme['primary']),
            text=df_sorted[value_col],
            textposition='outside',
            textfont=dict(color=theme['text_primary']),
            hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary']),
        xaxis=dict(
            showgrid=True if orientation == 'h' else False,
            gridcolor=theme['border']
        ),
        yaxis=dict(
            showgrid=False if orientation == 'h' else True,
            gridcolor=theme['border']
        ),
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    text_col: Optional[str] = None,
    title: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Create scatter plot with optional color and size encoding
    
    Args:
        df: DataFrame with data
        x_col: Name of x-axis column
        y_col: Name of y-axis column
        color_col: Optional column for color encoding
        size_col: Optional column for size encoding
        text_col: Optional column for labels
        title: Optional chart title
        height: Chart height
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    marker_config = dict(
        size=12 if not size_col else df[size_col] * 2,
        color=theme['primary'] if not color_col else df[color_col],
        line=dict(color=theme['surface'], width=2),
        opacity=0.7
    )
    
    if color_col:
        marker_config['colorscale'] = [
            [0, theme['info']],
            [0.5, theme['primary']],
            [1, theme['secondary']]
        ]
        marker_config['showscale'] = True
    
    fig = go.Figure(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='markers' if not text_col else 'markers+text',
        marker=marker_config,
        text=df[text_col] if text_col else None,
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>' if text_col else None
    ))
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary']),
        xaxis=dict(
            showgrid=True,
            gridcolor=theme['border']
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=theme['border']
        ),
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


def create_dual_axis_chart(
    df: pd.DataFrame,
    x_col: str,
    y1_col: str,
    y2_col: str,
    y1_name: str = 'Value',
    y2_name: str = 'Count',
    title: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Create chart with two y-axes (bars + line)
    
    Args:
        df: DataFrame with data
        x_col: Name of x-axis column
        y1_col: Name of first y-axis column (bars)
        y2_col: Name of second y-axis column (line)
        y1_name: Label for first y-axis
        y2_name: Label for second y-axis
        title: Optional chart title
        height: Chart height
    
    Returns:
        Plotly Figure object
    """
    theme = get_current_theme()
    
    fig = go.Figure()
    
    # Bars
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[y1_col],
        name=y1_name,
        marker=dict(color=theme['primary']),
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>' + y1_name + ': %{y}<extra></extra>'
    ))
    
    # Line
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y2_col],
        name=y2_name,
        mode='lines+markers',
        line=dict(color=theme['secondary'], width=3),
        marker=dict(size=8, color=theme['accent']),
        yaxis='y2',
        hovertemplate='<b>%{x}</b><br>' + y2_name + ': %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        plot_bgcolor=theme['surface'],
        paper_bgcolor=theme['surface'],
        font=dict(color=theme['text_primary']),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor=theme['border'],
            title=y1_name
        ),
        yaxis2=dict(
            showgrid=False,
            title=y2_name,
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        height=height
    )
    
    return fig


# Example usage and testing
if __name__ == "__main__":
    import streamlit as st
    from datetime import datetime, timedelta
    
    st.title("Visualization Components Demo")
    
    # Sample data
    dates = pd.date_range(start='2024-01-01', periods=12, freq='MS')
    values = [35 + i + np.random.normal(0, 1) for i in range(12)]
    
    df_trend = pd.DataFrame({'date': dates, 'value': values})
    
    st.plotly_chart(create_value_trend(df_trend), use_container_width=True)
