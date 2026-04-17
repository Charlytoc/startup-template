"""Concrete run / instance of a ``TaskTemplate`` (one row per actual execution)."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.task_assignment import TaskAssignment
from core.models.task_template import TaskTemplate
from core.models.workspace import Workspace
from core.models.workspace_member import WorkspaceMember


class TaskExecution(TimeStampedModel):
    """A single run of a task. Created by the scheduler, event dispatcher, or a manual trigger."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        WAITING_APPROVAL = "waiting_approval", "Waiting approval"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="task_executions",
    )
    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
    )
    task_assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
    )
    approved_by = models.ForeignKey(
        WorkspaceMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_task_executions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    requires_approval = models.BooleanField(default=False)

    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Run payload: resolved inputs, structured outputs, trigger info, errors, external delivery metadata.",
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=("workspace", "status", "-created")),
            models.Index(fields=("task_template", "status")),
            models.Index(fields=("task_assignment", "-created")),
        ]

    def __str__(self) -> str:
        return f"Execution {self.pk} [{self.get_status_display()}]"

    def clean(self) -> None:
        super().clean()
        if self.details is not None and not isinstance(self.details, dict):
            raise ValidationError({"details": "Must be a JSON object (dict)."})

        if (
            self.task_template_id
            and self.workspace_id
            and self.task_template.workspace_id != self.workspace_id
        ):
            raise ValidationError(
                "Task template must belong to the same workspace as the execution."
            )
        if (
            self.task_assignment_id
            and self.task_template_id
            and self.task_assignment.task_template_id != self.task_template_id
        ):
            raise ValidationError(
                "Task assignment must point to the same task template as the execution."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
