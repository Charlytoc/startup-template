from ninja import Router, Schema

from core.tasks.agentic_chat import run_agentic_chat
from core.services.auth import ApiKeyAuth

router = Router(tags=["AgenticChat"])


class AgenticChatMessageRequest(Schema):
    message: str


class AgenticChatMessageResponse(Schema):
    status: str


@router.get("/health", response={200: dict}, auth=ApiKeyAuth())
def health(request):
    return 200, {"status": "ok", "service": "agentic-chat"}


@router.post(
    "/messages",
    response={200: AgenticChatMessageResponse},
    auth=ApiKeyAuth(require_active_organization=True),
)
def send_message(request, data: AgenticChatMessageRequest):
    run_agentic_chat.delay(request.user.id, data.message, request.organization.id)
    return 200, AgenticChatMessageResponse(status="processing")
