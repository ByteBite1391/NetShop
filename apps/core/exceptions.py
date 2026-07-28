"""
Domain exception hierarchy.

Services raise these instead of returning error codes or touching HTTP concerns.
A central DRF exception handler (apps.common.exception_handler) translates them
into the consistent API envelope with the right status code. This keeps the
service layer HTTP-agnostic and reusable from Celery tasks and the admin.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for all domain-level errors. Carries an optional error code."""

    default_message: str = "A domain error occurred."
    default_code: str = "domain_error"

    def __init__(self, message: str | None = None, code: str | None = None) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.code = code or self.default_code


class NotFoundError(DomainError):
    default_message = "Resource not found."
    default_code = "not_found"


class ValidationError(DomainError):
    default_message = "Validation failed."
    default_code = "validation_error"


class AuthenticationError(DomainError):
    default_message = "Authentication failed."
    default_code = "authentication_error"


class PermissionDeniedError(DomainError):
    default_message = "You do not have permission to perform this action."
    default_code = "permission_denied"


class ConflictError(DomainError):
    default_message = "This action conflicts with the current state."
    default_code = "conflict"
