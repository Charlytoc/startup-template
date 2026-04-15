from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.organization import Organization
from core.models.role import Role


class Workspace(TimeStampedModel):
    """A workspace within an organization (agents, tasks, connectors are scoped here)."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="workspaces",
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ("organization_id", "name")

    def __str__(self):
        return f"{self.name} (org {self.organization_id})"


class WorkspaceMember(TimeStampedModel):
    """Workspace access: user + IAM role in that workspace."""

    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="workspace_members",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="workspace_members",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INVITED,
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workspace_invites_sent",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "workspace"),
                name="core_workspacemember_user_workspace_uniq",
            ),
        ]
        ordering = ("workspace_id", "user_id")

    def clean(self):
        super().clean()
        if self.workspace_id and self.role_id:
            if self.workspace.organization_id != self.role.organization_id:
                raise ValidationError(
                    {"role": "Role must belong to the same organization as the workspace."}
                )

    def __str__(self):
        return f"{self.user_id} → workspace {self.workspace_id} ({self.status})"
