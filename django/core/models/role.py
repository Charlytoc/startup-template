from django.db import models
from model_utils.models import TimeStampedModel

from core.models.organization import Organization
from core.schemas.capability_list import validate_capability_list


class Role(TimeStampedModel):
    """Org-scoped IAM role: slug, display name, and capability list (see ``clean()`` / serializers)."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    slug = models.SlugField(max_length=64)
    display_name = models.CharField(max_length=100)
    role_capabilities = models.JSONField(
        default=list,
        help_text='List of capability objects, each with at least {"id": "<string>"}.',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "slug"),
                name="core_role_organization_slug_uniq",
            ),
        ]
        ordering = ("organization_id", "slug")

    def clean(self):
        super().clean()
        validate_capability_list(self.role_capabilities, field_name="role_capabilities")

    def __str__(self):
        return f"{self.display_name} ({self.slug}) @ {self.organization_id}"
