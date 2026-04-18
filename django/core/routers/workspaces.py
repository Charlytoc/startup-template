import uuid
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth

from core.integrations.event_types import TELEGRAM_PRIVATE_MESSAGE
from core.integrations.workspace_actionables import (
    list_actionable_catalog_for_workspace,
    validate_job_assignment_config,
)
from core.models import CyberIdentity, IntegrationAccount, JobAssignment, Role, Workspace, WorkspaceMember
from core.services.auth import ApiKeyAuth, auth_service
from core.utils.schemas import ErrorResponseSchema

router = Router(tags=["Workspaces"])


class WorkspaceCreateRequest(Schema):
    name: str


class WorkspaceResponse(Schema):
    id: int
    name: str
    organization_id: str


def _workspace_response(ws: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        organization_id=str(ws.organization_id),
    )


def _default_member_role(organization):
    role, _ = Role.objects.get_or_create(
        organization=organization,
        slug="member",
        defaults={
            "display_name": "Member",
            "role_capabilities": [],
        },
    )
    return role


def _workspace_for_member(request, workspace_id: int) -> Workspace:
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


class IntegrationAccountListItem(Schema):
    id: uuid.UUID
    provider: str
    display_name: str
    status: str
    external_account_id: str
    created: datetime


@router.get(
    "/{workspace_id}/integrations/",
    response={
        200: list[IntegrationAccountListItem],
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def list_workspace_integrations(request, workspace_id: int):
    workspace = _workspace_for_member(request, workspace_id)
    rows = (
        IntegrationAccount.objects.filter(workspace=workspace)
        .exclude(status=IntegrationAccount.Status.REVOKED)
        .order_by("-created")
    )
    return 200, [
        IntegrationAccountListItem(
            id=row.id,
            provider=row.provider,
            display_name=row.display_name or "",
            status=row.status,
            external_account_id=row.external_account_id,
            created=row.created,
        )
        for row in rows
    ]


@router.get(
    "",
    response={200: list[WorkspaceResponse], 401: ErrorResponseSchema},
    auth=[ApiKeyAuth(), django_auth],
)
def list_workspaces(request):
    user = auth_service.get_user_from_request(request)
    org = auth_service.get_active_organization(request)
    qs = (
        Workspace.objects.filter(
            organization=org,
            workspace_members__user=user,
            workspace_members__status=WorkspaceMember.Status.ACTIVE,
        )
        .distinct()
        .order_by("name")
    )
    return 200, [_workspace_response(w) for w in qs]


@router.post(
    "",
    response={201: WorkspaceResponse, 400: ErrorResponseSchema, 401: ErrorResponseSchema},
    auth=[ApiKeyAuth(), django_auth],
)
def create_workspace(request, data: WorkspaceCreateRequest):
    name = (data.name or "").strip()
    if not name:
        return 400, ErrorResponseSchema(error="Workspace name is required.", error_code="WORKSPACE_NAME_REQUIRED")

    user = auth_service.get_user_from_request(request)
    org = auth_service.get_active_organization(request)
    role = _default_member_role(org)

    with transaction.atomic():
        ws = Workspace.objects.create(organization=org, name=name[: Workspace._meta.get_field("name").max_length])
        WorkspaceMember.objects.create(
            user=user,
            workspace=ws,
            role=role,
            status=WorkspaceMember.Status.ACTIVE,
            joined_at=timezone.now(),
        )

    return 201, _workspace_response(ws)


CYBER_IDENTITY_TYPES = [t.value for t in CyberIdentity.Type]


class CyberIdentityResponse(Schema):
    id: uuid.UUID
    workspace_id: int
    type: str
    display_name: str
    is_active: bool
    config: dict
    created: datetime


class CyberIdentityCreateRequest(Schema):
    type: str
    display_name: str
    is_active: bool = True
    config: dict = {}


class CyberIdentityUpdateRequest(Schema):
    type: str | None = None
    display_name: str | None = None
    is_active: bool | None = None
    config: dict | None = None


def _cyber_identity_response(row: CyberIdentity) -> CyberIdentityResponse:
    return CyberIdentityResponse(
        id=row.id,
        workspace_id=row.workspace_id,
        type=row.type,
        display_name=row.display_name,
        is_active=row.is_active,
        config=row.config or {},
        created=row.created,
    )


def _validate_type(value: str) -> str:
    if value not in CYBER_IDENTITY_TYPES:
        raise HttpError(400, f"Invalid type. Expected one of: {', '.join(CYBER_IDENTITY_TYPES)}.")
    return value


@router.get(
    "/{workspace_id}/cyber-identities/",
    response={
        200: list[CyberIdentityResponse],
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def list_cyber_identities(request, workspace_id: int):
    workspace = _workspace_for_member(request, workspace_id)
    rows = CyberIdentity.objects.filter(workspace=workspace).order_by("display_name")
    return 200, [_cyber_identity_response(r) for r in rows]


@router.post(
    "/{workspace_id}/cyber-identities/",
    response={
        201: CyberIdentityResponse,
        400: ErrorResponseSchema,
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def create_cyber_identity(request, workspace_id: int, data: CyberIdentityCreateRequest):
    workspace = _workspace_for_member(request, workspace_id)
    user = auth_service.get_user_from_request(request)
    display_name = (data.display_name or "").strip()
    if not display_name:
        return 400, ErrorResponseSchema(error="display_name is required.", error_code="DISPLAY_NAME_REQUIRED")
    _validate_type(data.type)
    row = CyberIdentity(
        workspace=workspace,
        created_by=user if getattr(user, "pk", None) else None,
        type=data.type,
        display_name=display_name[:200],
        is_active=data.is_active,
        config=data.config or {},
    )
    row.save()
    return 201, _cyber_identity_response(row)


@router.patch(
    "/{workspace_id}/cyber-identities/{cyber_identity_id}/",
    response={
        200: CyberIdentityResponse,
        400: ErrorResponseSchema,
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def update_cyber_identity(
    request,
    workspace_id: int,
    cyber_identity_id: uuid.UUID,
    data: CyberIdentityUpdateRequest,
):
    workspace = _workspace_for_member(request, workspace_id)
    row = CyberIdentity.objects.filter(id=cyber_identity_id, workspace=workspace).first()
    if row is None:
        raise HttpError(404, "Cyber identity not found.")

    if data.type is not None:
        _validate_type(data.type)
        row.type = data.type
    if data.display_name is not None:
        name = data.display_name.strip()
        if not name:
            return 400, ErrorResponseSchema(error="display_name cannot be empty.", error_code="DISPLAY_NAME_REQUIRED")
        row.display_name = name[:200]
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.config is not None:
        row.config = data.config
    row.save()
    return 200, _cyber_identity_response(row)


@router.delete(
    "/{workspace_id}/cyber-identities/{cyber_identity_id}/",
    response={204: None, 401: ErrorResponseSchema, 403: ErrorResponseSchema, 404: ErrorResponseSchema},
    auth=[ApiKeyAuth(), django_auth],
)
def delete_cyber_identity(request, workspace_id: int, cyber_identity_id: uuid.UUID):
    workspace = _workspace_for_member(request, workspace_id)
    row = CyberIdentity.objects.filter(id=cyber_identity_id, workspace=workspace).first()
    if row is None:
        raise HttpError(404, "Cyber identity not found.")
    row.delete()
    return 204, None


class ActionableCatalogItem(Schema):
    slug: str
    name: str
    description: str
    provider: str
    integration_account_id: str
    integration: dict


@router.get(
    "/{workspace_id}/actionables/",
    response={
        200: list[ActionableCatalogItem],
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def list_workspace_actionables(request, workspace_id: int):
    workspace = _workspace_for_member(request, workspace_id)
    raw = list_actionable_catalog_for_workspace(workspace)
    return 200, [ActionableCatalogItem(**row) for row in raw]


class JobAssignmentResponse(Schema):
    id: uuid.UUID
    workspace_id: int
    role_name: str
    description: str
    instructions: str
    enabled: bool
    config: dict
    created: datetime


def _job_assignment_response(row: JobAssignment) -> JobAssignmentResponse:
    return JobAssignmentResponse(
        id=row.id,
        workspace_id=row.workspace_id,
        role_name=row.role_name,
        description=row.description or "",
        instructions=row.instructions or "",
        enabled=row.enabled,
        config=row.config or {},
        created=row.created,
    )


class JobAssignmentCreateRequest(Schema):
    role_name: str
    description: str = ""
    instructions: str = ""
    enabled: bool = True
    config: dict = {}


class JobAssignmentUpdateRequest(Schema):
    role_name: str | None = None
    description: str | None = None
    instructions: str | None = None
    enabled: bool | None = None
    config: dict | None = None


def _default_job_config() -> dict:
    return {
        "accounts": [],
        "identities": [],
        "triggers": [],
        "actions": [],
    }


def _normalize_job_config(cfg: dict) -> dict:
    """Merge defaults, infer ``accounts`` from ``actions``, and add a default event trigger if none set."""
    out = {**_default_job_config(), **cfg}
    accs = [str(x) for x in (out.get("accounts") or [])]
    seen = set(accs)
    for act in out.get("actions") or []:
        if isinstance(act, dict) and act.get("integration_account_id"):
            iid = str(act["integration_account_id"])
            if iid not in seen:
                accs.append(iid)
                seen.add(iid)
    out["accounts"] = accs
    if not out.get("triggers"):
        out["triggers"] = [
            {"type": "event", "on": TELEGRAM_PRIVATE_MESSAGE.slug, "filter": {}},
        ]
    return out


@router.get(
    "/{workspace_id}/job-assignments/",
    response={
        200: list[JobAssignmentResponse],
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def list_job_assignments(request, workspace_id: int):
    workspace = _workspace_for_member(request, workspace_id)
    rows = JobAssignment.objects.filter(workspace=workspace).order_by("role_name")
    return 200, [_job_assignment_response(r) for r in rows]


@router.post(
    "/{workspace_id}/job-assignments/",
    response={
        201: JobAssignmentResponse,
        400: ErrorResponseSchema,
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def create_job_assignment(request, workspace_id: int, data: JobAssignmentCreateRequest):
    workspace = _workspace_for_member(request, workspace_id)
    role_name = (data.role_name or "").strip()
    if not role_name:
        return 400, ErrorResponseSchema(error="role_name is required.", error_code="ROLE_NAME_REQUIRED")

    cfg = _normalize_job_config(data.config or {})
    validate_job_assignment_config(workspace=workspace, config=cfg)

    row = JobAssignment(
        workspace=workspace,
        role_name=role_name[:200],
        description=(data.description or "").strip(),
        instructions=(data.instructions or "").strip(),
        enabled=data.enabled,
        config=cfg,
    )
    row.save()
    return 201, _job_assignment_response(row)


@router.patch(
    "/{workspace_id}/job-assignments/{job_assignment_id}/",
    response={
        200: JobAssignmentResponse,
        400: ErrorResponseSchema,
        401: ErrorResponseSchema,
        403: ErrorResponseSchema,
        404: ErrorResponseSchema,
    },
    auth=[ApiKeyAuth(), django_auth],
)
def update_job_assignment(
    request,
    workspace_id: int,
    job_assignment_id: uuid.UUID,
    data: JobAssignmentUpdateRequest,
):
    workspace = _workspace_for_member(request, workspace_id)
    row = JobAssignment.objects.filter(id=job_assignment_id, workspace=workspace).first()
    if row is None:
        raise HttpError(404, "Job assignment not found.")

    if data.role_name is not None:
        name = data.role_name.strip()
        if not name:
            return 400, ErrorResponseSchema(error="role_name cannot be empty.", error_code="ROLE_NAME_REQUIRED")
        row.role_name = name[:200]
    if data.description is not None:
        row.description = data.description.strip()
    if data.instructions is not None:
        row.instructions = data.instructions.strip()
    if data.enabled is not None:
        row.enabled = data.enabled
    if data.config is not None:
        merged = _normalize_job_config({**(row.config or {}), **data.config})
        validate_job_assignment_config(workspace=workspace, config=merged)
        row.config = merged
    row.save()
    return 200, _job_assignment_response(row)


@router.delete(
    "/{workspace_id}/job-assignments/{job_assignment_id}/",
    response={204: None, 401: ErrorResponseSchema, 403: ErrorResponseSchema, 404: ErrorResponseSchema},
    auth=[ApiKeyAuth(), django_auth],
)
def delete_job_assignment(request, workspace_id: int, job_assignment_id: uuid.UUID):
    workspace = _workspace_for_member(request, workspace_id)
    row = JobAssignment.objects.filter(id=job_assignment_id, workspace=workspace).first()
    if row is None:
        raise HttpError(404, "Job assignment not found.")
    row.delete()
    return 204, None
