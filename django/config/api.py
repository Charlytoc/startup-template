from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI, Schema
from config import settings
from ninja.errors import HttpError
# Include routers
from core.routers import agentic_chat_router, auth_router, integrations_instagram_router, integrations_telegram_router, workspaces_router

class ErrorResponseSchema(Schema):
    error: str
    error_code: str | None

docs_decorator = staff_member_required if not settings.DEBUG else None

api = NinjaAPI(docs_decorator=docs_decorator)

@api.exception_handler(HttpError)
def http_error(request, exc):
    error_code = getattr(exc, "error_code", None)
    return api.create_response(
        request,
        ErrorResponseSchema(error=str(exc), error_code=error_code),
        status=exc.status_code,
    )

api.add_router("/auth/", auth_router)
api.add_router("/agentic-chat/", agentic_chat_router)
api.add_router("/workspaces/", workspaces_router)
api.add_router("/integrations/telegram/", integrations_telegram_router)
api.add_router("/integrations/instagram/", integrations_instagram_router)