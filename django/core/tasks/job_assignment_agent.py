"""Async agent run for a ``JobAssignment`` triggered by an integration event (e.g. Telegram private message)."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from celery import shared_task
from celery.utils.log import get_task_logger

from core.agent.base import Agent, AgentConfig
from core.models import IntegrationAccount, JobAssignment
from core.models.agent_session_log import AgentSessionLog
from core.schemas.agentic_chat import ExchangeMessage
from core.services.job_task_processor_agent import JobTaskProcessorAgent
from core.services.telegram_private_message_history import (
    prior_private_chat_exchange_messages,
    telegram_chat_id,
)

logger = get_task_logger(__name__)

MODEL = "gpt-5.4-mini"
PROVIDER = "openai"


@shared_task(bind=True)
def run_job_assignment_agent(
    self,
    job_assignment_id: str,
    integration_account_id: str,
    message_json: str,
):
    """Run the agent loop for one job + one inbound Telegram-shaped message."""
    try:
        job = JobAssignment.objects.select_related("workspace").get(id=uuid.UUID(job_assignment_id))
    except (JobAssignment.DoesNotExist, ValueError) as exc:
        logger.warning("run_job_assignment_agent: job not found %s: %s", job_assignment_id, exc)
        return {"status": "error", "error": "job_not_found"}

    try:
        account = IntegrationAccount.objects.get(
            id=uuid.UUID(integration_account_id),
            workspace=job.workspace,
        )
    except (IntegrationAccount.DoesNotExist, ValueError) as exc:
        logger.warning("run_job_assignment_agent: account not found %s: %s", integration_account_id, exc)
        return {"status": "error", "error": "integration_not_found"}

    try:
        message = json.loads(message_json)
    except json.JSONDecodeError:
        return {"status": "error", "error": "invalid_message_json"}

    if not isinstance(message, dict):
        return {"status": "error", "error": "invalid_message"}

    tools = JobTaskProcessorAgent.build_tools_for_telegram_private_message(
        job=job, account=account, message=message
    )
    if not tools:
        logger.info("run_job_assignment_agent: no tools for job %s", job.id)
        return {"status": "skipped", "reason": "no_tools"}

    system_prompt = JobTaskProcessorAgent.build_system_prompt(job)
    user_content = JobTaskProcessorAgent.user_turn_content(message)
    chat_id = telegram_chat_id(message)
    current_message_id = message.get("message_id")
    try:
        current_message_id_int = int(current_message_id) if current_message_id is not None else None
    except (TypeError, ValueError):
        current_message_id_int = None

    prior: list[ExchangeMessage] = []
    if chat_id is not None:
        prior = prior_private_chat_exchange_messages(
            account,
            chat_id,
            exclude_message_id=current_message_id_int,
        )
    loop_messages = [*prior, ExchangeMessage(role="user", content=user_content)]

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
        summary = agent.start_agent_loop(
            messages=loop_messages,
            tools=tools,
        )
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
            "integration_account_id": str(account.id),
        }
        if summary.error:
            log.error_message = summary.error
        log.save()

        return {
            "status": "completed" if not summary.error else "error",
            "job_assignment_id": str(job.id),
            "agent_session_log_id": str(log.id),
        }
    except Exception as exc:
        duration = time.monotonic() - started
        log.status = AgentSessionLog.Status.ERROR
        log.error_message = str(exc)
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.save()
        logger.exception("run_job_assignment_agent failed job=%s", job.id)
        return {"status": "error", "error": str(exc)}
