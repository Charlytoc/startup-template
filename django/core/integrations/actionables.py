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


TASKS_SCHEDULE_ONE_OFF = Actionable(
    slug="tasks.schedule_one_off",
    provider="system",
    name="Schedule a one-off task",
    description=(
        "Let the agent schedule a future one-off task (e.g. reminders). "
        "Runs once at the specified offset and inherits the current job's channel and capabilities."
    ),
)

TASKS_CREATE_RECURRING_JOB = Actionable(
    slug="tasks.create_recurring_job",
    provider="system",
    name="Create a recurring job (cron)",
    description=(
        "Let the agent create a new JobAssignment that fires on a cron schedule "
        "(e.g. 'every Mon/Wed/Fri at 12:00'), inheriting accounts, identities and actions from the parent job."
    ),
)


SYSTEM_SEND_CHAT_MESSAGE = Actionable(
    slug="system.send_chat_message",
    provider="system",
    name="Send web chat message",
    description=(
        "Deliver a message to the user via the in-app web chat UI. "
        "The destination (user + conversation) is already bound; the agent only supplies the body."
    ),
)


ACTIONABLES: dict[str, Actionable] = {
    a.slug: a
    for a in (
        TELEGRAM_SEND_MESSAGE,
        TASKS_SCHEDULE_ONE_OFF,
        TASKS_CREATE_RECURRING_JOB,
        SYSTEM_SEND_CHAT_MESSAGE,
    )
}


def get_actionable(slug: str) -> Actionable | None:
    return ACTIONABLES.get(slug)
