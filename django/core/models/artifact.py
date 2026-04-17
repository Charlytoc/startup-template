"""Output file produced by a ``TaskExecution`` (generated image, rendered report, etc.)."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.media_object import MediaObject
from core.models.task_execution import TaskExecution


class Artifact(TimeStampedModel):
    """A file/media output attached to a task execution."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        TEXT = "text", "Text"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    task_execution = models.ForeignKey(
        TaskExecution,
        on_delete=models.CASCADE,
        related_name="artifacts",
    )
    media = models.ForeignKey(
        MediaObject,
        on_delete=models.PROTECT,
        related_name="artifacts",
    )

    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    label = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Free-form per-kind metadata (caption, summary, generator params, prompt, duration, size, etc, format (eg: markdown, html, etc, or png, jpg, etc)).",
    )

    class Meta:
        ordering = ("task_execution_id", "kind", "-created")
        indexes = [
            models.Index(fields=("task_execution", "kind")),
        ]

    def __str__(self) -> str:
        return f"Artifact {self.pk} ({self.get_kind_display()})"

    def clean(self) -> None:
        super().clean()
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": "Must be a JSON object (dict)."})
        if (
            self.task_execution_id
            and self.media_id
            and self.task_execution.workspace_id != self.media.workspace_id
        ):
            raise ValidationError(
                "Media must belong to the same workspace as the task execution."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
