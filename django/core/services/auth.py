import base64
import uuid

from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import APIKeyHeader

from core.models import ApiToken, Organization, OrganizationMember, User


ORGANIZATION_HEADER = "X-Org-Id"


def resolve_active_organization(user, organization_id: uuid.UUID) -> Organization:
    """Return the org referenced by ``organization_id`` if the user is an active member.

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

    if not Organization.objects.filter(id=organization_id).exists():
        raise HttpError(404, "Organization not found.")

    raise HttpError(
        403,
        "You do not have access to this organization (not a member or membership is not active).",
    )


class AuthService:
    @staticmethod
    def get_user_from_request(request: HttpRequest) -> User | None:
        """Return the authenticated user regardless of auth backend (API key or Django session)."""
        auth_user = getattr(request, "auth", None)
        if isinstance(auth_user, User):
            return auth_user
        if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
            return request.user  # type: ignore[return-value]
        return None

    @staticmethod
    def get_active_organization(request: HttpRequest) -> Organization:
        """Read ``X-Org-Id`` and resolve the active organization for the authenticated user."""
        user = AuthService.get_user_from_request(request)
        if user is None:
            raise HttpError(401, "Authentication required.")

        raw = request.headers.get(ORGANIZATION_HEADER)
        if raw is None or str(raw).strip() == "":
            err = HttpError(
                400,
                f"Missing required header {ORGANIZATION_HEADER} (active organization id).",
            )
            setattr(err, "error_code", "organization_header_required")
            raise err
        try:
            org_id = uuid.UUID(str(raw).strip())
        except (TypeError, ValueError, AttributeError):
            err = HttpError(
                400,
                f"Invalid {ORGANIZATION_HEADER}: expected a UUID organization id.",
            )
            setattr(err, "error_code", "organization_header_invalid")
            raise err

        return resolve_active_organization(user, org_id)


auth_service = AuthService()


class ApiKeyAuth(APIKeyHeader):
    param_name = "Authorization"

    def authenticate(self, request: HttpRequest, key: str | None) -> User | None:
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
            setattr(request, "user", api_token.user)
            return api_token.user
        except Exception:
            return None
