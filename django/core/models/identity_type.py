"""Organization-defined identity templates (capabilities, tool policy) for workspace cyber identities."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.organization import Organization
from core.schemas.capability_list import validate_capability_list


class IdentityType(TimeStampedModel):
    """
    Defines a class of cyber identity (e.g. "Influencer"): default capabilities and tool configuration.
    ``CyberIdentity`` rows in a workspace reference one of these; the type must belong to the same org as the workspace.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="identity_types",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identity_types_created",
    )
    name = models.CharField(max_length=100, help_text="Human-readable type name (unique per organization).")
    description = models.TextField(blank=True)

    capabilities = models.JSONField(
        default=list,
        help_text='Capability grants for identities of this type: list of objects with at least {"id": "<string>"}.',
    )
    tools_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tool policy for this type (allowed tools, provider options, limits). Must be a JSON object.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "name"),
                name="core_identitytype_organization_name_uniq",
            ),
        ]
        ordering = ("organization_id", "name")

    def __str__(self) -> str:
        return f"{self.name} @ {self.organization_id}"

    def clean(self) -> None:
        super().clean()
        validate_capability_list(self.capabilities, field_name="capabilities")
        if self.tools_config is None:
            return
        if not isinstance(self.tools_config, dict):
            raise ValidationError({"tools_config": "Must be a JSON object (dict)."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
