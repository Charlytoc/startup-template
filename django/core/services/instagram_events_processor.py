"""Route inbound Instagram DMs: resolve Conversation, persist user Message, enqueue agent."""

from __future__ import annotations

from typing import Any

from core.models import CyberIdentity, IntegrationAccount, JobAssignment
from core.services.conversations import (
    append_user_message,
    get_or_create_active_conversation,
)
from core.services.job_task_processor_agent import JobTaskProcessorAgent
from core.tasks.job_assignment_agent import run_job_assignment_agent


def _job_primary_identity(job: JobAssignment) -> CyberIdentity | None:
    cfg = job.get_config()
    if not cfg.identities:
        return None
    first = cfg.identities[0]
    return CyberIdentity.objects.filter(id=first.id, workspace=job.workspace).first()


def process_instagram_dm(
    *,
    account: IntegrationAccount,
    messaging: dict[str, Any],
    sender_igsid: str,
) -> None:
    """Resolve conversation, persist the user message, enqueue the agent."""
    message = messaging.get("message") or {}
    text = (message.get("text") or "").strip()

    job = JobTaskProcessorAgent.first_runnable_job_for_instagram_dm(account)
    if job is None:
        return

    identity = _job_primary_identity(job)
    if identity is None:
        return

    convo = get_or_create_active_conversation(
        account=account,
        cyber_identity=identity,
        external_thread_id=sender_igsid,
        external_user_id=sender_igsid,
    )

    user_msg = append_user_message(
        convo,
        content_text=text,
        content_structured={"instagram_message": messaging},
    )

    run_job_assignment_agent.delay(
        str(job.id),
        str(convo.id),
        str(user_msg.id),
    )
