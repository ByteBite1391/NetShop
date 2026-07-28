"""Reviews views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsStaff
from apps.common.responses import ok
from apps.core.exceptions import NotFoundError
from apps.products.models import Product
from apps.reviews.models import Review
from apps.reviews.serializers import (
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)
from apps.reviews.services import review_service


@extend_schema(tags=["reviews"])
class ReviewListView(generics.ListCreateAPIView):
    """List approved reviews for a product, or create a review (auth required)."""

    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return []

    def get_queryset(self):
        product_id = self.request.parser_context.get("kwargs", {}).get("product_id")
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            return Review.objects.none()
        return review_service.list_approved_for(product)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return ok(data=ReviewSerializer(qs, many=True).data)

    @extend_schema(request=ReviewCreateSerializer, responses=ReviewSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        product = Product.objects.filter(id=data["product"]).first()
        if product is None:
            raise NotFoundError("Product not found.")
        review = review_service.create(
            product=product,
            user=request.user,
            rating=data["rating"],
            title=data.get("title", ""),
            comment=data.get("comment", ""),
        )
        return ok(
            data=ReviewSerializer(review).data,
            message="Review submitted and pending moderation.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["reviews"])
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role in ("admin", "staff"):
            return Review.objects.all()
        return Review.objects.filter(is_approved=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return ok(data=ReviewSerializer(instance).data)

    @extend_schema(request=ReviewUpdateSerializer, responses=ReviewSerializer)
    def patch(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user_id != request.user.id:
            from apps.core.exceptions import PermissionDeniedError

            raise PermissionDeniedError("You can only edit your own reviews.")
        serializer = ReviewUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = review_service.update(review, **serializer.validated_data)
        return ok(data=ReviewSerializer(review).data, message="Review updated.")

    def delete(self, request, *args, **kwargs):
        review = self.get_object()
        review_service.delete(review, user=request.user)
        return ok(message="Review deleted.")


@extend_schema(tags=["reviews"])
class ReviewApproveView(generics.GenericAPIView):
    """Staff-only: approve a pending review."""

    serializer_class = ReviewSerializer
    permission_classes = [IsStaff]

    def post(self, request, *args, **kwargs):
        review = review_service.get(kwargs["pk"])
        review = review_service.approve(review)
        return ok(data=ReviewSerializer(review).data, message="Review approved.")
