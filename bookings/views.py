"""Views for learners' bookings and instructors' diaries."""
import datetime
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from instructors.models import Instructor
from packages.models import hours_display, package_minutes_balance
from payments.refunds import refund_booking
from progress.models import progress_summary

from .forms import BookingForm, CompleteLessonForm
from .models import Booking

logger = logging.getLogger(__name__)


def _instructor_or_403(request):
    """Return the logged-in user's Instructor record, or refuse access."""
    instructor = getattr(request.user, "instructor", None)
    if instructor is None:
        raise PermissionDenied("Only instructors can see this page.")
    return instructor


# ---------------------------------------------------------------------------
# Learner pages
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    """Learner home: upcoming and past lessons plus a progress summary."""
    if hasattr(request.user, "instructor"):
        return redirect("bookings:diary")

    Booking.objects.expire_stale_holds()
    bookings = request.user.bookings.select_related("instructor")
    upcoming = bookings.upcoming().exclude(
        status__in=[Booking.Status.CANCELLED, Booking.Status.EXPIRED]
    )
    context = {
        "upcoming": upcoming,
        "next_lesson": upcoming.filter(status=Booking.Status.CONFIRMED).first(),
        "past": bookings.past()[:10],
        "progress": progress_summary(request.user),
        "package_hours": hours_display(package_minutes_balance(request.user)),
        "hours_driven": sum(
            booking.duration_minutes for booking in bookings.filter(status=Booking.Status.COMPLETED)
        ) / 60,
    }
    return render(request, "bookings/dashboard.html", context)


@login_required
def booking_create(request, slug):
    """Choose a date, time and length for a lesson with an instructor."""
    instructor = get_object_or_404(Instructor, slug=slug)

    if hasattr(request.user, "instructor"):
        messages.info(request, "Instructor accounts can't book lessons.")
        return redirect(instructor)
    if not instructor.is_accepting_pupils:
        messages.warning(request, f"{instructor.first_name} isn't taking new bookings right now.")
        return redirect(instructor)
    if not request.user.profile.is_complete:
        messages.info(request, "Please add your phone number and pick-up address first.")
        return redirect(f"{reverse('accounts:profile')}?next={request.path}")

    Booking.objects.expire_stale_holds()
    if request.method == "POST":
        form = BookingForm(request.POST, instructor=instructor, learner=request.user)
        if form.is_valid():
            booking = form.save()
            messages.success(
                request,
                f"We're holding {timezone.localtime(booking.start):%A %d %B at %H:%M} for you. "
                "Pay now to confirm it.",
            )
            return redirect("payments:checkout", booking.pk)
        messages.error(request, "That lesson couldn't be booked. Please check the details below.")
    else:
        initial = {}
        if request.GET.get("date"):
            initial["date"] = request.GET["date"]
        form = BookingForm(initial=initial, instructor=instructor, learner=request.user)

    context = {"form": form, "instructor": instructor, "is_edit": False}
    return render(request, "bookings/booking_form.html", context)


def _learner_booking(request, pk):
    """Get a booking that belongs to the logged-in learner, or 404."""
    return get_object_or_404(
        Booking.objects.select_related("instructor", "instructor__user"),
        pk=pk,
        learner=request.user,
    )


@login_required
def booking_detail(request, pk):
    """One booking. Visible to its learner and its instructor only."""
    booking = get_object_or_404(
        Booking.objects.select_related("instructor", "instructor__user", "learner", "learner__profile"),
        pk=pk,
    )
    is_instructor = booking.instructor.user == request.user
    if booking.learner != request.user and not is_instructor:
        raise PermissionDenied("This isn't your booking.")
    payment = getattr(booking, "payment", None)
    context = {"booking": booking, "is_booking_instructor": is_instructor, "payment": payment}
    return render(request, "bookings/booking_detail.html", context)


@login_required
def booking_edit(request, pk):
    """Reschedule a booking (date, time, pick-up, notes)."""
    booking = _learner_booking(request, pk)
    if not booking.can_be_changed_by_learner:
        messages.error(
            request,
            "This lesson can no longer be changed online. Please call your instructor.",
        )
        return redirect(booking)

    if request.method == "POST":
        form = BookingForm(
            request.POST, instance=booking, instructor=booking.instructor, learner=request.user
        )
        if form.is_valid():
            booking = form.save()
            messages.success(request, f"Lesson moved to {timezone.localtime(booking.start):%A %d %B at %H:%M}.")
            return redirect(booking)
        messages.error(request, "That change couldn't be saved. Please check the details below.")
    else:
        form = BookingForm(instance=booking, instructor=booking.instructor, learner=request.user)

    context = {"form": form, "instructor": booking.instructor, "booking": booking, "is_edit": True}
    return render(request, "bookings/booking_form.html", context)


@login_required
def booking_cancel(request, pk):
    """Confirm, then cancel a booking and refund it if it was paid."""
    booking = _learner_booking(request, pk)
    if not booking.can_be_changed_by_learner:
        messages.error(
            request,
            "This lesson can no longer be cancelled online. Please call your instructor.",
        )
        return redirect(booking)

    if request.method == "POST":
        was_paid = booking.status == Booking.Status.CONFIRMED
        booking.cancel()
        if was_paid and booking.paid_with_package:
            messages.success(
                request,
                f"Lesson cancelled. {booking.hours_label} went back into your package.",
            )
        elif was_paid:
            if refund_booking(booking):
                messages.success(
                    request,
                    f"Lesson cancelled. A refund of {booking.price_display} is on its way "
                    "(5–10 working days).",
                )
            else:
                messages.warning(
                    request,
                    "Lesson cancelled. We couldn't process your refund automatically, "
                    "so the DRX team will refund you by hand within 2 working days.",
                )
        else:
            messages.success(request, "Booking cancelled. You haven't been charged.")
        return redirect("bookings:dashboard")
    return render(request, "bookings/booking_confirm_cancel.html", {"booking": booking})


# ---------------------------------------------------------------------------
# Instructor pages
# ---------------------------------------------------------------------------
@login_required
def diary(request):
    """Instructor's diary: the next 14 days of lessons and lessons to sign off."""
    instructor = _instructor_or_403(request)
    Booking.objects.expire_stale_holds()

    lessons = instructor.bookings.select_related("learner", "learner__profile")
    upcoming = lessons.upcoming().filter(status=Booking.Status.CONFIRMED)

    days = []
    today = timezone.localdate()
    for offset in range(14):
        day = today + datetime.timedelta(days=offset)
        day_lessons = [lesson for lesson in upcoming if timezone.localtime(lesson.start).date() == day]
        days.append({"date": day, "lessons": day_lessons, "working": instructor.works_on(day)})

    context = {
        "instructor": instructor,
        "days": days,
        "to_complete": lessons.filter(status=Booking.Status.CONFIRMED).past(),
        "learners": instructor.bookings.exclude(
            status__in=[Booking.Status.CANCELLED, Booking.Status.EXPIRED]
        ).values_list("learner__username", "learner__first_name").distinct().order_by("learner__first_name"),
    }
    return render(request, "bookings/diary.html", context)


@login_required
def booking_complete(request, pk):
    """Instructor marks a lesson as completed and leaves notes."""
    instructor = _instructor_or_403(request)
    booking = get_object_or_404(Booking, pk=pk, instructor=instructor)
    if not booking.can_be_completed:
        messages.error(request, "Only confirmed lessons that have started can be signed off.")
        return redirect(booking)

    if request.method == "POST":
        form = CompleteLessonForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = Booking.Status.COMPLETED
            booking.save()
            messages.success(request, f"Lesson with {booking.learner.first_name} signed off.")
            return redirect("progress:learner", booking.learner.username)
    else:
        form = CompleteLessonForm(instance=booking)
    return render(request, "bookings/booking_complete.html", {"form": form, "booking": booking})


@login_required
@require_POST
def instructor_cancel(request, pk):
    """Instructor cancels a lesson (e.g. illness). Always refunds the learner."""
    instructor = _instructor_or_403(request)
    booking = get_object_or_404(Booking, pk=pk, instructor=instructor)
    was_paid = booking.status == Booking.Status.CONFIRMED
    if not booking.cancel():
        messages.error(request, "That lesson can't be cancelled.")
        return redirect(booking)
    if was_paid and booking.paid_with_package:
        messages.success(request, "Lesson cancelled. The learner's package hours have been returned.")
    elif was_paid and not refund_booking(booking):
        messages.warning(request, "Lesson cancelled, but the refund failed. Please refund it in Stripe.")
    else:
        messages.success(request, "Lesson cancelled and the learner refunded.")
    return redirect("bookings:diary")
