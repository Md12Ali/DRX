"""URL patterns for the bookings app."""
from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("new/<slug:slug>/", views.booking_create, name="create"),
    path("<int:pk>/", views.booking_detail, name="detail"),
    path("<int:pk>/edit/", views.booking_edit, name="edit"),
    path("<int:pk>/cancel/", views.booking_cancel, name="cancel"),
    path("diary/", views.diary, name="diary"),
    path("timetable/<slug:slug>/", views.timetable, name="timetable"),
    path("<int:pk>/complete/", views.booking_complete, name="complete"),
    path("<int:pk>/instructor-cancel/", views.instructor_cancel, name="instructor_cancel"),
]
