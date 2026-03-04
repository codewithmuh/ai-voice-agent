import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

_twilio_client = None


def get_twilio_client():
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return _twilio_client


def send_sms(to: str, message: str) -> dict:
    client = get_twilio_client()
    result = client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to,
    )
    return {"success": True, "sid": result.sid}
