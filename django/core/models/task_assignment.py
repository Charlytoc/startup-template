"""Trigger + binding layer: when/where/who runs a given ``TaskTemplate``."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.task_template import TaskTemplate


class TaskAssignment(TimeStampedModel):
    """Binds a ``TaskTemplate`` to a concrete run context (trigger, targets, inputs, approvals)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    title = models.CharField(max_length=200, blank=True)

    creation_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Who/what created this assignment (user, agent, reason).",
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Assignment configuration: trigger, target accounts and identities, input overrides, approval policy.",
    )

    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("task_template_id", "title")
        indexes = [
            models.Index(fields=("task_template", "enabled")),
        ]

    def __str__(self) -> str:
        return str(self.title or self.task_template_id)

    def clean(self) -> None:
        super().clean()
        for field_name in ("creation_details", "config"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, dict):
                raise ValidationError({field_name: "Must be a JSON object (dict)."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
