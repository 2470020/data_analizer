"""
Googleカレンダー連携モジュール。

現状はデモ版のため、OAuth認証部分は未実装。
本実装には以下が必要：
  - Google Cloud Console でのプロジェクト作成
  - OAuth 2.0 クライアントID取得
  - Calendar API の有効化
  - google-auth-oauthlib, google-api-python-client のインストール
"""

from datetime import datetime, timedelta


def is_calendar_connected() -> bool:
    """
    Googleカレンダー連携済みかどうかを返す。
    現状は常にFalse（デモ版のため未接続扱い）。
    """
    # ここは未定
    # 本実装では st.session_state にOAuthトークンの有無を確認する処理を入れる
    return False


def get_auth_url() -> str:
    """
    Google OAuth認証用URLを生成する。

    本実装イメージ：
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/calendar.events"],
            redirect_uri="https://your-app.streamlit.app/"
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        return auth_url
    """
    # ここは未定
    return "#"  # 仮のプレースホルダーURL


def push_training_to_calendar(training_data: dict,
                              credentials=None) -> bool:
    """
    1日分のトレーニングメニューをGoogleカレンダーに登録する。

    本実装イメージ：
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=credentials)

        event = {
            "summary": training_data["summary"],
            "description": "\n".join(
                f"{b['menu_name']}：{b['detail']}（{b['duration_min']}分）"
                for b in training_data["training_blocks"]
            ),
            "start": {"date": training_data["date"]},
            "end":   {"date": training_data["date"]},
        }
        service.events().insert(
            calendarId="primary", body=event
        ).execute()
        return True
    """
    # ここは未定
    return False


def push_weekly_plan_to_calendar(weekly_plan: list,
                                 credentials=None) -> dict:
    """
    1週間分のトレーニングメニューを一括でカレンダー登録する。
    返り値：{"success": int, "failed": int}
    """
    # ここは未定
    return {"success": 0, "failed": len(weekly_plan)}