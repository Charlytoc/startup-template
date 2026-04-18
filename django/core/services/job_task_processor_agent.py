"""Select a ``JobAssignment`` for an inbound integration event and build agent loop inputs."""

from __future__ import annotations

import json
import uuid
from typing import Any

from core.agent.base import AgentToolConfig
from core.agent.tools.send_telegram_message import make_send_telegram_message_tool
from core.integrations.actionables import TELEGRAM_SEND_MESSAGE
from core.integrations.event_types import TELEGRAM_PRIVATE_MESSAGE
from core.models import CyberIdentity, IntegrationAccount, JobAssignment
from core.services.telegram_bot import get_bot_token


class JobTaskProcessorAgent:
    """Finds runnable jobs for an event and prepares tools + prompt for :class:`core.agent.base.Agent`."""

    @staticmethod
    def _job_listens_for_event(triggers: list[Any], event_slug: str) -> bool:
        for tr in triggers or []:
            if isinstance(tr, dict) and tr.get("type") == "event" and tr.get("on") == event_slug:
                return True
        return False

    @staticmethod
    def _action_targets_account(action: dict[str, Any], account_id: str) -> bool:
        return str(action.get("integration_account_id") or "") == account_id

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

        acc_id = str(account.id)
        tools: list[AgentToolConfig] = []
        seen_names: set[str] = set()

        for act in (job.config or {}).get("actions") or []:
            if not isinstance(act, dict):
                continue
            if not JobTaskProcessorAgent._action_targets_account(act, acc_id):
                continue
            slug = act.get("actionable_slug") or act.get("actionable_id")
            if slug == TELEGRAM_SEND_MESSAGE.slug:
                cfg = make_send_telegram_message_tool(bot_token=bot_token, chat_id=chat_id)
                if cfg.tool.name not in seen_names:
                    seen_names.add(cfg.tool.name)
                    tools.append(cfg)
        return tools

    @staticmethod
    def find_matching_jobs_for_telegram_private_message(
        account: IntegrationAccount,
    ) -> list[JobAssignment]:
        """Enabled jobs in the workspace that listen for private Telegram messages and include this bot in actions."""
        event_slug = TELEGRAM_PRIVATE_MESSAGE.slug
        acc_id = str(account.id)
        out: list[JobAssignment] = []
        qs = JobAssignment.objects.filter(workspace=account.workspace, enabled=True).order_by("role_name")
        for job in qs:
            cfg = job.config or {}
            identities = cfg.get("identities") or []
            if not isinstance(identities, list) or len(identities) == 0:
                continue
            if not JobTaskProcessorAgent._job_listens_for_event(cfg.get("triggers") or [], event_slug):
                continue
            actions = cfg.get("actions") or []
            if not any(
                isinstance(a, dict) and JobTaskProcessorAgent._action_targets_account(a, acc_id) for a in actions
            ):
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
        cfg = job.config or {}
        raw_ids = cfg.get("identities") or []
        id_list: list[uuid.UUID] = []
        for x in raw_ids:
            try:
                id_list.append(uuid.UUID(str(x)))
            except (TypeError, ValueError, AttributeError):
                continue
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
