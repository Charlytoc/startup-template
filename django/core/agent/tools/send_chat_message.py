"""Tool: send a message to the in-app web chat UI and persist it as an assistant Message."""

from __future__ import annotations

import logging

from core.agent.base import AgentTool, AgentToolConfig
from core.models import Conversation
from core.services.conversations import append_assistant_message
from core.services.redis_publisher import publish_to_bridge

logger = logging.getLogger(__name__)


def make_send_chat_message_tool(
    *,
    conversation: Conversation,
    user_id: int,
) -> AgentToolConfig:
    """Return a tool named ``send_chat_message`` bound to this web-chat conversation.

    On invocation:
    - Persists an **assistant** :class:`Message` on the conversation.
    - Publishes an ``agentic-chat-message`` event on the ``user-<id>`` bridge listener so the
      web client receives it in real time over the websocket.
    """
    tool = AgentTool(
        type="function",
        name="send_chat_message",
        description=(
            "Send a plain-text reply to the user in the in-app web chat. "
            "The destination is already fixed; only supply the message body."
        ),
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Full text of the message to show to the user in the chat UI.",
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
            msg = append_assistant_message(conversation, content_text=text)
        except Exception:
            logger.exception(
                "append_assistant_message failed conversation=%s user=%s",
                conversation.id, user_id,
            )
            return "Error: failed to persist message."
        try:
            created_iso = msg.created.isoformat() if msg.created else ""
            publish_to_bridge(
                listener=f"user-{user_id}",
                event="agentic-chat-message",
                data={
                    "conversation_id": str(conversation.id),
                    "message_id": str(msg.id),
                    "message": {
                        "role": "assistant",
                        "content": text,
                        "created": created_iso,
                    },
                    "timestamp": created_iso,
                },
            )
        except Exception:
            logger.exception(
                "publish_to_bridge failed conversation=%s user=%s",
                conversation.id, user_id,
            )
        return "Message sent successfully."

    return AgentToolConfig(tool=tool, function=execute)
