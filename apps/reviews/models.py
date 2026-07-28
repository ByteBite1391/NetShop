"""
Review model.

A user may leave one review per product (enforced by a unique constraint and in
the service). `is_approved` supports moderation: new reviews default to
`False`, and only approved reviews are public. An average rating is computed
from approved reviews via the service layer.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.products.models import Product


class Review(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=120, blank=True)
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"], name="unique_review_per_user_per_product"
            ),
        ]
        indexes = [models.Index(fields=["product", "is_approved"])]

    def __str__(self) -> str:
        return f"{self.user.email} -> {self.product.name} ({self.rating}/5)"
