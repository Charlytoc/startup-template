from django.contrib import admin
from core.admin.user import UserAdmin
from core.admin.organization import OrganizationAdmin
# from core.admin.api_token import ApiTokenAdmin
# from core.admin.agent_session_log import AgentSessionLogAdmin  # noqa: F401 — registers via @admin.register
from core.models import Organization, User

admin.site.register(User, UserAdmin)
admin.site.register(Organization, OrganizationAdmin)
# admin.site.register(ApiToken, ApiTokenAdmin)