"""Orders serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "quantity", "unit_price", "line_total")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "user",
            "user_email",
            "items",
            "shipping_full_name",
            "shipping_address_line",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "shipping_phone",
            "billing_full_name",
            "billing_address_line",
            "billing_city",
            "billing_state",
            "billing_postal_code",
            "billing_country",
            "subtotal",
            "discount",
            "tax",
            "shipping_fee",
            "total",
            "coupon_code",
            "created_at",
        )
        read_only_fields = (
            "id",
            "order_number",
            "status",
            "user",
            "subtotal",
            "discount",
            "tax",
            "total",
            "created_at",
        )


class AddressSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=160)
    address_line = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=120)
    state = serializers.CharField(max_length=120)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=80)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")


class CheckoutSerializer(serializers.Serializer):
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer(required=False)
    shipping_fee = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default="0.00"
    )


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
