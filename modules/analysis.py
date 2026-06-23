import pandas as pd
import numpy as np

LOW_IS_BETTER_KEYWORDS = ["走(秒)", "タイム", "秒", "run_", "_s"]


def _is_low_better(col_name: str) -> bool:
    return any(kw.lower() in col_name.lower()
               for kw in LOW_IS_BETTER_KEYWORDS)


def calc_team_stats(df: pd.DataFrame, metric_cols: list) -> pd.DataFrame:
    """
    pandas 3.x対応: 列ごとに個別計算してDataFrameを構築する。
    """
    if not metric_cols:
        return pd.DataFrame(columns=["チーム平均", "標準偏差"])

    rows = {}
    for col in metric_cols:
        rows[col] = {
            "チーム平均": df[col].mean(skipna=True),
            "標準偏差":   df[col].std(skipna=True)
        }
    return pd.DataFrame(rows).T


def calc_z_scores(df: pd.DataFrame, metric_cols: list) -> pd.DataFrame:
    z_df = df[metric_cols].copy()
    for col in metric_cols:
        mean = df[col].mean(skipna=True)
        std  = df[col].std(skipna=True)
        if std > 0:
            z_df[col] = (df[col] - mean) / std
            if _is_low_better(col):
                z_df[col] = -z_df[col]
        else:
            z_df[col] = 0.0
    return z_df


def get_player_data(df: pd.DataFrame, player_name: str,
                    name_col: str) -> pd.Series:
    return df[df[name_col].astype(str) == str(player_name)].iloc[0]


def normalize_for_radar(player_data: pd.Series,
                        team_stats: pd.DataFrame,
                        metric_cols: list) -> tuple:
    player_norm = []
    team_norm   = []

    for col in metric_cols:
        mean = team_stats.loc[col, "チーム平均"]
        std  = team_stats.loc[col, "標準偏差"]
        val  = player_data[col]

        if pd.isna(val) or std == 0:
            player_norm.append(50)
        else:
            p_z = (float(val) - float(mean)) / float(std)
            if _is_low_better(col):
                p_z = -p_z
            player_norm.append(min(max(p_z * 25 + 50, 0), 100))

        team_norm.append(50)

    return player_norm, team_norm


def calc_overall_ranking(df: pd.DataFrame,
                         metric_cols: list,
                         name_col: str) -> pd.DataFrame:
    """
    全選手の総合スコア・順位を計算して返す。
    各指標をZスコア化して平均し、100点満点に変換。
    """
    if not metric_cols:
        return pd.DataFrame()

    z_df = calc_z_scores(df, metric_cols)

    # 有効列（std > 0）のみ平均
    valid_cols = [c for c in metric_cols
                  if df[c].std(skipna=True) > 0]

    if not valid_cols:
        overall = pd.Series(50.0, index=df.index)
    else:
        overall = z_df[valid_cols].mean(axis=1, skipna=True)
        # Zスコア平均 → 0〜100スケール（平均50, ±2σ=0〜100）
        overall = (overall * 25 + 50).clip(0, 100)

    ranking_df = pd.DataFrame({
        name_col:     df[name_col].values,
        "総合スコア": overall.round(1).values,
    })

    # 各指標のZスコアも付加
    for col in metric_cols:
        std = df[col].std(skipna=True)
        if std > 0:
            ranking_df[col + "_z"] = z_df[col].round(2).values
        else:
            ranking_df[col + "_z"] = 0.0

    ranking_df = ranking_df.sort_values("総合スコア", ascending=False)
    ranking_df.insert(0, "順位", range(1, len(ranking_df) + 1))
    ranking_df = ranking_df.reset_index(drop=True)

    return ranking_df