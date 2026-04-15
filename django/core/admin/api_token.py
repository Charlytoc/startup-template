from django.contrib import admin


class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'token_preview', 'is_active', 'expires_at', 'last_used_at', 'created')
    list_filter = ('is_active', 'created', 'expires_at')
    search_fields = ('user__email', 'name', 'token')
    readonly_fields = ('token', 'created', 'modified', 'last_used_at')
    ordering = ('-created',)
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'token')}),
        ('Access', {'fields': ('capabilities',)}),
        ('Status', {'fields': ('is_active', 'expires_at', 'last_used_at')}),
        ('Timestamps', {'fields': ('created', 'modified')}),
    )
    
    def token_preview(self, obj):
        """Show first 8 characters of token for identification"""
        return f"{obj.token[:8]}..." if obj.token else "-"
    token_preview.short_description = "Token Preview"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
