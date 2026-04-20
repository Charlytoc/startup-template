"""Build agent context from stored ``IntegrationEvent`` rows (inbound + outbound Telegram private chat)."""

from __future__ import annotations

from typing import Any

from core.integrations.event_types import (
    TELEGRAM_PRIVATE_MESSAGE,
    TELEGRAM_PRIVATE_MESSAGE_CONTEXT_RESET,
    TELEGRAM_PRIVATE_MESSAGE_SENT,
)
from core.models import IntegrationAccount, IntegrationEvent
from core.schemas.agentic_chat import ExchangeMessage


def _inner_message(payload: dict[str, Any]) -> dict[str, Any]:
    """Payload may store ``message`` at top level or under ``update.message``."""
    msg = payload.get("message")
    if isinstance(msg, dict):
        return msg
    upd = payload.get("update")
    if isinstance(upd, dict):
        inner = upd.get("message")
        if isinstance(inner, dict):
            return inner
    return {}


def chat_id_from_payload(payload: dict[str, Any]) -> int | None:
    chat = _inner_message(payload).get("chat") or {}
    cid = chat.get("id")
    if cid is None:
        return None
    try:
        return int(cid)
    except (TypeError, ValueError):
        return None


def message_id_from_payload(payload: dict[str, Any]) -> int | None:
    mid = _inner_message(payload).get("message_id")
    if mid is None:
        return None
    try:
        return int(mid)
    except (TypeError, ValueError):
        return None


def text_from_payload(payload: dict[str, Any]) -> str:
    m = _inner_message(payload)
    return (m.get("text") or m.get("caption") or "").strip()


def _chat_message_ids(message: dict[str, Any]) -> tuple[int | None, int | None]:
    chat = message.get("chat") or {}
    raw_chat_id = chat.get("id")
    raw_message_id = message.get("message_id")
    try:
        chat_id = int(raw_chat_id) if raw_chat_id is not None else None
    except (TypeError, ValueError):
        chat_id = None
    try:
        message_id = int(raw_message_id) if raw_message_id is not None else None
    except (TypeError, ValueError):
        message_id = None
    return chat_id, message_id


def record_private_chat_context_reset_event(
    account: IntegrationAccount,
    message: dict[str, Any],
    *,
    requested_by_telegram_user_id: int | None = None,
) -> None:
    """Persist a marker event used to trim prior chat context on future turns."""
    chat_id, message_id = _chat_message_ids(message)
    if chat_id is None:
        return
    external_id = f"{chat_id}:{message_id}" if message_id is not None else f"{chat_id}:reset"
    IntegrationEvent.objects.get_or_create(
        integration_account=account,
        event_type=TELEGRAM_PRIVATE_MESSAGE_CONTEXT_RESET.slug,
        external_event_id=external_id[:255],
        defaults={
            "payload": {
                "message": message,
                "requested_by_telegram_user_id": requested_by_telegram_user_id,
            }
        },
    )


def telegram_chat_id(message: dict[str, Any]) -> int | None:
    chat = message.get("chat") or {}
    cid = chat.get("id")
    if cid is None:
        return None
    try:
        return int(cid)
    except (TypeError, ValueError):
        return None


def prior_private_chat_exchange_messages(
    account: IntegrationAccount,
    chat_id: int,
    *,
    exclude_message_id: int | None,
    max_messages: int = 20,
) -> list[ExchangeMessage]:
    """Return prior private-chat turns from ``IntegrationEvent`` (user + assistant), oldest first.

    Inbound rows use ``telegram.private_message``; outbound tool sends use
    ``telegram.private_message_sent``. Context reset markers use
    ``telegram.private_message_context_reset`` and clear all prior turns for that chat.
    Pass ``exclude_message_id`` for the current inbound Telegram ``message_id`` so it is
    not duplicated before the rich current user turn is appended.
    """
    events = list(
        IntegrationEvent.objects.filter(
            integration_account=account,
            event_type__in=(
                TELEGRAM_PRIVATE_MESSAGE.slug,
                TELEGRAM_PRIVATE_MESSAGE_SENT.slug,
                TELEGRAM_PRIVATE_MESSAGE_CONTEXT_RESET.slug,
            ),
        ).order_by("-created")[:400]
    )
    events.reverse()

    out: list[ExchangeMessage] = []
    for ev in events:
        payload = ev.payload if isinstance(ev.payload, dict) else {}
        if chat_id_from_payload(payload) != chat_id:
            continue
        if ev.event_type == TELEGRAM_PRIVATE_MESSAGE_CONTEXT_RESET.slug:
            out.clear()
        elif ev.event_type == TELEGRAM_PRIVATE_MESSAGE.slug:
            mid = message_id_from_payload(payload)
            if exclude_message_id is not None and mid == exclude_message_id:
                continue
            text = text_from_payload(payload)
            if not text:
                continue
            out.append(ExchangeMessage(role="user", content=text))
        elif ev.event_type == TELEGRAM_PRIVATE_MESSAGE_SENT.slug:
            text = text_from_payload(payload)
            if not text:
                continue
            out.append(ExchangeMessage(role="assistant", content=text))

    return out[-max_messages:]
