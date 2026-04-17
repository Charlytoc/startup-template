from django.contrib import admin


class IntegrationBridgeAdmin(admin.ModelAdmin):
    list_display = ("identity", "integration_account", "is_active", "created")
    list_filter = (
        "is_active",
        "integration_account__provider",
        "identity__workspace__organization",
    )
    search_fields = (
        "identity__display_name",
        "integration_account__display_name",
        "integration_account__external_account_id",
        "id",
    )
    readonly_fields = ("id", "created", "modified")
    raw_id_fields = ("identity", "integration_account")
    ordering = ("-created",)
