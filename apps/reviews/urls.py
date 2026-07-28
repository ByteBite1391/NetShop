"""Reviews API routes."""

from django.urls import path

from apps.reviews.views import ReviewApproveView, ReviewDetailView, ReviewListView

app_name = "reviews"

urlpatterns = [
    path("products/<int:product_id>/reviews/", ReviewListView.as_view(), name="review-list"),
    path("reviews/<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path("reviews/<int:pk>/approve/", ReviewApproveView.as_view(), name="review-approve"),
]
