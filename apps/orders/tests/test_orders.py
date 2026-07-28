"""Orders + payments API + service tests (checkout, stock, status, fake gateway)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cart.services import cart_service
from apps.core.exceptions import ValidationError
from apps.orders.models import OrderStatus
from apps.orders.services import order_service
from apps.payments.services import payment_service

pytestmark = pytest.mark.django_db

ADDRESS = {
    "full_name": "Alice Tester",
    "address_line": "1 Test St",
    "city": "Testville",
    "state": "TS",
    "postal_code": "12345",
    "country": "US",
}


class TestCheckout:
    def test_checkout_creates_order_and_decrements_stock(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("10.00"), stock=5)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 2)
        order = order_service.checkout(user, shipping_address=ADDRESS)
        assert order.status == OrderStatus.PENDING
        assert order.subtotal == Decimal("20.00")
        product.refresh_from_db()
        assert product.stock == 3
        # cart should be cleared
        assert cart.items.count() == 0
        # order item snapshot
        assert order.items.first().product_name == product.name

    def test_checkout_empty_cart_rejected(self, user):
        with pytest.raises(ValidationError):
            order_service.checkout(user, shipping_address=ADDRESS)

    def test_checkout_insufficient_stock_rolls_back(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("10.00"), stock=1)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 5)
        with pytest.raises(ValidationError):
            order_service.checkout(user, shipping_address=ADDRESS)
        # stock unchanged after rollback
        product.refresh_from_db()
        assert product.stock == 1
        # no order created
        assert user.orders.count() == 0

    def test_status_transition_forward(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("1.00"), stock=10)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        order = order_service.checkout(user, shipping_address=ADDRESS)
        order = order_service.transition_status(order, OrderStatus.PAID.value)
        assert order.status == OrderStatus.PAID
        order = order_service.transition_status(order, OrderStatus.FULFILLED.value)
        assert order.status == OrderStatus.FULFILLED

    def test_invalid_transition_rejected(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("1.00"), stock=10)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        order = order_service.checkout(user, shipping_address=ADDRESS)
        # PENDING -> DELIVERED is not allowed
        with pytest.raises(ValidationError):
            order_service.transition_status(order, OrderStatus.DELIVERED.value)


class TestCheckoutAPI:
    def test_checkout_authed(self, authed_client, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("5.00"), stock=10)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 2)
        resp = authed_client.post(
            "/api/v1/orders/checkout/",
            {"shipping_address": ADDRESS},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["status"] == "pending"


class TestPayments:
    def test_charge_succeeds_and_marks_order_paid(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("5.00"), stock=10)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        order = order_service.checkout(user, shipping_address=ADDRESS)
        payment = payment_service.charge(order.id, user=user)
        assert payment.status == "succeeded"
        order.refresh_from_db()
        assert order.status == OrderStatus.PAID

    def test_charge_fails_on_non_pending(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("5.00"), stock=10)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        order = order_service.checkout(user, shipping_address=ADDRESS)
        order_service.transition_status(order, OrderStatus.PAID.value)
        with pytest.raises(ValidationError):
            payment_service.charge(order.id, user=user)

    def test_refund_succeeded_payment(self, user):
        from tests.factories import ProductFactory

        product = ProductFactory(price=Decimal("5.00"), stock=10)
        cart = cart_service.get_or_create_cart(user=user)
        cart_service.add_item(cart, product.id, 1)
        order = order_service.checkout(user, shipping_address=ADDRESS)
        payment = payment_service.charge(order.id, user=user)
        payment = payment_service.refund(payment.id, user=user)
        assert payment.status == "refunded"
