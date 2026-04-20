"""Pydantic shape for ``CyberIdentity.config`` (per-identity runtime knobs)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CyberIdentityConfig(BaseModel):
    """Runtime config for a :class:`core.models.CyberIdentity`.

    Intentionally permissive (``extra='allow'``) so we can keep adding knobs without
    schema migrations. The only validated-on-write field today is ``model``.
    """

    model_config = ConfigDict(extra="allow")

    model: str | None = Field(
        default=None,
        description="OpenAI model identifier to use when this identity drives the agent.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form extra config.",
    )
