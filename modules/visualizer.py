import plotly.graph_objects as go
import pandas as pd

def draw_radar_chart(metric_cols: list, player_vals: list,
                     team_vals: list, player_name: str) -> go.Figure:
    """レーダーチャートを生成"""
    categories = metric_cols + [metric_cols[0]]  # 閉じるために先頭を末尾に追加
    player_vals_closed = player_vals + [player_vals[0]]
    team_vals_closed = team_vals + [team_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=team_vals_closed, theta=categories,
        fill="toself", name="チーム平均",
        line=dict(color="rgba(100,100,255,0.6)"),
        fillcolor="rgba(100,100,255,0.15)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=player_vals_closed, theta=categories,
        fill="toself", name=player_name,
        line=dict(color="rgba(255,80,80,0.9)"),
        fillcolor="rgba(255,80,80,0.25)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title=f"{player_name} vs チーム平均",
        height=450
    )
    return fig

def draw_bar_comparison(player_data: pd.Series, team_stats: pd.DataFrame,
                         metric_cols: list, player_name: str) -> go.Figure:
    """棒グラフで実数値比較"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="チーム平均", x=metric_cols,
        y=team_stats.loc[metric_cols, "チーム平均"].values,
        marker_color="royalblue", opacity=0.7
    ))
    fig.add_trace(go.Bar(
        name=player_name, x=metric_cols,
        y=[player_data[col] for col in metric_cols],
        marker_color="tomato", opacity=0.85
    ))
    fig.update_layout(
        barmode="group", title="実測値比較（選手 vs チーム平均）",
        height=380, xaxis_tickangle=-30
    )
    return fig