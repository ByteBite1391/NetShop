"""
Cart domain models.

Cart design
-----------
We support both anonymous and authenticated carts with a single Cart model:

- Anonymous cart: `user` is NULL, identified by `session_key` (from the request
  session). The client passes the session key (or we create one) so the cart
  persists across page reloads before login.
- Authenticated cart: `user` is set, `session_key` is NULL.

Merge on login
--------------
When an anonymous user logs in with items in their cart, the service merges
the anonymous cart into their authenticated cart (sum quantities on duplicate
products) and clears the anonymous one. This happens via a signal/login hook.

Coupons
-------
A Coupon has a code, optional percentage or fixed discount, validity window,
and usage limits. Cart -> Coupon is a nullable FK: applying a coupon links it.
`tax_rate` on Cart is a Decimal percentage — tax-ready design. Tax is computed
at checkout time by the order service, not stored on the cart.

Cart items store the price snapshot at add time so historical prices don't
change if the product price changes mid-session; the *effective* price is
recomputed on read so discounts apply.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.products.models import Product


class Cart(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    coupon = models.ForeignKey(
        "cart.Coupon",
        on_delete=models.SET_NULL,
        related_name="carts",
        null=True,
        blank=True,
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Tax percentage, e.g. 8.25 for 8.25%.",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name="cart_must_have_user_or_session",
            ),
        ]

    def __str__(self) -> str:
        return f"Cart#{self.id} ({self.user or self.session_key})"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="unique_product_in_cart"),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product.name}"


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    description = models.CharField(max_length=200, blank=True)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Percentage discount (e.g. 10 for 10%). Leave null for fixed.",
    )
    fixed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Fixed amount off. Leave null for percentage.",
    )
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    @property
    def is_valid_now(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if not (self.valid_from <= now <= self.valid_to):
            return False
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return False
        return True
