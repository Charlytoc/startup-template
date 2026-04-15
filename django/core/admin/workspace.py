from django.contrib import admin

from core.models import Workspace


class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "created", "modified")
    list_filter = ("organization",)
    search_fields = ("name", "organization__name")
    ordering = ("organization_id", "name")
    readonly_fields = ("created", "modified")
