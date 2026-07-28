"""Brands service — business logic."""

from __future__ import annotations

from django.db import transaction
from django.utils.text import slugify

from apps.brands.models import Brand
from apps.brands.repositories import BrandRepository
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError


class BrandService:
    def __init__(self, repo: BrandRepository) -> None:
        self.repo = repo

    @transaction.atomic
    def create(self, *, name: str, description: str = "") -> Brand:
        if not name.strip():
            raise ValidationError("Name is required.")
        if self.repo.name_exists(name):
            raise ConflictError("A brand with this name already exists.")
        return self.repo.create(
            name=name.strip(),
            slug=slugify(name),
            description=description,
        )

    @transaction.atomic
    def update(self, brand: Brand, **fields) -> Brand:
        if "name" in fields:
            new_name = fields["name"].strip()
            if not new_name:
                raise ValidationError("Name cannot be empty.")
            if self.repo.name_exists(new_name, exclude_id=brand.id):
                raise ConflictError("A brand with this name already exists.")
            fields["name"] = new_name
            fields["slug"] = slugify(new_name)
        for key, value in fields.items():
            setattr(brand, key, value)
        return self.repo.save(brand)

    def get(self, brand_id: int) -> Brand:
        brand = self.repo.get_by_id(brand_id)
        if brand is None:
            raise NotFoundError("Brand not found.")
        return brand


brand_service = BrandService(repo=BrandRepository())
