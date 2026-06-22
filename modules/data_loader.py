import pandas as pd
import io

NON_METRIC_COLS = ["選手名", "背番号", "氏名", "ID", "選手ID", "ポジション", "測定日"]

CHUNK_SIZE = 500  # 1回に読み込む行数


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
        # 全行数を取得
        uploaded_file.seek(0)
        df_full    = pd.read_excel(uploaded_file, engine="openpyxl",
                                   header=None)
        total_rows = len(df_full) - 1  # ヘッダー除く

        # チャンク分割読み込み
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

    # 選手ID・測定日の自動付与
    if "選手ID" not in df.columns:
        df.insert(0, "選手ID",
                  [f"P{str(i+1).zfill(3)}" for i in range(len(df))])
    if "測定日" not in df.columns:
        df["測定日"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    return df


def get_player_list(df: pd.DataFrame, name_col: str = "選手名") -> list:
    return df[name_col].dropna().tolist()


def get_metric_columns(df: pd.DataFrame) -> list:
    return [
        col for col in df.select_dtypes(include="number").columns
        if col not in NON_METRIC_COLS
    ]


def clean_dataframe(df: pd.DataFrame, metric_cols: list) -> tuple:
    """
    null値・外れ値（±3σ）を処理する。
    外れ値はNaNに置換し、レポートとして返す。
    """
    df     = df.copy()
    report = {}

    for col in metric_cols:
        mean = df[col].mean(skipna=True)
        std  = df[col].std(skipna=True)
        if std > 0:
            outlier_mask = (df[col] - mean).abs() > 3 * std
            if outlier_mask.any():
                outlier_players      = df.loc[outlier_mask, "選手名"].tolist()
                report[col]          = outlier_players
                df.loc[outlier_mask, col] = pd.NA

    return df, report


def create_sample_excel() -> bytes:
    data = {
        "選手名":         ["田中 太郎", "鈴木 一郎", "佐藤 健", "山田 花子", "中村 勇"],
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