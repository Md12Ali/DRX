"""Site-wide pages: home, about, the area checker and error handlers."""
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from bookings.models import Booking
from instructors.models import Instructor, Review
from packages.models import LessonPackage

from .postcodes import district, is_covered, normalise


def _postcode_check(raw):
    """A small result dict for the 'Do you cover my area?' checker."""
    raw = (raw or "").strip()[:10]
    if not raw:
        return None
    found = district(raw)
    if not found:
        return {"postcode": raw, "valid": False, "covered": False}
    return {
        "postcode": normalise(raw) or raw.upper(),
        "valid": True,
        "district": found,
        "covered": is_covered(raw),
        "areas": settings.COVERED_POSTCODE_DISTRICTS.get(found, ""),
    }


def home(request):
    """Personal landing page: the instructor, prices, area covered and reviews."""
    instructor = Instructor.objects.with_ratings().order_by("-is_accepting_pupils", "created_on").first()
    context = {
        "instructor": instructor,
        "packages": LessonPackage.objects.filter(is_active=True)[:3],
        "lessons_completed": Booking.objects.filter(status=Booking.Status.COMPLETED).count(),
        "latest_reviews": Review.objects.select_related("learner").filter(rating__gte=4)[:3],
        "postcode_result": _postcode_check(request.GET.get("postcode")),
    }
    return render(request, "core/home.html", context)


def postcode_check(request):
    """JSON version of the area checker, used by the home page script."""
    result = _postcode_check(request.GET.get("postcode"))
    if result is None:
        return JsonResponse({"error": "Please enter a postcode."}, status=400)
    return JsonResponse(result)


def about(request):
    """How booking works, prices, packages and the cancellation policy."""
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
