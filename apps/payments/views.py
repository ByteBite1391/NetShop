"""Payments views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import ok
from apps.payments.models import Payment
from apps.payments.serializers import ChargeSerializer, PaymentSerializer
from apps.payments.services import payment_service


@extend_schema(tags=["payments"])
class ChargeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChargeSerializer, responses=PaymentSerializer)
    def post(self, request):
        serializer = ChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = payment_service.charge(serializer.validated_data["order"], user=request.user)
        return ok(
            data=PaymentSerializer(payment).data,
            message="Payment processed.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["payments"])
class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return ok(data=PaymentSerializer(qs, many=True).data)


@extend_schema(tags=["payments"])
class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        payment = self.get_queryset().filter(id=kwargs["pk"]).first()
        if payment is None:
            from apps.core.exceptions import NotFoundError

            raise NotFoundError("Payment not found.")
        return ok(data=PaymentSerializer(payment).data)


@extend_schema(tags=["payments"])
class RefundView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        payment = payment_service.refund(pk, user=request.user)
        return ok(data=PaymentSerializer(payment).data, message="Refund processed.")
