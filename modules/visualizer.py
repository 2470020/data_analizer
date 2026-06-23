import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ============================================================
# カテゴリ定義
# ============================================================
CHART_CATEGORIES = {
    "🦘 ジャンプ・プライオメトリクス系": [
        "CMJ", "DJ-跳躍高", "DJ-RSI", "DJ-接地時間",
    ],
    "⚡ スプリント・パワー系": [
        "10m走", "20m走", "HG合計", "HG右", "HG左",
    ],
}

CATEGORY_COLORS = {
    "🦘 ジャンプ・プライオメトリクス系": {
        "player":     "#00e5ff",
        "player_fill": "rgba(0,229,255,0.15)",
        "team":       "#ff6b35",
        "team_fill":  "rgba(255,107,53,0.35)",
    },
    "⚡ スプリント・パワー系": {
        "player":     "#ffe600",
        "player_fill": "rgba(255,230,0,0.15)",
        "team":       "#ff3a6e",
        "team_fill":  "rgba(255,58,110,0.35)",
    },
}

_BG = "#0a0e1a"
_GRID = "#1e2d4a"


def _resolve_cols(metric_cols: list, category_keys: list) -> list:
    """カテゴリキーワードに部分一致する列を metric_cols から取得する"""
    result = []
    for key in category_keys:
        for col in metric_cols:
            if key.lower() in col.lower() and col not in result:
                result.append(col)
    return result


def draw_category_radar_charts(
    metric_cols: list,
    player_vals_map: dict,   # {col: normalized_val}
    team_vals_map: dict,     # {col: 50.0}
    player_name: str,
) -> dict:
    """
    カテゴリごとのレーダーチャートを辞書で返す。
    該当列が 0 本のカテゴリは None を返す。
    """
    figs = {}
    for cat_name, cat_keys in CHART_CATEGORIES.items():
        cols = _resolve_cols(metric_cols, cat_keys)
        if not cols:
            figs[cat_name] = None
            continue

        p_vals = [player_vals_map.get(c, 50) for c in cols]
        t_vals = [team_vals_map.get(c, 50)   for c in cols]
        colors  = CATEGORY_COLORS[cat_name]

        cats_closed  = cols + [cols[0]]
        p_closed     = p_vals + [p_vals[0]]
        t_closed     = t_vals + [t_vals[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=t_closed, theta=cats_closed, fill="toself",
            name="TEAM AVG",
            line=dict(color=colors["team"], width=1.5, dash="dot"),
            fillcolor=colors["team_fill"],
        ))
        fig.add_trace(go.Scatterpolar(
            r=p_closed, theta=cats_closed, fill="toself",
            name=player_name,
            line=dict(color=colors["player"], width=2.5),
            fillcolor=colors["player_fill"],
        ))
        fig.update_layout(
            title=dict(text=cat_name, font=dict(color="#e0e6f0", size=14), x=0.5),
            polar=dict(
                bgcolor=_BG,
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    gridcolor=_GRID, linecolor=_GRID,
                    tickfont=dict(color="#2a4a6a", size=9),
                    tickvals=[25, 50, 75, 100],
                ),
                angularaxis=dict(
                    gridcolor=_GRID, linecolor=_GRID,
                    tickfont=dict(color="#7a9cc0", size=11,
                                  family="Noto Sans JP"),
                ),
            ),
            paper_bgcolor=_BG,
            plot_bgcolor=_BG,
            font=dict(color="#e0e6f0", family="Rajdhani"),
            legend=dict(bgcolor="#0d1626", bordercolor=_GRID,
                        borderwidth=1, font=dict(size=11)),
            height=420,
            margin=dict(t=50, b=30, l=30, r=30),
        )
        figs[cat_name] = fig

    return figs


# 後方互換用（従来の単一レーダー）
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
            bgcolor=_BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=_GRID, linecolor=_GRID,
                tickfont=dict(color="#2a4a6a", size=9),
                tickvals=[25, 50, 75, 100]
            ),
            angularaxis=dict(
                gridcolor=_GRID, linecolor=_GRID,
                tickfont=dict(color="#7a9cc0", size=11,
                              family="Noto Sans JP")
            )
        ),
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=dict(color="#e0e6f0", family="Rajdhani"),
        legend=dict(bgcolor="#0d1626", bordercolor=_GRID,
                    borderwidth=1, font=dict(size=11)),
        height=460,
        margin=dict(t=30, b=30)
    )
    return fig