"""Products serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.brands.models import Brand
from apps.categories.models import Category
from apps.products.models import Discount, Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "is_primary", "order")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    effective_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "category",
            "category_name",
            "brand",
            "brand_name",
            "price",
            "effective_price",
            "stock",
            "is_in_stock",
            "is_active",
            "is_featured",
            "images",
            "created_at",
        )
        read_only_fields = ("id", "slug", "is_in_stock", "effective_price", "created_at")

    def get_effective_price(self, obj: Product) -> str:
        # Lazy import to avoid a circular import at module load time.
        from apps.products.services import product_service

        return str(product_service.get_effective_price(obj))


class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    sku = serializers.CharField(max_length=64)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.IntegerField()
    brand = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    stock = serializers.IntegerField(required=False, default=0, min_value=0)
    is_featured = serializers.BooleanField(required=False, default=False)

    def validate_category(self, value: int) -> int:
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value

    def validate_brand(self, value: int) -> int:
        if not Brand.objects.filter(id=value).exists():
            raise serializers.ValidationError("Brand not found.")
        return value

    def validate_price(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ("id", "name", "percentage", "is_active", "valid_from", "valid_to", "created_at")
        read_only_fields = ("id", "created_at")
