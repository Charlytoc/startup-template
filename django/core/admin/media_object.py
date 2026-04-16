from django.contrib import admin
from django.utils.html import format_html

from core.models import MediaObject


class MediaObjectAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "workspace",
        "mime_type",
        "byte_size",
        "created_by",
        "created",
    )
    list_filter = ("workspace__organization",)
    search_fields = (
        "title",
        "original_filename",
        "id",
        "workspace__name",
    )
    readonly_fields = ("id", "created", "modified", "public_url_preview")
    raw_id_fields = ("workspace", "created_by")
    ordering = ("-created",)

    @admin.display(description="Public URL")
    def public_url_preview(self, obj: MediaObject) -> str:
        url = obj.resolve_public_url()
        if not url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            url,
            url[:80] + ("…" if len(url) > 80 else ""),
        )
