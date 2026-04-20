"""A single turn in a :class:`core.models.Conversation` (user or assistant)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel
from openai.types.responses.response_input_item import Message as OpenAIInputMessage
from openai.types.responses.response_input_text import ResponseInputText
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText

from core.models.conversation import Conversation


class Message(TimeStampedModel):
    """One message in a conversation. ``content_text`` is plain text; ``content_structured`` is optional rich JSON."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    content_text = models.TextField(
        blank=True,
        default="",
        help_text="Plain-text content of the message. Empty string if only structured content is present.",
    )
    content_structured = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional structured content (tool calls, rich payloads, attachments metadata).",
    )

    class Meta:
        ordering = ("conversation_id", "created")
        indexes = [
            models.Index(fields=("conversation", "created")),
            models.Index(fields=("conversation", "role", "created")),
        ]

    def __str__(self) -> str:
        preview = (self.content_text or "").strip().splitlines()[0:1]
        head = preview[0][:60] if preview else "(structured)"
        return f"[{self.role}] {head}"

    def clean(self) -> None:
        super().clean()
        if self.content_structured is not None and not isinstance(self.content_structured, (dict, list)):
            raise ValidationError({"content_structured": "Must be a JSON object or array."})
        if not (self.content_text or "").strip() and self.content_structured is None:
            raise ValidationError("Message must have either content_text or content_structured.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def _text_for_openai(self) -> str:
        """Return the best plain-text projection of the message for OpenAI Responses API.

        Uses ``content_text`` if present; otherwise serializes ``content_structured`` as JSON so
        the model still has signal when only structured content was stored.
        """
        text = (self.content_text or "").strip()
        if text:
            return text
        if self.content_structured is not None:
            return json.dumps(self.content_structured, ensure_ascii=False, default=str)
        return ""

    def to_openai_input_item(self) -> OpenAIInputMessage | ResponseOutputMessage:
        """Convert this message to the right OpenAI Responses input item.

        - ``role == user``      → :class:`openai.types.responses.response_input_item.Message`
          with an ``input_text`` content part.
        - ``role == assistant`` → :class:`openai.types.responses.response_output_message.ResponseOutputMessage`
          with an ``output_text`` content part (shape matches prior API output so it can be fed back).
        """
        text = self._text_for_openai()
        if self.role == self.Role.USER:
            return OpenAIInputMessage(
                role="user",
                content=[ResponseInputText(type="input_text", text=text)],
            )
        if self.role == self.Role.ASSISTANT:
            return ResponseOutputMessage(
                id=f"msg_{uuid.uuid4().hex}",
                role="assistant",
                type="message",
                status="completed",
                content=[
                    ResponseOutputText(type="output_text", text=text, annotations=[]),
                ],
            )
        raise ValueError(f"Unsupported message role for OpenAI conversion: {self.role!r}")
