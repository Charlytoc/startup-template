"""Pydantic shapes for ``TaskExecution.inputs`` / ``TaskExecution.outputs``."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.schemas.channel import Channel


class IdentityConfigSnapshot(BaseModel):
    """Snapshot of a cyber identity's config at the moment the execution was created (reproducibility)."""

    model_config = ConfigDict(extra="allow")

    identity: UUID
    config: dict[str, Any] = Field(default_factory=dict)


class TaskExecutionInputs(BaseModel):
    """Inputs persisted on ``TaskExecution.inputs``.

    ``task_instructions`` is always required. ``output_schema`` is a JSON Schema dict that the
    agent must conform to (passed to the OpenAI ``response_format`` / structured outputs).
    """

    model_config = ConfigDict(extra="allow")

    task_instructions: str = Field(..., min_length=1)
    parent_job_assignment: UUID | None = None
    output_schema: dict[str, Any] | None = Field(
        default=None,
        description="Optional JSON Schema describing the expected ``final_output``.",
    )
    identity_config: IdentityConfigSnapshot | None = None
    channel: Channel | None = Field(
        default=None,
        description="Where the agent can reach the user (e.g. Telegram chat the task should reply to).",
    )
    trigger: dict[str, Any] | None = Field(
        default=None,
        description="What fired this execution (e.g. {'type':'event','event_id':...} or 'manual').",
    )
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime variables resolved from triggers / templates.",
    )


class ArtifactRef(BaseModel):
    """Lightweight reference to an :class:`core.models.Artifact` produced by the run."""

    model_config = ConfigDict(extra="allow")

    id: UUID
    kind: Literal["image", "video", "audio", "document", "text", "other"] = "other"
    label: str = ""


class TaskExecutionError(BaseModel):
    """Structured error record persisted when ``status == failed``."""

    model_config = ConfigDict(extra="allow")

    message: str
    type: str | None = None
    traceback: str | None = None


class TaskExecutionTokenUsage(BaseModel):
    """Token usage rolled up across the agent loop."""

    model_config = ConfigDict(extra="allow")

    input: int = 0
    output: int = 0
    total: int | None = None


class TaskExecutionOutputs(BaseModel):
    """Outputs persisted on ``TaskExecution.outputs``.

    ``final_output`` is a free-form dict because its shape is dictated by the run-time
    ``inputs.output_schema``. Keep it as ``dict`` here; validate against the JSON Schema at
    the call site (the OpenAI structured-output response will already conform).
    """

    model_config = ConfigDict(extra="allow")

    artifacts: list[ArtifactRef] = Field(default_factory=list)
    final_output: dict[str, Any] | None = None
    total_duration_ms: int | None = None
    agent_session_log: UUID | None = None
    error: TaskExecutionError | None = None
    token_usage: TaskExecutionTokenUsage | None = None
    cost_usd: float | None = None
