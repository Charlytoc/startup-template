from django.contrib import admin

from core.models import OrganizationMember


class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "status", "joined_at", "created")
    list_filter = ("status", "organization")
    search_fields = ("user__email", "organization__name")
    ordering = ("organization_id", "user_id")
    readonly_fields = ("created", "modified")
    raw_id_fields = ("user", "invited_by")
