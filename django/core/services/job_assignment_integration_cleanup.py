"""Keep ``JobAssignment`` rows consistent when an ``IntegrationAccount`` is removed."""

from __future__ import annotations

import logging
import uuid

from ninja.errors import HttpError

from core.integrations.actionables import INSTAGRAM_SEND_MESSAGE, TELEGRAM_SEND_MESSAGE
from core.integrations.event_types import INSTAGRAM_DM_MESSAGE, TELEGRAM_PRIVATE_MESSAGE
from core.integrations.workspace_actionables import validate_job_assignment_config
from core.models import JobAssignment
from core.models.integration_account import IntegrationAccount
from core.schemas.channel import InstagramDmChannel, TelegramPrivateChannel
from core.schemas.job_assignment import JobAssignmentConfig, JobAssignmentEventTrigger

logger = logging.getLogger(__name__)


def _references_account(cfg: JobAssignmentConfig, account_id: uuid.UUID) -> bool:
    if any(a.id == account_id for a in cfg.accounts):
        return True
    if any(a.integration_account_id == account_id for a in cfg.actions):
        return True
    for ch in cfg.channels:
        if isinstance(ch, TelegramPrivateChannel) and ch.integration_account_id == account_id:
            return True
        if isinstance(ch, InstagramDmChannel) and ch.integration_account_id == account_id:
            return True
    return False


def prune_jobs_referencing_integration_account(account: IntegrationAccount) -> None:
    """Update or delete workspace jobs that pointed at this integration account.

    Called from ``pre_delete`` on :class:`core.models.IntegrationAccount` so it runs for
    API disconnect, admin delete, or any other code path that removes the row.

    - Removes the account from ``config.accounts`` and any ``config.actions`` bound to it.
    - Drops matching ``TelegramPrivateChannel`` / ``InstagramDmChannel`` snapshots.
    - Drops event triggers that no longer match any remaining send-message action.
    - If **no actions** remain, the whole ``JobAssignment`` is deleted (nothing left to run).
    - Otherwise config is re-validated and saved.
    """
    workspace = account.workspace
    account_id = account.id

    for job in list(JobAssignment.objects.filter(workspace=workspace)):
        try:
            cfg = job.get_config()
        except Exception:
            logger.warning("prune_jobs: skip job=%s invalid config", job.id, exc_info=True)
            continue

        if not _references_account(cfg, account_id):
            continue

        new_accounts = [a for a in cfg.accounts if a.id != account_id]
        new_actions = [
            a
            for a in cfg.actions
            if a.integration_account_id is None or a.integration_account_id != account_id
        ]
        new_channels: list = []
        for ch in cfg.channels:
            if isinstance(ch, TelegramPrivateChannel) and ch.integration_account_id == account_id:
                continue
            if isinstance(ch, InstagramDmChannel) and ch.integration_account_id == account_id:
                continue
            new_channels.append(ch)

        has_ig_send = any(a.actionable_slug == INSTAGRAM_SEND_MESSAGE.slug for a in new_actions)
        has_tg_send = any(a.actionable_slug == TELEGRAM_SEND_MESSAGE.slug for a in new_actions)
        new_triggers: list = []
        for tr in cfg.triggers:
            if isinstance(tr, JobAssignmentEventTrigger):
                if tr.on == INSTAGRAM_DM_MESSAGE.slug and not has_ig_send:
                    continue
                if tr.on == TELEGRAM_PRIVATE_MESSAGE.slug and not has_tg_send:
                    continue
            new_triggers.append(tr)

        if not new_actions:
            logger.info(
                "prune_jobs: deleting job=%s workspace=%s (no actions left after removing account=%s)",
                job.id,
                workspace.id,
                account_id,
            )
            job.delete()
            continue

        new_cfg = cfg.model_copy(
            update={
                "accounts": new_accounts,
                "actions": new_actions,
                "channels": new_channels,
                "triggers": new_triggers,
            }
        )
        try:
            validated = validate_job_assignment_config(workspace=workspace, config=new_cfg)
        except HttpError as exc:
            logger.warning(
                "prune_jobs: deleting job=%s after account=%s remove; re-validate failed: %s",
                job.id,
                account_id,
                exc,
            )
            job.delete()
            continue

        job.set_config(validated)
        job.save(update_fields=["config", "modified"])
        logger.info(
            "prune_jobs: updated job=%s workspace=%s (removed references to account=%s)",
            job.id,
            workspace.id,
            account_id,
        )
