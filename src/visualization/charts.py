"""Visualization functions using Plotly."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict

# ── Required intentional colors ───────────────────────────────────────────────
_HOME_WIN = "#37003C"  # original pl dark purple
_AWAY_WIN = "#D85A30"  # muted red/coral
_DRAW     = "#888780"  # gray

# All charts use default plotly_white template except for these specific color mappings
_LAYOUT = dict(template="plotly_white")

def create_team_performance_chart(team_stats: Dict, team_name: str) -> go.Figure:
    """Bar chart – Wins / Draws / Losses for a team."""
    categories = ['Wins', 'Draws', 'Losses']
    values = [
        team_stats.get('wins', 0),
        team_stats.get('draws', 0),
        team_stats.get('losses', 0)
    ]
    colors = [_HOME_WIN, _DRAW, _AWAY_WIN]

    fig = go.Figure(data=[
        go.Bar(
            x=categories, y=values,
            marker_color=colors,
            text=values, textposition='auto',
            insidetextfont=dict(color='white')
        )
    ])
    fig.update_layout(
        title=f"{team_name} Match Results",
        height=350,
        **_LAYOUT
    )
    return fig


def create_form_chart(form: List[str], team_name: str) -> go.Figure:
    """Bar chart showing recent form (W/D/L) with fixed-height bars coloured by result."""
    colors_map = {'W': _HOME_WIN, 'D': _DRAW, 'L': _AWAY_WIN}
    colors = [colors_map.get(r, '#9ca3af') for r in form]

    # Fixed height of 1 for every bar so Losses are visible.
    # Colour conveys the result — green=W, grey=D, red=L.
    heights = [1] * len(form)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"M{i+1}" for i in range(len(form))],
        y=heights,
        marker_color=colors,
        text=form,
        textposition='inside',
        insidetextfont=dict(color='white', size=14),
    ))
    fig.update_layout(
        title=f"{team_name} Recent Form",
        yaxis=dict(visible=False, range=[0, 1.5]),
        xaxis=dict(title="Match"),
        height=220,
        **_LAYOUT
    )
    return fig


def create_comparison_radar(
    team1_stats: Dict, team2_stats: Dict,
    team1_name: str, team2_name: str
) -> go.Figure:
    """Radar chart comparing two teams across key metrics."""
    categories = ['Win Rate', 'Attack', 'Defence', 'Pts/Game']

    def _vals(s):
        return [
            s.get('win_rate', 0) * 100,
            min(s.get('avg_goals_scored', 0) * 20, 100),
            max(0, 100 - s.get('avg_goals_conceded', 0) * 20),
            s.get('points', 0) / max(s.get('total_matches', 1), 1) * 33.33,
        ]

    v1, v2 = _vals(team1_stats), _vals(team2_stats)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=v1 + [v1[0]], theta=categories + [categories[0]],
        fill='toself', name=team1_name,
        line=dict(color=_HOME_WIN)
    ))
    fig.add_trace(go.Scatterpolar(
        r=v2 + [v2[0]], theta=categories + [categories[0]],
        fill='toself', name=team2_name,
        line=dict(color=_AWAY_WIN)
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        title="Team Comparison",
        showlegend=True, height=400,
        **_LAYOUT
    )
    return fig


def create_prediction_gauge(prediction: Dict, team1_name: str, team2_name: str) -> go.Figure:
    """Three gauge indicators for Home Win / Draw / Away Win probabilities."""
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'indicator'}] * 3],
        subplot_titles=(team1_name, "Draw", team2_name)
    )

    gauges = [
        (prediction['home_win_prob'] * 100, _HOME_WIN, 1),
        (prediction['draw_prob'] * 100,     _DRAW,     2),
        (prediction['away_win_prob'] * 100, _AWAY_WIN, 3),
    ]
    for val, bar_color, col in gauges:
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=val,
            number={'suffix': '%'},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': bar_color},
            }
        ), row=1, col=col)

    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=50, b=10),
        **_LAYOUT
    )
    return fig
