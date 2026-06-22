import plotly.graph_objects as go
import pandas as pd


def draw_radar_chart(metric_cols: list, player_vals: list,
                     team_vals: list, player_name: str) -> go.Figure:
    categories    = metric_cols + [metric_cols[0]]
    player_closed = player_vals + [player_vals[0]]
    team_closed   = team_vals   + [team_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=team_closed, theta=categories, fill="toself",
        name="TEAM AVG",
        line=dict(color="#1e3a5f", width=1),
        fillcolor="rgba(30,58,95,0.4)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=player_closed, theta=categories, fill="toself",
        name=player_name,
        line=dict(color="#4da3ff", width=2),
        fillcolor="rgba(77,163,255,0.15)"
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0a0e1a",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#1e2d4a", linecolor="#1e2d4a",
                tickfont=dict(color="#2a4a6a", size=9),
                tickvals=[25, 50, 75, 100]
            ),
            angularaxis=dict(
                gridcolor="#1e2d4a", linecolor="#1e2d4a",
                tickfont=dict(color="#7a9cc0", size=11,
                              family="Noto Sans JP")
            )
        ),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        font=dict(color="#e0e6f0", family="Rajdhani"),
        legend=dict(bgcolor="#0d1626", bordercolor="#1e2d4a",
                    borderwidth=1, font=dict(size=11)),
        height=460,
        margin=dict(t=30, b=30)
    )
    return fig