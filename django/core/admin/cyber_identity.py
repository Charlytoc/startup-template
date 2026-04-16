from django.contrib import admin

from core.models import CyberIdentity


class CyberIdentityAdmin(admin.ModelAdmin):
    list_display = ("display_name", "workspace", "identity_type", "created_by", "is_active", "created", "modified")
    list_filter = ("is_active", "identity_type", "workspace__organization")
    search_fields = ("display_name", "id", "workspace__name", "identity_type__name")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("workspace", "identity_type", "created_by")
    ordering = ("workspace_id", "display_name")
