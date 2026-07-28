"""Brands serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.brands.models import Brand


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ("id", "name", "slug", "description", "logo", "is_active", "created_at")
        read_only_fields = ("id", "slug", "created_at")


class BrandCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)
