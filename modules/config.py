"""
指標の「方向性」を一元管理するモジュール。
ここだけ修正すれば全モジュールに反映される。
"""

# 値が低いほど良い指標のキーワード
LOW_IS_BETTER_KEYWORDS = [
    "走(秒)", "タイム", "秒", "run_", "_s",
    "time", "Time", "TIME"
]

# 数値列として扱わない列名（非分析列）
NON_METRIC_COLS = [
    "選手名", "背番号", "氏名", "ID", "選手ID",
    "ポジション", "測定日", "student_id", "name",
    "Name", "StudentID", "id", "No", "NO", "番号",
    "性別", "gender", "Gender", "グループ", "group"
]

# 単位パターン（レーダーチャートのグループ分けに使用）
UNIT_PATTERNS = {
    "cm":  ["cm", "ｃｍ"],
    "kg":  ["kg", "ｋｇ"],
    "秒":  ["秒", "_s", "(s)", "（秒）"],
    "m/s": ["m/s", "ｍ/ｓ"],
    "回":  ["回"],
    "点":  ["点", "スコア", "score"],
}


def is_low_better(col_name: str) -> bool:
    """値が低いほど良い指標かどうかを判定する"""
    return any(kw.lower() in col_name.lower()
               for kw in LOW_IS_BETTER_KEYWORDS)