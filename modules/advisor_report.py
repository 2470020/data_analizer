import pandas as pd


def _rank_word(rank_status: str) -> str:
    mapping = {
        "優秀":   "強み",
        "平均以上": "及第点",
        "要強化":  "課題",
        "重点課題": "最優先課題",
        "-":      "データ欠損"
    }
    return mapping.get(rank_status, rank_status)


def generate_coach_report(player_name: str,
                          advice_list: list,
                          rival_info: dict,
                          daily_training: dict) -> str:
    """
    コーチ口調の統合分析レポートを生成する。
    データ主体・簡潔・手厳しく。
    """
    strong_items = [a for a in advice_list if a["判定"] == "優秀"]
    weak_items   = [a for a in advice_list
                    if a["判定"] in ("要強化", "重点課題")]
    critical     = [a for a in advice_list if a["判定"] == "重点課題"]

    lines = []
    lines.append(f"【{player_name} 分析レポート】")
    lines.append("")

    # 総評
    if critical:
        lines.append(
            f"結論から言う。{', '.join([c['指標'] for c in critical])}が深刻に遅れている。"
            f"ここを放置している限り、上のレベルでは通用しない。"
        )
    elif weak_items:
        lines.append(
            f"全体としては悪くないが、{', '.join([w['指標'] for w in weak_items])}に伸びしろがある。"
            f"中途半端な選手で終わりたくなければ、ここを詰めろ。"
        )
    else:
        lines.append("全項目で平均を上回っている。現状維持ではなく、さらに上を狙え。")

    lines.append("")

    # 強み
    if strong_items:
        lines.append("■ 強み")
        for item in strong_items:
            lines.append(
                f"・{item['指標']}：{item['選手値']}"
                f"（チーム平均 {item['チーム平均']}）— この水準を落とすな。"
            )
        lines.append("")

    # 課題
    if weak_items:
        lines.append("■ 課題")
        for item in weak_items:
            tag = _rank_word(item["判定"])
            lines.append(
                f"・{item['指標']}：{item['選手値']}"
                f"（チーム平均 {item['チーム平均']}）— {tag}。Zスコア {item['Zスコア']}。"
            )
        lines.append("")

    # ライバル
    if rival_info.get("rival"):
        lines.append("■ ライバル設定")
        lines.append(
            f"課題が酷似しているのは {rival_info['rival']} だ。"
            f"同じ弱点を抱えている以上、ここに先を越されたら言い訳はできない。"
            f"対象項目：{', '.join(rival_info['weak_metrics'])}"
        )
        lines.append("")

    # 本日のトレーニング
    if daily_training and daily_training.get("training_blocks"):
        lines.append("■ 本日のメニュー")
        for block in daily_training["training_blocks"]:
            lines.append(
                f"・{block['menu_name']}（{block['detail']}、"
                f"{block['duration_min']}分）— 対象：{block['target_metric']}"
            )
        lines.append("")
        lines.append("これをやらずに結果だけ求めるな。まずは今日のメニューをこなせ。")

    return "\n".join(lines)