"""Automated tests for lesson packages. Stripe is always mocked."""
from types import SimpleNamespace
from unittest import mock

import stripe
from django.test import TestCase, override_settings
from django.urls import reverse

from bookings.models import Booking
from core.testing import PASSWORD, make_booking, make_instructor, make_learner

from .models import LessonPackage, PackagePurchase, hours_display, package_minutes_balance

STRIPE_SETTINGS = {"STRIPE_SECRET_KEY": "sk_test_dummy", "STRIPE_WEBHOOK_SECRET": "whsec_dummy"}


def give_hours(learner, hours):
    """A paid package purchase worth ``hours``."""
    package = LessonPackage.objects.get(slug="popular-10")
    return PackagePurchase.objects.create(
        learner=learner, package=package, hours=hours,
        price_pence=package.price_pence, status=PackagePurchase.Status.PAID,
    )


class PackageModelTests(TestCase):
    def test_seeded_packages(self):
        self.assertEqual(
            list(LessonPackage.objects.values_list("hours", flat=True)), [5, 10, 20, 30]
        )

    @override_settings(STANDARD_HOURLY_RATE_PENCE=3500)
    def test_savings_and_per_hour(self):
        package = LessonPackage.objects.get(slug="popular-10")
        self.assertEqual(package.price_display, "£330")
        self.assertEqual(package.per_hour_display, "£33.00")
        self.assertEqual(package.saving_display, "£20")

    def test_hours_display(self):
        self.assertEqual(hours_display(90), "1.5")
        self.assertEqual(hours_display(600), "10")


class BalanceTests(TestCase):
    def setUp(self):
        self.learner = make_learner("amira")
        self.instructor = make_instructor("sam")

    def test_only_paid_purchases_count(self):
        give_hours(self.learner, 10)
        PackagePurchase.objects.create(
            learner=self.learner, package=LessonPackage.objects.first(), hours=5, price_pence=17000
        )  # pending
        self.assertEqual(package_minutes_balance(self.learner), 600)

    def test_package_lessons_use_hours_and_cancelling_returns_them(self):
        give_hours(self.learner, 5)
        booking = make_booking(
            self.learner, self.instructor, minutes=90, payment_method=Booking.PaymentMethod.PACKAGE
        )
        make_booking(
            self.learner, self.instructor, minutes=60, status=Booking.Status.CANCELLED,
            payment_method=Booking.PaymentMethod.PACKAGE,
        )
        self.assertEqual(package_minutes_balance(self.learner), 210)
        booking.cancel()
        self.assertEqual(package_minutes_balance(self.learner), 300)


class PayWithPackageTests(TestCase):
    def setUp(self):
        self.learner = make_learner("amira")
        self.instructor = make_instructor("sam")
        self.booking = make_booking(
            self.learner, self.instructor, minutes=120, status=Booking.Status.PENDING
        )
        self.client.login(username="amira", password=PASSWORD)
        self.url = reverse("payments:pay_with_package", args=[self.booking.pk])

    def test_checkout_offers_package_when_enough_hours(self):
        give_hours(self.learner, 5)
        response = self.client.get(reverse("payments:checkout", args=[self.booking.pk]))
        self.assertContains(response, "Use 2 hours from my package")

    def test_checkout_hides_package_when_not_enough(self):
        give_hours(self.learner, 1)
        response = self.client.get(reverse("payments:checkout", args=[self.booking.pk]))
        self.assertNotContains(response, "from my package</button>")
        self.assertContains(response, "isn't enough for this lesson")

    def test_pay_with_package_confirms_booking(self):
        give_hours(self.learner, 5)
        self.client.post(self.url)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)
        self.assertTrue(self.booking.paid_with_package)
        self.assertEqual(package_minutes_balance(self.learner), 180)

    def test_not_enough_hours_is_refused(self):
        give_hours(self.learner, 1)
        self.client.post(self.url)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


@override_settings(**STRIPE_SETTINGS)
class BuyPackageTests(TestCase):
    def setUp(self):
        self.learner = make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)
        self.url = reverse("packages:buy", args=["popular-10"])

    def test_prices_page_is_public(self):
        self.client.logout()
        response = self.client.get(reverse("packages:list"))
        self.assertContains(response, "£330")
        self.assertContains(response, "save £20")
        self.assertContains(response, "1.5 hours £52.50")

    def test_buying_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PackagePurchase.objects.count(), 0)

    @mock.patch("stripe.checkout.Session.create")
    def test_buy_redirects_to_stripe(self, mock_create):
        mock_create.return_value = SimpleNamespace(id="cs_pkg", url="https://checkout.stripe.com/pkg")
        response = self.client.post(self.url)
        self.assertEqual(response.url, "https://checkout.stripe.com/pkg")
        purchase = PackagePurchase.objects.get()
        self.assertEqual((purchase.hours, purchase.price_pence), (10, 33000))
        self.assertEqual(purchase.stripe_session_id, "cs_pkg")

    @mock.patch("stripe.checkout.Session.create", side_effect=stripe.StripeError("Down"))
    def test_stripe_error(self, mock_create):
        response = self.client.post(self.url, follow=True)
        self.assertContains(response, "You have not been charged")
        self.assertEqual(PackagePurchase.objects.get().status, PackagePurchase.Status.FAILED)

    @mock.patch("stripe.checkout.Session.retrieve")
    def test_success_adds_hours(self, mock_retrieve):
        package = LessonPackage.objects.get(slug="popular-10")
        PackagePurchase.objects.create(
            learner=self.learner, package=package, hours=10, price_pence=33000, stripe_session_id="cs_pkg"
        )
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid", payment_intent="pi_pkg")
        response = self.client.get(reverse("packages:success"), {"session_id": "cs_pkg"})
        self.assertContains(response, "10 hours added")
        self.assertEqual(package_minutes_balance(self.learner), 600)

    def test_cancelled(self):
        package = LessonPackage.objects.get(slug="popular-10")
        purchase = PackagePurchase.objects.create(
            learner=self.learner, package=package, hours=10, price_pence=33000, stripe_session_id="cs_pkg"
        )
        response = self.client.get(reverse("packages:cancelled", args=[purchase.pk]), follow=True)
        self.assertContains(response, "You have not been charged")
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, PackagePurchase.Status.FAILED)

    def test_webhook_marks_package_paid(self):
        package = LessonPackage.objects.get(slug="popular-10")
        purchase = PackagePurchase.objects.create(
            learner=self.learner, package=package, hours=10, price_pence=33000, stripe_session_id="cs_pkg"
        )
        event = {"type": "checkout.session.completed",
                 "data": {"object": {"id": "cs_pkg", "payment_status": "paid", "payment_intent": "pi_1"}}}
        with mock.patch("stripe.Webhook.construct_event", return_value=event):
            self.client.post(reverse("payments:webhook"), data="{}", content_type="application/json")
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, PackagePurchase.Status.PAID)
