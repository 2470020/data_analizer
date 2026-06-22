import pandas as pd

LOW_IS_BETTER_KEYWORDS = ["走(秒)", "タイム", "秒"]


def _is_low_better(col_name: str) -> bool:
    return any(kw in col_name for kw in LOW_IS_BETTER_KEYWORDS)


def _calc_z(player_val, mean: float, std: float,
            col_name: str):
    if pd.isna(player_val) or std <= 0:
        return None
    z = (float(player_val) - float(mean)) / float(std)
    return -z if _is_low_better(col_name) else z


def generate_advice(player_data: pd.Series,
                    team_stats: pd.DataFrame,
                    metric_cols: list) -> list:
    advice_list = []

    for col in metric_cols:
        player_val = player_data[col]
        mean       = team_stats.loc[col, "チーム平均"]
        std        = team_stats.loc[col, "標準偏差"]
        z          = _calc_z(player_val, float(mean), float(std), col)

        if z is None or pd.isna(player_val):
            advice_list.append({
                "指標":       col,
                "判定":       "-",
                "選手値":     "-",
                "チーム平均": round(float(mean), 2),
                "Zスコア":    "-",
                "コメント":   "データなし（null値または外れ値として除外）"
            })
            continue

        if z >= 1.0:
            status  = "優秀"
            comment = "チーム内でトップクラスの数値です。この強みを活かしたトレーニングを継続してください。"
        elif z >= 0.0:
            status  = "平均以上"
            comment = "チーム平均を上回っています。さらに伸ばせる余地があります。"
        elif z >= -1.0:
            status  = "要強化"
            comment = "チーム平均をやや下回っています。重点的なトレーニングを推奨します。"
        else:
            status  = "重点課題"
            comment = "チーム内で改善が特に必要な項目です。専門コーチへの相談を検討してください。"

        advice_list.append({
            "指標":       col,
            "判定":       status,
            "選手値":     round(float(player_val), 2),
            "チーム平均": round(float(mean), 2),
            "Zスコア":    round(z, 2),
            "コメント":   comment
        })

    return advice_list