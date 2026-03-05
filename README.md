# AI Voice Receptionist
<img width="1352" height="813" alt="Screenshot 2026-03-05 at 3 09 41 AM" src="https://github.com/user-attachments/assets/8e631186-d932-4b36-bd09-c908c1e769a1" />

An AI-powered phone receptionist that answers calls 24/7, books appointments on Google Calendar, and sends SMS confirmations — built with Claude Agent SDK, Django, Vapi, and PostgreSQL.

## What It Does

- Answers incoming phone calls with a natural-sounding AI voice
- Checks Google Calendar availability in real time
- Books appointments and creates calendar events
- Sends SMS confirmations via Twilio
- Logs every call to PostgreSQL with a Django admin dashboard

## Tech Stack

| Component | Role |
|-----------|------|
| **Claude Agent SDK** | AI brain — processes conversation, decides actions, calls tools |
| **Vapi** | Telephony — phone numbers, speech-to-text, text-to-speech |
| **Django** | Backend server, webhook handler, admin panel |
| **PostgreSQL** | Call logging and analytics |
| **Google Calendar API** | Appointment availability and booking |
| **Twilio** | SMS confirmations |

## Architecture

```
[Phone Call] → [Vapi: STT/TTS] ↔ [Django + Claude Agent SDK]
                                        |        |        |
                                 [Google Cal] [Twilio] [PostgreSQL]
```

<img width="1487" height="814" alt="Screenshot 2026-03-05 at 3 11 53 AM" src="https://github.com/user-attachments/assets/7881f037-323b-4f09-b3ae-81ac2b04601d" />


## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/codewithmuh/ai-voice-agent.git
cd ai-voice-agent
cp .env.example .env
```

### 2. Generate a Django secret key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Paste the output into your `.env` file as the `SECRET_KEY` value.

### 3. Add your API keys to `.env`

```
SECRET_KEY=your-generated-secret-key
ANTHROPIC_API_KEY=sk-ant-...
VAPI_API_KEY=...
GOOGLE_CALENDAR_CREDENTIALS=google-calendar-credentials.json
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

**Where to get keys:**
- **Anthropic:** [console.anthropic.com](https://console.anthropic.com)
- **Vapi:** [dashboard.vapi.ai](https://dashboard.vapi.ai)
- **Google Calendar:** See detailed setup below
- **Twilio:** [twilio.com/console](https://www.twilio.com/console)

### 4. Google Calendar setup

#### Step 1: Create a Google Cloud project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a Project** → **New Project** → name it → **Create**

#### Step 2: Enable the Calendar API
1. Go to **APIs & Services** → **Library**
2. Search for **"Google Calendar API"** → click it → **Enable**

#### Step 3: Create service account credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **Service Account**
3. Name it (e.g., "calendar-bot") → **Create and Continue** → skip optional steps → **Done**
4. Click on the newly created service account → **Keys** tab → **Add Key** → **Create New Key** → **JSON** → **Create**
5. A `.json` file will download — move it to your project root:

```bash
mv ~/Downloads/your-downloaded-file.json ./google-calendar-credentials.json
```

#### Step 4: Get your Calendar ID
1. Open [Google Calendar](https://calendar.google.com)
2. Click the **gear icon (⚙️)** in the top-right → **Settings**
3. Under **Settings for my calendars** on the left, click the calendar you want
4. Click **Integrate calendar** — the **Calendar ID** is displayed there
5. For your default calendar, the Calendar ID is simply your Gmail address (e.g., `you@gmail.com`)

#### Step 5: Share calendar with service account
1. Open the downloaded JSON file and copy the `client_email` value (looks like `calendar-bot@your-project.iam.gserviceaccount.com`)
2. In Google Calendar → **Settings and sharing** for your calendar
3. Under **Share with specific people or groups** → **+ Add people and groups**
4. Paste the service account email → set permission to **Make changes to events** → **Send**

> **Tip:** Use the same Google account for both Google Cloud and Google Calendar to keep things simple.

### 5. Start with Docker Compose

```bash
docker compose up --build
```

This starts Django on `http://localhost:8000` and PostgreSQL on port 5432.

### 6. Run migrations and create admin user

Migrations run automatically on container start. To create a Django admin superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

### 7. Verify it works

```bash
curl http://localhost:8000/api/vapi/webhook/
# Returns: {"status": "ok", "service": "AI Voice Receptionist"}
```

### 8. Expose with ngrok

Install ngrok if you don't have it:

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

Start the tunnel:

```bash
ngrok http 8000
```

Copy the `https://...ngrok-free.app` URL from the output.

### 9. Connect Vapi

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Create or select an Assistant → set the **Server URL** to:
   ```
   https://your-ngrok-url.ngrok-free.app/api/vapi/webhook/
   ```
3. Buy a phone number and assign it to the assistant
4. Call the number to test

## Project Structure

```
ai-voice-agent/
├── receptionist_project/
│   ├── settings.py              # Django config
│   └── urls.py                  # URL routing
├── calls/
│   ├── models.py                # CallLog model
│   ├── views.py                 # Vapi webhook endpoint
│   ├── admin.py                 # Django admin registration
│   ├── agent/
│   │   ├── receptionist.py      # Claude agentic loop (the brain)
│   │   ├── tools.py             # 4 tool definitions
│   │   └── prompts.py           # System prompt
│   └── services/
│       ├── calendar.py          # Google Calendar API
│       ├── sms.py               # Twilio SMS
│       └── database.py          # Call logging
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

## Django Admin

Access the admin panel at `http://localhost:8000/admin/` to:
- View all call logs (caller phone, duration, timestamp)
- Filter calls by date and booking status
- Search by phone number
- See which calls resulted in booked appointments

## Deploy to Production

```bash
# Railway
railway init
railway add --plugin postgresql
railway up
```

Set your environment variables in the Railway dashboard, then update the Vapi Server URL to your Railway domain.

## License

MIT
