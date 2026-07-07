import pandas as pd
from modules.analysis import calc_z_scores


def calc_metric_ranking(df: pd.DataFrame,
                        name_col: str,
                        metric_col: str) -> pd.DataFrame:
    """
    1種目について、全選手の順位表を返す。
    「低い方が良い」種目（タイム系）は analysis.calc_z_scores 内の
    補正により自動的に向きが揃えられる。
    同じ値（同じZスコア）の選手は同順位とし、次の順位は人数分スキップする
    （例：1位が2人なら、次は3位）。

    返り値カラム： 順位, 名前, 値, Zスコア
    """
    z_df = calc_z_scores(df, [metric_col])

    rank_df = pd.DataFrame({
        "名前":     df[name_col].values,
        "値":       df[metric_col].values,
        "Zスコア":  z_df[metric_col].values
    })

    rank_df = rank_df.dropna(subset=["値"])
    rank_df["順位"] = rank_df["Zスコア"].rank(method="min", ascending=False).astype(int)
    rank_df = rank_df.sort_values("順位").reset_index(drop=True)
    rank_df = rank_df[["順位", "名前", "値", "Zスコア"]]

    return rank_df


def calc_group_ranking(df: pd.DataFrame,
                       name_col: str,
                       metric_cols_in_group: list) -> pd.DataFrame:
    """
    同一グループ（単位が同じ種目群、または指定した種目群）の
    平均Zスコアで順位表を返す。
    グループ内の欠損種目は無視して平均を取る。
    同じ平均Zスコアの選手は同順位とし、次の順位は人数分スキップする。

    返り値カラム： 順位, 名前, 平均Zスコア
    """
    if not metric_cols_in_group:
        return pd.DataFrame(columns=["順位", "名前", "平均Zスコア"])

    z_df = calc_z_scores(df, metric_cols_in_group)

    avg_z = z_df[metric_cols_in_group].mean(axis=1, skipna=True)

    rank_df = pd.DataFrame({
        "名前":      df[name_col].values,
        "平均Zスコア": avg_z.values
    })

    rank_df = rank_df.dropna(subset=["平均Zスコア"])
    rank_df["順位"] = rank_df["平均Zスコア"].rank(method="min", ascending=False).astype(int)
    rank_df = rank_df.sort_values("順位").reset_index(drop=True)
    rank_df = rank_df[["順位", "名前", "平均Zスコア"]]

    return rank_df


def calc_overall_ranking(df: pd.DataFrame,
                         name_col: str,
                         all_metric_cols: list) -> pd.DataFrame:
    """
    選択中の全種目を対象にした平均Zスコアで、総合順位表を返す。
    同じ総合Zスコアの選手は同順位とする。

    返り値カラム： 順位, 名前, 総合Zスコア
    """
    return calc_group_ranking(df, name_col, all_metric_cols).rename(
        columns={"平均Zスコア": "総合Zスコア"}
    )


def calc_type_group_ranking(df: pd.DataFrame,
                            name_col: str,
                            metric_cols: list,
                            cluster_df: pd.DataFrame,
                            cluster_id: int) -> pd.DataFrame:
    """
    指定したクラスタ（似たタイプのグループ）に所属する選手だけを対象に、
    選択中の測定項目の平均Zスコアで順位表を返す。

    返り値カラム： 順位, 名前, 平均Zスコア
    """
    if cluster_df.empty:
        return pd.DataFrame(columns=["順位", "名前", "平均Zスコア"])

    member_names = (cluster_df.loc[cluster_df["クラスタ"] == cluster_id, "名前"]
                     .astype(str).str.strip().values)

    df_in_cluster = df[
        df[name_col].astype(str).str.strip().isin(member_names)
    ].reset_index(drop=True)

    if df_in_cluster.empty:
        return pd.DataFrame(columns=["順位", "名前", "平均Zスコア"])

    return calc_group_ranking(df_in_cluster, name_col, metric_cols)


def get_player_rank(rank_df: pd.DataFrame,
                    name_col_in_rank: str,
                    player_name: str) -> dict:
    """
    順位表の中から特定選手の行を取り出す。
    見つからなければ None を返す。
    """
    if rank_df.empty or name_col_in_rank not in rank_df.columns:
        return None
    match = rank_df[rank_df[name_col_in_rank].astype(str).str.strip()
                     == str(player_name).strip()]
    if match.empty:
        return None
    row = match.iloc[0]
    return row.to_dict()