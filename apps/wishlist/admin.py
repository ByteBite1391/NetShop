"""Wishlist admin."""

from django.contrib import admin

from apps.wishlist.models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product_count", "created_at")
    search_fields = ("user__email",)
    filter_horizontal = ("products",)

    @admin.display(description="Products")
    def product_count(self, obj: Wishlist) -> int:
        return obj.products.count()
