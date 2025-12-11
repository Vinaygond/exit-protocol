from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, LoginHistory

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "is_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("date_joined", "last_login", "password_changed_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_verified", "groups", "user_permissions")}),
        ("Security", {"fields": ("failed_login_attempts", "last_failed_login", "password_changed_at")}),
        ("Timestamps", {"fields": ("date_joined", "last_login")}),
    )

@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "state", "timezone", "notifications_enabled")
    search_fields = ("user__email", "city", "state", "law_firm")

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp", "ip_address", "success", "country", "city")
    search_fields = ("user__email", "ip_address")
    ordering = ("-timestamp",)
