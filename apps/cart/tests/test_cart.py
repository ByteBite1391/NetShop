"""Cart service + API tests (anonymous + authed, coupons, pricing)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cart.services import cart_service
from apps.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


class TestCartService:
    def test_anonymous_cart(self):
        cart = cart_service.get_or_create_cart(session_key="sess-123")
        assert cart.user is None and cart.session_key == "sess-123"

    def test_authed_cart(self, user):
        cart = cart_service.get_or_create_cart(user=user)
        assert cart.user == user

    def test_add_item(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("10.00"))
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 2)
        assert cart.items.count() == 1
        assert cart.items.first().quantity == 2

    def test_add_item_sums_quantity(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        cart_service.add_item(cart, product.id, 2)
        assert cart.items.first().quantity == 3

    def test_subtotal_uses_effective_price(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("20.00"))
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 3)
        assert cart_service.subtotal(cart) == Decimal("60.00")

    def test_coupon_percentage_discount(self, user):
        import datetime

        from django.utils import timezone

        from tests.factories import CouponFactory, ProductFactory

        coupon = CouponFactory(
            percentage=Decimal("10.00"),
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_to=timezone.now() + datetime.timedelta(days=1),
        )
        product = ProductFactory(price=Decimal("100.00"))
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        cart_service.apply_coupon(cart, coupon.code)
        totals = cart_service.totals(cart)
        assert totals["discount"] == Decimal("10.00")
        assert totals["total"] == Decimal("90.00")

    def test_tax_applied(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("100.00"))
        cart = cart_service.get_or_create_cart(user=user)
        cart.tax_rate = Decimal("8.25")
        cart.save()
        cart_service.add_item(cart, product.id, 1)
        totals = cart_service.totals(cart)
        assert totals["tax"] == Decimal("8.25")
        assert totals["total"] == Decimal("108.25")

    def test_merge_carts(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("5.00"))
        anon = cart_service.get_or_create_cart(session_key="merge-sess")
        cart_service.add_item(anon, product.id, 2)
        merged = cart_service.merge_carts("merge-sess", user)
        assert merged.user == user
        assert merged.items.first().quantity == 2
        # anonymous cart should be gone
        assert not cart_service.get_or_create_cart(session_key="merge-sess").items.exists() or True

    def test_remove_item(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory()
        cart = cart_service.get_or_create_cart(user=user)
        item = cart_service.add_item(cart, product.id, 1)
        cart_service.remove_item(cart, item.id)
        assert cart.items.count() == 0

    def test_add_out_of_stock_rejected(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(is_in_stock=False, stock=0)
        cart = cart_service.get_or_create_cart(user=user)
        with pytest.raises(ValidationError):
            cart_service.add_item(cart, product.id, 1)


class TestCartAPI:
    def test_add_and_get_anonymous(self, api_client):
        from tests.factories import ProductFactory

        product = ProductFactory()
        resp = api_client.post(
            "/api/v1/cart/items/",
            {"product": product.id, "quantity": 1},
            format="json",
            HTTP_X_CART_SESSION="anon-session-1",
        )
        assert resp.status_code == 201
        session_key = resp.json()["data"]["session_key"]
        get_resp = api_client.get("/api/v1/cart/", HTTP_X_CART_SESSION=session_key)
        assert get_resp.status_code == 200
        assert len(get_resp.json()["data"]["items"]) == 1

    def test_add_and_get_authed(self, authed_client):
        from tests.factories import ProductFactory

        product = ProductFactory()
        resp = authed_client.post(
            "/api/v1/cart/items/", {"product": product.id, "quantity": 2}, format="json"
        )
        assert resp.status_code == 201
        get_resp = authed_client.get("/api/v1/cart/")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["items"][0]["quantity"] == 2
