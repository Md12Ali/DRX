"""Instructor directory, profiles, availability API and reviews."""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from bookings.models import Booking
from bookings.services import available_start_times

from .forms import InstructorProfileForm, ReviewForm
from .models import Instructor, Review

PREVIEW_DAYS = 14


def instructor_list(request):
    """All instructors, filterable by transmission and area or name."""
    instructors = Instructor.objects.with_ratings()
    query = request.GET.get("q", "").strip()[:60]
    transmission = request.GET.get("transmission", "")

    if query:
        instructors = instructors.filter(
            Q(areas_covered__icontains=query) | Q(display_name__icontains=query)
        )
    if transmission in (Instructor.Teaches.MANUAL, Instructor.Teaches.AUTOMATIC):
        instructors = instructors.filter(teaches__in=[transmission, Instructor.Teaches.BOTH])

    context = {
        "instructors": instructors.order_by("-is_accepting_pupils", "display_name"),
        "query": query,
        "transmission": transmission,
    }
    return render(request, "instructors/instructor_list.html", context)


def _upcoming_availability(instructor, days=PREVIEW_DAYS):
    """Number of free one-hour slots on each of the next ``days`` days."""
    today = timezone.localdate()
    summary = []
    for offset in range(days):
        day = today + datetime.timedelta(days=offset)
        free = len(available_start_times(instructor, day, 60)) if instructor.works_on(day) else 0
        summary.append({"date": day, "free": free, "working": instructor.works_on(day)})
    return summary


def instructor_detail(request, slug):
    """An instructor's public profile with prices, availability and reviews."""
    instructor = get_object_or_404(Instructor.objects.select_related("user"), slug=slug)
    average, count = instructor.rating_summary()

    can_review = False
    own_review = None
    if request.user.is_authenticated:
        own_review = instructor.reviews.filter(learner=request.user).first()
        can_review = own_review is None and Booking.objects.filter(
            instructor=instructor, learner=request.user, status=Booking.Status.COMPLETED
        ).exists()

    context = {
        "instructor": instructor,
        "average_rating": average,
        "review_count": count,
        "reviews": instructor.reviews.select_related("learner")[:20],
        "availability": _upcoming_availability(instructor) if instructor.is_accepting_pupils else [],
        "prices": instructor.price_table(),
        "can_review": can_review,
        "own_review": own_review,
    }
    return render(request, "instructors/instructor_detail.html", context)


def availability(request, slug):
    """JSON list of free start times, used by the booking form's time picker."""
    instructor = get_object_or_404(Instructor, slug=slug)
    try:
        date = datetime.date.fromisoformat(request.GET.get("date", ""))
        duration = int(request.GET.get("duration", "60"))
    except ValueError:
        return JsonResponse({"error": "Please choose a valid date."}, status=400)
    if duration not in Booking.Duration.values:
        return JsonResponse({"error": "Please choose a valid lesson length."}, status=400)

    exclude = None
    booking_id = request.GET.get("booking", "")
    if booking_id.isdigit() and request.user.is_authenticated:
        exclude = Booking.objects.filter(pk=int(booking_id), learner=request.user).first()

    times = available_start_times(instructor, date, duration, exclude_booking=exclude)
    return JsonResponse({
        "date": date.isoformat(),
        "works_that_day": instructor.works_on(date),
        "times": [timezone.localtime(time).strftime("%H:%M") for time in times],
    })


@login_required
def instructor_edit(request):
    """An instructor edits their own public profile."""
    instructor = getattr(request.user, "instructor", None)
    if instructor is None:
        raise PermissionDenied("Only instructors have a public profile to edit.")

    if request.method == "POST":
        form = InstructorProfileForm(request.POST, request.FILES, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Your public profile has been updated.")
            return redirect(instructor)
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = InstructorProfileForm(instance=instructor)
    return render(request, "instructors/instructor_form.html", {"form": form, "instructor": instructor})


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------
@login_required
def review_create(request, slug):
    """Leave a review. Only learners with a completed lesson may do so."""
    instructor = get_object_or_404(Instructor, slug=slug)
    has_completed_lesson = Booking.objects.filter(
        instructor=instructor, learner=request.user, status=Booking.Status.COMPLETED
    ).exists()
    if not has_completed_lesson:
        messages.error(request, "You can review an instructor after your first completed lesson.")
        return redirect(instructor)

    existing = instructor.reviews.filter(learner=request.user).first()
    if existing:
        messages.info(request, "You've already reviewed this instructor. You can edit your review.")
        return redirect("instructors:review_edit", existing.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.instructor = instructor
            review.learner = request.user
            review.save()
            messages.success(request, "Thanks for your review!")
            return redirect(f"{instructor.get_absolute_url()}#reviews")
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = ReviewForm()
    context = {"form": form, "instructor": instructor, "is_edit": False}
    return render(request, "instructors/review_form.html", context)


@login_required
def review_edit(request, pk):
    """Edit your own review."""
    review = get_object_or_404(Review.objects.select_related("instructor"), pk=pk, learner=request.user)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated.")
            return redirect(f"{review.instructor.get_absolute_url()}#reviews")
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = ReviewForm(instance=review)
    context = {"form": form, "instructor": review.instructor, "review": review, "is_edit": True}
    return render(request, "instructors/review_form.html", context)


@login_required
def review_delete(request, pk):
    """Confirm, then delete your own review."""
    review = get_object_or_404(Review.objects.select_related("instructor"), pk=pk, learner=request.user)
    if request.method == "POST":
        instructor = review.instructor
        review.delete()
        messages.success(request, "Your review has been deleted.")
        return redirect(instructor)
    return render(request, "instructors/review_confirm_delete.html", {"review": review})
