from ..models import CallLog


def log_call(details: dict) -> dict:
    call = CallLog.objects.create(
        caller_phone=details["caller_phone"],
        call_summary=details["call_summary"],
        appointment_booked=details["appointment_booked"],
        duration_seconds=details.get("duration_seconds"),
    )
    return {"success": True, "call_id": call.id}
