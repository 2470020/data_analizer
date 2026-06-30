import pandas as pd
import numpy as np

LOW_IS_BETTER_KEYWORDS = ["走(秒)", "タイム", "秒", "run_", "_s"]

UNIT_PATTERNS = {
    "cm":  ["cm", "ｃｍ"],
    "kg":  ["kg", "ｋｇ"],
    "秒":  ["秒", "_s", "(s)", "（秒）"],
    "m/s": ["m/s", "ｍ/ｓ"],
    "回":  ["回"],
    "点":  ["点", "スコア", "score"],
}


def _is_low_better(col_name: str) -> bool:
    return any(kw.lower() in col_name.lower()
               for kw in LOW_IS_BETTER_KEYWORDS)


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
                    name_col: str) -> pd.Series:
    return df[df[name_col].astype(str) == str(player_name)].iloc[0]


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


def normalize_value(val, mean: float, std: float, col_name: str):
    """
    単一値を0-100スケールに正規化する（z*25+50方式）。
    欠損 or 標準偏差0の場合はNoneを返す（呼び出し側で「欠測」として扱う）。
    """
    if pd.isna(val) or std == 0:
        return None
    z = (float(val) - float(mean)) / float(std)
    if _is_low_better(col_name):
        z = -z
    return min(max(z * 25 + 50, 0), 100)


def get_radar_data(player_data: pd.Series, team_stats: pd.DataFrame,
                   df: pd.DataFrame, metric_cols: list,
                   percentiles: tuple = (10, 90)) -> dict:
    """
    レーダーチャート描画に必要な情報をまとめて返す。

    - player_norm / team_norm : 0-100正規化値（描画用）
    - player_raw              : 選手の元の値（単位付き表示・ホバー用）
    - is_missing              : 欠損項目のフラグ（50に丸めて描画するが見た目で区別する）
    - z_scores                : 選手のZスコア（向き補正済み）
    - p_low / p_high          : チーム内パーセンタイル帯（向き補正済みで low<=high）
    - units                   : 各指標の単位
    """
    result = {
        "categories":  [], "player_norm": [], "player_raw": [],
        "team_norm":   [], "is_missing":  [], "z_scores":   [],
        "p_low":       [], "p_high":      [], "units":      [],
    }

    lo_pct, hi_pct = percentiles

    for col in metric_cols:
        mean = float(team_stats.loc[col, "チーム平均"])
        std  = float(team_stats.loc[col, "標準偏差"])
        val  = player_data[col]

        norm = normalize_value(val, mean, std, col)
        missing = norm is None
        if missing:
            norm = 50
            z = None
        else:
            z_raw = (float(val) - mean) / std if std > 0 else 0.0
            z = -z_raw if _is_low_better(col) else z_raw

        lo_val = df[col].quantile(lo_pct / 100)
        hi_val = df[col].quantile(hi_pct / 100)
        lo_n   = normalize_value(lo_val, mean, std, col)
        hi_n   = normalize_value(hi_val, mean, std, col)
        if lo_n is None: lo_n = 50
        if hi_n is None: hi_n = 50
        if _is_low_better(col):
            lo_n, hi_n = hi_n, lo_n

        result["categories"].append(col)
        result["player_norm"].append(norm)
        result["player_raw"].append(None if pd.isna(val) else round(float(val), 2))
        result["team_norm"].append(50)
        result["is_missing"].append(missing)
        result["z_scores"].append(None if z is None else round(z, 2))
        result["p_low"].append(round(min(lo_n, hi_n), 1))
        result["p_high"].append(round(max(lo_n, hi_n), 1))
        result["units"].append(extract_unit(col))

    return result


def extract_unit(col_name: str) -> str:
    """
    列名から単位を推定して返す。
    一致しなければ「その他」を返す。
    """
    col_lower = col_name.lower()
    for unit, patterns in UNIT_PATTERNS.items():
        for pat in patterns:
            if pat.lower() in col_lower:
                return unit
    return "その他"


def group_metrics_by_unit(metric_cols: list) -> dict:
    """
    測定項目を単位ごとにグループ分けする。
    返り値：{"cm": ["ジャンプ高(cm)", ...], "秒": [...], ...}
    """
    groups = {}
    for col in metric_cols:
        unit = extract_unit(col)
        groups.setdefault(unit, []).append(col)
    return groups