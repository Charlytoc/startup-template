"""Catalogue of actionables (agent capabilities). Referenced by slug from ``JobAssignment.config['actions']``.

Handlers/input schemas are intentionally omitted for now: this is just the static catalogue
so the rest of the system can validate slugs and expose them in the UI. Runtime wiring
lands together with the task runner.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Actionable:
    slug: str
    provider: str
    name: str
    description: str


TELEGRAM_SEND_MESSAGE = Actionable(
    slug="telegram.send_message",
    provider="telegram",
    name="Send Telegram message",
    description="Send a text message from a connected Telegram bot to a chat id the agent already knows.",
)


ACTIONABLES: dict[str, Actionable] = {
    a.slug: a
    for a in (TELEGRAM_SEND_MESSAGE,)
}


def get_actionable(slug: str) -> Actionable | None:
    return ACTIONABLES.get(slug)
