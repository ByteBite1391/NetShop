"""Wishlist service."""

from __future__ import annotations

from django.db import transaction

from apps.core.exceptions import NotFoundError
from apps.products.models import Product
from apps.wishlist.models import Wishlist


class WishlistService:
    def get_or_create(self, user) -> Wishlist:
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        return wishlist

    @transaction.atomic
    def add(self, user, product_id: int) -> Wishlist:
        product = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            raise NotFoundError("Product not found.")
        wishlist = self.get_or_create(user)
        wishlist.products.add(product)
        return wishlist

    @transaction.atomic
    def remove(self, user, product_id: int) -> Wishlist:
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            raise NotFoundError("Product not found.")
        wishlist = self.get_or_create(user)
        wishlist.products.remove(product)
        return wishlist


wishlist_service = WishlistService()
