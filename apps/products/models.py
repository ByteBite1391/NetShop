"""
Product domain models.

- Product: the sellable item, linked to a category and brand. Price stored as
  Decimal for money correctness (never float). SKU is unique. Slug auto-derived.
  `is_active` lets staff soft-hide. `is_featured` for homepage curation.
- ProductImage: multiple images per product, ordered.
- Inventory is tracked directly on Product via `stock` + `is_in_stock` to keep
  the common case simple; a dedicated Inventory model is the natural next step
  when per-variant stock is needed.
- Discount: optional percentage discount scoped to a product with a window.

Money is always stored as Decimal(max_digits=10, decimal_places=2). We never
use floats for currency — floating-point rounding errors are unacceptable in
e-commerce.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.brands.models import Brand
from apps.categories.models import Category
from apps.common.models import TimeStampedModel


class Product(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    stock = models.PositiveIntegerField(default=0)
    is_in_stock = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_in_stock"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Keep is_in_stock consistent with stock unless explicitly overridden later.
        if self.stock == 0:
            self.is_in_stock = False
        elif self.stock > 0 and not self.is_in_stock:
            self.is_in_stock = True
        super().save(*args, **kwargs)


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]


class Discount(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="discounts")
    name = models.CharField(max_length=120)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self) -> str:
        return f"{self.name} - {self.percentage}%"
