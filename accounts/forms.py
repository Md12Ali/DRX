"""Forms for learner registration and contact details."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from core.postcodes import covered_list_display, is_covered, normalise

from .models import Profile

User = get_user_model()


class RegisterForm(UserCreationForm):
    """Sign-up form for learners."""

    first_name = forms.CharField(
        max_length=50,
        label="First name",
        help_text="So your instructor knows what to call you.",
    )
    email = forms.EmailField(
        required=True,
        help_text="We send booking confirmations and receipts here.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "username", "email")

    def clean_first_name(self):
        """Presence check after trimming spaces."""
        first_name = self.cleaned_data["first_name"].strip()
        if not first_name:
            raise forms.ValidationError("Please enter your first name.")
        return first_name

    def clean_email(self):
        """Email addresses must be unique (case-insensitive)."""
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    """Learner contact and pick-up details."""

    class Meta:
        model = Profile
        fields = ("phone", "pickup_address", "postcode", "transmission")
        labels = {
            "phone": "Mobile number",
            "pickup_address": "Pick-up address",
            "transmission": "I want to learn in a",
        }
        help_texts = {
            "phone": "Your instructor will text you if they're running late.",
            "pickup_address": "Where lessons usually start, e.g. 12 Roman Road, London.",
            "postcode": "Pick-ups are available in E1, E2, E3, E8, E9, E14, EC1, EC2 and N1.",
            "transmission": "My lessons are in an automatic car.",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "pickup_address": forms.TextInput(attrs={"autocomplete": "address-line1"}),
            "postcode": forms.TextInput(attrs={"autocomplete": "postal-code"}),
        }

    def clean_postcode(self):
        """Tidy the postcode and check it's inside the area covered."""
        raw = self.cleaned_data["postcode"].strip()
        if not raw:
            return ""
        postcode = normalise(raw)
        if not postcode:
            raise forms.ValidationError("Enter a valid UK postcode, for example E3 5AA.")
        if not is_covered(postcode):
            raise forms.ValidationError(
                f"Sorry, pick-ups are only available in {covered_list_display()}."
            )
        return postcode

    def clean_pickup_address(self):
        return self.cleaned_data["pickup_address"].strip()
