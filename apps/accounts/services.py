"""
Accounts services — fat services, thin views.

All authentication business logic lives here so views stay trivial and the
logic is reusable from the admin, Celery tasks, and tests. Each service takes
the repositories it needs as constructor arguments (dependency injection) so
tests can swap in fakes without monkeypatching the ORM.

Token storage
-------------
Raw tokens are never persisted. We store `secrets.token_urlsafe()` output
*hashed* with hashlib; the raw token is returned to the caller (to email to
the user) and never read back. Verification compares hashes.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.repositories import TokenRepository, UserRepository
from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from apps.notifications.tasks import (
    send_password_reset_email,
    send_verification_email,
)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_token() -> tuple[str, str]:
    """Return (raw_token, token_hash). Only the hash is persisted."""
    raw = secrets.token_urlsafe(32)
    return raw, _hash_token(raw)


class AccountService:
    """Registration, email verification, and profile lookups."""

    def __init__(self, users: UserRepository, tokens: TokenRepository) -> None:
        self.users = users
        self.tokens = tokens

    @transaction.atomic
    def register(
        self, *, email: str, password: str, first_name: str = "", last_name: str = ""
    ) -> tuple[User, str]:
        """Create an unverified customer and issue an email-verification token.

        Returns (user, raw_token). The caller (view/task) is responsible for
        delivering the raw token — never persist it.
        """
        if self.users.email_exists(email):
            raise ConflictError("An account with this email already exists.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")

        user = self.users.create(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        raw_token, token_hash = _generate_token()
        self.tokens.create_activation_token(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=settings.ACCOUNT_VERIFICATION_TOKEN_HOURS),
        )
        send_verification_email.delay(
            user_email=user.email,
            first_name=user.first_name or user.email,
            token=raw_token,
        )
        return user, raw_token

    @transaction.atomic
    def verify_email(self, raw_token: str) -> User:
        token = self.tokens.get_activation_token(_hash_token(raw_token))
        if token is None:
            raise NotFoundError("Invalid verification token.")
        if token.is_used:
            raise ValidationError("This token has already been used.", code="token_used")
        if token.is_expired:
            raise ValidationError("This token has expired.", code="token_expired")

        user = token.user
        user.email_verified = True
        user.save(update_fields=["email_verified", "updated_at"])
        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])
        return user

    def get_profile(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user


class PasswordService:
    """Forgot-password / reset-password flow."""

    def __init__(self, users: UserRepository, tokens: TokenRepository) -> None:
        self.users = users
        self.tokens = tokens

    @transaction.atomic
    def request_reset(self, email: str) -> tuple[User | None, str | None]:
        """Issue a reset token if the user exists.

        We deliberately avoid revealing whether the email exists to prevent
        account enumeration. On an unknown email we return (None, None) and
        the caller sends nothing — but treats it the same to the client.
        """
        user = self.users.get_by_email(email)
        if user is None:
            return None, None
        raw_token, token_hash = _generate_token()
        self.tokens.create_password_reset_token(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_HOURS),
        )
        if user is not None and raw_token is not None:
            send_password_reset_email.delay(
                user_email=user.email,
                first_name=user.first_name or user.email,
                token=raw_token,
            )
        return user, raw_token

    @transaction.atomic
    def reset_password(self, raw_token: str, new_password: str) -> User:
        token = self.tokens.get_password_reset_token(_hash_token(raw_token))
        if token is None:
            raise NotFoundError("Invalid reset token.")
        if token.is_used:
            raise ValidationError("This token has already been used.", code="token_used")
        if token.is_expired:
            raise ValidationError("This token has expired.", code="token_expired")
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters.")

        user = token.user
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])
        return user


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
# Services are stateless and their repositories are cheap; a single instance
# per process is fine and keeps view code simple. Tests that need isolation
# instantiate services with their own repository/fake.
# ---------------------------------------------------------------------------

_users_repo = UserRepository()
_tokens_repo = TokenRepository()

from .auth import auth_service  # noqa: F401  (re-exported for convenience)

account_service = AccountService(users=_users_repo, tokens=_tokens_repo)
password_service = PasswordService(users=_users_repo, tokens=_tokens_repo)
