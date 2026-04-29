from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from core.admin.json_viewer import PrettyJSONAdminMixin
from core.models import TaskExecution


class TaskExecutionAdmin(PrettyJSONAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "job_assignment",
        "workspace",
        "status",
        "requires_approval",
        "agent_session_log_link",
        "started_at",
        "completed_at",
        "created",
    )
    list_filter = (
        "status",
        "requires_approval",
        "workspace__organization",
    )
    search_fields = ("id", "name", "job_assignment__role_name", "workspace__name")
    readonly_fields = ("id", "created", "modified", "agent_session_log_link")
    raw_id_fields = (
        "workspace",
        "job_assignment",
        "approved_by",
    )
    ordering = ("-created",)

    @admin.display(description="Agent session log")
    def agent_session_log_link(self, obj: TaskExecution):
        """Link to the :class:`AgentSessionLog` admin change page for this execution's run."""
        outputs = obj.outputs or {}
        log_id = outputs.get("agent_session_log")
        if not log_id:
            return "—"
        try:
            url = reverse("admin:core_agentsessionlog_change", args=[log_id])
        except Exception:
            return format_html("<code>{}</code>", log_id)
        return format_html('<a href="{}">{}</a>', url, str(log_id)[:8] + "…")
