"""Categories serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True, default=None)
    children_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_name",
            "children_count",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "slug", "created_at")


class CategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    parent = serializers.IntegerField(required=False, allow_null=True, default=None)
    is_active = serializers.BooleanField(required=False, default=True)
