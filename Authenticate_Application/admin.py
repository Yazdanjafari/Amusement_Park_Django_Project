from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError

User = get_user_model()  # Explicitly assign the custom User model to a variable

class CustomUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "get_role", "is_active", "is_staff", "is_superuser" )


    fieldsets = (
        (
            'اطلاعات شخصی',  # Redefine the personal information group
            {
                'fields': (
                    'username',
                    'first_name',
                    'last_name',
                    'nationality_id',
                    'phone_number',
                    'date_of_birth',
                    'email',
                ),
            },
        ),
        (
            'نقش کاربری',  # Group heading for role information
            {
                'fields': (
                    'role',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'categories',
                ),
            },
        ),
        (
            'Permissions',  # Include permissions if needed
            {
                'fields': (
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (
            'Important dates',  # Group for important dates
            {
                'fields': (
                    'last_login',
                    'date_joined',
                ),
            },
        ),
    )

    # Method to display role in list_display
    def get_role(self, obj):
        return obj.get_role_display()

    get_role.short_description = 'نوع دسترسی کاربر'

    # To access the `get_categories` method in list_display
    def get_categories_display(self, obj):
        return obj.get_categories()

    get_categories_display.short_description = 'Categories'  # Optional: set a custom column name in the admin

# Unregister the default User model only if it was registered previously
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Register the custom User model with the custom admin
admin.site.register(User, CustomUserAdmin)
