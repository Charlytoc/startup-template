from django.contrib import admin
from django.utils.html import format_html

from core.admin.json_viewer import PrettyJSONAdminMixin
from core.models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("role", "preview", "created")
    readonly_fields = ("role", "preview", "created")
    ordering = ("created",)

    @admin.display(description="Content")
    def preview(self, obj: Message):
        text = (obj.content_text or "").strip()
        if not text and obj.content_structured is not None:
            text = "(structured)"
        if len(text) > 400:
            text = text[:400] + "…"
        return format_html('<div style="white-space: pre-wrap; max-width: 60ch;">{}</div>', text)

    def has_add_permission(self, request, obj=None) -> bool:
        return False


class ConversationAdmin(PrettyJSONAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "workspace",
        "integration_account",
        "cyber_identity",
        "status",
        "message_count",
        "last_interaction_at",
        "created",
    )
    list_filter = ("status", "workspace__organization", "integration_account__provider")
    search_fields = ("id", "cyber_identity__display_name", "workspace__name")
    readonly_fields = ("id", "created", "modified", "last_interaction_at")
    raw_id_fields = ("workspace", "integration_account", "cyber_identity")
    ordering = ("-last_interaction_at", "-created")
    inlines = [MessageInline]

    @admin.display(description="Messages", ordering=None)
    def message_count(self, obj: Conversation) -> int:
        return obj.messages.count()
