"""Tool: send a Telegram or Instagram text message to a pre-resolved indexed target."""

from __future__ import annotations

import logging

from core.agent.base import AgentTool, AgentToolConfig
from core.models import Conversation, IntegrationAccount
from core.schemas.send_target import ResolvedSendTarget, SendTargetProvider
from core.services.conversations import append_assistant_message
from core.services.instagram_service import get_access_token, get_ig_user_id, instagram_send_message
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
            },
            "required": ["target_index", "message"],
            "additionalProperties": False,
        },
    )

    by_index: dict[int, ResolvedSendTarget] = {t.target_index: t for t in targets}

    def execute(target_index: int, message: str) -> str:
        text = (message or "").strip()
        if not text:
            return "Error: message must be non-empty."
        idx = int(target_index)
        target = by_index.get(idx)
        if target is None:
            return f"Error: invalid target_index={idx}. Valid indices: {sorted(by_index.keys())}."

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
                content_structured={"telegram_sent": sent},
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
                content_structured={"instagram_sent": sent},
            )
            return "Message sent successfully."

        return "Error: unsupported provider."

    return AgentToolConfig(tool=tool, function=execute)
