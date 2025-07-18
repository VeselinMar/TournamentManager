from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppUser

class CustomUserAdmin(UserAdmin):
    model = AppUser
    list_display = ['email', 'is_staff', 'is_superuser']
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('email',)

admin.site.register(AppUser, CustomUserAdmin)