"""Async Instagram webhook messaging: Graph enrichment, DM pipeline, agent."""

from __future__ import annotations

import uuid
from typing import Any

from celery import shared_task
from celery.utils.log import get_task_logger

from core.models import IntegrationAccount
from core.services.instagram_service import process_instagram_webhook_messaging

logger = get_task_logger(__name__)


@shared_task
def process_instagram_webhook_messaging_task(
    integration_account_id: str,
    ig_inbox_id: str,
    messaging: dict[str, Any],
) -> None:
    """Run full Instagram messaging handling after HTTP webhook matched an integration account."""
    try:
        pk = uuid.UUID(integration_account_id)
    except ValueError:
        logger.warning(
            "process_instagram_webhook_messaging_task invalid integration_account_id=%r",
            integration_account_id,
        )
        return

    account = IntegrationAccount.objects.select_related("workspace").filter(id=pk).first()
    if account is None:
        logger.warning(
            "process_instagram_webhook_messaging_task integration_account not found id=%s",
            integration_account_id,
        )
        return
    if account.provider != IntegrationAccount.Provider.INSTAGRAM:
        logger.warning(
            "process_instagram_webhook_messaging_task wrong provider id=%s provider=%s",
            integration_account_id,
            account.provider,
        )
        return

    process_instagram_webhook_messaging(
        account=account,
        ig_account_id=ig_inbox_id,
        raw_messaging=messaging,
    )
