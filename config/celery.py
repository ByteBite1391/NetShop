"""
Celery application bootstrap.

Importing this module configures the Celery app and wires Django settings so
that `celery -A config worker` / `celery -A config beat` work out of the box.

Why Celery?
-----------
Django is request/response. Anything slow or side-effectful (sending emails,
order fulfillment, receipt generation) would block a worker and hurt latency.
Celery is a battle-tested task queue that runs work in background processes,
retrying on failure. In development we set CELERY_TASK_ALWAYS_EAGER so tasks
run inline — the app works with zero extra infrastructure.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("nexcart")

# Read Celery config from Django settings (prefixed with CELERY_).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks defined in each app's `tasks.py`.
app.autodiscover_tasks()
