"""Products repository — data access only."""

from __future__ import annotations

from django.db.models import QuerySet
from django.utils import timezone

from apps.products.models import Product


class ProductRepository:
    def all(self) -> QuerySet[Product]:
        return Product.objects.select_related("category", "brand").filter(is_active=True)

    def all_for_admin(self) -> QuerySet[Product]:
        return Product.objects.select_related("category", "brand").all()

    def get_by_id(self, product_id: int) -> Product | None:
        return Product.objects.select_related("category", "brand").filter(id=product_id).first()

    def get_by_slug(self, slug: str) -> Product | None:
        return Product.objects.select_related("category", "brand").filter(slug=slug).first()

    def sku_exists(self, sku: str, exclude_id: int | None = None) -> bool:
        qs = Product.objects.filter(sku=sku)
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def create(self, **fields) -> Product:
        return Product.objects.create(**fields)

    def save(self, product: Product) -> Product:
        product.save()
        return product

    def filter(
        self,
        *,
        category_id: int | None = None,
        brand_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        is_featured: bool | None = None,
        search: str | None = None,
    ) -> QuerySet[Product]:
        qs = self.all()
        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if brand_id is not None:
            qs = qs.filter(brand_id=brand_id)
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        if is_featured is not None:
            qs = qs.filter(is_featured=is_featured)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


class DiscountRepository:
    def active_for(self, product: Product):
        now = timezone.now()
        return product.discounts.filter(
            is_active=True, valid_from__lte=now, valid_to__gte=now
        ).first()


product_repository = ProductRepository()
discount_repository = DiscountRepository()
