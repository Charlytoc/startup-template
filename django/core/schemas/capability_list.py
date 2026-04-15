"""Shared shape for Role.role_capabilities, ApiToken.capabilities, etc.: list of objects with required string `id`."""

from typing import Any

from django.core.exceptions import ValidationError
from pydantic import BaseModel, ConfigDict, TypeAdapter


class CapabilityItem(BaseModel):
    """At minimum ``{"id": "<string>"}``; extra keys allowed for forward compatibility."""

    model_config = ConfigDict(extra="allow")
    id: str


_capability_list_adapter = TypeAdapter(list[CapabilityItem])


def validate_capability_list(value: Any, *, field_name: str) -> None:
    """Raise ``ValidationError`` if value is not a valid capability list."""
    if value is None:
        return
    if not isinstance(value, list):
        raise ValidationError({field_name: "Must be a JSON array of objects."})
    try:
        _capability_list_adapter.validate_python(value)
    except Exception as exc:
        raise ValidationError({field_name: f"Invalid capability entry: {exc}"}) from exc
