"""
Accounts repositories — data access only.

Repositories encapsulate persistence so services stay ORM-light and the query
seams are obvious. For trivial CRUD we lean on the ORM directly inside the
service; these helpers exist where the query is non-trivial or reused.
"""

from __future__ import annotations

from typing import Protocol

from django.db.models import QuerySet

from apps.accounts.models import EmailActivationToken, PasswordResetToken, User


class IUserRepository(Protocol):
    """Protocol describing the user data-access surface services depend on."""

    def get_by_email(self, email: str) -> User | None: ...
    def get_by_id(self, user_id: int) -> User | None: ...
    def email_exists(self, email: str) -> bool: ...
    def create(self, **fields) -> User: ...
    def save(self, user: User) -> User: ...


class UserRepository:
    """Concrete repository backed by the Django ORM."""

    def get_by_email(self, email: str) -> User | None:
        return User.objects.filter(email__iexact=email).first()

    def get_by_id(self, user_id: int) -> User | None:
        return User.objects.filter(id=user_id).first()

    def email_exists(self, email: str) -> bool:
        return User.objects.filter(email__iexact=email).exists()

    def create(self, **fields) -> User:
        return User.objects.create_user(**fields)

    def save(self, user: User) -> User:
        user.save()
        return user

    def all_active(self) -> QuerySet[User]:
        return User.objects.filter(is_active=True)


class TokenRepository:
    """Persistence for email-activation and password-reset tokens."""

    def create_activation_token(
        self, user: User, token_hash: str, expires_at
    ) -> EmailActivationToken:
        return EmailActivationToken.objects.create(
            user=user, token_hash=token_hash, expires_at=expires_at
        )

    def get_activation_token(self, token_hash: str) -> EmailActivationToken | None:
        return (
            EmailActivationToken.objects.select_related("user")
            .filter(token_hash=token_hash)
            .first()
        )

    def create_password_reset_token(
        self, user: User, token_hash: str, expires_at
    ) -> PasswordResetToken:
        return PasswordResetToken.objects.create(
            user=user, token_hash=token_hash, expires_at=expires_at
        )

    def get_password_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        return (
            PasswordResetToken.objects.select_related("user").filter(token_hash=token_hash).first()
        )
