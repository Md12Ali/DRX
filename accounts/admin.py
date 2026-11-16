"""Admin configuration for learner profiles."""
from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "postcode", "transmission", "created_on")
    list_filter = ("transmission",)
    search_fields = ("user__username", "user__first_name", "user__email", "postcode")
