"""
Booking rules: which start times are free and whether a requested lesson
is allowed. Kept in one module so the form, the availability API and the
tests all use exactly the same logic.
"""
import datetime

from django.conf import settings
from django.utils import timezone

from .models import Booking


def booking_window():
    """(earliest allowed start, latest allowed start) as aware datetimes."""
    now = timezone.now()
    earliest = now + datetime.timedelta(hours=settings.BOOKING_MIN_NOTICE_HOURS)
    latest = now + datetime.timedelta(weeks=settings.BOOKING_MAX_WEEKS_AHEAD)
    return earliest, latest


def available_start_times(instructor, date, duration_minutes, exclude_booking=None):
    """
    Free start times for ``instructor`` on ``date`` for a lesson of
    ``duration_minutes``. Removes times inside the notice period, beyond the
    booking window, or overlapping another booking that holds its slot.
    """
    earliest, latest = booking_window()
    length = datetime.timedelta(minutes=duration_minutes)

    taken = instructor.bookings.holding_slot()
    if exclude_booking is not None:
        taken = taken.exclude(pk=exclude_booking.pk)
    day_start = timezone.make_aware(datetime.datetime.combine(date, datetime.time.min))
    taken = list(taken.overlapping(day_start, day_start + datetime.timedelta(days=1)))

    free = []
    for start in instructor.candidate_start_times(date, duration_minutes):
        if start < earliest or start > latest:
            continue
        end = start + length
        clashes = any(booking.start < end and booking.end > start for booking in taken)
        if not clashes:
            free.append(start)
    return free


def booking_problems(instructor, learner, start, duration_minutes, exclude_booking=None):
    """
    Return a list of human-readable reasons why this lesson can't be booked.
    An empty list means the booking is allowed.
    """
    problems = []
    end = start + datetime.timedelta(minutes=duration_minutes)
    earliest, latest = booking_window()
    local_start = timezone.localtime(start)

    if not instructor.is_accepting_pupils:
        problems.append(f"{instructor.first_name} isn't taking new bookings at the moment.")
    if start < earliest:
        problems.append(
            f"Lessons need to be booked at least {settings.BOOKING_MIN_NOTICE_HOURS} hours ahead."
        )
    if start > latest:
        problems.append(
            f"You can book up to {settings.BOOKING_MAX_WEEKS_AHEAD} weeks ahead."
        )
    if local_start.minute % settings.BOOKING_SLOT_STEP_MINUTES or local_start.second:
        problems.append("Lessons start on the hour or half past the hour.")
    if not instructor.works_on(local_start.date()):
        problems.append(f"{instructor.first_name} doesn't teach on {local_start:%A}s.")
    elif start not in instructor.candidate_start_times(local_start.date(), duration_minutes):
        problems.append(
            f"{instructor.first_name} teaches between {instructor.day_start:%H:%M} "
            f"and {instructor.day_end:%H:%M}."
        )

    instructor_clash = instructor.bookings.holding_slot().overlapping(start, end)
    learner_clash = Booking.objects.filter(learner=learner).holding_slot().overlapping(start, end)
    if exclude_booking is not None:
        instructor_clash = instructor_clash.exclude(pk=exclude_booking.pk)
        learner_clash = learner_clash.exclude(pk=exclude_booking.pk)
    if instructor_clash.exists():
        problems.append("Sorry, that time has just been booked. Please pick another slot.")
    elif learner_clash.exists():
        problems.append("You already have a lesson booked at that time.")

    return problems
