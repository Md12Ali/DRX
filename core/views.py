"""Site-wide pages: landing page, about page and error handlers."""
from django.db.models import Min
from django.shortcuts import render

from bookings.models import Booking
from instructors.models import Instructor, Review
from progress.models import Skill


def home(request):
    """Landing page: what DRX is, who teaches, what it costs."""
    instructors = Instructor.objects.with_ratings().accepting()
    context = {
        "featured_instructors": instructors.order_by("-review_count", "display_name")[:3],
        "instructor_count": instructors.count(),
        "from_price": instructors.aggregate(lowest=Min("hourly_rate_pence"))["lowest"],
        "lessons_completed": Booking.objects.filter(status=Booking.Status.COMPLETED).count(),
        "skill_count": Skill.objects.count(),
        "latest_reviews": Review.objects.select_related("instructor", "learner").filter(rating__gte=4)[:3],
    }
    return render(request, "core/home.html", context)


def about(request):
    """How DRX works, prices and cancellation policy."""
    return render(request, "core/about.html")


def page_not_found(request, exception):
    """Custom 404 with clear routes back into the site."""
    return render(request, "404.html", status=404)


def permission_denied(request, exception):
    """Custom 403 for pages a user isn't allowed to see."""
    return render(request, "403.html", status=403)


def server_error(request):
    """Custom 500 page."""
    return render(request, "500.html", status=500)
