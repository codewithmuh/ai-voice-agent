import logging
from datetime import datetime, timedelta
from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

_calendar_service = None


def get_calendar_service():
    global _calendar_service
    if _calendar_service is None:
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CALENDAR_CREDENTIALS, scopes=SCOPES
        )
        _calendar_service = build("calendar", "v3", credentials=creds)
    return _calendar_service


def get_calendar_id():
    return settings.GOOGLE_CALENDAR_ID


def check_availability(date: str) -> dict:
    service = get_calendar_service()
    calendar_id = get_calendar_id()

    start_of_day = f"{date}T08:00:00Z"
    end_of_day = f"{date}T18:00:00Z"

    events = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    busy_slots = [
        (e["start"]["dateTime"], e["end"]["dateTime"])
        for e in events.get("items", [])
    ]

    available = []
    for hour in range(8, 18):
        for minute in [0, 30]:
            slot = datetime.fromisoformat(f"{date}T{hour:02d}:{minute:02d}:00")
            is_busy = any(
                datetime.fromisoformat(s) <= slot < datetime.fromisoformat(e)
                for s, e in busy_slots
            )
            if not is_busy:
                available.append(f"{hour:02d}:{minute:02d}")

    return {"date": date, "available_slots": available, "total_available": len(available)}


def book_appointment(details: dict) -> dict:
    service = get_calendar_service()
    calendar_id = get_calendar_id()

    duration = 60 if details["appointment_type"] == "new_patient" else 30
    start = datetime.fromisoformat(f"{details['date']}T{details['time']}:00")
    end = start + timedelta(minutes=duration)

    event = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body={
                "summary": f"{details['appointment_type'].replace('_', ' ').title()} - {details['patient_name']}",
                "description": f"Phone: {details['patient_phone']}\nType: {details['appointment_type']}",
                "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            },
        )
        .execute()
    )

    return {
        "success": True,
        "event_id": event["id"],
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
