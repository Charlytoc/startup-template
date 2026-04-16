from django.contrib import admin

from core.models import IdentityType


class IdentityTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "created_by", "created", "modified")
    list_filter = ("organization",)
    search_fields = ("name", "description")
    readonly_fields = ("created", "modified")
    raw_id_fields = ("organization", "created_by")
    ordering = ("organization_id", "name")
