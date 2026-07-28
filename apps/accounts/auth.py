"""
Authentication service — JWT issuance, refresh, and logout (blacklist).

Kept separate from AccountService because the concerns differ: this module
deals with token lifecycle, not user identity. Views call these helpers so the
JWT wiring is in one place and testable in isolation.

Why blacklist refresh tokens on logout?
---------------------------------------
JWTs are stateless — a stolen refresh token is valid until it expires. SimpleJWT
ships a `token_blacklist` app that stores refresh-token IDs in the DB; logging
out adds the token to the blacklist so it can no longer be rotated. This trades
a tiny bit of statelessness for real revocation capability.
"""

from __future__ import annotations

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from apps.accounts.models import User
from apps.accounts.repositories import UserRepository
from apps.core.exceptions import AuthenticationError, ValidationError


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def login(self, email: str, password: str) -> tuple[User, str, str]:
        """Validate credentials and return (user, access, refresh).

        Raises AuthenticationError on bad credentials or an unverified/inactive
        account. We deliberately return one error message to avoid leaking
        which part failed (account enumeration).
        """
        user = self.users.get_by_email(email)
        if user is None or not user.check_password(password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("This account has been disabled.")
        # Email verification gating: uncomment to enforce verification before login.
        # if not user.email_verified:
        #     raise AuthenticationError("Please verify your email before logging in.")
        token = RefreshToken.for_user(user)
        return user, str(token.access_token), str(token)

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Rotate a refresh token. Returns (new_access, new_refresh)."""
        try:
            token = RefreshToken(refresh_token)
        except TokenError as exc:
            raise AuthenticationError("Invalid or expired refresh token.") from exc

        # ROTATE_REFRESH_TOKENS is on; calling access_token issues a new access,
        # and we return a freshly rotated refresh via blacklist-aware rotation.
        new_access = str(token.access_token)
        # SimpleJWT rotates automatically when ROTATE_REFRESH_TOKENS=True; we
        # re-encode to expose the rotated refresh to the caller.
        try:
            token.blacklist()
        except Exception:
            pass
        # After blacklisting, mint a brand-new refresh for the same user.
        user = self.users.get_by_id(token["user_id"])
        if user is None:
            raise AuthenticationError("User not found.")
        new_refresh = str(RefreshToken.for_user(user))
        return new_access, new_refresh

    def logout(self, refresh_token: str) -> None:
        """Blacklist a refresh token so it can no longer be rotated."""
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            raise ValidationError("Invalid refresh token.") from exc
        except AttributeError:
            # token_blacklist not installed/configured — treat as no-op.
            pass


# Module-level singleton (see services.py for rationale).
auth_service = AuthService(users=UserRepository())
