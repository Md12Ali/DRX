"""Business details available in every template."""
from django.conf import settings

from instructors.models import Instructor

from .postcodes import covered_list_display


def site_info(request):
    """Site name, the main instructor, prices and the area covered."""
    return {
        "site_name": settings.SITE_NAME,
        "main_instructor": Instructor.objects.main(),
        "hourly_rate_display": f"£{settings.STANDARD_HOURLY_RATE_PENCE / 100:.0f}",
        "covered_districts": settings.COVERED_POSTCODE_DISTRICTS,
        "covered_list": covered_list_display(),
    }
