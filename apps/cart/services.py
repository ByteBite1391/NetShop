"""
Cart service — the core pricing and merge logic.

Pricing flow
------------
1. Each CartItem has a `price_snapshot` (the product price at add time).
2. On read, we recompute the *effective* unit price using the product service
   (so active discounts apply), then multiply by quantity.
3. Subtotal = sum of effective line totals.
4. Coupon discount applies to subtotal.
5. Tax = (subtotal - discount) * tax_rate / 100.
6. Total = subtotal - discount + tax.

Merge on login
--------------
`merge_carts` moves anonymous-cart items into the authenticated cart, summing
quantities for products present in both, then deletes the anonymous cart.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.cart.models import Cart, CartItem, Coupon
from apps.core.exceptions import NotFoundError, ValidationError
from apps.products.services import product_service


class CartService:
    @transaction.atomic
    def get_or_create_cart(self, *, user=None, session_key: str | None = None) -> Cart:
        if user is not None:
            cart, _ = Cart.objects.get_or_create(user=user, defaults={"session_key": None})
            return cart
        if session_key is None:
            raise ValidationError("Anonymous carts require a session key.")
        cart, _ = Cart.objects.get_or_create(session_key=session_key, defaults={"user": None})
        return cart

    @transaction.atomic
    def add_item(self, cart: Cart, product_id: int, quantity: int = 1) -> CartItem:
        if quantity <= 0:
            raise ValidationError("Quantity must be positive.")
        from apps.products.models import Product

        product = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            raise NotFoundError("Product not found.")
        if not product.is_in_stock:
            raise ValidationError("This product is out of stock.")
        item = CartItem.objects.filter(cart=cart, product=product).first()
        if item is not None:
            item.quantity += quantity
            item.price_snapshot = product.price
            item.save(update_fields=["quantity", "price_snapshot", "updated_at"])
        else:
            item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
                price_snapshot=product.price,
            )
        return item

    @transaction.atomic
    def update_item(self, cart: Cart, item_id: int, quantity: int) -> CartItem:
        if quantity <= 0:
            raise ValidationError("Quantity must be positive.")
        item = CartItem.objects.filter(cart=cart, id=item_id).first()
        if item is None:
            raise NotFoundError("Cart item not found.")
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    @transaction.atomic
    def remove_item(self, cart: Cart, item_id: int) -> None:
        deleted, _ = CartItem.objects.filter(cart=cart, id=item_id).delete()
        if not deleted:
            raise NotFoundError("Cart item not found.")

    @transaction.atomic
    def clear(self, cart: Cart) -> None:
        cart.items.all().delete()
        cart.coupon = None
        cart.save(update_fields=["coupon", "updated_at"])

    @transaction.atomic
    def apply_coupon(self, cart: Cart, code: str) -> Coupon:
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if coupon is None:
            raise NotFoundError("Coupon not found.")
        if not coupon.is_valid_now:
            raise ValidationError("This coupon is no longer valid.")
        cart.coupon = coupon
        cart.save(update_fields=["coupon", "updated_at"])
        return coupon

    @transaction.atomic
    def remove_coupon(self, cart: Cart) -> None:
        cart.coupon = None
        cart.save(update_fields=["coupon", "updated_at"])

    @transaction.atomic
    def merge_carts(self, session_key: str, user) -> Cart:
        """Merge an anonymous cart into the user's cart on login."""
        anon = Cart.objects.filter(session_key=session_key).first()
        authed = self.get_or_create_cart(user=user)
        if anon is None or not anon.items.exists():
            return authed
        for anon_item in anon.items.all():
            existing = CartItem.objects.filter(cart=authed, product=anon_item.product).first()
            if existing is not None:
                existing.quantity += anon_item.quantity
                existing.save(update_fields=["quantity", "updated_at"])
            else:
                anon_item.cart = authed
                anon_item.save(update_fields=["cart", "updated_at"])
        anon.delete()
        return authed

    # --- Pricing ----------------------------------------------------------

    def line_effective_total(self, item: CartItem) -> Decimal:
        unit = product_service.get_effective_price(item.product)
        return (unit * item.quantity).quantize(Decimal("0.01"))

    def subtotal(self, cart: Cart) -> Decimal:
        total = Decimal("0.00")
        for item in cart.items.select_related("product"):
            total += self.line_effective_total(item)
        return total

    def coupon_discount(self, cart: Cart, subtotal: Decimal) -> Decimal:
        if cart.coupon is None or not cart.coupon.is_valid_now:
            return Decimal("0.00")
        c = cart.coupon
        if c.percentage is not None:
            discount = subtotal * (c.percentage / Decimal("100"))
        elif c.fixed_amount is not None:
            discount = c.fixed_amount
        else:
            discount = Decimal("0.00")
        # Never discount more than the subtotal.
        return min(discount, subtotal).quantize(Decimal("0.01"))

    def tax_amount(self, cart: Cart, discounted_subtotal: Decimal) -> Decimal:
        return (discounted_subtotal * cart.tax_rate / Decimal("100")).quantize(Decimal("0.01"))

    def totals(self, cart: Cart) -> dict:
        subtotal = self.subtotal(cart)
        discount = self.coupon_discount(cart, subtotal)
        taxable = subtotal - discount
        tax = self.tax_amount(cart, taxable)
        total = taxable + tax
        return {
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "total": total,
        }


cart_service = CartService()
