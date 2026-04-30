"""Reusable channel descriptors (where the agent can talk back to the user)."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TelegramPrivateChannel(BaseModel):
    """A pre-bound Telegram private chat (bot account + chat id)."""

    model_config = ConfigDict(extra="allow")

    type: Literal["telegram_private_chat"]
    integration_account_id: UUID
    chat_id: str


class WebChatChannel(BaseModel):
    """A pre-bound in-app web chat session (user + persona + job thread)."""

    model_config = ConfigDict(extra="allow")

    type: Literal["web_chat"]
    user_id: int
    cyber_identity_id: UUID
    job_assignment_id: UUID


class InstagramDmChannel(BaseModel):
    """A pre-bound Instagram DM thread (IG business account + sender IGSID)."""

    model_config = ConfigDict(extra="allow")

    type: Literal["instagram_dm"]
    integration_account_id: UUID
    recipient_igsid: str


Channel = Annotated[
    TelegramPrivateChannel | WebChatChannel | InstagramDmChannel,
    Field(discriminator="type"),
]
