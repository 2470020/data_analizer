import pandas as pd
import io
import re
from modules.config import NON_METRIC_COLS

CHUNK_SIZE = 500


def _clean_name(val) -> str:
    """
    選手名の表記ゆれを自動クレンジングする。
    全角・半角スペースの重複を除去し、前後トリム。
    """
    if pd.isna(val):
        return val
    s = str(val)
    s = re.sub(r'[\u3000\s]+', ' ', s)  # 全角スペース→半角、重複スペース→1つ
    return s.strip()


def _detect_unit_row(uploaded_file) -> bool:
    """2行目が単位行（秒・cm等）かどうかを判定する"""
    uploaded_file.seek(0)
    preview = pd.read_excel(uploaded_file, engine="openpyxl",
                            header=None, nrows=3)
    uploaded_file.seek(0)

    if len(preview) < 2:
        return False

    second_row = preview.iloc[1].dropna()
    if len(second_row) == 0:
        return True

    numeric_count = 0
    for val in second_row:
        try:
            float(str(val))
            numeric_count += 1
        except (ValueError, TypeError):
            pass

    return numeric_count == 0


def load_excel(uploaded_file, chunk_size: int = CHUNK_SIZE) -> pd.DataFrame:
    """
    xlsx・csv両対応。
    2行目の単位行を自動検出してスキップ。
    全列を数値変換試行。
    選手名の表記ゆれを自動クレンジング。
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        uploaded_file.seek(0)
        preview = pd.read_csv(uploaded_file, nrows=2,
                              encoding="utf-8-sig", header=0)
        uploaded_file.seek(0)

        has_unit_row = False
        if len(preview) >= 1:
            second_row = preview.iloc[0].dropna()
            numeric_count = 0
            for val in second_row:
                try:
                    float(str(val))
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass
            has_unit_row = numeric_count == 0

        chunks   = []
        skiprows = [1] if has_unit_row else None
        uploaded_file.seek(0)
        reader = pd.read_csv(
            uploaded_file,
            encoding="utf-8-sig",
            chunksize=chunk_size,
            skiprows=skiprows
        )
        for chunk in reader:
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)

    else:
        has_unit_row = _detect_unit_row(uploaded_file)
        skiprows     = [1] if has_unit_row else None
        uploaded_file.seek(0)
        df = pd.read_excel(
            uploaded_file,
            engine="openpyxl",
            skiprows=skiprows
        )

    df = df.dropna(how="all").reset_index(drop=True)

    # 数値変換
    for col in df.columns:
        if col in NON_METRIC_COLS:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() >= df[col].notna().sum() * 0.5:
            df[col] = converted

    # 選手ID・測定日の自動付与
    if "選手ID" not in df.columns and "student_id" not in df.columns:
        df.insert(0, "選手ID",
                  [f"P{str(i+1).zfill(3)}" for i in range(len(df))])
    if "測定日" not in df.columns:
        df["測定日"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    return df


def clean_name_column(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
    """選手名列の表記ゆれをクレンジングする"""
    if name_col in df.columns:
        df = df.copy()
        df[name_col] = df[name_col].apply(_clean_name)
    return df


def get_column_names(uploaded_file) -> list:
    filename = uploaded_file.name.lower()
    uploaded_file.seek(0)

    if filename.endswith(".csv"):
        preview = pd.read_csv(uploaded_file, nrows=0, encoding="utf-8-sig")
    else:
        preview = pd.read_excel(uploaded_file, engine="openpyxl", nrows=0)

    uploaded_file.seek(0)
    return preview.columns.tolist()


def guess_name_column(columns: list) -> str:
    priority_keywords = [
        "選手名", "氏名", "名前", "student_id",
        "name", "id", "ID", "選手ID"
    ]
    for kw in priority_keywords:
        matches = [c for c in columns if kw.lower() in c.lower()]
        if matches:
            return matches[0]
    return columns[0]


def get_player_list(df: pd.DataFrame, name_col: str) -> list:
    return df[name_col].dropna().astype(str).tolist()


def get_metric_columns(df: pd.DataFrame,
                       name_col: str = "選手名") -> list:
    exclude = set(NON_METRIC_COLS) | {name_col}
    result  = []
    for col in df.columns:
        if col in exclude:
            continue
        if str(col).strip() in exclude:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            result.append(col)
    return result


def clean_dataframe(df: pd.DataFrame,
                    metric_cols: list,
                    name_col: str = "選手名") -> tuple:
    """null値・外れ値（±3σ）を処理する"""
    df     = df.copy()
    report = {}

    for col in metric_cols:
        mean = df[col].mean(skipna=True)
        std  = df[col].std(skipna=True)
        if std > 0:
            outlier_mask = (df[col] - mean).abs() > 3 * std
            if outlier_mask.any():
                if name_col in df.columns:
                    outlier_players = df.loc[outlier_mask, name_col].tolist()
                else:
                    outlier_players = [
                        f"行{i}" for i in df[outlier_mask].index.tolist()
                    ]
                report[col]               = outlier_players
                df.loc[outlier_mask, col] = pd.NA

    return df, report


def create_sample_excel() -> bytes:
    data = {
        "選手名":         ["田中 太郎", "鈴木 一郎", "佐藤 健",
                           "山田 花子", "中村 勇"],
        "背番号":         [10, 7, 3, 5, 1],
        "ポジション":     ["FW", "MF", "DF", "MF", "GK"],
        "測定日":         ["2024-04-01"] * 5,
        "ジャンプ高(cm)": [65, 72, 58, 70, 63],
        "30m走(秒)":      [4.1, 3.9, 4.4, 4.0, 4.2],
        "握力(kg)":       [52, 48, 55, 45, 50],
        "最大酸素摂取量": [58, 62, 54, 60, 56],
        "体幹スコア":     [78, 85, 70, 88, 75],
    }
    df     = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="測定データ")
    return output.getvalue()