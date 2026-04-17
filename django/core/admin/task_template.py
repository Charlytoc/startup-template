from django.contrib import admin

from core.models import TaskTemplate


class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "workspace", "enabled", "created")
    list_filter = ("type", "enabled", "workspace__organization")
    search_fields = ("name", "description", "id", "workspace__name")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("workspace", "created_by")
    ordering = ("-created",)
