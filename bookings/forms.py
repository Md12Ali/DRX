"""Forms for booking and rescheduling lessons."""
import datetime

from django import forms
from django.utils import timezone

from core.postcodes import covered_list_display, is_covered, normalise

from .models import Booking
from .services import booking_problems


class BookingForm(forms.ModelForm):
    """
    Book a new lesson, or reschedule an existing one.

    ``instructor`` and ``learner`` are passed in by the view. When editing
    an existing booking the lesson length can't change, because it has
    already been paid for.
    """

    date = forms.DateField(
        label="Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "js-booking-date"}),
    )
    start_time = forms.TimeField(
        label="Start time",
        help_text="Lessons start on the hour.",
        widget=forms.TimeInput(
            attrs={"type": "time", "step": 1800, "class": "js-booking-time"},
            format="%H:%M",
        ),
    )

    class Meta:
        model = Booking
        fields = ("duration_minutes", "pickup_address", "pickup_postcode", "learner_notes")
        labels = {
            "duration_minutes": "Lesson length",
            "pickup_address": "Pick-up address",
            "pickup_postcode": "Pick-up postcode",
            "learner_notes": "Anything your instructor should know? (optional)",
        }
        widgets = {
            "duration_minutes": forms.RadioSelect(attrs={"class": "js-booking-duration"}),
            "learner_notes": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "e.g. I'd like to practise roundabouts, or my test is on 3 March.",
                "data-max-length": 500,
            }),
        }

    def __init__(self, *args, instructor, learner, **kwargs):
        super().__init__(*args, **kwargs)
        self.instructor = instructor
        self.learner = learner
        today = timezone.localdate()
        self.fields["date"].widget.attrs.update({
            "min": today.isoformat(),
            "max": (today + datetime.timedelta(weeks=8)).isoformat(),
            "data-availability-url": instructor.get_absolute_url() + "availability/",
        })

        if self.instance.pk:
            # Rescheduling: fill date/time from the booking, lock the length.
            local_start = timezone.localtime(self.instance.start)
            self.initial.setdefault("date", local_start.date())
            self.initial.setdefault("start_time", local_start.time())
            self.fields["duration_minutes"].disabled = True
            self.fields["duration_minutes"].help_text = (
                "The length of a paid lesson can't be changed. Cancel and rebook instead."
            )
        elif not self.initial.get("pickup_address"):
            # Never ask for information we already have.
            self.initial["pickup_address"] = learner.profile.pickup_address
            self.initial["pickup_postcode"] = learner.profile.postcode
        self.fields["pickup_postcode"].required = True
        self.fields["pickup_postcode"].help_text = f"Pick-ups in {covered_list_display()}."

    def clean_pickup_address(self):
        address = self.cleaned_data["pickup_address"].strip()
        if len(address) < 6:
            raise forms.ValidationError("Please enter a full pick-up address.")
        return address

    def clean_pickup_postcode(self):
        """Valid UK postcode inside the area covered."""
        postcode = normalise(self.cleaned_data["pickup_postcode"])
        if not postcode:
            raise forms.ValidationError("Enter a valid UK postcode, for example E3 5AA.")
        if not is_covered(postcode):
            raise forms.ValidationError(
                f"Sorry, pick-ups are only available in {covered_list_display()}."
            )
        return postcode

    def clean(self):
        """Combine date and time, then check every booking rule."""
        cleaned = super().clean()
        date = cleaned.get("date")
        start_time = cleaned.get("start_time")
        duration = cleaned.get("duration_minutes")
        if not (date and start_time and duration):
            return cleaned

        start = timezone.make_aware(datetime.datetime.combine(date, start_time))
        problems = booking_problems(
            self.instructor,
            self.learner,
            start,
            int(duration),
            exclude_booking=self.instance if self.instance.pk else None,
        )
        for problem in problems:
            self.add_error(None, problem)
        cleaned["start"] = start
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.start = self.cleaned_data["start"]
        if not booking.pk:
            booking.learner = self.learner
            booking.instructor = self.instructor
            booking.price_pence = self.instructor.lesson_price_pence(booking.duration_minutes)
        if commit:
            booking.save()
        return booking


class CompleteLessonForm(forms.ModelForm):
    """Instructor's notes when marking a lesson as complete."""

    class Meta:
        model = Booking
        fields = ("instructor_notes",)
        labels = {"instructor_notes": "Lesson notes for the learner"}
        widgets = {
            "instructor_notes": forms.Textarea(attrs={
                "rows": 5,
                "data-max-length": 1000,
                "placeholder": "What went well, what to practise next time…",
            }),
        }
