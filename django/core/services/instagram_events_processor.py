"""Route inbound Instagram DMs: resolve Conversation, persist user Message, enqueue agent."""

from __future__ import annotations

import logging
from typing import Any

from core.integrations.event_types import INSTAGRAM_DM_MESSAGE
from core.models import IntegrationAccount
from core.services.conversations import (
    append_user_message,
    get_or_create_active_conversation,
)
from core.services.job_task_processor_agent import JobTaskProcessorAgent
from core.services.task_execution_runner import (
    create_queued_event_task_execution,
    enqueue_task_execution,
)

logger = logging.getLogger(__name__)


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

    identity = JobTaskProcessorAgent.primary_identity_for_job(job)
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
    channel = JobTaskProcessorAgent.integration_channel_for_thread(account, sender_igsid)
    if channel is None:
        return
    instructions = text if text else "Instagram inbound message (no text)."
    task_ex = create_queued_event_task_execution(
        job=job,
        task_instructions=instructions,
        channel=channel,
        event_slug=INSTAGRAM_DM_MESSAGE.slug,
        conversation_id=convo.id,
        triggering_message_id=user_msg.id,
    )
    enqueue_task_execution(task_ex.id)
