"""Automated tests for the instructors app."""
import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from core.testing import PASSWORD, future_start, make_booking, make_instructor, make_learner

from .models import Instructor, Review


class InstructorModelTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")

    def test_lesson_price_is_pro_rata(self):
        self.assertEqual(self.instructor.lesson_price_pence(60), 3500)
        self.assertEqual(self.instructor.lesson_price_pence(90), 5250)
        self.assertEqual(self.instructor.lesson_price_pence(120), 7000)

    def test_candidate_start_times_fit_working_day(self):
        day = timezone.localdate() + datetime.timedelta(days=2)
        times = self.instructor.candidate_start_times(day, 60)
        # 08:00 to 19:00 in 30-minute steps = 23 start times
        self.assertEqual(len(times), 23)
        self.assertEqual(timezone.localtime(times[-1]).time(), datetime.time(19, 0))
        two_hour = self.instructor.candidate_start_times(day, 120)
        self.assertEqual(timezone.localtime(two_hour[-1]).time(), datetime.time(18, 0))

    def test_no_times_on_days_off(self):
        self.instructor.working_days = "0"  # Mondays only
        day = timezone.localdate()
        while day.weekday() == 0:
            day += datetime.timedelta(days=1)
        self.assertEqual(self.instructor.candidate_start_times(day, 60), [])

    def test_teaches_transmission(self):
        self.instructor.teaches = Instructor.Teaches.BOTH
        self.assertTrue(self.instructor.teaches_transmission("automatic"))
        self.instructor.teaches = Instructor.Teaches.MANUAL
        self.assertFalse(self.instructor.teaches_transmission("automatic"))

    def test_display_helpers(self):
        self.assertEqual(self.instructor.hourly_rate_display, "£35")
        self.assertEqual(self.instructor.area_list, ["Bow", "Hackney", "E3"])

    def test_new_instructors_teach_automatic(self):
        self.assertEqual(Instructor().teaches, Instructor.Teaches.AUTOMATIC)

    def test_new_instructors_are_shown_as_trainees(self):
        self.assertEqual(self.instructor.qualification, Instructor.Qualification.TRAINEE)
        self.assertFalse(self.instructor.is_adi)

    def test_main_instructor_prefers_one_taking_bookings(self):
        make_instructor("priya", is_accepting_pupils=True)
        self.instructor.is_accepting_pupils = False
        self.instructor.save()
        self.assertEqual(Instructor.objects.main().slug, "priya")
        self.assertEqual(self.instructor.initials, "SS")


class DirectoryViewTests(TestCase):
    def setUp(self):
        self.manual = make_instructor("sam", teaches=Instructor.Teaches.MANUAL, areas_covered="Ilford")
        self.auto = make_instructor("priya", teaches=Instructor.Teaches.AUTOMATIC, areas_covered="Romford")

    def test_list_filters_by_transmission(self):
        response = self.client.get(reverse("instructors:list"), {"transmission": "automatic"})
        self.assertEqual(list(response.context["instructors"]), [self.auto])

    def test_list_searches_areas(self):
        response = self.client.get(reverse("instructors:list"), {"q": "ilford"})
        self.assertEqual(list(response.context["instructors"]), [self.manual])

    def test_detail_shows_prices(self):
        response = self.client.get(self.manual.get_absolute_url())
        self.assertContains(response, "£52.50")
        # No badge, but trainees are still clearly described as trainees (DVSA advertising rule)
        self.assertNotContains(response, "qualification-badge")
        self.assertContains(response, "Licensed by DVSA as a trainee driving instructor")
        self.assertContains(response, "Calm and patient.")

    def test_single_instructor_list_redirects_to_profile(self):
        self.auto.bookings.all().delete()
        self.auto.delete()
        self.assertRedirects(self.client.get(reverse("instructors:list")), self.manual.get_absolute_url())

    def test_unknown_instructor_404(self):
        self.assertEqual(self.client.get("/instructors/nobody/").status_code, 404)


class AvailabilityApiTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.url = reverse("instructors:availability", args=["sam"])

    def test_bad_date(self):
        self.assertEqual(self.client.get(self.url, {"date": "nope"}).status_code, 400)

    def test_bad_duration(self):
        date = (timezone.localdate() + datetime.timedelta(days=3)).isoformat()
        self.assertEqual(self.client.get(self.url, {"date": date, "duration": "45"}).status_code, 400)

    def test_booked_times_are_removed(self):
        learner = make_learner("amira")
        make_booking(learner, self.instructor, start=future_start(days=3, hour=10))
        date = (timezone.localdate() + datetime.timedelta(days=3)).isoformat()
        times = self.client.get(self.url, {"date": date, "duration": "60"}).json()["times"]
        self.assertNotIn("10:00", times)
        self.assertNotIn("09:30", times)  # would overlap 10:00-10:30
        self.assertIn("09:00", times)
        self.assertIn("11:00", times)


class InstructorEditTests(TestCase):
    def test_learners_cannot_edit(self):
        make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("instructors:edit")).status_code, 403)

    def test_instructor_updates_rate_and_days(self):
        instructor = make_instructor("sam")
        self.client.login(username="sam", password=PASSWORD)
        self.client.post(reverse("instructors:edit"), {
            "qualification": "trainee", "tagline": "Patient lessons", "bio": "", "areas_covered": "Ilford",
            "teaches": "manual", "car": "Polo", "day_start": "09:00", "day_end": "17:00",
            "is_accepting_pupils": "on", "hourly_rate": "45.50", "days": ["0", "2", "4"],
        })
        instructor.refresh_from_db()
        self.assertEqual(instructor.hourly_rate_pence, 4550)
        self.assertEqual(instructor.working_days, "024")

    def test_working_day_must_be_an_hour(self):
        make_instructor("sam")
        self.client.login(username="sam", password=PASSWORD)
        response = self.client.post(reverse("instructors:edit"), {
            "areas_covered": "Ilford", "teaches": "manual", "day_start": "09:00",
            "day_end": "09:30", "hourly_rate": "40", "days": ["0"],
        })
        self.assertContains(response, "at least one hour long")


class ReviewTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")
        self.client.login(username="amira", password=PASSWORD)
        self.url = reverse("instructors:review_create", args=["sam"])

    def test_cannot_review_without_completed_lesson(self):
        self.client.post(self.url, {"rating": 5, "comment": "Brilliant instructor!"})
        self.assertEqual(Review.objects.count(), 0)

    def test_review_after_completed_lesson(self):
        make_booking(self.learner, self.instructor, status=Booking.Status.COMPLETED)
        self.client.post(self.url, {"rating": 5, "comment": "Brilliant instructor!"})
        self.assertEqual(self.instructor.rating_summary(), (5.0, 1))

    def test_edit_and_delete_own_review_only(self):
        other = make_learner("ben")
        review = Review.objects.create(instructor=self.instructor, learner=other, rating=4, comment="Good lessons.")
        response = self.client.post(reverse("instructors:review_delete", args=[review.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())

        mine = Review.objects.create(
            instructor=self.instructor, learner=self.learner, rating=3, comment="Okay lessons."
        )
        self.client.post(
            reverse("instructors:review_edit", args=[mine.pk]), {"rating": 5, "comment": "Actually great!"}
        )
        mine.refresh_from_db()
        self.assertEqual(mine.rating, 5)
        self.client.post(reverse("instructors:review_delete", args=[mine.pk]))
        self.assertFalse(Review.objects.filter(pk=mine.pk).exists())
