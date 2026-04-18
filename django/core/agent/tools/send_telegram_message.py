"""Tool: send a Telegram text message to a pre-bound private chat (bot token + chat id)."""

from __future__ import annotations

from core.agent.base import AgentTool, AgentToolConfig
from core.services.telegram_bot import telegram_send_message


def make_send_telegram_message_tool(*, bot_token: str, chat_id: int | str) -> AgentToolConfig:
    """Return a tool named ``send_telegram_message`` scoped to this bot and chat."""

    tool = AgentTool(
        type="function",
        name="send_telegram_message",
        description=(
            "Send a plain-text reply to the current Telegram private chat. "
            "The destination is already fixed to the user you are assisting; only supply the message body."
        ),
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Full text of the message to send to the user.",
                },
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    )

    def execute(message: str) -> str:
        text = (message or "").strip()
        if not text:
            return "Error: message must be non-empty."
        telegram_send_message(bot_token, chat_id, text)
        return "Message sent successfully."

    return AgentToolConfig(tool=tool, function=execute)
