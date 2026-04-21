"""Select a ``JobAssignment`` for an inbound event/task and build agent loop tools + prompt."""

from __future__ import annotations

import uuid

from core.agent.base import AgentToolConfig
from core.agent.tools.create_recurring_job import make_create_recurring_job_tool
from core.agent.tools.schedule_one_off_task import make_schedule_one_off_task_tool
from core.agent.tools.send_chat_message import make_send_chat_message_tool
from core.agent.tools.send_instagram_message import make_send_instagram_message_tool
from core.agent.tools.send_telegram_message import make_send_telegram_message_tool
from core.integrations.actionables import (
    INSTAGRAM_SEND_MESSAGE,
    SYSTEM_SEND_CHAT_MESSAGE,
    TASKS_CREATE_RECURRING_JOB,
    TASKS_SCHEDULE_ONE_OFF,
    TELEGRAM_SEND_MESSAGE,
)
from core.integrations.event_types import INSTAGRAM_DM_MESSAGE, TELEGRAM_PRIVATE_MESSAGE
from core.models import Conversation, CyberIdentity, IntegrationAccount, JobAssignment
from core.schemas.channel import Channel, InstagramDmChannel, TelegramPrivateChannel, WebChatChannel
from core.schemas.job_assignment import JobAssignmentEventTrigger
from core.services.instagram_service import get_access_token, get_ig_user_id
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
        instagram_account: IntegrationAccount | None = None
        instagram_page_token: str | None = None
        instagram_ig_user_id: str | None = None

        if conversation.integration_account_id:
            provider = conversation.integration_account.provider
            if provider == IntegrationAccount.Provider.TELEGRAM:
                telegram_account = conversation.integration_account
                telegram_bot_token = get_bot_token(telegram_account) or None
            elif provider == IntegrationAccount.Provider.INSTAGRAM:
                instagram_account = conversation.integration_account
                instagram_page_token = get_access_token(instagram_account) or None
                instagram_ig_user_id = get_ig_user_id(instagram_account) or None

        return JobTaskProcessorAgent._build_tools_from_actions(
            job=job,
            conversation=conversation,
            channel=channel,
            telegram_account=telegram_account,
            telegram_bot_token=telegram_bot_token,
            instagram_account=instagram_account,
            instagram_page_token=instagram_page_token,
            instagram_ig_user_id=instagram_ig_user_id,
        )

    @staticmethod
    def _build_tools_from_actions(
        *,
        job: JobAssignment,
        conversation: Conversation | None,
        channel: Channel | None,
        telegram_account: IntegrationAccount | None,
        telegram_bot_token: str | None,
        instagram_account: IntegrationAccount | None = None,
        instagram_page_token: str | None = None,
        instagram_ig_user_id: str | None = None,
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
            elif slug == INSTAGRAM_SEND_MESSAGE.slug:
                if (
                    conversation is not None
                    and instagram_account is not None
                    and instagram_page_token
                    and instagram_ig_user_id
                    and act.integration_account_id == instagram_account.id
                ):
                    _add(make_send_instagram_message_tool(
                        access_token=instagram_page_token,
                        ig_user_id=instagram_ig_user_id,
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
    def find_matching_jobs_for_instagram_dm(
        account: IntegrationAccount,
    ) -> list[JobAssignment]:
        """Enabled jobs in the workspace that listen for Instagram DMs and include this account in actions."""
        event_slug = INSTAGRAM_DM_MESSAGE.slug
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
    def first_runnable_job_for_instagram_dm(
        account: IntegrationAccount,
    ) -> JobAssignment | None:
        matches = JobTaskProcessorAgent.find_matching_jobs_for_instagram_dm(account)
        return matches[0] if matches else None

    @staticmethod
    def primary_identity_for_job(job: JobAssignment) -> CyberIdentity | None:
        cfg = job.get_config()
        if not cfg.identities:
            return None
        first = cfg.identities[0]
        return CyberIdentity.objects.filter(id=first.id, workspace=job.workspace).first()

    @staticmethod
    def integration_channel_for_thread(
        account: IntegrationAccount,
        external_thread_id: str,
    ) -> TelegramPrivateChannel | InstagramDmChannel | None:
        if account.provider == IntegrationAccount.Provider.TELEGRAM:
            return TelegramPrivateChannel(
                type="telegram_private_chat",
                integration_account_id=account.id,
                chat_id=external_thread_id,
            )
        if account.provider == IntegrationAccount.Provider.INSTAGRAM:
            return InstagramDmChannel(
                type="instagram_dm",
                integration_account_id=account.id,
                recipient_igsid=external_thread_id,
            )
        return None

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
    def _user_facing_send_tool_name(conversation: Conversation | None) -> str | None:
        """Name of the send-message tool for this thread (matches ``build_tools_for_conversation``)."""
        if conversation is None:
            return None
        if conversation.origin == Conversation.Origin.WEB:
            return "send_chat_message"
        account = conversation.integration_account
        if account is None:
            return None
        if account.provider == IntegrationAccount.Provider.TELEGRAM:
            return "send_telegram_message"
        if account.provider == IntegrationAccount.Provider.INSTAGRAM:
            return "send_instagram_message"
        return None

    @staticmethod
    def build_system_prompt(job: JobAssignment, *, conversation: Conversation | None = None) -> str:
        cfg_model = job.get_config()
        parts = [
            f"You are running the workspace job **{job.role_name}**.",
        ]
        if (job.description or "").strip():
            parts.append(f"Summary:\n{job.description.strip()}")
        if (job.instructions or "").strip():
            parts.append(f"Instructions:\n{job.instructions.strip()}")

        # Primary speaking role: first identity in job config (jobs are expected to use one).
        primary_id = cfg_model.identities[0].id if cfg_model.identities else None
        primary = (
            CyberIdentity.objects.filter(id=primary_id, workspace=job.workspace).first()
            if primary_id is not None
            else None
        )
        if primary is not None:
            type_label = primary.get_type_display()
            parts.append(
                "**Your persona (stay in character for the user):**\n"
                f"You are **{primary.display_name}** — a **{type_label}** identity in this workspace. "
                "Use this name and voice consistently when you address or represent yourself to the user; "
                "do not fall back to a vague unnamed assistant unless this persona would naturally do so."
            )
            if len(cfg_model.identities) > 1:
                parts.append(
                    "This job lists more than one identity in configuration; your **primary** user-facing "
                    f"role for this run is still **{primary.display_name}**."
                )
        else:
            parts.append(
                "**Persona:** This job has no cyber identity in scope; act as a neutral workspace agent."
            )

        tool_name = JobTaskProcessorAgent._user_facing_send_tool_name(conversation)
        if tool_name:
            parts.append(
                f"In **this** conversation, anything the end user must read or hear must be sent through "
                f"the **`{tool_name}`** tool (already scoped to this thread). Plain assistant text without "
                "that tool is not delivered to the user on this channel unless the instructions above say "
                "otherwise."
            )
        else:
            parts.append(
                "Use the send-message tool attached to this run for user-visible replies; plain assistant "
                "text alone may not reach the user depending on the channel."
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
    if account is None:
        return None

    cfg = conversation.get_config()
    if not cfg.external_thread_id:
        return None

    if account.provider == IntegrationAccount.Provider.TELEGRAM:
        return TelegramPrivateChannel(
            type="telegram_private_chat",
            integration_account_id=account.id,
            chat_id=cfg.external_thread_id,
        )

    if account.provider == IntegrationAccount.Provider.INSTAGRAM:
        return InstagramDmChannel(
            type="instagram_dm",
            integration_account_id=account.id,
            recipient_igsid=cfg.external_thread_id,
        )

    return None
