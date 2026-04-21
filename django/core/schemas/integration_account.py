"""Pydantic shapes for ``IntegrationAccount.config`` (per-provider plaintext JSON)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SenderApprovalStatus(str, Enum):
    """Lifecycle state of an external sender known to an :class:`IntegrationAccount`.

    ``PENDING``      — seen but not yet cleared (e.g. Telegram waiting for approval code).
    ``NOT_REQUIRED`` — provider has no approval gate (e.g. Instagram DMs today).
    ``APPROVED``     — sender may freely reach the bound jobs on this account.
    """

    PENDING = "pending"
    NOT_REQUIRED = "not_required"
    APPROVED = "approved"


class IntegrationAccountSender(BaseModel):
    """One external counterpart we have observed on an integration account.

    ``external_thread_id`` is the provider identifier used for routing (Telegram ``chat_id``,
    Instagram IGSID, ...).     ``extractions`` is a free-form JSON bag that future agent tools
    (``*.extract_user_context``) can fill with arbitrary data about the counterpart.
    Instagram inbound traffic may set ``instagram_user_profile`` (``username``, ``name`` from Graph).

    ``handle`` is a human-oriented id string for display or future tools (Telegram: ``@username``
    when present, else numeric ``from.id``; Instagram: ``@username`` from the webhook when
    present, otherwise from the Instagram User Profile API for the sender IGSID when allowed).
    """

    model_config = ConfigDict(extra="allow")

    external_thread_id: str
    approval_status: SenderApprovalStatus
    handle: str | None = None
    extractions: dict[str, Any] = Field(default_factory=dict)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class BaseIntegrationAccountConfig(BaseModel):
    """Common shape of ``IntegrationAccount.config`` regardless of provider."""

    model_config = ConfigDict(extra="allow")

    senders: list[IntegrationAccountSender] = Field(default_factory=list)


class TelegramAccountConfig(BaseIntegrationAccountConfig):
    webhook_path_token: str | None = None


class InstagramAccountConfig(BaseIntegrationAccountConfig):
    ig_user_id: str | None = None
    ig_username: str | None = None
    ig_oauth_graph_me_id: str | None = None
