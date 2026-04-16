from django.db import transaction
from django.utils import timezone
from ninja import Router, Schema

from core.models import Role, Workspace, WorkspaceMember
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
