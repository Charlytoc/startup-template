from django.contrib import admin


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'status', 'created', 'modified')
    list_filter = ('status', 'created')
    search_fields = ('name', 'domain')
    ordering = ('name',)
