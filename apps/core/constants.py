"""
Project-wide constants.

Centralising magic strings as enums keeps typos from causing silent bugs
("customer" vs "Customer") and makes refactorings greppable.
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNVERIFIED = "unverified"
