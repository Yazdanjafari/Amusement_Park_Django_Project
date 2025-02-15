from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()  # Explicitly assign the custom User model to a variable

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("username", "first_name", "last_name", "get_role", "is_active", "is_staff", "is_superuser")

    # Overriding the save_model to enforce validation
    def save_model(self, request, obj, form, change):
        try:
            obj.clean()  # Run the clean method
        except ValidationError as e:
            # Raise validation error to admin interface
            form.add_error(None, e)
            return
        super().save_model(request, obj, form, change)

    fieldsets = (
        (
            'اطلاعات امنیتی',  # Redefine the personal information group
            {
                'fields': (
                    'username',
                    'password', 
                ),
            },
        ),
        (
            'اطلاعات شخصی',  # Redefine the personal information group
            {
                'fields': (
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
            'تاریخ ها',  # Group for important dates
            {
                'fields': (
                    'last_login',
                    'date_joined',
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'password1', 'password2', 'first_name', 'last_name'),
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