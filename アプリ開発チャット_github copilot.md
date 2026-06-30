コードを確認しました。これは **Streamlit ベースのアスリート分析システム** で、体力測定データから選手のパフォーマンスプロファイルを生成する素晴らしいプロジェクトです。以下、追加可能な機能をいくつかご提案します。

## 🎯 推奨される追加機能

### **1. 時系列トレンド分析** ⭐ 高優先度
```
現状: 単一時点のデータ分析のみ
提案: 
- 同じ選手の複数時点のデータを比較
- 改善/低下のトレンドをグラフで可視化
- 季節別パフォーマンス変化を追跡
```

### **2. 負傷リスク予測** ⭐ 高優先度
```
現状: 個別指標の分析
提案:
- 複数指標の低下パターンから過労/負傷兆候を検出
- リスク度合いを可視化（低→中→高）
- 予防的アドバイスを自動生成
```

### **3. グループ・チーム分析**
```
現状: 全体ランキング、個別分析
提案:
- ポジション別の平均値比較
- グループ内での役割最適化提案
- 選手構成の多様性分析
```

### **4. カスタムスコアリング・ウェイト設定**
```
現状: 全指標を等しく扱う
提案:
- 競技種別ごとに重要度ウェイトを変更可能
- 複数のスコアリングモデルを保存・比較
```

### **5. 選手育成プラン自動生成**
```
現状: 改善ポイントの提案のみ
提案:
- 12週間/24週間などの育成計画を自動生成
- 目標選手への進捗マイルストーン
- 推奨トレーニング頻度・内容
```

### **6. 異常値検知と品質管理**
```
現状: ±3σで外れ値を除外するのみ
提案:
- 測定機器の不具合を検出
- 同じ測定者による計測ばらつきを分析
- データ品質スコア表示
```

### **7. ベンチマーク・参考値との比較**
```
現状: チーム内比較のみ
提案:
- 年代別・性別・競技別のナショナルベンチマーク
- 世界平均値との比較
```

### **8. 複数ファイルの履歴管理**
```
現状: 毎回ファイルアップロード
提案:
- データベース連携で測定履歴を自動保管
- 日付ごとの変更差分表示
- 過去データからの復元機能
```

### **9. PDF レポート自動生成**
```
現状: JSON/CSVエクスポートのみ
提案:
- 印刷可能なプロ仕様PDFレポート
- チームで共有できるハイライトサマリー
```

### **10. 競技種別テンプレート**
```
現状: 汎用分析
提案:
- サッカー / バスケ / 野球 etc の競技別テンプレート
- 競技に最適な指標セットを自動選択
- 競技ルール別のアドバイス
```

---

## 💡 実装優先度の目安

| 優先度 | 機能 | 工数 | 効果 |
|--------|------|------|------|
| 🔴 **高** | 時系列トレンド | 中 | **強** |
| 🔴 **高** | 負傷リスク予測 | 大 | **強** |
| 🟠 **中** | グループ分析 | 中 | 中 |
| 🟠 **中** | PDF レポート | 小 | 中 |
| 🟡 **低** | ウェイト設定 | 中 | 中 |

---

どの機能が最も興味深いですか？詳細な実装アドバイスが必要でしたら、お知らせください！



コードと実装希望の機能一覧を確認しました。現在のシステムと、あなたが考えている機能を整理します。リポジトリの構成を確認させてください。データセットとコード構造を確認しました。**あなたが提案している機能は非常にバランスが取れていて、現状の実装を見ると既に多くが実現されています。** 以下、詳細な分析と改善提案です。

---

## ✅ **実装状況の確認**

| 機能 | 実装状況 | 進捗度 |
|------|--------|--------|
| **データ読み込み** | ✅ 完全実装 | 100% |
| **基本統計・ランキング** | ✅ 完全実装 | 100% |
| **レーダーチャート** | ✅ 完全実装 | 100% |
| **スキルアップ（AIコーチング）** | ✅ 基本実装 | 85% |
| **カレンダー連携** | ❌ 未実装 | 0% |
| **栄養管理** | ❌ 未実装 | 0% |

---

## 🔧 **次のステップ：実装推奨機能の優先順位**

### **🔴 優先度 1 - すぐに実装可能（1-2週間）**

#### **1-1. 時系列トレンド分析**
```python
# 実装例の骨組み
def add_trend_analysis():
    """
    同じ選手の複数測定データを比較
    - 日付別パフォーマンス推移
    - 改善率の計算
    - 低下警告アラート
    """
```
**理由**: 
- データが既にあり、日付カラムを追加するだけ
- 選手の進捗を追跡できる最重要機能
- `git log`や`session-search`と組み合わせると、更新履歴も使える

**UI提案**:
```
┌─ 時系列分析 ─────────────────────┐
│ 選手選択: [ドロップダウン]        │
│ 指標選択: [マルチセレクト]        │
│ 期間指定: [DATE FROM] - [DATE TO] │
│                                   │
│ グラフ表示:                       │
│ [ラインチャート（3ヶ月推移）]    │
│ [改善率テーブル]                  │
└──────────────────────────────────┘
```

---

#### **1-2. 負傷・過労リスク予測**
```python
# モジュール: modules/risk_detection.py
def detect_fatigue_risk(player_data, historical_data):
    """
    複数指標の低下パターンから過労を検出
    - CMJ vs DJ: バウンス機能の低下
    - HG (握力): 全身疲労指標
    - 短距離 (10m走): 神経筋疲労
    """
    risk_score = calculate_multi_factor_risk(...)
    return {
        "risk_level": "HIGH/MEDIUM/LOW",
        "factors": [...],
        "recommendation": "休息を推奨"
    }
```

**データから見える知見**:
- **CMJ (Counter Movement Jump)**: 爆発力・下肢パワー
- **DJ-RSI (Reactive Strength Index)**: ストレッチ・ショートニング機能
- **HG (Hand Grip)**: 全身の神経筋疲労の指標
- **10m走 / 20m走**: 神経筋疲労が出やすい項目

**リスク判定ロジック例**:
```
IF (CMJ ↓ 10% AND DJ-RSI ↓ 15% AND HG ↓ 8%) → 高リスク
IF (10m走 時間 ↑ 3% AND 20m走 ↑ 3%) → 中リスク
```

---

### **🟠 優先度 2 - 高付加価値（2-3週間）**

#### **2-1. Google Calendar 連携**
```python
# モジュール: modules/calendar_integration.py
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

def create_training_schedule(player_name, recommendations):
    """
    Streamlit-oauthを使ってGoogleカレンダーに自動入力
    """
    # OAuth認証
    flow = InstalledAppFlow.from_client_secrets_file(...)
    creds = flow.run_local_server()
    
    # カレンダー作成
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': f'{player_name}: {training_type}',
        'description': recommendations,
        'start': {'dateTime': '2026-07-05T10:00:00'},
        'end': {'dateTime': '2026-07-05T11:00:00'},
    }
    service.events().insert(calendarId='primary', body=event).execute()
```

**Streamlit実装例**:
```python
import streamlit_authenticator as stauth

# セッション管理
if 'calendar_auth' not in st.session_state:
    st.session_state.calendar_auth = False

if st.button("📅 カレンダーに保存"):
    with st.spinner("Googleアカウントで認証中..."):
        creds = authenticate_google()
        create_training_schedule(player_name, recommendations)
    st.success("✅ カレンダーに追加されました！")
```

**実装難易度**: ⭐⭐⭐  
**メリット**: ユーザー体験が大きく向上

---

#### **2-2. 複数競技別テンプレート**
現在のデータセットから、競技別に最適な指標セットを自動提案:

```python
# modules/sport_templates.py
SPORT_TEMPLATES = {
    "サッカー": {
        "focus_metrics": ["10m走", "20m走", "CMJ", "DJ-RSI"],
        "weight": {"speed": 0.35, "power": 0.35, "agility": 0.30}
    },
    "バスケットボール": {
        "focus_metrics": ["CMJ", "DJ-RSI", "HG右", "HG左"],
        "weight": {"power": 0.50, "strength": 0.50}
    },
    "野球（投手）": {
        "focus_metrics": ["HG合計", "20m走", "DJ-RSI"],
        "weight": {"strength": 0.40, "speed": 0.30, "power": 0.30}
    }
}
```

---

### **🟡 優先度 3 - 高度な機能（3-4週間）**

#### **3-1. 栄養管理・食事提案**
```python
# modules/nutrition_advisor.py
def recommend_nutrition(player_data, training_type):
    """
    トレーニング内容に応じた栄養管理
    """
    if training_type == "筋力強化":
        return {
            "protein_target": "体重 × 2.0g",
            "carbs": "体重 × 7-10g",
            "recipes": get_recipes_from_api("高タンパク低脂肪")
        }
```

**外部API候補**:
- **Edamam API**: 栄養計算（無料枠あり）
- **Spoonacular API**: レシピ提案
- **USDA FoodData Central**: 日本食品データベース連携

---

#### **3-2. 詳細な選手育成プラン**
```python
# modules/training_plan_generator.py
def generate_12week_plan(player_data, target_player_data):
    """
    現在値 → 目標値への12週間プラン
    """
    return {
        "week_1_2": {"focus": "基礎体力", "sessions": 3},
        "week_3_4": {"focus": "パワー", "sessions": 4},
        "week_5_8": {"focus": "専門技術", "sessions": 4},
        "week_9_12": {"focus": "統合トレーニング", "sessions": 3},
    }
```

---

## 💡 **あなたの提案の問題点と改善案**

### ❌ **カレンダー連携 - 注意点**
現在の提案は「Google Calendar」のみ対応になっていますが:

```python
# ✅ 改善案: 複数カレンダー対応
class CalendarIntegrator:
    PROVIDERS = {
        "Google Calendar": GoogleCalendarAPI,
        "Microsoft Outlook": OutlookCalendarAPI,
        "iCal": iCalAPI,  # ダウンロード形式
    }
    
    def export_schedule(provider, events):
        """ユーザーが選んだカレンダーに対応"""
        pass
```

---

### ❌ **栄養管理 - スコープの問題**
「料理レシピサイトのAPI」は:
- **外部API依存が強い**（API変更で動作停止）
- **日本語対応が弱い**（海外サービス中心）
- **栄養学的根拠が不十分**（単なるレシピ検索では不足）

**改善案**:
```python
# ✅ ローカル栄養DB + 簡易推奨
class NutritionPlanner:
    LOCAL_FOOD_DB = {
        "鶏むね肉": {"protein": 23, "fat": 1.9, "carbs": 0},
        "玄米": {"protein": 2.8, "fat": 1.0, "carbs": 35},
        ...
    }
    
    def calculate_meal_plan(goals):
        """PFCバランスに基づく食材提案"""
        return {
            "breakfast": [...],  # DBから自動選択
            "lunch": [...],
            "dinner": [...],
        }
```

---

## 🎯 **今すぐ実装すべき優先度 TOP 3**

| # | 機能 | 理由 | 工数 |
|---|------|------|------|
| **1** | ⏰ 時系列トレンド | 選手進捗追跡が最優先 | 3日 |
| **2** | ⚠️ 負傷リスク検出 | 安全性向上、付加価値高 | 1週間 |
| **3** | 📅 カレンダー連携 | UX向上、ユーザー満足度↑ | 3-4日 |

---

## 📝 **実装チェックリスト**

```markdown
# Phase 1: Core Enhancement (現在 → 2週間)
- [ ] 時系列トレンド分析 UI・機能
- [ ] 負傷リスク予測ロジック
- [ ] 男女別・年代別ベンチマーク表示

# Phase 2: Integration (2-4週間)
- [ ] Google Calendar OAuth連携
- [ ] iCal エクスポート機能
- [ ] 複数競技テンプレート

# Phase 3: Advanced (1ヶ月以降)
- [ ] 簡易栄養管理
- [ ] 12週間育成プラン自動生成
- [ ] チーム分析 (ポジション別)
```

---

どの機能から実装を始めたいですか？ **時系列トレンド分析** の詳細実装コードをお見せすることもできます！