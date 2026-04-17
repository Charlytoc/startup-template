"""Reusable "recipe" describing how a given kind of agent task should be performed."""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.workspace import Workspace


class TaskTemplate(TimeStampedModel):
    """Workspace-scoped template: prompts, expected inputs/outputs, and tools for a task type."""

    class Type(models.TextChoices):
        POST = "post", "Post"
        REPLY = "reply", "Reply"
        REPORT = "report", "Report"
        NOTIFICATION = "notification", "Notification"
        CUSTOM = "custom", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="task_templates",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_templates_created",
    )

    type = models.CharField(max_length=40, choices=Type.choices)
    name = models.CharField(max_length=200, help_text="Short label shown in the UI.")
    description = models.TextField(blank=True)

    instructions = models.TextField(
        blank=True,
        help_text=(
            "System prompt / instructions the agent receives for this template. "
            "May reference input variables with '{{input_name}}' placeholders, resolved at execution time."
        ),
    )
    input_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="Pydantic/JSON schema plus defaults for the input variables consumed by ``instructions``.",
    )
    output_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="Pydantic JSON schema describing the expected output the agent must return.",
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Template-level configuration (allowed tools, model/provider, rate limits, ...).",
    )

    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("workspace_id", "type", "name")
        indexes = [
            models.Index(fields=("workspace", "type", "enabled")),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"

    def clean(self) -> None:
        super().clean()
        for field_name in ("input_schema", "output_schema", "config"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, dict):
                raise ValidationError({field_name: "Must be a JSON object (dict)."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
