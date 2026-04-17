"""Decide what (if anything) to do with an inbound Telegram message from an approved sender.

Current scope is intentionally minimal: detect whether the workspace has any usable task
defined; if not, reply with a fixed message so the user knows the bot is alive but idle.
Real task routing/execution will be added later.
"""

from __future__ import annotations

from typing import Any

from core.models import IntegrationAccount, JobAssignment
from core.services.telegram_bot import get_bot_token, telegram_send_message

NO_TASKS_REPLY = (
    "This bot has any defined tasks configured, please define something to "
    "start using your bot as an expert."
)


def _workspace_has_enabled_jobs(account: IntegrationAccount) -> bool:
    return JobAssignment.objects.filter(
        workspace=account.workspace,
        enabled=True,
    ).exists()


def process_approved_message(account: IntegrationAccount, message: dict[str, Any]) -> None:
    """Route an approved inbound message. For now: reply only when the workspace has no tasks."""
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    if _workspace_has_enabled_jobs(account):
        return

    bot_token = get_bot_token(account)
    if not bot_token:
        return
    telegram_send_message(bot_token, chat_id, NO_TASKS_REPLY)
