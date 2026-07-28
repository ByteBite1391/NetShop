"""
DRF exception handler that maps domain exceptions to the consistent envelope.

DRF's default handler produces a flat `{field: [errors]}` shape and doesn't know
about our `DomainError` hierarchy. This handler:
  1. Lets DRF handle standard DRF exceptions (and normalises their body).
  2. Maps our domain exceptions to the right HTTP status + envelope.
This keeps views thin — they call services and let exceptions bubble.
"""

from typing import Any

from rest_framework.views import exception_handler as drf_default_handler

from apps.common.responses import fail
from apps.core.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

# Domain error -> HTTP status mapping.
_STATUS_BY_DOMAIN: dict[type[DomainError], int] = {
    ValidationError: 400,
    AuthenticationError: 401,
    PermissionDeniedError: 403,
    NotFoundError: 404,
    ConflictError: 409,
}


def exception_handler(exc: Exception, context: dict[str, Any]):
    # 1. Domain errors — map to our envelope.
    if isinstance(exc, DomainError):
        status = _STATUS_BY_DOMAIN.get(type(exc), 400)
        return fail(message=exc.message, errors={"code": exc.code}, status=status)

    # 2. DRF exceptions — use the default handler, then normalise the shape.
    response = drf_default_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "message": _summarise_drf_error(response.data),
            "errors": response.data,
        }
    return response


def _summarise_drf_error(data: Any) -> str:
    """Turn DRF's varied error payloads into a single human-readable string."""
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
        return "Request failed validation."
    if isinstance(data, list) and data:
        return str(data[0])
    return "Request failed."
