"""Admin configuration for bookings."""
from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "learner", "instructor", "start", "duration_minutes", "status", "price_display")
    list_filter = ("status", "instructor", "duration_minutes")
    search_fields = ("learner__username", "learner__first_name", "instructor__display_name")
    date_hierarchy = "start"
    readonly_fields = ("end", "created_on", "updated_on")
