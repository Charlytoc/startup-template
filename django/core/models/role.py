from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.organization import Organization


class Role(TimeStampedModel):
    """Org-scoped IAM role: slug, display name, and capability list (validated in app layer)."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    slug = models.SlugField(max_length=64)
    display_name = models.CharField(max_length=100)
    role_capabilities = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "slug"),
                name="core_role_organization_slug_uniq",
            ),
        ]
        ordering = ("organization_id", "slug")

    def __str__(self):
        return f"{self.display_name} ({self.slug}) @ {self.organization_id}"
