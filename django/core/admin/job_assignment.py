from django.contrib import admin

from core.models import JobAssignment


class JobAssignmentAdmin(admin.ModelAdmin):
    list_display = ("role_name", "workspace", "enabled", "created")
    list_filter = ("enabled", "workspace__organization")
    search_fields = ("role_name", "description", "id", "workspace__name")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("workspace",)
    ordering = ("-created",)
