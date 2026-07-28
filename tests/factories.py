"""
Test factories — deterministic test data via factory_boy.

Factories make tests readable and avoid the `Model.objects.create(...)`
boilerplate that scatters default values across every test. Each factory
declares the minimum valid state for a model; tests override only the fields
they care about.
"""

from __future__ import annotations

from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.brands.models import Brand
from apps.cart.models import Cart, CartItem, Coupon
from apps.categories.models import Category
from apps.core.constants import UserRole
from apps.products.models import Product


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = UserRole.CUSTOMER
    is_active = True
    email_verified = True

    # factory_boy passes the value of the `password` declaration here. We name
    # the declaration `password` so tests read naturally:
    #   UserFactory(password="Str0ngP@ss!")  -> sets a usable password.
    @factory.post_generation
    def password(obj, create: bool, extracted: str | None, **kwargs):
        raw = extracted or "Str0ngP@ss!"
        obj.set_password(raw)
        if create:
            obj.save()
        # Stash the plaintext so tests that log in can retrieve it.
        obj._raw_password = raw


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Category {n}")
    description = "A test category"


class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Brand
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Brand {n}")
    description = "A test brand"


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    sku = factory.Sequence(lambda n: f"SKU-{n}")
    price = Decimal("19.99")
    stock = 10
    is_in_stock = True
    is_active = True
    category = factory.SubFactory(CategoryFactory)
    brand = factory.SubFactory(BrandFactory)


class CouponFactory(DjangoModelFactory):
    class Meta:
        model = Coupon

    code = factory.Sequence(lambda n: f"SAVE{n}")
    percentage = Decimal("10.00")
    is_active = True
    valid_from = factory.Faker("past_datetime")
    valid_to = factory.Faker("future_datetime")


class CartFactory(DjangoModelFactory):
    class Meta:
        model = Cart

    user = factory.SubFactory(UserFactory)


class CartItemFactory(DjangoModelFactory):
    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    price_snapshot = Decimal("19.99")
