"""Tool: send an Instagram DM to the Conversation's bound thread and persist the reply."""

from __future__ import annotations

import logging

from core.agent.base import AgentTool, AgentToolConfig
from core.models import Conversation
from core.services.conversations import append_assistant_message
from core.services.instagram_service import instagram_send_message

logger = logging.getLogger(__name__)


def make_send_instagram_message_tool(
    *,
    access_token: str,
    ig_user_id: str,
    conversation: Conversation,
) -> AgentToolConfig:
    """Return a tool named ``send_instagram_message`` bound to this conversation's DM thread."""
    cfg = conversation.get_config()
    recipient_igsid = cfg.external_thread_id

    tool = AgentTool(
        type="function",
        name="send_instagram_message",
        description=(
            "Send a plain-text reply to the current Instagram DM thread. "
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
            sent = instagram_send_message(access_token, ig_user_id, recipient_igsid, text)
        except ValueError as exc:
            return f"Error: {exc}"
        try:
            append_assistant_message(
                conversation,
                content_text=text,
                content_structured={"instagram_sent": sent},
            )
        except Exception:
            logger.exception(
                "append_assistant_message failed conversation=%s recipient=%s",
                conversation.id, recipient_igsid,
            )
        return "Message sent successfully."

    return AgentToolConfig(tool=tool, function=execute)
