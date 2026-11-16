"""Forms for instructor profiles and learner reviews."""
from django import forms

from .models import WEEKDAY_NAMES, Instructor, Review

MAX_PHOTO_BYTES = 3 * 1024 * 1024


class InstructorProfileForm(forms.ModelForm):
    """Lets an instructor edit their own public profile and working pattern."""

    hourly_rate = forms.DecimalField(
        label="Hourly rate (£)",
        min_value=10,
        max_value=200,
        decimal_places=2,
        help_text="What learners pay for one hour. Longer lessons are priced pro rata.",
    )
    days = forms.MultipleChoiceField(
        label="Days you teach",
        choices=[(str(index), name) for index, name in enumerate(WEEKDAY_NAMES)],
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Instructor
        fields = (
            "tagline", "bio", "areas_covered", "teaches", "car", "photo",
            "day_start", "day_end", "is_accepting_pupils",
        )
        labels = {
            "tagline": "Short tagline",
            "is_accepting_pupils": "I'm taking new bookings",
            "day_start": "First lesson from",
            "day_end": "Last lesson ends by",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5, "data-max-length": 1200}),
            "day_start": forms.TimeInput(attrs={"type": "time", "step": 1800}, format="%H:%M"),
            "day_end": forms.TimeInput(attrs={"type": "time", "step": 1800}, format="%H:%M"),
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*", "data-preview": "photo-preview"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault("hourly_rate", self.instance.hourly_rate_pence / 100)
        self.initial.setdefault("days", list(self.instance.working_days))

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and hasattr(photo, "size") and photo.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError("Please choose a photo smaller than 3 MB.")
        return photo

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("day_start"), cleaned.get("day_end")
        if start and end and (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute) < 60:
            self.add_error("day_end", "Your working day must be at least one hour long.")
        return cleaned

    def save(self, commit=True):
        instructor = super().save(commit=False)
        instructor.hourly_rate_pence = int(self.cleaned_data["hourly_rate"] * 100)
        instructor.working_days = "".join(sorted(self.cleaned_data["days"]))
        if commit:
            instructor.save()
        return instructor


class ReviewForm(forms.ModelForm):
    """A learner's star rating and comment."""

    class Meta:
        model = Review
        fields = ("rating", "comment")
        labels = {"rating": "Your rating", "comment": "Your review"}
        widgets = {
            "rating": forms.RadioSelect(
                choices=[(5, "5 - Excellent"), (4, "4 - Good"), (3, "3 - OK"), (2, "2 - Poor"), (1, "1 - Bad")]
            ),
            "comment": forms.Textarea(attrs={
                "rows": 4,
                "data-max-length": 600,
                "placeholder": "How were the lessons? Would you recommend this instructor?",
            }),
        }

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()
        if len(comment) < 10:
            raise forms.ValidationError("Please write at least a sentence (10 characters).")
        return comment
