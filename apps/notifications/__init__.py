"""Notifications app — asynchronous notifications via Celery.

This app owns the Celery task definitions. Other apps (orders, accounts) call
these tasks via `.delay()` to send emails in the background. In development
(CELERY_TASK_ALWAYS_EAGER) they run synchronously, so the app works without a
broker.
"""
