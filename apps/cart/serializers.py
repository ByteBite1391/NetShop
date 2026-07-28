"""Cart serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.cart.models import Cart, CartItem, Coupon


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    effective_unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
            "product_name",
            "product_slug",
            "quantity",
            "price_snapshot",
            "effective_unit_price",
            "line_total",
        )
        read_only_fields = ("id", "price_snapshot", "effective_unit_price", "line_total")

    def get_effective_unit_price(self, obj: CartItem) -> str:
        from apps.products.services import product_service

        return str(product_service.get_effective_price(obj.product))

    def get_line_total(self, obj: CartItem) -> str:
        from apps.cart.services import cart_service

        return str(cart_service.line_effective_total(obj))


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    totals = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(source="coupon.code", read_only=True, default=None)

    class Meta:
        model = Cart
        fields = ("id", "items", "totals", "coupon_code", "tax_rate", "created_at")
        read_only_fields = ("id", "totals", "created_at")

    def get_totals(self, obj: Cart) -> dict:
        from apps.cart.services import cart_service

        return {k: str(v) for k, v in cart_service.totals(obj).items()}


class AddItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "description",
            "percentage",
            "fixed_amount",
            "max_uses",
            "times_used",
            "valid_from",
            "valid_to",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "times_used", "created_at")
