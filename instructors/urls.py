"""URL patterns for the instructors app."""
from django.urls import path

from . import views

app_name = "instructors"

urlpatterns = [
    path("", views.instructor_list, name="list"),
    path("me/edit/", views.instructor_edit, name="edit"),
    path("reviews/<int:pk>/edit/", views.review_edit, name="review_edit"),
    path("reviews/<int:pk>/delete/", views.review_delete, name="review_delete"),
    path("<slug:slug>/", views.instructor_detail, name="detail"),
    path("<slug:slug>/availability/", views.availability, name="availability"),
    path("<slug:slug>/review/", views.review_create, name="review_create"),
]
