"""Select a ``JobAssignment`` for an inbound event/task and build agent loop tools + prompt."""

from __future__ import annotations

import uuid

from core.agent.base import AgentToolConfig
from core.agent.tools.create_recurring_job import make_create_recurring_job_tool
from core.agent.tools.schedule_one_off_task import make_schedule_one_off_task_tool
from core.agent.tools.send_chat_message import make_send_chat_message_tool
from core.agent.tools.send_telegram_message import make_send_telegram_message_tool
from core.integrations.actionables import (
    SYSTEM_SEND_CHAT_MESSAGE,
    TASKS_CREATE_RECURRING_JOB,
    TASKS_SCHEDULE_ONE_OFF,
    TELEGRAM_SEND_MESSAGE,
)
from core.integrations.event_types import TELEGRAM_PRIVATE_MESSAGE
from core.models import Conversation, CyberIdentity, IntegrationAccount, JobAssignment
from core.schemas.channel import Channel, TelegramPrivateChannel, WebChatChannel
from core.schemas.job_assignment import JobAssignmentEventTrigger
from core.services.telegram_bot import get_bot_token


class JobTaskProcessorAgent:
    """Finds runnable jobs for an event and prepares tools + prompt for :class:`core.agent.base.Agent`."""

    @staticmethod
    def build_tools_for_conversation(
        *,
        job: JobAssignment,
        conversation: Conversation,
    ) -> list[AgentToolConfig]:
        """Build tool list for an agent run bound to a ``Conversation``.

        The conversation already carries the integration account (channel) and the external
        thread id, so tools that reply back to the user (e.g. ``send_telegram_message``) are
        instantiated from it directly.
        """
        channel = _channel_for_conversation(conversation)
        telegram_account: IntegrationAccount | None = None
        telegram_bot_token: str | None = None
        if (
            conversation.integration_account_id
            and conversation.integration_account.provider == IntegrationAccount.Provider.TELEGRAM
        ):
            telegram_account = conversation.integration_account
            telegram_bot_token = get_bot_token(telegram_account) or None

        return JobTaskProcessorAgent._build_tools_from_actions(
            job=job,
            conversation=conversation,
            channel=channel,
            telegram_account=telegram_account,
            telegram_bot_token=telegram_bot_token,
        )

    @staticmethod
    def _build_tools_from_actions(
        *,
        job: JobAssignment,
        conversation: Conversation | None,
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

        for act in cfg_model.actions:
            slug = act.actionable_slug
            if slug == TELEGRAM_SEND_MESSAGE.slug:
                if (
                    conversation is not None
                    and telegram_account is not None
                    and telegram_bot_token
                    and act.integration_account_id == telegram_account.id
                ):
                    _add(make_send_telegram_message_tool(
                        bot_token=telegram_bot_token,
                        conversation=conversation,
                    ))
            elif slug == SYSTEM_SEND_CHAT_MESSAGE.slug:
                if (
                    conversation is not None
                    and conversation.origin == Conversation.Origin.WEB
                    and isinstance(channel, WebChatChannel)
                ):
                    _add(make_send_chat_message_tool(
                        conversation=conversation,
                        user_id=channel.user_id,
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
    ) -> JobAssignment | None:
        """Return the first matching job (checks configuration only; does not instantiate tools)."""
        matches = JobTaskProcessorAgent.find_matching_jobs_for_telegram_private_message(account)
        return matches[0] if matches else None

    @staticmethod
    def model_for_job(job: JobAssignment) -> str | None:
        """Return the first ``identity.config['model']`` found among the job's scoped identities."""
        cfg = job.get_config()
        for ident in cfg.identities:
            model = (ident.config or {}).get("model")
            if isinstance(model, str) and model.strip():
                return model.strip()
        id_list: list[uuid.UUID] = [ident.id for ident in cfg.identities]
        if not id_list:
            return None
        for row in CyberIdentity.objects.filter(id__in=id_list, workspace=job.workspace):
            model = (row.config or {}).get("model")
            if isinstance(model, str) and model.strip():
                return model.strip()
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
            "When you need to reply to the user, call the channel-specific send-message tool "
            "(e.g. **send_telegram_message** for Telegram, **send_chat_message** for the web chat) "
            "with the full text. Do not invent a different channel; the tool is already scoped to the "
            "current conversation."
        )
        return "\n\n".join(parts)


def _channel_for_conversation(conversation: Conversation) -> Channel | None:
    """Derive a :class:`Channel` from a ``Conversation``."""
    if conversation.origin == Conversation.Origin.WEB:
        cfg = conversation.get_config()
        if cfg.web_user_id is None:
            return None
        return WebChatChannel(
            type="web_chat",
            user_id=cfg.web_user_id,
            cyber_identity_id=conversation.cyber_identity_id,
        )

    account = conversation.integration_account
    if account is None or account.provider != IntegrationAccount.Provider.TELEGRAM:
        return None
    cfg = conversation.get_config()
    if not cfg.external_thread_id:
        return None
    return TelegramPrivateChannel(
        type="telegram_private_chat",
        integration_account_id=account.id,
        chat_id=cfg.external_thread_id,
    )
