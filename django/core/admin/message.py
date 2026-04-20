from django.contrib import admin

from core.models import Message


class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "created")
    list_filter = ("role",)
    search_fields = ("id", "conversation__id", "content_text")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("conversation",)
    ordering = ("-created",)
