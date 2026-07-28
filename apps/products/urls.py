"""Products API routes."""

from django.urls import path

from apps.products.views import (
    DiscountListView,
    ProductDetailView,
    ProductListView,
)

app_name = "products"

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/discounts/", DiscountListView.as_view(), name="discount-list"),
]
