from django.contrib import admin

from core.admin.json_viewer import PrettyJSONAdminMixin


class AgentSessionLogAdmin(PrettyJSONAdminMixin, admin.ModelAdmin):
    pretty_json_fields = ("inputs", "outputs", "tools")

    list_display = ("id", "user", "model", "provider", "status", "iterations", "tool_calls_count", "total_duration", "started_at")
    list_filter = ("status", "provider", "model")
    search_fields = ("user__email", "celery_task_id", "error_message")
    readonly_fields = (
        "id",
        "celery_task_id",
        "started_at",
        "ended_at",
        "total_duration",
        "iterations",
        "tool_calls_count",
        "inputs_pretty",
        "outputs_pretty",
        "tools_pretty",
    )
    exclude = ("inputs", "outputs", "tools")
    ordering = ("-started_at",)
