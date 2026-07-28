"""Wishlist views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import ok
from apps.wishlist.serializers import WishlistItemSerializer, WishlistSerializer
from apps.wishlist.services import wishlist_service


@extend_schema(tags=["wishlist"])
class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = wishlist_service.get_or_create(request.user)
        return ok(data=WishlistSerializer(wishlist).data)

    @extend_schema(request=WishlistItemSerializer)
    def post(self, request):
        serializer = WishlistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wishlist = wishlist_service.add(request.user, serializer.validated_data["product"])
        return ok(
            data=WishlistSerializer(wishlist).data,
            message="Product added to wishlist.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["wishlist"])
class WishlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id: int):
        wishlist = wishlist_service.remove(request.user, product_id)
        return ok(data=WishlistSerializer(wishlist).data, message="Product removed from wishlist.")
