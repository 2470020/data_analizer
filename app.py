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
                               normalize_for_radar, calc_overall_ranking)
from modules.advisor import generate_advice, find_ideal_player, generate_trainer_comment
from modules.visualizer import draw_category_radar_charts

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
.ranking-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Rajdhani', sans-serif;
}
.ranking-table th {
    background: #0d1626;
    color: #4da3ff;
    font-size: 11px;
    letter-spacing: 0.15em;
    padding: 8px 12px;
    border-bottom: 1px solid #1e3a5f;
    text-align: center;
}
.ranking-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #0d1626;
    text-align: center;
    font-size: 14px;
    color: #e0e6f0;
}
.ranking-table tr:nth-child(even) td { background: #0a0e1a; }
.ranking-table tr:nth-child(odd)  td { background: #0d1220; }
.ai-comment-box {
    background: #0d1626;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #4da3ff;
    padding: 16px 20px;
    margin: 8px 0;
    font-family: 'Noto Sans JP', sans-serif;
    font-size: 13px;
    line-height: 1.8;
    color: #c0d4e8;
}
.ai-comment-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: #4da3ff;
    margin-bottom: 6px;
}
.ideal-compare-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 4px;
    margin: 12px 0;
}
.ideal-compare-cell {
    background: #0d1626;
    border: 1px solid #1e2d4a;
    padding: 10px 12px;
}
.ideal-compare-col { font-size: 11px; color: #7a9cc0; margin-bottom: 4px; }
.ideal-compare-vals { display: flex; gap: 12px; align-items: baseline; }
.ideal-val-player { font-family: 'Rajdhani', sans-serif; font-size: 18px; color: #4da3ff; }
.ideal-val-model  { font-family: 'Rajdhani', sans-serif; font-size: 14px; color: #ffd700; }
.ideal-val-arrow  { font-size: 11px; color: #3a5a7a; }
.score-bar-wrap { background: #0d1626; border-radius: 2px; height: 6px; margin-top: 4px; }
.score-bar-fill { height: 6px; border-radius: 2px; background: linear-gradient(90deg, #1a6fc4, #4da3ff); }

/* ── AIトレーナーパネル ── */
.trainer-panel {
    background: linear-gradient(135deg, #0d1626 0%, #0a1a2e 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.4rem 1.2rem 1.2rem;
    margin-top: 0.5rem;
}
.trainer-section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4da3ff;
    border-left: 3px solid #4da3ff;
    padding-left: 0.5rem;
    margin: 1rem 0 0.4rem;
}
.trainer-text {
    font-size: 0.88rem;
    color: #c8d8e8;
    line-height: 1.7;
    margin: 0;
    font-family: 'Noto Sans JP', sans-serif;
}
.trainer-item {
    display: flex;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: #c8d8e8;
    line-height: 1.6;
    margin-bottom: 0.4rem;
    font-family: 'Noto Sans JP', sans-serif;
}
.trainer-bullet { color: #4da3ff; flex-shrink: 0; margin-top: 0.1rem; }
.trainer-strength {
    background: rgba(77,163,255,0.08);
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    font-size: 0.85rem;
    color: #c8d8e8;
    line-height: 1.6;
    font-family: 'Noto Sans JP', sans-serif;
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

    c1, c2, c3, c4 = st.columns(4)
    for col_ui, label, val in [
        (c1, "FUNCTION 01", "DATA<br>IMPORT"),
        (c2, "FUNCTION 02", "SKILL<br>ANALYSIS"),
        (c3, "FUNCTION 03", "AI<br>COACHING"),
        (c4, "FUNCTION 04", "TEAM<br>RANKING"),
    ]:
        with col_ui:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-box-label">{label}</div>
                <div class="stat-box-value">{val}</div>
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

if name_col not in df.columns:
    st.error(f"列「{name_col}」が見つかりません。サイドバーで列を確認してください。")
    st.stop()

all_metric_cols = get_metric_columns(df, name_col)

if not all_metric_cols:
    st.error("分析できる数値列が見つかりません。ファイルの内容を確認してください。")
    st.stop()

st.markdown(f"""
<div class="progress-info">
    FILES LOADED : {total} &nbsp;|&nbsp; TOTAL PLAYERS : {len(df)}
    &nbsp;|&nbsp; PARAMETERS : {len(all_metric_cols)}
</div>
""", unsafe_allow_html=True)

# ── 重複チェック ────────────────────────────────────
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

# ── クリーニング ────────────────────────────────────
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

# ── タブ ────────────────────────────────────────────
tab_player, tab_ranking = st.tabs(["PLAYER ANALYSIS", "TEAM RANKING"])


# ════════════════════════════════════════════════════
# AIトレーナーパネル描画関数
# ════════════════════════════════════════════════════
def render_trainer_panel(player_name: str, ideal_info: dict,
                         advice_list: list, metric_cols: list) -> None:
    """右カラム用 AIトレーナーパネル"""

    btn_key     = f"trainer_btn_{player_name}"
    session_key = f"trainer_comment_{player_name}"

    # ボタン（primary スタイルを上書き）
    st.markdown("""
    <style>
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #1a4a8a 0%, #0d2a5a 100%) !important;
        border: 1px solid #4da3ff !important;
        color: #ffffff !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 15px !important;
        letter-spacing: 0.15em !important;
        padding: 0.55rem 1rem !important;
        border-radius: 4px !important;
        width: 100% !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1e6fc4 0%, #1a4a8a 100%) !important;
        border-color: #7ac3ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🤖  AI トレーナー", key=btn_key, type="primary",
                 use_container_width=True):
        with st.spinner("AIトレーナーが分析中..."):
            comment = generate_trainer_comment(
                player_name=player_name,
                ideal_info=ideal_info,
                advice_list=advice_list,
                metric_cols=metric_cols,
            )
        st.session_state[session_key] = comment

    comment = st.session_state.get(session_key)
    if not comment:
        st.markdown(
            "<p style='color:#3a5a7a; font-size:0.82rem; margin-top:0.8rem;'>"
            "ボタンを押すとAIトレーナーからの<br>アドバイスが表示されます。"
            "</p>",
            unsafe_allow_html=True,
        )
        return

    overview = comment.get("総評", "")
    improve  = comment.get("重点改善", [])
    strength = comment.get("強み活用", "")

    html = f"""
<div class="trainer-panel">
  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem;">
    <span style="font-size:1.5rem;">🏋️</span>
    <span style="font-family:'Rajdhani',sans-serif;font-size:1rem;
                 font-weight:700;color:#4da3ff;letter-spacing:0.05em;">
      AI TRAINER
    </span>
  </div>
  <div class="trainer-section-label">現状分析</div>
  <p class="trainer-text">{overview}</p>
"""
    if improve:
        html += '<div class="trainer-section-label">重点改善ポイント</div>'
        for item in improve:
            html += f"""
  <div class="trainer-item">
    <span class="trainer-bullet">▶</span>
    <span>{item}</span>
  </div>"""

    if strength:
        html += f"""
  <div class="trainer-section-label">強みの活かし方</div>
  <div class="trainer-strength">{strength}</div>"""

    html += "\n</div>"
    st.markdown(html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# TAB 1 : PLAYER ANALYSIS
# ════════════════════════════════════════════════════
with tab_player:

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

    # ── 統計計算 ──────────────────────────────────
    team_stats  = calc_team_stats(df, selected_metrics)
    player_data = get_player_data(df, selected_player, name_col)
    advice_list = generate_advice(player_data, team_stats, selected_metrics)
    ideal_info  = find_ideal_player(
        df, player_data, team_stats, selected_metrics, name_col)

    # ── ランク変換 ────────────────────────────────
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

    # ── 総合順位 ──────────────────────────────────
    ranking_df   = calc_overall_ranking(df, selected_metrics, name_col)
    player_rank  = None
    player_score = None
    if not ranking_df.empty:
        row = ranking_df[ranking_df[name_col].astype(str) == str(selected_player)]
        if not row.empty:
            player_rank  = int(row["順位"].values[0])
            player_score = float(row["総合スコア"].values[0])

    rank_disp  = f"#{player_rank}"     if player_rank  else "-"
    score_disp = f"{player_score:.1f}" if player_score else "-"

    # ════════════════════════════════════════════════
    # メイン2カラムレイアウト（左：分析, 右：AIトレーナー）
    # ════════════════════════════════════════════════
    main_col, trainer_col = st.columns([3, 1])

    with main_col:

        # ── 選手ヘッダー ──────────────────────────
        st.markdown(f"""
        <div style="border-top:2px solid #1a6fc4; border-bottom:1px solid #1e2d4a;
                    padding:16px 0; margin:24px 0 8px; display:flex;
                    justify-content:space-between; align-items:flex-end;">
            <div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                            color:#4da3ff; letter-spacing:0.3em;">PLAYER PROFILE</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:32px;
                            font-weight:700; color:#fff; letter-spacing:0.1em;">
                    {str(selected_player).upper()}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'Rajdhani',sans-serif; font-size:11px;
                            color:#4da3ff; letter-spacing:0.2em;">OVERALL RANK</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:28px;
                            font-weight:700; color:#ffd700;">{rank_disp}</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:13px;
                            color:#7a9cc0;">SCORE {score_disp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── パラメーターグリッド ──────────────────
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

        # ── カテゴリ別レーダーチャート ────────────
        st.markdown('<div class="section-header">RADAR CHART — BY CATEGORY</div>',
                    unsafe_allow_html=True)

        # normalize_for_radar の結果をマップ形式に変換
        player_norm, team_norm = normalize_for_radar(
            player_data, team_stats, selected_metrics)
        player_vals_map = dict(zip(selected_metrics, player_norm))
        team_vals_map   = dict(zip(selected_metrics, team_norm))

        cat_figs = draw_category_radar_charts(
            metric_cols=selected_metrics,
            player_vals_map=player_vals_map,
            team_vals_map=team_vals_map,
            player_name=str(selected_player).upper(),
        )

        # カテゴリが1つも取れなかった場合は従来の全体チャートにフォールバック
        valid_cat_figs = {k: v for k, v in cat_figs.items() if v is not None}

        if valid_cat_figs:
            radar_cols = st.columns(len(valid_cat_figs))
            for rc, (cat_name, fig) in zip(radar_cols, valid_cat_figs.items()):
                with rc:
                    st.markdown(
                        f"<div style='font-family:\"Rajdhani\",sans-serif;"
                        f"font-size:12px;color:#7a9cc0;text-align:center;"
                        f"margin-bottom:4px;'>{cat_name}</div>",
                        unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            # フォールバック：全指標の単一レーダー
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
                    radialaxis=dict(visible=True, range=[0, 100],
                                    gridcolor="#1e2d4a", linecolor="#1e2d4a",
                                    tickfont=dict(color="#2a4a6a", size=9),
                                    tickvals=[25, 50, 75, 100]),
                    angularaxis=dict(gridcolor="#1e2d4a", linecolor="#1e2d4a",
                                     tickfont=dict(color="#7a9cc0", size=11,
                                                   family="Noto Sans JP"))
                ),
                paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a",
                font=dict(color="#e0e6f0", family="Rajdhani"),
                legend=dict(bgcolor="#0d1626", bordercolor="#1e2d4a",
                            borderwidth=1, font=dict(size=11)),
                height=460, margin=dict(t=30, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── AIモデル選手比較 ──────────────────────
        st.markdown('<div class="section-header">AI MODEL PLAYER COMPARISON</div>',
                    unsafe_allow_html=True)

        if ideal_info:
            comparison = ideal_info["比較"]

            # 目標選手名は伏せて「目標選手」と表示
            st.markdown("""
            <div style="font-family:'Rajdhani',sans-serif; font-size:12px;
                        color:#7a9cc0; margin-bottom:12px;">
                TARGET MODEL PLAYER &nbsp;→&nbsp;
                <span style="color:#ffd700; font-size:16px; font-weight:700;">
                    目標選手
                </span>
            </div>
            """, unsafe_allow_html=True)

            cells = ""
            for col, d in comparison.items():
                pv  = d["選手値"] if d["選手値"] is not None else "-"
                iv  = d["理想値"] if d["理想値"] is not None else "-"
                pz  = d["選手Z"]  if d["選手Z"]  is not None else 0
                bar = min(max((pz + 2) / 4 * 100, 0), 100)
                cells += f"""
                <div class="ideal-compare-cell">
                    <div class="ideal-compare-col">{col}</div>
                    <div class="ideal-compare-vals">
                        <span class="ideal-val-player">{pv}</span>
                        <span class="ideal-val-arrow">→</span>
                        <span class="ideal-val-model">{iv}</span>
                    </div>
                    <div class="score-bar-wrap">
                        <div class="score-bar-fill" style="width:{bar:.0f}%"></div>
                    </div>
                </div>"""

            st.markdown(f'<div class="ideal-compare-grid">{cells}</div>',
                        unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="null-warning">
                比較可能な選手データが不足しています（選手が1名のみ、またはデータ不足）。
            </div>""", unsafe_allow_html=True)

        # ── 分析レポート ──────────────────────────
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

        # ── エクスポート ──────────────────────────
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
            "advice":       advice_list,
            "ideal_player": ideal_info if ideal_info else {}
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

    # ── 右カラム：AIトレーナー ────────────────────
    with trainer_col:
        st.markdown(
            "<div style='margin-top:88px;'></div>",
            unsafe_allow_html=True)
        render_trainer_panel(
            player_name=str(selected_player),
            ideal_info=ideal_info,
            advice_list=advice_list,
            metric_cols=selected_metrics,
        )


# ════════════════════════════════════════════════════
# TAB 2 : TEAM RANKING
# ════════════════════════════════════════════════════
with tab_ranking:

    st.markdown('<div class="section-header">OVERALL RANKING SETUP</div>',
                unsafe_allow_html=True)

    ranking_metrics = st.multiselect(
        "ランキングに使用する指標",
        options=all_metric_cols,
        default=all_metric_cols,
        key="ranking_metrics"
    )

    if not ranking_metrics:
        st.warning("指標を1つ以上選択してください。")
    else:
        ranking_df = calc_overall_ranking(df, ranking_metrics, name_col)

        st.markdown('<div class="section-header">TEAM OVERALL RANKING</div>',
                    unsafe_allow_html=True)

        top3 = ranking_df.head(3)
        t1, t2, t3 = st.columns(3)
        medal_cols   = [t1, t2, t3]
        medal_icons  = ["🥇", "🥈", "🥉"]
        medal_colors = ["#ffd700", "#c0c0c0", "#cd7f32"]

        for idx, (col_ui, icon, color) in enumerate(
                zip(medal_cols, medal_icons, medal_colors)):
            if idx < len(top3):
                row = top3.iloc[idx]
                with col_ui:
                    st.markdown(f"""
                    <div style="border:1px solid {color}33; background:#0d1626;
                                padding:16px; text-align:center; margin-bottom:8px;">
                        <div style="font-size:28px;">{icon}</div>
                        <div style="font-family:'Rajdhani',sans-serif;
                                    font-size:18px; font-weight:700;
                                    color:{color}; letter-spacing:0.1em;">
                            {str(row[name_col]).upper()}
                        </div>
                        <div style="font-family:'Rajdhani',sans-serif;
                                    font-size:28px; font-weight:700; color:#fff;">
                            {row['総合スコア']:.1f}
                        </div>
                        <div style="font-family:'Rajdhani',sans-serif;
                                    font-size:11px; color:#4da3ff;">SCORE</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        def medal(rank):
            if rank == 1: return "🥇"
            if rank == 2: return "🥈"
            if rank == 3: return "🥉"
            return str(rank)

        rows_html = ""
        for _, row in ranking_df.iterrows():
            rank  = int(row["順位"])
            score = float(row["総合スコア"])
            name  = str(row[name_col])
            bar   = score

            bar_html = f"""
            <div style="background:#0a0e1a; border-radius:2px; height:4px;
                        width:120px; display:inline-block; vertical-align:middle;
                        margin-left:8px;">
                <div style="width:{bar:.0f}%; height:4px; border-radius:2px;
                            background:linear-gradient(90deg,#1a6fc4,#4da3ff);"></div>
            </div>"""

            rows_html += f"""
            <tr>
                <td style="font-family:'Rajdhani',sans-serif; font-size:18px;
                           color:{'#ffd700' if rank<=3 else '#5a7a9a'};">
                    {medal(rank)}
                </td>
                <td style="font-family:'Rajdhani',sans-serif; font-size:15px;
                           color:#e0e6f0; letter-spacing:0.05em;">
                    {name.upper()}
                </td>
                <td>
                    <span style="font-family:'Rajdhani',sans-serif;
                                 font-size:20px; font-weight:700; color:#4da3ff;">
                        {score:.1f}
                    </span>
                    {bar_html}
                </td>
            </tr>"""

        st.markdown(f"""
        <table class="ranking-table">
            <thead>
                <tr>
                    <th style="width:60px;">RANK</th>
                    <th style="text-align:left;">PLAYER</th>
                    <th style="text-align:left;">SCORE</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="section-header">TOP 5 RADAR COMPARISON</div>',
                    unsafe_allow_html=True)

        top5         = ranking_df.head(5)
        team_stats_r = calc_team_stats(df, ranking_metrics)
        fig2         = go.Figure()
        colors       = ["#ffd700", "#4da3ff", "#a0c4e8", "#7a9cc0", "#5a7a9a"]

        for i, (_, row) in enumerate(top5.iterrows()):
            pname = str(row[name_col])
            try:
                pdata = get_player_data(df, pname, name_col)
                pnorm, _ = normalize_for_radar(pdata, team_stats_r, ranking_metrics)
                cats   = ranking_metrics + [ranking_metrics[0]]
                pvals  = pnorm + [pnorm[0]]
                fig2.add_trace(go.Scatterpolar(
                    r=pvals, theta=cats, fill="toself",
                    name=pname.upper(),
                    line=dict(color=colors[i], width=2),
                    fillcolor=f"rgba({int(colors[i][1:3],16)},"
                              f"{int(colors[i][3:5],16)},"
                              f"{int(colors[i][5:7],16)},0.08)"
                ))
            except Exception:
                pass

        fig2.update_layout(
            polar=dict(
                bgcolor="#0a0e1a",
                radialaxis=dict(visible=True, range=[0, 100],
                                gridcolor="#1e2d4a", linecolor="#1e2d4a",
                                tickfont=dict(color="#2a4a6a", size=9),
                                tickvals=[25, 50, 75, 100]),
                angularaxis=dict(gridcolor="#1e2d4a", linecolor="#1e2d4a",
                                 tickfont=dict(color="#7a9cc0", size=11,
                                               family="Noto Sans JP"))
            ),
            paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a",
            font=dict(color="#e0e6f0", family="Rajdhani"),
            legend=dict(bgcolor="#0d1626", bordercolor="#1e2d4a",
                        borderwidth=1, font=dict(size=11)),
            height=500, margin=dict(t=30, b=30)
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-header">EXPORT RANKING</div>',
                    unsafe_allow_html=True)
        export_cols = [name_col, "順位", "総合スコア"]
        st.download_button(
            "EXPORT RANKING CSV",
            data=ranking_df[export_cols].to_csv(
                index=False, encoding="utf-8-sig"),
            file_name="team_ranking.csv",
            mime="text/csv"
        )