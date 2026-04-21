"""Read/write helpers for ``IntegrationAccount.config['senders']`` (see :mod:`core.schemas.integration_account`)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.db import transaction

from core.models import IntegrationAccount
from core.schemas.integration_account import (
    BaseIntegrationAccountConfig,
    IntegrationAccountSender,
    SenderApprovalStatus,
)

SENDERS_KEY = "senders"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_senders(config: dict[str, Any] | None) -> list[dict[str, Any]]:
    raw = (config or {}).get(SENDERS_KEY) or []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("external_thread_id"):
            out.append(dict(item))
    return out


def _find_index(senders: list[dict[str, Any]], external_thread_id: str) -> int:
    for i, s in enumerate(senders):
        if str(s.get("external_thread_id")) == external_thread_id:
            return i
    return -1


def _write(account: IntegrationAccount, senders: list[dict[str, Any]]) -> None:
    cfg = dict(account.config or {})
    cfg[SENDERS_KEY] = senders
    account.config = cfg
    account.save(update_fields=["config", "modified"])


def get_sender(
    account: IntegrationAccount, external_thread_id: str
) -> IntegrationAccountSender | None:
    """Return the typed sender for ``external_thread_id`` on ``account``, or ``None``."""
    external_thread_id = (external_thread_id or "").strip()
    if not external_thread_id:
        return None
    senders = _load_senders(account.config)
    idx = _find_index(senders, external_thread_id)
    if idx < 0:
        return None
    try:
        return IntegrationAccountSender.model_validate(senders[idx])
    except Exception:
        return None


def list_senders(account: IntegrationAccount) -> list[IntegrationAccountSender]:
    """All senders on the account, typed (invalid rows are dropped)."""
    out: list[IntegrationAccountSender] = []
    for row in _load_senders(account.config):
        try:
            out.append(IntegrationAccountSender.model_validate(row))
        except Exception:
            continue
    return out


def upsert_sender(
    account: IntegrationAccount,
    external_thread_id: str,
    *,
    default_status: SenderApprovalStatus,
) -> IntegrationAccountSender:
    """Insert a new sender with ``default_status`` or refresh ``last_seen_at`` on an existing one.

    Never downgrades the status of an existing sender.
    """
    external_thread_id = (external_thread_id or "").strip()
    if not external_thread_id:
        raise ValueError("external_thread_id is required")

    now_iso = _now_iso()
    with transaction.atomic():
        locked = IntegrationAccount.objects.select_for_update().get(pk=account.pk)
        senders = _load_senders(locked.config)
        idx = _find_index(senders, external_thread_id)
        if idx < 0:
            row = IntegrationAccountSender(
                external_thread_id=external_thread_id,
                approval_status=default_status,
                extractions={},
                first_seen_at=datetime.fromisoformat(now_iso),
                last_seen_at=datetime.fromisoformat(now_iso),
            ).model_dump(mode="json")
            senders.append(row)
        else:
            row = dict(senders[idx])
            row.setdefault("extractions", {})
            row.setdefault("first_seen_at", now_iso)
            row["last_seen_at"] = now_iso
            senders[idx] = row

        _write(locked, senders)
        account.config = locked.config

    return IntegrationAccountSender.model_validate(row)


def set_approval_status(
    account: IntegrationAccount,
    external_thread_id: str,
    status: SenderApprovalStatus,
) -> IntegrationAccountSender:
    """Create the sender if missing, then set ``approval_status`` to ``status``."""
    external_thread_id = (external_thread_id or "").strip()
    if not external_thread_id:
        raise ValueError("external_thread_id is required")

    now_iso = _now_iso()
    with transaction.atomic():
        locked = IntegrationAccount.objects.select_for_update().get(pk=account.pk)
        senders = _load_senders(locked.config)
        idx = _find_index(senders, external_thread_id)
        if idx < 0:
            row = IntegrationAccountSender(
                external_thread_id=external_thread_id,
                approval_status=status,
                extractions={},
                first_seen_at=datetime.fromisoformat(now_iso),
                last_seen_at=datetime.fromisoformat(now_iso),
            ).model_dump(mode="json")
            senders.append(row)
        else:
            row = dict(senders[idx])
            row["approval_status"] = status.value
            row["last_seen_at"] = now_iso
            row.setdefault("first_seen_at", now_iso)
            row.setdefault("extractions", {})
            senders[idx] = row

        _write(locked, senders)
        account.config = locked.config

    return IntegrationAccountSender.model_validate(row)


def merge_extractions(
    account: IntegrationAccount,
    external_thread_id: str,
    delta: dict[str, Any],
) -> IntegrationAccountSender:
    """Shallow-merge ``delta`` into an existing sender's ``extractions`` dict.

    Values in ``delta`` **overwrite** previous values at the top level. Nested structures are
    replaced wholesale; future tools can pass a deep-merge themselves if they need it.
    """
    external_thread_id = (external_thread_id or "").strip()
    if not external_thread_id:
        raise ValueError("external_thread_id is required")
    if not isinstance(delta, dict):
        raise ValueError("extractions delta must be a JSON object (dict)")

    now_iso = _now_iso()
    with transaction.atomic():
        locked = IntegrationAccount.objects.select_for_update().get(pk=account.pk)
        senders = _load_senders(locked.config)
        idx = _find_index(senders, external_thread_id)
        if idx < 0:
            raise ValueError(
                f"No sender with external_thread_id={external_thread_id!r} on account {account.id}"
            )
        row = dict(senders[idx])
        ex = row.get("extractions")
        if not isinstance(ex, dict):
            ex = {}
        ex.update(delta)
        row["extractions"] = ex
        row["last_seen_at"] = now_iso
        senders[idx] = row
        _write(locked, senders)
        account.config = locked.config

    return IntegrationAccountSender.model_validate(row)


def validate_senders_in_config(config: dict[str, Any] | None) -> None:
    """Raise ``ValueError`` if ``config['senders']`` is not a list of valid sender objects."""
    if not config or SENDERS_KEY not in config:
        return
    BaseIntegrationAccountConfig.model_validate({"senders": config.get(SENDERS_KEY)})
