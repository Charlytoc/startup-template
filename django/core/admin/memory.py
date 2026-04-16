from django.contrib import admin

from core.models import Memory


class MemoryAdmin(admin.ModelAdmin):
    list_display = ("short_content", "identity", "memory_type", "created", "modified")
    list_filter = ("memory_type", "identity__workspace__organization")
    search_fields = ("content", "source", "identity__display_name", "id")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("identity",)
    ordering = ("-created",)

    @admin.display(description="Content")
    def short_content(self, obj: Memory) -> str:
        text = (obj.content or "").strip().splitlines()[0] if obj.content else ""
        return (text[:80] + "…") if len(text) > 80 else (text or "—")
