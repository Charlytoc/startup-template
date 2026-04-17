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


EVENT_TYPES: dict[str, IntegrationEventType] = {
    e.slug: e
    for e in (TELEGRAM_PRIVATE_MESSAGE,)
}


def get_event_type(slug: str) -> IntegrationEventType | None:
    return EVENT_TYPES.get(slug)
