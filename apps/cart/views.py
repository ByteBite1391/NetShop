"""
Cart views.

Anonymous carts: identified by the `X-Cart-Session` header (or created on the
fly). Authenticated carts: tied to the user. Views resolve the right cart via
`_resolve_cart` so both flows share the same endpoints.
"""

from __future__ import annotations

import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.cart.models import Coupon
from apps.cart.serializers import (
    AddItemSerializer,
    ApplyCouponSerializer,
    CartSerializer,
    CouponSerializer,
    UpdateItemSerializer,
)
from apps.cart.services import cart_service
from apps.common.permissions import IsStaff
from apps.common.responses import ok


def _resolve_cart(request):
    """Return the cart for the current request (authed or anonymous)."""
    if request.user.is_authenticated:
        return cart_service.get_or_create_cart(user=request.user)
    session_key = request.headers.get("X-Cart-Session") or str(uuid.uuid4())
    return cart_service.get_or_create_cart(session_key=session_key), session_key


@extend_schema(tags=["cart"])
class CartView(APIView):
    """Get or clear the current cart."""

    def get_permissions(self):
        return [AllowAny()]

    def get(self, request):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        session_key = result[1] if isinstance(result, tuple) else None
        data = CartSerializer(cart).data
        if session_key:
            data["session_key"] = session_key
        return ok(data=data)

    def delete(self, request):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        cart_service.clear(cart)
        return ok(message="Cart cleared.")


@extend_schema(tags=["cart"])
class CartItemView(APIView):
    """Add or update an item in the cart."""

    def get_permissions(self):
        return [AllowAny()]

    @extend_schema(request=AddItemSerializer)
    def post(self, request):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        session_key = result[1] if isinstance(result, tuple) else None
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cart_service.add_item(cart, data["product"], data.get("quantity", 1))
        resp = ok(
            data=CartSerializer(cart).data, message="Item added.", status=status.HTTP_201_CREATED
        )
        if session_key:
            resp.data["data"]["session_key"] = session_key
        return resp

    @extend_schema(request=UpdateItemSerializer)
    def patch(self, request, item_id: int):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        serializer = UpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_service.update_item(cart, item_id, serializer.validated_data["quantity"])
        return ok(data=CartSerializer(cart).data, message="Item updated.")

    def delete(self, request, item_id: int):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        cart_service.remove_item(cart, item_id)
        return ok(data=CartSerializer(cart).data, message="Item removed.")


@extend_schema(tags=["cart"])
class CartCouponView(APIView):
    """Apply or remove a coupon on the cart."""

    def get_permissions(self):
        return [AllowAny()]

    @extend_schema(request=ApplyCouponSerializer)
    def post(self, request):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_service.apply_coupon(cart, serializer.validated_data["code"])
        return ok(data=CartSerializer(cart).data, message="Coupon applied.")

    def delete(self, request):
        result = _resolve_cart(request)
        cart = result[0] if isinstance(result, tuple) else result
        cart_service.remove_coupon(cart)
        return ok(data=CartSerializer(cart).data, message="Coupon removed.")


@extend_schema(tags=["cart"])
class CouponListView(generics.ListCreateAPIView):
    """Staff manage coupons; anyone can list active ones."""

    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaff()]
        return [AllowAny()]

    def get_queryset(self):
        return Coupon.objects.all().order_by("-created_at")
