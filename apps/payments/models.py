"""
Payment domain models.

A Payment records an attempt to pay for an Order. An order may have multiple
payments (retries, partial). `gateway` names the processor used (e.g. "fake",
"stripe"). `gateway_transaction_id` is the id returned by the gateway.

`status` tracks the payment lifecycle independently of the order status; the
order service reacts to payment status changes.
"""

from django.db import models

from apps.common.models import TimeStampedModel
from apps.orders.models import Order


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class Payment(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    gateway = models.CharField(max_length=32, default="fake")
    gateway_transaction_id = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True
    )
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "status"])]

    def __str__(self) -> str:
        return f"Payment#{self.id} {self.amount} {self.currency} ({self.status})"
