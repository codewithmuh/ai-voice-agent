import json
import logging
import uuid
import time
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .agent.receptionist import handle_conversation_turn
from .services.calendar import check_availability, book_appointment
from .services.sms import send_sms
from .services.database import log_call

logger = logging.getLogger(__name__)


def openai_messages_to_claude(messages: list) -> list:
    """Convert OpenAI-format messages to Claude-format messages."""
    claude_messages = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Skip system messages (we use our own system prompt)
        if role == "system":
            continue

        # Map OpenAI roles to Claude roles
        if role == "assistant":
            claude_messages.append({"role": "assistant", "content": content or ""})
        elif role in ("user", "human"):
            claude_messages.append({"role": "user", "content": content or ""})

    return claude_messages


@csrf_exempt
def chat_completions(request):
    """OpenAI-compatible chat completions endpoint for Vapi custom LLM."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    messages = data.get("messages", [])
    logger.info(f"[CUSTOM LLM] Received {len(messages)} messages")

    # Extract caller phone from VAPI call metadata or request
    caller_phone = None
    call_data = data.get("call", {})
    if call_data:
        caller_phone = call_data.get("customer", {}).get("number")
    # Fallback: check metadata
    if not caller_phone:
        metadata = data.get("metadata", {})
        caller_phone = metadata.get("customerNumber")
    if caller_phone:
        logger.info(f"[CUSTOM LLM] Caller phone: {caller_phone}")

    if not messages:
        return JsonResponse({"error": "No messages provided"}, status=400)

    # Convert OpenAI messages to Claude format
    claude_messages = openai_messages_to_claude(messages)

    if not claude_messages:
        return JsonResponse({"error": "No valid messages after conversion"}, status=400)

    # Ensure conversation starts with user message
    if claude_messages[0]["role"] != "user":
        claude_messages.insert(0, {"role": "user", "content": "Hello"})

    # Ensure alternating roles (Claude requires this)
    fixed_messages = []
    for msg in claude_messages:
        if fixed_messages and fixed_messages[-1]["role"] == msg["role"]:
            # Merge consecutive same-role messages
            fixed_messages[-1]["content"] += "\n" + msg["content"]
        else:
            fixed_messages.append(msg)

    logger.info(f"[CUSTOM LLM] Calling Claude with {len(fixed_messages)} messages")

    try:
        # Run the full agentic loop (Claude + tools)
        result = handle_conversation_turn(fixed_messages, caller_phone=caller_phone)
        response_text = result["text"]
        end_call = result["end_call"]
        logger.info(f"[CUSTOM LLM] Claude response: {response_text[:100]}... end_call={end_call}")
    except Exception as e:
        logger.error(f"[CUSTOM LLM ERROR] {e}")
        response_text = "I'm sorry, I'm having a technical issue right now. Please try calling back in a moment."
        end_call = False

    # Check if streaming was requested
    if data.get("stream", False):
        return _stream_response(response_text, end_call)

    # Return in OpenAI chat completions format
    return JsonResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "claude-sonnet-4-20250514",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    })


def _stream_response(text: str, end_call: bool = False):
    """Return a streaming response in OpenAI SSE format."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    def event_stream():
        # Send the content in a single chunk
        chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "claude-sonnet-4-20250514",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": text},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(chunk)}\n\n"

        # Send the stop chunk
        stop_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "claude-sonnet-4-20250514",
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        yield f"data: {json.dumps(stop_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )

    # Signal VAPI to end the call after this response
    if end_call:
        response["X-Vapi-End-Call"] = "true"

    return response


@csrf_exempt
def vapi_webhook(request):
    """Handle incoming Vapi webhook events (end-of-call, status updates)."""
    if request.method == "GET":
        return JsonResponse({"status": "ok", "service": "AI Voice Receptionist"})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = data.get("message", {})
    msg_type = message.get("type", "unknown")

    logger.info(f"[WEBHOOK] type={msg_type}")

    # Handle end-of-call report
    if msg_type == "end-of-call-report":
        call = message.get("call", {})
        summary = message.get("summary", "")
        transcript = message.get("transcript", "")
        caller_phone = call.get("customer", {}).get("number", "unknown")
        # VAPI sends duration in different places depending on version
        duration = call.get("duration") or message.get("durationSeconds") or message.get("duration")
        # Also check cost breakdown
        if not duration:
            cost = message.get("costBreakdown", {})
            duration = cost.get("duration") or cost.get("durationSeconds")

        logger.info(f"[CALL ENDED] id={call.get('id')} duration={duration}s phone={caller_phone}")

        try:
            log_call({
                "caller_phone": caller_phone,
                "call_summary": summary or transcript or "No summary available",
                "appointment_booked": False,
                "duration_seconds": int(duration) if duration else None,
            })
            logger.info("[CALL LOGGED] Successfully saved to database")
        except Exception as e:
            logger.error(f"[LOG ERROR] {e}")

    return JsonResponse({})


def execute_tool(name: str, tool_input: dict) -> dict:
    match name:
        case "check_availability":
            return check_availability(tool_input["date"])
        case "book_appointment":
            return book_appointment(tool_input)
        case "send_sms":
            return send_sms(tool_input["to"], tool_input["message"])
        case "log_call":
            return log_call(tool_input)
        case _:
            return {"error": f"Unknown tool: {name}"}
