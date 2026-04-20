from django.contrib import admin

from core.models import Conversation


class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workspace",
        "integration_account",
        "cyber_identity",
        "status",
        "last_interaction_at",
        "created",
    )
    list_filter = ("status", "workspace__organization", "integration_account__provider")
    search_fields = ("id", "cyber_identity__display_name", "workspace__name")
    readonly_fields = ("id", "created", "modified", "last_interaction_at")
    raw_id_fields = ("workspace", "integration_account", "cyber_identity")
    ordering = ("-last_interaction_at", "-created")
