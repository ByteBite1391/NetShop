"""
Accounts views — thin views, fat services.

Each view does only three things: parse input, call a service, shape the HTTP
response via the common response helpers. All business logic lives in
services/auth and is tested independently.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.auth import auth_service
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    TokenRefreshSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)
from apps.accounts.services import account_service, password_service
from apps.common.responses import created, fail, ok
from apps.core.exceptions import AuthenticationError


@extend_schema(tags=["auth"])
class RegisterView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer},
        description="Create a new customer account and issue an email-verification token.",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user, raw_token = account_service.register(
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        # In a real deployment a Celery task emails the verification link.
        # In dev (eager Celery) it would run synchronously; here we surface the
        # token only when DEBUG so tests/developers can verify the flow.
        from django.conf import settings

        envelope_data = UserSerializer(user).data
        if settings.DEBUG:
            envelope_data["verification_token"] = raw_token
        return created(
            data=envelope_data, message="Account created. Check your email to verify it."
        )


@extend_schema(tags=["auth"])
class LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=LoginSerializer,
        responses={200: OpenApiResponse(description="JWT tokens")},
        description="Authenticate with email + password and receive JWT access & refresh tokens.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, access, refresh = auth_service.login(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except AuthenticationError as exc:
            return fail(
                message=exc.message, errors={"code": exc.code}, status=status.HTTP_401_UNAUTHORIZED
            )
        return ok(
            data={
                "user": UserSerializer(user).data,
                "access": access,
                "refresh": refresh,
            },
            message="Login successful.",
        )


@extend_schema(tags=["auth"])
class TokenRefreshView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=TokenRefreshSerializer,
        responses={200: OpenApiResponse(description="Rotated JWT tokens")},
        description="Exchange a refresh token for a new access + refresh pair.",
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            access, refresh = auth_service.refresh(serializer.validated_data["refresh"])
        except AuthenticationError as exc:
            return fail(
                message=exc.message, errors={"code": exc.code}, status=status.HTTP_401_UNAUTHORIZED
            )
        return ok(data={"access": access, "refresh": refresh})


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=LogoutSerializer,
        responses={200: OpenApiResponse(description="Logged out")},
        description="Blacklist the given refresh token so it can no longer be rotated.",
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_service.logout(serializer.validated_data["refresh"])
        return ok(message="Logged out successfully.")


@extend_schema(tags=["auth"])
class EmailVerifyView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=EmailVerificationSerializer,
        responses={200: UserSerializer, 400: OpenApiResponse(description="Invalid/expired token")},
        description="Verify a user's email with the token emailed at registration.",
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = account_service.verify_email(serializer.validated_data["token"])
        return ok(data=UserSerializer(user).data, message="Email verified successfully.")


@extend_schema(tags=["auth"])
class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description="Reset email sent (if account exists)")},
        description="Request a password reset. Always returns 200 to prevent account enumeration.",
        examples=[
            OpenApiExample(
                "Always-200", value={"message": "If that email exists, a reset link has been sent."}
            )
        ],
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _user, raw_token = password_service.request_reset(serializer.validated_data["email"])
        from django.conf import settings

        # Celery would email the link here. In DEBUG we echo the token so the
        # flow is testable without an inbox.
        data = {}
        if settings.DEBUG and raw_token:
            data["reset_token"] = raw_token
        return ok(
            data=data,
            message="If that email exists, a reset link has been sent.",
        )


@extend_schema(tags=["auth"])
class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: UserSerializer, 400: OpenApiResponse(description="Invalid/expired token")},
        description="Reset a password using a reset token.",
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = password_service.reset_password(
            serializer.validated_data["token"],
            serializer.validated_data["new_password"],
        )
        return ok(data=UserSerializer(user).data, message="Password reset successfully.")


@extend_schema(tags=["users"])
class ProfileView(APIView):
    """The authenticated user's own profile."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={200: UserSerializer}, description="Retrieve the current user's profile."
    )
    def get(self, request):
        return ok(data=UserSerializer(request.user).data)

    @extend_schema(
        request=UpdateProfileSerializer,
        responses={200: UserSerializer},
        description="Update the current user's first/last name.",
    )
    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(data=UserSerializer(request.user).data, message="Profile updated.")


@extend_schema(tags=["users"])
class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(description="Password changed")},
        description="Change the current user's password (requires old password).",
    )
    def post(self, request):

        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not request.user.check_password(data["old_password"]):
            return fail(
                message="Current password is incorrect.",
                errors={"code": "bad_old_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Reuse reset_password logic by setting directly via the user object.
        request.user.set_password(data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        return ok(message="Password changed successfully.")
