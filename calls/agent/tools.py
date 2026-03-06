TOOLS = [
    {
        "name": "check_availability",
        "description": "Check available appointment slots on Google Calendar for a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date to check, in YYYY-MM-DD format",
                },
            },
            "required": ["date"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment on Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Time in HH:MM format (24hr)"},
                "patient_name": {"type": "string", "description": "Full name of patient"},
                "patient_phone": {"type": "string", "description": "Phone number of patient"},
                "appointment_type": {
                    "type": "string",
                    "enum": ["new_patient", "returning", "emergency"],
                    "description": "Type of appointment",
                },
            },
            "required": ["date", "time", "patient_name", "patient_phone", "appointment_type"],
        },
    },
    {
        "name": "send_sms",
        "description": "Send an SMS confirmation to the patient.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Phone number to send SMS to"},
                "message": {"type": "string", "description": "The SMS message body"},
            },
            "required": ["to", "message"],
        },
    },
    {
        "name": "log_call",
        "description": "Log call details to the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "caller_phone": {"type": "string"},
                "call_summary": {"type": "string"},
                "appointment_booked": {"type": "boolean"},
                "duration_seconds": {"type": "number"},
            },
            "required": ["caller_phone", "call_summary", "appointment_booked"],
        },
    },
    {
        "name": "end_call",
        "description": "End the phone call. Use this after saying goodbye to the caller so the call disconnects automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why the call is ending, e.g. 'booking_complete', 'caller_goodbye', 'no_further_questions'",
                },
            },
            "required": ["reason"],
        },
    },
]
