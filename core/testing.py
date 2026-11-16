"""Shared factories for the automated tests of every app."""
import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from bookings.models import Booking
from instructors.models import Instructor

User = get_user_model()
PASSWORD = "a-Strong-pass-123"


def make_learner(username="learner", complete_profile=True):
    """A learner, by default with a phone number and pick-up address."""
    user = User.objects.create_user(
        username=username, first_name=username.title(),
        email=f"{username}@example.com", password=PASSWORD,
    )
    if complete_profile:
        profile = user.profile
        profile.phone = "07700 900123"
        profile.pickup_address = "12 Roman Road, London"
        profile.postcode = "E3 5AA"
        profile.save()
    return user


def make_instructor(username="instructor", **extra):
    """An instructor who works every day from 08:00 to 20:00 at £35/hour."""
    user = User.objects.create_user(
        username=username, first_name="Sam", email=f"{username}@example.com", password=PASSWORD
    )
    fields = {
        "slug": username,
        "display_name": f"Sam {username.title()}",
        "areas_covered": "Bow, Hackney, E3",
        "hourly_rate_pence": 3500,
        "working_days": "0123456",
        "day_start": datetime.time(8, 0),
        "day_end": datetime.time(20, 0),
    }
    fields.update(extra)
    return Instructor.objects.create(user=user, **fields)


def future_start(days=3, hour=10, minute=0):
    """An aware datetime ``days`` from today at ``hour``:``minute`` local time."""
    date = timezone.localdate() + datetime.timedelta(days=days)
    return timezone.make_aware(datetime.datetime.combine(date, datetime.time(hour, minute)))


def make_booking(learner, instructor, start=None, status=Booking.Status.CONFIRMED, minutes=60, **extra):
    """A booking, confirmed by default."""
    return Booking.objects.create(
        learner=learner,
        instructor=instructor,
        start=start or future_start(),
        duration_minutes=minutes,
        pickup_address="12 Roman Road, London",
        pickup_postcode="E3 5AA",
        price_pence=instructor.lesson_price_pence(minutes),
        status=status,
        **extra,
    )
