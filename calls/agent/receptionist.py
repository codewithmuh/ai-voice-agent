import json
import logging
import threading
import anthropic
from .tools import TOOLS
from .prompts import get_receptionist_prompt
from ..services.calendar import check_availability, book_appointment
from ..services.sms import send_sms
from ..services.database import log_call

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()


def handle_conversation_turn(conversation_history: list, caller_phone: str = None) -> dict:
    """Run the agentic loop — Claude keeps calling tools until done.
    Returns {"text": str, "end_call": bool}."""
    system_prompt = get_receptionist_prompt()
    if caller_phone:
        system_prompt += f"\n\nCALLER INFO:\n- The caller's phone number is {caller_phone}. Use this number for booking and SMS by default. Just confirm: \"We'll send a confirmation to the number you're calling from. Would you like it sent to a different number instead?\""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        tools=TOOLS,
        messages=conversation_history,
    )

    should_end_call = False
    last_tool_name = None

    while response.stop_reason == "tool_use":
        tool_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if not tool_block:
            break

        # Handle end_call — collect any text before it and signal hangup
        if tool_block.name == "end_call":
            logger.info(f"[END_CALL] reason={tool_block.input.get('reason', 'unknown')}")
            should_end_call = True
            break

        last_tool_name = tool_block.name
        logger.info(f"[TOOL] {tool_block.name} {json.dumps(tool_block.input)}")
        try:
            tool_result = execute_tool(tool_block.name, tool_block.input)
        except Exception as e:
            logger.error(f"[TOOL ERROR] {tool_block.name}: {e}")
            tool_result = {"error": str(e)}
        logger.info(f"[RESULT] {json.dumps(tool_result)}")

        conversation_history.append(
            {"role": "assistant", "content": response.to_dict()["content"]}
        )
        conversation_history.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(tool_result),
                    }
                ],
            }
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=conversation_history,
        )

    text_block = next((b for b in response.content if b.type == "text"), None)
    response_text = text_block.text.strip() if text_block else ""

    # Fallback: if Claude returned empty text after tools, provide a sensible response
    if not response_text and last_tool_name:
        logger.warning(f"[EMPTY RESPONSE] after tool={last_tool_name}, using fallback")
        if last_tool_name in ("book_appointment", "send_sms"):
            response_text = "You're all set! Your appointment is confirmed and I've sent you a text with the details. Is there anything else I can help with?"
        else:
            response_text = "Is there anything else I can help you with?"

    return {
        "text": response_text,
        "end_call": should_end_call,
    }


def execute_tool(name: str, tool_input: dict) -> dict:
    match name:
        case "check_availability":
            return check_availability(tool_input["date"])
        case "book_appointment":
            return book_appointment(tool_input)
        case "send_sms":
            # Fire SMS in background to avoid blocking the voice response
            # Twilio can take 5-10s which triggers VAPI idle timeout
            threading.Thread(
                target=send_sms,
                args=(tool_input["to"], tool_input["message"]),
                daemon=True,
            ).start()
            return {"success": True, "message": "SMS is being sent"}
        case "log_call":
            threading.Thread(target=log_call, args=(tool_input,)).start()
            return {"success": True, "message": "Call logged"}
        case _:
            return {"error": f"Unknown tool: {name}"}
