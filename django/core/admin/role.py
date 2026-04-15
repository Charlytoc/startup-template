from django.contrib import admin

from core.models import Role


class RoleAdmin(admin.ModelAdmin):
    list_display = ("display_name", "slug", "organization", "created", "modified")
    list_filter = ("organization",)
    search_fields = ("display_name", "slug", "organization__name")
    ordering = ("organization_id", "slug")
    readonly_fields = ("created", "modified")
