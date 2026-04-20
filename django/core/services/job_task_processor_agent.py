"""Select a ``JobAssignment`` for an inbound integration event and build agent loop inputs."""

from __future__ import annotations

import json
import uuid
from typing import Any

from core.agent.base import AgentToolConfig
from core.agent.tools.create_recurring_job import make_create_recurring_job_tool
from core.agent.tools.schedule_one_off_task import make_schedule_one_off_task_tool
from core.agent.tools.send_telegram_message import make_send_telegram_message_tool
from core.integrations.actionables import (
    TASKS_CREATE_RECURRING_JOB,
    TASKS_SCHEDULE_ONE_OFF,
    TELEGRAM_SEND_MESSAGE,
)
from core.integrations.event_types import TELEGRAM_PRIVATE_MESSAGE
from core.models import CyberIdentity, IntegrationAccount, JobAssignment
from core.schemas.channel import Channel, TelegramPrivateChannel
from core.schemas.job_assignment import JobAssignmentEventTrigger
from core.services.telegram_bot import get_bot_token


class JobTaskProcessorAgent:
    """Finds runnable jobs for an event and prepares tools + prompt for :class:`core.agent.base.Agent`."""

    @staticmethod
    def build_tools_for_telegram_private_message(
        *,
        job: JobAssignment,
        account: IntegrationAccount,
        message: dict[str, Any],
    ) -> list[AgentToolConfig]:
        """Build tool list from job actions that target this integration account (Telegram for now)."""
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        bot_token = get_bot_token(account)
        if chat_id is None or not bot_token:
            return []

        cfg_model = job.get_config()
        channel = TelegramPrivateChannel(
            type="telegram_private_chat",
            integration_account_id=account.id,
            chat_id=str(chat_id),
        )
        return JobTaskProcessorAgent._build_tools_from_actions(
            job=job,
            channel=channel,
            telegram_account=account,
            telegram_bot_token=bot_token,
        )

    @staticmethod
    def build_tools_for_task_execution(
        *,
        job: JobAssignment,
        channel: Channel | None,
    ) -> list[AgentToolConfig]:
        """Build tools for a scheduled ``TaskExecution`` running under ``job`` with optional channel."""
        telegram_account: IntegrationAccount | None = None
        telegram_bot_token: str | None = None
        if isinstance(channel, TelegramPrivateChannel):
            telegram_account = IntegrationAccount.objects.filter(
                id=channel.integration_account_id, workspace=job.workspace
            ).first()
            if telegram_account is not None:
                telegram_bot_token = get_bot_token(telegram_account) or None

        return JobTaskProcessorAgent._build_tools_from_actions(
            job=job,
            channel=channel,
            telegram_account=telegram_account,
            telegram_bot_token=telegram_bot_token,
        )

    @staticmethod
    def _build_tools_from_actions(
        *,
        job: JobAssignment,
        channel: Channel | None,
        telegram_account: IntegrationAccount | None,
        telegram_bot_token: str | None,
    ) -> list[AgentToolConfig]:
        cfg_model = job.get_config()
        tools: list[AgentToolConfig] = []
        seen_names: set[str] = set()

        def _add(cfg: AgentToolConfig) -> None:
            if cfg.tool.name in seen_names:
                return
            seen_names.add(cfg.tool.name)
            tools.append(cfg)

        telegram_chat_id_value = None
        if isinstance(channel, TelegramPrivateChannel):
            telegram_chat_id_value = channel.chat_id

        for act in cfg_model.actions:
            slug = act.actionable_slug
            if slug == TELEGRAM_SEND_MESSAGE.slug:
                if (
                    telegram_account is not None
                    and telegram_bot_token
                    and telegram_chat_id_value is not None
                    and act.integration_account_id == telegram_account.id
                ):
                    _add(make_send_telegram_message_tool(
                        bot_token=telegram_bot_token,
                        chat_id=telegram_chat_id_value,
                        integration_account=telegram_account,
                    ))
            elif slug == TASKS_SCHEDULE_ONE_OFF.slug:
                _add(make_schedule_one_off_task_tool(job=job, channel=channel))
            elif slug == TASKS_CREATE_RECURRING_JOB.slug:
                _add(make_create_recurring_job_tool(job=job, channel=channel))
        return tools

    @staticmethod
    def find_matching_jobs_for_telegram_private_message(
        account: IntegrationAccount,
    ) -> list[JobAssignment]:
        """Enabled jobs in the workspace that listen for private Telegram messages and include this bot in actions."""
        event_slug = TELEGRAM_PRIVATE_MESSAGE.slug
        out: list[JobAssignment] = []
        qs = JobAssignment.objects.filter(workspace=account.workspace, enabled=True).order_by("role_name")
        for job in qs:
            cfg_model = job.get_config()
            if not cfg_model.identities:
                continue
            listens = any(
                isinstance(tr, JobAssignmentEventTrigger) and tr.on == event_slug
                for tr in cfg_model.triggers
            )
            if not listens:
                continue
            if not any(a.integration_account_id == account.id for a in cfg_model.actions):
                continue
            out.append(job)
        return out

    @staticmethod
    def first_runnable_job_for_telegram_private_message(
        account: IntegrationAccount,
        message: dict[str, Any],
    ) -> JobAssignment | None:
        """Return the first matching job that exposes at least one tool for this message."""
        for job in JobTaskProcessorAgent.find_matching_jobs_for_telegram_private_message(account):
            tools = JobTaskProcessorAgent.build_tools_for_telegram_private_message(
                job=job, account=account, message=message
            )
            if tools:
                return job
        return None

    @staticmethod
    def build_system_prompt(job: JobAssignment) -> str:
        cfg_model = job.get_config()
        id_list: list[uuid.UUID] = [ident.id for ident in cfg_model.identities]
        identities = CyberIdentity.objects.filter(id__in=id_list, workspace=job.workspace).order_by("display_name")
        lines = [f"- {cy.display_name} ({cy.type})" for cy in identities]
        identity_block = "\n".join(lines) if lines else "(none)"

        parts = [
            f"You are running the workspace job **{job.role_name}**.",
        ]
        if (job.description or "").strip():
            parts.append(f"Summary:\n{job.description.strip()}")
        if (job.instructions or "").strip():
            parts.append(f"Instructions:\n{job.instructions.strip()}")
        parts.append(f"Cyber identities in scope:\n{identity_block}")
        parts.append(
            "When you need to reply to the user, call **send_telegram_message** with the full text. "
            "Do not invent a different channel; the tool is already scoped to this private chat."
        )
        return "\n\n".join(parts)

    @staticmethod
    def user_turn_content(message: dict[str, Any]) -> str:
        """Serialize the inbound Telegram message for the model."""
        text = message.get("text") or message.get("caption") or ""
        text = (text or "").strip() or "(No text content.)"
        from_user = message.get("from") or {}
        uid = from_user.get("id")
        return json.dumps(
            {
                "telegram_user_id": uid,
                "text": text,
                "message": message,
            },
            ensure_ascii=False,
            default=str,
        )
