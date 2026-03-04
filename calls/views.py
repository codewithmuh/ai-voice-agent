import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .agent.receptionist import handle_conversation_turn

logger = logging.getLogger(__name__)


@csrf_exempt
def vapi_webhook(request):
    """Handle incoming Vapi webhook events."""
    if request.method == "GET":
        return JsonResponse({"status": "ok", "service": "AI Voice Receptionist"})

    data = json.loads(request.body)
    message = data.get("message", {})

    if message.get("type") == "conversation-update":
        transcript = message.get("transcript", [])

        history = [
            {
                "role": "assistant" if turn["role"] == "assistant" else "user",
                "content": turn["content"],
            }
            for turn in transcript
        ]

        agent_response = handle_conversation_turn(history)

        return JsonResponse(
            {
                "messageResponse": {
                    "assistantMessage": {
                        "content": agent_response,
                    },
                },
            }
        )

    if message.get("type") == "end-of-call-report":
        call = message.get("call", {})
        logger.info(f"Call ended: {call.get('id')} | Duration: {call.get('duration')}s")

    return JsonResponse({})
