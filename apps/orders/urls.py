"""Orders API routes."""

from django.urls import path

from apps.orders.views import (
    CheckoutView,
    OrderDetailView,
    OrderListView,
    OrderStatusView,
)

app_name = "orders"

urlpatterns = [
    path("orders/checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/status/", OrderStatusView.as_view(), name="order-status"),
]
