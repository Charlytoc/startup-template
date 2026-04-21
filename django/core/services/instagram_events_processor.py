"""Route inbound Instagram DMs: resolve Conversation, persist user Message, enqueue agent."""

from __future__ import annotations

import logging
from typing import Any

from core.models import CyberIdentity, IntegrationAccount, JobAssignment

logger = logging.getLogger(__name__)
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

    logger.info(
        "process_instagram_dm start integration_account_id=%s sender_igsid=%s text_len=%s mid=%s",
        account.id,
        sender_igsid,
        len(text),
        str(message.get("mid") or "")[:80],
    )

    job = JobTaskProcessorAgent.first_runnable_job_for_instagram_dm(account)
    if job is None:
        logger.warning(
            "process_instagram_dm no_runnable_job integration_account_id=%s workspace_id=%s",
            account.id,
            account.workspace_id,
        )
        return

    identity = _job_primary_identity(job)
    if identity is None:
        logger.warning(
            "process_instagram_dm no_primary_identity job_id=%s integration_account_id=%s",
            job.id,
            account.id,
        )
        return

    logger.info(
        "process_instagram_dm job_selected job_id=%s identity_id=%s",
        job.id,
        identity.id,
    )

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

    logger.info(
        "process_instagram_dm enqueue_agent job_id=%s conversation_id=%s user_message_id=%s",
        job.id,
        convo.id,
        user_msg.id,
    )
    run_job_assignment_agent.delay(
        str(job.id),
        str(convo.id),
        str(user_msg.id),
    )
