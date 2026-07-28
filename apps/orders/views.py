"""Orders views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsStaff
from apps.common.responses import ok
from apps.orders.models import Order
from apps.orders.serializers import (
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)
from apps.orders.services import order_service


@extend_schema(tags=["orders"])
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=CheckoutSerializer, responses=OrderSerializer)
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order = order_service.checkout(
            request.user,
            shipping_address=dict(data["shipping_address"]),
            billing_address=dict(data["billing_address"]) if data.get("billing_address") else None,
            shipping_fee=data.get("shipping_fee", 0),
        )
        return ok(
            data=OrderSerializer(order).data,
            message="Order created.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["orders"])
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return order_service.list_for_user(self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return ok(data=OrderSerializer(qs, many=True).data)


@extend_schema(tags=["orders"])
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        order = order_service.get(kwargs["pk"], request.user)
        return ok(data=OrderSerializer(order).data)


@extend_schema(tags=["orders"])
class OrderStatusView(APIView):
    """Staff-only: transition an order's status."""

    permission_classes = [IsStaff]

    @extend_schema(request=OrderStatusSerializer, responses=OrderSerializer)
    def post(self, request, pk: int):
        order = order_service.get_for_admin(pk)
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = order_service.transition_status(order, serializer.validated_data["status"])
        return ok(data=OrderSerializer(order).data, message="Order status updated.")
