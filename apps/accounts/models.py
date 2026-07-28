"""
Custom user model.

Why a custom user model?
------------------------
Django's built-in `User` is username-centric and hard to reshape once in
production. The official guidance is to start with a custom user before the
first migration — because `AUTH_USER_MODEL` cannot be cleanly changed after
tables exist. We make `email` the unique identifier and drop the username
field entirely; e-commerce customers log in with email, not a handle.

Roles
-----
A `role` field (admin / staff / customer) drives authz. We use TextChoices
for DB-level validation and easy display in the admin. RBAC is enforced via
the permission classes in apps.common.permissions.

Email verification & password reset
-----------------------------------
We store opaque tokens (not JWTs) with an expiry. Tokens are single-use and
hashed at rest so a DB read doesn't leak reusable credentials. This is
deliberately separate from the JWT auth tokens.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.core.constants import UserRole


class UserManager(BaseUserManager):
    """Manager for the email-based user model.

    `createsuperuser` is invoked by `manage.py createsuperuser`; it must set
    the admin role and `is_staff`/`is_superuser` so the Django admin works.
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("role", UserRole.CUSTOMER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Email-based user with role and email-verification state."""

    class Role(models.TextChoices):
        ADMIN = UserRole.ADMIN.value, "Admin"
        STAFF = UserRole.STAFF.value, "Staff"
        CUSTOMER = UserRole.CUSTOMER.value, "Customer"

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    role = models.CharField(
        max_length=16, choices=Role.choices, default=Role.CUSTOMER, db_index=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # email is the only required field for superuser

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["role", "is_active"])]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class EmailActivationToken(TimeStampedModel):
    """Single-use token for email verification.

    Tokens are random and stored hashed so a database read cannot leak a
    reusable credential. We compare hashes, not raw tokens.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activation_tokens")
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_used(self) -> bool:
        return self.used_at is not None


class PasswordResetToken(TimeStampedModel):
    """Single-use token for password reset, same storage pattern as above."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_used(self) -> bool:
        return self.used_at is not None
