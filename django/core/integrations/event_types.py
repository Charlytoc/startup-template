"""Catalogue of integration event types. The ``slug`` is what gets stored in ``IntegrationEvent.event_type``."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationEventType:
    slug: str
    provider: str
    description: str


TELEGRAM_PRIVATE_MESSAGE = IntegrationEventType(
    slug="telegram.private_message",
    provider="telegram",
    description="A private message was received by a connected Telegram bot from an approved sender.",
)

TELEGRAM_PRIVATE_MESSAGE_SENT = IntegrationEventType(
    slug="telegram.private_message_sent",
    provider="telegram",
    description="The bot sent a private message (e.g. job agent reply via sendMessage).",
)

TELEGRAM_PRIVATE_MESSAGE_CONTEXT_RESET = IntegrationEventType(
    slug="telegram.private_message_context_reset",
    provider="telegram",
    description="The user requested clearing prior private-chat context.",
)


EVENT_TYPES: dict[str, IntegrationEventType] = {
    e.slug: e
    for e in (
        TELEGRAM_PRIVATE_MESSAGE,
        TELEGRAM_PRIVATE_MESSAGE_SENT,
        TELEGRAM_PRIVATE_MESSAGE_CONTEXT_RESET,
    )
}


def get_event_type(slug: str) -> IntegrationEventType | None:
    return EVENT_TYPES.get(slug)
