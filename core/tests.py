"""Automated tests for the core app."""
from django.test import TestCase
from django.urls import reverse

from core.postcodes import covered_list_display, district, is_covered, normalise
from core.testing import make_instructor


class PostcodeTests(TestCase):
    def test_normalise(self):
        self.assertEqual(normalise("ec1a1bb"), "EC1A 1BB")
        self.assertEqual(normalise("not a postcode"), "")

    def test_district(self):
        self.assertEqual(district("E14 9GE"), "E14")
        self.assertEqual(district("EC1A 1BB"), "EC1")
        self.assertEqual(district("E1W 1AA"), "E1")
        self.assertEqual(district("N1C 4AA"), "N1")
        self.assertEqual(district("E10 5AA"), "E10")

    def test_covered_areas(self):
        covered = ["E1 6AN", "E2 9PJ", "E3 5AA", "E8 1AA", "E9 7HD", "E14 9GE", "EC1V 9NR", "EC2A 4NE", "N1 9GU"]
        for postcode in covered:
            self.assertTrue(is_covered(postcode), postcode)
        for postcode in ["E10 5AA", "E11 1AA", "N16 7AA", "IG3 8XX", "SW1A 1AA"]:
            self.assertFalse(is_covered(postcode), postcode)

    def test_list_display(self):
        self.assertEqual(covered_list_display(), "E1, E2, E3, E8, E9, E14, EC1, EC2 and N1")


class CorePageTests(TestCase):
    def test_home_page(self):
        make_instructor("sam")
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Learn to drive with Sam")
        self.assertContains(response, "£35")
        self.assertContains(response, "Confidence")  # a seeded package
        self.assertContains(response, "E14")

    def test_home_postcode_checker(self):
        response = self.client.get(reverse("core:home"), {"postcode": "e3 5aa"})
        self.assertContains(response, "Yes! E3 5AA is in E3")
        response = self.client.get(reverse("core:home"), {"postcode": "IG3 8XX"})
        self.assertContains(response, "outside the area I cover")

    def test_postcode_check_api(self):
        url = reverse("core:postcode_check")
        self.assertEqual(self.client.get(url).status_code, 400)
        data = self.client.get(url, {"postcode": "EC1A 1BB"}).json()
        self.assertTrue(data["covered"])
        self.assertEqual(data["district"], "EC1")

    def test_about_page(self):
        self.assertContains(self.client.get(reverse("core:about")), "Cancellations")

    def test_contact_phone_on_every_page(self):
        for url in [reverse("core:home"), reverse("core:about"), reverse("packages:list")]:
            response = self.client.get(url)
            self.assertContains(response, "07476 283894")
            self.assertContains(response, 'href="tel:+447476283894"')

    def test_custom_404(self):
        response = self.client.get("/no-such-page/")
        self.assertContains(response, "Back to the home page", status_code=404)
