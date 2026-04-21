"""Instagram Business Login API helpers, OAuth flow, webhook handling, and IntegrationAccount conventions.

Uses the new Instagram Business Login (instagram.com/oauth/authorize) introduced in 2024,
NOT the deprecated Facebook Login / facebook.com/dialog/oauth path.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
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

logger = logging.getLogger(__name__)

# Instagram Business Login endpoints
INSTAGRAM_OAUTH_URL = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_GRAPH_BASE = "https://graph.instagram.com"
INSTAGRAM_GRAPH_API_VERSION = "v21.0"

# Keys in IntegrationAccount.auth (encrypted)
AUTH_ACCESS_TOKEN = "access_token"

# Keys in IntegrationAccount.config (plaintext JSON)
CONFIG_IG_USER_ID = "ig_user_id"
CONFIG_IG_USERNAME = "ig_username"
CONFIG_IG_OAUTH_GRAPH_ME_ID = "ig_oauth_graph_me_id"
CONFIG_ME_ACCOUNTS_SNAPSHOT = "me_accounts_snapshot"

# Redis cache key for OAuth state
_OAUTH_STATE_TTL = 600  # 10 minutes
_OAUTH_STATE_PREFIX = "ig_oauth_state:"

# Scopes for Instagram Business Login
INSTAGRAM_OAUTH_SCOPES = [
    "instagram_business_basic",
    "instagram_business_manage_messages"
]


def _oauth_response_for_log(data: dict[str, Any]) -> dict[str, Any]:
    """Omit secrets from token endpoint JSON for logging."""
    out: dict[str, Any] = {}
    for key, val in data.items():
        if key == "access_token":
            s = str(val) if val is not None else ""
            out[key] = f"<set len={len(s)}>" if s else "<empty>"
        else:
            out[key] = val
    return out


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
    logger.info(
        "instagram_oauth_state stored workspace_id=%s user_id=%s state_prefix=%s ttl_s=%s",
        workspace_id,
        user_id,
        token[:10] + "…",
        _OAUTH_STATE_TTL,
    )
    return token


def consume_oauth_state(state_token: str) -> dict[str, int] | None:
    """Retrieve and delete the OAuth state payload. Returns None if missing/expired."""
    key = _state_cache_key(state_token)
    payload = cache.get(key)
    if payload is None:
        logger.warning(
            "instagram_oauth_state consume miss state_prefix=%s",
            (state_token[:10] + "…") if state_token else "(empty)",
        )
        return None
    cache.delete(key)
    logger.info(
        "instagram_oauth_state consumed workspace_id=%s user_id=%s state_prefix=%s",
        payload.get("workspace_id"),
        payload.get("user_id"),
        (state_token[:10] + "…") if state_token else "(empty)",
    )
    return payload


# ---------------------------------------------------------------------------
# OAuth URL builder
# ---------------------------------------------------------------------------

def build_instagram_oauth_url(state_token: str) -> str:
    redirect_uri = _callback_url()
    app_id = _app_id()
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": ",".join(INSTAGRAM_OAUTH_SCOPES),
        "response_type": "code",
        "state": state_token,
    }
    logger.info(
        "instagram_oauth_url built authorize_host=%s redirect_uri=%s app_id_configured=%s "
        "app_secret_configured=%s scopes=%s state_prefix=%s",
        INSTAGRAM_OAUTH_URL,
        redirect_uri,
        bool(app_id),
        bool(_app_secret()),
        INSTAGRAM_OAUTH_SCOPES,
        (state_token[:10] + "…") if state_token else "(empty)",
    )
    return f"{INSTAGRAM_OAUTH_URL}?{urlencode(params)}"


# ---------------------------------------------------------------------------
# Token exchange (Instagram Business Login)
# ---------------------------------------------------------------------------

def instagram_exchange_code(code: str) -> dict[str, Any]:
    """Exchange authorization code for a short-lived Instagram user access token."""
    logger.info(
        "instagram_exchange_code start url=%s code_len=%s redirect_uri=%s",
        INSTAGRAM_TOKEN_URL,
        len(code) if code else 0,
        _callback_url(),
    )
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
    logger.info(
        "instagram_exchange_code http_status=%s response_keys=%s",
        resp.status_code,
        list(data.keys()) if isinstance(data, dict) else type(data).__name__,
    )
    if "error_type" in data or "error" in data:
        msg = data.get("error_message") or data.get("error", {}).get("message") or "Code exchange failed"
        logger.warning("instagram_exchange_code error payload=%s", _oauth_response_for_log(data) if isinstance(data, dict) else data)
        raise ValueError(msg)
    logger.info("instagram_exchange_code ok summary=%s", _oauth_response_for_log(data))
    return data


def instagram_get_long_lived_token(short_token: str) -> dict[str, Any]:
    """Exchange a short-lived token for a long-lived Instagram user token (60 days)."""
    url = f"{INSTAGRAM_GRAPH_BASE}/access_token"
    logger.info(
        "instagram_get_long_lived_token start url=%s short_token_len=%s",
        url,
        len(short_token) if short_token else 0,
    )
    resp = requests.get(
        url,
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": _app_secret(),
            "access_token": short_token,
        },
        timeout=20,
    )
    data = resp.json()
    logger.info(
        "instagram_get_long_lived_token http_status=%s response_keys=%s",
        resp.status_code,
        list(data.keys()) if isinstance(data, dict) else type(data).__name__,
    )
    if "error" in data:
        logger.warning("instagram_get_long_lived_token error=%s", data.get("error"))
        raise ValueError(data["error"].get("message", "Long-lived token exchange failed"))
    safe = _oauth_response_for_log(data) if isinstance(data, dict) else data
    logger.info("instagram_get_long_lived_token ok summary=%s", safe)
    return data


# ---------------------------------------------------------------------------
# Graph API: user info
# ---------------------------------------------------------------------------

def instagram_get_user_info(access_token: str) -> dict[str, Any]:
    """Fetch IG profile fields for the authenticated user.

    ``user_id`` (when present) is the Instagram professional account id used in webhooks
    (``entry.id``); ``id`` can differ and historically matched only parts of the Graph API.
    """
    url = f"{INSTAGRAM_GRAPH_BASE}/me"
    me_fields = "id,username,name,user_id,account_type"
    logger.info(
        "instagram_get_user_info start url=%s fields=%s token_len=%s",
        url,
        me_fields,
        len(access_token) if access_token else 0,
    )
    resp = requests.get(
        url,
        params={
            "fields": me_fields,
            "access_token": access_token,
        },
        timeout=20,
    )
    data = resp.json()
    logger.info(
        "instagram_get_user_info http_status=%s response_keys=%s",
        resp.status_code,
        list(data.keys()) if isinstance(data, dict) else type(data).__name__,
    )
    if "error" in data:
        logger.warning("instagram_get_user_info error=%s", data.get("error"))
        raise ValueError(data["error"].get("message", "Failed to fetch user info"))
    logger.info(
        "instagram_get_user_info ok id=%s user_id=%s username=%s account_type=%s name_present=%s",
        data.get("id"),
        data.get("user_id"),
        data.get("username"),
        data.get("account_type"),
        bool(data.get("name")),
    )
    return data


def instagram_get_me_accounts(access_token: str) -> dict[str, Any]:
    """Call ``GET /{version}/me/accounts`` on the Instagram Graph host (same as ``/me``).

    Shape is often Facebook Page–like objects with an ``instagram_business_account`` child.
    For some Instagram user tokens this edge returns an error or an empty ``data`` list;
    callers should treat failures as non-fatal.
    """
    url = f"{INSTAGRAM_GRAPH_BASE}/{INSTAGRAM_GRAPH_API_VERSION}/me/accounts"
    params = {
        "access_token": access_token,
        "fields": "id,name,username,instagram_business_account{id,username,name}",
    }
    logger.info(
        "instagram_get_me_accounts start url=%s token_len=%s",
        url,
        len(access_token) if access_token else 0,
    )
    resp = requests.get(url, params=params, timeout=20)
    try:
        data = resp.json()
    except ValueError:
        logger.warning(
            "instagram_get_me_accounts invalid_json http_status=%s body_prefix=%s",
            resp.status_code,
            (resp.text[:200] + "…") if len(resp.text) > 200 else resp.text,
        )
        return {"data": [], "paging": {}}

    if not isinstance(data, dict):
        logger.warning(
            "instagram_get_me_accounts unexpected_payload_type=%s",
            type(data).__name__,
        )
        return {"data": [], "paging": {}}

    logger.info(
        "instagram_get_me_accounts http_status=%s response_keys=%s",
        resp.status_code,
        list(data.keys()),
    )
    if "error" in data:
        logger.warning("instagram_get_me_accounts error=%s", data.get("error"))
        return {"data": [], "paging": {}, "_http_status": resp.status_code, "_error": data.get("error")}

    rows = data.get("data")
    if not isinstance(rows, list):
        rows = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        iba = row.get("instagram_business_account")
        logger.info(
            "instagram_get_me_accounts row i=%s id=%s name=%s username=%s iba_id=%s iba_username=%s",
            i,
            row.get("id"),
            row.get("name"),
            row.get("username"),
            (iba or {}).get("id") if isinstance(iba, dict) else None,
            (iba or {}).get("username") if isinstance(iba, dict) else None,
        )
    logger.info(
        "instagram_get_me_accounts ok data_count=%s has_paging=%s",
        len(rows),
        bool(data.get("paging")),
    )
    return data


def me_accounts_snapshot_for_config(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Strip tokens and other secrets; safe to persist on ``IntegrationAccount.config``."""
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item: dict[str, Any] = {}
        for k in ("id", "name", "category", "username"):
            if row.get(k) is not None:
                item[k] = row[k]
        iba = row.get("instagram_business_account")
        if isinstance(iba, dict):
            item["instagram_business_account"] = {
                kk: iba[kk]
                for kk in ("id", "username", "name")
                if iba.get(kk) is not None
            }
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Graph API: send DM
# ---------------------------------------------------------------------------

def instagram_send_message(access_token: str, ig_user_id: str, recipient_igsid: str, text: str) -> dict[str, Any]:
    """Send a text DM from the IG Business Account to recipient_igsid."""
    resp = requests.post(
        f"{INSTAGRAM_GRAPH_BASE}/{INSTAGRAM_GRAPH_API_VERSION}/{ig_user_id}/messages",
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


def instagram_list_me_conversations(*, access_token: str, limit: int = 40) -> list[dict[str, Any]]:
    """List DM threads for the connected Instagram user (Instagram Login + Conversations API)."""
    if not access_token:
        return []
    url = f"{INSTAGRAM_GRAPH_BASE}/{INSTAGRAM_GRAPH_API_VERSION}/me/conversations"
    resp = requests.get(
        url,
        params={"platform": "instagram", "limit": limit, "access_token": access_token},
        timeout=30,
    )
    try:
        data = resp.json()
    except ValueError:
        logger.warning(
            "instagram_list_me_conversations invalid_json http_status=%s body_prefix=%r",
            resp.status_code,
            (resp.text or "")[:2000],
        )
        return []
    if not isinstance(data, dict) or "error" in data:
        logger.warning(
            "instagram_list_me_conversations failed http_status=%s body=%s",
            resp.status_code,
            json.dumps(data, default=str)[:4000] if isinstance(data, dict) else repr(data)[:2000],
        )
        return []
    rows = data.get("data")
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict)]


def _instagram_conversation_messages_payload(
    *, access_token: str, conversation_id: str
) -> dict[str, Any] | None:
    """GET ``/{conversation_id}?fields=messages…`` per Meta Conversations API."""
    if not access_token or not conversation_id:
        return None
    url = f"{INSTAGRAM_GRAPH_BASE}/{INSTAGRAM_GRAPH_API_VERSION}/{conversation_id}"
    field_variants = (
        "messages.limit(25){id,created_time,from,to,message}",
        "messages",
    )
    for fields in field_variants:
        resp = requests.get(
            url,
            params={"fields": fields, "access_token": access_token},
            timeout=30,
        )
        try:
            data = resp.json()
        except ValueError:
            logger.warning(
                "_instagram_conversation_messages_payload invalid_json conv_prefix=%s http_status=%s",
                conversation_id[:24],
                resp.status_code,
            )
            return None
        if not isinstance(data, dict):
            return None
        if "error" in data:
            err = data.get("error")
            if fields != field_variants[-1]:
                logger.debug(
                    "_instagram_conversation_messages_payload fields_retry conv_prefix=%s err=%s",
                    conversation_id[:24],
                    json.dumps(err, default=str)[:1500],
                )
                continue
            logger.debug(
                "_instagram_conversation_messages_payload graph_error conv_prefix=%s err=%s",
                conversation_id[:24],
                json.dumps(err, default=str)[:2000],
            )
            return None
        return data
    return None


def instagram_find_dm_message_by_mid(
    *,
    access_token: str,
    mid: str,
    max_conversations: int = 35,
) -> dict[str, Any] | None:
    """Locate webhook ``mid`` inside recent conversations (root ``GET /{mid}`` is empty on graph.instagram)."""
    convs = instagram_list_me_conversations(access_token=access_token, limit=max_conversations + 5)
    if not convs:
        logger.info("instagram_find_dm_message_by_mid no_conversations mid_prefix=%s", mid[:48])
        return None
    for conv in convs[:max_conversations]:
        cid = str(conv.get("id") or "").strip()
        if not cid:
            continue
        payload = _instagram_conversation_messages_payload(access_token=access_token, conversation_id=cid)
        if not payload:
            continue
        messages_obj = payload.get("messages")
        if not isinstance(messages_obj, dict):
            continue
        msg_rows = messages_obj.get("data")
        if not isinstance(msg_rows, list):
            continue
        for row in msg_rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("id") or "").strip() != mid:
                continue
            return row
    logger.info(
        "instagram_find_dm_message_by_mid not_found mid_prefix=%s scanned_conversations=%s",
        mid[:48],
        min(len(convs), max_conversations),
    )
    return None


def instagram_enrich_messaging_with_graph(
    *,
    account: IntegrationAccount,
    messaging: dict[str, Any],
) -> dict[str, Any]:
    """Fill sparse webhook ``messaging`` by resolving ``mid`` via Conversations API (not root ``GET /{mid}``)."""
    out = dict(messaging)
    mid: str | None = None
    msg = out.get("message")
    if isinstance(msg, dict):
        mid = str(msg.get("mid") or "").strip() or None
    if not mid:
        edit = out.get("message_edit")
        if isinstance(edit, dict):
            mid = str(edit.get("mid") or "").strip() or None
    if not mid:
        return out

    token = get_access_token(account)
    if not token:
        logger.warning("instagram_enrich_messaging_with_graph no_token account=%s", account.id)
        return out

    details = instagram_find_dm_message_by_mid(access_token=token, mid=mid)
    if not details:
        logger.info(
            "instagram_enrich_messaging_with_graph no_match mid_prefix=%s messaging_before=%s",
            mid[:48],
            json.dumps(out, default=str)[:8000],
        )
        return out

    logger.info(
        "instagram_enrich_messaging_with_graph resolved mid_prefix=%s keys=%s",
        mid[:48],
        list(details.keys()),
    )

    frm = details.get("from")
    if isinstance(frm, dict) and frm.get("id"):
        out["sender"] = {"id": str(frm["id"])}

    msg_out = out.get("message")
    if not isinstance(msg_out, dict):
        msg_out = {}
    else:
        msg_out = dict(msg_out)
    graph_message = details.get("message")
    if isinstance(graph_message, str) and graph_message.strip():
        msg_out["text"] = graph_message
    elif isinstance(graph_message, dict):
        t = graph_message.get("text")
        if isinstance(t, str) and t.strip():
            msg_out["text"] = t
    msg_out.setdefault("mid", mid)
    out["message"] = msg_out

    merged_dump = json.dumps(out, default=str)
    logger.info(
        "instagram_enrich_messaging_with_graph merged_messaging len=%s value=%s",
        len(merged_dump),
        merged_dump[:12000],
    )
    return out


# ---------------------------------------------------------------------------
# Graph API: Webhook field subscriptions (subscribed_apps)
# ---------------------------------------------------------------------------
# https://developers.facebook.com/docs/instagram-platform/webhooks


def _instagram_webhook_subscribed_fields_csv() -> str:
    raw = getattr(settings, "INSTAGRAM_WEBHOOK_SUBSCRIBED_FIELDS", "messages")
    if isinstance(raw, (list, tuple)):
        parts = [str(x).strip() for x in raw if str(x).strip()]
        return ",".join(parts) if parts else "messages"
    s = str(raw).strip()
    return s if s else "messages"


def instagram_enable_webhook_subscriptions(*, access_token: str, ig_user_id: str) -> dict[str, Any]:
    """Enable Meta→app webhook delivery for this Instagram professional account.

    Per Meta: ``POST https://graph.instagram.com/{{version}}/{{instagram-account-id}}/subscribed_apps``
    with ``subscribed_fields`` and the Instagram User access token.
    """
    uid = str(ig_user_id or "").strip()
    if not access_token or not uid:
        return {"success": False, "error": "missing_token_or_ig_user_id"}
    fields = _instagram_webhook_subscribed_fields_csv()
    url = f"{INSTAGRAM_GRAPH_BASE}/{INSTAGRAM_GRAPH_API_VERSION}/{uid}/subscribed_apps"
    logger.info(
        "instagram_enable_webhook_subscriptions POST url_suffix=%s/subscribed_apps fields=%s token_len=%s",
        uid,
        fields,
        len(access_token),
    )
    resp = requests.post(
        url,
        params={"subscribed_fields": fields, "access_token": access_token},
        timeout=30,
    )
    raw_text = resp.text or ""
    try:
        data = resp.json()
    except ValueError:
        logger.warning(
            "instagram_enable_webhook_subscriptions invalid_json http_status=%s body_prefix=%r",
            resp.status_code,
            raw_text[:2000],
        )
        return {"success": False, "http_status": resp.status_code, "error": "invalid_json"}
    if not isinstance(data, dict):
        return {"success": False, "http_status": resp.status_code, "error": "non_object_response"}
    if "error" in data:
        logger.warning(
            "instagram_enable_webhook_subscriptions graph_error http_status=%s err=%s",
            resp.status_code,
            json.dumps(data.get("error"), default=str)[:4000],
        )
        return {"success": False, "http_status": resp.status_code, "error": data.get("error")}
    if data.get("success") is True:
        logger.info("instagram_enable_webhook_subscriptions ok http_status=%s", resp.status_code)
        return {"success": True, "http_status": resp.status_code, "data": data}
    ok = 200 <= resp.status_code < 300
    if ok:
        logger.info(
            "instagram_enable_webhook_subscriptions ok_no_success_flag http_status=%s body=%s",
            resp.status_code,
            json.dumps(data, default=str)[:2000],
        )
    else:
        logger.warning(
            "instagram_enable_webhook_subscriptions unexpected http_status=%s body=%s",
            resp.status_code,
            json.dumps(data, default=str)[:2000],
        )
    return {"success": ok, "http_status": resp.status_code, "data": data}


def instagram_disable_webhook_subscriptions(*, access_token: str, ig_user_id: str) -> dict[str, Any]:
    """Remove this app's webhook subscription for the IG account (best-effort; same path as POST)."""
    uid = str(ig_user_id or "").strip()
    if not access_token or not uid:
        return {"success": False, "error": "missing_token_or_ig_user_id"}
    url = f"{INSTAGRAM_GRAPH_BASE}/{INSTAGRAM_GRAPH_API_VERSION}/{uid}/subscribed_apps"
    logger.info(
        "instagram_disable_webhook_subscriptions DELETE url_suffix=%s/subscribed_apps token_len=%s",
        uid,
        len(access_token),
    )
    resp = requests.delete(url, params={"access_token": access_token}, timeout=30)
    try:
        data = resp.json()
    except ValueError:
        logger.warning(
            "instagram_disable_webhook_subscriptions invalid_json http_status=%s body_prefix=%r",
            resp.status_code,
            (resp.text or "")[:2000],
        )
        return {"success": False, "http_status": resp.status_code, "error": "invalid_json"}
    if isinstance(data, dict) and "error" in data:
        logger.warning(
            "instagram_disable_webhook_subscriptions graph_error http_status=%s err=%s",
            resp.status_code,
            json.dumps(data.get("error"), default=str)[:4000],
        )
        return {"success": False, "http_status": resp.status_code, "error": data.get("error")}
    if isinstance(data, dict) and data.get("success") is True:
        logger.info("instagram_disable_webhook_subscriptions ok http_status=%s", resp.status_code)
        return {"success": True, "http_status": resp.status_code, "data": data}
    ok = 200 <= resp.status_code < 300
    logger.info(
        "instagram_disable_webhook_subscriptions done http_status=%s success_guess=%s body=%s",
        resp.status_code,
        ok,
        json.dumps(data, default=str)[:2000] if isinstance(data, dict) else repr(data)[:500],
    )
    return {"success": ok, "http_status": resp.status_code, "data": data if isinstance(data, dict) else {}}


# ---------------------------------------------------------------------------
# IntegrationAccount helpers
# ---------------------------------------------------------------------------

def get_access_token(account: IntegrationAccount) -> str:
    return str((account.auth or {}).get(AUTH_ACCESS_TOKEN, "")).strip()


def get_ig_user_id(account: IntegrationAccount) -> str:
    return str((account.config or {}).get(CONFIG_IG_USER_ID, account.external_account_id)).strip()


def find_account_by_ig_user_id(ig_user_id: str) -> IntegrationAccount | None:
    """Match webhook ``entry.id`` (professional id) to a connected account.

    Older rows stored only ``/me`` ``id`` on ``external_account_id``; webhooks use
    ``/me`` ``user_id``. We also match ``config.ig_oauth_graph_me_id`` for those rows
    when the webhook sends the graph ``id`` instead (rare).
    """
    if not ig_user_id:
        return None
    base = IntegrationAccount.objects.filter(
        provider=IntegrationAccount.Provider.INSTAGRAM,
        status=IntegrationAccount.Status.ACTIVE,
    )
    acc = base.filter(external_account_id=ig_user_id).first()
    if acc is not None:
        return acc
    return base.filter(config__ig_oauth_graph_me_id=ig_user_id).first()


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
    me_accounts_payload: dict[str, Any] | None = None,
    ig_oauth_graph_me_id: str | None = None,
) -> IntegrationAccount:
    """Create or update an IntegrationAccount for a connected Instagram Business account."""
    uid = getattr(user, "pk", None)
    logger.info(
        "connect_instagram_account begin workspace_id=%s user_id=%s ig_user_id=%s ig_username=%s "
        "access_token_len=%s",
        workspace.id,
        uid,
        ig_user_id,
        ig_username,
        len(access_token) if access_token else 0,
    )
    display_name = f"@{ig_username}" if ig_username else ig_user_id
    me_accounts_snapshot = me_accounts_snapshot_for_config(me_accounts_payload or {})
    logger.info(
        "connect_instagram_account me_accounts_snapshot_count=%s",
        len(me_accounts_snapshot),
    )

    def _ig_config() -> dict[str, Any]:
        cfg: dict[str, Any] = {
            CONFIG_IG_USER_ID: ig_user_id,
            CONFIG_IG_USERNAME: ig_username,
            CONFIG_ME_ACCOUNTS_SNAPSHOT: me_accounts_snapshot,
        }
        if ig_oauth_graph_me_id and ig_oauth_graph_me_id != ig_user_id:
            cfg[CONFIG_IG_OAUTH_GRAPH_ME_ID] = ig_oauth_graph_me_id
        return cfg

    with transaction.atomic():
        account, _created = IntegrationAccount.objects.get_or_create(
            workspace=workspace,
            provider=IntegrationAccount.Provider.INSTAGRAM,
            external_account_id=ig_user_id,
            defaults={
                "created_by": user if getattr(user, "pk", None) else None,
                "display_name": display_name[:200],
                "status": IntegrationAccount.Status.ACTIVE,
                "config": _ig_config(),
            },
        )
        if not _created:
            account.display_name = display_name[:200]
            account.status = IntegrationAccount.Status.ACTIVE
            cfg = dict(account.config or {})
            cfg[CONFIG_IG_USER_ID] = ig_user_id
            cfg[CONFIG_IG_USERNAME] = ig_username
            cfg[CONFIG_ME_ACCOUNTS_SNAPSHOT] = me_accounts_snapshot
            if ig_oauth_graph_me_id and ig_oauth_graph_me_id != ig_user_id:
                cfg[CONFIG_IG_OAUTH_GRAPH_ME_ID] = ig_oauth_graph_me_id
            elif CONFIG_IG_OAUTH_GRAPH_ME_ID in cfg and (
                not ig_oauth_graph_me_id or ig_oauth_graph_me_id == ig_user_id
            ):
                cfg.pop(CONFIG_IG_OAUTH_GRAPH_ME_ID, None)
            account.config = cfg

        account.auth = {AUTH_ACCESS_TOKEN: access_token}
        account.save()

        from core.services.job_assignment_defaults import ensure_default_job_assignment_for_instagram
        default_job = ensure_default_job_assignment_for_instagram(account=account, user=user)
        logger.info(
            "connect_instagram_account default_job_assignment job_id=%s",
            getattr(default_job, "id", None),
        )

    logger.info(
        "connect_instagram_account done integration_account_id=%s workspace_id=%s "
        "created_row=%s external_account_id=%s display_name=%s status=%s",
        account.id,
        workspace.id,
        _created,
        account.external_account_id,
        account.display_name,
        account.status,
    )

    sub = instagram_enable_webhook_subscriptions(access_token=access_token, ig_user_id=ig_user_id)
    if not sub.get("success"):
        logger.warning(
            "connect_instagram_account subscribed_apps_failed integration_account_id=%s "
            "external_account_id=%s detail=%s",
            account.id,
            ig_user_id,
            json.dumps(sub, default=str)[:4000],
        )
    else:
        logger.info(
            "connect_instagram_account subscribed_apps_ok integration_account_id=%s external_account_id=%s",
            account.id,
            ig_user_id,
        )

    return account


def disconnect_instagram_account(account: IntegrationAccount) -> None:
    if account.provider != IntegrationAccount.Provider.INSTAGRAM:
        raise ValueError("not an Instagram integration")
    logger.info(
        "disconnect_instagram_account integration_account_id=%s workspace_id=%s external_account_id=%s",
        account.id,
        account.workspace_id,
        account.external_account_id,
    )
    token = get_access_token(account)
    ig_uid = str(account.external_account_id or "").strip() or get_ig_user_id(account)
    if token and ig_uid:
        unsub = instagram_disable_webhook_subscriptions(access_token=token, ig_user_id=ig_uid)
        if not unsub.get("success"):
            logger.warning(
                "disconnect_instagram_account subscribed_apps_delete_failed integration_account_id=%s detail=%s",
                account.id,
                json.dumps(unsub, default=str)[:4000],
            )
    account.delete()


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

def verify_webhook_signature(request: HttpRequest) -> bool:
    """Validate X-Hub-Signature-256 against HMAC-SHA256(app_secret, body)."""
    secret = _app_secret()
    if not secret:
        logger.warning("instagram_webhook_signature skip app_secret not configured")
        return False
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header:
        logger.warning("instagram_webhook_signature fail missing X-Hub-Signature-256 header")
        return False
    if not sig_header.startswith("sha256="):
        logger.warning(
            "instagram_webhook_signature fail bad header format has_prefix=%s",
            sig_header[:16],
        )
        return False
    expected = "sha256=" + hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    ok = secrets.compare_digest(expected, sig_header)
    if not ok:
        logger.warning(
            "instagram_webhook_signature fail mismatch body_len=%s",
            len(request.body or b""),
        )
    else:
        logger.info(
            "instagram_webhook_signature ok body_len=%s",
            len(request.body or b""),
        )
    return ok


def _instagram_webhook_messaging_needs_dm_worker(messaging: dict[str, Any]) -> bool:
    """True only for payloads that can represent user text (skip read/delivery-only webhooks)."""
    if messaging.get("message"):
        return True
    edit = messaging.get("message_edit")
    return bool(isinstance(edit, dict) and str(edit.get("mid") or "").strip())


def _normalize_instagram_messaging_for_dm(messaging: dict[str, Any]) -> dict[str, Any] | None:
    """Return ``messaging`` with a ``message`` object, synthesizing one from ``message_edit`` when needed.

    Instagram can deliver edits as ``message_edit`` without a parallel ``message`` webhook; see
    https://developers.facebook.com/docs/instagram-platform/webhooks/examples/
    """
    if not isinstance(messaging, dict):
        return None
    if messaging.get("message"):
        return messaging
    edit = messaging.get("message_edit")
    if not isinstance(edit, dict):
        return None
    mid = str(edit.get("mid") or "").strip()
    if not mid:
        return None
    merged = dict(messaging)
    merged["message"] = {
        "mid": mid,
        "text": str(edit.get("text") or ""),
        "is_edit": True,
        "num_edit": edit.get("num_edit"),
    }
    logger.info(
        "instagram_webhook_payload normalized message_edit mid=%s num_edit=%s text_len=%s",
        mid,
        edit.get("num_edit"),
        len(str(edit.get("text") or "")),
    )
    return merged


def _instagram_sender_from_stored_mid(*, account: IntegrationAccount, mid: str) -> str | None:
    """Recover the DM peer IGSID using a prior user ``Message`` or ``IntegrationEvent`` with the same ``mid``."""
    from core.models.conversation import Conversation
    from core.models.message import Message

    msg = (
        Message.objects.filter(
            conversation__integration_account_id=account.id,
            conversation__origin=Conversation.Origin.INTEGRATION,
            role=Message.Role.USER,
            content_structured__instagram_message__message__mid=mid,
        )
        .select_related("conversation")
        .order_by("-created")
        .first()
    )
    if msg is not None and msg.conversation_id is not None:
        try:
            tid = (msg.conversation.get_config().external_thread_id or "").strip()
        except Exception:
            tid = ""
        if tid:
            return tid

    ev = (
        IntegrationEvent.objects.filter(
            integration_account=account,
            event_type=INSTAGRAM_DM_MESSAGE.slug,
            payload__message__mid=mid,
        )
        .order_by("-received_at")
        .first()
    )
    if ev is not None and isinstance(ev.payload, dict):
        sid = str((ev.payload.get("sender") or {}).get("id") or "").strip()
        ext = str(account.external_account_id or "").strip()
        if sid and sid != ext:
            return sid
    return None


def _instagram_sender_from_single_active_thread(*, account: IntegrationAccount) -> str | None:
    """If exactly one active integration thread exists, use its external thread id as the peer."""
    from core.models.conversation import Conversation

    convs = list(
        Conversation.objects.filter(
            integration_account_id=account.id,
            origin=Conversation.Origin.INTEGRATION,
            status=Conversation.Status.ACTIVE,
        )[:2]
    )
    if len(convs) != 1:
        return None
    try:
        tid = (convs[0].get_config().external_thread_id or "").strip()
    except Exception:
        tid = ""
    return tid or None


def _resolve_instagram_dm_sender_igsid(
    *,
    account: IntegrationAccount,
    messaging: dict[str, Any],
    ig_account_id: str,
    message: dict[str, Any],
) -> str:
    """Instagram-scoped id of the human in the thread (not the professional inbox id)."""
    biz = str(ig_account_id or "").strip()

    def _peer(x: str) -> bool:
        return bool(x) and x != biz

    sender = str((messaging.get("sender") or {}).get("id") or "").strip()
    # Outbound / echo: Meta sets sender to the professional inbox id and recipient to the human.
    # Never treat recipient as the "inbound user" in that case (it caused reply→webhook→reply loops).
    if sender == biz:
        return ""

    if _peer(sender):
        return sender

    recipient = str((messaging.get("recipient") or {}).get("id") or "").strip()
    if not sender and _peer(recipient):
        return recipient

    mid = str(message.get("mid") or "").strip()
    if mid and message.get("is_edit"):
        recovered = _instagram_sender_from_stored_mid(account=account, mid=mid)
        if recovered and _peer(recovered):
            logger.info(
                "instagram_webhook_payload sender_recovered_from_mid mid_prefix=%s sender=%s",
                mid[:24],
                recovered,
            )
            return recovered
        single = _instagram_sender_from_single_active_thread(account=account)
        if single and _peer(single):
            logger.info(
                "instagram_webhook_payload sender_recovered_single_active_thread sender=%s",
                single,
            )
            return single

    return ""


def process_instagram_webhook_messaging(
    *,
    account: IntegrationAccount,
    ig_account_id: str,
    raw_messaging: dict[str, Any],
) -> None:
    """Worker-side: normalize payload, Graph-enrich, resolve sender, record event, run DM + agent."""
    raw_dump = json.dumps(raw_messaging, default=str)
    logger.info(
        "instagram_webhook_work start integration_account_id=%s inbox_id=%s keys=%s raw_messaging=%s",
        account.id,
        ig_account_id,
        list(raw_messaging.keys()),
        raw_dump[:12000],
    )
    messaging = _normalize_instagram_messaging_for_dm(dict(raw_messaging))
    if messaging is None:
        logger.info(
            "instagram_webhook_work skip cannot_normalize keys=%s",
            list(raw_messaging.keys()),
        )
        return

    norm_dump = json.dumps(messaging, default=str)
    logger.info(
        "instagram_webhook_work after_normalize len=%s value=%s",
        len(norm_dump),
        norm_dump[:12000],
    )

    messaging = instagram_enrich_messaging_with_graph(account=account, messaging=messaging)

    message = messaging.get("message")
    if not isinstance(message, dict) or not message:
        logger.warning(
            "instagram_webhook_work skip no_message keys=%s",
            list(messaging.keys()),
        )
        return
    if message.get("is_echo"):
        logger.info("instagram_webhook_work skip is_echo mid=%s", message.get("mid"))
        return
    if message.get("is_self"):
        logger.info("instagram_webhook_work skip is_self mid=%s", message.get("mid"))
        return

    sender_igsid = _resolve_instagram_dm_sender_igsid(
        account=account,
        messaging=messaging,
        ig_account_id=ig_account_id,
        message=message,
    )
    if not sender_igsid or sender_igsid == ig_account_id:
        msg_dump = json.dumps(messaging, default=str)
        logger.warning(
            "instagram_webhook_work skip sender unresolved_or_self inbox_id=%s sender_igsid=%s "
            "keys=%s is_edit=%s messaging_json=%s",
            ig_account_id,
            sender_igsid or "(empty)",
            list(messaging.keys()),
            bool(message.get("is_edit")),
            msg_dump[:12000],
        )
        return

    mid = str(message.get("mid") or "")
    logger.info(
        "instagram_webhook_work dispatch integration_account_id=%s sender=%s mid_prefix=%s is_edit=%s",
        account.id,
        sender_igsid,
        mid[:32],
        bool(message.get("is_edit")),
    )
    _record_dm_event(account, messaging)

    from core.services.instagram_events_processor import process_instagram_dm

    process_instagram_dm(account=account, messaging=messaging, sender_igsid=sender_igsid)


def handle_webhook_payload(payload: dict[str, Any]) -> None:
    """Dispatch each messaging entry to the appropriate account's event processor."""
    obj = payload.get("object")
    if obj != "instagram":
        logger.info(
            "instagram_webhook_payload skip wrong_or_missing object=%r entry_count=%s",
            obj,
            len(payload.get("entry") or []) if isinstance(payload.get("entry"), list) else 0,
        )
        return

    entries = payload.get("entry", [])
    if not isinstance(entries, list):
        logger.warning("instagram_webhook_payload malformed entry is not a list type=%s", type(entries).__name__)
        return

    logger.info("instagram_webhook_payload object=instagram entry_count=%s", len(entries))

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        ig_account_id = str(entry.get("id") or "")
        if not ig_account_id:
            logger.warning("instagram_webhook_payload entry skip missing entry.id keys=%s", list(entry.keys()))
            continue

        messaging_list = entry.get("messaging", [])
        if not isinstance(messaging_list, list):
            messaging_list = []
        logger.info(
            "instagram_webhook_payload entry ig_user_id=%s messaging_count=%s",
            ig_account_id,
            len(messaging_list),
        )

        account = find_account_by_ig_user_id(ig_account_id)
        if account is None:
            logger.warning(
                "instagram_webhook_payload no_integration_account ig_user_id=%s (no active IntegrationAccount)",
                ig_account_id,
            )
            continue

        logger.info(
            "instagram_webhook_payload matched integration_account_id=%s workspace_id=%s",
            account.id,
            account.workspace_id,
        )

        for messaging in messaging_list:
            if not isinstance(messaging, dict):
                continue
            if not _instagram_webhook_messaging_needs_dm_worker(messaging):
                logger.info(
                    "instagram_webhook_payload skip_enqueue not_dm_signal keys=%s",
                    list(messaging.keys()),
                )
                continue
            from core.tasks.instagram_dm import process_instagram_webhook_messaging_task

            process_instagram_webhook_messaging_task.delay(
                str(account.id),
                ig_account_id,
                dict(messaging),
            )
            logger.info(
                "instagram_webhook_payload enqueued process_instagram_webhook_messaging_task "
                "integration_account_id=%s inbox_id=%s keys=%s",
                account.id,
                ig_account_id,
                list(messaging.keys()),
            )


def _record_dm_event(account: IntegrationAccount, messaging: dict[str, Any]) -> None:
    message = messaging.get("message") or {}
    mid = str(message.get("mid") or "")
    if message.get("is_edit"):
        ne = message.get("num_edit")
        external_id = f"{mid}:edit:{ne}"[:255] if mid else ""
    else:
        external_id = mid
    _ev, created = IntegrationEvent.objects.get_or_create(
        integration_account=account,
        event_type=INSTAGRAM_DM_MESSAGE.slug,
        external_event_id=external_id[:255],
        defaults={"payload": messaging},
    )
    logger.info(
        "instagram_webhook_integration_event integration_account_id=%s mid=%s created=%s",
        account.id,
        external_id[:80] if external_id else "(empty)",
        created,
    )


def process_webhook_request(request: HttpRequest) -> tuple[int, str]:
    """Entry point called from the router for POST webhook events."""
    raw_len = len(request.body or b"")
    logger.info(
        "instagram_webhook_post begin content_length_header=%s body_len=%s",
        request.headers.get("Content-Length"),
        raw_len,
    )

    if not verify_webhook_signature(request):
        logger.warning("instagram_webhook_post response 401 unauthorized body_len=%s", raw_len)
        return 401, "unauthorized"

    try:
        body = request.body.decode("utf-8") if request.body else ""
        payload = json.loads(body) if body else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("instagram_webhook_post response 400 invalid_json err=%s body_len=%s", exc, raw_len)
        return 400, "invalid json"

    if not isinstance(payload, dict):
        logger.warning(
            "instagram_webhook_post response 400 invalid_payload type=%s",
            type(payload).__name__,
        )
        return 400, "invalid payload"

    logger.info(
        "instagram_webhook_post parsed keys=%s object=%r",
        list(payload.keys()),
        payload.get("object"),
    )

    try:
        handle_webhook_payload(payload)
    except Exception:
        logger.exception("instagram_webhook_post handle_webhook_payload failed")

    logger.info("instagram_webhook_post response 200 ok")
    return 200, "ok"


def handle_webhook_verification(hub_mode: str, hub_verify_token: str, hub_challenge: str) -> tuple[int, str]:
    """Respond to Meta's GET webhook verification handshake."""
    verify_token = str(getattr(settings, "INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "") or "")
    if hub_mode == "subscribe" and secrets.compare_digest(hub_verify_token, verify_token):
        logger.info("instagram_webhook_verify GET ok hub.mode=subscribe challenge_len=%s", len(hub_challenge or ""))
        return 200, hub_challenge
    token_ok = bool(verify_token) and secrets.compare_digest(hub_verify_token, verify_token)
    logger.warning(
        "instagram_webhook_verify GET forbidden hub_mode=%r hub_mode_is_subscribe=%s verify_token_ok=%s",
        hub_mode,
        hub_mode == "subscribe",
        token_ok,
    )
    return 403, "forbidden"
