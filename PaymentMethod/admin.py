from django.contrib import admin
from .models import Payment, PaymentMethod, Invoice


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order_id", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_id", "transaction_id", "user__username", "user__email")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "method_type", "is_default", "is_active", "created_at")
    list_filter = ("method_type", "is_default", "is_active", "created_at")
    search_fields = ("user__username", "user__email", "upi_id", "paypal_email", "bank_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-id",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "payment", "invoice_user", "invoice_total", "issued_at")
    list_filter = ("issued_at",)
    search_fields = ("invoice_number", "payment__order_id", "payment__user__username", "payment__user__email")
    readonly_fields = ("issued_at",)
    ordering = ("-issued_at",)

    def invoice_user(self, obj):
        return obj.payment.user.username if obj.payment and obj.payment.user else "-"
    invoice_user.short_description = "User"

    def invoice_total(self, obj):
        return obj.payment.amount if obj.payment else 0
    invoice_total.short_description = "Total"