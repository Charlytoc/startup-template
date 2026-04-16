"""A concrete cyber identity in a workspace with a platform-managed type whitelist."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.workspace import Workspace


class CyberIdentity(TimeStampedModel):
    """Workspace-scoped persona/agent identity. Type is platform-defined; orgs configure each instance via ``config``."""

    class Type(models.TextChoices):
        INFLUENCER = "influencer", "Influencer"
        COMMUNITY_MANAGER = "community_manager", "Community manager"
        ANALYST = "analyst", "Analyst"
        PERSONAL_ASSISTANT = "personal_assistant", "Personal assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="cyber_identities",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cyber_identities_created",
    )

    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        help_text="Platform-defined identity type sold by the application.",
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Name of this identity in the workspace (e.g. campaign persona).",
    )
    is_active = models.BooleanField(default=True)

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-identity configuration owned by the org (tone, avatar MediaObject id, profile settings, etc.).",
    )

    class Meta:
        ordering = ("workspace_id", "display_name")
        indexes = [
            models.Index(fields=("workspace", "type")),
            models.Index(fields=("workspace", "is_active")),
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_type_display()})"

    def clean(self) -> None:
        super().clean()
        if self.config is not None and not isinstance(self.config, dict):
            raise ValidationError({"config": "Must be a JSON object (dict)."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
