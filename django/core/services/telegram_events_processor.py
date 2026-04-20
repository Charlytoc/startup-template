"""Route approved inbound Telegram traffic: enqueue job agent or fall back to a fixed reply."""

from __future__ import annotations

import json
from typing import Any

from core.models import IntegrationAccount, JobAssignment
from core.services.job_task_processor_agent import JobTaskProcessorAgent
from core.services.telegram_bot import get_bot_token, telegram_send_message
from core.services.telegram_private_message_history import (
    record_private_chat_context_reset_event,
)
from core.tasks.job_assignment_agent import run_job_assignment_agent

NO_TASKS_REPLY = (
    "This bot has any defined tasks configured, please define something to "
    "start using your bot as an expert."
)
CLEAR_CONTEXT_REPLY = "Done. I cleared our previous context. Send your next message."


def _workspace_has_configured_jobs(account: IntegrationAccount) -> bool:
    """True when the workspace has at least one enabled job with identities and actions (may not match this bot)."""
    for job in JobAssignment.objects.filter(workspace=account.workspace, enabled=True).iterator():
        cfg_model = job.get_config()
        if cfg_model.actions and cfg_model.identities:
            return True
    return False


def _is_clear_context_command(message: dict[str, Any]) -> bool:
    text = str(message.get("text") or "").strip().lower()
    if not text:
        return False
    command = text.split(maxsplit=1)[0]
    return command in {"/clear", "/clearcontext", "/reset"} or command.startswith("/clear@")


def process_approved_message(account: IntegrationAccount, message: dict[str, Any]) -> None:
    """Dispatch to the job agent when a runnable job exists; otherwise fixed copy or silence."""
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    if _is_clear_context_command(message):
        from_user = message.get("from") or {}
        raw_uid = from_user.get("id")
        try:
            telegram_user_id = int(raw_uid) if raw_uid is not None else None
        except (TypeError, ValueError):
            telegram_user_id = None
        record_private_chat_context_reset_event(
            account,
            message,
            requested_by_telegram_user_id=telegram_user_id,
        )
        bot_token = get_bot_token(account)
        if bot_token:
            telegram_send_message(bot_token, chat_id, CLEAR_CONTEXT_REPLY)
        return

    job = JobTaskProcessorAgent.first_runnable_job_for_telegram_private_message(account, message)
    if job is not None:
        run_job_assignment_agent.delay(
            str(job.id),
            str(account.id),
            json.dumps(message, default=str),
        )
        return

    if _workspace_has_configured_jobs(account):
        return

    bot_token = get_bot_token(account)
    if not bot_token:
        return
    telegram_send_message(bot_token, chat_id, NO_TASKS_REPLY)
