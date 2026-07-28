"""Wishlist serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.products.serializers import ProductSerializer
from apps.wishlist.models import Wishlist


class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Wishlist
        fields = ("id", "products", "product_count", "created_at")
        read_only_fields = ("id", "created_at")


class WishlistItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
