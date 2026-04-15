from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.organization import Organization


class OrganizationMember(TimeStampedModel):
    """Links a user to an organization (invite / billing / org-wide IAM), separate from workspace access."""

    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_members",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INVITED,
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_invites_sent",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "organization"),
                name="core_organizationmember_user_org_uniq",
            ),
        ]
        ordering = ("organization_id", "user_id")

    def __str__(self):
        return f"{self.user_id} → org {self.organization_id} ({self.status})"
