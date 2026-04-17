"""Workspace-scoped external account (Instagram, Gmail, Telegram, ...) with Fernet-encrypted auth."""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.workspace import Workspace
from core.utils.encryption import decrypt_dict, encrypt_dict


class IntegrationAccount(TimeStampedModel):
    """
    A third-party account connected to a workspace that CyberIdentities can act on.

    Secrets (OAuth tokens, bot tokens, refresh tokens, ...) live in ``encrypted_auth`` and
    are accessed via the :pyattr:`auth` property, which transparently decrypts/encrypts the
    payload with ``settings.INTEGRATION_ENCRYPTION_KEY``.
    """

    class Provider(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        GMAIL = "gmail", "Gmail"
        TELEGRAM = "telegram", "Telegram"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="integration_accounts",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integration_accounts_created",
    )

    provider = models.CharField(max_length=40, choices=Provider.choices)
    external_account_id = models.CharField(
        max_length=255,
        help_text="Stable id from the provider (IG business account id, gmail address, telegram bot id, ...).",
    )
    display_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human label shown in the UI (e.g. '@mybrand', 'support@acme.com').",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    encrypted_auth = models.TextField(
        blank=True,
        help_text="Fernet-encrypted JSON blob with provider-specific secrets (tokens, cookies, ...).",
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Non-secret provider configuration: granted scopes, webhook ids, timezone, "
            "cached profile metadata, etc. Validated by per-provider pydantic schemas at the service layer."
        ),
    )

    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ("workspace_id", "provider", "display_name")
        constraints = [
            models.UniqueConstraint(
                fields=("workspace", "provider", "external_account_id"),
                name="uniq_integration_per_workspace_provider_external",
            ),
        ]
        indexes = [
            models.Index(fields=("workspace", "provider", "status")),
        ]

    def __str__(self) -> str:
        label = self.display_name or self.external_account_id or str(self.pk)
        return f"{self.get_provider_display()} — {label}"

    @property
    def auth(self) -> dict[str, Any]:
        """Decrypted auth payload; returns ``{}`` when not set."""
        if not self.encrypted_auth:
            return {}
        return decrypt_dict(self.encrypted_auth, settings.INTEGRATION_ENCRYPTION_KEY)

    @auth.setter
    def auth(self, value: dict[str, Any] | None) -> None:
        if not value:
            self.encrypted_auth = ""
            return
        if not isinstance(value, dict):
            raise ValidationError({"auth": "Must be a JSON object (dict)."})
        self.encrypted_auth = encrypt_dict(value, settings.INTEGRATION_ENCRYPTION_KEY)

    def clean(self) -> None:
        super().clean()
        if self.config is not None and not isinstance(self.config, dict):
            raise ValidationError({"config": "Must be a JSON object (dict)."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
