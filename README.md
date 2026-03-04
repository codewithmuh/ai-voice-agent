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

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/codewithmuh/ai-voice-agent.git
cd ai-voice-agent
cp .env.example .env
```

### 2. Add your API keys to `.env`

```
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
- **Google Calendar:** Google Cloud Console → Enable Calendar API → Create Service Account → Download JSON
- **Twilio:** [twilio.com/console](https://www.twilio.com/console)

### 3. Google Calendar setup

1. Download your service account JSON and save it as `google-calendar-credentials.json` in the project root
2. Share your Google Calendar with the service account email (`your-service@project-id.iam.gserviceaccount.com`)

### 4. Start with Docker Compose

```bash
docker compose up --build
```

This starts Django on `http://localhost:8000` and PostgreSQL on port 5432.

### 5. Verify it works

```bash
curl http://localhost:8000/api/vapi/webhook/
# Returns: {"status": "ok", "service": "AI Voice Receptionist"}
```

### 6. Connect Vapi

1. Expose your server: `ngrok http 8000`
2. In Vapi dashboard → Create Assistant → Set Server URL to your ngrok URL + `/api/vapi/webhook/`
3. Buy a phone number and assign it to the assistant
4. Call the number

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

Access the admin panel at `http://localhost:8000/admin/` to view call logs, filter by date, and search by phone number.

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

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
