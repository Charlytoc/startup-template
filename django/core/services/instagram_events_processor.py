"""Route inbound Instagram DMs: resolve Conversation, persist user Message, enqueue agent."""

from __future__ import annotations

import logging
from typing import Any

from core.integrations.event_types import INSTAGRAM_DM_MESSAGE
from core.models import IntegrationAccount
from core.schemas.integration_account import SenderApprovalStatus
from core.services.chat_clear_commands import CLEAR_CONTEXT_REPLY, is_clear_context_text
from core.services.integration_senders import upsert_sender
from core.services.conversations import (
    append_user_message,
    archive_conversation,
    find_active_conversation,
    get_or_create_active_conversation,
)
from core.services.instagram_service import get_access_token, get_ig_user_id, instagram_send_message
from core.services.job_task_processor_agent import JobTaskProcessorAgent
from core.services.task_execution_runner import (
    create_queued_event_task_execution,
    enqueue_task_execution,
)

logger = logging.getLogger(__name__)


def _instagram_sender_handle_from_messaging(messaging: dict[str, Any]) -> str | None:
    """Return ``@username`` when Meta includes it on ``sender`` (often absent; then ``None``)."""
    sender = messaging.get("sender")
    if not isinstance(sender, dict):
        return None
    username = sender.get("username")
    if not isinstance(username, str):
        return None
    u = username.strip().lstrip("@")
    return f"@{u}" if u else None


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

    upsert_sender(
        account,
        sender_igsid,
        default_status=SenderApprovalStatus.NOT_REQUIRED,
        handle=_instagram_sender_handle_from_messaging(messaging),
    )

    if is_clear_context_text(text):
        convo = find_active_conversation(account=account, external_thread_id=sender_igsid)
        if convo is not None:
            archive_conversation(convo)
        token = get_access_token(account)
        ig_user_id = get_ig_user_id(account)
        if token and ig_user_id:
            try:
                instagram_send_message(token, ig_user_id, sender_igsid, CLEAR_CONTEXT_REPLY)
            except Exception:
                logger.exception(
                    "process_instagram_dm clear_context send_failed account_id=%s sender=%s",
                    account.id,
                    sender_igsid,
                )
        else:
            logger.warning(
                "process_instagram_dm clear_context skip_send missing_token account_id=%s",
                account.id,
            )
        return

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
