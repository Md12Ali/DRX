"""Learner details stored alongside Django's built-in User."""
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

UK_PHONE_VALIDATOR = RegexValidator(
    regex=r"^(\+44\s?7\d{3}|07\d{3})\s?\d{3}\s?\d{3}$",
    message="Enter a UK mobile number, for example 07700 900123.",
)
UK_POSTCODE_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$",
    message="Enter a valid UK postcode, for example IG3 8XX.",
)


class Transmission(models.TextChoices):
    """Shared by learners (preference) and instructors (what they teach)."""

    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"


class Profile(models.Model):
    """Contact and pick-up details, created automatically for every user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, blank=True, validators=[UK_PHONE_VALIDATOR])
    pickup_address = models.CharField(max_length=200, blank=True)
    postcode = models.CharField(max_length=10, blank=True, validators=[UK_POSTCODE_VALIDATOR])
    transmission = models.CharField(
        max_length=10,
        choices=Transmission.choices,
        default=Transmission.MANUAL,
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def is_instructor(self):
        """True if this user also has an instructor record."""
        return hasattr(self.user, "instructor")

    @property
    def full_pickup_address(self):
        """Address and postcode on one line, used to pre-fill bookings."""
        parts = [part for part in (self.pickup_address, self.postcode.upper()) if part]
        return ", ".join(parts)

    @property
    def is_complete(self):
        """Learners need a phone number and pick-up address before booking."""
        return bool(self.phone and self.pickup_address and self.postcode)
