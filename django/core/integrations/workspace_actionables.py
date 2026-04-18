"""Resolve which catalog actionables apply to a workspace given its connected integration accounts."""

from __future__ import annotations

import uuid
from typing import Any

from ninja.errors import HttpError

from core.integrations.actionables import ACTIONABLES, TELEGRAM_SEND_MESSAGE
from core.models import IntegrationAccount, Workspace


def _account_row(acc: IntegrationAccount) -> dict[str, Any]:
    return {
        "integration_account_id": str(acc.id),
        "provider": acc.provider,
        "display_name": acc.display_name or acc.external_account_id or str(acc.id),
        "status": acc.status,
    }


def list_actionable_catalog_for_workspace(workspace: Workspace) -> list[dict[str, Any]]:
    """Return UI-ready rows: one entry per (actionable, integration account) binding where applicable.

    Actionables that are not tied to a specific integration (future) can be appended here with
    ``integration_account_id`` omitted.
    """
    out: list[dict[str, Any]] = []
    accounts = list(
        IntegrationAccount.objects.filter(workspace=workspace).exclude(
            status=IntegrationAccount.Status.REVOKED,
        )
    )
    for acc in accounts:
        if acc.provider == IntegrationAccount.Provider.TELEGRAM:
            a = ACTIONABLES[TELEGRAM_SEND_MESSAGE.slug]
            out.append(
                {
                    "slug": a.slug,
                    "name": a.name,
                    "description": a.description,
                    "provider": a.provider,
                    "integration_account_id": str(acc.id),
                    "integration": _account_row(acc),
                }
            )
    return out


def validate_job_assignment_config(*, workspace: Workspace, config: dict[str, Any]) -> None:
    """Light validation: accounts / identities / actions reference workspace-owned rows and known slugs."""
    from core.integrations.event_types import EVENT_TYPES
    from core.models import CyberIdentity

    if not isinstance(config, dict):
        raise HttpError(400, "config must be an object.")

    account_ids = config.get("accounts") or []
    if account_ids is not None and not isinstance(account_ids, list):
        raise HttpError(400, "config.accounts must be a list.")
    for raw in account_ids:
        try:
            uid = uuid.UUID(str(raw))
        except (TypeError, ValueError, AttributeError):
            raise HttpError(400, f"Invalid integration account id in accounts: {raw!r}.")
        if not IntegrationAccount.objects.filter(id=uid, workspace=workspace).exists():
            raise HttpError(400, "One or more integration accounts are not in this workspace.")

    identity_ids = config.get("identities") or []
    if identity_ids is not None and not isinstance(identity_ids, list):
        raise HttpError(400, "config.identities must be a list.")
    for raw in identity_ids:
        try:
            uid = uuid.UUID(str(raw))
        except (TypeError, ValueError, AttributeError):
            raise HttpError(400, f"Invalid cyber identity id in identities: {raw!r}.")
        if not CyberIdentity.objects.filter(id=uid, workspace=workspace).exists():
            raise HttpError(400, "One or more cyber identities are not in this workspace.")
    if len(identity_ids) == 0:
        raise HttpError(400, "At least one cyber identity is required (config.identities).")

    triggers = config.get("triggers") or []
    if not isinstance(triggers, list):
        raise HttpError(400, "config.triggers must be a list.")
    for i, tr in enumerate(triggers):
        if not isinstance(tr, dict):
            raise HttpError(400, f"config.triggers[{i}] must be an object.")
        t = tr.get("type")
        if t not in ("cron", "event"):
            raise HttpError(400, f"config.triggers[{i}].type must be 'cron' or 'event'.")
        if t == "event":
            on = tr.get("on")
            if not on or not isinstance(on, str):
                raise HttpError(400, f"config.triggers[{i}].on must be a non-empty event slug string.")
            if on not in EVENT_TYPES:
                raise HttpError(400, f"Unknown event slug: {on!r}.")

    actions = config.get("actions") or []
    if not isinstance(actions, list):
        raise HttpError(400, "config.actions must be a list.")
    for i, act in enumerate(actions):
        if not isinstance(act, dict):
            raise HttpError(400, f"config.actions[{i}] must be an object.")
        slug = act.get("actionable_slug") or act.get("actionable_id")
        if not slug or not isinstance(slug, str):
            raise HttpError(400, f"config.actions[{i}] needs actionable_slug (string).")
        catalog = ACTIONABLES.get(slug)
        if catalog is None:
            raise HttpError(400, f"Unknown actionable slug: {slug!r}.")
        iid = act.get("integration_account_id")
        if catalog.provider == "telegram":
            if not iid:
                raise HttpError(400, f"Action {slug!r} requires integration_account_id.")
            try:
                acc_uuid = uuid.UUID(str(iid))
            except (TypeError, ValueError, AttributeError):
                raise HttpError(400, f"Invalid integration_account_id on action {slug!r}.")
            acc = IntegrationAccount.objects.filter(id=acc_uuid, workspace=workspace).first()
            if acc is None:
                raise HttpError(400, f"integration_account_id for action {slug!r} is not in this workspace.")
            if acc.provider != IntegrationAccount.Provider.TELEGRAM:
                raise HttpError(400, f"Action {slug!r} requires a Telegram integration account.")
