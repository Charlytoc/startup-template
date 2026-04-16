from django.contrib import admin

from core.models import IdentityAsset


class IdentityAssetAdmin(admin.ModelAdmin):
    list_display = ("label_or_type", "identity", "asset_type", "is_active", "created")
    list_filter = ("asset_type", "is_active", "identity__workspace__organization")
    search_fields = ("label", "identity__display_name", "media__title", "id")
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("identity", "created_by", "media")
    ordering = ("-created",)

    @admin.display(description="Label")
    def label_or_type(self, obj: IdentityAsset) -> str:
        return obj.label or obj.get_asset_type_display()
