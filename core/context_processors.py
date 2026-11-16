"""Business details available in every template."""
from django.conf import settings

from instructors.models import Instructor

from .postcodes import covered_list_display


def site_info(request):
    """Site name, the main instructor, prices and the area covered."""
    phone = settings.CONTACT_PHONE
    digits = "".join(ch for ch in phone if ch.isdigit())
    return {
        "site_name": settings.SITE_NAME,
        "contact_phone": phone,
        # UK mobile 07... becomes +447... for tel: and sms: links
        "contact_phone_link": "+44" + digits[1:] if digits.startswith("0") else "+" + digits,
        "main_instructor": Instructor.objects.main(),
        "hourly_rate_display": f"£{settings.STANDARD_HOURLY_RATE_PENCE / 100:.0f}",
        "covered_districts": settings.COVERED_POSTCODE_DISTRICTS,
        "covered_list": covered_list_display(),
    }
