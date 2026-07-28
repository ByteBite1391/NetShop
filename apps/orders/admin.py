"""Orders admin."""

from django.contrib import admin

from apps.orders.models import Order, OrderItem, OrderStatus


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "quantity", "unit_price", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "total",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "user__email")
    list_editable = ("status",)
    readonly_fields = (
        "order_number",
        "subtotal",
        "discount",
        "tax",
        "total",
        "created_at",
    )
    inlines = [OrderItemInline]
    actions = ["mark_paid"]

    @admin.action(description="Mark selected orders as paid")
    def mark_paid(self, request, queryset):
        updated = queryset.filter(status=OrderStatus.PENDING).update(status=OrderStatus.PAID)
        self.message_user(request, f"{updated} order(s) marked as paid.")
