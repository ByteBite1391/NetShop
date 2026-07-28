"""Brands views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny

from apps.brands.models import Brand
from apps.brands.serializers import BrandCreateSerializer, BrandSerializer
from apps.brands.services import brand_service
from apps.common.permissions import IsStaff
from apps.common.responses import ok


@extend_schema(tags=["brands"])
class BrandListView(generics.ListCreateAPIView):
    serializer_class = BrandSerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaff()]
        return [AllowAny()]

    def get_queryset(self):
        return Brand.objects.filter(is_active=True).order_by("name")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return ok(data=BrandSerializer(qs, many=True).data)

    @extend_schema(request=BrandCreateSerializer, responses=BrandSerializer)
    def post(self, request, *args, **kwargs):
        serializer = BrandCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        brand = brand_service.create(name=data["name"], description=data.get("description", ""))
        return ok(
            data=BrandSerializer(brand).data,
            message="Brand created.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["brands"])
class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BrandSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsStaff()]

    def get_queryset(self):
        return Brand.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return ok(data=BrandSerializer(instance).data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return ok(message="Brand deleted.")
