"""Reviews service — business logic, moderation, average rating."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Avg

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from apps.products.models import Product
from apps.reviews.models import Review


class ReviewService:
    @transaction.atomic
    def create(
        self,
        *,
        product: Product,
        user,
        rating: int,
        title: str = "",
        comment: str = "",
    ) -> Review:
        if not (1 <= rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")
        if Review.objects.filter(product=product, user=user).exists():
            raise ConflictError("You have already reviewed this product.")
        return Review.objects.create(
            product=product,
            user=user,
            rating=rating,
            title=title,
            comment=comment,
        )

    @transaction.atomic
    def update(
        self,
        review: Review,
        *,
        rating: int | None = None,
        title: str | None = None,
        comment: str | None = None,
    ) -> Review:
        if rating is not None:
            if not (1 <= rating <= 5):
                raise ValidationError("Rating must be between 1 and 5.")
            review.rating = rating
        if title is not None:
            review.title = title
        if comment is not None:
            review.comment = comment
        review.save()
        return review

    def list_approved_for(self, product: Product):
        return Review.objects.filter(product=product, is_approved=True).select_related("user")

    def average_rating(self, product: Product) -> float:
        agg = Review.objects.filter(product=product, is_approved=True).aggregate(avg=Avg("rating"))
        return round(agg["avg"], 2) if agg["avg"] is not None else 0.0

    @transaction.atomic
    def approve(self, review: Review) -> Review:
        review.is_approved = True
        review.save(update_fields=["is_approved", "updated_at"])
        return review

    @transaction.atomic
    def delete(self, review: Review, *, user) -> None:
        if review.user_id != user.id and user.role not in ("admin", "staff"):
            raise PermissionDeniedError("You can only delete your own reviews.")
        review.delete()

    def get(self, review_id: int) -> Review:
        try:
            return Review.objects.select_related("product", "user").get(id=review_id)
        except Review.DoesNotExist as exc:
            raise NotFoundError("Review not found.") from exc


review_service = ReviewService()
