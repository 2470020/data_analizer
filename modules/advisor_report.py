import random


def _level_phrase(z) -> str:
    """Zスコアを、数値を出さずに『今のレベル感』として言葉にする"""
    if z is None:
        return "まだデータが少なくて、はっきりとは言えませんが"
    if z >= 1.5:
        return "この種目は、チームの中でもかなり高いレベルにあります"
    if z >= 0.5:
        return "この種目は、平均よりしっかり上を行けています"
    if z >= -0.5:
        return "この種目は、ちょうどチームの平均くらいの位置にいます"
    if z >= -1.5:
        return "この種目は、もう一息で平均に追いつけそうな位置です"
    return "この種目は、今いちばん伸びしろが大きい部分です"


def _advice_phrase(z, metric_name: str) -> str:
    """レベルに応じたアドバイスのコメント（数値なし）"""
    if z is None:
        return "まずは継続して記録を取って、自分の傾向をつかんでいきましょう。"
    if z >= 1.5:
        return f"{metric_name}は今のあなたの武器です。フォームの安定感を保ちながら、他の種目に体力や意識を割いていきましょう。"
    if z >= 0.5:
        return f"良いペースで仕上がっています。基礎をキープしつつ、細かい技術の精度を上げていくと、さらに安定した結果につながります。"
    if z >= -0.5:
        return f"伸び悩みやすい時期かもしれませんが、フォームや動き出しの細部を見直すだけで変化が出やすいところです。焦らず取り組みましょう。"
    if z >= -1.5:
        return f"少しの積み重ねで結果が変わってくる段階です。練習の頻度よりも、毎回の質を意識してみてください。"
    return f"{metric_name}は今いちばん伸ばしがいのある種目です。基礎から丁寧に取り組むことで、他の種目にも良い影響が出てきます。"


def _training_suggestion(metric_name: str, z) -> str:
    """次のトレーニングの方向性（メニュー名は既存のtraining_generatorと連携想定）"""
    if z is not None and z >= 1.0:
        return f"今の{metric_name}の強さを維持するための軽めの調整メニューをおすすめします。"
    elif z is not None and z <= -1.0:
        return f"{metric_name}に絞った基礎強化メニューを、週の中に2〜3回取り入れてみましょう。"
    else:
        return f"{metric_name}は、フォーム確認を中心とした技術メニューが効果的です。"


def generate_metric_coach_comment(item: dict) -> dict:
    """
    1種目分の「AIトレーナーコメント」を生成する。
    数値（選手値・チーム平均・Zスコア）は一切文章に含めない。

    item: advice_list の中の1要素
          想定キー： "指標", "判定", "Zスコア"（無ければNone扱い）
    """
    metric_name = item["指標"]
    z = item.get("Zスコア")

    level   = _level_phrase(z)
    advice  = _advice_phrase(z, metric_name)
    training = _training_suggestion(metric_name, z)

    intro_variants = [
        f"「{metric_name}」について見てみましょう。",
        f"次は「{metric_name}」のお話です。",
        f"「{metric_name}」、ここが今回のポイントです。",
    ]
    intro = random.choice(intro_variants)

    comment_text = (
        f"{intro}\n"
        f"{level}。\n\n"
        f"{advice}\n\n"
        f"【今後のトレーニング】\n{training}"
    )

    return {
        "指標": metric_name,
        "コメント": comment_text
    }


def generate_coach_report(player_name: str,
                          advice_list: list,
                          rival_info: dict,
                          daily_training: dict) -> str:
    """
    旧来の統合レポート（互換用に残す）。
    数値を出さない全体まとめメッセージとして簡略化。
    """
    strong_items = [a for a in advice_list if a["判定"] == "優秀"]
    weak_items   = [a for a in advice_list
                    if a["判定"] in ("要強化", "重点課題")]

    lines = []
    lines.append(f"{player_name} さんへ")
    lines.append("")

    if weak_items:
        names = "、".join([w["指標"] for w in weak_items])
        lines.append(
            f"全体的に良い動きができています。"
            f"特に「{names}」を伸ばせると、さらに一段上のレベルに近づけそうです。"
            f"各種目の詳しいアドバイスは、下のボタンから種目ごとに確認できます。"
        )
    else:
        lines.append(
            "すべての種目で安定した結果が出ています。"
            "今の調子をキープしながら、種目ごとのアドバイスも参考にしてみてください。"
        )

    if strong_items:
        names = "、".join([s["指標"] for s in strong_items])
        lines.append("")
        lines.append(f"特に「{names}」はあなたの強みです。自信を持っていきましょう。")

    if rival_info.get("rival"):
        lines.append("")
        lines.append(
            f"{rival_info['rival']} さんも似た課題を持っています。"
            f"一緒に成長していける良い目標です。"
        )

    return "\n".join(lines)