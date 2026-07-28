"""
Celery tasks for the notifications app.

Why Celery for email?
---------------------
SMTP calls are slow (hundreds of ms to seconds) and can fail transiently. Doing
them synchronously in a Django view blocks the request and tanks latency under
load. Celery runs them in a separate process, retries on failure, and lets the
web worker respond immediately.

In development (CELERY_TASK_ALWAYS_EAGER=True) `.delay()` runs the task inline,
so the app is fully functional without a running Redis broker.
"""

from __future__ import annotations

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(
    self, subject: str, html_body: str, to: list[str], from_email: str | None = None
):
    """Send an HTML email (with plain-text fallback), retrying on failure."""
    try:
        send_mail(
            subject,
            strip_tags(html_body),
            from_email or "no-reply@nexcart.example",
            to,
            html_message=html_body,
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc) from exc


def _render(template_name: str, context: dict) -> str:
    return render_to_string(template_name, context)


@shared_task
def send_welcome_email(user_email: str, first_name: str) -> None:
    html = _render("notifications/welcome.html", {"first_name": first_name})
    send_email_task.delay(
        subject="Welcome to NexCart",
        html_body=html,
        to=[user_email],
    )


@shared_task
def send_verification_email(user_email: str, first_name: str, token: str) -> None:
    html = _render("notifications/verify_email.html", {"first_name": first_name, "token": token})
    send_email_task.delay(subject="Verify your NexCart email", html_body=html, to=[user_email])


@shared_task
def send_password_reset_email(user_email: str, first_name: str, token: str) -> None:
    html = _render("notifications/password_reset.html", {"first_name": first_name, "token": token})
    send_email_task.delay(subject="Reset your NexCart password", html_body=html, to=[user_email])


@shared_task
def send_order_confirmation_email(
    user_email: str, first_name: str, order_number: str, total: str
) -> None:
    html = _render(
        "notifications/order_confirmation.html",
        {"first_name": first_name, "order_number": order_number, "total": total},
    )
    send_email_task.delay(
        subject=f"Order {order_number} confirmed", html_body=html, to=[user_email]
    )
