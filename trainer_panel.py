"""
trainer_panel.py
----------------
Streamlit の右カラムに「AIトレーナー」ボタンを配置し、
押したらコーチングコメントを表示するパネルコンポーネント。

使い方（app.py 側）:
    from trainer_panel import render_trainer_panel

    left_col, right_col = st.columns([2, 1])
    with left_col:
        # レーダーチャートなど既存UI
        ...
    with right_col:
        render_trainer_panel(
            player_name=selected_player,
            ideal_info=ideal_info,
            advice_list=advice_list,
            metric_cols=metric_cols,
        )
"""

import streamlit as st
from advisor import generate_trainer_comment

_PANEL_CSS = """
<style>
.trainer-panel {
    background: linear-gradient(135deg, #0d1626 0%, #0a1a2e 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.4rem 1.2rem 1.2rem;
    margin-top: 0.5rem;
}
.trainer-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.trainer-icon {
    font-size: 1.6rem;
}
.trainer-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #4da3ff;
    letter-spacing: 0.05em;
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
}
.trainer-item {
    display: flex;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: #c8d8e8;
    line-height: 1.6;
    margin-bottom: 0.4rem;
}
.trainer-bullet {
    color: #4da3ff;
    flex-shrink: 0;
    margin-top: 0.1rem;
}
.trainer-strength {
    background: rgba(77,163,255,0.08);
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    font-size: 0.85rem;
    color: #c8d8e8;
    line-height: 1.6;
}
</style>
"""


def render_trainer_panel(
    player_name: str,
    ideal_info: dict,
    advice_list: list,
    metric_cols: list,
) -> None:
    """
    右カラム用 AIトレーナーパネルをレンダリングする。
    ボタンを押すとAPIを呼び出してコメントを表示。
    """
    st.markdown(_PANEL_CSS, unsafe_allow_html=True)

    # ---- ボタン ----
    btn_clicked = st.button(
        "🤖 AIトレーナー",
        key=f"trainer_btn_{player_name}",
        use_container_width=True,
        type="primary",
    )

    # セッションキー
    session_key = f"trainer_comment_{player_name}"

    if btn_clicked:
        with st.spinner("AIトレーナーが分析中..."):
            comment = generate_trainer_comment(
                player_name=player_name,
                ideal_info=ideal_info,
                advice_list=advice_list,
                metric_cols=metric_cols,
            )
        st.session_state[session_key] = comment

    # ---- コメント表示 ----
    comment = st.session_state.get(session_key)
    if not comment:
        st.markdown(
            "<p style='color:#3a5a7a;font-size:0.82rem;margin-top:0.8rem;'>"
            "ボタンを押すとAIトレーナーからのアドバイスが表示されます。"
            "</p>",
            unsafe_allow_html=True,
        )
        return

    # 総評
    overview   = comment.get("総評", "")
    improve    = comment.get("重点改善", [])
    strength   = comment.get("強み活用", "")

    html = f"""
<div class="trainer-panel">
  <div class="trainer-header">
    <span class="trainer-icon">🏋️</span>
    <span class="trainer-title">AIトレーナーより</span>
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