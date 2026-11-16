"""Automated tests for the bookings app."""
import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.testing import PASSWORD, future_start, make_booking, make_instructor, make_learner

from .models import Booking
from .services import available_start_times, booking_problems, week_timetable


class BookingModelTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")

    def test_end_and_reference_are_set(self):
        booking = make_booking(self.learner, self.instructor, minutes=90)
        self.assertEqual(booking.end - booking.start, datetime.timedelta(minutes=90))
        self.assertEqual(booking.reference, f"DRX-{booking.pk:05d}")
        self.assertEqual(booking.price_display, "£52.50")
        self.assertEqual(booking.hours_display, "1.5")

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
            "pickup_address": "12 Roman Road, London",
            "pickup_postcode": "E3 5AA",
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
        self.assertEqual(booking.price_pence, 5250)
        self.assertEqual(booking.pickup_postcode, "E3 5AA")
        self.assertEqual(booking.learner, self.learner)

    def test_create_booking_form_prefills_address(self):
        response = self.client.get(reverse("bookings:create", args=["sam"]))
        self.assertContains(response, "12 Roman Road, London")
        self.assertContains(response, "E3 5AA")

    def test_pickup_outside_area_rejected(self):
        response = self.client.post(
            reverse("bookings:create", args=["sam"]), self.booking_data(pickup_postcode="IG3 8XX")
        )
        self.assertContains(response, "only available in")
        self.assertEqual(Booking.objects.count(), 0)

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
        self.assertContains(response, "refund of £35.00")

    def test_cancel_package_booking_returns_hours(self):
        booking = make_booking(
            self.learner, self.instructor, payment_method=Booking.PaymentMethod.PACKAGE
        )
        response = self.client.post(reverse("bookings:cancel", args=[booking.pk]), follow=True)
        self.assertContains(response, "1 hour went back into your package")

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


class TimetableTests(TestCase):
    """The weekly timetable: free, booked, own lessons, privacy and week limits."""

    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("lily")
        self.other = make_learner("omar")
        self.start = future_start(days=3, hour=10)
        self.week = self.start.date() - datetime.timedelta(days=self.start.weekday())
        self.url = reverse("bookings:timetable", args=["sam"])

    def cell(self, table, when):
        """The timetable cell for an aware datetime."""
        local = timezone.localtime(when)
        row = next(r for r in table["rows"] if r["time"] == local.time())
        return row["cells"][(local.date() - table["days"][0]).days]

    def test_free_booked_and_own_slots(self):
        make_booking(self.other, self.instructor, start=self.start)
        mine = make_booking(self.learner, self.instructor, start=self.start + datetime.timedelta(hours=3))
        table = week_timetable(self.instructor, self.week, 60, viewer=self.learner)

        self.assertEqual(self.cell(table, self.start)["state"], "booked")
        self.assertEqual(self.cell(table, self.start + datetime.timedelta(minutes=30))["state"], "booked")
        self.assertEqual(self.cell(table, mine.start)["state"], "yours")
        self.assertEqual(self.cell(table, self.start + datetime.timedelta(hours=1))["state"], "free")

    def test_slot_just_before_a_lesson_is_closed_for_longer_lessons(self):
        make_booking(self.other, self.instructor, start=self.start)
        before = self.start - datetime.timedelta(hours=1)
        self.assertEqual(self.cell(week_timetable(self.instructor, self.week, 60), before)["state"], "free")
        self.assertEqual(self.cell(week_timetable(self.instructor, self.week, 120), before)["state"], "closed")

    def test_days_off_are_marked(self):
        self.instructor.working_days = "012345"  # Monday to Saturday
        self.instructor.save()
        table = week_timetable(self.instructor, self.week, 60)
        self.assertTrue(all(row["cells"][6]["state"] == "off" for row in table["rows"]))

    def test_visitors_can_see_it_and_free_times_link_to_the_booking_form(self):
        response = self.client.get(self.url, {"week": self.week.isoformat(), "duration": 90})
        self.assertEqual(response.status_code, 200)
        booking_link = (
            f'{reverse("bookings:create", args=["sam"])}?date={self.start:%Y-%m-%d}'
            f'&amp;time={timezone.localtime(self.start):%H:%M}&amp;duration=90'
        )
        self.assertContains(response, booking_link)

    def test_learners_never_see_who_else_booked(self):
        make_booking(self.other, self.instructor, start=self.start)
        self.client.force_login(self.learner)
        response = self.client.get(self.url, {"week": self.week.isoformat()})
        self.assertContains(response, "Booked")
        self.assertNotContains(response, "Omar")

    def test_instructor_sees_learner_names(self):
        make_booking(self.other, self.instructor, start=self.start)
        self.client.force_login(self.instructor.user)
        response = self.client.get(self.url, {"week": self.week.isoformat()})
        self.assertContains(response, "Omar")

    def test_week_is_kept_inside_the_booking_window(self):
        this_week = timezone.localdate() - datetime.timedelta(days=timezone.localdate().weekday())
        response = self.client.get(self.url, {"week": "2001-01-01", "duration": "999"})
        self.assertEqual(response.context["week"], this_week)
        self.assertEqual(response.context["duration"], 60)
        self.assertIsNone(response.context["previous_week"])
        response = self.client.get(self.url, {"week": "2999-01-01"})
        self.assertIsNone(response.context["next_week"])

    def test_booking_form_is_prefilled_from_the_timetable(self):
        self.client.force_login(self.learner)
        response = self.client.get(
            reverse("bookings:create", args=["sam"]),
            {"date": f"{self.start:%Y-%m-%d}", "time": "10:00", "duration": "120"},
        )
        form = response.context["form"]
        self.assertEqual(form.initial["start_time"], "10:00")
        self.assertEqual(form.initial["duration_minutes"], 120)
