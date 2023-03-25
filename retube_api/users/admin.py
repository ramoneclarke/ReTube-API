from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUserModel



class CustomUserAdmin(UserAdmin):
    model = CustomUserModel
    # Customize the display columns in the list view
    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ['is_staff']
    # Customize the edit form
    fieldsets = (
        (None, {'fields': ('email', 'password', 'username')}),
        ('Personal Info', {'fields': ()}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    # Customize the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username' 'email', 'password1', 'password2'),
        }),
    )
    # Customize the search fields
    search_fields = ('username', 'email')
    # Customize the ordering in the list view
    ordering = ('email', 'username')

# Register the custom user model and the new admin class
admin.site.register(CustomUserModel, CustomUserAdmin)
