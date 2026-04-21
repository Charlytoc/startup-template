"""Instagram integration endpoints: OAuth flow, webhook (verify + receive), disconnect."""

from __future__ import annotations

import logging
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
    instagram_get_me_accounts,
    instagram_get_user_info,
    process_webhook_request,
    store_oauth_state,
)
from core.utils.schemas import ErrorResponseSchema

logger = logging.getLogger(__name__)

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
    org = auth_service.get_active_organization(request)
    logger.info(
        "instagram_oauth_url request workspace_id=%s user_id=%s org_id=%s",
        workspace.id,
        user.pk,
        getattr(org, "id", None),
    )
    state_token = store_oauth_state(workspace_id=workspace.id, user_id=user.pk)
    url = build_instagram_oauth_url(state_token)
    logger.info(
        "instagram_oauth_url response workspace_id=%s user_id=%s oauth_url_len=%s",
        workspace.id,
        user.pk,
        len(url),
    )
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
    logger.info(
        "instagram_callback hit path=%s has_code=%s has_state=%s meta_error=%s code_len=%s state_prefix=%s",
        request.path,
        bool(params.code),
        bool(params.state),
        params.error,
        len(params.code) if params.code else 0,
        (params.state[:10] + "…") if params.state else None,
    )

    if params.error or not params.code or not params.state:
        reason = params.error_description or params.error or "missing_code"
        logger.warning(
            "instagram_callback early_redirect reason=%s frontend_connect_integration meta_error=%s",
            reason,
            params.error,
        )
        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/connect-integration?instagram_error={reason}"},
        )

    state_payload = consume_oauth_state(params.state)
    if state_payload is None:
        logger.warning("instagram_callback early_redirect reason=invalid_state")
        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/connect-integration?instagram_error=invalid_state"},
        )

    workspace_id: int = state_payload["workspace_id"]
    user_id: int = state_payload["user_id"]
    logger.info(
        "instagram_callback state_ok workspace_id=%s user_id=%s",
        workspace_id,
        user_id,
    )

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        workspace = Workspace.objects.get(id=workspace_id)
        logger.info(
            "instagram_callback loaded_user_workspace user_id=%s workspace_id=%s org_id=%s",
            user.pk,
            workspace.id,
            getattr(workspace, "organization_id", None),
        )

        short = instagram_exchange_code(params.code)
        long_lived = instagram_get_long_lived_token(short["access_token"])
        token = long_lived["access_token"]
        user_info = instagram_get_user_info(token)
        me_accounts = instagram_get_me_accounts(token)

        me_graph = str(user_info.get("id") or "").strip()
        professional = str(user_info.get("user_id") or "").strip()
        from_short = str(short.get("user_id") or "").strip()
        ig_user_id = professional or me_graph or from_short
        ig_oauth_graph_me_id = me_graph if me_graph and me_graph != ig_user_id else None
        ig_username = str(user_info.get("username") or "")
        logger.info(
            "instagram_callback resolved_ig external_account_id=%s ig_username=%s "
            "from_me_user_id=%s from_me_graph_id=%s from_short_user_id=%s",
            ig_user_id or "(empty)",
            ig_username or "(empty)",
            user_info.get("user_id"),
            user_info.get("id"),
            short.get("user_id"),
        )

        if not ig_user_id:
            logger.warning(
                "instagram_callback early_redirect reason=no_ig_accounts workspace_id=%s user_id=%s",
                workspace_id,
                user_id,
            )
            return HttpResponse(
                status=302,
                headers={"Location": f"{frontend}/workspaces/{workspace_id}/integrations?instagram_error=no_ig_accounts"},
            )

        account = connect_instagram_account(
            workspace=workspace,
            user=user,
            access_token=token,
            ig_user_id=ig_user_id,
            ig_username=ig_username,
            me_accounts_payload=me_accounts,
            ig_oauth_graph_me_id=ig_oauth_graph_me_id,
        )

        logger.info(
            "instagram_callback success_redirect workspace_id=%s integration_account_id=%s",
            workspace_id,
            account.id,
        )
        return HttpResponse(
            status=302,
            headers={"Location": f"{frontend}/workspaces/{workspace_id}/integrations?instagram_connected=true&account_ids={account.id}"},
        )

    except Exception:
        logger.exception(
            "instagram_callback failed workspace_id=%s user_id=%s",
            workspace_id,
            user_id,
        )
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
    logger.info(
        "instagram_webhook POST route hit path=%s content_type=%s",
        request.path,
        request.headers.get("Content-Type", ""),
    )
    status, body = process_webhook_request(request)
    logger.info("instagram_webhook POST done status=%s body=%r", status, body)
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
    user = auth_service.get_user_from_request(request)
    account = IntegrationAccount.objects.filter(
        id=integration_account_id,
        workspace=workspace,
        provider=IntegrationAccount.Provider.INSTAGRAM,
    ).first()
    if account is None:
        logger.warning(
            "instagram_disconnect not_found workspace_id=%s integration_account_id=%s user_id=%s",
            workspace_id,
            integration_account_id,
            getattr(user, "pk", None),
        )
        raise HttpError(404, "Instagram integration not found in this workspace.")
    logger.info(
        "instagram_disconnect request workspace_id=%s integration_account_id=%s user_id=%s external_account_id=%s",
        workspace_id,
        integration_account_id,
        getattr(user, "pk", None),
        account.external_account_id,
    )
    try:
        disconnect_instagram_account(account)
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return 204, None
