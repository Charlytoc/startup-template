"""Pydantic shapes for ``Conversation.config`` (flexible per-channel config bag)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationConfig(BaseModel):
    """Per-conversation runtime config.

    For integration-backed conversations (``Conversation.origin == "integration"``)
    both ``external_thread_id`` and ``external_user_id`` should be set so incoming/outgoing
    messages can be routed unambiguously (e.g. Telegram: ``chat_id`` + ``from.id``).

    For web-chat conversations (``origin == "web"``) there is no external provider; instead
    ``web_user_id`` identifies the app user that owns the conversation.
    """

    model_config = ConfigDict(extra="allow")

    external_thread_id: str | None = Field(
        default=None,
        description="External thread identifier on the provider (e.g. Telegram chat_id).",
    )
    external_user_id: str | None = Field(
        default=None,
        description="External user identifier of the counterpart (e.g. Telegram from.id).",
    )
    web_user_id: int | None = Field(
        default=None,
        description="Our app user id when origin='web'.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form extra config for this conversation (tone overrides, tools, etc.).",
    )
