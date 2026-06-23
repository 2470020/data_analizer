import pandas as pd
import json
import re

LOW_IS_BETTER_KEYWORDS = ["走(秒)", "タイム", "秒", "run_", "_s", "10m", "20m"]


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
    対象選手に最も近い「目標モデル選手」をチーム内から探す。
    返り値の理想選手名は番号・IDを伏せた形式で返す。
    """
    player_name = str(player_data[name_col])
    others = df[df[name_col].astype(str) != player_name].copy()
    if others.empty:
        return {}

    valid_cols = [c for c in metric_cols
                  if team_stats.loc[c, "標準偏差"] > 0]
    if not valid_cols:
        return {}

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

    min_dist   = float("inf")
    ideal_row  = None
    ideal_name = None

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
            gap = rz - player_z[col]
            dist += gap ** 2

        if dist < min_dist:
            min_dist   = dist
            ideal_row  = row
            ideal_name = str(row[name_col])

    if ideal_row is None:
        return {}

    comparison = {}
    for col in metric_cols:
        pv = player_data[col]
        iv = ideal_row[col]
        mean = float(team_stats.loc[col, "チーム平均"])
        std  = float(team_stats.loc[col, "標準偏差"])
        pz = _calc_z(pv, mean, std, col)
        iz = _calc_z(iv, mean, std, col)
        comparison[col] = {
            "選手値": round(float(pv), 2) if not pd.isna(pv) else None,
            "理想値": round(float(iv), 2) if not pd.isna(iv) else None,
            "選手Z":  round(pz, 2) if pz is not None else None,
            "理想Z":  round(iz, 2) if iz is not None else None,
            "差分":   round((float(iv) - float(pv)), 2)
                      if (not pd.isna(pv) and not pd.isna(iv)) else None,
        }

    return {
        "理想選手名":     ideal_name,       # 内部処理用（表示しない）
        "表示用目標":     "目標選手",        # UI表示用（番号・名前を伏せる）
        "比較":           comparison,
    }


def generate_trainer_comment(player_name: str,
                             ideal_info: dict,
                             advice_list: list,
                             metric_cols: list) -> dict:
    """
    AIトレーナーとして、選手への丁寧で的確なコーチングコメントを生成する。
    目標選手の名前・番号は一切出力しない。
    """
    if not ideal_info:
        return {
            "総評":     "比較できる選手データがありません。",
            "重点改善": [],
            "強み活用": "",
        }

    comparison = ideal_info["比較"]

    # 強み・弱みを抽出
    diffs = []
    for col, d in comparison.items():
        if d["差分"] is not None:
            diffs.append((col, d["差分"], d["選手Z"] or 0, d["理想Z"] or 0))

    strengths = sorted(
        [(c, dz, iz) for c, diff, dz, iz in diffs if iz > dz],
        key=lambda x: x[1], reverse=True
    )[:3]
    weaknesses = sorted(
        [(c, dz, iz) for c, diff, dz, iz in diffs if iz > dz],
        key=lambda x: x[2] - x[1]
    )[:3]

    # プロンプト：目標選手名を一切含めない
    prompt = f"""あなたは経験豊富なスポーツトレーナーです。
選手「{player_name}」のデータを分析し、具体的で前向きなトレーニングアドバイスを提供してください。

【改善が必要な指標（チーム内比較）】
"""
    for col, dz, iz in weaknesses:
        d = comparison[col]
        gap = round(iz - dz, 2)
        prompt += f"- {col}：現在値={d['選手値']}、Zスコア={dz:+.2f}（目標まで{gap:+.2f}）\n"

    prompt += "\n【現在の強み（チーム上位）】\n"
    for col, dz, iz in strengths:
        d = comparison[col]
        prompt += f"- {col}：現在値={d['選手値']}、Zスコア={dz:+.2f}\n"

    prompt += """
以下の条件でコメントを作成してください：
- トレーナー・コーチとして選手に語りかける口調（「〜しましょう」「〜を意識してください」など）
- 特定の選手名・番号・IDは一切出さない
- データに基づいた具体的なアドバイス
- 選手が前向きになれる励ましを含める
- 日本語

以下の形式でJSON形式のみ出力してください（前置き・説明不要）:
{
  "総評": "選手の現状と方向性を2〜3文で説明",
  "重点改善": ["具体的な改善アドバイス1", "アドバイス2", "アドバイス3"],
  "強み活用": "強みを活かしたトレーニング提案1〜2文"
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
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception:
        pass

    # フォールバック：ルールベース
    fb_improvements = []
    for col, dz, iz in weaknesses[:3]:
        d = comparison[col]
        fb_improvements.append(
            f"{col}の向上に集中しましょう。現在値{d['選手値']}から改善できる余地があります。"
        )
    strength_text = ""
    if strengths:
        s_names = [c for c, _, _ in strengths[:2]]
        strength_text = f"{', '.join(s_names)}は優れています。この強みをベースにトレーニングを組み立てましょう。"

    return {
        "総評":     f"{player_name}選手は伸びしろのある段階にあります。重点指標を絞って取り組みましょう。",
        "重点改善": fb_improvements or ["基礎体力の向上を継続してください。"],
        "強み活用": strength_text or "強みを確認した上でプログラムを設計しましょう。",
    }


# 後方互換
def generate_ai_comment(player_name, ideal_info, advice_list,
                        metric_cols, **kwargs):
    return generate_trainer_comment(player_name, ideal_info,
                                    advice_list, metric_cols)