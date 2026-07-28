"""Categories repository — data access only."""

from __future__ import annotations

from typing import Protocol

from django.db.models import QuerySet

from apps.categories.models import Category


class ICategoryRepository(Protocol):
    def all_active(self) -> QuerySet[Category]: ...
    def get_by_slug(self, slug: str) -> Category | None: ...
    def get_by_id(self, category_id: int) -> Category | None: ...
    def create(self, **fields) -> Category: ...
    def save(self, category: Category) -> Category: ...
    def delete(self, category: Category) -> None: ...


class CategoryRepository:
    def all_active(self) -> QuerySet[Category]:
        return Category.objects.filter(is_active=True)

    def all(self) -> QuerySet[Category]:
        return Category.objects.all()

    def get_by_slug(self, slug: str) -> Category | None:
        return Category.objects.filter(slug=slug).first()

    def get_by_id(self, category_id: int) -> Category | None:
        return Category.objects.filter(id=category_id).first()

    def create(self, **fields) -> Category:
        return Category.objects.create(**fields)

    def save(self, category: Category) -> Category:
        category.save()
        return category

    def delete(self, category: Category) -> None:
        category.delete()


category_repository = CategoryRepository()
