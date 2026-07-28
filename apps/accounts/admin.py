"""Admin registration for the accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import EmailActivationToken, PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Adapt Django's UserAdmin to our email-based custom user."""

    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "email_verified",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "email_verified", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Verification", {"fields": ("email_verified",)}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")


@admin.register(EmailActivationToken)
class EmailActivationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "is_used")
    search_fields = ("user__email",)
    readonly_fields = ("token_hash", "created_at", "updated_at")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "is_used")
    search_fields = ("user__email",)
    readonly_fields = ("token_hash", "created_at", "updated_at")
