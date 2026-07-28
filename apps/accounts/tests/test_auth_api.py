"""
Auth + profile API tests.

Covers the HTTP layer: status codes, the consistent response envelope, JWT
issuance, and the profile endpoints. These complement the service tests.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
VERIFY_URL = "/api/v1/auth/email/verify/"
RESET_URL = "/api/v1/auth/password/reset/"
RESET_CONFIRM_URL = "/api/v1/auth/password/reset/confirm/"
ME_URL = "/api/v1/me/"
CHANGE_PW_URL = "/api/v1/me/password/"


class TestRegisterAPI:
    def test_creates_account(self, api_client):
        resp = api_client.post(
            REGISTER_URL,
            {"email": "api@example.com", "password": "Str0ngP@ss!", "first_name": "Api"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["email"] == "api@example.com"
        assert body["data"]["role"] == "customer"
        assert body["data"]["email_verified"] is False
        # DEBUG mode exposes the verification token so tests can continue the flow.
        assert "verification_token" in body["data"]

    def test_rejects_duplicate(self, user_factory, api_client):
        user_factory(email="dup@example.com")
        resp = api_client.post(
            REGISTER_URL, {"email": "dup@example.com", "password": "Str0ngP@ss!"}, format="json"
        )
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_rejects_weak_password(self, api_client):
        resp = api_client.post(
            REGISTER_URL, {"email": "weak@example.com", "password": "12345"}, format="json"
        )
        assert resp.status_code == 400


class TestLoginAPI:
    def test_login_succeeds_with_verified_user(self, user_factory, api_client):
        user_factory(email="login@example.com", password="Str0ngP@ss!")
        resp = api_client.post(
            LOGIN_URL, {"email": "login@example.com", "password": "Str0ngP@ss!"}, format="json"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access" in data and "refresh" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_fails_with_wrong_password(self, user_factory, api_client):
        user_factory(email="login2@example.com", password="Str0ngP@ss!")
        resp = api_client.post(
            LOGIN_URL, {"email": "login2@example.com", "password": "wrong"}, format="json"
        )
        assert resp.status_code == 401
        assert resp.json()["success"] is False


class TestEmailVerifyAPI:
    def test_verifies_email(self, api_client):
        reg = api_client.post(
            REGISTER_URL, {"email": "ver@example.com", "password": "Str0ngP@ss!"}, format="json"
        )
        token = reg.json()["data"]["verification_token"]
        resp = api_client.post(VERIFY_URL, {"token": token}, format="json")
        assert resp.status_code == 200
        assert resp.json()["data"]["email_verified"] is True


class TestTokenRefreshAPI:
    def test_refresh_rotates_tokens(self, user_factory, api_client):
        user_factory(email="rf@example.com", password="Str0ngP@ss!")
        login = api_client.post(
            LOGIN_URL, {"email": "rf@example.com", "password": "Str0ngP@ss!"}, format="json"
        )
        refresh = login.json()["data"]["refresh"]
        resp = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")
        assert resp.status_code == 200
        assert "access" in resp.json()["data"]


class TestProfileAPI:
    def test_requires_auth(self, api_client):
        resp = api_client.get(ME_URL)
        assert resp.status_code == 401

    def test_returns_profile(self, authed_client, user):
        # `authed_client` is authenticated as `user`.
        resp = authed_client.get(ME_URL)
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == user.email

    def test_updates_profile(self, authed_client):
        resp = authed_client.patch(ME_URL, {"first_name": "NewName"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["data"]["first_name"] == "NewName"


class TestChangePasswordAPI:
    def test_changes_password(self, authed_client, user):
        user.set_password("OldP@ss123")
        user.save()
        resp = authed_client.post(
            CHANGE_PW_URL,
            {"old_password": "OldP@ss123", "new_password": "N3wP@ss!!"},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("N3wP@ss!!")

    def test_rejects_wrong_old_password(self, authed_client):
        resp = authed_client.post(
            CHANGE_PW_URL, {"old_password": "wrong", "new_password": "N3wP@ss!!"}, format="json"
        )
        assert resp.status_code == 400


class TestPasswordResetAPI:
    def test_full_reset_flow(self, user_factory, api_client):
        user_factory(email="flow@example.com", password="Str0ngP@ss!")
        req = api_client.post(RESET_URL, {"email": "flow@example.com"}, format="json")
        assert req.status_code == 200
        token = req.json()["data"]["reset_token"]
        confirm = api_client.post(
            RESET_CONFIRM_URL, {"token": token, "new_password": "N3wP@ss!!"}, format="json"
        )
        assert confirm.status_code == 200

        login = api_client.post(
            LOGIN_URL, {"email": "flow@example.com", "password": "N3wP@ss!!"}, format="json"
        )
        assert login.status_code == 200

    def test_reset_request_does_not_leak_account_existence(self, api_client):
        # Both unknown and known emails must return the same response.
        r1 = api_client.post(RESET_URL, {"email": "ghost@example.com"}, format="json")
        r2 = api_client.post(RESET_URL, {"email": "another@example.com"}, format="json")
        assert r1.status_code == r2.status_code == 200
        assert r1.json()["message"] == r2.json()["message"]
