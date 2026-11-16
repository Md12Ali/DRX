"""URL patterns for the payments app."""
from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("booking/<int:pk>/", views.checkout, name="checkout"),
    path("booking/<int:pk>/cancelled/", views.checkout_cancelled, name="cancelled"),
    path("success/", views.checkout_success, name="success"),
    path("webhook/", views.stripe_webhook, name="webhook"),
]
