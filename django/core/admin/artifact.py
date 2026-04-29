from django.contrib import admin

from core.models import Artifact


class ArtifactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workspace",
        "task_execution",
        "identity",
        "kind",
        "label",
        "media",
        "integration_account",
        "created",
    )
    list_filter = ("kind", "workspace__organization", "identity__type")
    search_fields = (
        "label",
        "task_execution__id",
        "identity__display_name",
        "media__title",
        "integration_account__display_name",
        "integration_account__external_account_id",
        "id",
    )
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("workspace", "task_execution", "identity", "media", "integration_account")
    ordering = ("-created",)
