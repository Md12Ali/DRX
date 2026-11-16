"""Form for an instructor to rate a learner's skills."""
from django import forms

from .models import SkillRating


class SkillRatingsForm(forms.Form):
    """
    One radio group per skill. Built dynamically from the syllabus, so new
    skills added in the admin appear automatically.
    """

    def __init__(self, *args, skills, current_levels, **kwargs):
        super().__init__(*args, **kwargs)
        self.skills = list(skills)
        choices = [("0", "Not started")] + [(str(value), label) for value, label in SkillRating.Level.choices]
        for skill in self.skills:
            self.fields[self.field_name(skill)] = forms.TypedChoiceField(
                label=skill.name,
                help_text=skill.description,
                choices=choices,
                coerce=int,
                initial=str(current_levels.get(skill.pk, 0)),
                widget=forms.RadioSelect,
            )

    @staticmethod
    def field_name(skill):
        return f"skill_{skill.pk}"

    def skill_fields(self):
        """(skill, bound field) pairs for the template."""
        return [(skill, self[self.field_name(skill)]) for skill in self.skills]

    def save(self, learner, instructor_user):
        """Create, update or remove ratings. Returns the number of changes."""
        changes = 0
        for skill in self.skills:
            level = self.cleaned_data[self.field_name(skill)]
            existing = SkillRating.objects.filter(learner=learner, skill=skill).first()
            if level == 0:
                if existing:
                    existing.delete()
                    changes += 1
                continue
            if existing is None:
                SkillRating.objects.create(
                    learner=learner, skill=skill, level=level, updated_by=instructor_user
                )
                changes += 1
            elif existing.level != level:
                existing.level = level
                existing.updated_by = instructor_user
                existing.save()
                changes += 1
        return changes
