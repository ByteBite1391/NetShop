"""Reviews serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "product",
            "user",
            "user_email",
            "user_name",
            "rating",
            "title",
            "comment",
            "is_approved",
            "created_at",
        )
        read_only_fields = ("id", "user", "is_approved", "created_at")


class ReviewCreateSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewUpdateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    title = serializers.CharField(max_length=120, required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
