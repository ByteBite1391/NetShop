"""Categories API routes."""

from django.urls import path

from apps.categories.views import CategoryDetailView, CategoryListView

app_name = "categories"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"),
]
