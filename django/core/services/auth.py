import base64

from ninja.errors import HttpError
from ninja.security import APIKeyHeader

from core.models import ApiToken, Organization, OrganizationMember


ORGANIZATION_HEADER = "X-Org-Id"


def resolve_active_organization(user, organization_id: int) -> Organization:
    """
    Resolve organization from header id: org must exist, be active, and user must be an active member.
    Raises HttpError with clear messages for clients.
    """
    member = (
        OrganizationMember.objects.select_related("organization")
        .filter(
            user=user,
            organization_id=organization_id,
            status=OrganizationMember.Status.ACTIVE,
            organization__status=Organization.Status.ACTIVE,
        )
        .first()
    )
    if member:
        return member.organization

    org_exists = Organization.objects.filter(id=organization_id).exists()
    if not org_exists:
        raise HttpError(404, "Organization not found.")

    raise HttpError(
        403,
        "You do not have access to this organization (not a member or membership is not active).",
    )


class ApiKeyAuth(APIKeyHeader):
    param_name = "Authorization"

    def __init__(self, *, require_active_organization: bool = False) -> None:
        self.require_active_organization = require_active_organization
        super().__init__()

    def authenticate(self, request, key: str | None):
        if not key:
            return None
        try:
            raw_token = key.split(" ")[-1]
            decoded_token = base64.b64decode(raw_token).decode("utf-8")

            api_token = ApiToken.objects.select_related("user", "user__organization").get(
                token=decoded_token, is_active=True
            )
            if not api_token.is_valid:
                return None

            api_token.mark_as_used()

            user = api_token.user
            setattr(request, "user", user)
            setattr(request, "organization", user.organization)

            if self.require_active_organization:
                org_id_raw = request.headers.get(ORGANIZATION_HEADER)
                if org_id_raw is None or str(org_id_raw).strip() == "":
                    err = HttpError(
                        400,
                        f"Missing required header {ORGANIZATION_HEADER} (active organization id).",
                    )
                    setattr(err, "error_code", "organization_header_required")
                    raise err
                try:
                    org_id = int(str(org_id_raw).strip())
                except (TypeError, ValueError):
                    err = HttpError(
                        400,
                        f"Invalid {ORGANIZATION_HEADER}: expected integer organization id.",
                    )
                    setattr(err, "error_code", "organization_header_invalid")
                    raise err

                org = resolve_active_organization(user, org_id)
                setattr(request, "organization", org)

            return user
        except HttpError:
            raise
        except Exception:
            return None
