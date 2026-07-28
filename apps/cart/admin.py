"""Cart admin."""

from django.contrib import admin

from apps.cart.models import Cart, CartItem, Coupon


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("price_snapshot",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "coupon", "tax_rate", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "session_key")
    inlines = [CartItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "percentage",
        "fixed_amount",
        "is_active",
        "times_used",
        "max_uses",
        "valid_to",
    )
    list_filter = ("is_active",)
    search_fields = ("code",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity", "price_snapshot")
    search_fields = ("product__name",)
