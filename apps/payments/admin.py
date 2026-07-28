"""Payments admin."""

from django.contrib import admin

from apps.payments.models import Payment, PaymentStatus


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "gateway", "status", "created_at")
    list_filter = ("status", "gateway")
    search_fields = ("order__order_number", "gateway_transaction_id")
    readonly_fields = ("amount", "currency", "gateway", "gateway_transaction_id", "created_at")
    actions = ["mark_refunded"]

    @admin.action(description="Mark selected as refunded")
    def mark_refunded(self, request, queryset):
        updated = queryset.filter(status=PaymentStatus.SUCCEEDED).update(
            status=PaymentStatus.REFUNDED
        )
        self.message_user(request, f"{updated} payment(s) refunded.")
