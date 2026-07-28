"""Categories + brands API tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db

CAT_URL = "/api/v1/categories/"
BRAND_URL = "/api/v1/brands/"


class TestCategories:
    def test_list_public(self, api_client, user_factory):
        from tests.factories import CategoryFactory

        CategoryFactory(name="Electronics")
        CategoryFactory(name="Books")
        resp = api_client.get(CAT_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        names = [c["name"] for c in data]
        assert "Electronics" in names and "Books" in names

    def test_create_requires_staff(self, authed_client):
        resp = authed_client.post(CAT_URL, {"name": "Toys"}, format="json")
        # authed_client is a customer, not staff
        assert resp.status_code == 403

    def test_create_by_staff(self, staff_user, api_client):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(staff_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        resp = api_client.post(CAT_URL, {"name": "Garden"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["data"]["slug"] == "garden"

    def test_detail_by_slug(self, api_client, user_factory):
        from tests.factories import CategoryFactory

        cat = CategoryFactory(name="Music")
        resp = api_client.get(f"{CAT_URL}{cat.slug}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Music"


class TestBrands:
    def test_list_public(self, api_client):
        from tests.factories import BrandFactory

        BrandFactory(name="Acme")
        resp = api_client.get(BRAND_URL)
        assert resp.status_code == 200
        assert any(b["name"] == "Acme" for b in resp.json()["data"])

    def test_create_by_staff(self, staff_user, api_client):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(staff_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        resp = api_client.post(BRAND_URL, {"name": "NexBrand"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["data"]["slug"] == "nexbrand"
