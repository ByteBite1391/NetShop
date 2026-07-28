"""Wishlist model — a user's saved products."""

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.products.models import Product


class Wishlist(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist"
    )
    products = models.ManyToManyField(Product, related_name="wishlisted_by", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Wishlist of {self.user.email}"
