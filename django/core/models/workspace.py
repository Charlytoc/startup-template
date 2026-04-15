from django.db import models
from model_utils.models import TimeStampedModel

from core.models.organization import Organization


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
