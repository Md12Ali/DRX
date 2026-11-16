"""Admin configuration for the syllabus and skill ratings."""
from django.contrib import admin

from .models import Skill, SkillRating


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "category")
    list_display_links = ("name",)
    list_filter = ("category",)
    ordering = ("order",)


@admin.register(SkillRating)
class SkillRatingAdmin(admin.ModelAdmin):
    list_display = ("learner", "skill", "level", "updated_by", "updated_on")
    list_filter = ("level", "skill__category")
    search_fields = ("learner__username", "learner__first_name")
