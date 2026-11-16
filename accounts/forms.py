"""Forms for learner registration and contact details."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

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
            "pickup_address": "Where lessons usually start, e.g. 12 High Road, Ilford.",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "pickup_address": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "postcode": forms.TextInput(attrs={"autocomplete": "postal-code"}),
        }

    def clean_postcode(self):
        """Store postcodes in capitals for consistency."""
        return self.cleaned_data["postcode"].strip().upper()

    def clean_pickup_address(self):
        return self.cleaned_data["pickup_address"].strip()
