"""Job the agent takes on: role, triggers, and which actionables it may use."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.workspace import Workspace


class JobAssignment(TimeStampedModel):
    """A durable "job" a workspace agent performs, bound to triggers and allowed actionables.

    Runtime targeting (accounts, identities, triggers, actions, approval policy, optional
    output schema) lives under ``config`` as a flexible JSON object; the rough shape is::

        {
          "accounts": [<IntegrationAccount.id>, ...],
          "identities": [<CyberIdentity.id>, ...],  # required, min length 1
          "triggers": [
            {"type": "event"|"cron", "on": "<event_slug or cron>", "filter": {...}}
          ],
          "actions": [
            {"actionable_slug": "telegram.send_message", "integration_account_id": "<uuid>"}
          ],
          "approval_policy": {...},
          "output_schema": {...}   # optional pydantic/json schema
        }
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="job_assignments",
    )

    role_name = models.CharField(
        max_length=200,
        help_text="Role the agent plays, e.g. 'Telegram Message Responder'.",
    )
    description = models.TextField(blank=True, help_text="What this job does, in plain text.")
    instructions = models.TextField(
        blank=True,
        help_text="Detailed instructions so the agent understands how to perform this job at runtime.",
    )

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Targeting + runtime policy: accounts, identities, triggers, actions, approval_policy, optional output_schema.",
    )

    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("workspace_id", "role_name")
        indexes = [
            models.Index(fields=("workspace", "enabled")),
        ]

    def __str__(self) -> str:
        return self.role_name

    def clean(self) -> None:
        super().clean()
        if self.config is not None and not isinstance(self.config, dict):
            raise ValidationError({"config": "Must be a JSON object (dict)."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
