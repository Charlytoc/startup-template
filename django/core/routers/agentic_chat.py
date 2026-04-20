"""Web chat entry point. Runs through the unified JobAssignment + Conversation pipeline.

A message POSTed here requires a ``cyber_identity_id`` that is web-chat enabled (i.e. has a
``system.send_chat_message`` JobAssignment). We:

1. resolve or create the active web-chat ``Conversation`` for ``(workspace, identity, user)``,
2. persist the user message,
3. enqueue :func:`core.tasks.job_assignment_agent.run_job_assignment_agent` so the agent replies
   via the ``send_chat_message`` tool (which writes both the assistant ``Message`` and the
   real-time bridge event).
"""

from __future__ import annotations

import uuid

from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth

from core.models import CyberIdentity, WorkspaceMember
from core.services.auth import ApiKeyAuth, auth_service
from core.services.conversations import (
    append_user_message,
    get_or_create_active_web_conversation,
)
from core.services.job_assignment_defaults import find_web_chat_job_for_identity
from core.tasks.job_assignment_agent import run_job_assignment_agent

router = Router(tags=["AgenticChat"])


class AgenticChatMessageRequest(Schema):
    message: str
    cyber_identity_id: uuid.UUID


class AgenticChatMessageResponse(Schema):
    status: str
    conversation_id: str
    message_id: str
    job_assignment_id: str


class AgenticChatErrorResponse(Schema):
    error: str
    error_code: str


@router.get("/health", response={200: dict}, auth=[ApiKeyAuth(), django_auth])
def health(request):
    return 200, {"status": "ok", "service": "agentic-chat"}


@router.post(
    "/messages",
    response={
        200: AgenticChatMessageResponse,
        400: AgenticChatErrorResponse,
        404: AgenticChatErrorResponse,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def send_message(request, data: AgenticChatMessageRequest):
    text = (data.message or "").strip()
    if not text:
        return 400, AgenticChatErrorResponse(
            error="message cannot be empty.", error_code="MESSAGE_REQUIRED"
        )

    user = auth_service.get_user_from_request(request)

    identity = CyberIdentity.objects.select_related("workspace").filter(
        id=data.cyber_identity_id
    ).first()
    if identity is None:
        return 404, AgenticChatErrorResponse(
            error="Cyber identity not found.", error_code="CYBER_IDENTITY_NOT_FOUND"
        )

    member = WorkspaceMember.objects.filter(
        user=user,
        workspace=identity.workspace,
        status=WorkspaceMember.Status.ACTIVE,
    ).first()
    if member is None:
        raise HttpError(403, "You are not an active member of this workspace.")

    if not identity.is_active:
        return 400, AgenticChatErrorResponse(
            error="This cyber identity is inactive.", error_code="CYBER_IDENTITY_INACTIVE"
        )

    job = find_web_chat_job_for_identity(identity)
    if job is None:
        return 400, AgenticChatErrorResponse(
            error="Web chat is not enabled for this cyber identity.",
            error_code="WEB_CHAT_NOT_ENABLED",
        )

    conversation = get_or_create_active_web_conversation(
        workspace=identity.workspace,
        cyber_identity=identity,
        web_user_id=user.id,
    )
    msg = append_user_message(conversation, content_text=text)

    run_job_assignment_agent.delay(
        str(job.id), str(conversation.id), str(msg.id)
    )

    return 200, AgenticChatMessageResponse(
        status="processing",
        conversation_id=str(conversation.id),
        message_id=str(msg.id),
        job_assignment_id=str(job.id),
    )
