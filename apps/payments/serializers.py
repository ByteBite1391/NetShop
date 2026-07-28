"""Payments serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "order_number",
            "amount",
            "currency",
            "gateway",
            "gateway_transaction_id",
            "status",
            "failure_reason",
            "created_at",
        )
        read_only_fields = (
            "id",
            "amount",
            "currency",
            "gateway",
            "gateway_transaction_id",
            "status",
            "failure_reason",
            "created_at",
        )


class ChargeSerializer(serializers.Serializer):
    order = serializers.IntegerField()
