"""Automated tests for the progress app."""
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from core.testing import PASSWORD, make_booking, make_instructor, make_learner

from .models import Skill, SkillRating, progress_summary


class SyllabusTests(TestCase):
    def test_syllabus_is_loaded_by_migration(self):
        self.assertEqual(Skill.objects.count(), 16)
        self.assertEqual(Skill.objects.first().name, "Cockpit drill and controls")


class ProgressSummaryTests(TestCase):
    def setUp(self):
        self.learner = make_learner("amira")

    def test_no_ratings_is_zero(self):
        summary = progress_summary(self.learner)
        self.assertEqual(summary["percent"], 0)
        self.assertFalse(summary["test_ready"])
        self.assertEqual(len(summary["focus_next"]), 3)

    def test_percent_and_test_ready(self):
        for skill in Skill.objects.all():
            SkillRating.objects.create(learner=self.learner, skill=skill, level=5)
        summary = progress_summary(self.learner)
        self.assertEqual(summary["percent"], 100)
        self.assertTrue(summary["test_ready"])

    def test_one_weak_skill_blocks_test_ready(self):
        skills = list(Skill.objects.all())
        for skill in skills:
            SkillRating.objects.create(learner=self.learner, skill=skill, level=5)
        SkillRating.objects.filter(skill=skills[0]).update(level=3)
        summary = progress_summary(self.learner)
        self.assertGreaterEqual(summary["percent"], 85)
        self.assertFalse(summary["test_ready"])
        self.assertEqual(summary["focus_next"], [skills[0]])


class ProgressViewTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor("sam")
        self.learner = make_learner("amira")
        self.url = reverse("progress:learner", args=["amira"])

    def form_data(self, level):
        return {f"skill_{skill.pk}": str(level) for skill in Skill.objects.all()}

    def test_learner_sees_own_progress(self):
        self.client.login(username="amira", password=PASSWORD)
        self.assertContains(self.client.get(reverse("progress:mine")), "Roundabouts")

    def test_learner_cannot_rate(self):
        self.client.login(username="amira", password=PASSWORD)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_instructor_must_teach_learner(self):
        self.client.login(username="sam", password=PASSWORD)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_instructor_rates_skills(self):
        make_booking(self.learner, self.instructor, status=Booking.Status.COMPLETED)
        self.client.login(username="sam", password=PASSWORD)
        self.client.post(self.url, self.form_data(4))
        self.assertEqual(self.learner.skill_ratings.count(), 16)
        self.assertEqual(self.learner.skill_ratings.first().updated_by, self.instructor.user)

        self.client.post(self.url, self.form_data(0))
        self.assertEqual(self.learner.skill_ratings.count(), 0)
