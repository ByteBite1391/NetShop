"""Payments service — orchestrate gateway charge + order status update."""

from __future__ import annotations

from django.db import transaction

from apps.core.exceptions import NotFoundError, ValidationError
from apps.orders.models import OrderStatus
from apps.orders.services import order_service
from apps.payments.gateways import get_gateway
from apps.payments.models import Payment, PaymentStatus


class PaymentService:
    @transaction.atomic
    def charge(self, order_id: int, *, user) -> Payment:
        order = order_service.get(order_id, user)
        if order.status != OrderStatus.PENDING:
            raise ValidationError(f"Order {order.order_number} is not pending payment.")
        gateway = get_gateway()
        payment = Payment.objects.create(
            order=order,
            amount=order.total,
            currency="USD",
            gateway=gateway.name,
            status=PaymentStatus.PENDING,
        )
        result = gateway.charge(
            amount=order.total,
            currency="USD",
            reference=order.order_number,
        )
        if result.success:
            payment.status = PaymentStatus.SUCCEEDED
            payment.gateway_transaction_id = result.transaction_id
            payment.save(update_fields=["status", "gateway_transaction_id", "updated_at"])
            order_service.transition_status(order, OrderStatus.PAID.value)
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = result.failure_reason
            payment.save(update_fields=["status", "failure_reason", "updated_at"])
        return payment

    @transaction.atomic
    def refund(self, payment_id: int, *, user) -> Payment:
        payment = Payment.objects.select_related("order").filter(id=payment_id).first()
        if payment is None:
            raise NotFoundError("Payment not found.")
        if payment.status != PaymentStatus.SUCCEEDED:
            raise ValidationError("Only succeeded payments can be refunded.")
        if payment.order.user_id != user.id and user.role not in ("admin", "staff"):
            from apps.core.exceptions import PermissionDeniedError

            raise PermissionDeniedError("You cannot refund this payment.")
        gateway = get_gateway(payment.gateway)
        result = gateway.refund(
            transaction_id=payment.gateway_transaction_id, amount=payment.amount
        )
        if result.success:
            payment.status = PaymentStatus.REFUNDED
            payment.save(update_fields=["status", "updated_at"])
        else:
            payment.failure_reason = result.failure_reason
            payment.save(update_fields=["failure_reason", "updated_at"])
        return payment

    def list_for_order(self, order_id: int, *, user) -> list[Payment]:
        order = order_service.get(order_id, user)
        return list(order.payments.all())


payment_service = PaymentService()
