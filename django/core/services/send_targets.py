"""Resolve validated outbound send targets for a job (Conversation-free core primitive)."""

from __future__ import annotations

import logging
import uuid
from typing import NamedTuple

from core.integrations.actionables import (
    INSTAGRAM_SEND_MESSAGE,
    TELEGRAM_SEND_MESSAGE,
)
from core.models import Conversation, IntegrationAccount, JobAssignment
from core.schemas.integration_account import SenderApprovalStatus
from core.schemas.job_assignment import JobAssignmentAction
from core.schemas.send_target import (
    ResolvedSendTarget,
    SendTargetProvider,
    SendTargetResolution,
)
from core.services.integration_senders import get_sender

logger = logging.getLogger(__name__)


class SendTargetSeed(NamedTuple):
    """Explicit (account, thread, role) for one possible recipient in this agent run."""

    integration_account: IntegrationAccount
    external_thread_id: str
    target_role: str


def resolve_send_target(
    *,
    job: JobAssignment,
    integration_account: IntegrationAccount,
    external_thread_id: str,
    actions: list[JobAssignmentAction] | None = None,
) -> SendTargetResolution | None:
    """Return a validated send target if the job may send to this integration + thread.

    Checks (1) job action binds ``telegram.send_message`` / ``instagram.send_message`` to this
    account, and (2) ``config.senders`` contains ``external_thread_id`` with an allowed
    ``approval_status`` (Telegram: ``APPROVED`` only; Instagram: not ``PENDING``).
    """
    tid = (external_thread_id or "").strip()
    if not tid:
        return None

    active_actions = actions if actions is not None else job.get_config().actions
    provider = integration_account.provider

    if provider == IntegrationAccount.Provider.TELEGRAM:
        slug = TELEGRAM_SEND_MESSAGE.slug
        stype = SendTargetProvider.TELEGRAM
    elif provider == IntegrationAccount.Provider.INSTAGRAM:
        slug = INSTAGRAM_SEND_MESSAGE.slug
        stype = SendTargetProvider.INSTAGRAM
    else:
        return None

    if not any(
        a.actionable_slug == slug and a.integration_account_id == integration_account.id
        for a in active_actions
    ):
        return None

    sender = get_sender(integration_account, tid)
    if sender is None:
        return None

    if provider == IntegrationAccount.Provider.TELEGRAM:
        if sender.approval_status != SenderApprovalStatus.APPROVED:
            return None
    elif sender.approval_status == SenderApprovalStatus.PENDING:
        return None

    return SendTargetResolution(
        provider=stype,
        integration_account_id=integration_account.id,
        external_thread_id=tid,
    )


def collect_resolved_send_targets(
    *,
    job: JobAssignment,
    conversation: Conversation | None,
    actions: list[JobAssignmentAction] | None = None,
) -> list[ResolvedSendTarget]:
    """Build the indexed target list for this run from explicit seeds (not a full sender scan)."""
    seeds: list[SendTargetSeed] = []
    active_actions = actions if actions is not None else job.get_config().actions
    if conversation is not None and conversation.origin == Conversation.Origin.WEB:
        web_user_id = conversation.get_config().web_user_id
        if web_user_id is not None:
            return [
                ResolvedSendTarget(
                    target_index=0,
                    target_role="This is the web chat user you are interacting with right now.",
                    provider=SendTargetProvider.WEB_CHAT,
                    web_user_id=web_user_id,
                )
            ]

    if (
        conversation is not None
        and conversation.origin == Conversation.Origin.INTEGRATION
        and conversation.integration_account_id is not None
    ):
        account = conversation.integration_account
        tid = (conversation.get_config().external_thread_id or "").strip()
        if tid and account.provider in (
            IntegrationAccount.Provider.TELEGRAM,
            IntegrationAccount.Provider.INSTAGRAM,
        ):
            seeds.append(
                SendTargetSeed(
                    integration_account=account,
                    external_thread_id=tid,
                    target_role="This is the user you are interacting with right now.",
                )
            )

    out: list[ResolvedSendTarget] = []
    for seed in seeds:
        res = resolve_send_target(
            job=job,
            integration_account=seed.integration_account,
            external_thread_id=seed.external_thread_id,
            actions=active_actions,
        )
        if res is None:
            logger.info(
                "send_targets skip_seed job_id=%s account_id=%s thread_prefix=%s",
                job.id,
                seed.integration_account.id,
                seed.external_thread_id[:24],
            )
            continue
        out.append(
            ResolvedSendTarget(
                target_index=len(out),
                target_role=seed.target_role,
                provider=res.provider,
                integration_account_id=res.integration_account_id,
                external_thread_id=res.external_thread_id,
            )
        )
    return out
