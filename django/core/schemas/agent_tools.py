"""Pydantic shapes for the arguments accepted by agent-callable tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


SCHEDULE_ONE_OFF_MAX_MINUTES = 60 * 24 * 30  # 30 days


class ScheduleOneOffTaskArgs(BaseModel):
    """Arguments for the ``schedule_one_off_task`` agent tool."""

    model_config = ConfigDict(extra="forbid")

    task_instructions: str = Field(
        ...,
        min_length=1,
        description=(
            "Plain-text instructions describing exactly what the future task must do "
            "(include any context the future agent will need)."
        ),
    )
    in_minutes: int = Field(
        ...,
        ge=1,
        le=SCHEDULE_ONE_OFF_MAX_MINUTES,
        description="How many minutes from now to run the task. Must be 1..43200 (30 days).",
    )


class CreateRecurringJobArgs(BaseModel):
    """Arguments for the ``create_recurring_job`` agent tool."""

    model_config = ConfigDict(extra="forbid")

    role_name: str = Field(..., min_length=1, max_length=200)
    instructions: str = Field(
        ...,
        min_length=1,
        description="What the routine should do every time it fires (used as the task instructions).",
    )
    cron: str = Field(
        ...,
        min_length=9,
        description="Standard 5-field UNIX cron expression (UTC). Example: '0 12 * * 1,3,5'.",
    )
    description: str = Field(default="", max_length=500)
