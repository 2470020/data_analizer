import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from modules.analysis import calc_z_scores


def cluster_players_by_type(df: pd.DataFrame,
                             name_col: str,
                             metric_cols: list,
                             n_clusters: int = 3,
                             random_state: int = 42) -> pd.DataFrame:
    """
    選択中の測定項目のZスコアをもとに、選手を似たタイプ同士で
    グループ分け（クラスタリング）する。
    欠損値はチーム平均（Zスコアなので0）で補完してから計算する。

    返り値カラム： 名前, クラスタ
    """
    if not metric_cols:
        return pd.DataFrame(columns=["名前", "クラスタ"])

    z_df = calc_z_scores(df, metric_cols)
    features_df = z_df[metric_cols].fillna(0.0)

    valid_mask = df[name_col].notna().values
    names = df.loc[valid_mask, name_col].values
    features = features_df.loc[valid_mask].values

    n_players = len(names)
    if n_players == 0:
        return pd.DataFrame(columns=["名前", "クラスタ"])

    # 人数がグループ数より少ない場合は自動調整
    k = max(1, min(n_clusters, n_players))

    km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    labels = km.fit_predict(features)

    cluster_df = pd.DataFrame({
        "名前":   names,
        "クラスタ": labels
    })

    return cluster_df


def get_cluster_summary(cluster_df: pd.DataFrame) -> pd.DataFrame:
    """
    クラスタごとの人数を集計して返す。
    返り値カラム： クラスタ, 人数
    """
    if cluster_df.empty:
        return pd.DataFrame(columns=["クラスタ", "人数"])

    summary = (cluster_df.groupby("クラスタ")
               .size()
               .reset_index(name="人数")
               .sort_values("クラスタ")
               .reset_index(drop=True))
    return summary