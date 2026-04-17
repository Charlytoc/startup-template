from django.contrib import admin

from core.models import Artifact


class ArtifactAdmin(admin.ModelAdmin):
    list_display = ("id", "task_execution", "kind", "label", "media", "created")
    list_filter = ("kind",)
    search_fields = ("label", "task_execution__id", "media__title", "id")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("task_execution", "media")
    ordering = ("-created",)
