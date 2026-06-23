import pandas as pd
import io

NON_METRIC_COLS = ["選手名", "背番号", "氏名", "ID", "選手ID",
                   "ポジション", "測定日", "student_id", "name",
                   "Name", "StudentID", "id", "No", "NO", "番号",
                   "性別", "gender", "Gender", "グループ", "group"]

CHUNK_SIZE = 500


def _skip_unit_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    2行目以降に単位行（数値でない行）が混入している場合に除去する。
    例：「（秒）」「（cm）」などの行をスキップ。
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return df

    mask = df[numeric_cols].apply(
        lambda row: row.notna().any(), axis=1
    )
    return df[mask].reset_index(drop=True)


def _detect_unit_row(preview: pd.DataFrame) -> bool:
    """
    2行目が単位行かどうかを判定する。
    
    判定ロジック:
    1. 全列のうち文字列値を持つ列の数をカウント
    2. 半数以上の列が文字列（単位っぽい値）なら単位行とみなす
    3. または、非数値列（ID・性別など除く）が1つでも文字列を含めば単位行とみなす
    """
    if len(preview) < 1:
        return False

    row = preview.iloc[0]

    # 各セルの値を確認
    str_count = 0
    total_non_empty = 0
    for val in row:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        total_non_empty += 1
        if isinstance(val, str):
            str_count += 1

    if total_non_empty == 0:
        return False

    # 半数以上が文字列 → 単位行
    return str_count / total_non_empty >= 0.5


def load_excel(uploaded_file, chunk_size: int = CHUNK_SIZE) -> pd.DataFrame:
    """
    大きいファイルをチャンク単位で分割読み込みし結合して返す。
    xlsx・csv両対応。2行目の単位行を自動スキップ。
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        chunks = []
        uploaded_file.seek(0)
        reader = pd.read_csv(
            uploaded_file,
            encoding="utf-8-sig",
            chunksize=chunk_size
        )
        for chunk in reader:
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)

    else:
        # 先頭2行を確認して単位行があるか判定
        uploaded_file.seek(0)
        preview = pd.read_excel(uploaded_file, engine="openpyxl", nrows=1)

        has_unit_row = _detect_unit_row(preview)

        uploaded_file.seek(0)
        df_full    = pd.read_excel(uploaded_file, engine="openpyxl",
                                   header=None)
        total_rows = len(df_full) - 1
        if has_unit_row:
            total_rows -= 1  # 単位行分を引く

        # チャンク読み込み
        chunks = []
        skip_extra = 2 if has_unit_row else 1  # ヘッダー行+単位行をスキップ

        for skip in range(0, total_rows, chunk_size):
            uploaded_file.seek(0)
            chunk = pd.read_excel(
                uploaded_file,
                engine="openpyxl",
                skiprows=range(1, skip + skip_extra),
                nrows=chunk_size,
                header=0
            )
            # 単位行が混入している場合に除去
            if has_unit_row and len(chunk) > 0:
                chunk = chunk.iloc[1:] if skip == 0 else chunk
            chunks.append(chunk)

        df = pd.concat(chunks, ignore_index=True)

    # 完全に空の行を除去
    df = df.dropna(how="all").reset_index(drop=True)

    if "選手ID" not in df.columns and "student_id" not in df.columns:
        df.insert(0, "選手ID",
                  [f"P{str(i+1).zfill(3)}" for i in range(len(df))])
    if "測定日" not in df.columns:
        df["測定日"] = pd.Timestamp.today().strftime("%Y-%m-%d")

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
    """
    数値列のみ抽出。
    NON_METRIC_COLSと選択されたname_colを除外。
    """
    exclude = set(NON_METRIC_COLS) | {name_col}

    result = []
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
    """
    null値・外れ値（±3σ）を処理する。
    """
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