"""Categories views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny

from apps.categories.models import Category
from apps.categories.serializers import CategoryCreateSerializer, CategorySerializer
from apps.categories.services import category_service
from apps.common.permissions import IsStaff
from apps.common.responses import ok


@extend_schema(tags=["categories"])
class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None  # categories are few; return all

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaff()]
        return [AllowAny()]

    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by("name")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = CategorySerializer(qs, many=True).data
        # annotate children_count
        for item, cat in zip(data, qs):  # noqa: B905
            item["children_count"] = cat.children.count()
        return ok(data=data)

    @extend_schema(request=CategoryCreateSerializer, responses=CategorySerializer)
    def post(self, request, *args, **kwargs):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        category = category_service.create(
            name=data["name"],
            description=data.get("description", ""),
            parent_id=data.get("parent"),
        )
        return ok(
            data=CategorySerializer(category).data,
            message="Category created.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["categories"])
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsStaff()]

    def get_queryset(self):
        return Category.objects.all()

    def perform_update(self, serializer):
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = CategorySerializer(instance).data
        data["children_count"] = instance.children.count()
        return ok(data=data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return ok(message="Category deleted.")
