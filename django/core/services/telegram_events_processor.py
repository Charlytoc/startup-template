"""Route approved inbound Telegram traffic: enqueue job agent or fall back to a fixed reply."""

from __future__ import annotations

import json
from typing import Any

from core.models import IntegrationAccount, JobAssignment
from core.services.job_task_processor_agent import JobTaskProcessorAgent
from core.services.telegram_bot import get_bot_token, telegram_send_message
from core.tasks.job_assignment_agent import run_job_assignment_agent

NO_TASKS_REPLY = (
    "This bot has any defined tasks configured, please define something to "
    "start using your bot as an expert."
)


def _workspace_has_configured_jobs(account: IntegrationAccount) -> bool:
    """True when the workspace has at least one enabled job with identities and actions (may not match this bot)."""
    for job in JobAssignment.objects.filter(workspace=account.workspace, enabled=True).iterator():
        cfg = job.config or {}
        acts = cfg.get("actions") or []
        ids = cfg.get("identities") or []
        if isinstance(acts, list) and len(acts) > 0 and isinstance(ids, list) and len(ids) > 0:
            return True
    return False


def process_approved_message(account: IntegrationAccount, message: dict[str, Any]) -> None:
    """Dispatch to the job agent when a runnable job exists; otherwise fixed copy or silence."""
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
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
