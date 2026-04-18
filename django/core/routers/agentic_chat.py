from ninja import Router, Schema
from ninja.security import django_auth

from core.services.auth import ApiKeyAuth, auth_service
from core.tasks.agentic_chat import run_agentic_chat

router = Router(tags=["AgenticChat"])


class AgenticChatMessageRequest(Schema):
    message: str


class AgenticChatMessageResponse(Schema):
    status: str


@router.get("/health", response={200: dict}, auth=[ApiKeyAuth(), django_auth])
def health(request):
    return 200, {"status": "ok", "service": "agentic-chat"}


@router.post(
    "/messages",
    response={200: AgenticChatMessageResponse},
    auth=[ApiKeyAuth(), django_auth],
)
def send_message(request, data: AgenticChatMessageRequest):
    user = auth_service.get_user_from_request(request)
    org = auth_service.get_active_organization(request)
    run_agentic_chat.delay(user.id, data.message, org.id)
    return 200, AgenticChatMessageResponse(status="processing")
