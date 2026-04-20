from django.contrib import admin

from core.admin.json_viewer import PrettyJSONAdminMixin
from core.models import CyberIdentity


class CyberIdentityAdmin(PrettyJSONAdminMixin, admin.ModelAdmin):
    list_display = ("display_name", "type", "workspace", "created_by", "is_active", "created", "modified")
    list_filter = ("is_active", "type", "workspace__organization")
    search_fields = ("display_name", "id", "workspace__name", "type")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("workspace", "created_by")
    ordering = ("workspace_id", "display_name")
