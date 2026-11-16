"""URL patterns for the packages app."""
from django.urls import path

from . import views

app_name = "packages"

urlpatterns = [
    path("", views.package_list, name="list"),
    path("<slug:slug>/buy/", views.buy_package, name="buy"),
    path("success/", views.purchase_success, name="success"),
    path("purchases/<int:pk>/cancelled/", views.purchase_cancelled, name="cancelled"),
]
