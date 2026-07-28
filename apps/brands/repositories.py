"""Brands repository — data access only."""

from __future__ import annotations

from apps.brands.models import Brand


class BrandRepository:
    def all_active(self):
        return Brand.objects.filter(is_active=True)

    def all(self):
        return Brand.objects.all()

    def get_by_slug(self, slug: str) -> Brand | None:
        return Brand.objects.filter(slug=slug).first()

    def get_by_id(self, brand_id: int) -> Brand | None:
        return Brand.objects.filter(id=brand_id).first()

    def name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        qs = Brand.objects.filter(name__iexact=name)
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def create(self, **fields) -> Brand:
        return Brand.objects.create(**fields)

    def save(self, brand: Brand) -> Brand:
        brand.save()
        return brand


brand_repository = BrandRepository()
