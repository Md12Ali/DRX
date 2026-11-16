"""Admin configuration for payments."""
from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount_display", "status", "created_on", "paid_on")
    list_filter = ("status",)
    search_fields = ("booking__learner__username", "stripe_session_id", "stripe_payment_intent")
    readonly_fields = ("stripe_session_id", "stripe_payment_intent", "created_on", "paid_on")
