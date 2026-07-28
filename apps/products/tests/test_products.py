"""Products API + service tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.core.exceptions import ConflictError, ValidationError
from apps.products.services import product_service

pytestmark = pytest.mark.django_db

PRODUCTS_URL = "/api/v1/products/"


class TestProductService:
    def test_create_product(self, user_factory):
        from tests.factories import BrandFactory, CategoryFactory

        cat = CategoryFactory()
        brand = BrandFactory()
        product = product_service.create(
            name="Widget",
            sku="WID-001",
            price=Decimal("9.99"),
            category_id=cat.id,
            brand_id=brand.id,
            stock=5,
        )
        assert product.slug == "widget"
        assert product.is_in_stock is True

    def test_duplicate_sku_rejected(self, user_factory):
        from tests.factories import BrandFactory, CategoryFactory, ProductFactory

        ProductFactory(sku="DUP")
        cat = CategoryFactory()
        brand = BrandFactory()
        with pytest.raises(ConflictError):
            product_service.create(
                name="Other",
                sku="DUP",
                price=Decimal("1.00"),
                category_id=cat.id,
                brand_id=brand.id,
            )

    def test_decrease_stock(self, user_factory):
        from tests.factories import ProductFactory

        product = ProductFactory(stock=10)
        product_service.decrease_stock(product, 3)
        product.refresh_from_db()
        assert product.stock == 7

    def test_decrease_stock_insufficient(self, user_factory):
        from tests.factories import ProductFactory

        product = ProductFactory(stock=2)
        with pytest.raises(ValidationError):
            product_service.decrease_stock(product, 5)

    def test_decrease_stock_to_zero_marks_out_of_stock(self, user_factory):
        from tests.factories import ProductFactory

        product = ProductFactory(stock=2)
        product_service.decrease_stock(product, 2)
        product.refresh_from_db()
        assert product.stock == 0 and product.is_in_stock is False


class TestProductAPI:
    def test_list_public(self, api_client):
        from tests.factories import ProductFactory

        ProductFactory(name="Alpha")
        ProductFactory(name="Beta")
        resp = api_client.get(PRODUCTS_URL)
        assert resp.status_code == 200

    def test_filter_by_category(self, api_client):
        from tests.factories import CategoryFactory, ProductFactory

        cat = CategoryFactory()
        ProductFactory(category=cat, name="InCat")
        ProductFactory(name="OutOfCat")
        resp = api_client.get(f"{PRODUCTS_URL}?category={cat.id}")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()["data"]["results"]]
        assert "InCat" in names and "OutOfCat" not in names

    def test_search(self, api_client):
        from tests.factories import ProductFactory

        ProductFactory(name="Red Phone")
        ProductFactory(name="Blue Laptop")
        resp = api_client.get(f"{PRODUCTS_URL}?search=phone")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()["data"]["results"]]
        assert any("Phone" in n for n in names)

    def test_detail_by_slug(self, api_client):
        from tests.factories import ProductFactory

        product = ProductFactory(name="Gamma")
        resp = api_client.get(f"{PRODUCTS_URL}{product.slug}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Gamma"
