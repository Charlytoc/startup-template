"""Conversation/Message service: resolve, append and archive workspace conversations.

This layer decouples the rest of the code from how conversations are persisted. The
old event-based history builder (:mod:`core.services.telegram_private_message_history`)
used ``IntegrationEvent`` rows as both raw ingestion log AND conversation store, which
coupled "things the provider told us" with "things we produced". Now:

- ``IntegrationEvent`` = raw provider snapshot only.
- ``Conversation`` + ``Message`` = durable dialog (both user and assistant turns).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from core.models import Conversation, CyberIdentity, IntegrationAccount, Message
from core.schemas.agentic_chat import ExchangeMessage
from core.schemas.conversation import ConversationConfig

logger = logging.getLogger(__name__)


def find_active_conversation(
    *,
    account: IntegrationAccount,
    external_thread_id: str,
) -> Conversation | None:
    """Return the most recent ``ACTIVE`` conversation for ``(account, external_thread_id)``."""
    return (
        Conversation.objects.filter(
            integration_account=account,
            status=Conversation.Status.ACTIVE,
            config__external_thread_id=external_thread_id,
        )
        .order_by("-last_interaction_at", "-created")
        .first()
    )


def get_or_create_active_conversation(
    *,
    account: IntegrationAccount,
    cyber_identity: CyberIdentity,
    external_thread_id: str,
    external_user_id: str,
) -> Conversation:
    """Return the active conversation for the thread, creating one when none exists."""
    existing = find_active_conversation(account=account, external_thread_id=external_thread_id)
    if existing is not None:
        return existing

    cfg = ConversationConfig(
        external_thread_id=external_thread_id,
        external_user_id=external_user_id,
    )
    with transaction.atomic():
        convo = Conversation(
            workspace=account.workspace,
            integration_account=account,
            cyber_identity=cyber_identity,
            status=Conversation.Status.ACTIVE,
        )
        convo.set_config(cfg)
        convo.save()
    logger.info(
        "conversations: created conversation=%s account=%s thread=%s",
        convo.id, account.id, external_thread_id,
    )
    return convo


def archive_conversation(conversation: Conversation) -> None:
    """Mark the conversation as ``ARCHIVED`` (e.g. user requested a context reset)."""
    if conversation.status == Conversation.Status.ARCHIVED:
        return
    conversation.status = Conversation.Status.ARCHIVED
    conversation.closed_at = timezone.now()
    conversation.save(update_fields=["status", "closed_at", "modified"])


def append_user_message(
    conversation: Conversation,
    *,
    content_text: str = "",
    content_structured: dict[str, Any] | list[Any] | None = None,
) -> Message:
    return _append_message(
        conversation,
        role=Message.Role.USER,
        content_text=content_text,
        content_structured=content_structured,
    )


def append_assistant_message(
    conversation: Conversation,
    *,
    content_text: str = "",
    content_structured: dict[str, Any] | list[Any] | None = None,
) -> Message:
    return _append_message(
        conversation,
        role=Message.Role.ASSISTANT,
        content_text=content_text,
        content_structured=content_structured,
    )


def _append_message(
    conversation: Conversation,
    *,
    role: str,
    content_text: str,
    content_structured: dict[str, Any] | list[Any] | None,
) -> Message:
    with transaction.atomic():
        msg = Message.objects.create(
            conversation=conversation,
            role=role,
            content_text=content_text or "",
            content_structured=content_structured,
        )
        conversation.last_interaction_at = msg.created
        conversation.save(update_fields=["last_interaction_at", "modified"])
    return msg


def prior_exchange_messages(
    conversation: Conversation,
    *,
    exclude_message_id: UUID | None = None,
    max_messages: int = 40,
) -> list[ExchangeMessage]:
    """Return messages in the conversation as :class:`ExchangeMessage` (oldest first).

    ``exclude_message_id`` lets the caller skip the current triggering message (so the caller
    can append a richer user-turn version later).
    """
    qs = Message.objects.filter(conversation=conversation).order_by("created")
    if exclude_message_id is not None:
        qs = qs.exclude(id=exclude_message_id)
    rows = list(qs[:max_messages])

    out: list[ExchangeMessage] = []
    for m in rows:
        text = (m.content_text or "").strip()
        if not text and m.content_structured is None:
            continue
        out.append(ExchangeMessage(role=m.role, content=text or m.content_structured or ""))
    return out
