"""
Base abstract models shared across the project.

`TimeStampedModel` gives every domain model created_at/updated_at for free.
Soft-delete is intentionally NOT implemented globally — it complicates queries
and indexes everywhere. We add soft-delete only on models that need it (orders,
reviews) and keep it explicit there.
"""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base providing self-managing created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
