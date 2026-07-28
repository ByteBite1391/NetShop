"""Accounts API routes — mounted under /api/v1/ by config/urls.py."""

from django.urls import path

from apps.accounts.views import (
    ChangePasswordView,
    EmailVerifyView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    TokenRefreshView,
)

app_name = "accounts"

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/email/verify/", EmailVerifyView.as_view(), name="email-verify"),
    path("auth/password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    # Profile
    path("me/", ProfileView.as_view(), name="me"),
    path("me/password/", ChangePasswordView.as_view(), name="change-password"),
]
