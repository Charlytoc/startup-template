"""Async agent run for a ``JobAssignment`` bound to a ``Conversation`` and a triggering ``Message``."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from celery import shared_task
from celery.utils.log import get_task_logger

from core.agent.base import Agent, AgentConfig
from core.models import Conversation, JobAssignment
from core.models.agent_session_log import AgentSessionLog
from core.schemas.agentic_chat import ExchangeMessage
from core.services.conversations import prior_exchange_messages
from core.services.job_task_processor_agent import JobTaskProcessorAgent

logger = get_task_logger(__name__)

MODEL = "gpt-5.4-mini"
PROVIDER = "openai"


@shared_task(bind=True)
def run_job_assignment_agent(
    self,
    job_assignment_id: str,
    conversation_id: str,
    triggering_message_id: str | None = None,
):
    """Run the agent loop for one job + one conversation (triggered by the given user message)."""
    try:
        job = JobAssignment.objects.select_related("workspace").get(
            id=uuid.UUID(job_assignment_id)
        )
    except (JobAssignment.DoesNotExist, ValueError) as exc:
        logger.warning("run_job_assignment_agent: job not found %s: %s", job_assignment_id, exc)
        return {"status": "error", "error": "job_not_found"}

    try:
        convo = (
            Conversation.objects.select_related("workspace", "integration_account", "cyber_identity")
            .get(id=uuid.UUID(conversation_id))
        )
    except (Conversation.DoesNotExist, ValueError) as exc:
        logger.warning(
            "run_job_assignment_agent: conversation not found %s: %s", conversation_id, exc
        )
        return {"status": "error", "error": "conversation_not_found"}

    if convo.workspace_id != job.workspace_id:
        return {"status": "error", "error": "conversation_workspace_mismatch"}

    tools = JobTaskProcessorAgent.build_tools_for_conversation(job=job, conversation=convo)
    if not tools:
        logger.info("run_job_assignment_agent: no tools for job=%s conversation=%s", job.id, convo.id)
        return {"status": "skipped", "reason": "no_tools"}

    system_prompt = JobTaskProcessorAgent.build_system_prompt(job)

    # The conversation already has the triggering user message persisted; pull all messages
    # as the loop history (oldest first).
    loop_messages: list[ExchangeMessage] = prior_exchange_messages(convo)
    if not loop_messages:
        return {"status": "skipped", "reason": "empty_conversation"}

    log = AgentSessionLog.objects.create(
        user=None,
        celery_task_id=self.request.id,
        model=MODEL,
        provider=PROVIDER,
        instructions=system_prompt,
        tools=[t.tool.model_dump() for t in tools],
        inputs=[m.model_dump() for m in loop_messages],
        status=AgentSessionLog.Status.PENDING,
    )

    started = time.monotonic()
    try:
        agent = Agent(
            config=AgentConfig(
                name=job.role_name[:80] or "Job agent",
                system_prompt=system_prompt,
                model=MODEL,
            )
        )
        summary = agent.start_agent_loop(messages=loop_messages, tools=tools)
        duration = time.monotonic() - started
        assistant_message = summary.final_response or ""

        log.status = AgentSessionLog.Status.ERROR if summary.error else AgentSessionLog.Status.COMPLETED
        log.iterations = summary.iterations
        log.tool_calls_count = summary.tool_calls_count
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.outputs = {
            "final_response": assistant_message,
            "messages": [m.model_dump() for m in summary.messages],
            "job_assignment_id": str(job.id),
            "conversation_id": str(convo.id),
            "triggering_message_id": str(triggering_message_id) if triggering_message_id else None,
        }
        if summary.error:
            log.error_message = summary.error
        log.save()

        return {
            "status": "completed" if not summary.error else "error",
            "job_assignment_id": str(job.id),
            "conversation_id": str(convo.id),
            "agent_session_log_id": str(log.id),
        }
    except Exception as exc:
        duration = time.monotonic() - started
        log.status = AgentSessionLog.Status.ERROR
        log.error_message = str(exc)
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.save()
        logger.exception("run_job_assignment_agent failed job=%s conversation=%s", job.id, convo.id)
        return {"status": "error", "error": str(exc)}
