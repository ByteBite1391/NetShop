"""Categories service — business logic."""

from __future__ import annotations

from django.db import transaction
from django.utils.text import slugify

from apps.categories.models import Category
from apps.categories.repositories import CategoryRepository
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self.repo = repo

    @transaction.atomic
    def create(self, *, name: str, description: str = "", parent_id: int | None = None) -> Category:
        if not name.strip():
            raise ValidationError("Name is required.")
        if Category.objects.filter(name__iexact=name).exists():
            raise ConflictError("A category with this name already exists.")
        parent = None
        if parent_id is not None:
            parent = self.repo.get_by_id(parent_id)
            if parent is None:
                raise NotFoundError("Parent category not found.")
        return self.repo.create(
            name=name.strip(),
            slug=slugify(name),
            description=description,
            parent=parent,
        )

    @transaction.atomic
    def update(self, category: Category, **fields) -> Category:
        if "name" in fields:
            new_name = fields["name"].strip()
            if not new_name:
                raise ValidationError("Name cannot be empty.")
            if Category.objects.filter(name__iexact=new_name).exclude(id=category.id).exists():
                raise ConflictError("A category with this name already exists.")
            fields["name"] = new_name
            fields["slug"] = slugify(new_name)
        if "parent_id" in fields:
            pid = fields.pop("parent_id")
            if pid is None:
                fields["parent"] = None
            else:
                parent = self.repo.get_by_id(pid)
                if parent is None:
                    raise NotFoundError("Parent category not found.")
                if parent.id == category.id:
                    raise ValidationError("A category cannot be its own parent.")
                fields["parent"] = parent
        for key, value in fields.items():
            setattr(category, key, value)
        return self.repo.save(category)

    def list_active(self) -> list[Category]:
        return list(self.repo.all_active())

    def get(self, category_id: int) -> Category:
        cat = self.repo.get_by_id(category_id)
        if cat is None:
            raise NotFoundError("Category not found.")
        return cat


category_service = CategoryService(repo=CategoryRepository())
