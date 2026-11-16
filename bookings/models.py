"""Driving lesson bookings."""
import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from instructors.models import Instructor


class BookingQuerySet(models.QuerySet):
    """Reusable queries for bookings."""

    def _hold_cutoff(self):
        return timezone.now() - datetime.timedelta(minutes=settings.BOOKING_PAYMENT_HOLD_MINUTES)

    def holding_slot(self):
        """
        Bookings that block their time slot: confirmed or completed lessons,
        plus unpaid bookings still inside their payment hold window.
        """
        return self.filter(
            Q(status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED])
            | Q(status=Booking.Status.PENDING, created_on__gte=self._hold_cutoff())
        )

    def overlapping(self, start, end):
        """Bookings that overlap the period ``start`` to ``end``."""
        return self.filter(start__lt=end, end__gt=start)

    def upcoming(self):
        return self.filter(start__gte=timezone.now()).order_by("start")

    def past(self):
        return self.filter(start__lt=timezone.now()).order_by("-start")

    def expire_stale_holds(self):
        """Cancel unpaid bookings whose payment hold has run out. Returns the count."""
        return self.filter(
            status=Booking.Status.PENDING,
            created_on__lt=self._hold_cutoff(),
        ).update(status=Booking.Status.EXPIRED)


class Booking(models.Model):
    """One driving lesson between a learner and an instructor."""

    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting payment"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired (not paid)"

    class Duration(models.IntegerChoices):
        ONE_HOUR = 60, "1 hour"
        NINETY_MINUTES = 90, "1.5 hours"
        TWO_HOURS = 120, "2 hours"

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(
        choices=Duration.choices,
        default=Duration.ONE_HOUR,
    )
    pickup_address = models.CharField(max_length=200)
    learner_notes = models.TextField(max_length=500, blank=True)
    instructor_notes = models.TextField(max_length=1000, blank=True)
    price_pence = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        ordering = ["start"]
        constraints = [
            models.CheckConstraint(condition=Q(end__gt=models.F("start")), name="booking_ends_after_start"),
        ]

    def __str__(self):
        local_start = timezone.localtime(self.start)
        return f"{self.learner.username} with {self.instructor} on {local_start:%d %b %Y %H:%M}"

    def get_absolute_url(self):
        return reverse("bookings:detail", args=[self.pk])

    def save(self, *args, **kwargs):
        """Keep ``end`` in step with ``start`` and the duration."""
        self.end = self.start + datetime.timedelta(minutes=self.duration_minutes)
        super().save(*args, **kwargs)

    # -- Display -----------------------------------------------------------
    @property
    def price_display(self):
        return f"£{self.price_pence / 100:.2f}"

    @property
    def reference(self):
        """Short booking reference shown to customers, e.g. DRX-00042."""
        return f"DRX-{self.pk:05d}"

    # -- Rules -------------------------------------------------------------
    @property
    def is_upcoming(self):
        return self.start > timezone.now()

    @property
    def hold_expires_at(self):
        return self.created_on + datetime.timedelta(minutes=settings.BOOKING_PAYMENT_HOLD_MINUTES)

    @property
    def is_awaiting_payment(self):
        """Pending and still inside the payment hold window."""
        return self.status == self.Status.PENDING and timezone.now() < self.hold_expires_at

    @property
    def can_be_changed_by_learner(self):
        """Learners may reschedule or cancel until the change cut-off."""
        if self.status not in (self.Status.PENDING, self.Status.CONFIRMED):
            return False
        cutoff = datetime.timedelta(hours=settings.BOOKING_CHANGE_CUTOFF_HOURS)
        return self.start - timezone.now() >= cutoff

    @property
    def can_be_completed(self):
        """Instructors mark confirmed lessons complete once they've started."""
        return self.status == self.Status.CONFIRMED and self.start <= timezone.now()

    def cancel(self):
        """Cancel the booking. Returns True if it was cancelled now."""
        if self.status not in (self.Status.PENDING, self.Status.CONFIRMED):
            return False
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status", "updated_on"])
        return True

    def confirm(self):
        """Mark a paid booking as confirmed. Returns True if the status changed."""
        if self.status == self.Status.CONFIRMED:
            return False
        self.status = self.Status.CONFIRMED
        self.save(update_fields=["status", "updated_on"])
        return True
