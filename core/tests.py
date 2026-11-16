"""Automated tests for the core app."""
from django.test import TestCase
from django.urls import reverse

from core.testing import make_instructor


class CorePageTests(TestCase):
    def test_home_page(self):
        instructor = make_instructor("sam")
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Book your first lesson")
        self.assertContains(response, instructor.display_name)
        self.assertContains(response, "£40")

    def test_about_page(self):
        self.assertContains(self.client.get(reverse("core:about")), "Cancellations")

    def test_custom_404(self):
        response = self.client.get("/no-such-page/")
        self.assertContains(response, "Back to the home page", status_code=404)
