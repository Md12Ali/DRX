"""Progress pages for learners and instructors."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking

from .forms import SkillRatingsForm
from .models import Skill, SkillRating, progress_summary

User = get_user_model()


@login_required
def my_progress(request):
    """A learner's own progress across the syllabus."""
    if hasattr(request.user, "instructor"):
        return redirect("bookings:diary")
    context = {
        "summary": progress_summary(request.user),
        "levels": SkillRating.Level.choices,
    }
    return render(request, "progress/my_progress.html", context)


@login_required
def learner_progress(request, username):
    """An instructor views and updates one of their learners' skills."""
    instructor = getattr(request.user, "instructor", None)
    if instructor is None:
        raise PermissionDenied("Only instructors can rate skills.")

    learner = get_object_or_404(User, username=username)
    teaches_learner = Booking.objects.filter(
        instructor=instructor,
        learner=learner,
        status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED],
    ).exists()
    if not teaches_learner:
        raise PermissionDenied("You can only rate learners who have booked with you.")

    skills = Skill.objects.all()
    current_levels = dict(learner.skill_ratings.values_list("skill_id", "level"))

    if request.method == "POST":
        form = SkillRatingsForm(request.POST, skills=skills, current_levels=current_levels)
        if form.is_valid():
            changes = form.save(learner, request.user)
            if changes:
                messages.success(
                    request,
                    f"Saved {changes} skill update{'s' if changes != 1 else ''} for {learner.first_name}.",
                )
            else:
                messages.info(request, "Nothing changed.")
            return redirect("progress:learner", learner.username)
        messages.error(request, "Please choose a level for every skill.")
    else:
        form = SkillRatingsForm(skills=skills, current_levels=current_levels)

    context = {
        "learner": learner,
        "form": form,
        "summary": progress_summary(learner),
        "recent_lessons": Booking.objects.filter(
            instructor=instructor, learner=learner, status=Booking.Status.COMPLETED
        ).order_by("-start")[:5],
    }
    return render(request, "progress/learner_progress.html", context)
