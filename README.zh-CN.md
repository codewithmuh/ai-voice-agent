# AI 语音接待员

<p align="center"><a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.ja.md">日本語</a></p>

[![GitHub Repo](https://img.shields.io/badge/GitHub-ai--voice--agent-blue?logo=github&style=for-the-badge)](https://github.com/codewithmuh/ai-voice-agent)
[![Stars](https://img.shields.io/github/stars/codewithmuh/ai-voice-agent?style=for-the-badge&logo=github)](https://github.com/codewithmuh/ai-voice-agent/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<img width="1352" height="813" alt="Screenshot 2026-03-05 at 3 09 41 AM" src="https://github.com/user-attachments/assets/8e631186-d932-4b36-bd09-c908c1e769a1" />

一款由 AI 驱动的电话接待员，可全天候接听来电、在 Google Calendar 中预约并发送短信确认——使用 Django、Claude AI、Vapi 和 PostgreSQL 构建。

## 功能

- 使用自然流畅的 AI 语音接听来电
- 实时检查 Google Calendar 的空闲时间
- 预约并创建日历事件
- 通过 Twilio 发送短信确认
- 将每通电话和每次预约记录到 PostgreSQL，并通过 Django 管理后台进行管理

## 技术栈

| 组件 | 作用 |
|-----------|------|
| **Django** | 后端核心——托管 Claude AI、工具、提示词和管理面板 |
| **Claude API (Anthropic)** | AI 对话引擎——处理语音、决定操作并调用工具 |
| **Vapi** | 语音通道——仅负责电话号码、语音转文本和文本转语音 |
| **PostgreSQL** | 通话日志和预约记录 |
| **Google Calendar API** | 查询预约空闲时间并进行预约 |
| **Twilio** | 短信确认 |

## 架构

Vapi **仅**用作语音传输层（STT/TTS）。所有 AI 逻辑、工具和提示词均位于 Django 中。

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

### 工作原理

1. 来电者拨打电话号码（通过 Vapi）
2. Vapi 将语音转换为文本，并将其发送到 Django 的 `/api/vapi/chat/completions/` 端点
3. Django 使用系统提示词和工具定义调用 Claude API
4. Claude 决定要执行的操作——检查日历、预约、发送短信等
5. Django 在本地执行工具，并将最终响应返回给 Vapi
6. Vapi 将文本响应转换回语音并播放给来电者

## 快速开始

### 1. 克隆并配置

```bash
git clone https://github.com/codewithmuh/ai-voice-agent.git
cd ai-voice-agent
cp .env.example .env
```

### 2. 生成 Django 密钥

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

将输出粘贴到 `.env` 文件中，作为 `SECRET_KEY` 的值。

### 3. 将 API 密钥添加到 `.env`

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

**密钥获取方式：**
- **Anthropic：** [console.anthropic.com](https://console.anthropic.com)
- **Vapi：** [dashboard.vapi.ai](https://dashboard.vapi.ai)
- **Google Calendar：** 请参阅下方的详细设置说明
- **Twilio：** [twilio.com/console](https://www.twilio.com/console)

### 4. 设置 Google Calendar

#### 第 1 步：创建 Google Cloud 项目
1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 点击 **Select a Project** → **New Project** → 输入名称 → **Create**

#### 第 2 步：启用 Calendar API
1. 前往 **APIs & Services** → **Library**
2. 搜索 **"Google Calendar API"** → 点击搜索结果 → **Enable**

#### 第 3 步：创建服务账号凭据
1. 前往 **APIs & Services** → **Credentials**
2. 点击 **+ Create Credentials** → **Service Account**
3. 输入名称（例如 "calendar-bot"）→ **Create and Continue** → 跳过可选步骤 → **Done**
4. 点击新创建的服务账号 → **Keys** 标签页 → **Add Key** → **Create New Key** → **JSON** → **Create**
5. 系统会下载一个 `.json` 文件——将其移至项目根目录：

```bash
mv ~/Downloads/your-downloaded-file.json ./google-calendar-credentials.json
```

#### 第 4 步：获取 Calendar ID
1. 打开 [Google Calendar](https://calendar.google.com)
2. 点击右上角的 **齿轮图标** → **Settings**
3. 在左侧的 **Settings for my calendars** 下，点击要使用的日历
4. 点击 **Integrate calendar**——此处会显示 **Calendar ID**
5. 对于默认日历，Calendar ID 就是你的 Gmail 地址（例如 `you@gmail.com`）

#### 第 5 步：与服务账号共享日历
1. 打开下载的 JSON 文件并复制 `client_email` 的值（格式类似 `calendar-bot@your-project.iam.gserviceaccount.com`）
2. 在 Google Calendar 中，前往日历的 **Settings and sharing**
3. 在 **Share with specific people or groups** 下，点击 **+ Add people and groups**
4. 粘贴服务账号电子邮件 → 将权限设为 **Make changes to events** → **Send**

> **提示：** Google Cloud 和 Google Calendar 使用同一个 Google 账号，可让设置更简单。

### 5. 使用 Docker Compose 启动

```bash
docker compose up --build
```

这会在 `http://localhost:8000` 上启动 Django，并在 5432 端口上启动 PostgreSQL。

### 6. 运行迁移并创建管理员用户

容器启动时会自动运行迁移。要创建 Django 管理员超级用户，请运行：

```bash
docker compose exec web python manage.py createsuperuser
```

### 7. 验证是否正常工作

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

### 8. 使用 ngrok 公开服务

如果尚未安装 ngrok，请先安装：

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

启动隧道：

```bash
ngrok http 8000
```

复制输出中的 `https://...ngrok-free.app` URL。

### 9. 连接 Vapi

1. 前往 [Vapi Dashboard](https://dashboard.vapi.ai)
2. 创建一个 Assistant
3. 将 **Model** 设为 `Custom LLM`，并使用以下 URL：
   ```
   https://your-ngrok-url.ngrok-free.app/api/vapi/chat/completions/
   ```
4. 将 **Server URL**（用于通话结束报告）设为：
   ```
   https://your-ngrok-url.ngrok-free.app/api/vapi/webhook/
   ```
5. 购买或导入电话号码，并将其分配给该 Assistant
6. 拨打该号码进行测试（也可以使用 Vapi 控制面板中的网页通话按钮）

> **重要：** Vapi 会将对话消息发送到 Custom LLM URL。Django 调用 Claude、运行工具并返回响应。Vapi 仅负责语音处理（STT/TTS）。

## 项目结构

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

### 主要端点

| 端点 | 用途 |
|----------|---------|
| `POST /api/vapi/chat/completions/` | 自定义 LLM——接收来自 Vapi 的消息，调用 Claude 和工具并返回响应 |
| `POST /api/vapi/webhook/` | Webhook——接收通话结束报告并将通话记录到数据库 |
| `GET /api/vapi/webhook/` | 健康检查 |

## Django 管理后台

通过 `http://localhost:8000/admin/` 访问管理面板，可以：
- 查看所有通话日志（来电者电话号码、时长、摘要、时间戳）
- 查看所有已预约事项（患者姓名、日期、时间、类型）
- 按日期和预约状态筛选通话
- 按类型和日期筛选预约
- 按电话号码或患者姓名搜索

## 部署到生产环境

```bash
# Railway
railway init
railway add --plugin postgresql
railway up
```

在 Railway 控制面板中设置环境变量，然后将 Vapi Custom LLM URL 和 Server URL 更新为 Railway 域名。
![installtion thumbinil](https://github.com/user-attachments/assets/84b56fbb-16e1-4a95-9ee3-dcfc6b15b45f)

## 许可证

MIT
