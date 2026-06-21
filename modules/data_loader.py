import pandas as pd
import io

# 数値列として扱わない列名
NON_METRIC_COLS = ["選手名", "背番号", "氏名", "ID", "ポジション"]

def load_excel(uploaded_file) -> pd.DataFrame:
    """アップロードされたExcelをDataFrameに変換"""
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    return df

def get_player_list(df: pd.DataFrame, name_col: str = "選手名") -> list:
    return df[name_col].dropna().tolist()

def get_metric_columns(df: pd.DataFrame) -> list:
    """数値列のみ自動抽出（選手名・背番号等を除外）"""
    return [
        col for col in df.select_dtypes(include="number").columns
        if col not in NON_METRIC_COLS
    ]

def create_sample_excel() -> bytes:
    """サンプルExcelを生成してバイト列で返す"""
    data = {
        "選手名": ["田中 太郎", "鈴木 一郎", "佐藤 健", "山田 花子", "中村 勇"],
        "背番号": [10, 7, 3, 5, 1],
        "ジャンプ高(cm)": [65, 72, 58, 70, 63],
        "30m走(秒)": [4.1, 3.9, 4.4, 4.0, 4.2],
        "握力(kg)": [52, 48, 55, 45, 50],
        "最大酸素摂取量": [58, 62, 54, 60, 56],
        "体幹スコア": [78, 85, 70, 88, 75],
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="測定データ")
    return output.getvalue()