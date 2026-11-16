"""Stripe payments for lesson bookings."""
from django.db import models
from django.utils import timezone

from bookings.models import Booking


class Payment(models.Model):
    """The payment for one booking, made through Stripe Checkout."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed or cancelled"
        REFUNDED = "refunded", "Refunded"
        REFUND_FAILED = "refund_failed", "Refund needs manual action"

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    amount_pence = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    created_on = models.DateTimeField(auto_now_add=True)
    paid_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.amount_display} for {self.booking.reference} ({self.get_status_display()})"

    @property
    def amount_display(self):
        return f"£{self.amount_pence / 100:.2f}"

    def mark_paid(self, payment_intent=""):
        """
        Record a successful payment and confirm the booking.
        Safe to call twice (success page and webhook). True the first time only.
        """
        if self.status == self.Status.PAID:
            return False
        self.status = self.Status.PAID
        self.paid_on = timezone.now()
        if payment_intent:
            self.stripe_payment_intent = payment_intent
        self.save(update_fields=["status", "paid_on", "stripe_payment_intent"])
        self.booking.confirm()
        return True

    def mark_failed(self):
        """Mark a still-pending payment as failed or abandoned."""
        if self.status == self.Status.PENDING:
            self.status = self.Status.FAILED
            self.save(update_fields=["status"])
