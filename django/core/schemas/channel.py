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


Channel = Annotated[TelegramPrivateChannel, Field(discriminator="type")]
