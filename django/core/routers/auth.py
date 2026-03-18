import base64
from typing import Optional

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from ninja import Router, Schema
from ninja.security import django_auth

from core.models import ApiToken, Organization, User
from core.utils.auth import ApiKeyAuth
from core.utils.schemas import ErrorResponseSchema

router = Router(tags=["Authentication"])


class SignupRequest(Schema):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[int] = None


class LoginRequest(Schema):
    email: str
    password: str


class UserResponse(Schema):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    organization: dict
    profile_picture: Optional[str]
    is_active: bool
    is_staff: bool
    created: str


class OrganizationResponse(Schema):
    id: int
    name: str
    domain: str
    status: str


class AuthResponse(Schema):
    api_token: str
    user: UserResponse
    organization: OrganizationResponse


def get_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        organization={
            "id": user.organization.id,
            "name": user.organization.name,
            "domain": user.organization.domain,
            "status": user.organization.status,
        },
        profile_picture=user.profile_picture.url if user.profile_picture else None,
        is_active=user.is_active,
        is_staff=user.is_staff,
        created=user.created.isoformat(),
    )


def get_organization_response(org: Organization) -> OrganizationResponse:
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        domain=org.domain,
        status=org.status,
    )


def get_auth_context(request):
    if hasattr(request, "user") and request.user.is_authenticated:
        return request.user, request.user.organization
    return request.user, request.organization


@router.get("/organizations", response={200: list[OrganizationResponse]})
def list_organizations(request):
    organizations = Organization.objects.filter(status=Organization.Status.ACTIVE)
    return 200, [get_organization_response(org) for org in organizations]


@router.post("/signup", response={201: AuthResponse, 400: ErrorResponseSchema})
def signup(request, data: SignupRequest):
    existing_user = User.objects.filter(email=data.email).first()
    if existing_user:
        return 400, ErrorResponseSchema(error="User with this email already exists", error_code="USER_EXISTS")

    with transaction.atomic():
        default_org, _ = Organization.objects.get_or_create(
            name="Default",
            defaults={"domain": "default.local", "status": Organization.Status.ACTIVE},
        )
        organization = default_org
        if data.organization_id:
            organization = Organization.objects.filter(id=data.organization_id).first() or default_org

        try:
            user = User.objects.create_user(
                email=data.email,
                password=data.password,
                first_name=data.first_name,
                last_name=data.last_name,
                organization=organization,
            )
        except IntegrityError:
            return 400, ErrorResponseSchema(error="User with this email already exists", error_code="USER_EXISTS")

        api_token = ApiToken.objects.create(user=user, name="Default Token")
        encoded_token = base64.b64encode(api_token.token.encode()).decode()

    return 201, AuthResponse(
        api_token=encoded_token,
        user=get_user_response(user).dict(),
        organization=get_organization_response(organization).dict(),
    )


@router.post("/login", response={200: AuthResponse, 401: ErrorResponseSchema})
def login(request, data: LoginRequest):
    user = authenticate(email=data.email, password=data.password)
    if not user:
        return 401, ErrorResponseSchema(error="Invalid email or password", error_code="INVALID_CREDENTIALS")
    if not user.is_active:
        return 401, ErrorResponseSchema(error="Account is deactivated", error_code="ACCOUNT_DEACTIVATED")

    api_token, _ = ApiToken.objects.get_or_create(user=user, name="Default Token", defaults={"is_active": True})
    encoded_token = base64.b64encode(api_token.token.encode()).decode()
    return 200, AuthResponse(
        api_token=encoded_token,
        user=get_user_response(user).dict(),
        organization=get_organization_response(user.organization).dict(),
    )


@router.get("/me", response={200: UserResponse, 401: ErrorResponseSchema}, auth=[ApiKeyAuth(), django_auth])
def get_current_user(request):
    try:
        user, _organization = get_auth_context(request)
        return 200, get_user_response(user)
    except Exception:
        return 401, ErrorResponseSchema(error="Authentication required", error_code="AUTH_REQUIRED")


@router.post("/logout", response={200: dict, 401: ErrorResponseSchema}, auth=[ApiKeyAuth(), django_auth])
def logout(request):
    try:
        _user, _organization = get_auth_context(request)
        if hasattr(request, "user") and request.user.is_authenticated:
            from django.contrib.auth import logout as django_logout

            django_logout(request)
        return 200, {"message": "Successfully logged out"}
    except Exception:
        return 401, ErrorResponseSchema(error="Authentication required", error_code="AUTH_REQUIRED")
