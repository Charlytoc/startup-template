from django.contrib import admin

class AgentSessionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "model", "provider", "status", "iterations", "tool_calls_count", "total_duration", "started_at")
    list_filter = ("status", "provider", "model")
    search_fields = ("user__email", "celery_task_id", "error_message")
    readonly_fields = ("id", "celery_task_id", "started_at", "ended_at", "total_duration", "iterations", "tool_calls_count", "inputs", "outputs", "tools")
    ordering = ("-started_at",)
