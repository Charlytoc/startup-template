"""Run a :class:`core.models.TaskExecution` with its parent job's capabilities."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from django.db import transaction

from core.agent.base import Agent, AgentConfig
from core.models import Artifact, Conversation, CyberIdentity, IntegrationAccount, JobAssignment, TaskExecution
from core.models.agent_session_log import AgentSessionLog
from core.schemas.agentic_chat import ExchangeMessage
from core.schemas.channel import Channel, InstagramDmChannel, TelegramPrivateChannel, WebChatChannel
from core.schemas.task_execution import (
    ArtifactRef,
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


def _trigger_type(trigger: dict[str, Any] | None) -> str:
    if not trigger:
        return ""
    return str(trigger.get("type") or "")


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
    trigger_type = _trigger_type(trigger_dict)
    is_event = _trigger_is_event(trigger_dict)
    actions_override = inputs.actions if inputs.actions else None

    if trigger_type == "artifact_creator_completed":
        loop_messages = prior_exchange_messages(conversation)
        task_msg = ExchangeMessage(role="user", content=inputs.task_instructions)
        loop_messages = [*loop_messages, task_msg] if loop_messages else [task_msg]
        system_prompt = (
            JobTaskProcessorAgent.build_system_prompt(
                job,
                conversation=conversation,
                actions_override=actions_override,
            )
            + "\n\nAn artifact creator task has finished in the background. Review the structured "
            "artifact data below and notify the user naturally through the appropriate send tool. "
            "Do not create new artifacts unless the user explicitly asks for changes."
        )
    elif trigger_type == "artifact_creator":
        loop_messages = prior_exchange_messages(conversation)
        task_msg = ExchangeMessage(role="user", content=inputs.task_instructions)
        loop_messages = [*loop_messages, task_msg] if loop_messages else [task_msg]
        system_prompt = (
            JobTaskProcessorAgent.build_system_prompt(
                job,
                conversation=conversation,
                actions_override=actions_override,
            )
            + "\n\nThis run is an artifact creator task. Create durable artifacts that satisfy "
            "the latest instructions. Prefer saving the useful output through the artifact tools; "
            "do not treat plain final text as the saved artifact."
        )
    elif is_event:
        loop_messages = prior_exchange_messages(conversation)
        if not loop_messages:
            return _fail(task, "empty_conversation")
        system_prompt = JobTaskProcessorAgent.build_system_prompt(
            job,
            conversation=conversation,
            actions_override=actions_override,
        )
    else:
        append_user_message(
            conversation,
            content_text=inputs.task_instructions,
            content_structured={"trigger": "task_execution", "task_execution_id": str(task.id)},
        )
        system_prompt = (
            JobTaskProcessorAgent.build_system_prompt(
                job,
                conversation=conversation,
                actions_override=actions_override,
            )
            + "\n\nYou are executing a deferred task created earlier. Use the tools "
            "to complete the instructions below. When you are done, output a brief confirmation."
        )
        loop_messages = [ExchangeMessage(role="user", content=inputs.task_instructions)]

    tools = JobTaskProcessorAgent.build_tools_for_conversation(
        job=job,
        conversation=conversation,
        task_execution=task,
        actions_override=actions_override,
    )
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

        artifact_refs = [
            ArtifactRef(id=a.id, kind=a.kind, label=a.label)
            for a in task.artifacts.all().order_by("created")
        ]
        outputs = TaskExecutionOutputs(
            artifacts=artifact_refs,
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

        if trigger_type == "artifact_creator":
            _enqueue_artifact_creator_callback(
                task=task,
                inputs=inputs,
                status="failed" if summary.error else "completed",
                error_message=summary.error,
            )

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
        if trigger_type == "artifact_creator":
            _enqueue_artifact_creator_callback(
                task=task,
                inputs=inputs,
                status="failed",
                error_message=str(exc),
            )
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


def _enqueue_artifact_creator_callback(
    *,
    task: TaskExecution,
    inputs: TaskExecutionInputs,
    status: str,
    error_message: str | None = None,
) -> TaskExecution | None:
    """Queue a parent/orchestrator run to notify the user after artifact creation finishes."""
    if inputs.channel is None or inputs.parent_job_assignment is None:
        logger.info(
            "artifact_creator_callback skip missing_channel_or_parent task=%s",
            task.id,
        )
        return None

    parent_job = JobAssignment.objects.filter(
        id=inputs.parent_job_assignment,
        workspace=task.workspace,
    ).first()
    if parent_job is None:
        logger.warning(
            "artifact_creator_callback skip parent_not_found task=%s parent=%s",
            task.id,
            inputs.parent_job_assignment,
        )
        return None

    artifacts = _artifact_callback_payload(task)
    task_instructions = _artifact_callback_instructions(
        task=task,
        status=status,
        artifacts=artifacts,
        error_message=error_message,
    )

    parent_cfg = parent_job.get_config()
    identity_snapshot: IdentityConfigSnapshot | None = None
    if parent_cfg.identities:
        first = parent_cfg.identities[0]
        identity_snapshot = IdentityConfigSnapshot(identity=first.id, config=first.config)

    callback_inputs = TaskExecutionInputs(
        task_instructions=task_instructions,
        parent_job_assignment=parent_job.id,
        identity_config=identity_snapshot,
        channel=inputs.channel,
        trigger={
            "type": "artifact_creator_completed",
            "artifact_task_execution_id": str(task.id),
            "status": status,
            "artifact_ids": [a["id"] for a in artifacts],
        },
        variables={
            "artifact_creator": {
                "task_execution_id": str(task.id),
                "name": task.name or "",
                "status": status,
                "error_message": error_message or "",
            },
            "artifacts": artifacts,
        },
    )

    with transaction.atomic():
        locked = TaskExecution.objects.select_for_update().get(id=task.id)
        locked_outputs = dict(locked.outputs or {})
        final_output = dict(locked_outputs.get("final_output") or {})
        existing_id = final_output.get("parent_callback_task_execution_id")
        if existing_id:
            logger.info(
                "artifact_creator_callback already_queued task=%s callback=%s",
                task.id,
                existing_id,
            )
            return TaskExecution.objects.filter(id=existing_id).first()

        callback = TaskExecution(
            workspace=task.workspace,
            job_assignment=parent_job,
            name=f"Artifact result - {task.name or str(task.id)}"[:200],
            status=TaskExecution.Status.QUEUED,
            requires_approval=False,
            scheduled_to=None,
        )
        callback.set_inputs(callback_inputs)
        callback.save()

        final_output["parent_callback_task_execution_id"] = str(callback.id)
        locked_outputs["final_output"] = final_output
        locked.outputs = locked_outputs
        locked.save(update_fields=["outputs", "modified"])

        transaction.on_commit(lambda: enqueue_task_execution(callback.id))

    logger.info(
        "artifact_creator_callback queued task=%s callback=%s status=%s artifacts=%s",
        task.id,
        callback.id,
        status,
        len(artifacts),
    )
    return callback


def _artifact_callback_payload(task: TaskExecution) -> list[dict[str, Any]]:
    rows = (
        Artifact.objects.filter(task_execution=task)
        .select_related("media", "identity", "integration_account")
        .order_by("created")
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        media = row.media
        metadata = row.metadata or {}
        item: dict[str, Any] = {
            "id": str(row.id),
            "kind": row.kind,
            "label": row.label or "",
            "created": row.created.isoformat() if row.created else "",
            "metadata": {
                "extension": metadata.get("extension"),
                "mime_type": metadata.get("mime_type"),
                "prompt": metadata.get("prompt"),
            },
            "media": None,
        }
        if row.kind == Artifact.Kind.TEXT:
            text = str(metadata.get("text") or "")
            item["text_preview"] = text[:500]
        if media is not None:
            item["media"] = {
                "id": str(media.id),
                "display_name": media.display_name,
                "mime_type": media.mime_type or "",
                "byte_size": media.byte_size,
                "public_url": media.resolve_public_url(),
            }
        out.append(item)
    return out


def _artifact_callback_instructions(
    *,
    task: TaskExecution,
    status: str,
    artifacts: list[dict[str, Any]],
    error_message: str | None,
) -> str:
    if status == "completed":
        lines = [
            "The background artifact creator finished successfully.",
            f"Artifact task: {task.name or task.id}",
            f"Created artifacts: {len(artifacts)}.",
        ]
        for artifact in artifacts:
            label = artifact.get("label") or "(untitled)"
            kind = artifact.get("kind") or "artifact"
            url = ((artifact.get("media") or {}).get("public_url") or "").strip()
            preview = str(artifact.get("text_preview") or "").strip()
            detail = f"- {kind}: {label} (id: {artifact.get('id')})"
            if url:
                detail += f" URL: {url}"
            elif preview:
                detail += f" Preview: {preview}"
            lines.append(detail)
        lines.append(
            "Send one concise message in the same language and tone as the conversation. "
            "Say the artifact is ready and pass every created artifact id in the `artifact_ids` "
            "argument of `send_message`. Do not write artifact:// links in the message text."
        )
        return "\n".join(lines)

    return "\n".join(
        [
            "The background artifact creator failed.",
            f"Artifact task: {task.name or task.id}",
            f"Error: {error_message or 'unknown error'}",
            "Apologize briefly to the user and explain that the artifact could not be created.",
        ]
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
