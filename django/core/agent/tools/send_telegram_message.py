"""Tool: send a Telegram text message to the Conversation's bound chat and persist the reply."""

from __future__ import annotations

import logging

from core.agent.base import AgentTool, AgentToolConfig
from core.models import Conversation
from core.services.conversations import append_assistant_message
from core.services.telegram_bot import telegram_send_message

logger = logging.getLogger(__name__)


def make_send_telegram_message_tool(
    *,
    bot_token: str,
    conversation: Conversation,
) -> AgentToolConfig:
    """Return a tool named ``send_telegram_message`` bound to this conversation's chat + bot.

    The conversation carries everything needed to send and persist the reply:

    - ``conversation.integration_account`` identifies the bot workspace-side.
    - ``conversation.config.external_thread_id`` is the Telegram ``chat_id``.
    - After a successful send, an **assistant** :class:`Message` is appended to the conversation.
    """
    cfg = conversation.get_config()
    chat_id = cfg.external_thread_id

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
            sent = telegram_send_message(bot_token, chat_id, text)
        except ValueError as exc:
            return f"Error: {exc}"
        try:
            append_assistant_message(
                conversation,
                content_text=text,
                content_structured={"telegram_sent": sent},
            )
        except Exception:
            logger.exception(
                "append_assistant_message failed conversation=%s chat_id=%s",
                conversation.id, chat_id,
            )
        return "Message sent successfully."

    return AgentToolConfig(tool=tool, function=execute)
