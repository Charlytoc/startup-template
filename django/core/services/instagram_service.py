"""Instagram integration via Facebook Login (Graph API).

Uses facebook.com/dialog/oauth (Facebook Login) so we can call
graph.facebook.com/me/accounts to retrieve the classic Instagram
Business Account ID (the one Meta sends in webhook entry.id).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any
from urllib.parse import urlencode

import logging

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest

from core.integrations.event_types import INSTAGRAM_DM_MESSAGE
from core.models import IntegrationAccount, IntegrationEvent, Workspace

logger = logging.getLogger(__name__)

# Facebook / Instagram Graph API endpoints
FACEBOOK_API_VERSION = "v25.0"
FACEBOOK_OAUTH_URL = f"https://www.facebook.com/{FACEBOOK_API_VERSION}/dialog/oauth"
FACEBOOK_TOKEN_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/oauth/access_token"
FACEBOOK_GRAPH_BASE = "https://graph.facebook.com"

# Keys in IntegrationAccount.auth (encrypted)
AUTH_ACCESS_TOKEN = "access_token"       # Page Access Token — used for sending messages
AUTH_FB_USER_TOKEN = "fb_user_token"     # Long-lived Facebook User Token — kept for reference

# Keys in IntegrationAccount.config (plaintext JSON)
CONFIG_IG_USER_ID = "ig_user_id"
CONFIG_IG_USERNAME = "ig_username"

# Redis cache key for OAuth state
_OAUTH_STATE_TTL = 600  # 10 minutes
_OAUTH_STATE_PREFIX = "ig_oauth_state:"

# Facebook Login scopes needed for Instagram Business messaging
INSTAGRAM_OAUTH_SCOPES = [
    "pages_show_list",
    "instagram_manage_messages",
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
    token = secrets.token_urlsafe(32)
    cache.set(_state_cache_key(token), {"workspace_id": workspace_id, "user_id": user_id}, _OAUTH_STATE_TTL)
    return token


def consume_oauth_state(state_token: str) -> dict[str, int] | None:
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
    return f"{FACEBOOK_OAUTH_URL}?{urlencode(params)}"


# ---------------------------------------------------------------------------
# Token exchange (Facebook Login)
# ---------------------------------------------------------------------------

def instagram_exchange_code(code: str) -> dict[str, Any]:
    """Exchange authorization code for a short-lived Facebook User Access Token."""
    resp = requests.get(
        FACEBOOK_TOKEN_URL,
        params={
            "client_id": _app_id(),
            "client_secret": _app_secret(),
            "redirect_uri": _callback_url(),
            "code": code,
        },
        timeout=20,
    )
    data = resp.json()
    if "error" in data:
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        raise ValueError(msg or "Code exchange failed")
    # Returns: {"access_token": "...", "token_type": "bearer"}
    return data


def instagram_get_long_lived_token(short_token: str) -> dict[str, Any]:
    """Exchange a short-lived Facebook User Token for a long-lived one (60 days)."""
    resp = requests.get(
        f"{FACEBOOK_GRAPH_BASE}/{FACEBOOK_API_VERSION}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": _app_id(),
            "client_secret": _app_secret(),
            "fb_exchange_token": short_token,
        },
        timeout=20,
    )
    data = resp.json()
    if "error" in data:
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        raise ValueError(msg or "Long-lived token exchange failed")
    # Returns: {"access_token": "...", "token_type": "bearer", "expires_in": ...}
    return data


# ---------------------------------------------------------------------------
# Graph API: fetch linked Instagram Business Account + Page Access Token
# ---------------------------------------------------------------------------

def instagram_get_account_info(fb_user_token: str) -> tuple[str, str, str]:
    """Return (classic_ig_user_id, ig_username, page_access_token).

    Calls /me/accounts on the Facebook Graph API.  Each item in data[] is a
    Facebook Page; we look for the first one with a linked instagram_business_account.
    The classic ig_user_id is what Meta sends in webhook entry.id (starts with 178…).
    page_access_token is the token used to send Instagram DMs.
    Returns ("", "", "") when no linked Instagram Business Account is found.
    """
    # Log who we're authenticated as and what permissions were granted
    try:
        me_resp = requests.get(
            f"{FACEBOOK_GRAPH_BASE}/{FACEBOOK_API_VERSION}/me",
            params={"fields": "id,name", "access_token": fb_user_token},
            timeout=20,
        )
        logger.info("instagram_get_account_info: /me=%s", me_resp.json())
    except Exception as exc:
        logger.warning("instagram_get_account_info: /me call failed: %s", exc)

    try:
        perm_resp = requests.get(
            f"{FACEBOOK_GRAPH_BASE}/{FACEBOOK_API_VERSION}/me/permissions",
            params={"access_token": fb_user_token},
            timeout=20,
        )
        logger.info("instagram_get_account_info: /me/permissions=%s", perm_resp.json())
    except Exception as exc:
        logger.warning("instagram_get_account_info: /me/permissions call failed: %s", exc)

    resp = requests.get(
        f"{FACEBOOK_GRAPH_BASE}/{FACEBOOK_API_VERSION}/me/accounts",
        params={
            "fields": "name,access_token,instagram_business_account{id,username}",
            "access_token": fb_user_token,
        },
        timeout=20,
    )
    data = resp.json()
    logger.info("instagram_get_account_info: /me/accounts response=%s", data)
    if "error" in data:
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        raise ValueError(msg or "Failed to fetch Facebook pages")

    for page in data.get("data", []):
        iba = page.get("instagram_business_account") or {}
        classic_id = str(iba.get("id") or "").strip()
        username = str(iba.get("username") or "").strip()
        page_token = str(page.get("access_token") or "").strip()
        logger.info("instagram_get_account_info: page=%r classic_id=%r username=%r has_token=%s",
                    page.get("name"), classic_id, username, bool(page_token))
        if classic_id and page_token:
            return classic_id, username, page_token

    return "", "", ""


# ---------------------------------------------------------------------------
# Graph API: send DM
# ---------------------------------------------------------------------------

def instagram_send_message(access_token: str, ig_user_id: str, recipient_igsid: str, text: str) -> dict[str, Any]:
    """Send a text DM from the IG Business Account to recipient_igsid.

    access_token must be the Page Access Token associated with the Facebook Page
    linked to this Instagram Business Account.
    """
    resp = requests.post(
        f"{FACEBOOK_GRAPH_BASE}/{FACEBOOK_API_VERSION}/{ig_user_id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "recipient": {"id": recipient_igsid},
            "message": {"text": text},
        },
        timeout=20,
    )
    data = resp.json()
    if "error" in data:
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        raise ValueError(msg or "Instagram sendMessage failed")
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
    page_access_token: str,
    fb_user_token: str,
    ig_user_id: str,
    ig_username: str,
) -> IntegrationAccount:
    """Create or update an IntegrationAccount for a connected Instagram Business account.

    ig_user_id must be the classic Instagram Business Account ID (webhooks send this in entry.id).
    page_access_token is the Facebook Page Access Token used to send messages.
    fb_user_token is the long-lived Facebook User Token, stored for potential refresh.
    """
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

        account.auth = {
            AUTH_ACCESS_TOKEN: page_access_token,
            AUTH_FB_USER_TOKEN: fb_user_token,
        }
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
    obj = payload.get("object")
    if obj != "instagram":
        logger.info("instagram_webhook: ignoring object=%r (expected 'instagram')", obj)
        return

    for entry in payload.get("entry", []):
        ig_account_id = str(entry.get("id") or "")
        logger.info("instagram_webhook: processing entry id=%r keys=%s", ig_account_id, list(entry.keys()))

        if not ig_account_id:
            logger.warning("instagram_webhook: entry has no id, skipping")
            continue

        account = find_account_by_ig_user_id(ig_account_id)
        if account is None:
            logger.warning(
                "instagram_webhook: no active IntegrationAccount found for ig_user_id=%r "
                "(check that external_account_id in DB matches this id)",
                ig_account_id,
            )
            continue

        logger.info("instagram_webhook: matched account=%s (%s)", account.id, account.display_name)

        messaging_list = entry.get("messaging", [])
        if not messaging_list:
            logger.info("instagram_webhook: entry has no 'messaging' field, keys present: %s", list(entry.keys()))

        for messaging in messaging_list:
            message = messaging.get("message")
            logger.info("instagram_webhook: messaging event sender=%r recipient=%r has_message=%s",
                        (messaging.get("sender") or {}).get("id"),
                        (messaging.get("recipient") or {}).get("id"),
                        message is not None)

            if not message:
                logger.info("instagram_webhook: no 'message' in messaging event, full event: %s", json.dumps(messaging))
                continue
            if message.get("is_echo"):
                logger.info("instagram_webhook: skipping echo message")
                continue

            sender_igsid = str((messaging.get("sender") or {}).get("id") or "")
            if not sender_igsid or sender_igsid == ig_account_id:
                logger.warning("instagram_webhook: invalid sender_igsid=%r ig_account_id=%r", sender_igsid, ig_account_id)
                continue

            logger.info("instagram_webhook: dispatching DM from sender=%s to account=%s", sender_igsid, account.id)
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
        logger.warning("instagram_webhook: signature verification failed")
        return 401, "unauthorized"

    try:
        body = request.body.decode("utf-8") if request.body else ""
        payload = json.loads(body) if body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("instagram_webhook: invalid JSON body")
        return 400, "invalid json"

    if not isinstance(payload, dict):
        logger.warning("instagram_webhook: payload is not a dict")
        return 400, "invalid payload"

    logger.info("instagram_webhook: received payload object=%r entries=%d raw=%s",
                payload.get("object"), len(payload.get("entry", [])), json.dumps(payload))

    try:
        handle_webhook_payload(payload)
    except Exception:
        logger.exception("instagram_webhook: unhandled error in handle_webhook_payload")

    return 200, "ok"


def handle_webhook_verification(hub_mode: str, hub_verify_token: str, hub_challenge: str) -> tuple[int, str]:
    """Respond to Meta's GET webhook verification handshake."""
    verify_token = str(getattr(settings, "INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "") or "")
    if hub_mode == "subscribe" and secrets.compare_digest(hub_verify_token, verify_token):
        return 200, hub_challenge
    return 403, "forbidden"
