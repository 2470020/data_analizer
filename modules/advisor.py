import pandas as pd
import json
import re

LOW_IS_BETTER_KEYWORDS = ["走(秒)", "タイム", "秒", "run_", "_s"]


def _is_low_better(col_name: str) -> bool:
    return any(kw.lower() in col_name.lower()
               for kw in LOW_IS_BETTER_KEYWORDS)


def _calc_z(player_val, mean: float, std: float, col_name: str):
    if pd.isna(player_val) or std <= 0:
        return None
    z = (float(player_val) - float(mean)) / float(std)
    return -z if _is_low_better(col_name) else z


def generate_advice(player_data: pd.Series,
                    team_stats: pd.DataFrame,
                    metric_cols: list) -> list:
    advice_list = []

    for col in metric_cols:
        player_val = player_data[col]
        mean       = team_stats.loc[col, "チーム平均"]
        std        = team_stats.loc[col, "標準偏差"]
        z          = _calc_z(player_val, float(mean), float(std), col)

        if z is None or pd.isna(player_val):
            advice_list.append({
                "指標":       col,
                "判定":       "-",
                "選手値":     "-",
                "チーム平均": round(float(mean), 2),
                "Zスコア":    "-",
                "コメント":   "データなし（null値または外れ値として除外）"
            })
            continue

        if z >= 1.0:
            status  = "優秀"
            comment = "チーム内でトップクラスの数値です。この強みを活かしたトレーニングを継続してください。"
        elif z >= 0.0:
            status  = "平均以上"
            comment = "チーム平均を上回っています。さらに伸ばせる余地があります。"
        elif z >= -1.0:
            status  = "要強化"
            comment = "チーム平均をやや下回っています。重点的なトレーニングを推奨します。"
        else:
            status  = "重点課題"
            comment = "チーム内で改善が特に必要な項目です。専門コーチへの相談を検討してください。"

        advice_list.append({
            "指標":       col,
            "判定":       status,
            "選手値":     round(float(player_val), 2),
            "チーム平均": round(float(mean), 2),
            "Zスコア":    round(z, 2),
            "コメント":   comment
        })

    return advice_list


def find_ideal_player(df: pd.DataFrame,
                      player_data: pd.Series,
                      team_stats: pd.DataFrame,
                      metric_cols: list,
                      name_col: str) -> dict:
    """
    対象選手に最も近い「理想モデル選手」をチーム内から探す。
    各指標のZスコア差の二乗和が最小の選手を返す。
    """
    player_name = str(player_data[name_col])

    # 対象選手以外
    others = df[df[name_col].astype(str) != player_name].copy()
    if others.empty:
        return {}

    valid_cols = [c for c in metric_cols
                  if team_stats.loc[c, "標準偏差"] > 0]
    if not valid_cols:
        return {}

    # 対象選手のZスコアベクトル
    player_z = {}
    for col in valid_cols:
        mean = float(team_stats.loc[col, "チーム平均"])
        std  = float(team_stats.loc[col, "標準偏差"])
        val  = player_data[col]
        if pd.isna(val):
            player_z[col] = 0.0
        else:
            z = (float(val) - mean) / std
            player_z[col] = -z if _is_low_better(col) else z

    # 各選手との距離を計算
    min_dist    = float("inf")
    ideal_row   = None
    ideal_name  = None

    for _, row in others.iterrows():
        dist = 0.0
        for col in valid_cols:
            mean = float(team_stats.loc[col, "チーム平均"])
            std  = float(team_stats.loc[col, "標準偏差"])
            val  = row[col]
            if pd.isna(val):
                rz = 0.0
            else:
                z = (float(val) - mean) / std
                rz = -z if _is_low_better(col) else z
            # 理想は自分より上の選手なので、自分より低い指標は重みを大きく
            gap = rz - player_z[col]
            dist += gap ** 2

        if dist < min_dist:
            min_dist   = dist
            ideal_row  = row
            ideal_name = str(row[name_col])

    if ideal_row is None:
        return {}

    # 比較データを構築
    comparison = {}
    for col in metric_cols:
        pv = player_data[col]
        iv = ideal_row[col]
        mean = float(team_stats.loc[col, "チーム平均"])
        std  = float(team_stats.loc[col, "標準偏差"])

        pz = _calc_z(pv, mean, std, col)
        iz = _calc_z(iv, mean, std, col)

        comparison[col] = {
            "選手値":     round(float(pv), 2) if not pd.isna(pv) else None,
            "理想値":     round(float(iv), 2) if not pd.isna(iv) else None,
            "選手Z":      round(pz, 2) if pz is not None else None,
            "理想Z":      round(iz, 2) if iz is not None else None,
            "差分":       round((float(iv) - float(pv)), 2)
                          if (not pd.isna(pv) and not pd.isna(iv)) else None,
        }

    return {
        "理想選手名": ideal_name,
        "比較":       comparison,
    }


def generate_ai_comment(player_name: str,
                        ideal_info: dict,
                        advice_list: list,
                        metric_cols: list) -> str:
    """
    Anthropic APIを使って理想モデル選手との比較コメントを生成する。
    APIキーがない場合はルールベースのコメントを返す。
    """
    if not ideal_info:
        return "比較できる選手データがありません。"

    ideal_name  = ideal_info["理想選手名"]
    comparison  = ideal_info["比較"]

    # 強み・弱みの上位3つを抽出
    diffs = []
    for col, d in comparison.items():
        if d["差分"] is not None:
            diffs.append((col, d["差分"], d["選手Z"], d["理想Z"]))

    strengths = sorted(
        [(c, dz, iz) for c, diff, dz, iz in diffs if (iz or 0) > (dz or 0)],
        key=lambda x: (x[2] or 0), reverse=True
    )[:3]
    weaknesses = sorted(
        [(c, dz, iz) for c, diff, dz, iz in diffs if (iz or 0) > (dz or 0)],
        key=lambda x: ((x[2] or 0) - (x[1] or 0))
    )[:3]

    # プロンプト構築
    prompt = f"""あなたはスポーツ科学の専門コーチです。
以下のデータをもとに、選手「{player_name}」への具体的なアドバイスを日本語で生成してください。

【目標モデル選手】{ideal_name}

【主な差分（改善余地が大きい指標）】
"""
    for col, dz, iz in weaknesses:
        d = comparison[col]
        prompt += f"- {col}：選手={d['選手値']}、モデル={d['理想値']}（Zスコア差: {round((iz or 0)-(dz or 0), 2)}）\n"

    prompt += "\n【現在の強み（上位指標）】\n"
    for col, dz, iz in strengths:
        d = comparison[col]
        prompt += f"- {col}：選手={d['選手値']}、モデル={d['理想値']}\n"

    prompt += """
以下の形式でJSON形式のみ出力してください（前置き・説明不要）:
{
  "総評": "2〜3文で選手の現状と方向性",
  "重点改善": ["具体的な改善アドバイス1", "具体的な改善アドバイス2", "具体的な改善アドバイス3"],
  "強み活用": "強みをどう活かすか1〜2文"
}"""

    try:
        import requests
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model":      "claude-sonnet-4-6",
                "max_tokens": 1000,
                "messages":   [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if response.status_code == 200:
            text = response.json()["content"][0]["text"]
            # JSONを抽出
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return data
    except Exception:
        pass

    # フォールバック：ルールベース
    fb_improvements = []
    for col, dz, iz in weaknesses[:3]:
        d = comparison[col]
        gap = round((iz or 0) - (dz or 0), 2)
        fb_improvements.append(
            f"{col}はモデル選手より{abs(d['差分'] or 0):.2f}の差があります。集中的なトレーニングを推奨します。"
        )

    strength_text = ""
    if strengths:
        s_names = [c for c, _, _ in strengths[:2]]
        strength_text = f"{', '.join(s_names)}はチーム内でも高水準です。この強みを軸にトレーニングを設計してください。"

    return {
        "総評":     f"目標モデルは{ideal_name}です。全体的なパフォーマンス向上に向けて、重点指標の改善が必要です。",
        "重点改善": fb_improvements if fb_improvements else ["データが不足しています。"],
        "強み活用": strength_text or "強みデータを確認してください。"
    }