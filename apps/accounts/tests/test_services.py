"""
Service-layer unit tests for accounts.

These tests exercise the business logic directly (no HTTP) so failures point
at the rule, not the plumbing. API behaviour is covered in test_auth_api.py.
"""

from __future__ import annotations

import pytest

from apps.accounts.services import account_service, password_service
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    def test_creates_unverified_customer(self):
        user, raw_token = account_service.register(email="bob@example.com", password="Str0ngP@ss!")
        assert user.email == "bob@example.com"
        assert user.role == "customer"
        assert user.email_verified is False
        assert raw_token  # token returned to caller

    def test_rejects_duplicate_email(self, user_factory):
        user_factory(email="dup@example.com")
        with pytest.raises(ConflictError):
            account_service.register(email="dup@example.com", password="Str0ngP@ss!")

    def test_rejects_short_password(self):
        with pytest.raises(ValidationError):
            account_service.register(email="short@example.com", password="123")


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


class TestVerifyEmail:
    def test_verifies_with_valid_token(self):
        user, raw_token = account_service.register(email="v@example.com", password="Str0ngP@ss!")
        verified = account_service.verify_email(raw_token)
        assert verified.email_verified is True
        assert verified.id == user.id

    def test_rejects_unknown_token(self):
        with pytest.raises(NotFoundError):
            account_service.verify_email("not-a-real-token")

    def test_rejects_reused_token(self):
        _, raw_token = account_service.register(email="r@example.com", password="Str0ngP@ss!")
        account_service.verify_email(raw_token)
        with pytest.raises(ValidationError):
            account_service.verify_email(raw_token)


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


class TestPasswordReset:
    def test_request_returns_token_for_known_user(self, user_factory):
        user_factory(email="pr@example.com")
        found, raw_token = password_service.request_reset("pr@example.com")
        assert found is not None and raw_token

    def test_request_returns_none_for_unknown_email(self):
        found, raw_token = password_service.request_reset("nobody@example.com")
        assert found is None and raw_token is None

    def test_reset_changes_password(self, user_factory):
        user_factory(email="rp@example.com")
        _, raw_token = password_service.request_reset("rp@example.com")
        updated = password_service.reset_password(raw_token, "N3wP@ss!!")
        updated.refresh_from_db()
        assert updated.check_password("N3wP@ss!!")

    def test_reset_rejects_short_password(self, user_factory):
        user_factory(email="rp2@example.com")
        _, raw_token = password_service.request_reset("rp2@example.com")
        with pytest.raises(ValidationError):
            password_service.reset_password(raw_token, "123")

    def test_reset_rejects_reused_token(self, user_factory):
        user_factory(email="rp3@example.com")
        _, raw_token = password_service.request_reset("rp3@example.com")
        password_service.reset_password(raw_token, "N3wP@ss!!")
        with pytest.raises(ValidationError):
            password_service.reset_password(raw_token, "N3wP@ss22")
