from django.contrib import admin

from core.models import IntegrationEvent


class IntegrationEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "integration_account",
        "received_at",
        "processed_at",
    )
    list_filter = (
        "event_type",
        "integration_account__provider",
        "integration_account__workspace__organization",
    )
    search_fields = ("event_type", "external_event_id", "id")
    readonly_fields = ("id", "created", "modified", "received_at")
    raw_id_fields = ("integration_account",)
    ordering = ("-received_at",)
