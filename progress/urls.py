"""URL patterns for the progress app."""
from django.urls import path

from . import views

app_name = "progress"

urlpatterns = [
    path("", views.my_progress, name="mine"),
    path("learners/<str:username>/", views.learner_progress, name="learner"),
]
