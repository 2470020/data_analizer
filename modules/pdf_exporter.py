"""
選手個別カルテをPDF形式で出力するモジュール。
reportlab を使用。
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


def _register_font():
    """日本語フォントを登録する（環境によってパスを変更）"""
    font_paths = [
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Japanese", path))
                return "Japanese"
            except Exception:
                continue
    return "Helvetica"


def generate_player_pdf(player_name: str,
                        advice_list: list,
                        daily_training: dict,
                        weekly_plan: list,
                        coach_report: str,
                        rival_info: dict) -> bytes:
    """
    選手個別カルテをPDFとして生成し、バイト列で返す。
    """
    buffer   = io.BytesIO()
    doc      = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    font_name = _register_font()
    styles    = getSampleStyleSheet()

    # カスタムスタイル
    title_style = ParagraphStyle(
        "Title", fontName=font_name, fontSize=18,
        textColor=colors.HexColor("#1a6fc4"), spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "Sub", fontName=font_name, fontSize=10,
        textColor=colors.HexColor("#7a9cc0"), spaceAfter=8
    )
    section_style = ParagraphStyle(
        "Section", fontName=font_name, fontSize=11,
        textColor=colors.HexColor("#1a6fc4"),
        spaceBefore=12, spaceAfter=6,
        borderPad=4
    )
    body_style = ParagraphStyle(
        "Body", fontName=font_name, fontSize=9,
        textColor=colors.HexColor("#333333"), spaceAfter=4,
        leading=14
    )

    story = []

    # ── タイトル ──
    story.append(Paragraph(f"ATHLETE REPORT", title_style))
    story.append(Paragraph(f"選手名：{player_name}", sub_style))
    story.append(Paragraph(f"測定日：{daily_training.get('date', '-')}",
                           sub_style))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#1a6fc4")))
    story.append(Spacer(1, 6))

    # ── パラメーター表 ──
    story.append(Paragraph("■ スキルパラメーター", section_style))
    table_data = [["指標", "選手値", "チーム平均", "Zスコア", "判定"]]
    for item in advice_list:
        table_data.append([
            item["指標"],
            str(item["選手値"]),
            str(item["チーム平均"]),
            str(item["Zスコア"]),
            item["判定"]
        ])

    param_table = Table(table_data, colWidths=[45*mm, 25*mm, 25*mm, 25*mm, 25*mm])
    param_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1a6fc4")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), font_name),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [colors.HexColor("#f0f4fa"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(param_table)
    story.append(Spacer(1, 8))

    # ── コーチレポート ──
    story.append(Paragraph("■ コーチレポート", section_style))
    for line in coach_report.split("\n"):
        if line.strip():
            story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 8))

    # ── ライバル ──
    if rival_info.get("rival"):
        story.append(Paragraph("■ ライバル選手", section_style))
        story.append(Paragraph(
            f"課題が最も近い選手：{rival_info['rival']}　"
            f"（類似項目：{', '.join(rival_info['weak_metrics'])}）",
            body_style
        ))
        story.append(Spacer(1, 8))

    # ── 週間トレーニングプラン ──
    story.append(Paragraph("■ 週間トレーニングプラン", section_style))
    week_data = [["日付", "曜日", "メニュー", "対象項目", "時間"]]
    for day in weekly_plan:
        week_data.append([
            day["date"],
            day["weekday"],
            day["menu_name"],
            day["target_metric"],
            f"{day['duration_min']}分"
        ])

    week_table = Table(week_data,
                       colWidths=[28*mm, 12*mm, 50*mm, 40*mm, 15*mm])
    week_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1a6fc4")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), font_name),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [colors.HexColor("#f0f4fa"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ("ALIGN",         (4, 0), (4, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(week_table)

    doc.build(story)
    return buffer.getvalue()