from django.contrib import admin

from core.models import WorkspaceMember


class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "workspace", "role", "status", "joined_at", "created")
    list_filter = ("status", "workspace__organization")
    search_fields = ("user__email", "workspace__name", "role__slug", "role__display_name")
    ordering = ("workspace_id", "user_id")
    readonly_fields = ("created", "modified")
    raw_id_fields = ("user", "workspace", "role", "invited_by")
