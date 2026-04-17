from django.contrib import admin

from core.models import TaskAssignment


class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("title_or_template", "task_template", "enabled", "created")
    list_filter = (
        "enabled",
        "task_template__type",
        "task_template__workspace__organization",
    )
    search_fields = ("title", "task_template__name", "id")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("task_template",)
    ordering = ("-created",)

    @admin.display(description="Title")
    def title_or_template(self, obj: TaskAssignment) -> str:
        return obj.title or obj.task_template.name
