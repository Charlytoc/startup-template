"""Run a :class:`core.models.TaskExecution` with its parent job's capabilities."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from django.db import transaction

from core.agent.base import Agent, AgentConfig
from core.models import Conversation, CyberIdentity, IntegrationAccount, JobAssignment, TaskExecution
from core.models.agent_session_log import AgentSessionLog
from core.schemas.agentic_chat import ExchangeMessage
from core.schemas.channel import Channel, InstagramDmChannel, TelegramPrivateChannel, WebChatChannel
from core.schemas.task_execution import (
    IdentityConfigSnapshot,
    TaskExecutionError,
    TaskExecutionInputs,
    TaskExecutionOutputs,
)
from core.services.conversations import (
    append_user_message,
    find_active_web_conversation,
    get_or_create_active_conversation,
    prior_exchange_messages,
)
from core.services.job_task_processor_agent import JobTaskProcessorAgent

logger = logging.getLogger(__name__)

MODEL = "gpt-5.4-mini"
PROVIDER = "openai"

WEB_CHAT_EVENT_SLUG = "web_chat.user_message"


def _trigger_is_event(trigger: dict[str, Any] | None) -> bool:
    if not trigger:
        return False
    return trigger.get("type") == "event"


def create_queued_event_task_execution(
    *,
    job: JobAssignment,
    task_instructions: str,
    channel: Channel,
    event_slug: str,
    conversation_id: uuid.UUID,
    triggering_message_id: uuid.UUID,
) -> TaskExecution:
    """Persist a ``TaskExecution`` for an inbound/event-driven run (already ``QUEUED`` for immediate Celery)."""
    cfg = job.get_config()
    identity_snapshot: IdentityConfigSnapshot | None = None
    if cfg.identities:
        first = cfg.identities[0]
        identity_snapshot = IdentityConfigSnapshot(identity=first.id, config=first.config)

    inputs = TaskExecutionInputs(
        task_instructions=task_instructions,
        parent_job_assignment=job.id,
        identity_config=identity_snapshot,
        channel=channel,
        trigger={
            "type": "event",
            "event_slug": event_slug,
            "conversation_id": str(conversation_id),
            "triggering_message_id": str(triggering_message_id),
        },
    )
    task = TaskExecution(
        workspace=job.workspace,
        job_assignment=job,
        status=TaskExecution.Status.QUEUED,
        requires_approval=False,
        scheduled_to=None,
    )
    task.set_inputs(inputs)
    task.save()
    return task


def enqueue_task_execution(task_id: uuid.UUID) -> None:
    from core.tasks.task_execution import run_task_execution

    run_task_execution.delay(str(task_id))


def run_task_execution(task_execution_id: str, celery_task_id: str | None = None) -> dict:
    """Run the agent loop for a single ``TaskExecution``.

    Returns a small status dict so the Celery task can report it.
    """
    try:
        task_id = uuid.UUID(task_execution_id)
    except ValueError:
        return {"status": "error", "error": "invalid_task_execution_id"}

    task = (
        TaskExecution.objects.select_related("job_assignment", "workspace")
        .filter(id=task_id)
        .first()
    )
    if task is None:
        return {"status": "error", "error": "task_not_found"}

    job: JobAssignment | None = task.job_assignment
    if job is None:
        return _fail(task, "task_has_no_parent_job_assignment")

    try:
        inputs = task.get_inputs()
    except Exception as exc:
        logger.exception("run_task_execution: invalid inputs on task=%s", task.id)
        return _fail(task, f"invalid_inputs: {exc}")

    conversation = _resolve_conversation_for_task(job, inputs.channel)
    if conversation is None:
        return _fail(task, "cannot_resolve_conversation_for_task")

    trigger_dict = inputs.trigger if isinstance(inputs.trigger, dict) else None
    is_event = _trigger_is_event(trigger_dict)

    if is_event:
        loop_messages = prior_exchange_messages(conversation)
        if not loop_messages:
            return _fail(task, "empty_conversation")
        system_prompt = JobTaskProcessorAgent.build_system_prompt(job, conversation=conversation)
    else:
        append_user_message(
            conversation,
            content_text=inputs.task_instructions,
            content_structured={"trigger": "task_execution", "task_execution_id": str(task.id)},
        )
        system_prompt = (
            JobTaskProcessorAgent.build_system_prompt(job, conversation=conversation)
            + "\n\nYou are executing a deferred task created earlier. Use the tools "
            "to complete the instructions below. When you are done, output a brief confirmation."
        )
        loop_messages = [ExchangeMessage(role="user", content=inputs.task_instructions)]

    tools = JobTaskProcessorAgent.build_tools_for_conversation(job=job, conversation=conversation)
    if not tools:
        return _fail(task, "no_tools_available_for_task")

    model = JobTaskProcessorAgent.model_for_job(job) or MODEL
    log = AgentSessionLog.objects.create(
        user=None,
        celery_task_id=celery_task_id,
        model=model,
        provider=PROVIDER,
        instructions=system_prompt,
        tools=[t.tool.model_dump() for t in tools],
        inputs=[m.model_dump() for m in loop_messages],
        status=AgentSessionLog.Status.PENDING,
    )

    task.status = TaskExecution.Status.RUNNING
    task.started_at = datetime.now(timezone.utc)
    task.save(update_fields=["status", "started_at", "modified"])

    started = time.monotonic()
    try:
        agent = Agent(
            config=AgentConfig(
                name=job.role_name[:80] or "Task agent",
                system_prompt=system_prompt,
                model=model,
            )
        )
        summary = agent.start_agent_loop(messages=loop_messages, tools=tools)
        duration = time.monotonic() - started

        log.status = (
            AgentSessionLog.Status.ERROR if summary.error else AgentSessionLog.Status.COMPLETED
        )
        log.iterations = summary.iterations
        log.tool_calls_count = summary.tool_calls_count
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.outputs = {
            "final_response": summary.final_response or "",
            "messages": [m.model_dump() for m in summary.messages],
            "task_execution_id": str(task.id),
            "job_assignment_id": str(job.id),
            "conversation_id": str(conversation.id),
        }
        if trigger_dict and is_event:
            tid = trigger_dict.get("triggering_message_id")
            if tid:
                log.outputs["triggering_message_id"] = str(tid)
        if summary.error:
            log.error_message = summary.error
        log.save()

        outputs = TaskExecutionOutputs(
            total_duration_ms=int(duration * 1000),
            agent_session_log=log.id,
            error=TaskExecutionError(message=summary.error) if summary.error else None,
        )
        task.set_outputs(outputs)
        task.status = (
            TaskExecution.Status.FAILED if summary.error else TaskExecution.Status.COMPLETED
        )
        task.completed_at = datetime.now(timezone.utc)
        task.save(update_fields=["status", "outputs", "completed_at", "modified"])

        return {
            "status": "completed" if not summary.error else "error",
            "task_execution_id": str(task.id),
            "agent_session_log_id": str(log.id),
        }
    except Exception as exc:
        duration = time.monotonic() - started
        log.status = AgentSessionLog.Status.ERROR
        log.error_message = str(exc)
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.save()
        logger.exception("run_task_execution failed task=%s", task.id)
        outputs = TaskExecutionOutputs(
            total_duration_ms=int(duration * 1000),
            agent_session_log=log.id,
            error=TaskExecutionError(message=str(exc), type=type(exc).__name__),
        )
        task.set_outputs(outputs)
        task.status = TaskExecution.Status.FAILED
        task.completed_at = datetime.now(timezone.utc)
        task.save(update_fields=["status", "outputs", "completed_at", "modified"])
        return {"status": "error", "error": str(exc)}


def _resolve_conversation_for_task(
    job: JobAssignment, channel: Channel | None
) -> Conversation | None:
    """Find or create the ``Conversation`` the task should speak on, based on its channel."""
    if channel is None:
        return None

    identity = JobTaskProcessorAgent.primary_identity_for_job(job)
    if identity is None:
        return None

    if isinstance(channel, TelegramPrivateChannel):
        account = IntegrationAccount.objects.filter(
            id=channel.integration_account_id, workspace=job.workspace
        ).first()
        if account is None:
            return None
        return get_or_create_active_conversation(
            account=account,
            cyber_identity=identity,
            external_thread_id=channel.chat_id,
            external_user_id=channel.chat_id,
        )

    if isinstance(channel, InstagramDmChannel):
        account = IntegrationAccount.objects.filter(
            id=channel.integration_account_id, workspace=job.workspace
        ).first()
        if account is None:
            return None
        return get_or_create_active_conversation(
            account=account,
            cyber_identity=identity,
            external_thread_id=channel.recipient_igsid,
            external_user_id=channel.recipient_igsid,
        )

    if isinstance(channel, WebChatChannel):
        cyber = CyberIdentity.objects.filter(
            id=channel.cyber_identity_id, workspace=job.workspace
        ).first()
        if cyber is None:
            return None
        return find_active_web_conversation(
            workspace=job.workspace,
            cyber_identity=cyber,
            web_user_id=channel.user_id,
        )

    return None


def _fail(task: TaskExecution, reason: str) -> dict:
    with transaction.atomic():
        task.status = TaskExecution.Status.FAILED
        task.completed_at = datetime.now(timezone.utc)
        outputs = TaskExecutionOutputs(error=TaskExecutionError(message=reason))
        task.set_outputs(outputs)
        task.save(update_fields=["status", "outputs", "completed_at", "modified"])
    logger.warning("run_task_execution failed task=%s reason=%s", task.id, reason)
    return {"status": "error", "error": reason}
