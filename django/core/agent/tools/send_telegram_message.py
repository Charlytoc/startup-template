"""Tool: send a Telegram text message to a pre-bound private chat (bot token + chat id)."""

from __future__ import annotations

import logging

from core.agent.base import AgentTool, AgentToolConfig
from core.models import IntegrationAccount
from core.services.telegram_bot import record_private_message_sent_event, telegram_send_message

logger = logging.getLogger(__name__)


def make_send_telegram_message_tool(
    *,
    bot_token: str,
    chat_id: int | str,
    integration_account: IntegrationAccount,
) -> AgentToolConfig:
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
        try:
            msg_result = telegram_send_message(bot_token, chat_id, text)
        except ValueError as exc:
            return f"Error: {exc}"
        try:
            record_private_message_sent_event(integration_account, msg_result)
        except Exception:
            logger.exception(
                "record_private_message_sent_event failed account=%s chat_id=%s",
                integration_account.id,
                chat_id,
            )
        return "Message sent successfully."

    return AgentToolConfig(tool=tool, function=execute)
