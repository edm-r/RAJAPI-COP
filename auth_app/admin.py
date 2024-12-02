from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role')
    list_filter = UserAdmin.list_filter + ('role',)
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'newsletter_subscription')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'classes': ('wide',),
            'fields': ('role', 'phone_number', 'newsletter_subscription'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)