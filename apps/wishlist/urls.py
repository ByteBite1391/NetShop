"""Wishlist API routes."""

from django.urls import path

from apps.wishlist.views import WishlistItemView, WishlistView

app_name = "wishlist"

urlpatterns = [
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/<int:product_id>/", WishlistItemView.as_view(), name="wishlist-item"),
]
