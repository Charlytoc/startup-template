"""Tool: send a user-visible message to a pre-resolved indexed target."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from core.agent.base import AgentTool, AgentToolConfig
from core.models import Artifact, Conversation, IntegrationAccount
from core.schemas.send_target import ResolvedSendTarget, SendTargetProvider
from core.services.conversations import append_assistant_message
from core.services.instagram_service import get_access_token, get_ig_user_id, instagram_send_message
from core.services.redis_publisher import publish_to_bridge
from core.services.telegram_bot import get_bot_token, telegram_send_message

logger = logging.getLogger(__name__)


def _append_if_same_thread(
    *,
    conversation_for_append: Conversation | None,
    target: ResolvedSendTarget,
    text: str,
    content_structured: dict,
) -> None:
    if conversation_for_append is None:
        return
    if conversation_for_append.integration_account_id != target.integration_account_id:
        return
    cfg = conversation_for_append.get_config()
    if (cfg.external_thread_id or "").strip() != target.external_thread_id.strip():
        return
    try:
        append_assistant_message(
            conversation_for_append,
            content_text=text,
            content_structured=content_structured,
        )
    except Exception:
        logger.exception(
            "append_assistant_message failed conversation=%s target_index=%s",
            conversation_for_append.id,
            target.target_index,
        )


def _artifact_attachment_payload(artifact: Artifact) -> dict[str, Any]:
    metadata = artifact.metadata or {}
    payload: dict[str, Any] = {
        "type": "artifact",
        "artifact_id": str(artifact.id),
        "kind": artifact.kind,
        "label": artifact.label or "",
        "created": artifact.created.isoformat() if artifact.created else "",
        "media": None,
        "text_preview": "",
    }
    if artifact.kind == Artifact.Kind.TEXT:
        payload["text_preview"] = str(metadata.get("text") or "")[:500]
    if artifact.media_id and artifact.media is not None:
        payload["media"] = {
            "id": str(artifact.media.id),
            "display_name": artifact.media.display_name,
            "mime_type": artifact.media.mime_type or "",
            "byte_size": artifact.media.byte_size,
            "public_url": artifact.media.resolve_public_url(),
        }
    return payload


def _resolve_artifact_attachments(
    *,
    conversation: Conversation | None,
    artifact_ids: list[str] | None,
) -> tuple[list[dict[str, Any]], str | None]:
    if not artifact_ids:
        return [], None
    if conversation is None:
        return [], "artifact_ids require an active conversation."

    parsed: list[UUID] = []
    for raw in artifact_ids:
        try:
            parsed.append(UUID(str(raw)))
        except (TypeError, ValueError):
            return [], f"Invalid artifact id: {raw!r}."

    rows = list(
        Artifact.objects.filter(id__in=parsed, workspace=conversation.workspace)
        .select_related("media")
        .order_by("created")
    )
    by_id = {row.id: row for row in rows}
    missing = [str(aid) for aid in parsed if aid not in by_id]
    if missing:
        return [], f"Artifacts not found in this workspace: {', '.join(missing)}."
    return [_artifact_attachment_payload(by_id[aid]) for aid in parsed], None


def _send_web_chat_message(
    *,
    conversation: Conversation | None,
    target: ResolvedSendTarget,
    text: str,
    content_structured: dict[str, Any] | None,
) -> str:
    if conversation is None:
        return "Error: web chat conversation not available."
    if target.web_user_id is None:
        return "Error: web chat target is missing user id."
    try:
        msg = append_assistant_message(
            conversation,
            content_text=text,
            content_structured=content_structured,
        )
    except Exception:
        logger.exception(
            "append_assistant_message failed conversation=%s user=%s",
            conversation.id,
            target.web_user_id,
        )
        return "Error: failed to persist message."
    try:
        created_iso = msg.created.isoformat() if msg.created else ""
        publish_to_bridge(
            listener=f"user-{target.web_user_id}",
            event="agentic-chat-message",
            data={
                "conversation_id": str(conversation.id),
                "message_id": str(msg.id),
                "message": {
                    "role": "assistant",
                    "content": text,
                    "created": created_iso,
                    "attachments": (content_structured or {}).get("attachments") or [],
                },
                "timestamp": created_iso,
            },
        )
    except Exception:
        logger.exception(
            "publish_to_bridge failed conversation=%s user=%s",
            conversation.id,
            target.web_user_id,
        )
    return "Message sent successfully."


def make_send_message_tool(
    *,
    targets: list[ResolvedSendTarget],
    conversation_for_append: Conversation | None = None,
) -> AgentToolConfig:
    """Return ``send_message`` with ``target_index`` + ``message`` (destinations are server-fixed)."""
    lines = "\n".join(
        f"- {t.target_index}: ({t.target_role}) [{t.provider.value}]"
        for t in targets
    )
    tool = AgentTool(
        type="function",
        name="send_message",
        description=(
            "Send a plain-text message to one of the outbound targets listed in the system prompt. "
            "Pick the correct **target_index** (0-based). Only **message** is free text; you cannot "
            "change the destination or integration account from this call.\n\n"
            f"Targets for this run:\n{lines}"
        ),
        parameters={
            "type": "object",
            "properties": {
                "target_index": {
                    "type": "integer",
                    "description": "Index of the target from the system prompt list (0-based).",
                },
                "message": {
                    "type": "string",
                    "description": "Full text to send to that target.",
                },
                "artifact_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional artifact ids to attach to this message. Use this when notifying "
                        "the user about generated images, text artifacts, or other durable outputs."
                    ),
                    "default": [],
                },
            },
            "required": ["target_index", "message"],
            "additionalProperties": False,
        },
    )

    by_index: dict[int, ResolvedSendTarget] = {t.target_index: t for t in targets}

    def execute(target_index: int, message: str, artifact_ids: list[str] | None = None) -> str:
        text = (message or "").strip()
        if not text:
            return "Error: message must be non-empty."
        attachments, attachment_error = _resolve_artifact_attachments(
            conversation=conversation_for_append,
            artifact_ids=artifact_ids,
        )
        if attachment_error is not None:
            return f"Error: {attachment_error}"
        content_structured: dict[str, Any] | None = (
            {"attachments": attachments} if attachments else None
        )
        idx = int(target_index)
        target = by_index.get(idx)
        if target is None:
            return f"Error: invalid target_index={idx}. Valid indices: {sorted(by_index.keys())}."

        if target.provider == SendTargetProvider.WEB_CHAT:
            return _send_web_chat_message(
                conversation=conversation_for_append,
                target=target,
                text=text,
                content_structured=content_structured,
            )

        if target.integration_account_id is None:
            return "Error: integration account not configured for target."
        account = IntegrationAccount.objects.filter(id=target.integration_account_id).first()
        if account is None:
            return "Error: integration account not found."

        if target.provider == SendTargetProvider.TELEGRAM:
            token = get_bot_token(account)
            if not token:
                return "Error: Telegram bot token not configured."
            try:
                sent = telegram_send_message(token, target.external_thread_id, text)
            except ValueError as exc:
                return f"Error: {exc}"
            _append_if_same_thread(
                conversation_for_append=conversation_for_append,
                target=target,
                text=text,
                content_structured={
                    **(content_structured or {}),
                    "telegram_sent": sent,
                },
            )
            return "Message sent successfully."

        if target.provider == SendTargetProvider.INSTAGRAM:
            access = get_access_token(account)
            ig_uid = get_ig_user_id(account)
            if not access or not ig_uid:
                return "Error: Instagram token or ig_user_id not configured."
            try:
                sent = instagram_send_message(access, ig_uid, target.external_thread_id, text)
            except ValueError as exc:
                return f"Error: {exc}"
            _append_if_same_thread(
                conversation_for_append=conversation_for_append,
                target=target,
                text=text,
                content_structured={
                    **(content_structured or {}),
                    "instagram_sent": sent,
                },
            )
            return "Message sent successfully."

        return "Error: unsupported provider."

    return AgentToolConfig(tool=tool, function=execute)
