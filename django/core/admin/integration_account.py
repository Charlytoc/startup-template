from django.contrib import admin

from core.admin.json_viewer import PrettyJSONAdminMixin
from core.models import IntegrationAccount


class IntegrationAccountAdmin(PrettyJSONAdminMixin, admin.ModelAdmin):
    list_display = (
        "display_name_or_external",
        "provider",
        "workspace",
        "status",
        "last_synced_at",
        "created",
    )
    list_filter = ("provider", "status", "workspace__organization")
    search_fields = ("display_name", "external_account_id", "id", "workspace__name")
    readonly_fields = ("id", "created", "modified", "encrypted_auth")
    raw_id_fields = ("workspace", "created_by")
    ordering = ("-created",)

    @admin.display(description="Account")
    def display_name_or_external(self, obj: IntegrationAccount) -> str:
        return obj.display_name or obj.external_account_id or str(obj.pk)
