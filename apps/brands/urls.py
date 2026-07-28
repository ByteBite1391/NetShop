"""Brands API routes."""

from django.urls import path

from apps.brands.views import BrandDetailView, BrandListView

app_name = "brands"

urlpatterns = [
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("brands/<slug:slug>/", BrandDetailView.as_view(), name="brand-detail"),
]
