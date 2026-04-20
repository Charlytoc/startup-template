"""Pydantic shapes for ``Conversation.config`` (flexible per-channel config bag)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationConfig(BaseModel):
    """Per-conversation runtime config. Holds the external thread/user ids plus future extensions.

    ``external_thread_id`` and ``external_user_id`` are **required** because every conversation
    lives against one ``IntegrationAccount`` and we need both ids to route incoming/outgoing
    messages unambiguously (e.g. Telegram: ``chat_id`` + ``from.id``).
    """

    model_config = ConfigDict(extra="allow")

    external_thread_id: str = Field(
        ...,
        min_length=1,
        description="External thread identifier on the provider (e.g. Telegram chat_id).",
    )
    external_user_id: str = Field(
        ...,
        min_length=1,
        description="External user identifier of the counterpart (e.g. Telegram from.id).",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form extra config for this conversation (tone overrides, tools, etc.).",
    )
