"""
Consistent API response helpers.

Every endpoint returns the same envelope so frontend clients can parse errors
and data uniformly:

    {"success": True,  "message": str|None, "data": <payload>}
    {"success": False, "message": str,      "errors": <detail>}

We return a DRF `Response` directly so the renderer (JSON) and status code stay
in sync. Views should prefer these helpers over hand-rolling dicts.
"""

from typing import Any

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED


def ok(data: Any = None, message: str | None = None, status: int = HTTP_200_OK) -> Response:
    """Success response."""
    return Response({"success": True, "message": message, "data": data}, status=status)


def created(data: Any = None, message: str | None = None) -> Response:
    """201 Created success response."""
    return ok(data=data, message=message, status=HTTP_201_CREATED)


def fail(message: str, errors: Any = None, status: int = HTTP_200_OK) -> Response:
    """Failure response. Callers pass the desired HTTP status (often 4xx)."""
    return Response({"success": False, "message": message, "errors": errors}, status=status)
