"""Instagram integration endpoints: OAuth flow, webhook (verify + receive), disconnect."""

from __future__ import annotations

import uuid

from django.http import HttpRequest, HttpResponse
from ninja import Query, Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth

from core.models import IntegrationAccount, Workspace, WorkspaceMember
from core.services.auth import ApiKeyAuth, auth_service
from core.services.instagram_service import (
    _frontend_url,
    build_instagram_oauth_url,
    connect_instagram_account,
    consume_oauth_state,
    disconnect_instagram_account,
    handle_webhook_verification,
    instagram_exchange_code,
    instagram_get_long_lived_token,
    instagram_get_user_info,
    process_webhook_request,
    store_oauth_state,
)
from core.utils.schemas import ErrorResponseSchema

router = Router(tags=["Integrations / Instagram"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class InstagramOAuthUrlResponse(Schema):
    oauth_url: str


class InstagramConnectedAccount(Schema):
    integration_account_id: uuid.UUID
    display_name: str
    ig_username: str


class InstagramConnectResponse(Schema):
    accounts: list[InstagramConnectedAccount]


# ---------------------------------------------------------------------------
# Workspace guard
# ---------------------------------------------------------------------------

def _require_workspace(request: HttpRequest, workspace_id: int) -> Workspace:
    user = auth_service.get_user_from_request(request)
    org = auth_service.get_active_organization(request)
    workspace = Workspace.objects.filter(id=workspace_id, organization=org).first()
    if workspace is None:
        raise HttpError(404, "Workspace not found.")
    member = WorkspaceMember.objects.filter(
        user=user,
        workspace=workspace,
        status=WorkspaceMember.Status.ACTIVE,
    ).first()
    if member is None:
        raise HttpError(403, "You are not an active member of this workspace.")
    return workspace


# ---------------------------------------------------------------------------
# OAuth: initiate
# ---------------------------------------------------------------------------

@router.get(
    "/workspaces/{workspace_id}/instagram/oauth-url",
    response={
        200: InstagramOAuthUrlResponse,
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def instagram_oauth_url(request: HttpRequest, workspace_id: int):
    workspace = _require_workspace(request, workspace_id)
    user = auth_service.get_user_from_request(request)
    state_token = store_oauth_state(workspace_id=workspace.id, user_id=user.pk)
    url = build_instagram_oauth_url(state_token)
    return 200, InstagramOAuthUrlResponse(oauth_url=url)


# ---------------------------------------------------------------------------
# OAuth: callback (browser redirect from Meta)
# ---------------------------------------------------------------------------

class _CallbackParams(Schema):
    code: str | None = None
    state: str | None = None
    error: str | None = None
    error_description: str | None = None


@router.get("/callback/")
def instagram_callback(request: HttpRequest, params: _CallbackParams = Query(...)) -> HttpResponse:
    """
    Meta redirects here after the user authorizes (or denies) the Instagram OAuth request.
    We exchange the code, create IntegrationAccount rows, then redirect to the frontend.
    """
    frontend = _frontend_url()

    if params.error or not params.code or not params.state:
        reason = params.error_description or params.error or "missing_code"
        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/connect-integration?instagram_error={reason}"},
        )

    state_payload = consume_oauth_state(params.state)
    if state_payload is None:
        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/connect-integration?instagram_error=invalid_state"},
        )

    workspace_id: int = state_payload["workspace_id"]
    user_id: int = state_payload["user_id"]

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        workspace = Workspace.objects.get(id=workspace_id)

        short = instagram_exchange_code(params.code)
        long_lived = instagram_get_long_lived_token(short["access_token"])
        user_info = instagram_get_user_info(long_lived["access_token"])

        ig_user_id = str(user_info.get("id") or short.get("user_id") or "")
        ig_username = str(user_info.get("username") or "")

        if not ig_user_id:
            return HttpResponse(
                status=302,
                headers={"Location": f"{frontend}/workspaces/{workspace_id}/integrations?instagram_error=no_ig_accounts"},
            )

        account = connect_instagram_account(
            workspace=workspace,
            user=user,
            access_token=long_lived["access_token"],
            ig_user_id=ig_user_id,
            ig_username=ig_username,
        )

        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/workspaces/{workspace_id}/integrations?instagram_connected=true&account_ids={account.id}"},
        )

    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Instagram OAuth callback failed workspace=%s", workspace_id)
        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/workspaces/{workspace_id}/integrations?instagram_error=server_error"},
        )


# ---------------------------------------------------------------------------
# Webhook: Meta verification (GET) + events (POST)
# ---------------------------------------------------------------------------

@router.get("/webhook/")
def instagram_webhook_verify(
    request: HttpRequest,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> HttpResponse:
    status, body = handle_webhook_verification(
        hub_mode=hub_mode or "",
        hub_verify_token=hub_verify_token or "",
        hub_challenge=hub_challenge or "",
    )
    return HttpResponse(body, status=status, content_type="text/plain")


@router.post("/webhook/")
def instagram_webhook(request: HttpRequest) -> HttpResponse:
    status, body = process_webhook_request(request)
    return HttpResponse(body, status=status, content_type="text/plain")


# ---------------------------------------------------------------------------
# Disconnect
# ---------------------------------------------------------------------------

@router.delete(
    "/workspaces/{workspace_id}/instagram/{integration_account_id}",
    response={204: None, 401: ErrorResponseSchema, 403: ErrorResponseSchema, 404: ErrorResponseSchema},
    auth=[ApiKeyAuth(), django_auth],
)
def instagram_disconnect(request: HttpRequest, workspace_id: int, integration_account_id: uuid.UUID):
    workspace = _require_workspace(request, workspace_id)
    account = IntegrationAccount.objects.filter(
        id=integration_account_id,
        workspace=workspace,
        provider=IntegrationAccount.Provider.INSTAGRAM,
    ).first()
    if account is None:
        raise HttpError(404, "Instagram integration not found in this workspace.")
    try:
        disconnect_instagram_account(account)
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return 204, None
