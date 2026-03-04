import json
import logging
import anthropic
from .tools import TOOLS
from .prompts import RECEPTIONIST_PROMPT
from ..services.calendar import check_availability, book_appointment
from ..services.sms import send_sms
from ..services.database import log_call

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()


def handle_conversation_turn(conversation_history: list) -> str:
    """Run the agentic loop — Claude keeps calling tools until done."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=RECEPTIONIST_PROMPT,
        tools=TOOLS,
        messages=conversation_history,
    )

    while response.stop_reason == "tool_use":
        tool_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if not tool_block:
            break

        logger.info(f"[TOOL] {tool_block.name} {json.dumps(tool_block.input)}")
        tool_result = execute_tool(tool_block.name, tool_block.input)
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
            max_tokens=300,
            system=RECEPTIONIST_PROMPT,
            tools=TOOLS,
            messages=conversation_history,
        )

    text_block = next((b for b in response.content if b.type == "text"), None)
    return text_block.text if text_block else ""


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
