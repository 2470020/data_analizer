import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np
from modules.data_loader import (load_excel, get_column_names,
                                  guess_name_column, get_player_list,
                                  get_metric_columns, create_sample_excel,
                                  clean_dataframe, clean_name_column)
from modules.analysis import (calc_team_stats, get_player_data,
                               normalize_for_radar, group_metrics_by_unit,
                               calc_z_scores)
from modules.advisor import generate_advice
from modules.training_generator import (generate_daily_training,
                                         generate_weekly_plan)
from modules.rival_finder import find_rival, compare_with_rival
from modules.advisor_report import generate_coach_report
from modules.pdf_exporter import generate_player_pdf
from modules.calendar_integration import (is_calendar_connected,
                                           push_training_to_calendar,
                                           push_weekly_plan_to_calendar)

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
.cal-guide-box {
    background: linear-gradient(135deg, #0d1626 0%, #0a1a2e 100%);
    border: 1px solid #1e3a5f;
    border-left: 4px solid #1a6fc4;
    padding: 20px 24px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)


# ── キャッシュ関数 ──────────────────────────────────
@st.cache_data(show_spinner=False)
def cached_load_excel(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    """同じファイルは再読み込みしない（キャッシュ）"""
    import io as _io
    class _FakeBuf:
        def __init__(self, b, n):
            self._buf  = _io.BytesIO(b)
            self.name  = n
            self.size  = len(b)
        def read(self, *a):   return self._buf.read(*a)
        def seek(self, *a):   return self._buf.seek(*a)
        def tell(self, *a):   return self._buf.tell(*a)
    return load_excel(_FakeBuf(file_bytes, file_name))


@st.cache_data(show_spinner=False)
def cached_team_stats(df_json: str, metric_cols_key: str) -> pd.DataFrame:
    """チーム統計もキャッシュ"""
    df   = pd.read_json(df_json)
    cols = metric_cols_key.split("|||")
    return calc_team_stats(df, cols)


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
            <div class="stat-box-value">COACH<br>REPORT</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:48px; font-family:'Rajdhani',sans-serif;
                font-size:12px; color:#2a4a6a; letter-spacing:0.2em;">
        LOAD EXCEL FILE TO BEGIN ANALYSIS
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── データ読み込み（キャッシュ対応） ────────────────
dfs    = []
errors = []
total  = len(uploaded_files)

progress = st.progress(0, text="ファイルを読み込んでいます...")

for i, f in enumerate(uploaded_files):
    try:
        file_bytes = f.read()
        f.seek(0)
        df_part    = cached_load_excel(file_bytes, f.name)
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

if name_col not in df.columns:
    st.error(f"列「{name_col}」が見つかりません。")
    st.stop()

# ── 表記ゆれクレンジング ────────────────────────────
df = clean_name_column(df, name_col)

all_metric_cols = get_metric_columns(df, name_col)

if not all_metric_cols:
    st.error("分析できる数値列が見つかりません。")
    st.stop()

st.markdown(f"""
<div class="progress-info">
    FILES LOADED : {total} &nbsp;|&nbsp; TOTAL PLAYERS : {len(df)}
    &nbsp;|&nbsp; PARAMETERS : {len(all_metric_cols)}
</div>
""", unsafe_allow_html=True)

# 重複チェック
non_null_df = df[df[name_col].notna()]
duplicates  = non_null_df[
    non_null_df.duplicated(subset=[name_col], keep=False)
][name_col].unique()

if len(duplicates) > 0:
    dup_names = ", ".join([str(d) for d in duplicates])
    st.markdown(f"""
    <div class="null-warning">
        <strong>DUPLICATE DETECTED</strong> —
        同じIDが複数存在します：{dup_names}<br>
        <span style="font-size:11px;">最初のデータを優先します。</span>
    </div>""", unsafe_allow_html=True)
    df = df.drop_duplicates(subset=[name_col], keep="first")

df = df[df[name_col].notna()].reset_index(drop=True)

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

# ── データ存在チェック ──────────────────────────────
if player_data is None:
    st.warning(f"「{selected_player}」のデータが見つかりません。"
               f"名前の表記を確認してください。")
    st.stop()

advice_list = generate_advice(player_data, team_stats, selected_metrics)

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

# ── レーダーチャート（単位別） ──────────────────────
st.markdown('<div class="section-header">RADAR CHART（単位別）</div>',
            unsafe_allow_html=True)

metric_groups = group_metrics_by_unit(selected_metrics)
group_items   = list(metric_groups.items())

for row_start in range(0, len(group_items), 2):
    row_groups = group_items[row_start:row_start + 2]
    cols       = st.columns(len(row_groups))

    for col_widget, (unit, cols_in_group) in zip(cols, row_groups):
        with col_widget:
            st.markdown(f"""
            <div style="font-family:'Rajdhani',sans-serif; font-size:12px;
                        color:#4da3ff; letter-spacing:0.1em; margin-bottom:4px;">
                UNIT : {unit}
            </div>""", unsafe_allow_html=True)

            if len(cols_in_group) < 2:
                val      = player_data[cols_in_group[0]]
                mean_val = float(team_stats.loc[cols_in_group[0], "チーム平均"])
                st.markdown(f"""
                <div class="param-cell">
                    <span class="param-label">{cols_in_group[0]}</span>
                    <span class="param-value mid">
                        {val if not pd.isna(val) else '-'}
                        （平均:{round(mean_val,1)}）
                    </span>
                </div>""", unsafe_allow_html=True)
                continue

            group_player_norm, group_team_norm = normalize_for_radar(
                player_data, team_stats, cols_in_group)
            categories = cols_in_group + [cols_in_group[0]]
            p_vals     = group_player_norm + [group_player_norm[0]]
            t_vals     = group_team_norm   + [group_team_norm[0]]

            gfig = go.Figure()
            gfig.add_trace(go.Scatterpolar(
                r=t_vals, theta=categories, fill="toself",
                name="TEAM AVG",
                line=dict(color="#1e3a5f", width=1),
                fillcolor="rgba(30,58,95,0.4)"
            ))
            gfig.add_trace(go.Scatterpolar(
                r=p_vals, theta=categories, fill="toself",
                name=str(selected_player).upper(),
                line=dict(color="#4da3ff", width=2),
                fillcolor="rgba(77,163,255,0.15)"
            ))
            gfig.update_layout(
                polar=dict(
                    bgcolor="#0a0e1a",
                    radialaxis=dict(
                        visible=True, range=[0, 100],
                        gridcolor="#1e2d4a", linecolor="#1e2d4a",
                        tickfont=dict(color="#2a4a6a", size=8),
                        tickvals=[25, 50, 75, 100]
                    ),
                    angularaxis=dict(
                        gridcolor="#1e2d4a", linecolor="#1e2d4a",
                        tickfont=dict(color="#7a9cc0", size=10,
                                      family="Noto Sans JP")
                    )
                ),
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a",
                font=dict(color="#e0e6f0", family="Rajdhani"),
                legend=dict(bgcolor="#0d1626", bordercolor="#1e2d4a",
                            borderwidth=1, font=dict(size=9)),
                height=320,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(gfig, use_container_width=True)

# ── 分析レポート（選択状態キープ） ─────────────────
st.markdown('<div class="section-header">ANALYSIS REPORT</div>',
            unsafe_allow_html=True)

# セッション状態で選択を保持
if "selected_advice_metric" not in st.session_state:
    st.session_state.selected_advice_metric = "全て表示"

filter_options = ["全て表示", "優秀", "平均以上", "要強化", "重点課題"]
selected_filter = st.radio(
    "表示フィルター",
    filter_options,
    index=filter_options.index(st.session_state.selected_advice_metric),
    horizontal=True,
    label_visibility="collapsed"
)
st.session_state.selected_advice_metric = selected_filter

report_html = ""
for item in advice_list:
    if selected_filter != "全て表示" and item["判定"] != selected_filter:
        continue
    col_name = item["指標"]
    val      = item["選手値"]
    is_null  = val == "-"
    std_val  = float(team_stats.loc[col_name, "標準偏差"])
    mean_val = float(team_stats.loc[col_name, "チーム平均"])
    z        = None if is_null else (
                   (float(val) - mean_val) / std_val if std_val > 0 else 0.0)
    rank     = z_to_rank(z)

    report_html += f"""
    <div style="display:grid; grid-template-columns:2fr 1fr 4fr;
                gap:4px; border-bottom:1px solid #1e2d4a; padding:4px 0;">
        <div style="font-family:'Noto Sans JP',sans-serif;
                    font-size:12px; color:#7a9cc0; padding:6px 0;">
            {col_name}
        </div>
        <div style="padding:4px 0;">
            <span class="rank-badge rank-{rank}">{rank}</span>
        </div>
        <div style="font-family:'Noto Sans JP',sans-serif;
                    font-size:12px; color:#5a7a9a; padding:6px 0;">
            {item["コメント"]}
        </div>
    </div>"""

if report_html:
    st.markdown(report_html, unsafe_allow_html=True)
else:
    st.info("該当する項目がありません。")

# ── トレーニングメニュー ────────────────────────────
st.markdown('<div class="section-header">TRAINING MENU</div>',
            unsafe_allow_html=True)

tab_daily, tab_weekly = st.tabs(["DAILY", "WEEKLY"])

with tab_daily:
    daily_training = generate_daily_training(advice_list)
    st.markdown(f"""
    <div style="font-family:'Rajdhani',sans-serif; font-size:13px;
                color:#4da3ff; letter-spacing:0.1em; margin-bottom:8px;">
        {daily_training['date']} &nbsp;|&nbsp;
        TOTAL : {daily_training['total_duration']} MIN
    </div>
    <div style="font-family:'Noto Sans JP',sans-serif; font-size:12px;
                color:#7a9cc0; margin-bottom:16px;">
        {daily_training['summary']}
    </div>
    """, unsafe_allow_html=True)

    daily_html = ""
    for block in daily_training["training_blocks"]:
        daily_html += f"""
        <div class="param-cell" style="margin-bottom:4px;">
            <div>
                <span class="param-label">
                    {block['target_metric']}（{block['reason']}）
                </span><br>
                <span style="font-family:'Noto Sans JP',sans-serif;
                             font-size:13px; color:#e0e6f0;">
                    {block['menu_name']} — {block['detail']}
                </span>
            </div>
            <span class="rank-badge rank-B">{block['duration_min']}分</span>
        </div>"""
    st.markdown(daily_html, unsafe_allow_html=True)

with tab_weekly:
    weekly_plan = generate_weekly_plan(advice_list)
    weekly_html = ""
    for day in weekly_plan:
        weekly_html += f"""
        <div class="param-cell" style="margin-bottom:4px;">
            <div>
                <span class="param-label">
                    {day['date']}（{day['weekday']}）
                </span><br>
                <span style="font-family:'Noto Sans JP',sans-serif;
                             font-size:13px; color:#e0e6f0;">
                    {day['menu_name']} — {day['detail']}
                    （対象：{day['target_metric']}）
                </span>
            </div>
            <span class="rank-badge rank-B">{day['duration_min']}分</span>
        </div>"""
    st.markdown(weekly_html, unsafe_allow_html=True)

# ── ライバル選手抽出 ────────────────────────────────
weak_metric_names = [
    item["指標"] for item in advice_list
    if item["判定"] in ("要強化", "重点課題")
]

rival_info = find_rival(
    df, team_stats, selected_player, name_col,
    selected_metrics, weak_metric_names
)

st.markdown('<div class="section-header">RIVAL PLAYER</div>',
            unsafe_allow_html=True)

if rival_info.get("rival"):
    st.markdown(f"""
    <div style="border-top:2px solid #ff4d4d; padding:12px 0;">
        <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                    color:#ff4d4d; letter-spacing:0.2em;">RIVAL DETECTED</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:24px;
                    font-weight:700; color:#fff;">
            {rival_info['rival']}
        </div>
        <div style="font-family:'Noto Sans JP',sans-serif; font-size:11px;
                    color:#7a9cc0; margin-top:4px;">
            類似する課題：{', '.join(rival_info['weak_metrics'])}
            （距離スコア：{rival_info['distance']}）
        </div>
    </div>
    """, unsafe_allow_html=True)

    comparison = compare_with_rival(
        df, name_col, selected_player,
        rival_info["rival"], selected_metrics
    )

    comp_html = """
    <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr;
                gap:2px; margin-top:8px;">
        <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                    color:#4da3ff; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">指標</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                    color:#4da3ff; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">自分</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                    color:#ff7a7a; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">ライバル</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                    color:#e0e6f0; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">差</div>"""

    for comp in comparison:
        comp_html += f"""
        <div style="font-family:'Noto Sans JP',sans-serif; font-size:12px;
                    color:#7a9cc0; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">{comp['指標']}</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:14px;
                    color:#4da3ff; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">{comp['自分']}</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:14px;
                    color:#ff7a7a; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">{comp['ライバル']}</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:14px;
                    color:#e0e6f0; padding:4px 0;
                    border-bottom:1px solid #1e2d4a;">{comp['差']}</div>"""

    comp_html += "</div>"
    st.markdown(comp_html, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="null-warning">比較対象となる選手が見つかりませんでした。</div>
    """, unsafe_allow_html=True)

# ── グループ散布図マップ ────────────────────────────
st.markdown('<div class="section-header">PLAYER DISTRIBUTION MAP</div>',
            unsafe_allow_html=True)

if len(selected_metrics) >= 2:
    try:
        from sklearn.decomposition import PCA
        z_all = calc_z_scores(df, selected_metrics).fillna(0)
        pca   = PCA(n_components=2)
        coords = pca.fit_transform(z_all[selected_metrics].values)

        scatter_df = pd.DataFrame({
            "x":     coords[:, 0],
            "y":     coords[:, 1],
            "選手":  df[name_col].astype(str).values,
            "タイプ": ["対象選手" if str(n) == str(selected_player)
                      else "他の選手"
                      for n in df[name_col]]
        })

        scatter_fig = px.scatter(
            scatter_df, x="x", y="y",
            color="タイプ", hover_name="選手",
            color_discrete_map={
                "対象選手": "#ff4d4d",
                "他の選手": "#4da3ff"
            },
            title="選手分布マップ（PCA 2次元）"
        )
        scatter_fig.update_layout(
            paper_bgcolor="#0a0e1a",
            plot_bgcolor="#0d1626",
            font=dict(color="#e0e6f0", family="Rajdhani"),
            xaxis=dict(gridcolor="#1e2d4a", zerolinecolor="#1e2d4a"),
            yaxis=dict(gridcolor="#1e2d4a", zerolinecolor="#1e2d4a"),
            height=380
        )
        st.plotly_chart(scatter_fig, use_container_width=True)
        st.markdown("""
        <div style="font-family:'Noto Sans JP',sans-serif; font-size:11px;
                    color:#5a7a9a; margin-top:-8px;">
            ※ 近い位置にいる選手ほど、測定パターンが類似しています。
        </div>""", unsafe_allow_html=True)
    except ImportError:
        st.info("散布図マップにはscikit-learnが必要です：pip install scikit-learn")
else:
    st.info("散布図マップには2項目以上の選択が必要です。")

# ── コーチレポート ──────────────────────────────────
st.markdown('<div class="section-header">COACH REPORT</div>',
            unsafe_allow_html=True)

coach_report = generate_coach_report(
    str(selected_player), advice_list, rival_info, daily_training
)

st.markdown(f"""
<div style="background:#0d1626; border-left:3px solid #4da3ff;
            padding:16px 20px; font-family:'Noto Sans JP',sans-serif;
            font-size:13px; color:#c0d0e0; line-height:1.9;
            white-space:pre-wrap;">{coach_report}</div>
""", unsafe_allow_html=True)

# ── Googleカレンダー連携（ガイダンスUI） ────────────
st.markdown('<div class="section-header">GOOGLE CALENDAR SYNC</div>',
            unsafe_allow_html=True)

if is_calendar_connected():
    cal_col1, cal_col2 = st.columns(2)
    with cal_col1:
        if st.button("本日のメニューをカレンダーに登録"):
            success = push_training_to_calendar(daily_training)
            st.success("カレンダーに登録しました。") if success \
                else st.error("登録に失敗しました。")
    with cal_col2:
        if st.button("1週間分をカレンダーに登録"):
            result = push_weekly_plan_to_calendar(weekly_plan)
            st.info(f"成功：{result['success']} / 失敗：{result['failed']}")
else:
    st.markdown("""
    <div class="cal-guide-box">
        <div style="font-family:'Rajdhani',sans-serif; font-size:14px;
                    color:#4da3ff; letter-spacing:0.15em; margin-bottom:8px;">
            CALENDAR SYNC — HOW IT WORKS
        </div>
        <div style="font-family:'Noto Sans JP',sans-serif; font-size:12px;
                    color:#a0b8d0; line-height:2.0;">
            本システムでは <strong style="color:#e0e6f0;">Google Calendar API</strong>
            を設定することで、<br>
            AIが生成したトレーニングメニューを選手のカレンダーに
            <strong style="color:#e0e6f0;">即時同期</strong>できます。<br><br>
            ✅ 選手はスマホのGoogleカレンダーでメニューを確認<br>
            ✅ コーチはワンクリックで週間プランを一括配信<br>
            ✅ 測定データ更新のたびにメニューを自動更新<br><br>
            <span style="color:#5a7a9a; font-size:11px;">
                ※ 本機能はGoogle Cloud ConsoleでのOAuth認証設定後に利用可能になります。
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Googleアカウントで連携（準備中）", disabled=True)

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
    "player":         str(selected_player),
    "metrics":        selected_metrics,
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
    "advice":         advice_list,
    "rival":          rival_info,
    "daily_training": daily_training,
    "weekly_plan":    weekly_plan,
    "coach_report":   coach_report
}

ec1, ec2, ec3 = st.columns(3)
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
with ec3:
    try:
        pdf_bytes = generate_player_pdf(
            str(selected_player), advice_list,
            daily_training, weekly_plan,
            coach_report, rival_info
        )
        st.download_button(
            "EXPORT PDF（選手カルテ）",
            data=pdf_bytes,
            file_name=f"{selected_player}_report.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.button("EXPORT PDF（準備中）", disabled=True)