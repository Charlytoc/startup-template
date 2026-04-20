"""Run a :class:`core.models.TaskExecution` with its parent job's capabilities."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from django.db import transaction

from core.agent.base import Agent, AgentConfig
from core.models import Conversation, CyberIdentity, IntegrationAccount, JobAssignment, TaskExecution
from core.models.agent_session_log import AgentSessionLog
from core.schemas.agentic_chat import ExchangeMessage
from core.schemas.channel import Channel, TelegramPrivateChannel
from core.schemas.task_execution import (
    TaskExecutionError,
    TaskExecutionOutputs,
)
from core.services.conversations import append_user_message, get_or_create_active_conversation
from core.services.job_task_processor_agent import JobTaskProcessorAgent

logger = logging.getLogger(__name__)

MODEL = "gpt-5.4-mini"
PROVIDER = "openai"


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

    append_user_message(
        conversation,
        content_text=inputs.task_instructions,
        content_structured={"trigger": "task_execution", "task_execution_id": str(task.id)},
    )

    tools = JobTaskProcessorAgent.build_tools_for_conversation(job=job, conversation=conversation)
    if not tools:
        return _fail(task, "no_tools_available_for_task")

    system_prompt = (
        JobTaskProcessorAgent.build_system_prompt(job)
        + "\n\nYou are executing a deferred task created earlier. Use the tools "
        "to complete the instructions below. When you are done, output a brief confirmation."
    )
    user_content = inputs.task_instructions
    loop_messages = [ExchangeMessage(role="user", content=user_content)]

    log = AgentSessionLog.objects.create(
        user=None,
        celery_task_id=celery_task_id,
        model=MODEL,
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
                model=MODEL,
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
        }
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
    if not isinstance(channel, TelegramPrivateChannel):
        return None
    account = IntegrationAccount.objects.filter(
        id=channel.integration_account_id, workspace=job.workspace
    ).first()
    if account is None:
        return None

    cfg = job.get_config()
    if not cfg.identities:
        return None
    identity = CyberIdentity.objects.filter(
        id=cfg.identities[0].id, workspace=job.workspace
    ).first()
    if identity is None:
        return None

    return get_or_create_active_conversation(
        account=account,
        cyber_identity=identity,
        external_thread_id=channel.chat_id,
        external_user_id=channel.chat_id,
    )


def _fail(task: TaskExecution, reason: str) -> dict:
    with transaction.atomic():
        task.status = TaskExecution.Status.FAILED
        task.completed_at = datetime.now(timezone.utc)
        outputs = TaskExecutionOutputs(error=TaskExecutionError(message=reason))
        task.set_outputs(outputs)
        task.save(update_fields=["status", "outputs", "completed_at", "modified"])
    logger.warning("run_task_execution failed task=%s reason=%s", task.id, reason)
    return {"status": "error", "error": reason}
