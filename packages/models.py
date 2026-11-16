"""Prepaid lesson packages and the hours learners have left."""
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking


class LessonPackage(models.Model):
    """A bundle of lesson hours sold at a discount, e.g. 10 hours for £330."""

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    hours = models.PositiveSmallIntegerField()
    price_pence = models.PositiveIntegerField()
    description = models.CharField(max_length=200, blank=True)
    is_popular = models.BooleanField(default=False, help_text="Highlight as the most popular package.")
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "hours"]

    def __str__(self):
        return f"{self.name} ({self.hours} hours)"

    def get_absolute_url(self):
        return reverse("packages:list") + f"#package-{self.slug}"

    @property
    def price_display(self):
        return f"£{self.price_pence / 100:.0f}"

    @property
    def per_hour_display(self):
        return f"£{self.price_pence / self.hours / 100:.2f}"

    @property
    def full_price_pence(self):
        """What these hours would cost one lesson at a time."""
        return self.hours * settings.STANDARD_HOURLY_RATE_PENCE

    @property
    def saving_pence(self):
        return max(self.full_price_pence - self.price_pence, 0)

    @property
    def saving_display(self):
        return f"£{self.saving_pence / 100:.0f}"


class PackagePurchase(models.Model):
    """One learner buying one package through Stripe."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed or cancelled"

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="package_purchases",
    )
    package = models.ForeignKey(LessonPackage, on_delete=models.PROTECT, related_name="purchases")
    hours = models.PositiveSmallIntegerField(help_text="Copied from the package when bought.")
    price_pence = models.PositiveIntegerField(help_text="Copied from the package when bought.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    paid_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.learner.username}: {self.package.name} ({self.get_status_display()})"

    @property
    def price_display(self):
        return f"£{self.price_pence / 100:.2f}"

    def mark_paid(self, payment_intent=""):
        """Record payment. Safe to call twice; True the first time only."""
        if self.status == self.Status.PAID:
            return False
        self.status = self.Status.PAID
        self.paid_on = timezone.now()
        if payment_intent:
            self.stripe_payment_intent = payment_intent
        self.save(update_fields=["status", "paid_on", "stripe_payment_intent"])
        return True

    def mark_failed(self):
        if self.status == self.Status.PENDING:
            self.status = self.Status.FAILED
            self.save(update_fields=["status"])


def package_minutes_balance(learner):
    """
    Minutes of prepaid lessons the learner has left.

    Bought = every paid package. Used = confirmed or completed lessons paid
    with package hours. Because it's calculated, cancelling a lesson paid
    with package hours gives the hours back automatically.
    """
    if not learner.is_authenticated:
        return 0
    bought_hours = learner.package_purchases.filter(
        status=PackagePurchase.Status.PAID
    ).aggregate(total=Sum("hours"))["total"] or 0
    used_minutes = learner.bookings.filter(
        payment_method=Booking.PaymentMethod.PACKAGE,
        status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED],
    ).aggregate(total=Sum("duration_minutes"))["total"] or 0
    return bought_hours * 60 - used_minutes


def hours_display(minutes):
    """150 -> '2.5'."""
    return f"{minutes / 60:g}"
