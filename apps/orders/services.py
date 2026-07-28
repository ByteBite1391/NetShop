"""
Orders service — checkout, status transitions, atomicity.

Checkout flow
-------------
1. Resolve the user's cart.
2. Compute totals via cart_service.
3. In a single atomic transaction: create the Order + OrderItems, decrement
   product stock for each item, mark the coupon as used, and clear the cart.
   If any step fails the whole checkout rolls back — no partial orders, no
   negative stock.
4. Return the order. Payment is handled separately by the payments app.

Order numbers are generated as NXC-<timestamp>-<random> and guaranteed unique
via a DB unique constraint.
"""

from __future__ import annotations

import secrets
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.cart.services import cart_service
from apps.core.exceptions import NotFoundError, ValidationError
from apps.notifications.tasks import send_order_confirmation_email
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.products.services import product_service


class OrderService:
    def _generate_order_number(self) -> str:
        ts = timezone.now().strftime("%Y%m%d%H%M%S")
        suffix = secrets.token_hex(3).upper()
        candidate = f"NXC-{ts}-{suffix}"
        while Order.objects.filter(order_number=candidate).exists():
            suffix = secrets.token_hex(3).upper()
            candidate = f"NXC-{ts}-{suffix}"
        return candidate

    @transaction.atomic
    def checkout(
        self,
        user,
        *,
        shipping_address: dict[str, Any],
        billing_address: dict[str, Any] | None = None,
        shipping_fee: Decimal = Decimal("0.00"),
    ) -> Order:
        cart = cart_service.get_or_create_cart(user=user)
        if not cart.items.exists():
            raise ValidationError("Cannot checkout an empty cart.")

        billing = billing_address or shipping_address
        totals = cart_service.totals(cart)

        order = Order.objects.create(
            user=user,
            order_number=self._generate_order_number(),
            status=OrderStatus.PENDING,
            shipping_full_name=shipping_address["full_name"],
            shipping_address_line=shipping_address["address_line"],
            shipping_city=shipping_address["city"],
            shipping_state=shipping_address["state"],
            shipping_postal_code=shipping_address["postal_code"],
            shipping_country=shipping_address["country"],
            shipping_phone=shipping_address.get("phone", ""),
            billing_full_name=billing["full_name"],
            billing_address_line=billing["address_line"],
            billing_city=billing["city"],
            billing_state=billing["state"],
            billing_postal_code=billing["postal_code"],
            billing_country=billing["country"],
            subtotal=totals["subtotal"],
            discount=totals["discount"],
            tax=totals["tax"],
            shipping_fee=Decimal(shipping_fee),
            total=totals["total"] + Decimal(shipping_fee),
            coupon_code=cart.coupon.code if cart.coupon else "",
        )

        for item in cart.items.select_related("product"):
            unit_price = product_service.get_effective_price(item.product)
            line_total = (unit_price * item.quantity).quantize(Decimal("0.01"))
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
            # Decrement stock atomically inside the same transaction.
            product_service.decrease_stock(item.product, item.quantity)

        # Mark coupon used.
        if cart.coupon is not None:
            cart.coupon.times_used += 1
            cart.coupon.save(update_fields=["times_used", "updated_at"])

        # Clear the cart.
        cart_service.clear(cart)
        # Notify the customer (queued via Celery; eager in dev).
        send_order_confirmation_email.delay(
            user_email=user.email,
            first_name=user.first_name or user.email,
            order_number=order.order_number,
            total=str(order.total),
        )
        return order

    def get(self, order_id: int, user) -> Order:
        order = Order.objects.filter(id=order_id, user=user).first()
        if order is None:
            raise NotFoundError("Order not found.")
        return order

    def list_for_user(self, user):
        return Order.objects.filter(user=user).order_by("-created_at")

    @transaction.atomic
    def transition_status(self, order: Order, new_status: str) -> Order:
        valid = {s.value for s in OrderStatus}
        if new_status not in valid:
            raise ValidationError(f"Invalid status: {new_status}.")
        # Enforce a simple forward-only transition graph.
        graph = {
            OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
            OrderStatus.PAID: {OrderStatus.FULFILLED, OrderStatus.CANCELLED},
            OrderStatus.FULFILLED: {OrderStatus.SHIPPED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
            OrderStatus.DELIVERED: set(),
            OrderStatus.CANCELLED: set(),
        }
        allowed = graph.get(order.status, set())
        if new_status not in allowed and new_status != order.status:
            raise ValidationError(f"Cannot transition order from {order.status} to {new_status}.")
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        return order

    def get_for_admin(self, order_id: int) -> Order:
        order = Order.objects.filter(id=order_id).first()
        if order is None:
            raise NotFoundError("Order not found.")
        return order


order_service = OrderService()
