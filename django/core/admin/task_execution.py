from django.contrib import admin

from core.models import TaskExecution


class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job_assignment",
        "workspace",
        "status",
        "requires_approval",
        "started_at",
        "completed_at",
        "created",
    )
    list_filter = (
        "status",
        "requires_approval",
        "workspace__organization",
    )
    search_fields = ("id", "job_assignment__role_name", "workspace__name")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = (
        "workspace",
        "job_assignment",
        "approved_by",
    )
    ordering = ("-created",)
