"""Through model linking a ``CyberIdentity`` to an ``IntegrationAccount`` with scoped capabilities."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.cyber_identity import CyberIdentity
from core.models.integration_account import IntegrationAccount


class IntegrationBridge(TimeStampedModel):
    """
    Binds a ``CyberIdentity`` to an ``IntegrationAccount`` and declares what the identity is allowed to do on it.

    The ``capabilities`` JSON is the source of truth for permission-like checks and is
    validated against a per-provider pydantic schema at the service layer. ``config`` is
    free-form per-bridge runtime configuration (quiet hours, persona overrides, etc.).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    identity = models.ForeignKey(
        CyberIdentity,
        on_delete=models.CASCADE,
        related_name="integration_bridges",
    )
    integration_account = models.ForeignKey(
        IntegrationAccount,
        on_delete=models.CASCADE,
        related_name="identity_bridges",
    )

    is_active = models.BooleanField(default=True)

    capabilities = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Scoped capabilities this identity has on the account "
            "(e.g. {'can_post': true, 'can_reply_dm': false}). "
            "Validated by a per-provider pydantic schema at the service layer."
        ),
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-bridge runtime configuration set when integrations are wired up.",
    )

    class Meta:
        ordering = ("integration_account_id", "identity_id")
        constraints = [
            models.UniqueConstraint(
                fields=("identity", "integration_account"),
                name="uniq_identity_integration_bridge",
            ),
        ]
        indexes = [
            models.Index(fields=("integration_account", "is_active")),
            models.Index(fields=("identity", "is_active")),
        ]

    def __str__(self) -> str:
        return f"{self.identity_id} ↔ {self.integration_account_id}"

    def clean(self) -> None:
        super().clean()
        for field_name in ("capabilities", "config"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, dict):
                raise ValidationError({field_name: "Must be a JSON object (dict)."})
        if (
            self.identity_id
            and self.integration_account_id
            and self.identity.workspace_id != self.integration_account.workspace_id
        ):
            raise ValidationError(
                "Identity and integration account must belong to the same workspace."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
