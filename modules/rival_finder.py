import pandas as pd
import numpy as np


def find_rival(df: pd.DataFrame,
               team_stats: pd.DataFrame,
               selected_player: str,
               name_col: str,
               metric_cols: list,
               weak_metrics: list) -> dict:
    """
    弱点項目（weak_metrics）のZスコアパターンが最も近い選手を
    ライバルとして抽出する。

    判定基準：
        弱点項目に絞ったZスコアベクトルのユークリッド距離が最小の選手
    """
    if not weak_metrics:
        weak_metrics = metric_cols[:3]  # 弱点がなければ上位3項目で代用

    # Zスコア計算（弱点項目のみ）
    z_df = pd.DataFrame(index=df.index)
    for col in weak_metrics:
        mean = team_stats.loc[col, "チーム平均"]
        std  = team_stats.loc[col, "標準偏差"]
        if std > 0:
            z_df[col] = (df[col] - mean) / std
        else:
            z_df[col] = 0.0

    z_df[name_col] = df[name_col].values

    # 対象選手のZスコアベクトル
    target_row = z_df[z_df[name_col].astype(str) == str(selected_player)]
    if target_row.empty:
        return {"rival": None, "distance": None}

    target_vec = target_row[weak_metrics].iloc[0].fillna(0).values

    # 自分以外の選手との距離を計算
    candidates = z_df[z_df[name_col].astype(str) != str(selected_player)].copy()
    if candidates.empty:
        return {"rival": None, "distance": None}

    distances = []
    for _, row in candidates.iterrows():
        vec  = row[weak_metrics].fillna(0).values.astype(float)
        dist = np.linalg.norm(target_vec.astype(float) - vec)
        distances.append(dist)

    candidates["distance"] = distances
    nearest = candidates.sort_values("distance").iloc[0]

    return {
        "rival":        str(nearest[name_col]),
        "distance":      round(float(nearest["distance"]), 3),
        "weak_metrics":  weak_metrics
    }


def compare_with_rival(df: pd.DataFrame,
                       name_col: str,
                       selected_player: str,
                       rival_name: str,
                       metric_cols: list) -> list:
    """
    選択選手とライバルの各項目を比較するテーブルを生成する。
    """
    player_row = df[df[name_col].astype(str) == str(selected_player)].iloc[0]
    rival_row  = df[df[name_col].astype(str) == str(rival_name)].iloc[0]

    comparison = []
    for col in metric_cols:
        p_val = player_row[col]
        r_val = rival_row[col]
        if pd.isna(p_val) or pd.isna(r_val):
            diff_text = "-"
        else:
            diff = float(p_val) - float(r_val)
            diff_text = f"+{round(diff,2)}" if diff >= 0 else str(round(diff, 2))

        comparison.append({
            "指標":       col,
            "自分":       "-" if pd.isna(p_val) else round(float(p_val), 2),
            "ライバル":    "-" if pd.isna(r_val) else round(float(r_val), 2),
            "差":         diff_text
        })

    return comparison