"""Instructors, their working pattern, and reviews left by learners."""
import datetime

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils import timezone

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class InstructorQuerySet(models.QuerySet):
    """Reusable queries for instructors."""

    def accepting(self):
        """Instructors currently taking new learners."""
        return self.filter(is_accepting_pupils=True)

    def main(self):
        """
        The instructor this website is built around: the first one who is
        taking bookings (or the first one at all). Lets the site work as a
        personal website today and grow into a multi-instructor school later.
        """
        return self.order_by("-is_accepting_pupils", "created_on").first()

    def with_ratings(self):
        """Attach the average rating and number of reviews."""
        return self.select_related("user").annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews", distinct=True),
        )


class Instructor(models.Model):
    """A DVSA-approved driving instructor who teaches through DRX."""

    class Qualification(models.TextChoices):
        TRAINEE = "trainee", "Trainee driving instructor (DVSA trainee licence)"
        ADI = "adi", "DVSA Approved Driving Instructor (ADI)"

    class Teaches(models.TextChoices):
        MANUAL = "manual", "Manual"
        AUTOMATIC = "automatic", "Automatic"
        BOTH = "both", "Manual and automatic"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor",
    )
    slug = models.SlugField(max_length=60, unique=True)
    display_name = models.CharField(max_length=60)
    tagline = models.CharField(max_length=120, blank=True)
    qualification = models.CharField(
        max_length=10,
        choices=Qualification.choices,
        default=Qualification.TRAINEE,
        help_text="Only choose ADI once you're on the ADI register. Trainees must not advertise as ADIs.",
    )
    bio = models.TextField(max_length=1200, blank=True)
    areas_covered = models.CharField(
        max_length=200,
        help_text="Comma-separated towns or postcode areas, e.g. Ilford, Romford, IG3",
    )
    teaches = models.CharField(max_length=10, choices=Teaches.choices, default=Teaches.AUTOMATIC)
    car = models.CharField(max_length=80, blank=True)
    photo = models.ImageField(upload_to="instructors/", blank=True)
    hourly_rate_pence = models.PositiveIntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(20000)],
        default=3500,
    )
    working_days = models.CharField(
        max_length=7,
        default="012345",
        help_text="Days worked: 0 = Monday ... 6 = Sunday. '012345' is Monday to Saturday.",
    )
    day_start = models.TimeField(default=datetime.time(8, 0))
    day_end = models.TimeField(default=datetime.time(20, 0))
    is_accepting_pupils = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = InstructorQuerySet.as_manager()

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("instructors:detail", args=[self.slug])

    # -- Display helpers ---------------------------------------------------
    @property
    def first_name(self):
        return self.display_name.split()[0]

    @property
    def initials(self):
        words = self.display_name.split()
        return "".join(word[0] for word in words[:2]).upper()

    @property
    def hourly_rate_display(self):
        return f"£{self.hourly_rate_pence / 100:.0f}"

    @property
    def is_adi(self):
        return self.qualification == self.Qualification.ADI

    @property
    def area_list(self):
        return [area.strip() for area in self.areas_covered.split(",") if area.strip()]

    @property
    def working_days_display(self):
        """E.g. 'Mon, Tue, Wed, Thu, Fri, Sat'."""
        return ", ".join(WEEKDAY_NAMES[int(day)] for day in sorted(self.working_days) if day.isdigit())

    # -- Business data -----------------------------------------------------
    def teaches_transmission(self, transmission):
        """True if the instructor teaches the given transmission type."""
        return self.teaches in (self.Teaches.BOTH, transmission)

    def lesson_price_pence(self, minutes):
        """Price of a lesson of ``minutes`` length, rounded to the nearest penny."""
        return round(self.hourly_rate_pence * minutes / 60)

    def price_table(self):
        """[(label, '£40.00'), ...] for every lesson length on offer."""
        lengths = [(60, "1 hour"), (90, "1.5 hours"), (120, "2 hours")]
        return [(label, f"£{self.lesson_price_pence(minutes) / 100:.2f}") for minutes, label in lengths]

    def works_on(self, date):
        """True if ``date`` is one of the instructor's working days."""
        return str(date.weekday()) in self.working_days

    def candidate_start_times(self, date, duration_minutes):
        """
        Every start time on ``date`` (as aware datetimes) at which a lesson of
        ``duration_minutes`` fits inside working hours. Clashes and notice
        periods are checked separately by the bookings app.
        """
        if not self.works_on(date):
            return []

        step = datetime.timedelta(minutes=settings.BOOKING_SLOT_STEP_MINUTES)
        length = datetime.timedelta(minutes=duration_minutes)
        current_tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.datetime.combine(date, self.day_start), current_tz)
        last_end = timezone.make_aware(datetime.datetime.combine(date, self.day_end), current_tz)

        times = []
        while start + length <= last_end:
            times.append(start)
            start += step
        return times

    def rating_summary(self):
        """(average rating rounded to 1dp or None, number of reviews)."""
        stats = self.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        average = round(stats["avg"], 1) if stats["avg"] is not None else None
        return average, stats["count"]


class Review(models.Model):
    """A learner's review of an instructor, after at least one completed lesson."""

    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name="reviews")
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(max_length=600)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_on"]
        constraints = [
            models.UniqueConstraint(fields=["instructor", "learner"], name="one_review_per_learner"),
        ]

    def __str__(self):
        return f"{self.rating}/5 for {self.instructor} by {self.learner.username}"

    @property
    def stars(self):
        """E.g. '★★★★☆' for a rating of 4."""
        return "★" * self.rating + "☆" * (5 - self.rating)
