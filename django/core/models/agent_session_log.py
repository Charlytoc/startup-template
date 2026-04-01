import uuid

from django.db import models
from model_utils.models import TimeStampedModel


class AgentSessionLog(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_session_logs",
    )
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    # Agent configuration snapshot (what was used for this run)
    model = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, default="openai")
    instructions = models.TextField(blank=True)
    tools = models.JSONField(default=list)  # tool definitions passed to the agent

    # Input / Output
    inputs = models.JSONField(default=list)   # list of ExchangeMessage dicts
    outputs = models.JSONField(default=dict)  # final_response + all messages from loop

    # Execution metrics
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    iterations = models.PositiveIntegerField(default=0)
    tool_calls_count = models.PositiveIntegerField(default=0)
    total_duration = models.FloatField(null=True, blank=True)  # seconds
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"AgentSessionLog({self.id}) [{self.status}] user={self.user_id} model={self.model}"
