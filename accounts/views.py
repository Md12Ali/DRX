"""Views for registration, logging in and out, and the learner's details."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.utils import redirect_back

from .forms import ProfileForm, RegisterForm


def register(request):
    """Create a learner account. Only available to anonymous visitors."""
    if request.user.is_authenticated:
        messages.info(request, "You're already logged in.")
        return redirect("bookings:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to DRX, {user.first_name}! Add your pick-up details so you can book.",
            )
            return redirect("accounts:profile")
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class DRXLoginView(LoginView):
    """Log-in page. Logged-in users are sent straight to their dashboard."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        messages.success(self.request, f"Welcome back, {user.first_name or user.username}.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "That username and password didn't match.")
        return super().form_invalid(form)


@require_POST
def logout_view(request):
    """Log out (POST only, protected by CSRF)."""
    logout(request)
    messages.info(request, "You've been logged out. Drive safe!")
    return redirect("core:home")


@login_required
def profile(request):
    """View and edit the logged-in user's contact and pick-up details."""
    profile_obj = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Your details have been saved.")
            return redirect_back(request, "bookings:dashboard")
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = ProfileForm(instance=profile_obj)
    context = {"form": form, "next": request.GET.get("next", "")}
    return render(request, "accounts/profile.html", context)


@login_required
def account_delete(request):
    """Permanently delete the logged-in learner's account after confirmation."""
    if request.user.profile.is_instructor:
        messages.error(request, "Instructor accounts are closed by the DRX office. Please get in touch.")
        return redirect("accounts:profile")

    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.info(request, "Your account and all your data have been deleted.")
        return redirect("core:home")
    return render(request, "accounts/account_delete.html")
