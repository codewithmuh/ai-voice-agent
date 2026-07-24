# AI 音声受付

<p align="center"><a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.ja.md">日本語</a></p>

[![GitHub Repo](https://img.shields.io/badge/GitHub-ai--voice--agent-blue?logo=github&style=for-the-badge)](https://github.com/codewithmuh/ai-voice-agent)
[![Stars](https://img.shields.io/github/stars/codewithmuh/ai-voice-agent?style=for-the-badge&logo=github)](https://github.com/codewithmuh/ai-voice-agent/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<img width="1352" height="813" alt="Screenshot 2026-03-05 at 3 09 41 AM" src="https://github.com/user-attachments/assets/8e631186-d932-4b36-bd09-c908c1e769a1" />

24時間365日電話に応答し、Google Calendar で予約を取り、SMS で確認を送信する AI 搭載の電話受付システムです。Django、Claude AI、Vapi、PostgreSQL で構築されています。

## 機能

- 自然な AI 音声で着信に応答
- Google Calendar の空き状況をリアルタイムで確認
- 予約を受け付け、カレンダーイベントを作成
- Twilio 経由で SMS 確認を送信
- すべての通話と予約を PostgreSQL に記録し、Django 管理画面で管理

## 技術スタック

| コンポーネント | 役割 |
|-----------|------|
| **Django** | バックエンドの中核——Claude AI、ツール、プロンプト、管理パネルをホスト |
| **Claude API (Anthropic)** | AI 会話エンジン——音声を処理し、アクションを判断してツールを呼び出す |
| **Vapi** | 音声パイプ——電話番号、音声テキスト変換、テキスト音声変換のみを担当 |
| **PostgreSQL** | 通話ログと予約記録 |
| **Google Calendar API** | 予約可能時間の確認と予約 |
| **Twilio** | SMS 確認 |

## アーキテクチャ

Vapi は音声転送レイヤー（STT/TTS）として**のみ**使用します。すべての AI ロジック、ツール、プロンプトは Django にあります。

```
[Phone Call] → [Vapi: STT only] → [Django Custom LLM Endpoint]
                                          ↓
                                   [Claude AI + Tools]
                                    ↙     ↓      ↘
                            [Google Cal] [Twilio] [PostgreSQL]
                                          ↓
                                   [Django Response]
                                          ↓
                              [Vapi: TTS only] → [Caller hears response]
```

<img width="1487" height="814" alt="Screenshot 2026-03-05 at 3 11 53 AM" src="https://github.com/user-attachments/assets/7881f037-323b-4f09-b3ae-81ac2b04601d" />

### 仕組み

1. 発信者が電話番号に電話します（Vapi 経由）
2. Vapi が音声をテキストに変換し、Django の `/api/vapi/chat/completions/` エンドポイントへ送信します
3. Django がシステムプロンプトとツール定義を指定して Claude API を呼び出します
4. Claude が実行内容を判断します——カレンダーの確認、予約、SMS 送信など
5. Django がローカルでツールを実行し、最終応答を Vapi に返します
6. Vapi がテキスト応答を音声に変換して発信者に返します

## クイックスタート

### 1. クローンと設定

```bash
git clone https://github.com/codewithmuh/ai-voice-agent.git
cd ai-voice-agent
cp .env.example .env
```

### 2. Django シークレットキーの生成

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

出力を `.env` ファイルに `SECRET_KEY` の値として貼り付けます。

### 3. API キーを `.env` に追加

```
SECRET_KEY=your-generated-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*

DB_NAME=ai_receptionist
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

ANTHROPIC_API_KEY=sk-ant-...
VAPI_API_KEY=...
GOOGLE_CALENDAR_CREDENTIALS=google-calendar-credentials.json
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

**キーの入手先：**
- **Anthropic：** [console.anthropic.com](https://console.anthropic.com)
- **Vapi：** [dashboard.vapi.ai](https://dashboard.vapi.ai)
- **Google Calendar：** 以下の詳しい設定手順を参照
- **Twilio：** [twilio.com/console](https://www.twilio.com/console)

### 4. Google Calendar の設定

#### ステップ 1：Google Cloud プロジェクトを作成
1. [Google Cloud Console](https://console.cloud.google.com) に移動します
2. **Select a Project** → **New Project** の順にクリック → 名前を入力 → **Create**

#### ステップ 2：Calendar API を有効化
1. **APIs & Services** → **Library** に移動します
2. **"Google Calendar API"** を検索 → クリック → **Enable**

#### ステップ 3：サービスアカウント認証情報を作成
1. **APIs & Services** → **Credentials** に移動します
2. **+ Create Credentials** → **Service Account** をクリックします
3. 名前（例："calendar-bot"）を入力 → **Create and Continue** → 任意の手順をスキップ → **Done**
4. 新しく作成したサービスアカウントをクリック → **Keys** タブ → **Add Key** → **Create New Key** → **JSON** → **Create**
5. `.json` ファイルがダウンロードされます——プロジェクトのルートへ移動してください：

```bash
mv ~/Downloads/your-downloaded-file.json ./google-calendar-credentials.json
```

#### ステップ 4：Calendar ID を取得
1. [Google Calendar](https://calendar.google.com) を開きます
2. 右上の **歯車アイコン** → **Settings** をクリックします
3. 左側の **Settings for my calendars** で、使用するカレンダーをクリックします
4. **Integrate calendar** をクリックします——そこに **Calendar ID** が表示されます
5. デフォルトカレンダーの場合、Calendar ID は Gmail アドレスそのものです（例：`you@gmail.com`）

#### ステップ 5：カレンダーをサービスアカウントと共有
1. ダウンロードした JSON ファイルを開き、`client_email` の値（`calendar-bot@your-project.iam.gserviceaccount.com` のような形式）をコピーします
2. Google Calendar で、対象カレンダーの **Settings and sharing** に移動します
3. **Share with specific people or groups** で **+ Add people and groups** をクリックします
4. サービスアカウントのメールアドレスを貼り付け → 権限を **Make changes to events** に設定 → **Send**

> **ヒント：** Google Cloud と Google Calendar で同じ Google アカウントを使用すると、設定が簡単になります。

### 5. Docker Compose で起動

```bash
docker compose up --build
```

これにより、Django が `http://localhost:8000` で、PostgreSQL がポート 5432 で起動します。

### 6. マイグレーションの実行と管理ユーザーの作成

マイグレーションはコンテナ起動時に自動実行されます。Django 管理者のスーパーユーザーを作成するには：

```bash
docker compose exec web python manage.py createsuperuser
```

### 7. 動作確認

```bash
# Test the webhook endpoint
curl http://localhost:8000/api/vapi/webhook/
# Returns: {"status": "ok", "service": "AI Voice Receptionist"}

# Test the custom LLM endpoint
curl -X POST http://localhost:8000/api/vapi/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hi, I want to book an appointment"}]}'
# Returns an OpenAI-format response with Claude's reply
```

### 8. ngrok で公開

ngrok が未インストールの場合はインストールします：

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

トンネルを起動します：

```bash
ngrok http 8000
```

出力から `https://...ngrok-free.app` URL をコピーします。

### 9. Vapi に接続

1. [Vapi Dashboard](https://dashboard.vapi.ai) に移動します
2. Assistant を作成します
3. **Model** を `Custom LLM` に設定し、次の URL を指定します：
   ```
   https://your-ngrok-url.ngrok-free.app/api/vapi/chat/completions/
   ```
4. **Server URL**（通話終了レポート用）を次のように設定します：
   ```
   https://your-ngrok-url.ngrok-free.app/api/vapi/webhook/
   ```
5. 電話番号を購入またはインポートし、Assistant に割り当てます
6. 電話番号に発信してテストします（Vapi ダッシュボードのウェブ通話ボタンも使用できます）

> **重要：** Custom LLM URL は、Vapi が会話メッセージを送信する先です。Django が Claude を呼び出してツールを実行し、応答を返します。Vapi は音声（STT/TTS）のみを処理します。

## プロジェクト構成

```
ai-voice-agent/
├── receptionist_project/
│   ├── settings.py              # Django config
│   └── urls.py                  # URL routing
├── calls/
│   ├── models.py                # CallLog + Appointment models
│   ├── views.py                 # Custom LLM endpoint + Vapi webhook
│   ├── urls.py                  # API routes
│   ├── admin.py                 # Django admin registration
│   ├── agent/
│   │   ├── receptionist.py      # Claude agentic loop (the brain)
│   │   ├── tools.py             # Tool definitions (calendar, SMS, DB)
│   │   └── prompts.py           # System prompt (Bright Smile Dental)
│   └── services/
│       ├── calendar.py          # Google Calendar API
│       ├── sms.py               # Twilio SMS
│       └── database.py          # Call logging
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

### 主要エンドポイント

| エンドポイント | 目的 |
|----------|---------|
| `POST /api/vapi/chat/completions/` | カスタム LLM——Vapi からメッセージを受信し、Claude とツールを呼び出して応答を返す |
| `POST /api/vapi/webhook/` | Webhook——通話終了レポートを受信し、通話をデータベースに記録 |
| `GET /api/vapi/webhook/` | ヘルスチェック |

## Django 管理画面

`http://localhost:8000/admin/` で管理パネルにアクセスし、以下を行えます：
- すべての通話ログ（発信者の電話番号、通話時間、要約、タイムスタンプ）を表示
- すべての予約（患者名、日付、時刻、種類）を表示
- 日付と予約状況で通話を絞り込み
- 種類と日付で予約を絞り込み
- 電話番号または患者名で検索

## 本番環境へのデプロイ

```bash
# Railway
railway init
railway add --plugin postgresql
railway up
```

Railway ダッシュボードで環境変数を設定し、Vapi Custom LLM URL と Server URL を Railway ドメインに更新します。
![installtion thumbinil](https://github.com/user-attachments/assets/84b56fbb-16e1-4a95-9ee3-dcfc6b15b45f)

## ライセンス

MIT
