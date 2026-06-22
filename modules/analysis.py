import pandas as pd
import numpy as np

LOW_IS_BETTER_KEYWORDS = ["走(秒)", "タイム", "秒"]


def _is_low_better(col_name: str) -> bool:
    return any(kw in col_name for kw in LOW_IS_BETTER_KEYWORDS)


def calc_team_stats(df: pd.DataFrame, metric_cols: list) -> pd.DataFrame:
    """null値を除いてチーム統計を計算"""
    stats         = df[metric_cols].agg(["mean", "std"]).T
    stats.columns = ["チーム平均", "標準偏差"]
    return stats


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
                    name_col: str = "選手名") -> pd.Series:
    return df[df[name_col] == player_name].iloc[0]


def normalize_for_radar(player_data: pd.Series,
                        team_stats: pd.DataFrame,
                        metric_cols: list) -> tuple:
    """null値の項目は50（平均）として扱う"""
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