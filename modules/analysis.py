import pandas as pd
import numpy as np
from modules.config import LOW_IS_BETTER_KEYWORDS, UNIT_PATTERNS, is_low_better


def calc_team_stats(df: pd.DataFrame, metric_cols: list) -> pd.DataFrame:
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
            if is_low_better(col):
                z_df[col] = -z_df[col]
        else:
            z_df[col] = 0.0
    return z_df


def get_player_data(df: pd.DataFrame, player_name: str,
                    name_col: str) -> pd.Series:
    match = df[df[name_col].astype(str) == str(player_name)]
    if match.empty:
        return None
    return match.iloc[0]


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
            if is_low_better(col):
                p_z = -p_z
            player_norm.append(min(max(p_z * 25 + 50, 0), 100))

        team_norm.append(50)

    return player_norm, team_norm


def _percentile_rank(series: pd.Series, val) -> float:
    """
    series内でvalが位置するパーセンタイル順位（0-100）を返す。
    同値は0.5件分として扱う（中央値的な扱い、tie='average'相当）。
    """
    s = series.dropna().to_numpy(dtype=float)
    if len(s) == 0 or pd.isna(val):
        return None
    val = float(val)
    less  = (s < val).sum()
    equal = (s == val).sum()
    return float((less + 0.5 * equal) / len(s) * 100)


def get_radar_data(player_data: pd.Series, team_stats: pd.DataFrame,
                   df: pd.DataFrame, metric_cols: list,
                   percentiles: tuple = (10, 90)) -> dict:
    """
    レーダーチャート描画に必要な情報をまとめて返す。

    正規化はチーム内でのパーセンタイル順位（0-100）を使用する。
    平均・標準偏差ベースのZスコア方式と異なり、分布の形や外れ値の
    影響を受けにくく、±2σ相当でのクリッピングも発生しない。

    - player_norm / team_norm : 0-100パーセンタイル順位（描画用、向き補正済み）
    - player_raw              : 選手の元の値（単位付き表示・ホバー用）
    - is_missing              : 欠損項目のフラグ（50に丸めて描画するが見た目で区別する）
    - percentile              : 選手のパーセンタイル順位（向き補正済み、表示用）
    - units                   : 各指標の単位
    """
    result = {
        "categories":  [], "player_norm": [], "player_raw": [],
        "team_norm":   [], "is_missing":  [], "percentile":  [],
        "units":       [],
    }

    for col in metric_cols:
        series = df[col]
        val    = player_data[col]
        mean   = float(team_stats.loc[col, "チーム平均"])
        low_better = is_low_better(col)

        pct = _percentile_rank(series, val)
        missing = pct is None
        if not missing and low_better:
            pct = 100 - pct
        norm = 50 if missing else pct

        mean_pct = _percentile_rank(series, mean)
        if mean_pct is not None and low_better:
            mean_pct = 100 - mean_pct
        team_norm = 50 if mean_pct is None else mean_pct

        result["categories"].append(col)
        result["player_norm"].append(norm)
        result["player_raw"].append(None if pd.isna(val) else round(float(val), 2))
        result["team_norm"].append(round(team_norm, 1))
        result["is_missing"].append(missing)
        result["percentile"].append(None if missing else round(pct, 1))
        result["units"].append(extract_unit(col))

    return result


def extract_unit(col_name: str) -> str:
    col_lower = col_name.lower()
    for unit, patterns in UNIT_PATTERNS.items():
        for pat in patterns:
            if pat.lower() in col_lower:
                return unit
    return "その他"


def group_metrics_by_unit(metric_cols: list) -> dict:
    groups = {}
    for col in metric_cols:
        unit = extract_unit(col)
        groups.setdefault(unit, []).append(col)
    return groups