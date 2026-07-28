"""
Products service — business logic including stock management and pricing.

Pricing model
-------------
`get_effective_price` returns the price after applying any active discount.
The cart and order services use this so a single pricing rule lives in one
place — never duplicated in the cart.

Stock management
----------------
`decrease_stock` is the single safe way to reduce stock; it's called inside an
atomic transaction during checkout. It guards against going negative and keeps
`is_in_stock` in sync.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils.text import slugify

from apps.brands.models import Brand
from apps.categories.models import Category
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.products.models import Product
from apps.products.repositories import DiscountRepository, ProductRepository


class ProductService:
    def __init__(self, products: ProductRepository, discounts: DiscountRepository) -> None:
        self.products = products
        self.discounts = discounts

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        sku: str,
        price: Decimal,
        category_id: int,
        brand_id: int,
        description: str = "",
        stock: int = 0,
        is_featured: bool = False,
    ) -> Product:
        if not name.strip():
            raise ValidationError("Name is required.")
        if not sku.strip():
            raise ValidationError("SKU is required.")
        if self.products.sku_exists(sku):
            raise ConflictError("A product with this SKU already exists.")
        if price <= 0:
            raise ValidationError("Price must be positive.")
        category = Category.objects.filter(id=category_id).first()
        if category is None:
            raise NotFoundError("Category not found.")
        brand = Brand.objects.filter(id=brand_id).first()
        if brand is None:
            raise NotFoundError("Brand not found.")
        return self.products.create(
            name=name.strip(),
            slug=slugify(name),
            sku=sku.strip(),
            price=price,
            category=category,
            brand=brand,
            description=description,
            stock=stock,
            is_featured=is_featured,
        )

    @transaction.atomic
    def update(self, product: Product, **fields) -> Product:
        if "name" in fields:
            new_name = fields["name"].strip()
            if not new_name:
                raise ValidationError("Name cannot be empty.")
            fields["name"] = new_name
            fields["slug"] = slugify(new_name)
        if "sku" in fields:
            new_sku = fields["sku"].strip()
            if not new_sku:
                raise ValidationError("SKU cannot be empty.")
            if self.products.sku_exists(new_sku, exclude_id=product.id):
                raise ConflictError("A product with this SKU already exists.")
            fields["sku"] = new_sku
        if "category_id" in fields:
            cat = Category.objects.filter(id=fields.pop("category_id")).first()
            if cat is None:
                raise NotFoundError("Category not found.")
            fields["category"] = cat
        if "brand_id" in fields:
            brand = Brand.objects.filter(id=fields.pop("brand_id")).first()
            if brand is None:
                raise NotFoundError("Brand not found.")
            fields["brand"] = brand
        for key, value in fields.items():
            setattr(product, key, value)
        return self.products.save(product)

    def get(self, product_id: int) -> Product:
        product = self.products.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    def get_by_slug(self, slug: str) -> Product:
        product = self.products.get_by_slug(slug)
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    def get_effective_price(self, product: Product) -> Decimal:
        """Return price after applying any active discount."""
        discount = self.discounts.active_for(product)
        if discount is None:
            return product.price
        discounted = product.price * (Decimal("1") - discount.percentage / Decimal("100"))
        # Round to 2dp; never undercharge due to truncation.
        return discounted.quantize(Decimal("0.01"))

    @transaction.atomic
    def decrease_stock(self, product: Product, quantity: int) -> Product:
        """Reduce stock safely; raises if insufficient."""
        if quantity <= 0:
            raise ValidationError("Quantity must be positive.")
        product.refresh_from_db(fields=["stock"])
        if product.stock < quantity:
            raise ValidationError(
                f"Insufficient stock for {product.name}: have {product.stock}, need {quantity}."
            )
        product.stock -= quantity
        if product.stock == 0:
            product.is_in_stock = False
        return self.products.save(product)

    def list_filtered(self, **filters):
        return self.products.filter(**filters)


product_service = ProductService(products=ProductRepository(), discounts=DiscountRepository())
