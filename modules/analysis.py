import re

UNIT_PATTERNS = {
    "cm":  ["cm", "ｃｍ"],
    "kg":  ["kg", "ｋｇ"],
    "秒":  ["秒", "_s", "(s)", "（秒）"],
    "m/s": ["m/s", "ｍ/ｓ"],
    "回":  ["回"],
    "点":  ["点", "スコア", "score"],
}


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