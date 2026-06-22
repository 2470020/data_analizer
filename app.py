import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import numpy as np
from modules.data_loader import (load_excel, get_column_names,
                                  guess_name_column, get_player_list,
                                  get_metric_columns, create_sample_excel,
                                  clean_dataframe)
from modules.analysis import (calc_team_stats, get_player_data,
                               normalize_for_radar)
from modules.advisor import generate_advice

# ── ページ設定 ──────────────────────────────────────
st.set_page_config(
    page_title="ATHLETE ANALYSIS SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── グローバルCSS ───────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

.stApp { background-color: #0a0e1a; color: #e0e6f0; }
[data-testid="stSidebar"] {
    background-color: #0d1220;
    border-right: 1px solid #1e2d4a;
}
.stButton > button, .stDownloadButton > button {
    background: transparent;
    border: 1px solid #1a6fc4;
    color: #4da3ff;
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 0.08em;
    transition: all 0.2s;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: #1a6fc422;
    border-color: #4da3ff;
}
hr { border-color: #1e2d4a; }
.param-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2px;
    background: #1e2d4a;
    border: 2px solid #1e2d4a;
    margin-bottom: 16px;
}
.param-cell {
    background: #0d1626;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.param-label {
    font-family: 'Noto Sans JP', sans-serif;
    font-size: 11px;
    color: #7a9cc0;
    letter-spacing: 0.05em;
}
.param-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 22px;
    font-weight: 700;
}
.param-value.high { color: #4da3ff; }
.param-value.mid  { color: #e0e6f0; }
.param-value.low  { color: #5a7a9a; }
.param-value.none { color: #3a4a5a; }
.rank-badge {
    display: inline-block;
    font-family: 'Rajdhani', sans-serif;
    font-size: 13px;
    font-weight: 700;
    padding: 2px 10px;
    border: 1px solid;
    letter-spacing: 0.1em;
}
.rank-S { color: #ffd700; border-color: #ffd700; }
.rank-A { color: #4da3ff; border-color: #4da3ff; }
.rank-B { color: #a0c4e8; border-color: #a0c4e8; }
.rank-C { color: #7a9cc0; border-color: #7a9cc0; }
.rank-D { color: #5a7a9a; border-color: #5a7a9a; }
.rank-N { color: #3a4a5a; border-color: #3a4a5a; }
.section-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: #4da3ff;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 4px;
    margin: 20px 0 12px;
}
.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: #ffffff;
    line-height: 1.1;
}
.hero-sub {
    font-family: 'Rajdhani', sans-serif;
    font-size: 13px;
    letter-spacing: 0.3em;
    color: #4da3ff;
    margin-bottom: 32px;
}
.stat-box {
    border: 1px solid #1e3a5f;
    background: #0d1626;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.stat-box-label {
    font-size: 10px;
    letter-spacing: 0.2em;
    color: #4da3ff;
    font-family: 'Rajdhani', sans-serif;
    text-transform: uppercase;
}
.stat-box-value {
    font-size: 28px;
    font-weight: 700;
    font-family: 'Rajdhani', sans-serif;
    color: #ffffff;
}
.null-warning {
    background: #1a1a2e;
    border-left: 3px solid #1a6fc4;
    padding: 8px 14px;
    font-family: 'Noto Sans JP', sans-serif;
    font-size: 12px;
    color: #7a9cc0;
    margin-bottom: 12px;
}
.progress-info {
    font-family: 'Rajdhani', sans-serif;
    font-size: 12px;
    color: #4da3ff;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── サイドバー ──────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">DATA INPUT</div>',
                unsafe_allow_html=True)
    st.download_button(
        label="SAMPLE DATA DOWNLOAD",
        data=create_sample_excel(),
        file_name="sample_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("""
    <div style="font-family:'Noto Sans JP',sans-serif; font-size:11px;
                color:#5a7a9a; margin:8px 0 4px; line-height:1.8;">
        大きいファイルは自動で分割して<br>読み込みます（xlsx / csv対応）
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "UPLOAD FILE（xlsx / csv）",
        type=["xlsx", "csv"],
        accept_multiple_files=True
    )

    # ── 列名候補をファイルから動的生成 ────────────
    name_col = "選手名"

    if uploaded_files:
        try:
            all_columns = get_column_names(uploaded_files[0])
            default_col = guess_name_column(all_columns)
            default_idx = all_columns.index(default_col)

            st.markdown(
                '<div class="section-header">PLAYER ID COLUMN</div>',
                unsafe_allow_html=True)
            name_col = st.selectbox(
                "選手を識別する列を選択",
                options=all_columns,
                index=default_idx
            )
        except Exception:
            name_col = st.text_input("選手名の列名", value="選手名")

        st.markdown('<div class="section-header">LOADED FILES</div>',
                    unsafe_allow_html=True)
        for i, f in enumerate(uploaded_files):
            size_kb = round(f.size / 1024, 1)
            st.markdown(f"""
            <div style="font-family:'Rajdhani',sans-serif; font-size:12px;
                        color:#7a9cc0; padding:3px 0;
                        border-bottom:1px solid #1e2d4a;">
                <span style="color:#4da3ff;">{i+1}/{len(uploaded_files)}</span>
                　{f.name}<br>
                <span style="font-size:10px; color:#3a5a7a;">{size_kb} KB</span>
            </div>""", unsafe_allow_html=True)
    else:
        name_col = st.text_input("選手名の列名", value="選手名")

# ── タイトル画面 ────────────────────────────────────
if not uploaded_files:
    st.markdown("""
    <div style="padding: 60px 0 40px;">
        <div class="hero-sub">SPORTS PERFORMANCE ANALYTICS</div>
        <div class="hero-title">ATHLETE<br>ANALYSIS<br>SYSTEM</div>
        <div style="width:60px; height:3px; background:#1a6fc4; margin:24px 0;"></div>
        <div style="font-family:'Noto Sans JP',sans-serif; font-size:13px;
                    color:#5a7a9a; line-height:2;">
            IoTデバイスから出力された体力測定データを解析し、<br>
            選手個別のパフォーマンスプロファイルを生成します。
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-box-label">FUNCTION 01</div>
            <div class="stat-box-value">DATA<br>IMPORT</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-box-label">FUNCTION 02</div>
            <div class="stat-box-value">SKILL<br>ANALYSIS</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-box-label">FUNCTION 03</div>
            <div class="stat-box-value">PLAYER<br>REPORT</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:48px; font-family:'Rajdhani',sans-serif;
                font-size:12px; color:#2a4a6a; letter-spacing:0.2em;">
        LOAD EXCEL FILE TO BEGIN ANALYSIS
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── データ読み込み ──────────────────────────────────
dfs    = []
errors = []
total  = len(uploaded_files)

progress = st.progress(0, text="ファイルを読み込んでいます...")

for i, f in enumerate(uploaded_files):
    try:
        df_part = load_excel(f)
        dfs.append(df_part)
        progress.progress(
            (i + 1) / total,
            text=f"読み込み中... {i+1}/{total}　{f.name}"
        )
    except Exception as e:
        errors.append(f"{f.name}：{e}")

progress.empty()

if errors:
    for err in errors:
        st.error(f"読み込み失敗 — {err}")

if not dfs:
    st.error("有効なファイルがありません。")
    st.stop()

df = pd.concat(dfs, ignore_index=True)

st.markdown(f"""
<div class="progress-info">
    FILES LOADED : {total} &nbsp;|&nbsp; TOTAL PLAYERS : {len(df)}
</div>
""", unsafe_allow_html=True)

all_metric_cols = get_metric_columns(df, name_col)

if name_col not in df.columns:
    st.error(f"列「{name_col}」が見つかりません。サイドバーで列を確認してください。")
    st.stop()

# 重複チェック
duplicates = df[df.duplicated(subset=[name_col], keep=False)][name_col].unique()
if len(duplicates) > 0:
    dup_names = ", ".join([str(d) for d in duplicates])
    st.markdown(f"""
    <div class="null-warning">
        <strong>DUPLICATE DETECTED</strong> —
        同じIDが複数存在します：{dup_names}<br>
        <span style="font-size:11px;">最初のデータを優先します。</span>
    </div>""", unsafe_allow_html=True)
    df = df.drop_duplicates(subset=[name_col], keep="first")

# クリーニング
df, outlier_report = clean_dataframe(df, all_metric_cols, name_col=name_col)

if outlier_report:
    warn_lines = "".join(
        f"<div>・ {col}：{', '.join([str(p) for p in players])}</div>"
        for col, players in outlier_report.items()
    )
    st.markdown(f"""
    <div class="null-warning">
        <strong>OUTLIER DETECTED</strong> — 外れ値（±3σ）を除外しました<br>
        {warn_lines}
    </div>""", unsafe_allow_html=True)

# ── 分析設定 ────────────────────────────────────────
st.markdown('<div class="section-header">ANALYSIS SETUP</div>',
            unsafe_allow_html=True)

col_s, col_m = st.columns([1, 2])
with col_s:
    player_list     = get_player_list(df, name_col)
    selected_player = st.selectbox("SELECT PLAYER", player_list)
with col_m:
    selected_metrics = st.multiselect(
        "SELECT PARAMETERS",
        options=all_metric_cols,
        default=all_metric_cols
    )

if not selected_metrics:
    st.warning("測定項目を1つ以上選択してください。")
    st.stop()

# ── 統計計算 ────────────────────────────────────────
team_stats  = calc_team_stats(df, selected_metrics)
player_data = get_player_data(df, selected_player, name_col)
advice_list = generate_advice(player_data, team_stats, selected_metrics)

# ── ランク変換 ──────────────────────────────────────
def z_to_rank(z) -> str:
    if z is None: return "N"
    if z >= 1.5:  return "S"
    if z >= 0.5:  return "A"
    if z >= -0.5: return "B"
    if z >= -1.5: return "C"
    return "D"

def z_to_class(z) -> str:
    if z is None: return "none"
    if z >= 0.5:  return "high"
    if z >= -0.5: return "mid"
    return "low"

# ── 選手ヘッダー ────────────────────────────────────
st.markdown(f"""
<div style="border-top:2px solid #1a6fc4; border-bottom:1px solid #1e2d4a;
            padding:16px 0; margin:24px 0 8px;">
    <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                color:#4da3ff; letter-spacing:0.3em;">PLAYER PROFILE</div>
    <div style="font-family:'Rajdhani',sans-serif; font-size:32px;
                font-weight:700; color:#fff; letter-spacing:0.1em;">
        {str(selected_player).upper()}
    </div>
</div>
""", unsafe_allow_html=True)

# ── パラメーターグリッド ────────────────────────────
st.markdown('<div class="section-header">SKILL PARAMETER SUMMARY</div>',
            unsafe_allow_html=True)

cells_html = ""
for item in advice_list:
    col_name = item["指標"]
    val      = item["選手値"]
    is_null  = val == "-"
    std_val  = float(team_stats.loc[col_name, "標準偏差"])
    mean_val = float(team_stats.loc[col_name, "チーム平均"])
    z        = None if is_null else (
                   (float(val) - mean_val) / std_val if std_val > 0 else 0.0)
    rank     = z_to_rank(z)
    cls      = z_to_class(z)

    cells_html += f"""
    <div class="param-cell">
        <span class="param-label">{col_name}</span>
        <div style="display:flex;align-items:center;gap:8px;">
            <span class="param-value {cls}">{val}</span>
            <span class="rank-badge rank-{rank}">{rank}</span>
        </div>
    </div>"""

st.markdown(f'<div class="param-grid">{cells_html}</div>',
            unsafe_allow_html=True)

# ── レーダーチャート ────────────────────────────────
st.markdown('<div class="section-header">RADAR CHART</div>',
            unsafe_allow_html=True)

player_norm, team_norm = normalize_for_radar(
    player_data, team_stats, selected_metrics)
categories = selected_metrics + [selected_metrics[0]]
p_vals     = player_norm + [player_norm[0]]
t_vals     = team_norm   + [team_norm[0]]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=t_vals, theta=categories, fill="toself",
    name="TEAM AVG",
    line=dict(color="#1e3a5f", width=1),
    fillcolor="rgba(30,58,95,0.4)"
))
fig.add_trace(go.Scatterpolar(
    r=p_vals, theta=categories, fill="toself",
    name=str(selected_player).upper(),
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
st.plotly_chart(fig, use_container_width=True)

# ── 分析レポート ────────────────────────────────────
st.markdown('<div class="section-header">ANALYSIS REPORT</div>',
            unsafe_allow_html=True)

for item in advice_list:
    col_name = item["指標"]
    val      = item["選手値"]
    is_null  = val == "-"
    std_val  = float(team_stats.loc[col_name, "標準偏差"])
    mean_val = float(team_stats.loc[col_name, "チーム平均"])
    z        = None if is_null else (
                   (float(val) - mean_val) / std_val if std_val > 0 else 0.0)
    rank     = z_to_rank(z)

    r1, r2, r3 = st.columns([2, 1, 4])
    with r1:
        st.markdown(f"""
        <div style="font-family:'Noto Sans JP',sans-serif;
                    font-size:12px; color:#7a9cc0; padding:6px 0;">
            {col_name}
        </div>""", unsafe_allow_html=True)
    with r2:
        st.markdown(
            f'<div style="padding:4px 0;">'
            f'<span class="rank-badge rank-{rank}">{rank}</span></div>',
            unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
        <div style="font-family:'Noto Sans JP',sans-serif;
                    font-size:12px; color:#5a7a9a; padding:6px 0;">
            {item["コメント"]}
        </div>""", unsafe_allow_html=True)

# ── エクスポート ────────────────────────────────────
st.markdown('<div class="section-header">EXPORT</div>',
            unsafe_allow_html=True)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):  return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray):  return obj.tolist()
        return super().default(obj)

export_data = {
    "player":  str(selected_player),
    "metrics": selected_metrics,
    "values": {
        col: "-" if pd.isna(player_data[col])
             else float(player_data[col])
        for col in selected_metrics
    },
    "team_stats": {
        col: {"mean": float(team_stats.loc[col, "チーム平均"]),
              "std":  float(team_stats.loc[col, "標準偏差"])}
        for col in selected_metrics
    },
    "advice": advice_list
}

ec1, ec2 = st.columns(2)
with ec1:
    st.download_button(
        "EXPORT JSON",
        data=json.dumps(export_data, ensure_ascii=False,
                        indent=2, cls=NumpyEncoder),
        file_name=f"{selected_player}_analysis.json",
        mime="application/json"
    )
with ec2:
    advice_df = pd.DataFrame(advice_list)
    st.download_button(
        "EXPORT CSV",
        data=advice_df.to_csv(index=False, encoding="utf-8-sig"),
        file_name=f"{selected_player}_analysis.csv",
        mime="text/csv"
    )