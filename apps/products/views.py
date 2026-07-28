"""Products views — list/detail with filtering, search, ordering, pagination."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsStaff
from apps.common.responses import ok
from apps.products.models import Discount, Product
from apps.products.serializers import (
    DiscountSerializer,
    ProductCreateSerializer,
    ProductSerializer,
)
from apps.products.services import product_service


@extend_schema(tags=["products"])
class ProductListView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]

    search_fields = ["name", "description", "sku"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaff()]
        return [AllowAny()]

    def get_queryset(self):
        qs = Product.objects.select_related("category", "brand").filter(is_active=True)
        # Manual filtering by query params (keeps deps light; django-filter can
        # be added later if filter complexity grows).
        params = self.request.query_params
        if category := params.get("category"):
            qs = qs.filter(category_id=category)
        if brand := params.get("brand"):
            qs = qs.filter(brand_id=brand)
        if min_price := params.get("min_price"):
            qs = qs.filter(price__gte=min_price)
        if max_price := params.get("max_price"):
            qs = qs.filter(price__lte=max_price)
        if params.get("featured") in ("true", "1"):
            qs = qs.filter(is_featured=True)
        if params.get("in_stock") in ("true", "1"):
            qs = qs.filter(is_in_stock=True)
        return qs

    @extend_schema(
        request=ProductCreateSerializer,
        responses=ProductSerializer,
        parameters=[
            OpenApiParameter("category", int, description="Filter by category ID"),
            OpenApiParameter("brand", int, description="Filter by brand ID"),
            OpenApiParameter("min_price", float, description="Min price"),
            OpenApiParameter("max_price", float, description="Max price"),
            OpenApiParameter("featured", bool, description="Featured only"),
            OpenApiParameter("in_stock", bool, description="In stock only"),
            OpenApiParameter("search", str, description="Search name/description/sku"),
            OpenApiParameter("ordering", str, description="price,-created_at,name"),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=ProductCreateSerializer, responses=ProductSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        product = product_service.create(
            name=data["name"],
            sku=data["sku"],
            price=data["price"],
            category_id=data["category"],
            brand_id=data["brand"],
            description=data.get("description", ""),
            stock=data.get("stock", 0),
            is_featured=data.get("is_featured", False),
        )
        return ok(
            data=ProductSerializer(product).data,
            message="Product created.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["products"])
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsStaff()]

    def get_queryset(self):
        return Product.objects.select_related("category", "brand").all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return ok(data=ProductSerializer(instance).data)


@extend_schema(tags=["products"])
class DiscountListView(generics.ListCreateAPIView):
    serializer_class = DiscountSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaff()]
        return [AllowAny()]

    def get_queryset(self):
        return Discount.objects.select_related("product").all()
