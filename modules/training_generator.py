import pandas as pd
from datetime import date, timedelta

# 指標ごとのトレーニングメニュー辞書
# キーワードでマッチングし、弱点に対応するメニューを返す
TRAINING_MENU_DB = {
    "走": [
        {"name": "スプリントドリル", "detail": "10m×6本（全力走）", "duration": 15},
        {"name": "ラダートレーニング", "detail": "クイックステップ 5種類×2セット", "duration": 10},
        {"name": "加速走", "detail": "20m加速走×8本", "duration": 15},
    ],
    "ジャンプ": [
        {"name": "プライオメトリクス", "detail": "ボックスジャンプ 3セット×10回", "duration": 15},
        {"name": "垂直跳びドリル", "detail": "連続垂直跳び 5セット×5回", "duration": 10},
    ],
    "CMJ": [
        {"name": "プライオメトリクス", "detail": "ボックスジャンプ 3セット×10回", "duration": 15},
        {"name": "垂直跳びドリル", "detail": "連続垂直跳び 5セット×5回", "duration": 10},
    ],
    "握力": [
        {"name": "グリップトレーニング", "detail": "ハンドグリッパー 3セット×15回", "duration": 10},
        {"name": "懸垂", "detail": "懸垂（または斜め懸垂）3セット×8回", "duration": 10},
    ],
    "HG": [
        {"name": "グリップトレーニング", "detail": "ハンドグリッパー 3セット×15回", "duration": 10},
        {"name": "懸垂", "detail": "懸垂（または斜め懸垂）3セット×8回", "duration": 10},
    ],
    "体幹": [
        {"name": "プランク", "detail": "プランク 60秒×3セット", "duration": 10},
        {"name": "メディシンボールスロー", "detail": "回旋投げ 各方向10回×3セット", "duration": 15},
    ],
    "酸素摂取": [
        {"name": "インターバル走", "detail": "400m×6本（休憩90秒）", "duration": 25},
        {"name": "ファルトレク", "detail": "ペース変化走 20分間", "duration": 20},
    ],
}

DEFAULT_MENU = [
    {"name": "基礎フィジカル", "detail": "サーキットトレーニング 20分", "duration": 20},
    {"name": "ストレッチ・モビリティ", "detail": "全身可動域トレーニング", "duration": 15},
]


def _match_menu(metric_name: str) -> list:
    """指標名からキーワードマッチでメニューを取得"""
    for keyword, menus in TRAINING_MENU_DB.items():
        if keyword in metric_name:
            return menus
    return DEFAULT_MENU


def generate_daily_training(advice_list: list,
                            target_date: date = None) -> dict:
    """
    分析結果（advice_list）から、弱点項目に対応する
    1日分のトレーニングメニューを自動生成する。

    弱点（Zスコアが低い項目）上位2つに対応するメニューを選定。
    """
    if target_date is None:
        target_date = date.today()

    # Zスコアが低い項目（重点課題・要強化）を抽出して優先
    weak_items = [
        item for item in advice_list
        if item["判定"] in ("重点課題", "要強化")
    ]

    # 弱点がなければ全項目からランダム的に選択（維持メニュー）
    target_items = weak_items if weak_items else advice_list[:2]

    # 上位2項目に対応するメニューを生成
    training_blocks = []
    for item in target_items[:2]:
        menus = _match_menu(item["指標"])
        # 各弱点につき1メニューを選択（先頭固定で再現性確保）
        menu = menus[0]
        training_blocks.append({
            "target_metric": item["指標"],
            "reason":        item["判定"],
            "menu_name":      menu["name"],
            "detail":         menu["detail"],
            "duration_min":   menu["duration"]
        })

    total_duration = sum(b["duration_min"] for b in training_blocks)

    return {
        "date":            target_date.isoformat(),
        "training_blocks": training_blocks,
        "total_duration":  total_duration,
        "summary":         f"本日の重点項目：{', '.join([b['target_metric'] for b in training_blocks])}"
    }


def generate_weekly_plan(advice_list: list,
                         start_date: date = None) -> list:
    """
    1週間分（7日間）のトレーニングメニューを生成する。
    日替わりで弱点項目を順番に取り上げる。
    """
    if start_date is None:
        start_date = date.today()

    weak_items = [
        item for item in advice_list
        if item["判定"] in ("重点課題", "要強化")
    ]
    rotation_items = weak_items if weak_items else advice_list

    weekly_plan = []
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        # 日替わりで対象項目をローテーション
        idx          = day_offset % len(rotation_items)
        item         = rotation_items[idx]
        menus        = _match_menu(item["指標"])
        menu         = menus[day_offset % len(menus)]

        weekly_plan.append({
            "date":          current_date.isoformat(),
            "weekday":        ["月", "火", "水", "木", "金", "土", "日"][current_date.weekday()],
            "target_metric":  item["指標"],
            "menu_name":      menu["name"],
            "detail":         menu["detail"],
            "duration_min":   menu["duration"]
        })

    return weekly_plan