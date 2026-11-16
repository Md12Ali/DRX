"""Admin configuration for instructors and reviews."""
from django.contrib import admin

from .models import Instructor, Review


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "teaches", "hourly_rate_display", "is_accepting_pupils")
    list_filter = ("teaches", "is_accepting_pupils")
    search_fields = ("display_name", "areas_covered", "user__username")
    prepopulated_fields = {"slug": ("display_name",)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("instructor", "learner", "rating", "created_on")
    list_filter = ("rating", "instructor")
    search_fields = ("comment", "learner__username")
