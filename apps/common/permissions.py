"""
Role-based permission helpers.

The custom user model carries a `role` field (ADMIN / STAFF / CUSTOMER). These
permissions keep role checks declarative at the view level instead of scattering
`if request.user.role == ...` checks through views and services.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    """Allow only ADMIN users."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsStaff(BasePermission):
    """Allow ADMIN or STAFF users."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "staff")
        )


class IsOwnerOrReadOnly(BasePermission):
    """Read for everyone (authed), write only for the object owner or staff."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        if owner is not None and owner == request.user:
            return True
        return request.user.role in ("admin", "staff")
