r"""
Order domain models.

Order lifecycle
---------------
PENDING -> PAID -> FULFILLED -> SHIPPED -> DELIVERED
                  \-> CANCELLED  (can be cancelled before fulfilment)

Addresses are stored as snapshot fields on the Order (not FKs to an address
book) so an order's shipping address is immutable even if the user edits their
address book later — a critical e-commerce invariant.

OrderItem stores the price at purchase time (price_snapshot) plus the
effective price paid. Money is Decimal.
"""

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.core.constants import AccountStatus  # noqa: F401 (kept for enum parity)


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FULFILLED = "fulfilled", "Fulfilled"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class Order(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )

    # Address snapshots (immutable post-checkout).
    shipping_full_name = models.CharField(max_length=160)
    shipping_address_line = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=120)
    shipping_state = models.CharField(max_length=120)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=80)
    shipping_phone = models.CharField(max_length=30, blank=True)

    billing_full_name = models.CharField(max_length=160)
    billing_address_line = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=120)
    billing_state = models.CharField(max_length=120)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=80)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    coupon_code = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self) -> str:
        return f"{self.order_number} ({self.status})"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    product_name = models.CharField(max_length=200)  # snapshot in case product is later edited
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # effective price paid
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_name}"
