"""Shared pytest fixtures available to every test in the project."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.constants import UserRole


@pytest.fixture(autouse=True)
def _enable_debug_token_echo(settings):
    """Let auth views echo verification/reset tokens during tests so the flows
    are exercisable end-to-end without a real email inbox."""
    settings.DEBUG = True


@pytest.fixture
def api_client() -> APIClient:
    """A fresh DRF API client with no auth."""
    return APIClient()


@pytest.fixture
def authed_client(api_client: APIClient, user: User) -> APIClient:
    """API client authenticated as `user`."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def user_factory(db):
    """Factory function that builds users with sensible defaults."""
    from tests.factories import UserFactory

    return UserFactory


@pytest.fixture
def user(user_factory) -> User:
    """A single regular customer user."""
    return user_factory()


@pytest.fixture
def admin_user(user_factory) -> User:
    return user_factory(role=UserRole.ADMIN, is_staff=True, is_superuser=True, email_verified=True)


@pytest.fixture
def staff_user(user_factory) -> User:
    return user_factory(role=UserRole.STAFF, is_staff=True, email_verified=True)
