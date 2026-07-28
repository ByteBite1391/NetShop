"""
Development settings.

- DEBUG=True
- SQLite (when DATABASE_URL is not provided)
- Celery runs tasks eagerly so the app works without a Redis broker
- Verbose logging
"""

import os

from .base import *

DEBUG = True

# In dev, allow any host when DEBUG is on, but keep ALLOWED_HOSTS env-driven otherwise.
if os.environ.get("DJANGO_ALLOWED_HOSTS"):
    pass  # already set in base
else:
    ALLOWED_HOSTS = ["*"]

# Eager Celery: tasks run synchronously, no broker required.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Developer-friendly logging.
LOGGING["loggers"]["django"]["level"] = "INFO"  # type: ignore[name-defined]
LOGGING["loggers"]["django.db.backends"] = {"handlers": ["console"], "level": "WARNING", "propagate": False}  # type: ignore[name-defined]
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # type: ignore[name-defined]
