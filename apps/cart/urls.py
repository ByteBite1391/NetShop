"""Cart API routes."""

from django.urls import path

from apps.cart.views import CartCouponView, CartItemView, CartView, CouponListView

app_name = "cart"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemView.as_view(), name="cart-item-add"),
    path("cart/items/<int:item_id>/", CartItemView.as_view(), name="cart-item-detail"),
    path("cart/coupon/", CartCouponView.as_view(), name="cart-coupon"),
    path("coupons/", CouponListView.as_view(), name="coupon-list"),
]
