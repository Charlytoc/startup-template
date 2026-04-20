"""Instagram Business Login API helpers, OAuth flow, webhook handling, and IntegrationAccount conventions.

Uses the new Instagram Business Login (instagram.com/oauth/authorize) introduced in 2024,
NOT the deprecated Facebook Login / facebook.com/dialog/oauth path.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest

from core.integrations.event_types import INSTAGRAM_DM_MESSAGE
from core.models import IntegrationAccount, IntegrationEvent, Workspace

# Instagram Business Login endpoints
INSTAGRAM_OAUTH_URL = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_GRAPH_BASE = "https://graph.instagram.com"

# Keys in IntegrationAccount.auth (encrypted)
AUTH_ACCESS_TOKEN = "access_token"

# Keys in IntegrationAccount.config (plaintext JSON)
CONFIG_IG_USER_ID = "ig_user_id"
CONFIG_IG_USERNAME = "ig_username"

# Redis cache key for OAuth state
_OAUTH_STATE_TTL = 600  # 10 minutes
_OAUTH_STATE_PREFIX = "ig_oauth_state:"

# Scopes for Instagram Business Login
INSTAGRAM_OAUTH_SCOPES = [
    "instagram_business_basic",
    "instagram_business_manage_messages",
]


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

def _app_id() -> str:
    return str(getattr(settings, "INSTAGRAM_APP_ID", "") or "")


def _app_secret() -> str:
    return str(getattr(settings, "INSTAGRAM_APP_SECRET", "") or "")


def _frontend_url() -> str:
    return str(getattr(settings, "FRONTEND_URL", "http://localhost:3000")).rstrip("/")


def _callback_url() -> str:
    base = str(getattr(settings, "SITE_URL", "http://127.0.0.1:8000")).rstrip("/")
    return f"{base}/api/integrations/instagram/callback/"


# ---------------------------------------------------------------------------
# OAuth state (Redis cache)
# ---------------------------------------------------------------------------

def _state_cache_key(state_token: str) -> str:
    return f"{_OAUTH_STATE_PREFIX}{state_token}"


def store_oauth_state(workspace_id: int, user_id: int) -> str:
    """Generate a random state token, store workspace/user in cache, return the token."""
    token = secrets.token_urlsafe(32)
    cache.set(_state_cache_key(token), {"workspace_id": workspace_id, "user_id": user_id}, _OAUTH_STATE_TTL)
    return token


def consume_oauth_state(state_token: str) -> dict[str, int] | None:
    """Retrieve and delete the OAuth state payload. Returns None if missing/expired."""
    key = _state_cache_key(state_token)
    payload = cache.get(key)
    if payload is None:
        return None
    cache.delete(key)
    return payload


# ---------------------------------------------------------------------------
# OAuth URL builder
# ---------------------------------------------------------------------------

def build_instagram_oauth_url(state_token: str) -> str:
    params = {
        "client_id": _app_id(),
        "redirect_uri": _callback_url(),
        "scope": ",".join(INSTAGRAM_OAUTH_SCOPES),
        "response_type": "code",
        "state": state_token,
    }
    return f"{INSTAGRAM_OAUTH_URL}?{urlencode(params)}"


# ---------------------------------------------------------------------------
# Token exchange (Instagram Business Login)
# ---------------------------------------------------------------------------

def instagram_exchange_code(code: str) -> dict[str, Any]:
    """Exchange authorization code for a short-lived Instagram user access token."""
    resp = requests.post(
        INSTAGRAM_TOKEN_URL,
        data={
            "client_id": _app_id(),
            "client_secret": _app_secret(),
            "grant_type": "authorization_code",
            "redirect_uri": _callback_url(),
            "code": code,
        },
        timeout=20,
    )
    data = resp.json()
    if "error_type" in data or "error" in data:
        msg = data.get("error_message") or data.get("error", {}).get("message") or "Code exchange failed"
        raise ValueError(msg)
    # Returns: {"access_token": "...", "token_type": "bearer", "permissions": [...], "user_id": ...}
    return data


def instagram_get_long_lived_token(short_token: str) -> dict[str, Any]:
    """Exchange a short-lived token for a long-lived Instagram user token (60 days)."""
    resp = requests.get(
        f"{INSTAGRAM_GRAPH_BASE}/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": _app_secret(),
            "access_token": short_token,
        },
        timeout=20,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"].get("message", "Long-lived token exchange failed"))
    # Returns: {"access_token": "...", "token_type": "bearer", "expires_in": 5183944}
    return data


# ---------------------------------------------------------------------------
# Graph API: user info
# ---------------------------------------------------------------------------

def instagram_get_user_info(access_token: str) -> dict[str, Any]:
    """Fetch the IG Business account id and username for the authenticated user."""
    resp = requests.get(
        f"{INSTAGRAM_GRAPH_BASE}/me",
        params={
            "fields": "id,username,name",
            "access_token": access_token,
        },
        timeout=20,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"].get("message", "Failed to fetch user info"))
    return data  # {"id": "...", "username": "...", "name": "..."}


# ---------------------------------------------------------------------------
# Graph API: send DM
# ---------------------------------------------------------------------------

def instagram_send_message(access_token: str, ig_user_id: str, recipient_igsid: str, text: str) -> dict[str, Any]:
    """Send a text DM from the IG Business Account to recipient_igsid."""
    resp = requests.post(
        f"{INSTAGRAM_GRAPH_BASE}/v21.0/{ig_user_id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "recipient": {"id": recipient_igsid},
            "message": {"text": text},
        },
        timeout=20,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"].get("message", "Instagram sendMessage failed"))
    return data


# ---------------------------------------------------------------------------
# IntegrationAccount helpers
# ---------------------------------------------------------------------------

def get_access_token(account: IntegrationAccount) -> str:
    return str((account.auth or {}).get(AUTH_ACCESS_TOKEN, "")).strip()


def get_ig_user_id(account: IntegrationAccount) -> str:
    return str((account.config or {}).get(CONFIG_IG_USER_ID, account.external_account_id)).strip()


def find_account_by_ig_user_id(ig_user_id: str) -> IntegrationAccount | None:
    return IntegrationAccount.objects.filter(
        provider=IntegrationAccount.Provider.INSTAGRAM,
        external_account_id=ig_user_id,
        status=IntegrationAccount.Status.ACTIVE,
    ).first()


# ---------------------------------------------------------------------------
# Connect / disconnect
# ---------------------------------------------------------------------------

def connect_instagram_account(
    *,
    workspace: Workspace,
    user,
    access_token: str,
    ig_user_id: str,
    ig_username: str,
) -> IntegrationAccount:
    """Create or update an IntegrationAccount for a connected Instagram Business account."""
    display_name = f"@{ig_username}" if ig_username else ig_user_id

    with transaction.atomic():
        account, _created = IntegrationAccount.objects.get_or_create(
            workspace=workspace,
            provider=IntegrationAccount.Provider.INSTAGRAM,
            external_account_id=ig_user_id,
            defaults={
                "created_by": user if getattr(user, "pk", None) else None,
                "display_name": display_name[:200],
                "status": IntegrationAccount.Status.ACTIVE,
                "config": {
                    CONFIG_IG_USER_ID: ig_user_id,
                    CONFIG_IG_USERNAME: ig_username,
                },
            },
        )
        if not _created:
            account.display_name = display_name[:200]
            account.status = IntegrationAccount.Status.ACTIVE
            cfg = dict(account.config or {})
            cfg[CONFIG_IG_USER_ID] = ig_user_id
            cfg[CONFIG_IG_USERNAME] = ig_username
            account.config = cfg

        account.auth = {AUTH_ACCESS_TOKEN: access_token}
        account.save()

        from core.services.job_assignment_defaults import ensure_default_job_assignment_for_instagram
        ensure_default_job_assignment_for_instagram(account=account, user=user)

    return account


def disconnect_instagram_account(account: IntegrationAccount) -> None:
    if account.provider != IntegrationAccount.Provider.INSTAGRAM:
        raise ValueError("not an Instagram integration")
    account.delete()


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

def verify_webhook_signature(request: HttpRequest) -> bool:
    """Validate X-Hub-Signature-256 against HMAC-SHA256(app_secret, body)."""
    secret = _app_secret()
    if not secret:
        return False
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    return secrets.compare_digest(expected, sig_header)


def handle_webhook_payload(payload: dict[str, Any]) -> None:
    """Dispatch each messaging entry to the appropriate account's event processor."""
    if payload.get("object") != "instagram":
        return

    for entry in payload.get("entry", []):
        ig_account_id = str(entry.get("id") or "")
        if not ig_account_id:
            continue

        account = find_account_by_ig_user_id(ig_account_id)
        if account is None:
            continue

        for messaging in entry.get("messaging", []):
            message = messaging.get("message")
            if not message:
                continue
            if message.get("is_echo"):
                continue

            sender_igsid = str((messaging.get("sender") or {}).get("id") or "")
            if not sender_igsid or sender_igsid == ig_account_id:
                continue

            _record_dm_event(account, messaging)

            from core.services.instagram_events_processor import process_instagram_dm
            process_instagram_dm(account=account, messaging=messaging, sender_igsid=sender_igsid)


def _record_dm_event(account: IntegrationAccount, messaging: dict[str, Any]) -> None:
    message = messaging.get("message") or {}
    external_id = str(message.get("mid") or "")
    IntegrationEvent.objects.get_or_create(
        integration_account=account,
        event_type=INSTAGRAM_DM_MESSAGE.slug,
        external_event_id=external_id[:255],
        defaults={"payload": messaging},
    )


def process_webhook_request(request: HttpRequest) -> tuple[int, str]:
    """Entry point called from the router for POST webhook events."""
    if not verify_webhook_signature(request):
        return 401, "unauthorized"

    try:
        body = request.body.decode("utf-8") if request.body else ""
        payload = json.loads(body) if body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 400, "invalid json"

    if not isinstance(payload, dict):
        return 400, "invalid payload"

    try:
        handle_webhook_payload(payload)
    except Exception:
        pass

    return 200, "ok"


def handle_webhook_verification(hub_mode: str, hub_verify_token: str, hub_challenge: str) -> tuple[int, str]:
    """Respond to Meta's GET webhook verification handshake."""
    verify_token = str(getattr(settings, "INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "") or "")
    if hub_mode == "subscribe" and secrets.compare_digest(hub_verify_token, verify_token):
        return 200, hub_challenge
    return 403, "forbidden"
