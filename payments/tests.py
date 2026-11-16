"""Automated tests for the payments app. Stripe is always mocked."""
import datetime
from types import SimpleNamespace
from unittest import mock

import stripe
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from core.testing import PASSWORD, make_booking, make_instructor, make_learner

from .models import Payment
from .refunds import refund_booking

STRIPE_SETTINGS = {"STRIPE_SECRET_KEY": "sk_test_dummy", "STRIPE_WEBHOOK_SECRET": "whsec_dummy"}


@override_settings(**STRIPE_SETTINGS)
class CheckoutTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")
        self.booking = make_booking(self.learner, self.instructor, status=Booking.Status.PENDING)
        self.client.login(username="amira", password=PASSWORD)
        self.url = reverse("payments:checkout", args=[self.booking.pk])

    def test_summary_page(self):
        response = self.client.get(self.url)
        self.assertContains(response, "£35.00")
        self.assertContains(response, self.booking.reference)

    def test_other_learners_cannot_pay(self):
        make_learner("ben")
        self.client.login(username="ben", password=PASSWORD)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    @mock.patch("payments.views.stripe.checkout.Session.create")
    def test_redirects_to_stripe(self, mock_create):
        mock_create.return_value = SimpleNamespace(id="cs_1", url="https://checkout.stripe.com/x")
        response = self.client.post(self.url)
        self.assertEqual(response.url, "https://checkout.stripe.com/x")
        payment = Payment.objects.get()
        self.assertEqual(payment.stripe_session_id, "cs_1")
        self.assertEqual(payment.amount_pence, 3500)

    @mock.patch("payments.views.stripe.checkout.Session.create")
    def test_stripe_error_is_reported(self, mock_create):
        mock_create.side_effect = stripe.StripeError("Network down")
        response = self.client.post(self.url, follow=True)
        self.assertContains(response, "You have not been charged")

    @override_settings(STRIPE_SECRET_KEY="")
    def test_missing_keys(self):
        response = self.client.post(self.url, follow=True)
        self.assertContains(response, "Card payments are not available")

    def test_expired_hold_cannot_be_paid(self):
        Booking.objects.filter(pk=self.booking.pk).update(created_on=timezone.now() - datetime.timedelta(hours=1))
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, "slot has been released")

    @mock.patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_confirms_booking(self, mock_retrieve):
        Payment.objects.create(booking=self.booking, amount_pence=4000, stripe_session_id="cs_1")
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid", payment_intent="pi_1")
        response = self.client.get(reverse("payments:success"), {"session_id": "cs_1"})
        self.assertContains(response, "Your lesson is booked")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(Payment.objects.get().stripe_payment_intent, "pi_1")

    @mock.patch("payments.views.stripe.checkout.Session.retrieve")
    def test_unpaid_session_not_trusted(self, mock_retrieve):
        Payment.objects.create(booking=self.booking, amount_pence=4000, stripe_session_id="cs_1")
        mock_retrieve.return_value = SimpleNamespace(payment_status="unpaid")
        self.client.get(reverse("payments:success"), {"session_id": "cs_1"})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)

    def test_cancelled_page(self):
        Payment.objects.create(booking=self.booking, amount_pence=4000, stripe_session_id="cs_1")
        response = self.client.get(reverse("payments:cancelled", args=[self.booking.pk]))
        self.assertContains(response, "You have not been charged")
        self.assertEqual(Payment.objects.get().status, Payment.Status.FAILED)


@override_settings(**STRIPE_SETTINGS)
class WebhookTests(TestCase):
    def setUp(self):
        booking = make_booking(make_learner("amira"), make_instructor("sam"), status=Booking.Status.PENDING)
        self.payment = Payment.objects.create(booking=booking, amount_pence=4000, stripe_session_id="cs_1")

    def send(self, event_type, payment_status="paid"):
        event = {
            "type": event_type,
            "data": {"object": {"id": "cs_1", "payment_status": payment_status, "payment_intent": "pi_9"}},
        }
        with mock.patch("payments.views.stripe.Webhook.construct_event", return_value=event):
            return self.client.post(reverse("payments:webhook"), data="{}", content_type="application/json")

    def test_completed_event_confirms(self):
        self.assertEqual(self.send("checkout.session.completed").status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.payment.booking.status, Booking.Status.CONFIRMED)

    def test_expired_event_fails_payment(self):
        self.send("checkout.session.expired", payment_status="unpaid")
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.FAILED)

    def test_bad_signature(self):
        response = self.client.post(
            reverse("payments:webhook"), data="{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="bad"
        )
        self.assertEqual(response.status_code, 400)


@override_settings(**STRIPE_SETTINGS)
class RefundTests(TestCase):
    def setUp(self):
        booking = make_booking(make_learner("amira"), make_instructor("sam"))
        self.payment = Payment.objects.create(
            booking=booking, amount_pence=4000, stripe_session_id="cs_1",
            stripe_payment_intent="pi_1", status=Payment.Status.PAID,
        )

    @mock.patch("payments.refunds.stripe.Refund.create")
    def test_successful_refund(self, mock_refund):
        self.assertTrue(refund_booking(self.payment.booking))
        mock_refund.assert_called_once_with(payment_intent="pi_1")
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)

    @mock.patch("payments.refunds.stripe.Refund.create", side_effect=stripe.StripeError("Down"))
    def test_failed_refund_is_flagged(self, mock_refund):
        self.assertFalse(refund_booking(self.payment.booking))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REFUND_FAILED)

    def test_unpaid_booking_needs_no_refund(self):
        booking = make_booking(make_learner("ben"), make_instructor("priya"), status=Booking.Status.PENDING)
        self.assertTrue(refund_booking(booking))
