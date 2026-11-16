"""Skills on the driving syllabus and each learner's level in them."""
from django.conf import settings
from django.db import models


class Skill(models.Model):
    """One topic on the learning-to-drive syllabus, e.g. 'Roundabouts'."""

    class Category(models.TextChoices):
        CONTROLS = "controls", "Car control"
        ROADS = "roads", "Roads and junctions"
        MANOEUVRES = "manoeuvres", "Manoeuvres"
        TEST = "test", "Test readiness"

    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=12, choices=Category.choices)
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class SkillRating(models.Model):
    """
    A learner's current level in one skill, set by their instructor.
    Uses the five-step scale common in UK driver training.
    """

    class Level(models.IntegerChoices):
        INTRODUCED = 1, "Introduced"
        INSTRUCTED = 2, "Under full instruction"
        PROMPTED = 3, "Prompted"
        SELDOM_PROMPTED = 4, "Seldom prompted"
        INDEPENDENT = 5, "Independent"

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_ratings",
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="ratings")
    level = models.PositiveSmallIntegerField(choices=Level.choices, default=Level.INTRODUCED)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["skill__order"]
        constraints = [
            models.UniqueConstraint(fields=["learner", "skill"], name="one_rating_per_skill"),
        ]

    def __str__(self):
        return f"{self.learner.username}: {self.skill} = {self.get_level_display()}"

    @property
    def percent(self):
        return self.level * 20


TEST_READY_PERCENT = 85
TEST_READY_MIN_LEVEL = SkillRating.Level.SELDOM_PROMPTED


def progress_summary(learner):
    """
    Overall progress for ``learner`` across every skill.

    Skills without a rating count as 0. A learner is test-ready when
    they score at least 85% overall and every skill is 'Seldom prompted'
    or better.
    """
    skills = list(Skill.objects.all())
    levels = dict(learner.skill_ratings.values_list("skill_id", "level"))

    rows = []
    total_points = 0
    weakest = []
    for skill in skills:
        level = levels.get(skill.pk, 0)
        total_points += level
        rows.append({"skill": skill, "level": level, "percent": level * 20})
        if level < TEST_READY_MIN_LEVEL:
            weakest.append(skill)

    max_points = len(skills) * SkillRating.Level.INDEPENDENT
    percent = round(total_points * 100 / max_points) if max_points else 0
    return {
        "rows": rows,
        "percent": percent,
        "rated_count": len(levels),
        "skill_count": len(skills),
        "test_ready": bool(skills) and percent >= TEST_READY_PERCENT and not weakest,
        "focus_next": weakest[:3],
    }
