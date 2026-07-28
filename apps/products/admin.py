"""Products admin."""

from django.contrib import admin

from apps.products.models import Discount, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "brand",
        "price",
        "stock",
        "is_in_stock",
        "is_active",
        "is_featured",
    )
    list_filter = ("is_active", "is_in_stock", "is_featured", "category", "brand")
    search_fields = ("name", "sku", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "stock", "is_active", "is_featured")
    inlines = [ProductImageInline]


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "percentage", "is_active", "valid_from", "valid_to")
    list_filter = ("is_active",)
    search_fields = ("name", "product__name")
