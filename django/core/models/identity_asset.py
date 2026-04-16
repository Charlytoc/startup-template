"""User-uploaded reference material attached to a ``CyberIdentity`` (images, audio, policy docs, etc.)."""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.cyber_identity import CyberIdentity
from core.models.media_object import MediaObject


class IdentityAsset(TimeStampedModel):
    """
    Stable reference material owned by an identity.

    Unlike :class:`Memory` (agent-authored text), an ``IdentityAsset`` is user-uploaded
    and always backed by a :class:`MediaObject`. It is consumed by generation and RAG
    pipelines as reference material (e.g. reference images for image generation,
    policy documents for retrieval).
    """

    class AssetType(models.TextChoices):
        REFERENCE_IMAGE = "reference_image", "Reference image"
        REFERENCE_AUDIO = "reference_audio", "Reference audio"
        POLICY_DOCUMENT = "policy_document", "Policy document"
        BRAND_GUIDELINE = "brand_guideline", "Brand guideline"
        STYLE_REFERENCE = "style_reference", "Style reference"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    identity = models.ForeignKey(
        CyberIdentity,
        on_delete=models.CASCADE,
        related_name="assets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identity_assets_created",
    )
    media = models.ForeignKey(
        MediaObject,
        on_delete=models.PROTECT,
        related_name="identity_assets",
        help_text="The stored binary this asset points to.",
    )

    asset_type = models.CharField(
        max_length=40,
        choices=AssetType.choices,
        help_text="Platform-defined category that drives which pipeline consumes the asset.",
    )
    label = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional human-readable label (e.g. 'front-facing portrait').",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive assets are not fed to generation/RAG pipelines.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Free-form metadata (per-type hints, capture context, provider tags, etc.).",
    )

    class Meta:
        ordering = ("identity_id", "asset_type", "-created")
        indexes = [
            models.Index(fields=("identity", "asset_type", "is_active")),
        ]

    def __str__(self) -> str:
        label = self.label or self.get_asset_type_display()
        return f"{label} — {self.identity_id}"

    def clean(self) -> None:
        super().clean()
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": "Must be a JSON object (dict)."})
        if (
            self.identity_id
            and self.media_id
            and self.identity.workspace_id != self.media.workspace_id
        ):
            raise ValidationError(
                {"media": "MediaObject must belong to the same workspace as the identity."}
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
