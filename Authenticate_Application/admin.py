from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from Authenticate_Application.models import MyUser

admin.site.site_header = "پنل مدیریت وب اپلیکیشن شهربازی"
admin.site.site_title = "پنل مدیریت وب اپلیکیشن شهربازی"

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ['username', 'first_name', 'last_name', 'nationality_id', 'phone_number', 'duty', 'email', 'date_of_birth']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = MyUser
        fields = ['username', 'password', 'first_name', 'last_name', 'nationality_id', 'phone_number', 'duty', 'email', 'date_of_birth', 'is_active', 'is_staff', 'is_superuser', 'groups']  # Added 'groups' here


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ['username', 'first_name', 'last_name', 'nationality_id', 'phone_number', 'duty', 'email', 'date_of_birth', 'is_active', 'is_staff', 'is_superuser']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    
    fieldsets = [
        (None, {'fields': ['username', 'password']}), 
        ('Personal info', {'fields': ['first_name', 'last_name', 'nationality_id', 'phone_number', 'duty', 'email', 'date_of_birth']}), 
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups']}), 
    ]
    
    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': ['username', 'first_name', 'last_name', 'nationality_id', 'phone_number', 'email', 'date_of_birth', 'password1', 'password2', 'groups'],  # Added 'groups' here
        }),
    ]
    
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    filter_horizontal = ['groups']  

admin.site.register(MyUser, UserAdmin)
