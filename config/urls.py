"""
Root URL configuration.

API routes are versioned under /api/v1/ so we can introduce v2 without breaking
existing clients. Each app registers its own URLs in its `urls.py`.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

api_v1_patterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.categories.urls")),
    path("", include("apps.brands.urls")),
    path("", include("apps.products.urls")),
    path("", include("apps.reviews.urls")),
    path("", include("apps.cart.urls")),
    path("", include("apps.wishlist.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.payments.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "v1"), namespace="v1")),
    # OpenAPI schema + docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
