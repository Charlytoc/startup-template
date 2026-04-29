from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.conf import settings
from django.core.files import File
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import os
from core.services.openai_service import OpenAIService

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'organization', 'is_active', 'is_staff', 'created')
    list_filter = ('is_active', 'is_staff', 'organization', 'created')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('created', 'modified', 'profile_picture_preview')
    ordering = ('-created',)
    actions = ['generate_profile_picture']
    
    fieldsets = (
        (None, {'fields': ('email','password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'profile_picture', 'profile_picture_preview')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Organization', {'fields': ('organization',)}),
        ('Important dates', {'fields': ('last_login', 'created', 'modified')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'organization'),
        }),
    )

    def generate_profile_picture(self, request, queryset):
        """
        Generate profile pictures for selected users using AI
        """
        if not settings.OPENAI_API_KEY:
            self.message_user(request, "OpenAI API key not configured", level=messages.ERROR)
            return

        openai_service = OpenAIService(settings.OPENAI_API_KEY)
        success_count = 0
        error_count = 0

        for user in queryset:
            try:
                # Create a description for the user based on available info
                description_parts = []
                if user.first_name:
                    description_parts.append(f"name: {user.first_name}")
                if user.last_name:
                    description_parts.append(f"surname: {user.last_name}")
                
                # Add some generic professional characteristics
                description_parts.append("professional, friendly, approachable")
                
                user_description = ", ".join(description_parts) if description_parts else "professional person"
                
                # Generate the image
                image_path = openai_service.generate_profile_avatar(
                    user_description=user_description,
                    output_dir=os.path.join(settings.MEDIA_ROOT, 'users', 'profile_pictures')
                )
                
                if image_path and os.path.exists(image_path):
                    # Save the image to the user's profile_picture field
                    with open(image_path, 'rb') as f:
                        user.profile_picture.save(
                            os.path.basename(image_path),
                            File(f),
                            save=True
                        )
                    
                    # Clean up the temporary file
                    os.remove(image_path)
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                self.message_user(
                    request, 
                    f"Error generating profile picture for {user.email}: {str(e)}", 
                    level=messages.ERROR
                )
                error_count += 1

        if success_count > 0:
            self.message_user(
                request, 
                f"Successfully generated {success_count} profile picture(s)", 
                level=messages.SUCCESS
            )
        
        if error_count > 0:
            self.message_user(
                request, 
                f"Failed to generate {error_count} profile picture(s)", 
                level=messages.WARNING
            )

    generate_profile_picture.short_description = "Generate AI profile picture"

    def profile_picture_preview(self, obj):
        """Display profile picture preview in admin"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.profile_picture.url
            )
        return mark_safe('<span style="color: #999;">No image uploaded</span>')
    
    profile_picture_preview.short_description = "Profile Picture Preview"
    