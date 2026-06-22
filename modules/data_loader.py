import pandas as pd
import io

NON_METRIC_COLS = ["選手名", "背番号", "氏名", "ID", "選手ID",
                   "ポジション", "測定日", "student_id", "name",
                   "Name", "StudentID"]

CHUNK_SIZE = 500


def load_excel(uploaded_file, chunk_size: int = CHUNK_SIZE) -> pd.DataFrame:
    """
    大きいファイルをチャンク単位で分割読み込みし結合して返す。
    xlsx・csv両対応。
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
        uploaded_file.seek(0)
        df_full    = pd.read_excel(uploaded_file, engine="openpyxl",
                                   header=None)
        total_rows = len(df_full) - 1

        chunks = []
        for skip in range(0, total_rows, chunk_size):
            uploaded_file.seek(0)
            chunk = pd.read_excel(
                uploaded_file,
                engine="openpyxl",
                skiprows=range(1, skip + 1),
                nrows=chunk_size
            )
            chunks.append(chunk)

        df = pd.concat(chunks, ignore_index=True)

    if "選手ID" not in df.columns and "student_id" not in df.columns:
        df.insert(0, "選手ID",
                  [f"P{str(i+1).zfill(3)}" for i in range(len(df))])
    if "測定日" not in df.columns:
        df["測定日"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    return df


def get_column_names(uploaded_file) -> list:
    """
    ファイルの列名だけを軽量に先読みして返す。
    アップロード後のサイドバー候補表示に使用。
    """
    filename = uploaded_file.name.lower()
    uploaded_file.seek(0)

    if filename.endswith(".csv"):
        preview = pd.read_csv(uploaded_file, nrows=0, encoding="utf-8-sig")
    else:
        preview = pd.read_excel(uploaded_file, engine="openpyxl", nrows=0)

    uploaded_file.seek(0)
    return preview.columns.tolist()


def guess_name_column(columns: list) -> str:
    """
    列名リストから選手識別列を自動推定する。
    優先キーワード順に検索し、見つからなければ先頭列を返す。
    """
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
    数値列のみ抽出。NON_METRIC_COLSと選択された選手名列を除外。
    """
    exclude = set(NON_METRIC_COLS) | {name_col}
    return [
        col for col in df.select_dtypes(include="number").columns
        if col not in exclude
    ]


def clean_dataframe(df: pd.DataFrame,
                    metric_cols: list,
                    name_col: str = "選手名") -> tuple:
    """
    null値・外れ値（±3σ）を処理する。
    name_colが存在しない場合はインデックス番号で代替。
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