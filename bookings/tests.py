"""Automated tests for the bookings app."""
import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.testing import PASSWORD, future_start, make_booking, make_instructor, make_learner

from .models import Booking
from .services import available_start_times, booking_problems


class BookingModelTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")

    def test_end_and_reference_are_set(self):
        booking = make_booking(self.learner, self.instructor, minutes=90)
        self.assertEqual(booking.end - booking.start, datetime.timedelta(minutes=90))
        self.assertEqual(booking.reference, f"DRX-{booking.pk:05d}")
        self.assertEqual(booking.price_display, "£60.00")

    def test_change_cutoff(self):
        soon = make_booking(self.learner, self.instructor, start=timezone.now() + datetime.timedelta(hours=5))
        later = make_booking(self.learner, self.instructor, start=future_start(days=5))
        self.assertFalse(soon.can_be_changed_by_learner)
        self.assertTrue(later.can_be_changed_by_learner)

    def test_stale_pending_bookings_expire_and_free_the_slot(self):
        booking = make_booking(self.learner, self.instructor, status=Booking.Status.PENDING)
        self.assertIn(booking, Booking.objects.holding_slot())
        Booking.objects.filter(pk=booking.pk).update(created_on=timezone.now() - datetime.timedelta(hours=1))
        self.assertNotIn(booking, Booking.objects.holding_slot())
        self.assertEqual(Booking.objects.expire_stale_holds(), 1)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)

    def test_cancel_only_once(self):
        booking = make_booking(self.learner, self.instructor)
        self.assertTrue(booking.cancel())
        self.assertFalse(booking.cancel())


class BookingRuleTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")

    def test_valid_booking_has_no_problems(self):
        self.assertEqual(booking_problems(self.instructor, self.learner, future_start(), 60), [])

    def test_short_notice_rejected(self):
        start = timezone.localtime() + datetime.timedelta(hours=2)
        start = start.replace(minute=0, second=0, microsecond=0)
        problems = booking_problems(self.instructor, self.learner, start, 60)
        self.assertTrue(any("12 hours ahead" in problem for problem in problems))

    def test_too_far_ahead_rejected(self):
        problems = booking_problems(self.instructor, self.learner, future_start(days=70), 60)
        self.assertTrue(any("weeks ahead" in problem for problem in problems))

    def test_outside_working_hours(self):
        problems = booking_problems(self.instructor, self.learner, future_start(hour=19, minute=30), 60)
        self.assertTrue(any("teaches between" in problem for problem in problems))

    def test_odd_start_minute(self):
        problems = booking_problems(self.instructor, self.learner, future_start(minute=15), 60)
        self.assertTrue(any("half past" in problem for problem in problems))

    def test_day_off(self):
        start = future_start()
        self.instructor.working_days = str((timezone.localtime(start).weekday() + 1) % 7)
        problems = booking_problems(self.instructor, self.learner, start, 60)
        self.assertTrue(any("doesn't teach on" in problem for problem in problems))

    def test_instructor_clash(self):
        make_booking(make_learner("ben"), self.instructor, start=future_start(hour=10))
        problems = booking_problems(self.instructor, self.learner, future_start(hour=10, minute=30), 60)
        self.assertTrue(any("just been booked" in problem for problem in problems))

    def test_learner_clash_with_other_instructor(self):
        other = make_instructor("priya")
        make_booking(self.learner, other, start=future_start(hour=10))
        problems = booking_problems(self.instructor, self.learner, future_start(hour=10), 60)
        self.assertTrue(any("already have a lesson" in problem for problem in problems))

    def test_rescheduling_ignores_own_booking(self):
        booking = make_booking(self.learner, self.instructor, start=future_start(hour=10))
        problems = booking_problems(
            self.instructor, self.learner, future_start(hour=10, minute=30), 60, exclude_booking=booking
        )
        self.assertEqual(problems, [])

    def test_available_times_skip_cancelled_bookings(self):
        make_booking(self.learner, self.instructor, start=future_start(hour=10), status=Booking.Status.CANCELLED)
        times = available_start_times(self.instructor, timezone.localdate() + datetime.timedelta(days=3), 60)
        self.assertIn(future_start(hour=10), times)


class LearnerViewTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)

    def booking_data(self, **overrides):
        start = future_start()
        data = {
            "date": timezone.localtime(start).date().isoformat(),
            "start_time": "10:00",
            "duration_minutes": "90",
            "pickup_address": "12 High Road, Ilford",
            "learner_notes": "",
        }
        data.update(overrides)
        return data

    def test_dashboard_lists_bookings(self):
        make_booking(self.learner, self.instructor)
        self.assertContains(self.client.get(reverse("bookings:dashboard")), self.instructor.display_name)

    def test_incomplete_profile_is_sent_to_details_page(self):
        make_learner("ben", complete_profile=False)
        self.client.login(username="ben", password=PASSWORD)
        response = self.client.get(reverse("bookings:create", args=["sam"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:profile"), response.url)

    def test_create_booking_then_pay(self):
        response = self.client.post(reverse("bookings:create", args=["sam"]), self.booking_data())
        booking = Booking.objects.get()
        self.assertRedirects(response, reverse("payments:checkout", args=[booking.pk]))
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.price_pence, 6000)
        self.assertEqual(booking.learner, self.learner)

    def test_create_booking_form_prefills_address(self):
        response = self.client.get(reverse("bookings:create", args=["sam"]))
        self.assertContains(response, "12 High Road, Ilford, IG3 8XX")

    def test_invalid_booking_is_not_saved(self):
        self.client.post(reverse("bookings:create", args=["sam"]), self.booking_data(start_time="22:00"))
        self.assertEqual(Booking.objects.count(), 0)

    def test_reschedule(self):
        booking = make_booking(self.learner, self.instructor)
        self.client.post(reverse("bookings:edit", args=[booking.pk]), self.booking_data(start_time="14:00"))
        booking.refresh_from_db()
        self.assertEqual(timezone.localtime(booking.start).time(), datetime.time(14, 0))
        self.assertEqual(booking.duration_minutes, 60)  # length is locked

    def test_cannot_reschedule_inside_cutoff(self):
        booking = make_booking(self.learner, self.instructor, start=timezone.now() + datetime.timedelta(hours=5))
        response = self.client.get(reverse("bookings:edit", args=[booking.pk]))
        self.assertRedirects(response, booking.get_absolute_url())

    def test_cannot_see_someone_elses_booking(self):
        other = make_booking(make_learner("ben"), self.instructor)
        self.assertEqual(self.client.get(other.get_absolute_url()).status_code, 403)
        self.assertEqual(self.client.get(reverse("bookings:edit", args=[other.pk])).status_code, 404)

    def test_cancel_unpaid_booking(self):
        booking = make_booking(self.learner, self.instructor, status=Booking.Status.PENDING)
        self.client.post(reverse("bookings:cancel", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    @mock.patch("bookings.views.refund_booking", return_value=True)
    def test_cancel_paid_booking_refunds(self, mock_refund):
        booking = make_booking(self.learner, self.instructor)
        response = self.client.post(reverse("bookings:cancel", args=[booking.pk]), follow=True)
        mock_refund.assert_called_once()
        self.assertContains(response, "refund of £40.00")

    def test_diary_is_for_instructors_only(self):
        self.assertEqual(self.client.get(reverse("bookings:diary")).status_code, 403)


class InstructorViewTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")
        self.client.login(username="sam", password=PASSWORD)

    def test_dashboard_redirects_instructors_to_diary(self):
        self.assertRedirects(self.client.get(reverse("bookings:dashboard")), reverse("bookings:diary"))

    def test_diary_shows_lessons(self):
        make_booking(self.learner, self.instructor, start=future_start(days=2))
        self.assertContains(self.client.get(reverse("bookings:diary")), "Amira")

    def test_complete_lesson(self):
        booking = make_booking(self.learner, self.instructor, start=timezone.now() - datetime.timedelta(hours=2))
        self.client.post(reverse("bookings:complete", args=[booking.pk]), {"instructor_notes": "Great roundabouts."})
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)
        self.assertEqual(booking.instructor_notes, "Great roundabouts.")

    def test_cannot_complete_future_lesson(self):
        booking = make_booking(self.learner, self.instructor)
        self.client.post(reverse("bookings:complete", args=[booking.pk]), {"instructor_notes": "x"})
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_cannot_touch_another_instructors_booking(self):
        other = make_instructor("priya")
        booking = make_booking(self.learner, other, start=timezone.now() - datetime.timedelta(hours=2))
        response = self.client.post(reverse("bookings:complete", args=[booking.pk]), {"instructor_notes": "x"})
        self.assertEqual(response.status_code, 404)

    @mock.patch("bookings.views.refund_booking", return_value=True)
    def test_instructor_cancel_refunds(self, mock_refund):
        booking = make_booking(self.learner, self.instructor)
        self.client.post(reverse("bookings:instructor_cancel", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        mock_refund.assert_called_once()
