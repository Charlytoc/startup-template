from django.db.models.signals import post_delete
from django.dispatch import receiver

from core.models.integration_account import IntegrationAccount
from core.services.job_assignment_integration_cleanup import (
    cleanup_job_assignments_for_deleted_integration_account,
)


@receiver(post_delete, sender=IntegrationAccount)
def _cleanup_job_assignments_on_integration_account_delete(sender, instance, **kwargs):
    cleanup_job_assignments_for_deleted_integration_account(
        workspace_id=instance.workspace_id,
        integration_account_id=instance.pk,
    )
