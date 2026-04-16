"""A concrete cyber identity in a workspace, instantiated from an org-level ``IdentityType``."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.identity_type import IdentityType
from core.models.workspace import Workspace


class CyberIdentity(TimeStampedModel):
    """
    Workspace-scoped persona/agent identity. ``identity_type`` supplies default capabilities and ``tools_config``;
    per-instance settings can live in ``config``.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="cyber_identities",
    )
    identity_type = models.ForeignKey(
        IdentityType,
        on_delete=models.PROTECT,
        related_name="cyber_identities",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cyber_identities_created",
    )

    display_name = models.CharField(max_length=200, help_text="Name of this identity in the workspace (e.g. campaign persona).")
    is_active = models.BooleanField(default=True)

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional per-instance settings (e.g. avatar MediaObject id, tone notes). Must be a JSON object.",
    )

    class Meta:
        ordering = ("workspace_id", "display_name")
        indexes = [
            models.Index(fields=("workspace", "identity_type")),
            models.Index(fields=("workspace", "is_active")),
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.identity_type.name})"

    def clean(self) -> None:
        super().clean()
        if self.workspace_id and self.identity_type_id and self.identity_type and self.workspace:
            if self.identity_type.organization_id != self.workspace.organization_id:
                raise ValidationError(
                    {"identity_type": "Identity type must belong to the same organization as the workspace."}
                )
        if self.config is not None and not isinstance(self.config, dict):
            raise ValidationError({"config": "Must be a JSON object (dict)."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
