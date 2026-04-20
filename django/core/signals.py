"""Django model signals for ``core``."""

from __future__ import annotations

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from core.models.integration_account import IntegrationAccount
from core.services.job_assignment_integration_cleanup import (
    prune_jobs_referencing_integration_account,
)


@receiver(pre_delete, sender=IntegrationAccount)
def integration_account_pre_delete_prune_jobs(
    sender,
    instance: IntegrationAccount,
    **kwargs,
) -> None:
    """Strip or delete ``JobAssignment`` rows that embed this account in ``config`` JSON."""
    prune_jobs_referencing_integration_account(instance)
