from django.contrib import admin

from core.models import TaskExecution


class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task_template",
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
        "task_template__type",
        "workspace__organization",
    )
    search_fields = ("id", "task_template__name", "workspace__name")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = (
        "workspace",
        "task_template",
        "task_assignment",
        "approved_by",
    )
    ordering = ("-created",)
