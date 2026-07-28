"""Payments API routes."""

from django.urls import path

from apps.payments.views import (
    ChargeView,
    PaymentDetailView,
    PaymentListView,
    RefundView,
)

app_name = "payments"

urlpatterns = [
    path("payments/charge/", ChargeView.as_view(), name="charge"),
    path("payments/", PaymentListView.as_view(), name="payment-list"),
    path("payments/<int:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("payments/<int:pk>/refund/", RefundView.as_view(), name="refund"),
]
