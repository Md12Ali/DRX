"""Automated tests for the accounts app."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.testing import PASSWORD, make_instructor, make_learner

from .forms import ProfileForm, RegisterForm
from .models import Profile

User = get_user_model()


class ProfileModelTests(TestCase):
    def test_profile_created_automatically(self):
        user = make_learner("amira", complete_profile=False)
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertFalse(user.profile.is_complete)

    def test_full_pickup_address(self):
        user = make_learner("amira")
        self.assertEqual(user.profile.full_pickup_address, "12 High Road, Ilford, IG3 8XX")
        self.assertTrue(user.profile.is_complete)

    def test_is_instructor(self):
        instructor = make_instructor("sam")
        self.assertTrue(instructor.user.profile.is_instructor)
        self.assertFalse(make_learner("amira").profile.is_instructor)


class FormTests(TestCase):
    def test_register_requires_unique_email(self):
        make_learner("amira")
        form = RegisterForm(data={
            "first_name": "Amy", "username": "amy", "email": "AMIRA@example.com",
            "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_profile_rejects_bad_phone_and_postcode(self):
        form = ProfileForm(data={
            "phone": "12345", "pickup_address": "1 Road", "postcode": "NOTAPOSTCODE",
            "transmission": "manual",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
        self.assertIn("postcode", form.errors)

    def test_profile_uppercases_postcode(self):
        form = ProfileForm(data={
            "phone": "07700 900123", "pickup_address": "1 High Road",
            "postcode": "ig3 8xx", "transmission": "automatic",
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["postcode"], "IG3 8XX")


class AuthViewTests(TestCase):
    def test_register_logs_in_and_asks_for_details(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Jamil", "username": "jamil", "email": "jamil@example.com",
            "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertTrue(User.objects.filter(username="jamil").exists())

    def test_login_and_register_redirect_logged_in_users(self):
        make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("accounts:register")), reverse("bookings:dashboard"))
        self.assertRedirects(self.client.get(reverse("accounts:login")), reverse("bookings:dashboard"))

    def test_logout_requires_post(self):
        make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("accounts:logout")), reverse("core:home"))

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_profile_update(self):
        user = make_learner("amira", complete_profile=False)
        self.client.login(username="amira", password=PASSWORD)
        self.client.post(reverse("accounts:profile"), {
            "phone": "07700 900456", "pickup_address": "5 Green Lane, Ilford",
            "postcode": "ig1 1aa", "transmission": "automatic",
        })
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.postcode, "IG1 1AA")
        self.assertEqual(user.profile.transmission, "automatic")

    def test_learner_can_delete_account(self):
        make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)
        self.assertRedirects(self.client.post(reverse("accounts:account_delete")), reverse("core:home"))
        self.assertFalse(User.objects.filter(username="amira").exists())

    def test_instructor_cannot_self_delete(self):
        make_instructor("sam")
        self.client.login(username="sam", password=PASSWORD)
        self.client.post(reverse("accounts:account_delete"))
        self.assertTrue(User.objects.filter(username="sam").exists())
