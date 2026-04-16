"""Agent-authored long-term memory for a ``CyberIdentity`` (core memories + on-demand knowledge)."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.cyber_identity import CyberIdentity


class Memory(TimeStampedModel):
    """
    Text memory owned by a ``CyberIdentity``.

    - ``CORE`` memories are always injected into the agent prompt.
    - ``KNOWLEDGE`` memories are retrieved on demand (e.g. by topic) while the agent executes a task.
    """

    class MemoryType(models.TextChoices):
        CORE = "core", "Core"
        KNOWLEDGE = "knowledge", "Knowledge"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    identity = models.ForeignKey(
        CyberIdentity,
        on_delete=models.CASCADE,
        related_name="memories",
    )

    memory_type = models.CharField(
        max_length=20,
        choices=MemoryType.choices,
        default=MemoryType.KNOWLEDGE,
    )
    content = models.TextField(help_text="The memory text to inject or retrieve.")
    source = models.TextField(
        blank=True,
        help_text="Short explanation of why the agent stored this memory (context, task, etc.).",
    )
    topics = models.JSONField(
        default=list,
        blank=True,
        help_text="Topic tags as a list of strings; used to retrieve knowledge memories by topic.",
    )

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=("identity", "memory_type", "-created")),
        ]

    def __str__(self) -> str:
        preview = (self.content or "").strip().splitlines()[0][:60] if self.content else str(self.pk)
        return f"[{self.get_memory_type_display()}] {preview}"

    def clean(self) -> None:
        super().clean()
        if not (self.content or "").strip():
            raise ValidationError({"content": "Memory content cannot be empty."})
        _validate_topics(self.topics)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


def _validate_topics(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise ValidationError({"topics": "Must be a JSON array of strings."})
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError({"topics": "Each topic must be a non-empty string."})
