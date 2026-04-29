"""Concrete run / instance of a ``JobAssignment`` (one row per actual execution)."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.job_assignment import JobAssignment
from core.models.workspace import Workspace
from core.models.workspace_member import WorkspaceMember
from core.schemas.task_execution import TaskExecutionInputs, TaskExecutionOutputs


class TaskExecution(TimeStampedModel):
    """A single run of a ``JobAssignment`` (produced by a trigger, schedule or manual start)."""

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
    job_assignment = models.ForeignKey(
        JobAssignment,
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
    name = models.CharField(max_length=200, blank=True)
    requires_approval = models.BooleanField(default=False)

    inputs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Run inputs: firing trigger, event payload, resolved variables.",
    )
    outputs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Run outputs: final_output, artifact ids, agent_session_log ids, error details.",
    )

    scheduled_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this execution should run (deferred / scheduled). Null = run as soon as possible.",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=("workspace", "status", "-created")),
            models.Index(fields=("job_assignment", "-created")),
            models.Index(fields=("status", "scheduled_to")),
        ]

    def __str__(self) -> str:
        return f"Execution {self.pk} [{self.get_status_display()}]"

    def clean(self) -> None:
        super().clean()
        for field_name in ("inputs", "outputs"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, dict):
                raise ValidationError({field_name: "Must be a JSON object (dict)."})

        if (
            self.job_assignment_id
            and self.workspace_id
            and self.job_assignment.workspace_id != self.workspace_id
        ):
            raise ValidationError(
                "Job assignment must belong to the same workspace as the execution."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def get_inputs(self) -> TaskExecutionInputs:
        return TaskExecutionInputs.model_validate(self.inputs)

    def set_inputs(self, inputs: TaskExecutionInputs) -> None:
        self.inputs = inputs.model_dump(mode="json")

    def get_outputs(self) -> TaskExecutionOutputs:
        return TaskExecutionOutputs.model_validate(self.outputs)

    def set_outputs(self, outputs: TaskExecutionOutputs) -> None:
        self.outputs = outputs.model_dump(mode="json")
