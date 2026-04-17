import uuid
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError

from core.models import IntegrationAccount, Role, Workspace, WorkspaceMember
from core.services.auth import ApiKeyAuth
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


def _default_member_role(request):
    org = request.organization
    role, _ = Role.objects.get_or_create(
        organization=org,
        slug="member",
        defaults={
            "display_name": "Member",
            "role_capabilities": [],
        },
    )
    return role


def _workspace_for_member(request, workspace_id: int) -> Workspace:
    org = request.organization
    workspace = Workspace.objects.filter(id=workspace_id, organization=org).first()
    if workspace is None:
        raise HttpError(404, "Workspace not found.")
    member = WorkspaceMember.objects.filter(
        user=request.user,
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
    auth=ApiKeyAuth(require_active_organization=True),
)
def list_workspace_integrations(request, workspace_id: int):
    workspace = _workspace_for_member(request, workspace_id)
    rows = IntegrationAccount.objects.filter(workspace=workspace).order_by("-created")
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


@router.get("", response={200: list[WorkspaceResponse], 401: ErrorResponseSchema}, auth=ApiKeyAuth(require_active_organization=True))
def list_workspaces(request):
    org = request.organization
    qs = (
        Workspace.objects.filter(
            organization=org,
            workspace_members__user=request.user,
            workspace_members__status=WorkspaceMember.Status.ACTIVE,
        )
        .distinct()
        .order_by("name")
    )
    return 200, [_workspace_response(w) for w in qs]


@router.post(
    "",
    response={201: WorkspaceResponse, 400: ErrorResponseSchema, 401: ErrorResponseSchema},
    auth=ApiKeyAuth(require_active_organization=True),
)
def create_workspace(request, data: WorkspaceCreateRequest):
    name = (data.name or "").strip()
    if not name:
        return 400, ErrorResponseSchema(error="Workspace name is required.", error_code="WORKSPACE_NAME_REQUIRED")

    org = request.organization
    role = _default_member_role(request)

    with transaction.atomic():
        ws = Workspace.objects.create(organization=org, name=name[: Workspace._meta.get_field("name").max_length])
        WorkspaceMember.objects.create(
            user=request.user,
            workspace=ws,
            role=role,
            status=WorkspaceMember.Status.ACTIVE,
            joined_at=timezone.now(),
        )

    return 201, _workspace_response(ws)
