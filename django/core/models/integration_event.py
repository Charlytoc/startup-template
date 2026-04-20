"""Inbound event log from external integrations (webhooks, pollers, ...). No dispatch logic yet."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from core.models.integration_account import IntegrationAccount


class IntegrationEvent(TimeStampedModel):
    """
    Activity tied to an ``IntegrationAccount`` (inbound webhooks, outbound API actions we log, …).

    Stored verbatim so event dispatching and replay (firing ``JobAssignment`` runs via
    ``TaskExecution``) can be built later without replaying from the provider.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    integration_account = models.ForeignKey(
        IntegrationAccount,
        on_delete=models.CASCADE,
        related_name="events",
    )

    event_type = models.CharField(
        max_length=100,
        help_text="Provider-qualified event id, e.g. 'instagram.new_comment', 'gmail.new_email'.",
    )
    external_event_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Provider-side identifier used for idempotency if any. Its optional but it's a good practice to have it.",
    )

    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw provider payload.",
    )

    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when the orchestrator has handled this event (created executions, ignored, ...).",
    )
    error_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured error info for the last failed processing attempt, e.g. {'message': ..., 'traceback': ...}.",
    )

    class Meta:
        ordering = ("-received_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("integration_account", "event_type", "external_event_id"),
                name="uniq_integration_event_external_id",
                condition=models.Q(external_event_id__gt=""),
            ),
        ]
        indexes = [
            models.Index(fields=("integration_account", "event_type", "-received_at")),
            models.Index(fields=("processed_at",)),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.integration_account_id}"

    def clean(self) -> None:
        super().clean()
        for field_name in ("payload", "error_details"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, dict):
                raise ValidationError({field_name: "Must be a JSON object (dict)."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
