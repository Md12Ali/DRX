"""
UK postcode helpers used to check pick-ups are inside the area covered.

A full postcode such as "EC1A 1BB" has an outward code ("EC1A") and an
inward code ("1BB"). Coverage is decided by the postcode *district*: the
letters and digits at the start of the outward code ("EC1"), so EC1A, EC1M
and EC1V all count as EC1, and E1W (Wapping) counts as E1.
"""
import re

from django.conf import settings

FULL_POSTCODE = re.compile(r"^([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})$")
DISTRICT = re.compile(r"^([A-Z]{1,2}\d{1,2})")


def normalise(postcode):
    """'ec1a1bb ' -> 'EC1A 1BB'. Returns '' if it isn't a full UK postcode."""
    compact = re.sub(r"\s+", "", (postcode or "").upper())
    match = FULL_POSTCODE.match(compact)
    if not match:
        return ""
    return f"{match.group(1)} {match.group(2)}"


def district(postcode):
    """
    The postcode district, e.g. 'E14 9GE' -> 'E14', 'EC1A 1BB' -> 'EC1',
    'E1W 1AA' -> 'E1'. Also accepts just an outward code such as 'N1C'.
    Returns '' if it can't be read.
    """
    full = normalise(postcode)
    outward = full.split(" ")[0] if full else re.sub(r"\s+", "", (postcode or "").upper())
    match = DISTRICT.match(outward)
    return match.group(1) if match else ""


def is_covered(postcode):
    """True if the postcode's district is one we pick up from."""
    return district(postcode) in settings.COVERED_POSTCODE_DISTRICTS


def covered_list_display():
    """'E1, E2, E3, E8, E9, E14, EC1, EC2 and N1'."""
    districts = list(settings.COVERED_POSTCODE_DISTRICTS)
    if len(districts) == 1:
        return districts[0]
    return ", ".join(districts[:-1]) + " and " + districts[-1]
