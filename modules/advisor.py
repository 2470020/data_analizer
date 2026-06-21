import pandas as pd

LOW_IS_BETTER = ["30m走(秒)", "50m走(秒)", "タイム"]

def generate_advice(player_data: pd.Series, team_stats: pd.DataFrame,
                    metric_cols: list) -> list[dict]:
    """
    各指標に対して判定コメントを生成
    返り値: [{"metric": str, "status": str, "comment": str}, ...]
    """
    advice_list = []
    for col in metric_cols:
        player_val = player_data[col]
        mean = team_stats.loc[col, "チーム平均"]
        std = team_stats.loc[col, "標準偏差"]
        z = (player_val - mean) / std if std > 0 else 0

        # 低いほど良い指標は符号反転
        if any(keyword in col for keyword in LOW_IS_BETTER):
            z = -z

        if z >= 1.0:
            status = "🟢 優秀"
            comment = f"チーム内でトップクラス。この強みを活かしたトレーニングを継続してください。"
        elif z >= 0:
            status = "🔵 平均以上"
            comment = f"チーム平均を上回っています。さらに伸ばせる余地があります。"
        elif z >= -1.0:
            status = "🟡 要強化"
            comment = f"チーム平均をやや下回っています。重点的なトレーニングを推奨します。"
        else:
            status = "🔴 重点課題"
            comment = f"チーム内で改善が特に必要な項目です。専門コーチへの相談を検討してください。"

        advice_list.append({"指標": col, "判定": status,
                             "選手値": player_val,
                             "チーム平均": round(mean, 2),
                             "コメント": comment})
    return advice_list